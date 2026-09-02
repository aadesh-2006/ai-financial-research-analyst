"""Alembic migration lifecycle and reproducibility tests.

Verifies schema creation, rollback, and re-application purely through Alembic
CLI / programmatic command API rather than Base.metadata.create_all().
"""
import os
import tempfile
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.fixture
def temp_db_url():
    """Creates a temporary SQLite file database path for testing migrations from scratch."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    
    db_url = f"sqlite:///{temp_path.replace(os.sep, '/')}"
    yield db_url
    
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


def get_alembic_config(db_url: str) -> Config:
    """Builds an Alembic Config pointing to backend/alembic.ini and overriding the DB URL."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ini_path = os.path.join(base_dir, "alembic.ini")
    cfg = Config(ini_path)
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_alembic_migration_from_empty_database(temp_db_url: str):
    """
    Verifies that Alembic successfully upgrades an empty database to 'head'
    without using Base.metadata.create_all().
    """
    cfg = get_alembic_config(temp_db_url)
    
    # 1. Run Alembic upgrade to head from scratch
    command.upgrade(cfg, "head")

    # 2. Inspect created database schema directly from database engine
    engine = create_engine(temp_db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Confirm all 4 normalized domain tables plus alembic_version exist
    assert "alembic_version" in tables
    assert "companies" in tables
    assert "analysis_snapshots" in tables
    assert "research_reports" in tables
    assert "research_sources" in tables

    # 3. Verify company columns and unique index
    company_cols = [c["name"] for c in inspector.get_columns("companies")]
    assert "id" in company_cols
    assert "ticker" in company_cols
    assert "company_name" in company_cols
    assert "sector" in company_cols

    indexes = inspector.get_indexes("companies")
    ticker_index = next((idx for idx in indexes if idx["name"] == "ix_companies_ticker"), None)
    assert ticker_index is not None
    assert ticker_index.get("unique") == 1 or ticker_index.get("unique") is True

    # 4. Verify foreign keys created by Alembic
    snapshot_fks = inspector.get_foreign_keys("analysis_snapshots")
    assert any(fk["referred_table"] == "companies" for fk in snapshot_fks)

    report_fks = inspector.get_foreign_keys("research_reports")
    assert any(fk["referred_table"] == "companies" for fk in report_fks)

    source_fks = inspector.get_foreign_keys("research_sources")
    assert any(fk["referred_table"] == "research_reports" for fk in source_fks)


def test_alembic_migration_downgrade_and_reupgrade(temp_db_url: str):
    """
    Verifies that Alembic migrations can be cleanly rolled back to 'base'
    and reapplied to 'head' without error.
    """
    cfg = get_alembic_config(temp_db_url)

    # Upgrade to head
    command.upgrade(cfg, "head")
    engine = create_engine(temp_db_url)
    assert "companies" in inspect(engine).get_table_names()

    # Downgrade to base (rolls back all tables)
    command.downgrade(cfg, "base")
    tables_after_downgrade = inspect(engine).get_table_names()
    assert "companies" not in tables_after_downgrade
    assert "analysis_snapshots" not in tables_after_downgrade
    assert "research_reports" not in tables_after_downgrade
    assert "research_sources" not in tables_after_downgrade

    # Re-upgrade to head cleanly
    command.upgrade(cfg, "head")
    tables_after_reupgrade = inspect(engine).get_table_names()
    assert "companies" in tables_after_reupgrade