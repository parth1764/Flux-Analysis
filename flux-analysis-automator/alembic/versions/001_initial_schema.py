"""Initial schema — banks, financials, flux, explanations, approvals."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> postgresql.ENUM:
    e = postgresql.ENUM(*values, name=name)
    e.create(op.get_bind(), checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    op.create_table(
        "banks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index("ix_banks_ticker", "banks", ["ticker"], unique=False)

    period_type = _enum("periodtype", "QUARTER", "ANNUAL")

    op.create_table(
        "financial_statements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=32), nullable=False),
        sa.Column("period_type", period_type, nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("fiscal_quarter", sa.Integer(), nullable=True),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_metric", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["banks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id", "period", "normalized_metric", name="uq_financial_bank_period_metric"),
    )
    op.create_index("ix_financial_bank_period", "financial_statements", ["bank_id", "period"], unique=False)
    op.create_index("ix_financial_statements_normalized_metric", "financial_statements", ["normalized_metric"], unique=False)

    materiality = _enum("materialitystatus", "MATERIAL", "NOT_MATERIAL", "UNDEFINED")

    op.create_table(
        "flux_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("current_period", sa.String(length=32), nullable=False),
        sa.Column("previous_period", sa.String(length=32), nullable=False),
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("previous_value", sa.Float(), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("absolute_change", sa.Float(), nullable=True),
        sa.Column("percentage_change", sa.Float(), nullable=True),
        sa.Column("percentage_change_defined", sa.Boolean(), nullable=False),
        sa.Column("materiality_status", materiality, nullable=False),
        sa.Column("materiality_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["banks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "bank_id", "current_period", "previous_period", "metric_name", name="uq_flux_bank_periods_metric"
        ),
    )
    op.create_index("ix_flux_materiality", "flux_analyses", ["materiality_status"], unique=False)

    validation = _enum("validationstatus", "PENDING", "PASSED", "FAILED")

    op.create_table(
        "explanations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("flux_id", sa.Integer(), nullable=False),
        sa.Column("generated_explanation", sa.Text(), nullable=False),
        sa.Column("structured_payload", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("validation_status", validation, nullable=False),
        sa.Column("validation_errors", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["flux_id"], ["flux_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_explanations_flux_id", "explanations", ["flux_id"], unique=False)

    approval = _enum("approvalstatus", "PENDING", "APPROVED", "REJECTED")

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("flux_id", sa.Integer(), nullable=False),
        sa.Column("status", approval, nullable=False),
        sa.Column("reviewer", sa.String(length=255), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["flux_id"], ["flux_analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approvals_flux_id", "approvals", ["flux_id"], unique=False)


def downgrade() -> None:
    op.drop_table("approvals")
    op.drop_table("explanations")
    op.drop_table("flux_analyses")
    op.drop_table("financial_statements")
    op.drop_table("banks")
    for name in ("approvalstatus", "validationstatus", "materialitystatus", "periodtype"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
