"""Comprehensive unit and guardrail test suite for Grounded LLM Research Layer."""
from unittest.mock import MagicMock, patch
import pytest

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
from app.research.context import (
    build_research_context,
    extract_sources,
    format_context_as_text,
)
from app.research.llm import (
    LLMAPIError,
    LLMKeyMissingError,
    call_structured_research_llm,
)
from app.research.prompts import RESEARCH_SYSTEM_PROMPT, build_user_prompt
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
from app.research.service import ResearchService
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
def sample_company_data():
    """Provides normalized CompanyData for a representative corporate."""
    return CompanyData(
        ticker="ACME",
        company_profile=CompanyProfile(
            ticker="ACME",
            name="Acme Corp",
            cik="0001234567",
            sector="Technology",
            industry="Software - Infrastructure",
            description="Acme Corp provides mission-critical enterprise software systems.",
        ),
        historical_financials=[
            HistoricalFinancial(
                fiscal_year=2023,
                revenue=100_000.0,
                operating_income=25_000.0,
                net_income=20_000.0,
                operating_cash_flow=30_000.0,
                capex=5_000.0,
                free_cash_flow=25_000.0,
                total_debt=10_000.0,
                stockholders_equity=50_000.0,
            ),
            HistoricalFinancial(
                fiscal_year=2024,
                revenue=120_000.0,
                operating_income=32_000.0,
                net_income=26_000.0,
                operating_cash_flow=38_000.0,
                capex=6_000.0,
                free_cash_flow=32_000.0,
                total_debt=12_000.0,
                stockholders_equity=65_000.0,
            ),
        ],
        market_data=MarketData(
            current_price=150.0,
            shares_outstanding=1_000.0,
            market_cap=150_000.0,
            beta=1.15,
            total_cash=10_000.0,
            total_debt=12_000.0,
        ),
        news=[
            NewsArticle(
                headline="Acme Corp Unveils New Cloud Infrastructure Platform",
                source="Tech Daily",
                url="https://news.example.com/acme-cloud",
                published_at="2026-08-15T12:00:00Z",
                summary="Acme announced expanding cloud enterprise solutions.",
            )
        ],
    )


@pytest.fixture
def sample_financial_analysis():
    """Provides a deterministic FinancialAnalysis bundle with DCF."""
    return FinancialAnalysis(
        ticker="ACME",
        company_name="Acme Corp",
        sector="Technology",
        industry="Software - Infrastructure",
        growth=GrowthAnalysis(
            revenue_growth_yoy=0.20,
            revenue_cagr_3yr=0.18,
            net_income_growth_yoy=0.30,
            fcf_growth_yoy=0.28,
        ),
        profitability=ProfitabilityAnalysis(
            operating_margin=0.267,
            net_margin=0.217,
            roe=0.452,
            roic=0.415,
        ),
        leverage=LeverageAnalysis(
            debt_to_equity=0.185,
            total_debt=12_000.0,
            stockholders_equity=65_000.0,
        ),
        cash_flow=CashFlowAnalysis(
            operating_cash_flow=38_000.0,
            capex=6_000.0,
            free_cash_flow=32_000.0,
            fcf_margin=0.267,
            fcf_conversion=1.23,
        ),
        valuation=ValuationMetrics(
            pe_ratio=25.5,
            forward_pe=22.0,
            ev_to_ebitda=18.2,
            price_to_sales=5.5,
            price_to_fcf=20.8,
            market_cap=150_000.0,
            enterprise_value=152_000.0,
        ),
        health=FinancialHealth(
            overall="Strong",
            growth_pillar="Strong",
            profitability_pillar="Strong",
            leverage_pillar="Strong",
            cash_flow_pillar="Strong",
            key_observations=["Healthy 20% revenue growth", "Robust FCF margin of 26.7%"],
        ),
        dcf=DCFValuation(
            status="calculated",
            risk_free_rate=0.045,
            beta=1.15,
            equity_risk_premium=0.05,
            cost_of_equity=0.1025,
            after_tax_cost_of_debt=0.0474,
            wacc=0.098,
            fcf_growth_assumption=0.15,
            terminal_growth_rate=0.025,
            pv_explicit_fcf=145_000.0,
            terminal_value=650_000.0,
            pv_terminal_value=405_000.0,
            enterprise_value=550_000.0,
            cash=10_000.0,
            total_debt=12_000.0,
            net_debt=2_000.0,
            equity_value=548_000.0,
            shares_outstanding=1_000.0,
            current_share_price=150.0,
            implied_share_price=548.0,
            upside_downside_pct=265.3,
            projections=[
                DCFProjection(year=1, projected_fcf=36_800.0, discount_factor=0.9107, present_value=33_513.76),
                DCFProjection(year=2, projected_fcf=42_320.0, discount_factor=0.8294, present_value=35_100.22),
            ],
            sensitivity_table=SensitivityTable(
                wacc_range=[0.08, 0.10, 0.12],
                terminal_growth_range=[0.02, 0.025, 0.03],
                cells=[
                    SensitivityCell(wacc=0.08, terminal_growth=0.025, implied_share_price=650.0),
                    SensitivityCell(wacc=0.10, terminal_growth=0.025, implied_share_price=548.0),
                ],
            ),
        ),
    )


