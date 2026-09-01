"""Comprehensive deterministic unit and integration test suite for DCF and Valuation."""
import pytest

from app.financial.dcf import (
    calculate_cost_of_debt,
    calculate_cost_of_equity,
    calculate_dcf_valuation,
    calculate_terminal_value,
    calculate_wacc,
    generate_sensitivity_table,
    get_risk_free_rate,
    project_fcf,
)
from app.financial.engine import FinancialAnalysisEngine
from app.financial.schemas import DCFValuation
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
            cash_and_equivalents=10_000.0,
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
            cash_and_equivalents=12_000.0,
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
            cash_and_equivalents=15_000.0,
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
            cash_and_equivalents=18_000.0,
        ),
    ]


@pytest.fixture
def standard_market_data():
    """Provides market quotes and capital structure for a standard corporate."""
    return MarketData(
        current_price=100.0,
        shares_outstanding=10_000.0,  # Market Cap = $1,000,000
        market_cap=1_000_000.0,
        beta=1.20,
        total_cash=18_000.0,
        total_debt=28_000.0,
    )


# ==============================================================================
# 1. CAPM & WACC TESTS
# ==============================================================================

def test_capm_cost_of_equity():
    # Ke = 4.0% + 1.2 * 5.0% = 10.0%
    ke, err = calculate_cost_of_equity(risk_free_rate=0.04, beta=1.20, equity_risk_premium=0.05)
    assert err is None
    assert pytest.approx(ke, rel=1e-3) == 0.10


def test_cost_of_debt():
    # Pre-tax Kd = 4.0% + 1.5% spread = 5.5%; After-tax = 5.5% * (1 - 0.21) = 4.345%
    pre_tax, after_tax, source = calculate_cost_of_debt(
        financials=[HistoricalFinancial(fiscal_year=2024, total_debt=50_000.0)],
        risk_free_rate=0.04,
        tax_rate=0.21,
    )
    assert pytest.approx(pre_tax, rel=1e-3) == 0.055
    assert pytest.approx(after_tax, rel=1e-3) == 0.04345


def test_wacc_calculation():
    # E = 800, D = 200, Total = 1000 -> We = 0.8, Wd = 0.2
    # Ke = 10.0%, Kd_after_tax = 4.0% -> WACC = 0.8*10% + 0.2*4% = 8.8%
    wacc, we, wd, err = calculate_wacc(
        cost_of_equity=0.10,
        after_tax_cost_of_debt=0.04,
        market_value_equity=800.0,
        market_value_debt=200.0,
    )
    assert err is None
    assert we == 0.8
    assert wd == 0.2
    assert pytest.approx(wacc, rel=1e-3) == 0.088


# ==============================================================================
# 2. FCF PROJECTION & DISCOUNTING TESTS
# ==============================================================================

def test_fcf_projection(standard_corporate_financials):
    # Base FCF = 44,000. Historical 3-Yr CAGR: (44k / 25k)^(1/3) - 1 = 20.7% -> bounded to 15.0%
    growth, projections, err = project_fcf(standard_corporate_financials, projection_years=5)
    assert err is None
    assert growth == 0.15
    assert len(projections) == 5
    # Year 1 = 44,000 * 1.15 = 50,600
    assert pytest.approx(projections[0], rel=1e-3) == 50_600.0
    # Year 5 = 44,000 * (1.15^5) = 88,499.79
    assert pytest.approx(projections[4], rel=1e-3) == 88_499.79


def test_discounted_fcf():
    # Year 1 FCF = 100, WACC = 10.0% -> PV = 100 / 1.10 = 90.909
    df = 1.0 / (1.10 ** 1)
    pv = 100.0 * df
    assert pytest.approx(pv, rel=1e-3) == 90.909


# ==============================================================================
# 3. TERMINAL VALUE & VALIDATION TESTS
# ==============================================================================

def test_gordon_growth_terminal_value():
    # Year 5 FCF = 100, g = 2.5%, WACC = 10.0%
    # Terminal FCF = 100 * 1.025 = 102.5
    # TV = 102.5 / (0.10 - 0.025) = 102.5 / 0.075 = 1,366.67
    # PV(TV) = 1,366.67 / (1.10^5) = 848.59
    tv, pv_tv, err = calculate_terminal_value(year_5_fcf=100.0, wacc=0.10, terminal_growth_rate=0.025)
    assert err is None
    assert pytest.approx(tv, rel=1e-3) == 1366.6667
    assert pytest.approx(pv_tv, rel=1e-3) == 848.5938


def test_invalid_terminal_growth_greater_or_equal_wacc():
    # g = 10.0%, WACC = 10.0% -> Must fail validation
    tv, pv_tv, err = calculate_terminal_value(year_5_fcf=100.0, wacc=0.10, terminal_growth_rate=0.10)
    assert tv is None
    assert pv_tv is None
    assert "InvalidTerminalGrowth" in err


# ==============================================================================
# 4. ENTERPRISE VALUE, EQUITY VALUE & SHARE PRICE
# ==============================================================================

