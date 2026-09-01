"""Deterministic cash flow analysis (OCF, Capex, FCF, FCF Margin, and Conversion)."""
from typing import List, Optional
from app.financial.schemas import CashFlowAnalysis, Metric
from app.schemas.financial import HistoricalFinancial


def calculate_cash_flow_analysis(
    financials: List[HistoricalFinancial], sector: Optional[str] = None
) -> CashFlowAnalysis:
    """
    Computes deterministic cash flow metrics for the latest fiscal period.
    Safeguards against distorted conversion rates when Net Income or Revenue is non-positive,
    and cleanly handles missing Capex for financial institutions.
    """
    if not financials:
        return CashFlowAnalysis()

    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year)
    latest = sorted_fin[-1]

    ocf = latest.operating_cash_flow
    capex = latest.capex
    fcf = latest.free_cash_flow

    # 1. FCF Margin (FCF / Revenue)
    fcf_margin = None
    fcf_margin_warning = None
    if fcf is not None and latest.revenue is not None:
        if latest.revenue > 0:
            fcf_margin = fcf / latest.revenue
        else:
            fcf_margin_warning = "Revenue non-positive; FCF margin undefined."
    elif fcf is None:
        fcf_margin_warning = "Free cash flow unavailable for period (common for financial institutions)."
    else:
        fcf_margin_warning = "Revenue unavailable for period."

    # 2. FCF Conversion (FCF / Net Income)
    fcf_conversion = None
    fcf_conversion_warning = None
    if fcf is not None and latest.net_income is not None:
        if latest.net_income > 0:
            fcf_conversion = fcf / latest.net_income
        else:
            fcf_conversion_warning = "Net income is non-positive; FCF conversion is mathematically distorted."
    elif fcf is None:
        fcf_conversion_warning = "Free cash flow unavailable for conversion calculation."
    else:
        fcf_conversion_warning = "Net income unavailable for conversion calculation."

    # 3. Assemble Explainable Metric Objects
    metrics = {
        "operating_cash_flow": Metric(
            value=ocf,
            unit="currency",
            formula="Operating Cash Flow",
            source_fields=["operating_cash_flow"],
            status="available" if ocf is not None else "unavailable",
            warning=None if ocf is not None else "Operating cash flow line item missing.",
        ),
        "capex": Metric(
            value=capex,
            unit="currency",
            formula="Capital Expenditures (Property, Plant & Equipment additions)",
            source_fields=["capex"],
            status="available" if capex is not None else "unavailable",
            warning="Capex not reported in 10-K (common for financial institutions)." if capex is None else None,
        ),
        "free_cash_flow": Metric(
            value=fcf,
            unit="currency",
            formula="Operating Cash Flow - Capex",
            source_fields=["operating_cash_flow", "capex"],
            status="available" if fcf is not None else "unavailable",
            warning="Free cash flow could not be calculated due to missing Capex or OCF." if fcf is None else None,
        ),
        "fcf_margin": Metric(
            value=fcf_margin,
            unit="percentage",
            formula="Free Cash Flow / Revenue",
            source_fields=["free_cash_flow", "revenue"],
            status="available" if fcf_margin is not None else "unavailable",
            warning=fcf_margin_warning,
        ),
        "fcf_conversion": Metric(
            value=fcf_conversion,
            unit="ratio",
            formula="Free Cash Flow / Net Income",
            source_fields=["free_cash_flow", "net_income"],
            status="available" if fcf_conversion is not None else "unavailable",
            warning=fcf_conversion_warning,
        ),
    }

    return CashFlowAnalysis(
        operating_cash_flow=ocf,
        capex=capex,
        free_cash_flow=fcf,
        fcf_margin=fcf_margin,
        fcf_conversion=fcf_conversion,
        metrics=metrics,
    )