@pytest.fixture
def sample_mock_report():
    """Provides a valid mock ResearchReport conforming to schema."""
    return ResearchReport(
        ticker="ACME",
        company_name="Acme Corp",
        executive_summary="Acme Corp demonstrates robust top-line growth and disciplined capital allocation.",
        investment_thesis="Market expansion in enterprise infrastructure provides sustainable long-term cash generation.",
        financial_snapshot=FinancialSnapshot(
            summary="Strong fiscal performance with 20.0% revenue expansion and expanding operating margin of 26.7%.",
            key_points=["Revenue reached $120.00K with 20% growth", "FCF conversion of 123% indicates high earnings quality"],
        ),
        valuation_assessment=ValuationAssessment(
            summary="Trading at 25.5x trailing P/E and 5.5x P/S reflecting premium positioning.",
            multiples_summary="P/E: 25.5x, P/S: 5.5x, EV/EBITDA: 18.2x",
            key_points=["Multiple reflects software sector premium", "Forward multiple moderates to 22.0x"],
        ),
        strengths=["High operating margin of 26.7%", "Low leverage profile with D/E of 0.19x"],
        risks=["Valuation sensitive to macroeconomic discount rates", "Cloud competition"],
        catalysts=["Enterprise cloud platform adoption", "Expansion into enterprise tiers"],
        concerns=["Increasing R&D requirements", "Potential customer concentration"],
        financial_health_assessment=FinancialHealthAssessment(
            summary="Balance sheet exhibits exceptional solvency with low debt and positive net liquidity.",
            overall_rating="Strong",
            observations=["Solvent capital structure", "Healthy FCF generation"],
        ),
        dcf_interpretation=DCFInterpretation(
            summary="Baseline DCF model indicates significant intrinsic value under a 9.8% WACC and 2.5% terminal growth rate.",
            valuation_signal="Market price trades at a discount to model-implied baseline intrinsic value.",
            sensitivity_observation="Valuation ranges from $548.00 to $650.00 across tested discount rates.",
            model_upside_downside_pct=265.3,
        ),
        news_and_market_context=NewsMarketContext(
            summary="Recent news highlights new cloud infrastructure initiatives.",
            relevant_headlines=["Acme Corp Unveils New Cloud Infrastructure Platform"],
        ),
        conclusion="Acme presents a fundamentally resilient growth profile with strong balance sheet characteristics.",
        confidence=ReportConfidence(
            level="High",
            rationale="Audited SEC 10-K financial history and reliable market data availability.",
        ),
        limitations=["DCF model assumes steady 15% medium-term FCF growth which may face market cyclicality."],
        sources=[
            ResearchSource(provider="SEC_EDGAR", title="SEC 10-K Annual Report", source_type="filing")
        ],
    )


# ==============================================================================
# 1. CONTEXT BUILDER TESTS
# ==============================================================================

