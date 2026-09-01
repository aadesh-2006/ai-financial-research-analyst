"""Valuation multiples exposing market metrics and deterministic derivations."""
from typing import List, Optional
from app.financial.schemas import Metric, ValuationMetrics
from app.schemas.financial import HistoricalFinancial, MarketData


def calculate_valuation_metrics(
    market_data: MarketData,
    financials: List[HistoricalFinancial],
    sector: Optional[str] = None,
) -> ValuationMetrics:
    """
    Exposes provider-reported valuation multiples (P/E, Forward P/E, EV/EBITDA)
    and computes deterministic multiples (Price-to-Sales, Price-to-FCF).
    """
    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year) if financials else []
    latest = sorted_fin[-1] if sorted_fin else None

    market_cap = market_data.market_cap
    ev = market_data.enterprise_value
    pe = market_data.pe_ratio
    forward_pe = market_data.forward_pe
    ev_ebitda = market_data.ev_to_ebitda

    # 1. Deterministic Price-to-Sales (P/S = Market Cap / Latest Revenue)
    ps_val = None
    ps_warning = None
    if market_cap is not None and latest and latest.revenue is not None:
        if latest.revenue > 0:
            ps_val = market_cap / latest.revenue
        else:
            ps_warning = "Latest annual revenue is non-positive; P/S undefined."
    else:
        ps_warning = "Market capitalization or latest revenue unavailable."

    # 2. Deterministic Price-to-FCF (P/FCF = Market Cap / Latest FCF)
    p_fcf_val = None
    p_fcf_warning = None
    if market_cap is not None and latest and latest.free_cash_flow is not None:
        if latest.free_cash_flow > 0:
            p_fcf_val = market_cap / latest.free_cash_flow
        else:
            p_fcf_warning = "Latest annual FCF is non-positive; Price-to-FCF undefined."
    elif latest and latest.free_cash_flow is None:
        p_fcf_warning = "Free cash flow unavailable for latest fiscal period."
    else:
        p_fcf_warning = "Market capitalization or free cash flow unavailable."

    # 3. Assemble Explainable Metric Objects
    metrics = {
        "pe_ratio": Metric(
            value=pe,
            unit="multiple",
            formula="Provider Reported: Current Price / Trailing EPS",
            source_fields=["market_data.pe_ratio"],
            status="available" if pe is not None else "unavailable",
            warning="Trailing P/E not reported (common for unprofitable entities)." if pe is None else None,
        ),
        "forward_pe": Metric(
            value=forward_pe,
            unit="multiple",
            formula="Provider Reported: Current Price / Consensus Forward EPS",
            source_fields=["market_data.forward_pe"],
            status="available" if forward_pe is not None else "unavailable",
            warning="Forward P/E estimate unavailable from market consensus." if forward_pe is None else None,
        ),
        "ev_to_ebitda": Metric(
            value=ev_ebitda,
            unit="multiple",
            formula="Provider Reported: Enterprise Value / EBITDA",
            source_fields=["market_data.ev_to_ebitda"],
            status="available" if ev_ebitda is not None else "unavailable",
            warning="EV/EBITDA not applicable or unavailable (common for banks/financials)." if ev_ebitda is None else None,
        ),
        "price_to_sales": Metric(
            value=ps_val,
            unit="multiple",
            formula="Engine Derived: Market Cap / Latest Annual Revenue",
            source_fields=["market_data.market_cap", "historical_financials.revenue"],
            status="available" if ps_val is not None else "unavailable",
            warning=ps_warning,
        ),
        "price_to_fcf": Metric(
            value=p_fcf_val,
            unit="multiple",
            formula="Engine Derived: Market Cap / Latest Annual Free Cash Flow",
            source_fields=["market_data.market_cap", "historical_financials.free_cash_flow"],
            status="available" if p_fcf_val is not None else "unavailable",
            warning=p_fcf_warning,
        ),
    }

    return ValuationMetrics(
        pe_ratio=pe,
        forward_pe=forward_pe,
        ev_to_ebitda=ev_ebitda,
        price_to_sales=ps_val,
        price_to_fcf=p_fcf_val,
        market_cap=market_cap,
        enterprise_value=ev,
        metrics=metrics,
    )