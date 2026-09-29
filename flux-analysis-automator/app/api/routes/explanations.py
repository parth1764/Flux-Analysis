from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ApprovalStatus
from app.db.repositories.financial_repos import ApprovalRepository, ExplanationRepository
from app.schemas.common import ApprovalAction, ExplanationOut
from app.services.explanation_service import ApprovalService, ExplanationService

router = APIRouter(prefix="/explanations", tags=["explanations"])


def _serialize(expl, db: Session) -> ExplanationOut:
    approval = ApprovalRepository(db).get_for_flux(expl.flux_id)
    return ExplanationOut(
        id=expl.id,
        flux_id=expl.flux_id,
        generated_explanation=expl.generated_explanation,
        model_name=expl.model_name,
        validation_status=expl.validation_status.value,
        validation_errors=expl.validation_errors,
        approval_status=approval.status.value if approval else ApprovalStatus.PENDING.value,
    )


@router.post("/generate")
def generate_explanations(db: Session = Depends(get_db)):
    return ExplanationService(db).run_for_material_flux()


@router.get("", response_model=list[ExplanationOut])
def list_explanations(db: Session = Depends(get_db)):
    rows = ExplanationRepository(db).list_all()
    return [_serialize(r, db) for r in rows]


@router.get("/pending", response_model=list[ExplanationOut])
def pending_explanations(db: Session = Depends(get_db)):
    rows = ExplanationRepository(db).list_all(limit=500)
    pending = []
    for r in rows:
        approval = ApprovalRepository(db).get_for_flux(r.flux_id)
        if approval and approval.status == ApprovalStatus.PENDING:
            pending.append(_serialize(r, db))
    return pending


@router.post("/{explanation_id}/approve")
def approve_explanation(explanation_id: int, body: ApprovalAction, db: Session = Depends(get_db)):
    try:
        return ApprovalService(db).approve(explanation_id, body.reviewer, body.comment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{explanation_id}/reject")
def reject_explanation(explanation_id: int, body: ApprovalAction, db: Session = Depends(get_db)):
    try:
        return ApprovalService(db).reject(explanation_id, body.reviewer, body.comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
