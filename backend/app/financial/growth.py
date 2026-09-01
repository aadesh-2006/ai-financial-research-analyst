"""Deterministic growth calculations (Revenue, Net Income, and Free Cash Flow)."""
from typing import List, Optional
from app.financial.schemas import GrowthAnalysis, Metric
from app.schemas.financial import HistoricalFinancial


def calculate_growth_analysis(
    financials: List[HistoricalFinancial], sector: Optional[str] = None
) -> GrowthAnalysis:
    """
    Computes deterministic growth metrics and historical time series.
    Chronologically sorts annual data and safeguards against division-by-zero
    and negative/zero denominator anomalies.
    """
    if not financials:
        return GrowthAnalysis()

    # Sort chronologically by fiscal year
    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year)
    
    rev_series = []
    ni_series = []
    fcf_series = []

    # 1. Year-over-Year Series Calculations
    for i in range(1, len(sorted_fin)):
        curr = sorted_fin[i]
        prev = sorted_fin[i - 1]
        fy = curr.fiscal_year

        # Revenue YoY
        rev_growth = None
        if curr.revenue is not None and prev.revenue is not None:
            if prev.revenue > 0:
                rev_growth = (curr.revenue - prev.revenue) / prev.revenue

        rev_series.append({
            "fiscal_year": fy,
            "revenue": curr.revenue,
            "previous_revenue": prev.revenue,
            "growth": rev_growth,
        })

        # Net Income YoY (handles negative/zero base cleanly)
        ni_growth = None
        ni_note = None
        if curr.net_income is not None and prev.net_income is not None:
            if prev.net_income > 0:
                ni_growth = (curr.net_income - prev.net_income) / prev.net_income
            else:
                ni_note = "Prior-year net income non-positive; percentage growth undefined."

        ni_series.append({
            "fiscal_year": fy,
            "net_income": curr.net_income,
            "previous_net_income": prev.net_income,
            "growth": ni_growth,
            "note": ni_note,
        })

        # Free Cash Flow YoY
        fcf_growth = None
        fcf_note = None
        if curr.free_cash_flow is not None and prev.free_cash_flow is not None:
            if prev.free_cash_flow > 0:
                fcf_growth = (curr.free_cash_flow - prev.free_cash_flow) / prev.free_cash_flow
            else:
                fcf_note = "Prior-year FCF non-positive; percentage growth undefined."
        else:
            fcf_note = "FCF unavailable for period (common for financial institutions)."

        fcf_series.append({
            "fiscal_year": fy,
            "free_cash_flow": curr.free_cash_flow,
            "previous_free_cash_flow": prev.free_cash_flow,
            "growth": fcf_growth,
            "note": fcf_note,
        })

    # 2. Latest YoY Metrics
    latest_rev_growth = rev_series[-1]["growth"] if rev_series else None
    latest_ni_growth = ni_series[-1]["growth"] if ni_series else None
    latest_fcf_growth = fcf_series[-1]["growth"] if fcf_series else None

    # 3. Revenue CAGR Calculation (Prefer 3-year, fallback to available periods >= 2)
    cagr_val = None
    cagr_formula = "(Revenue_latest / Revenue_initial)^(1/n) - 1"
    cagr_warning = None

    valid_rev_fin = [f for f in sorted_fin if f.revenue is not None and f.revenue > 0]
    if len(valid_rev_fin) >= 4:
        # Exactly 3-year span (t and t-3)
        end_f = valid_rev_fin[-1]
        start_f = valid_rev_fin[-4]
        years_span = end_f.fiscal_year - start_f.fiscal_year
        if years_span == 3 and start_f.revenue > 0:
            cagr_val = (end_f.revenue / start_f.revenue) ** (1.0 / 3.0) - 1.0
            cagr_formula = f"(Rev_{end_f.fiscal_year} / Rev_{start_f.fiscal_year})^(1/3) - 1"
    elif len(valid_rev_fin) >= 3:
        # 2-year span fallback
        end_f = valid_rev_fin[-1]
        start_f = valid_rev_fin[-3]
        years_span = end_f.fiscal_year - start_f.fiscal_year
        if years_span > 0 and start_f.revenue > 0:
            cagr_val = (end_f.revenue / start_f.revenue) ** (1.0 / float(years_span)) - 1.0
            cagr_formula = f"(Rev_{end_f.fiscal_year} / Rev_{start_f.fiscal_year})^(1/{years_span}) - 1"
            cagr_warning = f"Calculated across {years_span} years due to available historical depth."
    else:
        cagr_warning = "Insufficient positive revenue periods for CAGR computation."

    # 4. Assemble Explainable Metric Objects
    metrics = {
        "revenue_growth_yoy": Metric(
            value=latest_rev_growth,
            unit="percentage",
            formula="(Revenue_t - Revenue_t-1) / Revenue_t-1",
            source_fields=["revenue"],
            status="available" if latest_rev_growth is not None else "unavailable",
            warning="Prior-year revenue missing or zero" if latest_rev_growth is None else None,
        ),
        "revenue_cagr_3yr": Metric(
            value=cagr_val,
            unit="percentage",
            formula=cagr_formula,
            source_fields=["revenue"],
            status="available" if cagr_val is not None else "unavailable",
            warning=cagr_warning,
        ),
        "net_income_growth_yoy": Metric(
            value=latest_ni_growth,
            unit="percentage",
            formula="(NetIncome_t - NetIncome_t-1) / NetIncome_t-1",
            source_fields=["net_income"],
            status="available" if latest_ni_growth is not None else "unavailable",
            warning=ni_series[-1]["note"] if (ni_series and ni_series[-1]["note"]) else None,
        ),
        "fcf_growth_yoy": Metric(
            value=latest_fcf_growth,
            unit="percentage",
            formula="(FCF_t - FCF_t-1) / FCF_t-1",
            source_fields=["operating_cash_flow", "capex"],
            status="available" if latest_fcf_growth is not None else "unavailable",
            warning=fcf_series[-1]["note"] if (fcf_series and fcf_series[-1]["note"]) else None,
        ),
    }

    return GrowthAnalysis(
        revenue_growth_yoy=latest_rev_growth,
        revenue_cagr_3yr=cagr_val,
        net_income_growth_yoy=latest_ni_growth,
        fcf_growth_yoy=latest_fcf_growth,
        revenue_growth_series=rev_series,
        net_income_growth_series=ni_series,
        fcf_growth_series=fcf_series,
        metrics=metrics,
    )