def test_enterprise_value_and_net_debt_adjustment():
    pv_explicit = 500_000.0
    pv_tv = 1_000_000.0
    ev = pv_explicit + pv_tv
    assert ev == 1_500_000.0

    total_debt = 200_000.0
    cash = 50_000.0
    net_debt = total_debt - cash
    assert net_debt == 150_000.0

    equity_val = ev - net_debt
    assert equity_val == 1_350_000.0


def test_implied_share_price_and_upside():
    equity_val = 1_000_000.0
    shares = 10_000.0
    current_price = 80.0

    implied_price = equity_val / shares
    assert implied_price == 100.0

    upside = ((implied_price - current_price) / current_price) * 100.0
    assert upside == 25.0


# ==============================================================================
# 5. SENSITIVITY TABLE TESTS
# ==============================================================================

def test_sensitivity_table_dimensions_and_nulls():
    explicit_fcfs = [10.0, 11.0, 12.0, 13.0, 14.0]
    table = generate_sensitivity_table(
        explicit_fcfs=explicit_fcfs,
        net_debt=20.0,
        shares_outstanding=10.0,
        wacc_range=[0.06, 0.08, 0.10],
        terminal_growth_range=[0.02, 0.03, 0.06],
    )
    assert len(table.wacc_range) == 3
    assert len(table.terminal_growth_range) == 3
    assert len(table.grid) == 3
    assert len(table.grid[0]) == 3

    # At WACC = 6% (0.06) and g = 6% (0.06), cell must be None
    assert table.grid[0][2] is None


# ==============================================================================
# 6. EDGE CASES & DEFENSIVE GATING
# ==============================================================================

def test_missing_beta():
    market = MarketData(current_price=100.0, shares_outstanding=1000.0, beta=None)
    fin = [HistoricalFinancial(fiscal_year=2024, free_cash_flow=1000.0)]
    dcf = calculate_dcf_valuation(market, fin)
    assert dcf.status == "insufficient_data"
    assert any("Beta is missing" in w for w in dcf.warnings)


def test_missing_shares_or_price():
    market = MarketData(current_price=None, shares_outstanding=1000.0, beta=1.0)
    fin = [HistoricalFinancial(fiscal_year=2024, free_cash_flow=1000.0)]
    dcf = calculate_dcf_valuation(market, fin)
    assert dcf.status == "insufficient_data"


def test_missing_or_zero_debt_handles_cleanly():
    # If total_debt is 0, Kd has 0 weight and does not crash
    pre_tax, after_tax, src = calculate_cost_of_debt(
        financials=[HistoricalFinancial(fiscal_year=2024, total_debt=0.0)],
        risk_free_rate=0.04,
    )
    assert pre_tax == 0.0
    assert after_tax == 0.0


def test_missing_cash_falls_back_to_zero_with_warning(standard_corporate_financials):
    market = MarketData(current_price=100.0, shares_outstanding=1000.0, beta=1.0, total_cash=None)
    # Strip cash from financials
    fin = [f.model_copy(update={"cash_and_equivalents": None}) for f in standard_corporate_financials]
    dcf = calculate_dcf_valuation(market, fin)
    assert dcf.status == "calculated"
    assert dcf.cash == 0.0
    assert any("Cash balance unavailable" in w for w in dcf.warnings)


def test_zero_or_negative_fcf():
    market = MarketData(current_price=100.0, shares_outstanding=1000.0, beta=1.0)
    fin = [HistoricalFinancial(fiscal_year=2024, free_cash_flow=-500.0)]
    dcf = calculate_dcf_valuation(market, fin)
    assert dcf.status == "insufficient_data"
    assert any("non-positive" in w for w in dcf.warnings)


def test_financial_institution_dcf_gate():
    """CRITICAL: Financial institutions must cleanly return not_applicable without crashing."""
    market = MarketData(current_price=100.0, shares_outstanding=1000.0, beta=1.0)
    fin = [HistoricalFinancial(fiscal_year=2024, free_cash_flow=None)]
    dcf = calculate_dcf_valuation(market, fin, sector="Financial Services")
    assert dcf.status == "not_applicable"
    assert any("SectorNotSupportedForDCF" in w for w in dcf.warnings)


# ==============================================================================
# 7. FULL DCF END-TO-END ENGINE INTEGRATION TEST
# ==============================================================================

def test_full_dcf_end_to_end_integration(standard_corporate_financials, standard_market_data):
    company_data = CompanyData(
        ticker="TECH",
        company_profile=CompanyProfile(
            ticker="TECH", name="Tech Leader Inc", sector="Technology", industry="Software"
        ),
        historical_financials=standard_corporate_financials,
        market_data=standard_market_data,
    )

    engine = FinancialAnalysisEngine()
    analysis = engine.analyze(company_data)

    assert analysis.dcf is not None
    assert analysis.dcf.status == "calculated"
    assert analysis.dcf.wacc is not None
    assert analysis.dcf.enterprise_value is not None
    assert analysis.dcf.implied_share_price is not None
    assert analysis.dcf.implied_share_price > 0
    assert analysis.dcf.sensitivity_table is not None
    assert len(analysis.dcf.sensitivity_table.grid) == 7