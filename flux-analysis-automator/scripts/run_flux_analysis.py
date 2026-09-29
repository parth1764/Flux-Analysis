#!/usr/bin/env python3
"""Calculate period-over-period flux and materiality."""

from app.db.database import SessionLocal
from app.services.ingestion_service import FluxService


def main() -> None:
    db = SessionLocal()
    try:
        print(FluxService(db).run())
    finally:
        db.close()


if __name__ == "__main__":
    main()
