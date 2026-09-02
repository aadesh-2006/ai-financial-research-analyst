"""Integration tests for FastAPI endpoints with PostgreSQL / database persistence."""
import pytest
from datetime import datetime
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.db.models import Base, Company, AnalysisSnapshot, ResearchReportRecord, ResearchSourceRecord
from app.db.session import get_db
from app.main import create_app
from app.api.routes import get_orchestrator, get_financial_engine, get_research_service
from app.schemas.financial import CompanyData, CompanyProfile, MarketData
from app.financial.schemas import FinancialAnalysis, FinancialHealth, DCFValuation
from app.research.schemas import ResearchReport, ReportConfidence, DCFInterpretation


@pytest.fixture
def test_db_session() -> Session:
    """Fixture creating an isolated in-memory database for API integration tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client_with_db(test_db_session: Session):
    """FastAPI TestClient with database session overridden with test_db_session."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db_session

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


def test_api_analyze_persists_to_database(client_with_db: TestClient, test_db_session: Session):
    """Verifies that POST /api/analyze persists the company and snapshot into the database."""
    # Setup mock data and engine
    mock_profile = CompanyProfile(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        currency="USD",
        website="https://www.apple.com",
        description="Consumer electronics.",
    )
    mock_data = CompanyData(
        ticker="AAPL",
        company_profile=mock_profile,
        annual_financials=[],
        market_data=MarketData(current_price=220.0),
        news=[],
    )
    mock_analysis = FinancialAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        currency="USD",
        growth={"revenue_growth_yoy": 0.08, "revenue_cagr_3yr": 0.06, "net_income_growth_yoy": 0.05, "fcf_growth_yoy": 0.07, "revenue_growth_series": [], "net_income_growth_series": [], "fcf_growth_series": []},
        profitability={"gross_margin": 0.45, "operating_margin": 0.30, "net_margin": 0.25, "roe": 1.6, "roic": 0.4},
        leverage={"debt_to_equity": 1.75, "debt_to_ebitda": 0.85, "interest_coverage": 25.0, "total_debt": 105000000000.0, "stockholders_equity": 60000000000.0},
        cash_flow={"operating_cash_flow": 115000000000.0, "capex": 10000000000.0, "free_cash_flow": 105000000000.0, "fcf_margin": 0.27, "fcf_conversion": 1.05},
        valuation={"pe_ratio": 32.5, "forward_pe": 28.0, "ev_to_ebitda": 24.0, "price_to_sales": 8.5, "price_to_fcf": 31.4, "market_cap": 3300000000000.0, "enterprise_value": 3340000000000.0, "price_to_book": None},
        historical_trends=[],
        health=FinancialHealth(overall="Strong", growth_pillar="Strong", profitability_pillar="Strong", leverage_pillar="Moderate", cash_flow_pillar="Strong", key_observations=[]),
        dcf=DCFValuation(ticker="AAPL", status="calculated", current_share_price=220.0, implied_share_price=210.50, upside_downside_pct=-4.3, wacc=0.085),
    )

    mock_orch = MagicMock()
    mock_orch.get_company_data.return_value = mock_data
    mock_eng = MagicMock()
    mock_eng.analyze.return_value = mock_analysis

    client_with_db.app.dependency_overrides[get_orchestrator] = lambda: mock_orch
    client_with_db.app.dependency_overrides[get_financial_engine] = lambda: mock_eng

    res = client_with_db.post("/api/analyze", json={"ticker": "AAPL"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["ticker"] == "AAPL"
    assert data["company_name"] == "Apple Inc."

    # Assert database persistence
    company = test_db_session.query(Company).filter_by(ticker="AAPL").first()
    assert company is not None
    assert company.company_name == "Apple Inc."
    assert company.sector == "Technology"

    snapshots = test_db_session.query(AnalysisSnapshot).filter_by(company_id=company.id).all()
    assert len(snapshots) == 1
    assert float(snapshots[0].current_share_price) == 220.0
    assert float(snapshots[0].implied_share_price) == 210.50
    assert snapshots[0].dcf_status == "calculated"


def test_api_research_persists_report_and_sources(client_with_db: TestClient, test_db_session: Session):
    """Verifies that POST /api/research persists research report and sources into the database."""
    mock_profile = CompanyProfile(ticker="MSFT", name="Microsoft Corp.")
    mock_data = CompanyData(
        ticker="MSFT",
        company_profile=mock_profile,
        annual_financials=[],
        market_data=MarketData(current_price=415.0),
        news=[],
    )
    mock_analysis = FinancialAnalysis(
        ticker="MSFT",
        company_name="Microsoft Corp.",
        currency="USD",
        growth={"revenue_growth_yoy": 0.1, "revenue_cagr_3yr": 0.1, "net_income_growth_yoy": 0.1, "fcf_growth_yoy": 0.1, "revenue_growth_series": [], "net_income_growth_series": [], "fcf_growth_series": []},
        profitability={"gross_margin": 0.6, "operating_margin": 0.4, "net_margin": 0.35, "roe": 0.4, "roic": 0.3},
        leverage={"debt_to_equity": 0.5, "debt_to_ebitda": 0.6, "interest_coverage": 20.0, "total_debt": 50000000000.0, "stockholders_equity": 100000000000.0},
        cash_flow={"operating_cash_flow": 80000000000.0, "capex": 20000000000.0, "free_cash_flow": 60000000000.0, "fcf_margin": 0.25, "fcf_conversion": 0.9},
        valuation={"pe_ratio": 35.0, "forward_pe": 30.0, "ev_to_ebitda": 22.0, "price_to_sales": 10.0, "price_to_fcf": 40.0, "market_cap": 3000000000000.0, "enterprise_value": 3050000000000.0},
        historical_trends=[],
        health=FinancialHealth(overall="Strong", growth_pillar="Strong", profitability_pillar="Strong", leverage_pillar="Strong", cash_flow_pillar="Strong", key_observations=[]),
    )
    mock_report = ResearchReport(
        ticker="MSFT",
        company_name="Microsoft Corp.",
        generated_at="2026-09-02T19:00:00Z",
        executive_summary="Dominant enterprise software moat.",
        investment_thesis="Cloud and AI leadership.",
        financial_snapshot={"summary": "High margins.", "key_points": []},
        valuation_assessment={"summary": "Premium multiple.", "multiples_summary": "35x P/E", "key_points": []},
        strengths=["Azure expansion"],
        risks=["Antitrust"],
        catalysts=["Copilot monetization"],
        concerns=["Capex expansion"],
        financial_health_assessment={"summary": "Strong balance sheet.", "overall_rating": "Strong", "observations": []},
        dcf_interpretation=DCFInterpretation(summary="Baseline DCF.", valuation_signal="Fairly Valued", sensitivity_observation="Low"),
        news_and_market_context={"summary": "News summary.", "relevant_headlines": []},
        conclusion="Strong compounder.",
        confidence=ReportConfidence(level="High", rationale="Audited SEC reports."),
        limitations=[],
        sources=[{"provider": "SEC_EDGAR", "title": "10-K", "url": "https://sec.gov", "source_type": "filing"}],
        disclaimer="Disclaimer notice.",
    )

    mock_orch = MagicMock()
    mock_orch.get_company_data.return_value = mock_data
    mock_eng = MagicMock()
    mock_eng.analyze.return_value = mock_analysis
    mock_rs = MagicMock()
    mock_rs.generate_report.return_value = mock_report

    client_with_db.app.dependency_overrides[get_orchestrator] = lambda: mock_orch
    client_with_db.app.dependency_overrides[get_financial_engine] = lambda: mock_eng
    client_with_db.app.dependency_overrides[get_research_service] = lambda: mock_rs

    res = client_with_db.post("/api/research", json={"ticker": "MSFT"})
    assert res.status_code == status.HTTP_200_OK

    # Assert database records
    company = test_db_session.query(Company).filter_by(ticker="MSFT").first()
    assert company is not None

    reports = test_db_session.query(ResearchReportRecord).filter_by(company_id=company.id).all()
    assert len(reports) == 1
    assert reports[0].confidence_level == "High"
    assert reports[0].valuation_signal == "Fairly Valued"

    sources = test_db_session.query(ResearchSourceRecord).filter_by(research_report_id=reports[0].id).all()
    assert len(sources) == 1
    assert sources[0].provider == "SEC_EDGAR"


def test_api_history_endpoints(client_with_db: TestClient, test_db_session: Session):
    """Verifies GET /api/companies, /api/companies/{ticker}/analyses, and /api/companies/{ticker}/research."""
    # Preseed database with a company, snapshot, and report
    comp = Company(ticker="NVDA", company_name="Nvidia Corp.", sector="Technology", industry="Semiconductors")
    test_db_session.add(comp)
    test_db_session.commit()

    snapshot = AnalysisSnapshot(
        company_id=comp.id,
        analyzed_at=datetime(2026, 9, 1, 12, 0),
        current_share_price=120.0,
        implied_share_price=135.0,
        upside_downside_pct=12.5,
        wacc=0.09,
        dcf_status="calculated",
        health_rating="Strong",
        payload={"ticker": "NVDA"},
    )
    test_db_session.add(snapshot)

    report = ResearchReportRecord(
        company_id=comp.id,
        generated_at=datetime(2026, 9, 1, 14, 0),
        confidence_level="High",
        valuation_signal="Undervalued",
        payload={"executive_summary": "AI datacenter market leader."},
    )
    test_db_session.add(report)
    test_db_session.commit()

    # 1. GET /api/companies
    res_companies = client_with_db.get("/api/companies")
    assert res_companies.status_code == status.HTTP_200_OK
    companies_list = res_companies.json()
    assert len(companies_list) == 1
    assert companies_list[0]["ticker"] == "NVDA"
    assert companies_list[0]["latest_share_price"] == 120.0
    assert companies_list[0]["dcf_status"] == "calculated"

    # 2. GET /api/companies/NVDA/analyses
    res_analyses = client_with_db.get("/api/companies/NVDA/analyses")
    assert res_analyses.status_code == status.HTTP_200_OK
    analyses_list = res_analyses.json()
    assert len(analyses_list) == 1
    assert analyses_list[0]["ticker"] == "NVDA"
    assert analyses_list[0]["implied_share_price"] == 135.0

    # 3. GET /api/companies/NVDA/research
    res_research = client_with_db.get("/api/companies/NVDA/research")
    assert res_research.status_code == status.HTTP_200_OK
    research_list = res_research.json()
    assert len(research_list) == 1
    assert research_list[0]["ticker"] == "NVDA"
    assert research_list[0]["confidence_level"] == "High"
    assert research_list[0]["executive_summary"] == "AI datacenter market leader."

    # 4. Querying non-existent ticker returns 404 TICKER_NOT_FOUND
    res_404 = client_with_db.get("/api/companies/UNKNOWN/analyses")
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["error"]["code"] == "TICKER_NOT_FOUND"

    res_res_404 = client_with_db.get("/api/companies/UNKNOWN/research")
    assert res_res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_res_404.json()["error"]["code"] == "TICKER_NOT_FOUND"


def test_database_error_sanitization_does_not_leak_secrets(client_with_db: TestClient):
    """Verifies that database exceptions return HTTP 500 without leaking connection credentials."""
    from sqlalchemy.exc import OperationalError

    mock_repo = MagicMock()
    mock_repo.list_recent.side_effect = OperationalError(
        statement="SELECT * FROM companies",
        params={},
        orig=Exception("FATAL: password authentication failed for user 'admin_user:SuperSecretPassword123' at prod.db:5432"),
    )

    from app.api.routes import get_company_repo
    client_with_db.app.dependency_overrides[get_company_repo] = lambda: mock_repo

    res = client_with_db.get("/api/companies")
    assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = res.json()
    assert data["error"]["code"] == "DATABASE_ERROR"
    assert "SuperSecretPassword123" not in res.text
    assert "prod.db:5432" not in res.text
    assert "A database operation failed" in data["error"]["message"]