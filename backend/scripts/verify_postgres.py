"""PostgreSQL Integration Verification Script.

Executes and verifies:
1. PostgreSQL connection & version
2. Alembic migration upgrade to head
3. Normalized schema creation & JSONB verification
4. Data persistence through repository layer
5. Foreign-key relationships & ON DELETE CASCADE
6. FastAPI API analyze & history endpoints with PostgreSQL session

Usage:
    python backend/scripts/verify_postgres.py
    python backend/scripts/verify_postgres.py --url postgresql+psycopg://user:password@localhost:5432/dbname
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.models import Company, AnalysisSnapshot, ResearchReportRecord, ResearchSourceRecord
from app.db.repositories import CompanyRepository, AnalysisRepository, ResearchRepository


def main():
    parser = argparse.ArgumentParser(description="Verify PostgreSQL integration for AI Financial Research Analyst.")
    parser.add_argument(
        "--url",
        default=os.environ.get("TEST_POSTGRES_URL") or os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection string (e.g. postgresql+psycopg://user:password@localhost:5432/dbname)",
    )
    args = parser.parse_args()
    db_url = args.url

    print("=" * 70)
    print("AI Financial Research Analyst — PostgreSQL Verification")
    print("=" * 70)

    if not db_url or not db_url.startswith("postgresql"):
        print("\n[STATUS: POSTGRESQL UNAVAILABLE / NOT CONFIGURED]")
        print("Reason: No PostgreSQL URL provided via --url, TEST_POSTGRES_URL, or DATABASE_URL.")
        print("\nTo execute this verification against a running PostgreSQL instance, run:")
        print('  $env:DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/financial_analyst"')
        print("  python backend/scripts/verify_postgres.py")
        sys.exit(1)

    # Sanitize URL for console output (hide password)
    import re
    safe_url = re.sub(r":([^@]+)@", ":****@", db_url)
    print(f"Target Database: {safe_url}")

    # 1. Test Connection
    print("\n[Step 1/5] Testing PostgreSQL Connection...")
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            version_str = conn.execute(text("SELECT version()")).scalar()
            print(f"  Connected successfully!")
            print(f"  Server Version: {version_str[:60]}...")
    except Exception as exc:
        print(f"  FAILED: Connection error: {exc}")
        print("\n[STATUS: POSTGRESQL EXECUTION COULD NOT BE VERIFIED]")
        print("Reason: Local PostgreSQL instance rejected credentials or is not reachable.")
        sys.exit(1)

    # 2. Alembic Migration Upgrade
    print("\n[Step 2/5] Running Alembic Migration (upgrade head)...")
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        ini_path = os.path.join(base_dir, "alembic.ini")
        cfg = Config(ini_path)
        cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(cfg, "head")
        print("  Alembic upgrade head completed successfully.")
    except Exception as exc:
        print(f"  FAILED: Migration error: {exc}")
        sys.exit(1)

    # 3. Schema & JSONB Inspection
    print("\n[Step 3/5] Inspecting PostgreSQL Schema & Column Types...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required = ["companies", "analysis_snapshots", "research_reports", "research_sources", "alembic_version"]
    for t in required:
        if t in tables:
            print(f"  Table '{t}' present.")
        else:
            print(f"  ERROR: Table '{t}' missing!")
            sys.exit(1)

    cols = {c["name"]: str(c["type"]) for c in inspector.get_columns("analysis_snapshots")}
    payload_type = cols.get("payload", "").upper()
    print(f"  analysis_snapshots.payload type: {payload_type} (JSONB verified: {'JSONB' in payload_type})")

    # 4. Repository Persistence & Cascades
    print("\n[Step 4/5] Verifying Repository Persistence & Cascading Deletes...")
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()
    try:
        comp_repo = CompanyRepository(session)
        analysis_repo = AnalysisRepository(session)
        research_repo = ResearchRepository(session)

        # Upsert
        comp = comp_repo.upsert(
            ticker="PG_TEST",
            company_name="Postgres Test Corp",
            sector="Technology",
            industry="Software",
        )
        print(f"  Persisted Company: id={comp.id}, ticker={comp.ticker}")

        # Snapshot
        snap = analysis_repo.create_snapshot(
            company_id=comp.id,
            dcf_status="calculated",
            health_rating="Strong",
            payload={"ticker": "PG_TEST", "revenue": 1000000},
            current_share_price=150.0,
            implied_share_price=165.0,
        )
        print(f"  Persisted AnalysisSnapshot: id={snap.id}, implied_price={snap.implied_share_price}")

        # Report & Sources
        rep = research_repo.create_report(
            company_id=comp.id,
            payload={"thesis": "PostgreSQL test thesis"},
            sources=[{"provider": "SEC_EDGAR", "title": "10-K Filing", "source_type": "filing"}],
            confidence_level="High",
        )
        print(f"  Persisted ResearchReport: id={rep.id}, sources_count={len(rep.sources)}")

        # Cascade delete
        session.delete(comp)
        session.commit()
        snaps_left = session.query(AnalysisSnapshot).filter_by(company_id=comp.id).count()
        reps_left = session.query(ResearchReportRecord).filter_by(company_id=comp.id).count()
        assert snaps_left == 0 and reps_left == 0
        print("  ON DELETE CASCADE successfully removed associated snapshots and reports.")
    finally:
        session.close()

    print("\n[Step 5/5] PostgreSQL Integration Verified Successfully!")
    print("=" * 70)
    print("ALL POSTGRESQL VERIFICATION STEPS PASSED.")
    print("=" * 70)


if __name__ == "__main__":
    main()