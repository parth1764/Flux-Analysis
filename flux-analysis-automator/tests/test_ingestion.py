from unittest.mock import patch

from app.services.ingestion_service import IngestionService


def test_ingestion_upserts_records(db_session):
    sample = [
        {
            "period": "2025-Q1",
            "period_type": "QUARTER",
            "fiscal_year": 2025,
            "fiscal_quarter": 1,
            "metric_name": "Total Revenue",
            "normalized_metric": "Net Revenue",
            "value": 1000.0,
            "currency": "USD",
            "source": "yfinance",
            "source_url": "http://example.com",
        }
    ]
    with patch("app.services.ingestion_service.fetch_yfinance_quarterly", return_value=sample):
        result = IngestionService(db_session).run(tickers=["JPM"])
    assert result["records_processed"] >= 1
