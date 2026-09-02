"""PostgreSQL integration verification suite.

Executes real PostgreSQL tests when a live PostgreSQL instance is available via
TEST_POSTGRES_URL or DATABASE_URL environment variables.

If PostgreSQL is not reachable or credentials are not configured, tests are explicitly
skipped with a clear diagnostic notice, ensuring CI and local portability while
providing a genuine PostgreSQL verification path.
"""
import os
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

from app.db.models import Base, Company, AnalysisSnapshot, ResearchReportRecord, ResearchSourceRecord
from app.db.repositories import CompanyRepository, AnalysisRepository, ResearchRepository


def get_postgres_url() -> str | None:
    """Returns PostgreSQL connection URL from environment if configured."""
    for key in ("TEST_POSTGRES_URL", "DATABASE_URL"):
        url = os.environ.get(key, "").strip()
        if url.startswith("postgresql"):
            return url
    return None


@pytest.fixture(scope="module")
def postgres_engine():
    """
    Connects to PostgreSQL instance. Skips test module if PostgreSQL is unavailable.
    """
    pg_url = get_postgres_url()
    if not pg_url:
        pytest.skip(
            "PostgreSQL integration test skipped: No PostgreSQL URL configured. "
            "Set TEST_POSTGRES_URL or DATABASE_URL (e.g. postgresql+psycopg://user:pass@localhost:5432/dbname) "
            "to run live PostgreSQL integration tests."
        )

    try:
        engine = create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(
            f"PostgreSQL integration test skipped: Unable to connect to PostgreSQL at '{pg_url}'. "
            f"Error: {exc}. Please verify PostgreSQL credentials."
        )

    yield engine
    engine.dispose()


@pytest.fixture
def postgres_session(postgres_engine):
    """Provides an isolated session on PostgreSQL, cleaned up after each test."""
    # Ensure tables exist via Alembic / metadata
    Base.metadata.create_all(bind=postgres_engine)
    SessionClass = sessionmaker(bind=postgres_engine)
    session = SessionClass()
    try:
        yield session
    finally:
        session.close()
        # Clean up data after test
        with postgres_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE companies CASCADE"))


def test_postgres_alembic_migration_and_schema(postgres_engine):
    """Verifies that Alembic migration applies cleanly against a real PostgreSQL instance."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ini_path = os.path.join(base_dir, "alembic.ini")
    cfg = Config(ini_path)
    cfg.set_main_option("sqlalchemy.url", get_postgres_url())

    # Run upgrade head via Alembic
    command.upgrade(cfg, "head")

    inspector = inspect(postgres_engine)
    tables = inspector.get_table_names()
    assert "companies" in tables
    assert "analysis_snapshots" in tables
    assert "research_reports" in tables
    assert "research_sources" in tables

    # Verify JSONB column type in PostgreSQL
    snapshot_cols = {c["name"]: str(c["type"]) for c in inspector.get_columns("analysis_snapshots")}
    assert "JSONB" in snapshot_cols.get("payload", "").upper()


def test_postgres_company_and_snapshot_persistence(postgres_session):
    """Verifies company upsert and analysis snapshot persistence in real PostgreSQL."""
    comp_repo = CompanyRepository(postgres_session)
    analysis_repo = AnalysisRepository(postgres_session)

    company = comp_repo.upsert(
        ticker="PG_AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
    )
    assert company.id is not None

    snapshot = analysis_repo.create_snapshot(
        company_id=company.id,
        dcf_status="calculated",
        health_rating="Strong",
        payload={"ticker": "PG_AAPL", "growth": {"revenue_growth_yoy": 0.08}},
        analyzed_at=datetime.now(timezone.utc),
        current_share_price=225.0,
        implied_share_price=215.0,
        upside_downside_pct=-4.44,
        wacc=0.085,
    )
    assert snapshot.id is not None
    assert float(snapshot.current_share_price) == 225.0

    # Query back using repository
    history = analysis_repo.list_by_ticker("PG_AAPL")
    assert len(history) == 1
    assert history[0].dcf_status == "calculated"


def test_postgres_cascade_delete(postgres_session):
    """Verifies foreign key cascade deletion in real PostgreSQL."""
    comp_repo = CompanyRepository(postgres_session)
    analysis_repo = AnalysisRepository(postgres_session)
    research_repo = ResearchRepository(postgres_session)

    company = comp_repo.upsert(ticker="PG_CASCADE", company_name="Cascade Corp.")
    analysis_repo.create_snapshot(company.id, "calculated", "Strong", {"metric": 1})
    research_repo.create_report(
        company.id,
        payload={"thesis": "Cascade test"},
        sources=[{"provider": "SEC", "title": "10-K", "source_type": "filing"}],
    )

    assert len(analysis_repo.list_by_ticker("PG_CASCADE")) == 1
    assert len(research_repo.list_by_ticker("PG_CASCADE")) == 1

    # Delete company in PostgreSQL
    postgres_session.delete(company)
    postgres_session.commit()

    # Verify related records were cascaded
    assert len(analysis_repo.list_by_ticker("PG_CASCADE")) == 0
    assert len(research_repo.list_by_ticker("PG_CASCADE")) == 0