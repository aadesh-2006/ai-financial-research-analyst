"""Unit tests for SQLAlchemy 2.x database models, relationships, and repositories."""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base, Company, AnalysisSnapshot, ResearchReportRecord, ResearchSourceRecord
from app.db.repositories import CompanyRepository, AnalysisRepository, ResearchRepository


@pytest.fixture
def db_session() -> Session:
    """Fixture providing an isolated, in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_database_connection_and_table_creation(db_session: Session):
    """Verifies that all tables and constraints initialize cleanly in an empty database."""
    tables = Base.metadata.tables.keys()
    assert "companies" in tables
    assert "analysis_snapshots" in tables
    assert "research_reports" in tables
    assert "research_sources" in tables


def test_company_upsert_insert_and_update(db_session: Session):
    """Verifies CompanyRepository creates new companies and safely updates existing records."""
    repo = CompanyRepository(db_session)

    # 1. Insert new company
    comp1 = repo.upsert(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        currency="USD",
        website="https://apple.com",
        description="Initial description",
    )
    assert comp1.id is not None
    assert comp1.ticker == "AAPL"
    assert comp1.sector == "Technology"

    # 2. Update existing company with new profile details
    comp2 = repo.upsert(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        website="https://www.apple.com",
        description="Updated hardware and software ecosystem description.",
    )
    assert comp2.id == comp1.id
    assert comp2.website == "https://www.apple.com"
    assert comp2.description == "Updated hardware and software ecosystem description."

    # Total company records for AAPL remains exactly 1
    stmt = select(Company).where(Company.ticker == "AAPL")
    results = list(db_session.scalars(stmt).all())
    assert len(results) == 1


def test_analysis_snapshot_persistence_and_relationship(db_session: Session):
    """Verifies AnalysisRepository persists snapshots and links correctly to Company."""
    comp_repo = CompanyRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)

    comp = comp_repo.upsert(ticker="MSFT", company_name="Microsoft Corp.")
    payload = {"ticker": "MSFT", "health": {"overall": "Strong"}}

    snapshot = analysis_repo.create_snapshot(
        company_id=comp.id,
        dcf_status="calculated",
        health_rating="Strong",
        payload=payload,
        analyzed_at=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
        current_share_price=415.50,
        implied_share_price=430.00,
        upside_downside_pct=3.49,
        wacc=0.082,
    )

    assert snapshot.id is not None
    assert snapshot.company_id == comp.id
    assert float(snapshot.current_share_price) == 415.50
    assert float(snapshot.implied_share_price) == 430.00
    assert snapshot.dcf_status == "calculated"
    assert snapshot.company.ticker == "MSFT"


def test_multiple_snapshots_ordered_by_most_recent(db_session: Session):
    """Verifies history query returns snapshots in descending chronological order."""
    comp_repo = CompanyRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)

    comp = comp_repo.upsert(ticker="NVDA", company_name="Nvidia Corp.")

    # Insert 3 snapshots across time
    t1 = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    analysis_repo.create_snapshot(comp.id, "calculated", "Strong", {"v": 1}, analyzed_at=t1, current_share_price=100.0)
    analysis_repo.create_snapshot(comp.id, "calculated", "Strong", {"v": 2}, analyzed_at=t2, current_share_price=110.0)
    analysis_repo.create_snapshot(comp.id, "calculated", "Strong", {"v": 3}, analyzed_at=t3, current_share_price=120.0)

    history = analysis_repo.list_by_ticker("NVDA")
    assert len(history) == 3
    assert float(history[0].current_share_price) == 120.0  # Most recent first
    assert float(history[1].current_share_price) == 110.0
    assert float(history[2].current_share_price) == 100.0

    latest = analysis_repo.get_latest_by_ticker("NVDA")
    assert latest is not None
    assert float(latest.current_share_price) == 120.0


def test_research_report_persistence_with_sources(db_session: Session):
    """Verifies ResearchRepository persists research memos with foreign-key source citations."""
    comp_repo = CompanyRepository(db_session)
    research_repo = ResearchRepository(db_session)

    comp = comp_repo.upsert(ticker="AAPL", company_name="Apple Inc.")
    payload = {"executive_summary": "Strong cash generation.", "thesis": "Ecosystem lock-in."}
    sources = [
        {"provider": "SEC_EDGAR", "title": "Form 10-K", "url": "https://sec.gov", "source_type": "filing"},
        {"provider": "YAHOO_FINANCE", "title": "Market Quote", "url": "https://finance.yahoo.com", "source_type": "market_data"},
    ]

    report = research_repo.create_report(
        company_id=comp.id,
        payload=payload,
        sources=sources,
        confidence_level="High",
        valuation_signal="Fairly Valued",
        generated_at=datetime(2026, 9, 1, 15, 30, tzinfo=timezone.utc),
    )

    assert report.id is not None
    assert report.confidence_level == "High"
    assert len(report.sources) == 2
    assert report.sources[0].provider in ["SEC_EDGAR", "YAHOO_FINANCE"]
    assert report.sources[0].research_report_id == report.id


def test_cascade_delete_company_removes_snapshots_and_reports(db_session: Session):
    """Verifies that removing a company cascades to delete its snapshots, reports, and source citations."""
    comp_repo = CompanyRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)
    research_repo = ResearchRepository(db_session)

    comp = comp_repo.upsert(ticker="TEMP", company_name="Temporary Corp.")
    analysis_repo.create_snapshot(comp.id, "calculated", "Strong", {})
    research_repo.create_report(
        comp.id,
        payload={},
        sources=[{"provider": "SEC", "title": "Filing", "source_type": "filing"}],
    )

    # Confirm created
    assert len(analysis_repo.list_by_ticker("TEMP")) == 1
    assert len(research_repo.list_by_ticker("TEMP")) == 1

    # Delete company
    db_session.delete(comp)
    db_session.commit()

    # All related records should be cascaded
    assert len(db_session.scalars(select(AnalysisSnapshot)).all()) == 0
    assert len(db_session.scalars(select(ResearchReportRecord)).all()) == 0
    assert len(db_session.scalars(select(ResearchSourceRecord)).all()) == 0