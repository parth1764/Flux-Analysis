#!/usr/bin/env python3
"""
Full pipeline:
INGEST → FLUX → MATERIALITY (in flux) → EXPLANATIONS → VALIDATE
(Does not auto-approve.)
"""

from app.db.database import SessionLocal
from app.services.explanation_service import ExplanationService
from app.services.ingestion_service import FluxService, IngestionService


def main() -> None:
    db = SessionLocal()
    try:
        ingest = IngestionService(db).run()
        flux = FluxService(db).run()
        explanations = ExplanationService(db).run_for_material_flux()
        print({"ingestion": ingest, "flux": flux, "explanations": explanations})
    finally:
        db.close()


if __name__ == "__main__":
    main()