def test_context_builder_includes_financial_metrics(sample_company_data, sample_financial_analysis):
    ctx = build_research_context(sample_company_data, sample_financial_analysis)

    assert ctx["company"]["ticker"] == "ACME"
    assert ctx["company"]["name"] == "Acme Corp"
    assert ctx["growth"]["revenue_growth_yoy"] == "20.0%"
    assert ctx["profitability"]["operating_margin"] == "26.7%"
    assert ctx["leverage"]["debt_to_equity"] in ("0.18x", "0.19x")
    assert ctx["cash_flow"]["free_cash_flow"] == "$32,000.00"


def test_context_builder_includes_dcf(sample_company_data, sample_financial_analysis):
    ctx = build_research_context(sample_company_data, sample_financial_analysis)
    dcf = ctx["dcf"]

    assert dcf["is_applicable"] is True
    assert dcf["status"] == "calculated"
    assert dcf["wacc"] == "9.8%"
    assert dcf["implied_share_price"] == "$548.00"
    assert dcf["upside_downside_pct"] == "+265.3%"
    assert len(dcf["explicit_projections"]) == 2


def test_context_builder_includes_news(sample_company_data, sample_financial_analysis):
    ctx = build_research_context(sample_company_data, sample_financial_analysis)
    news = ctx["news"]

    assert len(news) == 1
    assert "Cloud Infrastructure" in news[0]["headline"]
    assert news[0]["source"] == "Tech Daily"


def test_missing_values_remain_explicit(sample_company_data, sample_financial_analysis):
    # Null out metrics to verify explicit formatting
    sample_financial_analysis.growth.revenue_growth_yoy = None
    sample_financial_analysis.profitability.operating_margin = None
    ctx = build_research_context(sample_company_data, sample_financial_analysis)

    assert ctx["growth"]["revenue_growth_yoy"] == "N/A"
    assert ctx["profitability"]["operating_margin"] == "N/A"

    text = format_context_as_text(ctx)
    assert "- Revenue YoY Growth: N/A" in text
    assert "- Operating Margin: N/A" in text


def test_dcf_not_applicable_preserved(sample_company_data, sample_financial_analysis):
    sample_financial_analysis.dcf.status = "not_applicable"
    ctx = build_research_context(sample_company_data, sample_financial_analysis)

    assert ctx["dcf"]["is_applicable"] is False
    assert ctx["dcf"]["status"] == "not_applicable"
    assert "not applicable" in ctx["dcf"]["note"].lower()

    text = format_context_as_text(ctx)
    assert "[STATUS: NOT_APPLICABLE]" in text


def test_financial_institution_context_does_not_manufacture_dcf(sample_company_data, sample_financial_analysis):
    sample_company_data.company_profile.sector = "Financial Services"
    sample_financial_analysis.dcf.status = "not_applicable"

    ctx = build_research_context(sample_company_data, sample_financial_analysis)
    assert ctx["dcf"]["is_applicable"] is False
    assert "commercial banks" in ctx["dcf"]["note"].lower()


# ==============================================================================
# 2. SOURCE PROVENANCE TESTS
# ==============================================================================

def test_source_metadata_preserved(sample_company_data, sample_financial_analysis):
    sources = extract_sources(sample_company_data, sample_financial_analysis)

    providers = [s.provider for s in sources]
    assert "SEC_EDGAR" in providers
    assert "yfinance" in providers
    assert "Tech Daily" in providers
    assert "FinancialAnalysisEngine" in providers

    # Ensure URLs are accurately recorded
    sec_src = next(s for s in sources if s.provider == "SEC_EDGAR")
    assert "0001234567" in sec_src.url


# ==============================================================================
# 3. PROMPT & GROUNDING RULE TESTS
# ==============================================================================

def test_prompt_construction_contains_grounding_rules():
    assert "ZERO INVENTED NUMBERS" in RESEARCH_SYSTEM_PROMPT
    assert "ZERO FINANCIAL CALCULATIONS" in RESEARCH_SYSTEM_PROMPT
    assert "MODEL-IMPLIED VALUATION" in RESEARCH_SYSTEM_PROMPT
    assert "FINANCIAL INSTITUTION DCF GATE" in RESEARCH_SYSTEM_PROMPT

    user_prompt = build_user_prompt("SAMPLE_CONTEXT", "TEST", "Test Corp")
    assert "Test Corp" in user_prompt
    assert "SAMPLE_CONTEXT" in user_prompt


