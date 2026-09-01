"""Deterministic financial health analysis across Growth, Profitability, Leverage, and Cash Flow."""
from typing import List, Optional
from app.financial.schemas import (
    CashFlowAnalysis,
    FinancialHealth,
    GrowthAnalysis,
    LeverageAnalysis,
    ProfitabilityAnalysis,
)


def evaluate_financial_health(
    growth: GrowthAnalysis,
    profitability: ProfitabilityAnalysis,
    leverage: LeverageAnalysis,
    cash_flow: CashFlowAnalysis,
    sector: Optional[str] = None,
) -> FinancialHealth:
    """
    Evaluates corporate financial characteristics into transparent, rule-based qualitative pillars.
    Avoids arbitrary black-box scores and explicitly accommodates financial institution accounting.
    """
    is_financial_institution = False
    if sector and ("Financial" in sector or "Bank" in sector):
        is_financial_institution = True

    key_observations: List[str] = []
    warnings: List[str] = []

    # --------------------------------------------------------------------------
    # 1. Growth Pillar
    # --------------------------------------------------------------------------
    rev_g = growth.revenue_growth_yoy
    ni_g = growth.net_income_growth_yoy
    cagr = growth.revenue_cagr_3yr

    if rev_g is not None:
        if rev_g >= 0.12:
            growth_pillar = "Strong"
            key_observations.append(f"Robust top-line revenue expansion of {rev_g:.1%} YoY.")
        elif rev_g >= 0.03:
            growth_pillar = "Moderate"
            key_observations.append(f"Steady top-line revenue growth of {rev_g:.1%} YoY.")
        elif rev_g >= 0.0:
            growth_pillar = "Moderate"
            key_observations.append(f"Modest flat-to-positive revenue growth of {rev_g:.1%} YoY.")
        else:
            growth_pillar = "Weak"
            key_observations.append(f"Top-line revenue contracted by {abs(rev_g):.1%} YoY.")
    else:
        growth_pillar = "Neutral"
        warnings.append("Insufficient data to establish annual revenue growth trend.")

    # --------------------------------------------------------------------------
    # 2. Profitability Pillar
    # --------------------------------------------------------------------------
    op_m = profitability.operating_margin
    net_m = profitability.net_margin
    roe = profitability.roe

    if is_financial_institution:
        # For banks, ROE and Net Margin are standard primary profitability benchmarks
        if roe is not None and roe >= 0.12:
            prof_pillar = "Strong"
            key_observations.append(f"Strong banking return on equity (ROE) of {roe:.1%}.")
        elif roe is not None and roe >= 0.07:
            prof_pillar = "Moderate"
            key_observations.append(f"Moderate banking return on equity (ROE) of {roe:.1%}.")
        elif roe is not None and roe < 0.0:
            prof_pillar = "Weak"
            key_observations.append("Net loss reported; return on equity is negative.")
        else:
            prof_pillar = "Neutral"
    else:
        # Standard corporate profitability
        if op_m is not None and op_m >= 0.20 and (roe is None or roe >= 0.15):
            prof_pillar = "Strong"
            key_observations.append(f"High operating margin of {op_m:.1%} with strong returns on capital.")
        elif op_m is not None and op_m >= 0.08:
            prof_pillar = "Moderate"
            key_observations.append(f"Healthy operating profitability with an operating margin of {op_m:.1%}.")
        elif op_m is not None and op_m < 0.0:
            prof_pillar = "Weak"
            key_observations.append(f"Operating deficit reported with negative operating margin ({op_m:.1%}).")
        else:
            prof_pillar = "Neutral"

    # --------------------------------------------------------------------------
    # 3. Leverage Pillar
    # --------------------------------------------------------------------------
    de = leverage.debt_to_equity

    if is_financial_institution:
        # Commercial banks naturally operate with high asset/deposit leverage
        lev_pillar = "Moderate"
        key_observations.append("Financial institution balance sheet structured around deposit/borrowing leverage.")
    elif de is not None:
        if de <= 0.6:
            lev_pillar = "Strong"
            key_observations.append(f"Conservative capital structure with low Debt-to-Equity of {de:.2f}x.")
        elif de <= 2.0:
            lev_pillar = "Moderate"
            key_observations.append(f"Manageable leverage profile with Debt-to-Equity of {de:.2f}x.")
        else:
            lev_pillar = "Cautious"
            key_observations.append(f"Elevated leverage with Debt-to-Equity of {de:.2f}x.")
    else:
        lev_pillar = "Neutral"
        warnings.append("Debt or equity data unavailable to evaluate financial leverage.")

    # --------------------------------------------------------------------------
    # 4. Cash Flow Pillar
    # --------------------------------------------------------------------------
    fcf = cash_flow.free_cash_flow
    fcf_m = cash_flow.fcf_margin
    fcf_conv = cash_flow.fcf_conversion

    if is_financial_institution:
        cf_pillar = "Neutral"
        key_observations.append("Traditional Free Cash Flow (FCF) metric is not applicable to financial institutions.")
    elif fcf is not None and fcf > 0:
        if fcf_conv is not None and fcf_conv >= 0.85:
            cf_pillar = "Strong"
            key_observations.append(f"Exceptional cash conversion with FCF/Net Income of {fcf_conv:.1%}.")
        elif fcf_m is not None and fcf_m >= 0.10:
            cf_pillar = "Strong"
            key_observations.append(f"Strong cash generation with an FCF margin of {fcf_m:.1%}.")
        else:
            cf_pillar = "Moderate"
            key_observations.append(f"Positive free cash flow generation (${fcf:,.0f}).")
    elif fcf is not None and fcf <= 0:
        cf_pillar = "Weak"
        key_observations.append(f"Negative free cash flow reported (${fcf:,.0f}).")
    else:
        cf_pillar = "Neutral"
        warnings.append("Free cash flow could not be calculated.")

    # --------------------------------------------------------------------------
    # 5. Overall Synthesis
    # --------------------------------------------------------------------------
    pillars = [growth_pillar, prof_pillar, lev_pillar]
    if not is_financial_institution:
        pillars.append(cf_pillar)

    strong_count = pillars.count("Strong")
    weak_count = pillars.count("Weak")
    cautious_count = pillars.count("Cautious")

    if weak_count >= 2:
        overall = "Cautious"
    elif strong_count >= 3 and weak_count == 0 and cautious_count == 0:
        overall = "Strong"
    elif strong_count >= 2 and weak_count == 0:
        overall = "Strong"
    elif weak_count == 0 and cautious_count <= 1:
        overall = "Moderate"
    else:
        overall = "Moderate"

    return FinancialHealth(
        overall=overall,
        growth_pillar=growth_pillar,
        profitability_pillar=prof_pillar,
        leverage_pillar=lev_pillar,
        cash_flow_pillar=cf_pillar,
        key_observations=key_observations,
        warnings=warnings,
    )