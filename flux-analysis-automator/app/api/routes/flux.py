from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories.financial_repos import FluxRepository
from app.schemas.common import FluxOut
from app.services.ingestion_service import FluxService

router = APIRouter(prefix="/flux", tags=["flux"])


def _serialize(flux) -> FluxOut:
    return FluxOut(
        id=flux.id,
        bank_id=flux.bank_id,
        bank_name=flux.bank.name if flux.bank else None,
        ticker=flux.bank.ticker if flux.bank else None,
        current_period=flux.current_period,
        previous_period=flux.previous_period,
        metric_name=flux.metric_name,
        previous_value=flux.previous_value,
        current_value=flux.current_value,
        absolute_change=flux.absolute_change,
        percentage_change=flux.percentage_change,
        percentage_change_defined=flux.percentage_change_defined,
        materiality_status=flux.materiality_status.value,
        materiality_reason=flux.materiality_reason,
    )


@router.post("/run")
def run_flux(db: Session = Depends(get_db)):
    return FluxService(db).run()


@router.get("", response_model=list[FluxOut])
def list_flux(
    bank_id: int | None = None,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    rows = FluxRepository(db).list_flux(bank_id=bank_id, limit=limit)
    return [_serialize(r) for r in rows]


@router.get("/material", response_model=list[FluxOut])
def list_material_flux(
    bank_id: int | None = None,
    db: Session = Depends(get_db),
):
    rows = FluxRepository(db).list_flux(bank_id=bank_id, material_only=True, limit=2000)
    return [_serialize(r) for r in rows]


@router.get("/{flux_id}", response_model=FluxOut)
def get_flux(flux_id: int, db: Session = Depends(get_db)):
    row = FluxRepository(db).get_by_id(flux_id)
    if not row:
        raise HTTPException(status_code=404, detail="Flux not found")
    return _serialize(row)