# ==============================================================================
# 4. LLM INVOCATION & ERROR HANDLING TESTS
# ==============================================================================

def test_missing_api_key_handled(sample_company_data, sample_financial_analysis):
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(LLMKeyMissingError) as exc_info:
            call_structured_research_llm("Context text", "TEST", "Test Corp", api_key=None)
        assert "OPENAI_API_KEY is missing" in str(exc_info.value)


def test_api_failure_handled():
    with patch("app.research.llm.OpenAI") as mock_openai:
        client_instance = MagicMock()
        client_instance.beta.chat.completions.parse.side_effect = Exception("Connection refused by peer")
        mock_openai.return_value = client_instance

        with pytest.raises(LLMAPIError) as exc_info:
            call_structured_research_llm("Context text", "TEST", "Test Corp", api_key="fake-key")
        assert "Connection refused" in str(exc_info.value)


def test_valid_structured_llm_response_parses_successfully(sample_mock_report):
    with patch("app.research.llm.OpenAI") as mock_openai:
        mock_choice = MagicMock()
        mock_choice.message.refusal = None
        mock_choice.message.parsed = sample_mock_report

        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]

        client_instance = MagicMock()
        client_instance.beta.chat.completions.parse.return_value = mock_completion
        mock_openai.return_value = client_instance

        report = call_structured_research_llm("Context text", "ACME", "Acme Corp", api_key="fake-key")
        assert report.ticker == "ACME"
        assert report.financial_snapshot.summary is not None
        assert report.dcf_interpretation.model_upside_downside_pct == 265.3


# ==============================================================================
# 5. HALLUCINATION GUARDRAIL TESTS (CRITICAL REQUIREMENT)
# ==============================================================================

def test_hallucination_guardrail_ticker_alignment(sample_company_data, sample_financial_analysis, sample_mock_report):
    service = ResearchService()
    # Simulate an LLM returning an inconsistent ticker
    sample_mock_report.ticker = "WRONG_TICKER"

    aligned = service.validate_and_align_report(sample_mock_report, sample_company_data, sample_financial_analysis)
    assert aligned.ticker == "ACME"


def test_hallucination_guardrail_dcf_upside_alignment(sample_company_data, sample_financial_analysis, sample_mock_report):
    service = ResearchService()
    # Simulate LLM inventing a different upside % (e.g. +999.0%)
    sample_mock_report.dcf_interpretation.model_upside_downside_pct = 999.0

    aligned = service.validate_and_align_report(sample_mock_report, sample_company_data, sample_financial_analysis)
    # Must be strictly clamped to the deterministic engine calculation (265.3%)
    assert aligned.dcf_interpretation.model_upside_downside_pct == 265.3


def test_hallucination_guardrail_bank_dcf_cleared(sample_company_data, sample_financial_analysis, sample_mock_report):
    service = ResearchService()
    # Bank with not_applicable DCF
    sample_financial_analysis.dcf.status = "not_applicable"
    # Simulate LLM attempting to fabricate a 45.0% DCF upside
    sample_mock_report.dcf_interpretation.model_upside_downside_pct = 45.0

    aligned = service.validate_and_align_report(sample_mock_report, sample_company_data, sample_financial_analysis)
    # Must be strictly cleared to None for financial institutions
    assert aligned.dcf_interpretation.model_upside_downside_pct is None


def test_end_to_end_research_service_with_mocked_llm(sample_company_data, sample_financial_analysis, sample_mock_report):
    service = ResearchService()

    with patch("app.research.service.call_structured_research_llm", return_value=sample_mock_report):
        report = service.generate_report(
            company_data=sample_company_data,
            financial_analysis=sample_financial_analysis,
            api_key="fake-key",
        )

        assert report.ticker == "ACME"
        assert report.company_name == "Acme Corp"
        assert report.executive_summary is not None
        assert report.dcf_interpretation.model_upside_downside_pct == 265.3
        # Ensure verified sources were attached
        providers = [s.provider for s in report.sources]
        assert "SEC_EDGAR" in providers
        assert "yfinance" in providers