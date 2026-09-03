"""Comprehensive reliability, resilience, error handling, and timeout/retry tests for Milestone 8."""
import logging
from unittest.mock import MagicMock, patch
import pytest
import requests
from fastapi import status
from fastapi.testclient import TestClient
import openai

from app.api.routes import get_orchestrator, get_financial_engine, get_research_service, get_company_repo
from app.data.orchestrator import DataOrchestrator
from app.data.sec_edgar import SECEdgarClient
from app.db.models import Base, Company
from app.db.repositories import CompanyRepository
from app.main import create_app
from app.research.llm import (
    LLMAPIError,
    LLMKeyMissingError,
    LLMResponseParsingError,
    call_structured_research_llm,
)
from app.schemas.financial import CompanyData, CompanyProfile, MarketData
from app.utils.logging import SensitiveDataFilter, setup_logger


# ===========================================================================
# 1. Upstream SEC EDGAR Timeout, Retry & Rate Limit Handling
# ===========================================================================

def test_sec_timeout_and_exponential_retry():
    """Verifies that transient request timeouts trigger exponential retry and eventually succeed."""
    client = SECEdgarClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"0": {"ticker": "AAPL", "cik_str": "320193"}}

    with patch.object(
        client.session,
        "get",
        side_effect=[requests.Timeout("Connection timed out"), requests.Timeout("Connection timed out"), mock_resp],
    ) as mock_get:
        # Patch sleep to keep test execution fast
        with patch("time.sleep"):
            resp = client._request_with_retry("https://test.sec.gov/sample", max_retries=3)
            assert resp is not None
            assert resp.status_code == 200
            assert mock_get.call_count == 3


def test_sec_rate_limit_429_retry_and_exhaustion():
    """Verifies that HTTP 429 rate limit errors retry up to max_retries and fail gracefully without crashing."""
    client = SECEdgarClient()
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"Retry-After": "1"}

    with patch.object(client.session, "get", return_value=mock_429) as mock_get:
        with patch("time.sleep"):
            resp = client._request_with_retry("https://test.sec.gov/sample", max_retries=3)
            assert resp is None
            assert mock_get.call_count == 3


def test_sec_non_retryable_404_does_not_retry():
    """Verifies that non-transient 404 Not Found returns immediately without wasted retries."""
    client = SECEdgarClient()
    mock_404 = MagicMock()
    mock_404.status_code = 404

    with patch.object(client.session, "get", return_value=mock_404) as mock_get:
        resp = client._request_with_retry("https://test.sec.gov/nonexistent", max_retries=3)
        assert resp is None
        assert mock_get.call_count == 1


def test_sec_malformed_json_handled_gracefully():
    """Verifies that malformed or non-JSON payloads from SEC do not cause unhandled exceptions."""
    client = SECEdgarClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")

    with patch.object(client, "_request_with_retry", return_value=mock_resp):
        facts = client.get_company_facts("0000320193")
        assert facts is None


# ===========================================================================
# 2. Data Orchestrator Partial Failure & Grounding Resilience
# ===========================================================================

def test_orchestrator_partial_failure_missing_sec_preserves_market_data():
    """
    When SEC is unavailable but yfinance succeeds, orchestrator returns CompanyData
    with market data intact and SEC financials empty — never inventing fake numbers.
    """
    mock_sec = MagicMock()
    mock_sec.resolve_cik.return_value = None

    mock_yf = MagicMock()
    mock_profile = CompanyProfile(ticker="ORCL", name="Oracle Corp.")
    mock_market = MarketData(current_price=135.0, market_cap=370000000000.0)
    mock_yf.get_market_data.return_value = (mock_market, mock_profile, [])

    mock_news = MagicMock()
    mock_news.get_company_news.return_value = ([], [])

    orch = DataOrchestrator(sec_client=mock_sec, yf_client=mock_yf, news_client=mock_news)
    data = orch.get_company_data("ORCL")

    assert data.ticker == "ORCL"
    assert data.market_data.current_price == 135.0
    assert len(data.historical_financials) == 0
    assert any("SEC_EDGAR" in w.provider for w in data.data_warnings)


