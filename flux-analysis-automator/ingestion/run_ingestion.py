"""CLI entry: python -m ingestion.run_ingestion"""

from app.db.database import SessionLocal
from app.services.ingestion_service import IngestionService


def main() -> None:
    db = SessionLocal()
    try:
        print(IngestionService(db).run())
    finally:
        db.close()


if __name__ == "__main__":
    main()
