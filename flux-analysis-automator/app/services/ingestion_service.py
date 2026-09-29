from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Bank, FinancialStatement, FluxAnalysis, MaterialityStatus
from app.db.repositories.financial_repos import BankRepository, FinancialRepository, FluxRepository
from app.utils.financial_utils import calculate_flux, evaluate_materiality, period_sort_key
from ingestion.sources.yfinance_source import fetch_yfinance_quarterly

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.banks = BankRepository(db)
        self.financials = FinancialRepository(db)

    def run(self, tickers: list[str] | None = None) -> dict[str, Any]:
        self.banks.seed_defaults()
        banks = self.banks.list_banks()
        if tickers:
            banks = [b for b in banks if b.ticker in tickers]

        processed = 0
        rejected = 0
        for bank in banks:
            try:
                records = fetch_yfinance_quarterly(bank.ticker)
                for rec in records:
                    if rec["value"] is None:
                        rejected += 1
                        continue
                    self.financials.upsert_record(bank.id, rec)
                    processed += 1
                self.db.commit()
            except Exception as exc:
                logger.exception("Ingestion failed for %s: %s", bank.ticker, exc)
                self.db.rollback()
                continue
        logger.info("Ingestion complete processed=%s rejected=%s", processed, rejected)
        return {"records_processed": processed, "records_rejected": rejected, "banks": len(banks)}


class FluxService:
    def __init__(self, db: Session):
        self.db = db
        self.banks = BankRepository(db)
        self.financials = FinancialRepository(db)
        self.flux_repo = FluxRepository(db)

    def run(self) -> dict[str, int]:
        count = 0
        for bank in self.banks.list_banks():
            count += self._run_for_bank(bank)
        return {"flux_records": count}

    def _run_for_bank(self, bank: Bank) -> int:
        periods = sorted(set(self.financials.distinct_periods(bank.id)), key=period_sort_key)
        if len(periods) < 2:
            logger.warning("Not enough periods for bank %s", bank.ticker)
            return 0
        current_p, previous_p = periods[-1], periods[-2]
        rows = (
            self.db.query(FinancialStatement)
            .filter(FinancialStatement.bank_id == bank.id, FinancialStatement.period.in_([current_p, previous_p]))
            .all()
        )
        by_metric: dict[str, dict[str, float]] = {}
        for row in rows:
            by_metric.setdefault(row.normalized_metric, {})[row.period] = row.value

        created = 0
        for metric, period_map in by_metric.items():
            prev_v = period_map.get(previous_p)
            cur_v = period_map.get(current_p)
            flux_calc = calculate_flux(prev_v, cur_v)
            mat = evaluate_materiality(
                flux_calc.absolute_change,
                flux_calc.percentage_change,
                flux_calc.percentage_change_defined,
                metric,
            )
            status = MaterialityStatus[mat.status] if mat.status in MaterialityStatus.__members__ else MaterialityStatus.UNDEFINED
            entity = FluxAnalysis(
                bank_id=bank.id,
                current_period=current_p,
                previous_period=previous_p,
                metric_name=metric,
                previous_value=prev_v,
                current_value=cur_v,
                absolute_change=flux_calc.absolute_change,
                percentage_change=flux_calc.percentage_change,
                percentage_change_defined=flux_calc.percentage_change_defined,
                materiality_status=status,
                materiality_reason=mat.reason,
            )
            self.flux_repo.upsert_flux(entity)
            created += 1
        return created