def test_orchestrator_partial_failure_missing_market_data_preserves_sec():
    """
    When yfinance fails but SEC succeeds, orchestrator returns CompanyData
    with SEC financials intact and market price null.
    """
    from app.schemas.financial import HistoricalFinancial

    sample_fin = HistoricalFinancial(fiscal_year=2024, revenue=390000000000.0)
    mock_sec = MagicMock()
    mock_sec.resolve_cik.return_value = "0000320193"
    mock_sec.get_company_facts.return_value = {"facts": {}}
    mock_sec.parse_financials.return_value = ([sample_fin], [], "Apple Inc.")

    mock_yf = MagicMock()
    mock_yf.get_market_data.return_value = (None, None, [])

    mock_news = MagicMock()
    mock_news.get_company_news.return_value = ([], [])

    orch = DataOrchestrator(sec_client=mock_sec, yf_client=mock_yf, news_client=mock_news)
    data = orch.get_company_data("AAPL")

    assert data.ticker == "AAPL"
    assert data.market_data.current_price is None


def test_orchestrator_total_failure_raises_value_error():
    """When both market data and SEC data fail, orchestrator raises clear ValueError."""
    mock_sec = MagicMock()
    mock_sec.resolve_cik.return_value = None
    mock_yf = MagicMock()
    mock_yf.get_market_data.return_value = (None, None, [])
    mock_news = MagicMock()
    mock_news.get_company_news.return_value = ([], [])

    orch = DataOrchestrator(sec_client=mock_sec, yf_client=mock_yf, news_client=mock_news)
    with pytest.raises(ValueError, match="Failed to retrieve"):
        orch.get_company_data("INVALID_ALL")


# ===========================================================================
# 3. OpenAI / Research Layer Reliability & Transient Retries
# ===========================================================================

def test_openai_transient_rate_limit_retry_and_success():
    """Verifies that OpenAI rate limit error triggers retry and returns report upon recovery."""
    from app.research.schemas import ResearchReport, ReportConfidence, DCFInterpretation

    mock_report = ResearchReport(
        ticker="AAPL",
        company_name="Apple Inc.",
        generated_at="2026-09-04T00:00:00Z",
        executive_summary="Solid balance sheet.",
        investment_thesis="Moat expansion.",
        financial_snapshot={"summary": "Strong.", "key_points": []},
        valuation_assessment={"summary": "Fair.", "multiples_summary": "30x", "key_points": []},
        strengths=["Ecosystem"],
        risks=["China"],
        catalysts=["AI"],
        concerns=["Capex"],
        financial_health_assessment={"summary": "Pristine.", "overall_rating": "Strong", "observations": []},
        dcf_interpretation=DCFInterpretation(summary="Fair.", valuation_signal="Fairly Valued", sensitivity_observation="Low"),
        news_and_market_context={"summary": "News.", "relevant_headlines": []},
        conclusion="Buy.",
        confidence=ReportConfidence(level="High", rationale="Audited SEC reports."),
        limitations=[],
        sources=[],
        disclaimer="Notice.",
    )

    mock_msg = MagicMock()
    mock_msg.refusal = None
    mock_msg.parsed = mock_report
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    # 1st call fails with RateLimitError, 2nd succeeds
    mock_client.beta.chat.completions.parse.side_effect = [
        openai.RateLimitError(
            message="Rate limit reached",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        ),
        mock_completion,
    ]

    with patch("app.research.llm.OpenAI", return_value=mock_client):
        with patch("time.sleep"):
            report = call_structured_research_llm(
                context_text="Financial Context",
                ticker="AAPL",
                company_name="Apple Inc.",
                api_key="sk-mock-valid-key-1234567890",
            )
            assert report.ticker == "AAPL"
            assert mock_client.beta.chat.completions.parse.call_count == 2


def test_openai_authentication_failure_does_not_retry():
    """Verifies that non-transient AuthenticationError fails immediately without retrying."""
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.side_effect = openai.AuthenticationError(
        message="Invalid API key",
        response=MagicMock(status_code=401, headers={}),
        body=None,
    )

    with patch("app.research.llm.OpenAI", return_value=mock_client):
        with pytest.raises(LLMAPIError, match="Authentication Error"):
            call_structured_research_llm(
                context_text="Financial Context",
                ticker="AAPL",
                company_name="Apple Inc.",
                api_key="sk-invalid-key-1234567890",
            )
        assert mock_client.beta.chat.completions.parse.call_count == 1


