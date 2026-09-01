"""Deterministic Discounted Cash Flow (DCF), WACC, Terminal Value, and Sensitivity Engine."""
from typing import Any, Dict, List, Optional, Tuple
import yfinance as yf

from app.financial.schemas import (
    DCFProjection,
    DCFValuation,
    Metric,
    SensitivityCell,
    SensitivityTable,
)
from app.schemas.financial import HistoricalFinancial, MarketData
from app.utils.logging import logger

# Configurable Default Assumptions
DEFAULT_RISK_FREE_RATE = 0.042       # 4.20% (10-Yr US Treasury benchmark fallback)
DEFAULT_EQUITY_RISK_PREMIUM = 0.050   # 5.00% (historical long-term equity risk premium)
DEFAULT_TERMINAL_GROWTH_RATE = 0.025  # 2.50% (long-term sustainable GDP growth rate)
DEFAULT_TAX_RATE = 0.210              # 21.0% (US federal corporate statutory tax rate)
DEFAULT_DEBT_SPREAD = 0.015           # 1.50% (150 bps corporate borrowing spread over Rf)

# Standard Sensitivity Grid Parameters
DEFAULT_WACC_RANGE = [0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12]
DEFAULT_TERMINAL_GROWTH_RANGE = [0.010, 0.015, 0.020, 0.025, 0.030, 0.035]


def get_risk_free_rate(fallback: float = DEFAULT_RISK_FREE_RATE) -> Tuple[float, str]:
    """
    Fetches the live 10-Year US Treasury yield (^TNX) via yfinance.
    Normalizes percentage quotes (e.g. 4.25 -> 0.0425) into decimal representation.
    """
    try:
        t = yf.Ticker("^TNX")
        info = t.info or {}
        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
        if price is not None:
            float_price = float(price)
            # Normalize percentage quotes (>0.20) into decimal
            rate = float_price / 100.0 if float_price > 0.20 else float_price
            if 0.001 <= rate <= 0.25:
                return rate, "Live 10-Year US Treasury yield (^TNX)"
    except Exception as e:
        logger.warning(f"Failed to fetch ^TNX risk-free rate: {e}")

    return fallback, f"Configurable default assumption ({fallback:.2%} benchmark fallback)"


