from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    pass


class PeriodType(str, enum.Enum):
    QUARTER = "QUARTER"
    ANNUAL = "ANNUAL"


class MaterialityStatus(str, enum.Enum):
    MATERIAL = "MATERIAL"
    NOT_MATERIAL = "NOT_MATERIAL"
    UNDEFINED = "UNDEFINED"


class ValidationStatus(str, enum.Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    country: Mapped[str] = mapped_column(String(64), nullable=False, default="US")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    financial_statements: Mapped[list[FinancialStatement]] = relationship(back_populates="bank")
    flux_analyses: Mapped[list[FluxAnalysis]] = relationship(back_populates="bank")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "bank_id",
            "period",
            "normalized_metric",
            name="uq_financial_bank_period_metric",
        ),
        Index("ix_financial_bank_period", "bank_id", "period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String(32), nullable=False)
    period_type: Mapped[PeriodType] = mapped_column(Enum(PeriodType), nullable=False)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True)
    fiscal_quarter: Mapped[int | None] = mapped_column(nullable=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_metric: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bank: Mapped[Bank] = relationship(back_populates="financial_statements")


class FluxAnalysis(Base):
    __tablename__ = "flux_analyses"
    __table_args__ = (
        UniqueConstraint(
            "bank_id",
            "current_period",
            "previous_period",
            "metric_name",
            name="uq_flux_bank_periods_metric",
        ),
        Index("ix_flux_materiality", "materiality_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id", ondelete="CASCADE"), nullable=False)
    current_period: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_period: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_change_defined: Mapped[bool] = mapped_column(default=True)
    materiality_status: Mapped[MaterialityStatus] = mapped_column(
        Enum(MaterialityStatus), nullable=False, default=MaterialityStatus.UNDEFINED
    )
    materiality_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bank: Mapped[Bank] = relationship(back_populates="flux_analyses")
    explanations: Mapped[list[Explanation]] = relationship(back_populates="flux")
    approvals: Mapped[list[Approval]] = relationship(back_populates="flux")


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    flux_id: Mapped[int] = mapped_column(
        ForeignKey("flux_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generated_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus), nullable=False, default=ValidationStatus.PENDING
    )
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    flux: Mapped[FluxAnalysis] = relationship(back_populates="explanations")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    flux_id: Mapped[int] = mapped_column(
        ForeignKey("flux_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING
    )
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    flux: Mapped[FluxAnalysis] = relationship(back_populates="approvals")