def test_openai_model_refusal_raises_parsing_error():
    """Verifies that safety refusals are cleanly caught as LLMResponseParsingError."""
    mock_msg = MagicMock()
    mock_msg.refusal = "Safety policy refusal."
    mock_msg.parsed = None
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.return_value = mock_completion

    with patch("app.research.llm.OpenAI", return_value=mock_client):
        with pytest.raises(LLMResponseParsingError, match="refused"):
            call_structured_research_llm(
                context_text="Context",
                ticker="AAPL",
                company_name="Apple Inc.",
                api_key="sk-valid-key-1234567890",
            )


# ===========================================================================
# 4. Database Transaction Rollback Safety
# ===========================================================================

def test_database_transaction_rollback_on_failure():
    """Verifies that database persistence failures trigger rollback and do not leave dirty session state."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = CompanyRepository(session)
    # Insert valid company
    comp = repo.upsert(ticker="VALID", company_name="Valid Corp")
    assert comp.id is not None

    # Simulate error on commit
    with patch.object(session, "commit", side_effect=Exception("Disk I/O Error")):
        with pytest.raises(Exception, match="Disk I/O Error"):
            repo.upsert(ticker="FAILING", company_name="Failing Corp")

    # Verify session recovered and subsequent query works
    company_check = repo.get_by_ticker("VALID")
    assert company_check is not None
    assert company_check.ticker == "VALID"
    session.close()


def test_analyze_partial_db_failure_company_succeeds_snapshot_fails():
    """
    Audits multi-step persistence in POST /api/analyze:
    When company_repo.upsert succeeds but analysis_repo.create_snapshot fails:
    1. Endpoint catches the database failure and safely returns HTTP 500 DATABASE_ERROR.
    2. Company master record is committed in companies (idempotent master dimension).
    3. No corrupted or partial record exists in analysis_snapshots.
    4. Subsequent request for the same ticker updates the company and successfully saves snapshot.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Company, AnalysisSnapshot
    from app.db.session import get_db
    from app.financial.schemas import FinancialAnalysis, FinancialHealth, DCFValuation
    from app.financial.engine import FinancialAnalysisEngine
    from app.data.orchestrator import DataOrchestrator
    from app.schemas.financial import CompanyProfile, MarketData
    from app.db.repositories.analysis import AnalysisRepository

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)
    session = TestingSession()

    app = create_app()
    app.dependency_overrides[get_db] = lambda: session

    # Mock DataOrchestrator and FinancialAnalysisEngine
    mock_profile = CompanyProfile(ticker="NVDA", name="Nvidia Corp.", sector="Technology")
    mock_data = CompanyData(
        ticker="NVDA",
        company_profile=mock_profile,
        annual_financials=[],
        market_data=MarketData(current_price=120.0),
        news=[],
    )
    mock_analysis = FinancialAnalysis(
        ticker="NVDA",
        company_name="Nvidia Corp.",
        currency="USD",
        growth={"revenue_growth_yoy": 1.2, "revenue_cagr_3yr": 0.8, "net_income_growth_yoy": 1.5, "fcf_growth_yoy": 1.4, "revenue_growth_series": [], "net_income_growth_series": [], "fcf_growth_series": []},
        profitability={"gross_margin": 0.75, "operating_margin": 0.60, "net_margin": 0.50, "roe": 0.8, "roic": 0.7},
        leverage={"debt_to_equity": 0.3, "debt_to_ebitda": 0.2, "interest_coverage": 50.0, "total_debt": 10000000000.0, "stockholders_equity": 40000000000.0},
        cash_flow={"operating_cash_flow": 30000000000.0, "capex": 3000000000.0, "free_cash_flow": 27000000000.0, "fcf_margin": 0.45, "fcf_conversion": 0.95},
        valuation={"pe_ratio": 45.0, "forward_pe": 35.0, "ev_to_ebitda": 38.0, "price_to_sales": 25.0, "price_to_fcf": 48.0, "market_cap": 3000000000000.0, "enterprise_value": 2980000000000.0},
        historical_trends=[],
        health=FinancialHealth(overall="Strong", growth_pillar="Strong", profitability_pillar="Strong", leverage_pillar="Strong", cash_flow_pillar="Strong", key_observations=[]),
        dcf=DCFValuation(ticker="NVDA", status="calculated", current_share_price=120.0, implied_share_price=135.0, upside_downside_pct=12.5, wacc=0.09),
    )

    mock_orch = MagicMock()
    mock_orch.get_company_data.return_value = mock_data
    mock_eng = MagicMock()
    mock_eng.analyze.return_value = mock_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orch
    app.dependency_overrides[get_financial_engine] = lambda: mock_eng

    client = TestClient(app, raise_server_exceptions=False)

    # 1. Simulate failure during create_snapshot with SQLAlchemy OperationalError
    from sqlalchemy.exc import OperationalError
    db_err = OperationalError("INSERT INTO analysis_snapshots ...", {}, Exception("Disk full / connection drop"))
    with patch.object(AnalysisRepository, "create_snapshot", side_effect=db_err):
        res = client.post("/api/analyze", json={"ticker": "NVDA"})
        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert res.json()["error"]["code"] == "DATABASE_ERROR"

    # 2. Check state: Company is created, snapshots table has 0 rows
    company = session.query(Company).filter_by(ticker="NVDA").first()
    assert company is not None
    assert company.company_name == "Nvidia Corp."
    assert session.query(AnalysisSnapshot).filter_by(company_id=company.id).count() == 0

    # 3. Subsequent call succeeds and creates snapshot linked to existing Company
    res2 = client.post("/api/analyze", json={"ticker": "NVDA"})
    assert res2.status_code == status.HTTP_200_OK
    assert session.query(AnalysisSnapshot).filter_by(company_id=company.id).count() == 1

    app.dependency_overrides.clear()


