"""Deterministic profitability calculations (Margins, ROE, and ROIC)."""
from typing import List, Optional
from app.financial.schemas import Metric, ProfitabilityAnalysis
from app.schemas.financial import HistoricalFinancial


def calculate_profitability_analysis(
    financials: List[HistoricalFinancial], sector: Optional[str] = None
) -> ProfitabilityAnalysis:
    """
    Computes deterministic profitability and return metrics for the latest fiscal period.
    Handles average balance sheet denominators and prevents distorted ratios from
    negative or zero equity.
    """
    if not financials:
        return ProfitabilityAnalysis()

    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year)
    latest = sorted_fin[-1]
    prev = sorted_fin[-2] if len(sorted_fin) >= 2 else None

    # 1. Gross Margin (Strict: only if gross profit is reported; otherwise None)
    gross_margin_val = None
    gross_warning = "Gross profit not separately broken out in standardized 10-K extraction."

    # 2. Operating Margin
    op_margin_val = None
    op_margin_warning = None
    if latest.operating_income is not None and latest.revenue is not None:
        if latest.revenue > 0:
            op_margin_val = latest.operating_income / latest.revenue
        else:
            op_margin_warning = "Revenue non-positive; operating margin undefined."
    else:
        op_margin_warning = "Operating income or revenue missing for latest period."

    # 3. Net Margin
    net_margin_val = None
    net_margin_warning = None
    if latest.net_income is not None and latest.revenue is not None:
        if latest.revenue > 0:
            net_margin_val = latest.net_income / latest.revenue
        else:
            net_margin_warning = "Revenue non-positive; net margin undefined."
    else:
        net_margin_warning = "Net income or revenue missing for latest period."

    # 4. Return on Equity (ROE) using Average Shareholders' Equity
    roe_val = None
    roe_formula = "Net Income / Average Shareholders' Equity"
    roe_warning = None

    if latest.net_income is not None and latest.stockholders_equity is not None:
        avg_equity = latest.stockholders_equity
        if prev and prev.stockholders_equity is not None:
            avg_equity = (latest.stockholders_equity + prev.stockholders_equity) / 2.0
            roe_formula = "Net Income / ((Equity_t + Equity_t-1) / 2)"
        else:
            roe_formula = "Net Income / Ending Shareholders' Equity"
            roe_warning = "Calculated using ending equity; prior-year balance unavailable for 2-period average."

        if avg_equity > 0:
            roe_val = latest.net_income / avg_equity
        else:
            roe_warning = "Shareholders' equity is non-positive; ROE is economically distorted."
    else:
        roe_warning = "Net income or shareholders' equity unavailable for latest period."

    # 5. Return on Invested Capital (ROIC)
    # Formula: Operating Income / Average Invested Capital (Total Debt + Equity)
    roic_val = None
    roic_formula = "Operating Income / Average Invested Capital (Debt + Equity)"
    roic_warning = None

    if latest.operating_income is not None and latest.stockholders_equity is not None:
        curr_debt = latest.total_debt or 0.0
        curr_ic = curr_debt + latest.stockholders_equity

        avg_ic = curr_ic
        if prev and prev.stockholders_equity is not None:
            prev_debt = prev.total_debt or 0.0
            prev_ic = prev_debt + prev.stockholders_equity
            avg_ic = (curr_ic + prev_ic) / 2.0
            roic_formula = "Operating Income / ((Invested Capital_t + Invested Capital_t-1) / 2)"
        else:
            roic_formula = "Operating Income / Ending Invested Capital"
            roic_warning = "Calculated using ending invested capital; prior-year balance unavailable for averaging."

        if avg_ic > 0:
            roic_val = latest.operating_income / avg_ic
        else:
            roic_warning = "Invested capital is non-positive; ROIC is economically distorted."
    else:
        roic_warning = "Operating income, debt, or equity unavailable for latest period."

    # 6. Assemble Explainable Metric Objects
    metrics = {
        "gross_margin": Metric(
            value=gross_margin_val,
            unit="percentage",
            formula="Gross Profit / Revenue",
            source_fields=["revenue"],
            status="available" if gross_margin_val is not None else "unavailable",
            warning=gross_warning,
        ),
        "operating_margin": Metric(
            value=op_margin_val,
            unit="percentage",
            formula="Operating Income / Revenue",
            source_fields=["operating_income", "revenue"],
            status="available" if op_margin_val is not None else "unavailable",
            warning=op_margin_warning,
        ),
        "net_margin": Metric(
            value=net_margin_val,
            unit="percentage",
            formula="Net Income / Revenue",
            source_fields=["net_income", "revenue"],
            status="available" if net_margin_val is not None else "unavailable",
            warning=net_margin_warning,
        ),
        "roe": Metric(
            value=roe_val,
            unit="percentage",
            formula=roe_formula,
            source_fields=["net_income", "stockholders_equity"],
            status="available" if roe_val is not None else "unavailable",
            warning=roe_warning,
        ),
        "roic": Metric(
            value=roic_val,
            unit="percentage",
            formula=roic_formula,
            source_fields=["operating_income", "total_debt", "stockholders_equity"],
            status="available" if roic_val is not None else "unavailable",
            warning=roic_warning,
        ),
    }

    return ProfitabilityAnalysis(
        gross_margin=gross_margin_val,
        operating_margin=op_margin_val,
        net_margin=net_margin_val,
        roe=roe_val,
        roic=roic_val,
        metrics=metrics,
    )