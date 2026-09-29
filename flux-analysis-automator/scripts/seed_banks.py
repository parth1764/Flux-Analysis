#!/usr/bin/env python3
"""Seed six global banks into PostgreSQL."""

from app.db.database import SessionLocal
from app.db.repositories.financial_repos import BankRepository


def main() -> None:
    db = SessionLocal()
    try:
        created = BankRepository(db).seed_defaults()
        print(f"Seeded banks (new rows): {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