def calculate_cost_of_equity(
    risk_free_rate: float,
    beta: Optional[float],
    equity_risk_premium: float = DEFAULT_EQUITY_RISK_PREMIUM,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes Cost of Equity using the Capital Asset Pricing Model (CAPM):
    Ke = Risk-Free Rate + Beta * Equity Risk Premium
    """
    if beta is None or beta <= 0:
        return None, "Beta is missing or non-positive; CAPM Cost of Equity undefined."

    ke = risk_free_rate + (beta * equity_risk_premium)
    return ke, None


def calculate_cost_of_debt(
    financials: List[HistoricalFinancial],
    risk_free_rate: float,
    tax_rate: float = DEFAULT_TAX_RATE,
) -> Tuple[float, float, str]:
    """
    Determines pre-tax and after-tax cost of debt.
    Kd_after_tax = Pre-tax Kd * (1 - Tax Rate)
    Uses corporate borrowing spread over Rf when interest expense is not isolated.
    """
    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year) if financials else []
    latest = sorted_fin[-1] if sorted_fin else None
    debt = latest.total_debt if latest else None

    if debt is None or debt <= 0:
        # Entity operates with zero or negligible debt
        return 0.0, 0.0, "Zero or negligible debt on balance sheet (0% debt weight)"

    # Benchmark spread assumption: Risk-free rate + 150 bps corporate spread
    pre_tax_kd = risk_free_rate + DEFAULT_DEBT_SPREAD
    after_tax_kd = pre_tax_kd * (1.0 - tax_rate)
    return pre_tax_kd, after_tax_kd, f"Rf ({risk_free_rate:.2%}) + {DEFAULT_DEBT_SPREAD:.2%} corporate spread"


def calculate_wacc(
    cost_of_equity: float,
    after_tax_cost_of_debt: float,
    market_value_equity: float,
    market_value_debt: float,
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
    """
    Computes Weighted Average Cost of Capital (WACC) using market value weights:
    WACC = (E / (D + E)) * Ke + (D / (D + E)) * Kd_after_tax
    """
    total_capital = market_value_equity + market_value_debt
    if total_capital <= 0:
        return None, None, None, "Total enterprise capital (Debt + Equity) is non-positive."

    we = market_value_equity / total_capital
    wd = market_value_debt / total_capital
    wacc = (we * cost_of_equity) + (wd * after_tax_cost_of_debt)

    return wacc, we, wd, None


def project_fcf(
    financials: List[HistoricalFinancial],
    projection_years: int = 5,
) -> Tuple[Optional[float], List[float], Optional[str]]:
    """
    Projects Free Cash Flows for 5 years using a bounded historical growth rate.
    Safeguards against negative starting cash flows and extreme growth spikes.
    """
    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year) if financials else []
    if not sorted_fin:
        return None, [], "No historical financial periods available for FCF projection."

    latest = sorted_fin[-1]
    base_fcf = latest.free_cash_flow

    if base_fcf is None or base_fcf <= 0:
        return (
            None,
            [],
            "Latest annual Free Cash Flow is non-positive or unavailable; standard DCF projection cannot be established.",
        )

    # Calculate historical FCF growth to inform forecast
    valid_fcfs = [f.free_cash_flow for f in sorted_fin if f.free_cash_flow is not None and f.free_cash_flow > 0]
    hist_growth = None
    if len(valid_fcfs) >= 4:
        # 3-year FCF CAGR
        hist_growth = (valid_fcfs[-1] / valid_fcfs[-4]) ** (1.0 / 3.0) - 1.0
    elif len(valid_fcfs) >= 2:
        # 1-year YoY FCF growth
        hist_growth = (valid_fcfs[-1] - valid_fcfs[-2]) / valid_fcfs[-2]

    # Bound growth assumption: minimum 2.0%, maximum 15.0%, default 4.0% if negative/erratic
    if hist_growth is not None and hist_growth > 0:
        fcf_growth = max(0.02, min(hist_growth, 0.15))
    else:
        fcf_growth = 0.04  # 4.0% conservative GDP/inflation benchmark

    projections = []
    curr = base_fcf
    for _ in range(projection_years):
        curr = curr * (1.0 + fcf_growth)
        projections.append(curr)

    return fcf_growth, projections, None


def calculate_terminal_value(
    year_5_fcf: float,
    wacc: float,
    terminal_growth_rate: float = DEFAULT_TERMINAL_GROWTH_RATE,
) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Computes Gordon Growth Terminal Value:
    Terminal Value = (Year 5 FCF * (1 + g)) / (WACC - g)
    PV Terminal Value = Terminal Value / (1 + WACC)^5
    """
    if terminal_growth_rate >= wacc:
        return (
            None,
            None,
            f"InvalidTerminalGrowth: Terminal growth rate ({terminal_growth_rate:.1%}) must be strictly less than WACC ({wacc:.1%}).",
        )

    terminal_fcf = year_5_fcf * (1.0 + terminal_growth_rate)
    tv = terminal_fcf / (wacc - terminal_growth_rate)
    pv_tv = tv / ((1.0 + wacc) ** 5)

    return tv, pv_tv, None


def generate_sensitivity_table(
    explicit_fcfs: List[float],
    net_debt: float,
    shares_outstanding: float,
    wacc_range: List[float] = DEFAULT_WACC_RANGE,
    terminal_growth_range: List[float] = DEFAULT_TERMINAL_GROWTH_RANGE,
) -> SensitivityTable:
    """
    Generates a deterministic 2D matrix evaluating implied share price
    across variations in WACC and Terminal Growth rates.
    """
    grid: List[List[Optional[float]]] = []
    cells: List[SensitivityCell] = []

    if not explicit_fcfs or shares_outstanding <= 0:
        return SensitivityTable(
            wacc_range=wacc_range,
            terminal_growth_range=terminal_growth_range,
            grid=[],
            cells=[],
        )

    year_5_fcf = explicit_fcfs[-1]
    n_years = len(explicit_fcfs)

    for w in wacc_range:
        row: List[Optional[float]] = []
        for tg in terminal_growth_range:
            if tg >= w:
                row.append(None)
                cells.append(SensitivityCell(wacc=w, terminal_growth=tg, implied_share_price=None))
                continue

            # PV of explicit forecast under scenario WACC
            pv_explicit = sum(fcf / ((1.0 + w) ** t) for t, fcf in enumerate(explicit_fcfs, 1))

            # Terminal Value under scenario WACC and growth
            tv = (year_5_fcf * (1.0 + tg)) / (w - tg)
            pv_tv = tv / ((1.0 + w) ** n_years)

            ev = pv_explicit + pv_tv
            equity_val = ev - net_debt
            price = equity_val / shares_outstanding

            clean_price = round(price, 2) if price > 0 else 0.0
            row.append(clean_price)
            cells.append(SensitivityCell(wacc=w, terminal_growth=tg, implied_share_price=clean_price))

        grid.append(row)

    return SensitivityTable(
        wacc_range=wacc_range,
        terminal_growth_range=terminal_growth_range,
        grid=grid,
        cells=cells,
    )


def calculate_dcf_valuation(
    market_data: MarketData,
    financials: List[HistoricalFinancial],
    sector: Optional[str] = None,
    risk_free_rate_override: Optional[float] = None,
    terminal_growth_override: Optional[float] = None,
    equity_risk_premium_override: Optional[float] = None,
) -> DCFValuation:
    """
    Executes the complete deterministic DCF valuation pipeline.
    Includes CAPM Cost of Equity, WACC, 5-Year FCF Projections, Gordon Growth Terminal Value,
    Enterprise/Equity Value, Implied Share Price, and 2D Sensitivity Matrix.
    Safely gates out financial institutions/banks.
    """
    warnings: List[str] = []

    # --------------------------------------------------------------------------
    # 1. Sector-Aware DCF Gate (Critical Rule)
    # --------------------------------------------------------------------------
    if sector and ("Financial" in sector or "Bank" in sector):
        gate_msg = (
            "SectorNotSupportedForDCF: Traditional Free Cash Flow DCF modeling is "
            "mathematically and conceptually inappropriate for financial institutions and banks. "
            "Commercial banks intermediate capital through interest spreads and regulatory capital "
            "rather than industrial capex and operating cash flow. Recommended valuation methodologies "
            "include Price-to-Earnings (P/E), Price-to-Book (P/B), and Return on Equity (ROE) benchmarking."
        )
        return DCFValuation(
            status="not_applicable",
            warnings=[gate_msg],
        )

    # --------------------------------------------------------------------------
    # 2. Input Parameter Resolution
    # --------------------------------------------------------------------------
    rf, rf_source = (
        (risk_free_rate_override, "User Override")
        if risk_free_rate_override is not None
        else get_risk_free_rate()
    )
    erp = equity_risk_premium_override or DEFAULT_EQUITY_RISK_PREMIUM
    tg = terminal_growth_override or DEFAULT_TERMINAL_GROWTH_RATE
    tax_rate = DEFAULT_TAX_RATE

    beta = market_data.beta
    current_price = market_data.current_price
    shares_out = market_data.shares_outstanding

    if beta is None or beta <= 0:
        warnings.append("Beta is missing from market data; DCF cannot compute Cost of Equity via CAPM.")
        return DCFValuation(status="insufficient_data", warnings=warnings)

    if current_price is None or current_price <= 0 or shares_out is None or shares_out <= 0:
        warnings.append("Current share price or shares outstanding unavailable; cannot establish capital structure.")
        return DCFValuation(status="insufficient_data", warnings=warnings)

    # --------------------------------------------------------------------------
    # 3. Cost of Equity (CAPM) & Cost of Debt
    # --------------------------------------------------------------------------
    ke, ke_err = calculate_cost_of_equity(rf, beta, erp)
    if ke_err or ke is None:
        warnings.append(ke_err or "Cost of Equity calculation failed.")
        return DCFValuation(status="insufficient_data", warnings=warnings)

    pre_tax_kd, after_tax_kd, kd_source = calculate_cost_of_debt(financials, rf, tax_rate)

    # --------------------------------------------------------------------------
    # 4. Capital Weights & WACC
    # --------------------------------------------------------------------------
    sorted_fin = sorted(financials, key=lambda x: x.fiscal_year) if financials else []
    latest = sorted_fin[-1] if sorted_fin else None

    # Market value of equity = Price * Shares
    mkt_equity = current_price * shares_out
    # Debt: latest SEC total debt or market data debt
    total_debt = (latest.total_debt if latest and latest.total_debt is not None else market_data.total_debt) or 0.0

    wacc, we, wd, wacc_err = calculate_wacc(ke, after_tax_kd, mkt_equity, total_debt)
    if wacc_err or wacc is None:
        warnings.append(wacc_err or "WACC calculation failed.")
        return DCFValuation(status="insufficient_data", warnings=warnings)

    # --------------------------------------------------------------------------
    # 5. 5-Year FCF Projections & Discounting
    # --------------------------------------------------------------------------
    fcf_growth, raw_projections, proj_err = project_fcf(financials, projection_years=5)
    if proj_err or not raw_projections:
        warnings.append(proj_err or "FCF projection failed.")
        return DCFValuation(
            status="insufficient_data",
            risk_free_rate=rf,
            beta=beta,
            cost_of_equity=ke,
            wacc=wacc,
            warnings=warnings,
        )

    dcf_projections: List[DCFProjection] = []
    pv_explicit = 0.0
    for t, proj_fcf in enumerate(raw_projections, 1):
        df = 1.0 / ((1.0 + wacc) ** t)
        pv = proj_fcf * df
        pv_explicit += pv
        dcf_projections.append(
            DCFProjection(
                year=t,
                projected_fcf=proj_fcf,
                discount_factor=df,
                present_value=pv,
            )
        )

    # --------------------------------------------------------------------------
    # 6. Terminal Value (Gordon Growth)
    # --------------------------------------------------------------------------
    tv, pv_tv, tv_err = calculate_terminal_value(raw_projections[-1], wacc, tg)
    if tv_err or tv is None or pv_tv is None:
        warnings.append(tv_err or "Terminal value calculation failed.")
        return DCFValuation(
            status="error",
            risk_free_rate=rf,
            beta=beta,
            cost_of_equity=ke,
            wacc=wacc,
            fcf_growth_assumption=fcf_growth,
            projections=dcf_projections,
            pv_explicit_fcf=pv_explicit,
            warnings=warnings,
        )

    # --------------------------------------------------------------------------
    # 7. Enterprise Value, Net Debt, and Equity Value
    # --------------------------------------------------------------------------
    enterprise_value = pv_explicit + pv_tv

    # Cash: prefer yfinance total_cash, then SEC cash_and_equivalents, else 0.0
    cash = 0.0
    if market_data.total_cash is not None:
        cash = market_data.total_cash
    elif latest and latest.cash_and_equivalents is not None:
        cash = latest.cash_and_equivalents
    else:
        warnings.append("Cash balance unavailable; assuming zero cash for net debt adjustment.")

    net_debt = total_debt - cash
    equity_value = enterprise_value - net_debt

    # --------------------------------------------------------------------------
    # 8. Implied Intrinsic Share Price & Upside/Downside
    # --------------------------------------------------------------------------
    implied_price = equity_value / shares_out
    upside_downside = ((implied_price - current_price) / current_price) * 100.0

    # --------------------------------------------------------------------------
    # 9. 2D Sensitivity Matrix
    # --------------------------------------------------------------------------
    sensitivity = generate_sensitivity_table(
        explicit_fcfs=raw_projections,
        net_debt=net_debt,
        shares_outstanding=shares_out,
    )

    # --------------------------------------------------------------------------
    # 10. Explainable Metrics Bundle
    # --------------------------------------------------------------------------
    metrics = {
        "wacc": Metric(
            value=wacc,
            unit="percentage",
            formula="We * Ke + Wd * Kd * (1 - T)",
            source_fields=["beta", "current_price", "shares_outstanding", "total_debt"],
            status="available",
        ),
        "cost_of_equity": Metric(
            value=ke,
            unit="percentage",
            formula="Rf + Beta * ERP",
            source_fields=["risk_free_rate", "beta"],
            status="available",
        ),
        "enterprise_value": Metric(
            value=enterprise_value,
            unit="currency",
            formula="PV(Explicit FCF) + PV(Terminal Value)",
            source_fields=["projections", "terminal_value", "wacc"],
            status="available",
        ),
        "implied_share_price": Metric(
            value=implied_price,
            unit="currency",
            formula="Equity Value / Shares Outstanding",
            source_fields=["equity_value", "shares_outstanding"],
            status="available",
        ),
    }

    return DCFValuation(
        status="calculated",
        risk_free_rate=rf,
        beta=beta,
        equity_risk_premium=erp,
        cost_of_equity=ke,
        pre_tax_cost_of_debt=pre_tax_kd,
        tax_rate=tax_rate,
        after_tax_cost_of_debt=after_tax_kd,
        market_value_equity=mkt_equity,
        market_value_debt=total_debt,
        equity_weight=we,
        debt_weight=wd,
        wacc=wacc,
        fcf_growth_assumption=fcf_growth,
        terminal_growth_rate=tg,
        projections=dcf_projections,
        pv_explicit_fcf=pv_explicit,
        terminal_value=tv,
        pv_terminal_value=pv_tv,
        enterprise_value=enterprise_value,
        cash=cash,
        total_debt=total_debt,
        net_debt=net_debt,
        equity_value=equity_value,
        shares_outstanding=shares_out,
        current_share_price=current_price,
        implied_share_price=implied_price,
        upside_downside_pct=upside_downside,
        sensitivity_table=sensitivity,
        warnings=warnings,
        metrics=metrics,
    )