from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Approval,
    ApprovalStatus,
    Bank,
    Explanation,
    FinancialStatement,
    FluxAnalysis,
    MaterialityStatus,
    PeriodType,
    ValidationStatus,
)

DEFAULT_BANKS = [
    ("JPMorgan Chase", "JPM"),
    ("Bank of America", "BAC"),
    ("Wells Fargo", "WFC"),
    ("Citigroup", "C"),
    ("Goldman Sachs", "GS"),
    ("Morgan Stanley", "MS"),
]


class BankRepository:
    def __init__(self, db: Session):
        self.db = db

    def seed_defaults(self) -> int:
        created = 0
        for name, ticker in DEFAULT_BANKS:
            exists = self.db.query(Bank).filter(Bank.ticker == ticker).first()
            if exists:
                continue
            self.db.add(Bank(name=name, ticker=ticker, country="US", currency="USD"))
            created += 1
        self.db.commit()
        return created

    def list_banks(self) -> list[Bank]:
        return self.db.query(Bank).order_by(Bank.name).all()

    def get_by_id(self, bank_id: int) -> Bank | None:
        return self.db.query(Bank).filter(Bank.id == bank_id).first()

    def get_by_ticker(self, ticker: str) -> Bank | None:
        return self.db.query(Bank).filter(Bank.ticker == ticker.upper()).first()


class FinancialRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_record(self, bank_id: int, record: dict) -> None:
        existing = (
            self.db.query(FinancialStatement)
            .filter(
                FinancialStatement.bank_id == bank_id,
                FinancialStatement.period == record["period"],
                FinancialStatement.normalized_metric == record["normalized_metric"],
            )
            .first()
        )
        period_type = PeriodType.QUARTER if record["period_type"] == "QUARTER" else PeriodType.ANNUAL
        if existing:
            existing.metric_name = record["metric_name"]
            existing.value = record["value"]
            existing.currency = record["currency"]
            existing.source = record["source"]
            existing.source_url = record.get("source_url")
            existing.period_type = period_type
            existing.fiscal_year = record.get("fiscal_year")
            existing.fiscal_quarter = record.get("fiscal_quarter")
        else:
            self.db.add(
                FinancialStatement(
                    bank_id=bank_id,
                    period=record["period"],
                    period_type=period_type,
                    fiscal_year=record.get("fiscal_year"),
                    fiscal_quarter=record.get("fiscal_quarter"),
                    metric_name=record["metric_name"],
                    normalized_metric=record["normalized_metric"],
                    value=record["value"],
                    currency=record["currency"],
                    source=record["source"],
                    source_url=record.get("source_url"),
                )
            )
        self.db.flush()

    def list_financials(self, bank_id: int | None = None, limit: int = 500) -> list[FinancialStatement]:
        q = self.db.query(FinancialStatement)
        if bank_id:
            q = q.filter(FinancialStatement.bank_id == bank_id)
        return q.order_by(FinancialStatement.period.desc()).limit(limit).all()

    def distinct_periods(self, bank_id: int) -> list[str]:
        rows = (
            self.db.query(FinancialStatement.period)
            .filter(FinancialStatement.bank_id == bank_id)
            .distinct()
            .all()
        )
        return [r[0] for r in rows]


class FluxRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_flux(self, flux: FluxAnalysis) -> FluxAnalysis:
        existing = (
            self.db.query(FluxAnalysis)
            .filter(
                FluxAnalysis.bank_id == flux.bank_id,
                FluxAnalysis.current_period == flux.current_period,
                FluxAnalysis.previous_period == flux.previous_period,
                FluxAnalysis.metric_name == flux.metric_name,
            )
            .first()
        )
        if existing:
            for attr in (
                "previous_value",
                "current_value",
                "absolute_change",
                "percentage_change",
                "percentage_change_defined",
                "materiality_status",
                "materiality_reason",
            ):
                setattr(existing, attr, getattr(flux, attr))
            self.db.commit()
            self.db.refresh(existing)
            return existing
        self.db.add(flux)
        self.db.commit()
        self.db.refresh(flux)
        return flux

    def list_flux(
        self,
        bank_id: int | None = None,
        material_only: bool = False,
        limit: int = 500,
    ) -> list[FluxAnalysis]:
        q = self.db.query(FluxAnalysis).options(joinedload(FluxAnalysis.bank), joinedload(FluxAnalysis.explanations))
        if bank_id:
            q = q.filter(FluxAnalysis.bank_id == bank_id)
        if material_only:
            q = q.filter(FluxAnalysis.materiality_status == MaterialityStatus.MATERIAL)
        return q.order_by(FluxAnalysis.created_at.desc()).limit(limit).all()

    def get_by_id(self, flux_id: int) -> FluxAnalysis | None:
        return self.db.query(FluxAnalysis).filter(FluxAnalysis.id == flux_id).first()


class ExplanationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, explanation: Explanation) -> Explanation:
        self.db.add(explanation)
        self.db.commit()
        self.db.refresh(explanation)
        return explanation

    def list_all(self, limit: int = 200) -> list[Explanation]:
        return self.db.query(Explanation).order_by(Explanation.created_at.desc()).limit(limit).all()

    def list_pending_validation(self) -> list[Explanation]:
        return (
            self.db.query(Explanation)
            .filter(Explanation.validation_status == ValidationStatus.PENDING)
            .order_by(Explanation.created_at.desc())
            .all()
        )

    def get_by_id(self, explanation_id: int) -> Explanation | None:
        return self.db.query(Explanation).filter(Explanation.id == explanation_id).first()


class ApprovalRepository:
    def __init__(self, db: Session):
        self.db = db

    def ensure_pending_for_flux(self, flux_id: int) -> Approval:
        row = (
            self.db.query(Approval)
            .filter(Approval.flux_id == flux_id, Approval.status == ApprovalStatus.PENDING)
            .first()
        )
        if row:
            return row
        row = Approval(flux_id=flux_id, status=ApprovalStatus.PENDING)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_for_flux(self, flux_id: int) -> Approval | None:
        return self.db.query(Approval).filter(Approval.flux_id == flux_id).order_by(Approval.id.desc()).first()

    def update_status(
        self,
        flux_id: int,
        status: ApprovalStatus,
        reviewer: str | None,
        comment: str | None,
    ) -> Approval:
        approval = self.get_for_flux(flux_id) or Approval(flux_id=flux_id)
        approval.status = status
        approval.reviewer = reviewer
        approval.review_comment = comment
        if status == ApprovalStatus.APPROVED:
            from datetime import datetime, timezone

            approval.approved_at = datetime.now(timezone.utc)
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval
