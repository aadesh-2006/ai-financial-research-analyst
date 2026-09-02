"""Comprehensive integration test suite for FastAPI backend API endpoints."""
from unittest.mock import MagicMock, patch
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.routes import get_financial_engine, get_orchestrator, get_research_service
from app.financial.schemas import (
    CashFlowAnalysis,
    DCFProjection,
    DCFValuation,
    FinancialAnalysis,
    FinancialHealth,
    GrowthAnalysis,
    LeverageAnalysis,
    ProfitabilityAnalysis,
    SensitivityCell,
    SensitivityTable,
    ValuationMetrics,
)
from app.main import app
from app.research.llm import LLMAPIError, LLMKeyMissingError
from app.research.schemas import (
    DCFInterpretation,
    FinancialHealthAssessment,
    FinancialSnapshot,
    NewsMarketContext,
    ReportConfidence,
    ResearchReport,
    ResearchSource,
    ValuationAssessment,
)
from app.schemas.financial import (
    CompanyData,
    CompanyProfile,
    HistoricalFinancial,
    MarketData,
    NewsArticle,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def client():
    """Provides a FastAPI test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_company_data():
    """Provides normalized CompanyData for a standard company (AAPL / ACME)."""
    return CompanyData(
        ticker="AAPL",
        company_profile=CompanyProfile(
            ticker="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            description="Designs and manufactures mobile devices and personal computers.",
            website="https://www.apple.com",
            currency="USD",
        ),
        market_data=MarketData(
            ticker="AAPL",
            current_price=220.0,
            market_cap=3_300_000_000_000.0,
            shares_outstanding=15_000_000_000.0,
            beta=1.1,
            pe_ratio=32.5,
            forward_pe=28.0,
            price_to_sales=8.5,
            ev_to_ebitda=24.0,
            total_cash=65_000_000_000.0,
            total_debt=105_000_000_000.0,
            currency="USD",
        ),
        historical_financials=[
            HistoricalFinancial(
                fiscal_year=2024,
                revenue=390_000_000_000.0,
                operating_income=120_000_000_000.0,
                net_income=100_000_000_000.0,
                operating_cash_flow=115_000_000_000.0,
                capex=10_000_000_000.0,
                free_cash_flow=105_000_000_000.0,
                total_debt=105_000_000_000.0,
                stockholders_equity=60_000_000_000.0,
            )
        ],
        news=[
            NewsArticle(
                headline="Apple unveils new AI features across product line",
                source="TechWire",
                url="https://techwire.com/apple-ai",
                published_at="2026-09-01T12:00:00Z",
                summary="Apple highlighted privacy-focused artificial intelligence capabilities.",
            )
        ],
    )


@pytest.fixture
def sample_financial_analysis():
    """Provides deterministic FinancialAnalysis bundle."""
    return FinancialAnalysis(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        currency="USD",
        growth=GrowthAnalysis(
            revenue_growth_yoy=0.08,
            revenue_cagr_3yr=0.07,
            net_income_growth_yoy=0.10,
            fcf_growth_yoy=0.12,
        ),
        profitability=ProfitabilityAnalysis(
            gross_margin=0.45,
            operating_margin=0.30,
            net_margin=0.25,
            roe=1.60,
            roic=0.42,
        ),
        leverage=LeverageAnalysis(
            debt_to_equity=1.75,
            debt_to_ebitda=0.85,
            interest_coverage=25.0,
            total_debt=105_000_000_000.0,
            stockholders_equity=60_000_000_000.0,
        ),
        cash_flow=CashFlowAnalysis(
            operating_cash_flow=115_000_000_000.0,
            capex=10_000_000_000.0,
            free_cash_flow=105_000_000_000.0,
            fcf_margin=0.27,
            fcf_conversion=1.05,
        ),
        valuation=ValuationMetrics(
            pe_ratio=32.5,
            forward_pe=28.0,
            ev_to_ebitda=24.0,
            price_to_sales=8.5,
            price_to_fcf=31.4,
            market_cap=3_300_000_000_000.0,
            enterprise_value=3_340_000_000_000.0,
        ),
        dcf=DCFValuation(
            ticker="AAPL",
            status="calculated",
            risk_free_rate=0.042,
            beta=1.1,
            wacc=0.085,
            terminal_growth_rate=0.025,
            implied_share_price=210.50,
            current_share_price=220.0,
            upside_downside_pct=-4.3,
            projections=[
                DCFProjection(year=1, projected_fcf=110_000_000_000.0, discount_factor=0.9217, present_value=101_387_000_000.0)
            ],
            sensitivity_table=SensitivityTable(
                wacc_range=[0.075, 0.085, 0.095],
                growth_range=[0.02, 0.025, 0.03],
                cells=[
                    SensitivityCell(wacc=0.085, terminal_growth=0.025, implied_share_price=210.50, upside_pct=-4.3)
                ],
            ),
        ),
        historical_trends=[],
        health=FinancialHealth(
            overall="Strong",
            growth_pillar="Strong",
            profitability_pillar="Strong",
            leverage_pillar="Moderate",
            cash_flow_pillar="Strong",
            key_observations=["Exceptional cash conversion and high operating profitability."],
        ),
        warnings=[],
    )


@pytest.fixture
def sample_research_report():
    """Provides a valid structured ResearchReport."""
    return ResearchReport(
        ticker="AAPL",
        company_name="Apple Inc.",
        executive_summary="Apple exhibits industry-leading operating margins and exceptional free cash flow.",
        investment_thesis="A robust ecosystem driving recurring services revenue with premium device pricing power.",
        financial_snapshot=FinancialSnapshot(
            summary="Strong top-line stability with consistent 30% operating margins.",
            key_points=["Revenue grew 8% YoY", "Free cash flow exceeded $100B"],
            revenue_growth_yoy_pct=8.0,
            operating_margin_pct=30.0,
            net_margin_pct=25.0,
            free_cash_flow=105_000_000_000.0,
        ),
        valuation_assessment=ValuationAssessment(
            summary="Trading at a premium multiple reflecting institutional quality.",
            multiples_summary="P/E of 32.5x vs 5-year historical average.",
            key_points=["Premium valuation supported by high ROIC"],
            current_share_price=220.0,
            pe_ratio=32.5,
            forward_pe=28.0,
            price_to_sales=8.5,
            ev_to_ebitda=24.0,
            price_to_book=None,
        ),
        strengths=["Immense ecosystem lock-in", "Aggressive share repurchase program"],
        risks=["Regulatory scrutiny over App Store fees", "Concentration in flagship hardware"],
        catalysts=["Expansion of on-device Apple Intelligence features"],
        concerns=["Lengthening consumer smartphone replacement cycles"],
        financial_health_assessment=FinancialHealthAssessment(
            summary="Pristine balance sheet with ample liquidity and manageable debt.",
            overall_rating="Strong",
            observations=["Debt is comfortably covered by annual operational cash flows."],
        ),
        dcf_interpretation=DCFInterpretation(
            summary="Model implies fair value near current trading levels assuming an 8.5% WACC.",
            valuation_signal="Model-implied value is balanced with prevailing market quotes.",
            sensitivity_observation="Dispersion remains tight between $190 and $235.",
            model_wacc_pct=8.5,
            model_terminal_growth_pct=2.5,
            model_implied_share_price=210.50,
            model_upside_downside_pct=-4.3,
        ),
        news_and_market_context=NewsMarketContext(
            summary="Recent headlines center on strategic rollout of Apple Intelligence.",
            relevant_headlines=["Apple unveils new AI features across product line"],
        ),
        conclusion="High-quality fundamental asset with sound capital discipline.",
        confidence=ReportConfidence(
            level="High",
            rationale="Robust 10-K disclosures and high visibility into operating cash flows.",
        ),
        limitations=["DCF model sensitive to long-term terminal growth rate assumption."],
        sources=[
            ResearchSource(
                provider="SEC_EDGAR",
                title="SEC Form 10-K Annual Reports (Fiscal Years: 2024)",
                url="https://www.sec.gov/edgar/browse/?CIK=0000320193",
                source_type="filing",
            )
        ],
    )


# ==============================================================================
# 1. HEALTH ENDPOINT TESTS
# ==============================================================================

def test_health_endpoint_returns_200_and_expected_status(client):
    """GET /api/health returns 200 OK with service identifier, requiring zero credentials."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-financial-research-analyst"


# ==============================================================================
# 2. POST /api/analyze TESTS (DETERMINISTIC ENGINE)
# ==============================================================================

def test_analyze_with_valid_ticker_returns_200(client, sample_company_data, sample_financial_analysis):
    """POST /api/analyze executes deterministic pipeline and returns 200 with structured analysis."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine

    try:
        response = client.post("/api/analyze", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
        assert data["growth"]["revenue_growth_yoy"] == 0.08
        assert data["profitability"]["operating_margin"] == 0.30
        assert data["dcf"]["implied_share_price"] == 210.50
        assert data["description"] == sample_company_data.company_profile.description
        assert data["website"] == sample_company_data.company_profile.website
    finally:
        app.dependency_overrides.clear()


def test_analyze_normalizes_lowercase_ticker(client, sample_company_data, sample_financial_analysis):
    """POST /api/analyze normalizes lowercase ticker e.g. 'aapl' -> 'AAPL'."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine

    try:
        response = client.post("/api/analyze", json={"ticker": "aapl"})
        assert response.status_code == status.HTTP_200_OK
        mock_orchestrator.get_company_data.assert_called_once_with("AAPL")
        assert response.json()["ticker"] == "AAPL"
    finally:
        app.dependency_overrides.clear()


def test_analyze_rejects_malformed_or_empty_ticker(client):
    """POST /api/analyze rejects empty, whitespace, and special-character tickers with 400."""
    # Empty string
    res_empty = client.post("/api/analyze", json={"ticker": ""})
    assert res_empty.status_code == status.HTTP_400_BAD_REQUEST
    assert res_empty.json()["error"]["code"] == "INVALID_REQUEST"

    # Whitespace string
    res_spaces = client.post("/api/analyze", json={"ticker": "   "})
    assert res_spaces.status_code == status.HTTP_400_BAD_REQUEST
    assert res_spaces.json()["error"]["code"] == "INVALID_REQUEST"

    # Invalid characters ($$$)
    res_invalid = client.post("/api/analyze", json={"ticker": "$$$"})
    assert res_invalid.status_code == status.HTTP_400_BAD_REQUEST
    assert res_invalid.json()["error"]["code"] == "INVALID_REQUEST"


def test_analyze_does_not_require_openai_api_key(client, sample_company_data, sample_financial_analysis):
    """POST /api/analyze runs completely independent of OPENAI_API_KEY."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine

    try:
        with patch.dict("os.environ", {}, clear=True):
            response = client.post("/api/analyze", json={"ticker": "AAPL"})
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["ticker"] == "AAPL"
    finally:
        app.dependency_overrides.clear()


def test_analyze_preserves_deterministic_dcf_output(client, sample_company_data, sample_financial_analysis):
    """POST /api/analyze preserves exact WACC, implied price, and sensitivity table."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine

    try:
        response = client.post("/api/analyze", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_200_OK
        dcf = response.json()["dcf"]
        assert dcf["status"] == "calculated"
        assert dcf["wacc"] == 0.085
        assert dcf["implied_share_price"] == 210.50
        assert dcf["upside_downside_pct"] == -4.3
        assert len(dcf["sensitivity_table"]["cells"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_analyze_preserves_bank_dcf_not_applicable_behavior(client, sample_company_data, sample_financial_analysis):
    """POST /api/analyze preserves JPM / financial institution not_applicable DCF gate."""
    sample_financial_analysis.dcf.status = "not_applicable"
    sample_financial_analysis.dcf.implied_share_price = None
    sample_financial_analysis.dcf.upside_downside_pct = None

    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine

    try:
        response = client.post("/api/analyze", json={"ticker": "JPM"})
        assert response.status_code == status.HTTP_200_OK
        dcf = response.json()["dcf"]
        assert dcf["status"] == "not_applicable"
        assert dcf["implied_share_price"] is None
        assert dcf["upside_downside_pct"] is None
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 3. POST /api/research TESTS (GROUNDED LLM LAYER)
# ==============================================================================

def test_research_with_mocked_service_returns_valid_report(
    client, sample_company_data, sample_financial_analysis, sample_research_report
):
    """POST /api/research coordinates ingestion, engine, and LLM synthesis returning 200."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    mock_research = MagicMock()
    mock_research.generate_report.return_value = sample_research_report

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine
    app.dependency_overrides[get_research_service] = lambda: mock_research

    try:
        response = client.post("/api/research", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
        assert data["executive_summary"] is not None
        assert data["dcf_interpretation"]["model_wacc_pct"] == 8.5
        assert data["dcf_interpretation"]["model_upside_downside_pct"] == -4.3
        assert len(data["sources"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_research_handles_missing_openai_api_key_cleanly(
    client, sample_company_data, sample_financial_analysis
):
    """POST /api/research returns clean 503 when OPENAI_API_KEY is not configured."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    mock_research = MagicMock()
    mock_research.generate_report.side_effect = LLMKeyMissingError("OPENAI_API_KEY is missing.")

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine
    app.dependency_overrides[get_research_service] = lambda: mock_research

    try:
        response = client.post("/api/research", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["error"]["code"] == "OPENAI_API_KEY_MISSING"
        assert "OPENAI_API_KEY" in data["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_research_handles_openai_api_failure_cleanly(
    client, sample_company_data, sample_financial_analysis
):
    """POST /api/research maps upstream OpenAI API failure to 502 Bad Gateway."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    mock_research = MagicMock()
    mock_research.generate_report.side_effect = LLMAPIError("OpenAI Authentication Error: Invalid API key.")

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine
    app.dependency_overrides[get_research_service] = lambda: mock_research

    try:
        response = client.post("/api/research", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert data["error"]["code"] == "OPENAI_AUTH_ERROR"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 4. ERROR HANDLING & RESILIENCE TESTS
# ==============================================================================

def test_upstream_data_failure_maps_to_structured_error(client):
    """When DataOrchestrator cannot find data for ticker, returns structured 404."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.side_effect = ValueError(
        "Failed to retrieve data for ticker 'BADTICKER'. Verify the ticker symbol is valid."
    )

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

    try:
        response = client.post("/api/analyze", json={"ticker": "BADTICKER"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"]["code"] == "TICKER_NOT_FOUND"
        assert "BADTICKER" in data["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_unexpected_internal_error_does_not_leak_stack_traces_or_secrets(client):
    """Unexpected internal exceptions map to clean 500 without exposing secrets or traces."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.side_effect = RuntimeError("secret_token_abcdef123456 crashed the DB")

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

    try:
        response = client.post("/api/analyze", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # Must not leak the secret token or python stack trace
        assert "secret_token" not in str(data)
        assert "Traceback" not in str(data)
    finally:
        app.dependency_overrides.clear()


def test_response_models_serialize_cleanly(client, sample_company_data, sample_financial_analysis):
    """Verifies that all nullable fields and complex nested models serialize to valid JSON."""
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_company_data.return_value = sample_company_data

    mock_engine = MagicMock()
    mock_engine.analyze.return_value = sample_financial_analysis

    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_financial_engine] = lambda: mock_engine

    try:
        response = client.post("/api/analyze", json={"ticker": "AAPL"})
        assert response.status_code == status.HTTP_200_OK
        # Must be valid json without any raw Python representations
        data = response.json()
        assert isinstance(data["growth"]["revenue_growth_series"], list)
        assert isinstance(data["dcf"]["projections"], list)
        assert data["valuation"]["price_to_sales"] == 8.5
        assert data["valuation"]["pe_ratio"] == 32.5
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 5. CORS MIDDLEWARE TESTS
# ==============================================================================

def test_cors_middleware_allows_configured_origins(client):
    """Verifies CORS headers are returned for preflight requests from allowed origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/api/analyze", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_middleware_rejects_disallowed_origins(client):
    """Verifies disallowed origins do not receive allow-origin header."""
    headers = {
        "Origin": "http://malicious-site.com",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/api/analyze", headers=headers)
    assert response.headers.get("access-control-allow-origin") is None