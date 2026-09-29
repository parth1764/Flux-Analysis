from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.ai.validators import validate_explanation_numbers
from app.db.models import (
    ApprovalStatus,
    Explanation,
    FluxAnalysis,
    MaterialityStatus,
    ValidationStatus,
)
from app.db.repositories.financial_repos import ApprovalRepository, ExplanationRepository, FluxRepository

logger = logging.getLogger(__name__)


class ExplanationService:
    def __init__(self, db: Session):
        self.db = db
        self.flux_repo = FluxRepository(db)
        self.explanations = ExplanationRepository(db)
        self.approvals = ApprovalRepository(db)
        self.llm = LLMClient()

    def run_for_material_flux(self) -> dict[str, int]:
        material = self.flux_repo.list_flux(material_only=True, limit=1000)
        generated = 0
        for flux in material:
            if flux.explanations:
                continue
            self._generate_one(flux)
            generated += 1
        return {"explanations_generated": generated}

    def _generate_one(self, flux: FluxAnalysis) -> Explanation:
        bank_name = flux.bank.name if flux.bank else "Unknown"
        context = {
            "bank": bank_name,
            "metric": flux.metric_name,
            "previous_period": flux.previous_period,
            "previous_value": flux.previous_value,
            "current_period": flux.current_period,
            "current_value": flux.current_value,
            "absolute_change": flux.absolute_change,
            "percentage_change": flux.percentage_change,
        }
        payload, model_name, prompt_version = self.llm.generate_explanation(context)
        narrative = payload.get("explanation", "")
        validation_ok, errors = validate_explanation_numbers(
            narrative,
            allowed_values=[v for v in [flux.previous_value, flux.current_value, flux.absolute_change] if v is not None],
            allowed_percentages=[flux.percentage_change] if flux.percentage_change is not None else [],
        )
        status = ValidationStatus.PASSED if validation_ok else ValidationStatus.FAILED
        row = Explanation(
            flux_id=flux.id,
            generated_explanation=narrative,
            structured_payload=json.dumps(payload),
            model_name=model_name,
            prompt_version=prompt_version,
            validation_status=status,
            validation_errors="; ".join(errors) if errors else None,
        )
        saved = self.explanations.create(row)
        self.approvals.ensure_pending_for_flux(flux.id)
        logger.info("Explanation %s validation=%s", saved.id, status.value)
        return saved


class ValidationService:
    @staticmethod
    def revalidate(explanation: Explanation, flux: FluxAnalysis) -> tuple[ValidationStatus, list[str]]:
        ok, errors = validate_explanation_numbers(
            explanation.generated_explanation,
            allowed_values=[v for v in [flux.previous_value, flux.current_value, flux.absolute_change] if v is not None],
            allowed_percentages=[flux.percentage_change] if flux.percentage_change is not None else [],
        )
        return (ValidationStatus.PASSED if ok else ValidationStatus.FAILED), errors


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db
        self.explanations = ExplanationRepository(db)
        self.approvals = ApprovalRepository(db)

    def approve(self, explanation_id: int, reviewer: str, comment: str | None) -> dict[str, Any]:
        expl = self.explanations.get_by_id(explanation_id)
        if not expl:
            raise ValueError("Explanation not found")
        if expl.validation_status != ValidationStatus.PASSED:
            raise ValueError("Cannot approve explanation that failed validation")
        approval = self.approvals.update_status(expl.flux_id, ApprovalStatus.APPROVED, reviewer, comment)
        return {"explanation_id": explanation_id, "approval_status": approval.status.value}

    def reject(self, explanation_id: int, reviewer: str, comment: str | None) -> dict[str, Any]:
        expl = self.explanations.get_by_id(explanation_id)
        if not expl:
            raise ValueError("Explanation not found")
        approval = self.approvals.update_status(expl.flux_id, ApprovalStatus.REJECTED, reviewer, comment)
        return {"explanation_id": explanation_id, "approval_status": approval.status.value}
