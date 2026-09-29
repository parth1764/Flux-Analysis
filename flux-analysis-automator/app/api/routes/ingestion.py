from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.explanation_service import ExplanationService
from app.services.ingestion_service import FluxService, IngestionService

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/run")
def ingestion_run(db: Session = Depends(get_db)):
    return IngestionService(db).run()


@router.post("/pipeline")
def full_pipeline(db: Session = Depends(get_db)):
    ingest = IngestionService(db).run()
    flux = FluxService(db).run()
    explanations = ExplanationService(db).run_for_material_flux()
    return {"ingestion": ingest, "flux": flux, "explanations": explanations}
