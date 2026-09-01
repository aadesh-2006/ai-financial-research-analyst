"""Extensive unit and integration tests for the deterministic Financial Analysis Engine."""
import pytest
from app.financial.cash_flow import calculate_cash_flow_analysis
from app.financial.engine import FinancialAnalysisEngine
from app.financial.growth import calculate_growth_analysis
from app.financial.health import evaluate_financial_health
from app.financial.leverage import calculate_leverage_analysis
from app.financial.profitability import calculate_profitability_analysis
from app.financial.schemas import FinancialAnalysis
from app.financial.valuation_metrics import calculate_valuation_metrics
from app.schemas.financial import (
    CompanyData,
    CompanyProfile,
    HistoricalFinancial,
    MarketData,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def standard_corporate_financials():
    """Provides 4 years of clean corporate financials for a profitable tech company."""
    return [
        HistoricalFinancial(
            fiscal_year=2021,
            revenue=100_000.0,
            operating_income=25_000.0,
            net_income=20_000.0,
            operating_cash_flow=30_000.0,
            capex=5_000.0,
            free_cash_flow=25_000.0,
            total_debt=20_000.0,
            stockholders_equity=50_000.0,
        ),
        HistoricalFinancial(
            fiscal_year=2022,
            revenue=120_000.0,
            operating_income=32_000.0,
            net_income=26_000.0,
            operating_cash_flow=38_000.0,
            capex=6_000.0,
            free_cash_flow=32_000.0,
            total_debt=22_000.0,
            stockholders_equity=60_000.0,
        ),
        HistoricalFinancial(
            fiscal_year=2023,
            revenue=140_000.0,
            operating_income=40_000.0,
            net_income=33_000.0,
            operating_cash_flow=45_000.0,
            capex=7_000.0,
            free_cash_flow=38_000.0,
            total_debt=25_000.0,
            stockholders_equity=75_000.0,
        ),
        HistoricalFinancial(
            fiscal_year=2024,
            revenue=160_000.0,
            operating_income=48_000.0,
            net_income=40_000.0,
            operating_cash_flow=52_000.0,
            capex=8_000.0,
            free_cash_flow=44_000.0,
            total_debt=28_000.0,
            stockholders_equity=95_000.0,
        ),
    ]


@pytest.fixture
def bank_financials():
    """Provides financials typical of a commercial bank (no Capex, high leverage)."""
    return [
        HistoricalFinancial(
            fiscal_year=2023,
            revenue=50_000.0,
            operating_income=None,
            net_income=15_000.0,
            operating_cash_flow=10_000.0,
            capex=None,
            free_cash_flow=None,
            total_debt=40_000.0,
            stockholders_equity=100_000.0,
        ),
        HistoricalFinancial(
            fiscal_year=2024,
            revenue=55_000.0,
            operating_income=None,
            net_income=16_500.0,
            operating_cash_flow=-5_000.0,
            capex=None,
            free_cash_flow=None,
            total_debt=45_000.0,
            stockholders_equity=110_000.0,
        ),
    ]


# ==============================================================================
# 1. GROWTH ANALYSIS TESTS
# ==============================================================================

def test_growth_revenue_yoy_and_cagr(standard_corporate_financials):
    growth = calculate_growth_analysis(standard_corporate_financials)
    # Latest YoY: (160k - 140k) / 140k = 14.2857%
    assert growth.revenue_growth_yoy is not None
    assert pytest.approx(growth.revenue_growth_yoy, rel=1e-3) == 0.142857

    # 3-year CAGR: (160k / 100k)^(1/3) - 1 = 16.96%
    assert growth.revenue_cagr_3yr is not None
    assert pytest.approx(growth.revenue_cagr_3yr, rel=1e-3) == 0.169607

    assert len(growth.revenue_growth_series) == 3


def test_growth_negative_and_zero_denominator():
    fin = [
        HistoricalFinancial(fiscal_year=2022, revenue=0.0, net_income=-10_000.0, free_cash_flow=0.0),
        HistoricalFinancial(fiscal_year=2023, revenue=50_000.0, net_income=5_000.0, free_cash_flow=10_000.0),
    ]
    growth = calculate_growth_analysis(fin)

    # Zero revenue base -> None
    assert growth.revenue_growth_yoy is None
    # Negative Net Income base -> None + note
    assert growth.net_income_growth_yoy is None
    assert "non-positive" in growth.net_income_growth_series[-1]["note"]
    # Zero FCF base -> None + note
    assert growth.fcf_growth_yoy is None


# ==============================================================================
# 2. PROFITABILITY TESTS
# ==============================================================================

def test_profitability_standard(standard_corporate_financials):
    prof = calculate_profitability_analysis(standard_corporate_financials)
    # Operating margin: 48k / 160k = 30%
    assert prof.operating_margin == 0.30
    # Net margin: 40k / 160k = 25%
    assert prof.net_margin == 0.25
    # Average equity: (95k + 75k) / 2 = 85k -> ROE: 40k / 85k = 47.0588%
    assert pytest.approx(prof.roe, rel=1e-3) == 0.470588
    # Average IC: 2024 = 28k + 95k = 123k; 2023 = 25k + 75k = 100k; Avg = 111.5k
    # ROIC = 48k / 111.5k = 43.0493%
    assert pytest.approx(prof.roic, rel=1e-3) == 0.430493
    # Gross margin is strictly None when not broken out
    assert prof.gross_margin is None


def test_profitability_negative_equity():
    fin = [
        HistoricalFinancial(
            fiscal_year=2024,
            revenue=100_000.0,
            operating_income=10_000.0,
            net_income=5_000.0,
            stockholders_equity=-20_000.0,
        )
    ]
    prof = calculate_profitability_analysis(fin)
    assert prof.roe is None
    assert "non-positive" in prof.metrics["roe"].warning


# ==============================================================================
# 3. LEVERAGE TESTS
# ==============================================================================

def test_leverage_standard(standard_corporate_financials):
    lev = calculate_leverage_analysis(standard_corporate_financials)
    # Debt-to-Equity: 28k / 95k = 0.2947x
    assert pytest.approx(lev.debt_to_equity, rel=1e-3) == 0.294736
    # EBITDA and Interest Coverage are None with clear explanations
    assert lev.debt_to_ebitda is None
    assert lev.interest_coverage is None
    assert "EBITDA cannot be reliably derived" in lev.metrics["debt_to_ebitda"].warning


def test_leverage_zero_and_negative_equity():
    fin = [HistoricalFinancial(fiscal_year=2024, total_debt=50_000.0, stockholders_equity=0.0)]
    lev = calculate_leverage_analysis(fin)
    assert lev.debt_to_equity is None
    assert "non-positive" in lev.metrics["debt_to_equity"].warning


# ==============================================================================
# 4. CASH FLOW TESTS
# ==============================================================================

def test_cash_flow_standard(standard_corporate_financials):
    cf = calculate_cash_flow_analysis(standard_corporate_financials)
    assert cf.operating_cash_flow == 52_000.0
    assert cf.capex == 8_000.0
    assert cf.free_cash_flow == 44_000.0
    # FCF Margin: 44k / 160k = 27.5%
    assert cf.fcf_margin == 0.275
    # FCF Conversion: 44k / 40k = 110%
    assert cf.fcf_conversion == 1.10


def test_cash_flow_missing_capex_and_negative_ni():
    fin = [
        HistoricalFinancial(
            fiscal_year=2024,
            revenue=100_000.0,
            operating_cash_flow=20_000.0,
            capex=None,
            free_cash_flow=None,
            net_income=-5_000.0,
        )
    ]
    cf = calculate_cash_flow_analysis(fin)
    assert cf.free_cash_flow is None
    assert cf.fcf_margin is None
    assert cf.fcf_conversion is None


# ==============================================================================
# 5. VALUATION MULTIPLES TESTS
# ==============================================================================

def test_valuation_multiples(standard_corporate_financials):
    market = MarketData(
        market_cap=800_000.0,
        enterprise_value=820_000.0,
        pe_ratio=20.0,
        forward_pe=18.0,
        ev_to_ebitda=14.0,
    )
    val = calculate_valuation_metrics(market, standard_corporate_financials)
    assert val.pe_ratio == 20.0
    assert val.forward_pe == 18.0
    assert val.ev_to_ebitda == 14.0
    # Price-to-Sales: 800k / 160k = 5.0x
    assert val.price_to_sales == 5.0
    # Price-to-FCF: 800k / 44k = 18.1818x
    assert pytest.approx(val.price_to_fcf, rel=1e-3) == 18.1818


# ==============================================================================
# 6. FINANCIAL HEALTH EVALUATION TESTS
# ==============================================================================

def test_health_evaluation_strong_company(standard_corporate_financials):
    growth = calculate_growth_analysis(standard_corporate_financials)
    prof = calculate_profitability_analysis(standard_corporate_financials)
    lev = calculate_leverage_analysis(standard_corporate_financials)
    cf = calculate_cash_flow_analysis(standard_corporate_financials)

    health = evaluate_financial_health(growth, prof, lev, cf, sector="Technology")
    assert health.overall == "Strong"
    assert health.growth_pillar == "Strong"
    assert health.profitability_pillar == "Strong"
    assert health.cash_flow_pillar == "Strong"


def test_health_evaluation_bank(bank_financials):
    growth = calculate_growth_analysis(bank_financials, sector="Financial Services")
    prof = calculate_profitability_analysis(bank_financials, sector="Financial Services")
    lev = calculate_leverage_analysis(bank_financials, sector="Financial Services")
    cf = calculate_cash_flow_analysis(bank_financials, sector="Financial Services")

    health = evaluate_financial_health(growth, prof, lev, cf, sector="Financial Services")
    # FCF must be Neutral, NOT Weak
    assert health.cash_flow_pillar == "Neutral"
    assert health.profitability_pillar == "Strong"
    assert health.overall in ("Strong", "Moderate")


# ==============================================================================
# 7. END-TO-END ENGINE INTEGRATION TEST
# ==============================================================================

def test_financial_engine_end_to_end(standard_corporate_financials):
    company_data = CompanyData(
        ticker="TEST",
        company_profile=CompanyProfile(
            ticker="TEST", name="Test Enterprise", sector="Technology", industry="Software"
        ),
        historical_financials=standard_corporate_financials,
        market_data=MarketData(market_cap=500_000.0, pe_ratio=15.0),
    )

    engine = FinancialAnalysisEngine()
    analysis = engine.analyze(company_data)

    assert isinstance(analysis, FinancialAnalysis)
    assert analysis.ticker == "TEST"
    assert len(analysis.historical_trends) == 4
    # Check trend continuity
    assert analysis.historical_trends[-1].revenue == 160_000.0
    assert analysis.historical_trends[-1].operating_margin == 0.30
    assert analysis.growth.revenue_growth_yoy is not None
    assert analysis.health.overall == "Strong"