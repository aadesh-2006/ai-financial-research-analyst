"""SQLAlchemy 2.x declarative models for financial analysis and research persistence."""
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    Numeric,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

# Dialect-portable JSON type: JSONB on PostgreSQL, JSON on SQLite
JSON_TYPE = JSON().with_variant(postgresql.JSONB, "postgresql")


class Company(Base):
    """Normalized company identity and profile."""
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    analysis_snapshots: Mapped[List["AnalysisSnapshot"]] = relationship(
        "AnalysisSnapshot",
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisSnapshot.analyzed_at)",
    )
    research_reports: Mapped[List["ResearchReportRecord"]] = relationship(
        "ResearchReportRecord",
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="desc(ResearchReportRecord.generated_at)",
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, ticker={self.ticker}, name={self.company_name})>"


class AnalysisSnapshot(Base):
    """Deterministic financial and DCF analysis snapshot."""
    __tablename__ = "analysis_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    current_share_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    implied_share_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    upside_downside_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    wacc: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), nullable=True)
    dcf_status: Mapped[str] = mapped_column(String(50), nullable=False)
    health_rating: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="analysis_snapshots")

    def __repr__(self) -> str:
        return f"<AnalysisSnapshot(id={self.id}, company_id={self.company_id}, status={self.dcf_status})>"


class ResearchReportRecord(Base):
    """Grounded AI investment research memo record."""
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    confidence_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    valuation_signal: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payload: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="research_reports")
    sources: Mapped[List["ResearchSourceRecord"]] = relationship(
        "ResearchSourceRecord",
        back_populates="report",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ResearchReportRecord(id={self.id}, company_id={self.company_id}, confidence={self.confidence_level})>"


class ResearchSourceRecord(Base):
    """Normalized research citation source associated with an AI memo."""
    __tablename__ = "research_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    research_report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("research_reports.id", ondelete="CASCADE"), index=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    report: Mapped["ResearchReportRecord"] = relationship("ResearchReportRecord", back_populates="sources")

    def __repr__(self) -> str:
        return f"<ResearchSourceRecord(id={self.id}, provider={self.provider}, title={self.title[:30]})>"