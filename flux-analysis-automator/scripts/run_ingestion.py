#!/usr/bin/env python3
"""Run public-data ingestion (yFinance)."""

from app.db.database import SessionLocal
from app.services.ingestion_service import IngestionService


def main() -> None:
    db = SessionLocal()
    try:
        result = IngestionService(db).run()
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
