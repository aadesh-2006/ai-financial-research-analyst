"""Initial database schema for financial research persistence.

Revision ID: 001
Revises: None
Create Date: 2026-09-02 19:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    # 1. companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=150), nullable=True),
        sa.Column("currency", sa.String(length=10), server_default="USD", nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"], unique=True)

    # 2. analysis_snapshots table
    op.create_table(
        "analysis_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_share_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("implied_share_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("upside_downside_pct", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("wacc", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("dcf_status", sa.String(length=50), nullable=False),
        sa.Column("health_rating", sa.String(length=50), nullable=False),
        sa.Column("payload", JSON_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_snapshots_company_id", "analysis_snapshots", ["company_id"])
    op.create_index("ix_analysis_snapshots_analyzed_at", "analysis_snapshots", ["analyzed_at"])

    # 3. research_reports table
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence_level", sa.String(length=50), nullable=True),
        sa.Column("valuation_signal", sa.String(length=100), nullable=True),
        sa.Column("payload", JSON_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_reports_company_id", "research_reports", ["company_id"])
    op.create_index("ix_research_reports_generated_at", "research_reports", ["generated_at"])

    # 4. research_sources table
    op.create_table(
        "research_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("research_report_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.String(length=100), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["research_report_id"], ["research_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_sources_report_id", "research_sources", ["research_report_id"])


def downgrade() -> None:
    op.drop_table("research_sources")
    op.drop_table("research_reports")
    op.drop_table("analysis_snapshots")
    op.drop_table("companies")