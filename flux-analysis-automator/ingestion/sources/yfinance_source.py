from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
import yfinance as yf

from app.services.normalization_service import normalize_metric_name

logger = logging.getLogger(__name__)


def _period_label(ts: pd.Timestamp, period_type: str) -> tuple[str, int | None, int | None]:
    year = int(ts.year)
    quarter = int((ts.month - 1) // 3 + 1)
    if period_type == "QUARTER":
        return f"{year}-Q{quarter}", year, quarter
    return f"{year}-FY", year, None


def fetch_yfinance_quarterly(ticker: str) -> list[dict]:
    """Extract normalized quarterly metrics from yFinance public statements."""
    stock = yf.Ticker(ticker)
    frames = [
        ("quarterly_income_stmt", stock.quarterly_income_stmt),
        ("quarterly_balance_sheet", stock.quarterly_balance_sheet),
        ("quarterly_cashflow", stock.quarterly_cashflow),
    ]
    records: list[dict] = []
    source_url = f"https://finance.yahoo.com/quote/{ticker}/financials"

    for frame_name, df in frames:
        if df is None or df.empty:
            logger.warning("Empty frame %s for %s", frame_name, ticker)
            continue
        for metric_name in df.index.astype(str):
            normalized = normalize_metric_name(metric_name)
            if not normalized:
                continue
            for col in df.columns:
                value = df.at[metric_name, col]
                if pd.isna(value):
                    continue
                period, fy, fq = _period_label(pd.Timestamp(col), "QUARTER")
                records.append(
                    {
                        "period": period,
                        "period_type": "QUARTER",
                        "fiscal_year": fy,
                        "fiscal_quarter": fq,
                        "metric_name": metric_name,
                        "normalized_metric": normalized,
                        "value": float(value),
                        "currency": "USD",
                        "source": "yfinance",
                        "source_url": source_url,
                        "ingestion_timestamp": datetime.utcnow().isoformat(),
                    }
                )
    logger.info("yFinance extracted %s records for %s", len(records), ticker)
    return records