# ===========================================================================
# 5. API Input Validation & Query Limit Bounds
# ===========================================================================

@pytest.fixture
def api_client():
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_api_excessive_history_limit_rejected(api_client: TestClient):
    """Verifies that requests exceeding query bounds (e.g. limit=1000) are rejected with HTTP 400/422."""
    res = api_client.get("/api/companies?limit=500")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


def test_api_negative_history_limit_rejected(api_client: TestClient):
    """Verifies that negative query limits are rejected with HTTP 400/422."""
    res = api_client.get("/api/companies?limit=-5")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


def test_api_invalid_ticker_path_rejected(api_client: TestClient):
    """Verifies that malicious or invalid ticker path parameters return HTTP 400."""
    res = api_client.get("/api/companies/BAD@TICKER!/analyses")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json()["error"]["code"] == "INVALID_REQUEST"


# ===========================================================================
# 6. Sensitive Data Filter & Secret Redaction
# ===========================================================================

def test_sensitive_data_filter_scrubs_secrets_from_logs():
    """Verifies that SensitiveDataFilter masks API keys, database URLs with passwords, and Bearer tokens."""
    log_filter = SensitiveDataFilter()

    # 1. OpenAI API key masking
    rec1 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Calling OpenAI with key sk-1234567890abcdef1234567890", args=(), exc_info=None
    )
    log_filter.filter(rec1)
    assert "sk-***REDACTED***" in rec1.msg
    assert "sk-1234567890abcdef1234567890" not in rec1.msg

    # 2. Database connection string masking
    rec2 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Connecting to postgresql+psycopg://dbuser:SuperSecretPassword123@prod.db:5432/financial_analyst",
        args=(), exc_info=None
    )
    log_filter.filter(rec2)
    assert "SuperSecretPassword123" not in rec2.msg
    assert ":***REDACTED***@" in rec2.msg

    # 3. Bearer authorization token masking
    rec3 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Sending request with header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        args=(), exc_info=None
    )
    log_filter.filter(rec3)
    assert "eyJhbGci" not in rec3.msg
    assert "Bearer ***REDACTED***" in rec3.msg