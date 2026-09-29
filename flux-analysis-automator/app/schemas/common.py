from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BankOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ticker: str
    country: str
    currency: str


class FinancialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_id: int
    period: str
    period_type: str
    normalized_metric: str
    metric_name: str
    value: float
    currency: str
    source: str
    source_url: str | None


class FluxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_id: int
    bank_name: str | None = None
    ticker: str | None = None
    current_period: str
    previous_period: str
    metric_name: str
    previous_value: float | None
    current_value: float | None
    absolute_change: float | None
    percentage_change: float | None
    percentage_change_defined: bool
    materiality_status: str
    materiality_reason: str | None


class ExplanationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    flux_id: int
    generated_explanation: str
    model_name: str | None
    validation_status: str
    validation_errors: str | None
    approval_status: str | None = None


class ApprovalAction(BaseModel):
    reviewer: str = "analyst@example.com"
    comment: str | None = None


class PaginatedMeta(BaseModel):
    total: int
    limit: int
    offset: int
