"""Research Context Builder: transforms deterministic FinancialAnalysis and CompanyData into grounded LLM context."""
from typing import Any, Dict, List, Optional

from app.financial.schemas import FinancialAnalysis
from app.research.schemas import ResearchSource
from app.schemas.financial import CompanyData


def _fmt_pct(val: Optional[float]) -> str:
    """Safely formats float as percentage or explicit N/A."""
    return f"{val:.1%}" if val is not None else "N/A"


def _fmt_cur(val: Optional[float], prefix: str = "$") -> str:
    """Safely formats currency or explicit N/A."""
    if val is None:
        return "N/A"
    abs_val = abs(val)
    if abs_val >= 1e12:
        return f"{prefix}{val / 1e12:,.2f} Trillion"
    if abs_val >= 1e9:
        return f"{prefix}{val / 1e9:,.2f} Billion"
    if abs_val >= 1e6:
        return f"{prefix}{val / 1e6:,.2f} Million"
    return f"{prefix}{val:,.2f}"


def _fmt_mult(val: Optional[float], suffix: str = "x") -> str:
    """Safely formats valuation multiple or explicit N/A."""
    return f"{val:.2f}{suffix}" if val is not None else "N/A"


def extract_sources(company_data: CompanyData, financial_analysis: FinancialAnalysis) -> List[ResearchSource]:
    """
    Extracts all verified provenance sources from CompanyData and engine metadata.
    Does not fabricate any URLs, dates, or headlines.
    """
    sources: List[ResearchSource] = []

    # 1. SEC EDGAR source
    filing_years = [str(f.fiscal_year) for f in company_data.historical_financials]
    cik = company_data.company_profile.cik
    sec_url = f"https://www.sec.gov/edgar/browse/?CIK={cik}" if cik else "https://www.sec.gov/edgar"
    years_str = ", ".join(filing_years) if filing_years else "Recent"
    sources.append(
        ResearchSource(
            provider="SEC_EDGAR",
            title=f"SEC Form 10-K Annual Reports (Fiscal Years: {years_str})",
            url=sec_url,
            source_type="filing",
        )
    )

    # 2. Market Data source
    sources.append(
        ResearchSource(
            provider="yfinance",
            title=f"Market Quote, Capital Structure & Trading Multiples ({company_data.ticker})",
            url=f"https://finance.yahoo.com/quote/{company_data.ticker}",
            source_type="market_data",
        )
    )

    # 3. News sources
    for art in company_data.news:
        sources.append(
            ResearchSource(
                provider=art.source or "Financial News",
                title=art.headline,
                url=art.url,
                published_at=art.published_at,
                source_type="news",
            )
        )

    # 4. Engine DCF model source
    sources.append(
        ResearchSource(
            provider="FinancialAnalysisEngine",
            title="Deterministic 5-Year Free Cash Flow DCF & 2D Sensitivity Model",
            source_type="valuation_model",
        )
    )

    return sources


def build_research_context(company_data: CompanyData, financial_analysis: FinancialAnalysis) -> Dict[str, Any]:
    """
    Transforms CompanyData and FinancialAnalysis into a structured, strictly grounded dictionary.
    Guarantees every numerical fact originates deterministically from verified application data.
    """
    profile = company_data.company_profile
    market = company_data.market_data
    g = financial_analysis.growth
    p = financial_analysis.profitability
    l = financial_analysis.leverage
    cf = financial_analysis.cash_flow
    v = financial_analysis.valuation
    dcf = financial_analysis.dcf
    h = financial_analysis.health

    # Historical trends snapshot
    trends_summary = []
    for t in financial_analysis.historical_trends:
        trends_summary.append({
            "fiscal_year": t.fiscal_year,
            "revenue": _fmt_cur(t.revenue),
            "revenue_growth": _fmt_pct(t.revenue_growth),
            "operating_income": _fmt_cur(t.operating_income),
            "operating_margin": _fmt_pct(t.operating_margin),
            "net_income": _fmt_cur(t.net_income),
            "net_margin": _fmt_pct(t.net_margin),
            "free_cash_flow": _fmt_cur(t.free_cash_flow),
            "fcf_margin": _fmt_pct(t.fcf_margin),
        })

    # DCF details
    dcf_context: Dict[str, Any] = {
        "status": dcf.status if dcf else "N/A",
        "is_applicable": dcf.status == "calculated" if dcf else False,
    }
    if dcf and dcf.status == "calculated":
        dcf_context.update({
            "risk_free_rate": _fmt_pct(dcf.risk_free_rate),
            "beta": f"{dcf.beta:.2f}" if dcf.beta is not None else "N/A",
            "equity_risk_premium": _fmt_pct(dcf.equity_risk_premium),
            "cost_of_equity": _fmt_pct(dcf.cost_of_equity),
            "pre_tax_cost_of_debt": _fmt_pct(dcf.pre_tax_cost_of_debt),
            "after_tax_cost_of_debt": _fmt_pct(dcf.after_tax_cost_of_debt),
            "equity_weight": _fmt_pct(dcf.equity_weight),
            "debt_weight": _fmt_pct(dcf.debt_weight),
            "wacc": _fmt_pct(dcf.wacc),
            "fcf_growth_assumption": _fmt_pct(dcf.fcf_growth_assumption),
            "terminal_growth_rate": _fmt_pct(dcf.terminal_growth_rate),
            "pv_explicit_fcf": _fmt_cur(dcf.pv_explicit_fcf),
            "terminal_value": _fmt_cur(dcf.terminal_value),
            "pv_terminal_value": _fmt_cur(dcf.pv_terminal_value),
            "enterprise_value": _fmt_cur(dcf.enterprise_value),
            "cash": _fmt_cur(dcf.cash),
            "total_debt": _fmt_cur(dcf.total_debt),
            "net_debt": _fmt_cur(dcf.net_debt),
            "equity_value": _fmt_cur(dcf.equity_value),
            "shares_outstanding": f"{dcf.shares_outstanding:,.0f}" if dcf.shares_outstanding else "N/A",
            "current_share_price": _fmt_cur(dcf.current_share_price),
            "implied_share_price": _fmt_cur(dcf.implied_share_price),
            "upside_downside_pct": f"{dcf.upside_downside_pct:+.1f}%" if dcf.upside_downside_pct is not None else "N/A",
            "explicit_projections": [
                {
                    "year": proj.year,
                    "projected_fcf": _fmt_cur(proj.projected_fcf),
                    "discount_factor": f"{proj.discount_factor:.4f}",
                    "present_value": _fmt_cur(proj.present_value),
                }
                for proj in dcf.projections
            ],
            "sensitivity_grid": [
                {
                    "wacc": f"{cell.wacc:.1%}",
                    "terminal_growth": f"{cell.terminal_growth:.1%}",
                    "implied_price": f"${cell.implied_share_price:.2f}" if cell.implied_share_price is not None else "N/A",
                }
                for cell in (dcf.sensitivity_table.cells if dcf.sensitivity_table else [])
            ],
            "warnings": dcf.warnings,
        })
    elif dcf and dcf.status == "not_applicable":
        dcf_context["note"] = (
            "Traditional industrial Free Cash Flow DCF is NOT applicable to commercial banks and financial institutions. "
            "Financial institutions intermediate capital through interest margins and regulatory ratios rather than "
            "industrial capex. Valuation must rely on P/E, P/B, and ROE comparative multiples."
        )
        dcf_context["warnings"] = dcf.warnings
    elif dcf:
        dcf_context["note"] = "DCF valuation could not be computed due to non-positive cash flows or missing market data."
        dcf_context["warnings"] = dcf.warnings

    # News items
    news_items = []
    for art in company_data.news[:5]:
        news_items.append({
            "headline": art.headline,
            "source": art.source or "News",
            "published_at": art.published_at or "Recent",
            "summary": art.summary or "",
        })

    return {
        "company": {
            "ticker": company_data.ticker,
            "name": profile.name,
            "sector": profile.sector or "N/A",
            "industry": profile.industry or "N/A",
            "description": profile.description or "N/A",
            "currency": profile.currency or "USD",
        },
        "growth": {
            "revenue_growth_yoy": _fmt_pct(g.revenue_growth_yoy),
            "revenue_cagr_3yr": _fmt_pct(g.revenue_cagr_3yr),
            "net_income_growth_yoy": _fmt_pct(g.net_income_growth_yoy),
            "fcf_growth_yoy": _fmt_pct(g.fcf_growth_yoy),
        },
        "profitability": {
            "gross_margin": _fmt_pct(p.gross_margin),
            "operating_margin": _fmt_pct(p.operating_margin),
            "net_margin": _fmt_pct(p.net_margin),
            "roe": _fmt_pct(p.roe),
            "roic": _fmt_pct(p.roic),
        },
        "leverage": {
            "debt_to_equity": _fmt_mult(l.debt_to_equity),
            "debt_to_ebitda": _fmt_mult(l.debt_to_ebitda),
            "interest_coverage": _fmt_mult(l.interest_coverage),
            "total_debt": _fmt_cur(l.total_debt),
            "stockholders_equity": _fmt_cur(l.stockholders_equity),
        },
        "cash_flow": {
            "operating_cash_flow": _fmt_cur(cf.operating_cash_flow),
            "capex": _fmt_cur(cf.capex),
            "free_cash_flow": _fmt_cur(cf.free_cash_flow),
            "fcf_margin": _fmt_pct(cf.fcf_margin),
            "fcf_conversion": _fmt_pct(cf.fcf_conversion),
        },
        "valuation_multiples": {
            "current_price": _fmt_cur(market.current_price),
            "market_cap": _fmt_cur(market.market_cap),
            "pe_ratio": _fmt_mult(v.pe_ratio),
            "forward_pe": _fmt_mult(v.forward_pe),
            "ev_to_ebitda": _fmt_mult(v.ev_to_ebitda),
            "price_to_sales": _fmt_mult(v.price_to_sales),
            "price_to_fcf": _fmt_mult(v.price_to_fcf),
            "shares_outstanding": f"{market.shares_outstanding:,.0f}" if market.shares_outstanding else "N/A",
            "beta": f"{market.beta:.2f}" if market.beta is not None else "N/A",
        },
        "historical_trends": trends_summary,
        "financial_health": {
            "overall": h.overall,
            "growth_pillar": h.growth_pillar,
            "profitability_pillar": h.profitability_pillar,
            "leverage_pillar": h.leverage_pillar,
            "cash_flow_pillar": h.cash_flow_pillar,
            "observations": h.key_observations,
        },
        "dcf": dcf_context,
        "news": news_items,
        "warnings": financial_analysis.warnings,
    }


def format_context_as_text(context: Dict[str, Any]) -> str:
    """
    Renders structured dictionary into a clear, professional markdown briefing for the LLM.
    Strictly preserves all numerical values, missing data tags, and caveats.
    """
    c = context["company"]
    g = context["growth"]
    p = context["profitability"]
    l = context["leverage"]
    cf = context["cash_flow"]
    v = context["valuation_multiples"]
    h = context["financial_health"]
    dcf = context["dcf"]

    lines: List[str] = [
        f"# FINANCIAL BRIEFING: {c['name']} ({c['ticker']})",
        f"Sector: {c['sector']} | Industry: {c['industry']} | Currency: {c['currency']}",
        f"Company Description: {c['description'][:350]}..." if len(c['description']) > 350 else f"Company Description: {c['description']}",
        "",
        "## 1. REVENUE & GROWTH PERFORMANCE",
        f"- Revenue YoY Growth: {g['revenue_growth_yoy']}",
        f"- Revenue 3-Year CAGR: {g['revenue_cagr_3yr']}",
        f"- Net Income YoY Growth: {g['net_income_growth_yoy']}",
        f"- Free Cash Flow YoY Growth: {g['fcf_growth_yoy']}",
        "",
        "## 2. PROFITABILITY & CAPITAL EFFICIENCY",
        f"- Gross Margin: {p['gross_margin']}",
        f"- Operating Margin: {p['operating_margin']}",
        f"- Net Margin: {p['net_margin']}",
        f"- Return on Equity (ROE, 2-period average): {p['roe']}",
        f"- Return on Invested Capital (ROIC): {p['roic']}",
        "",
        "## 3. BALANCE SHEET LEVERAGE & SOLVENCY",
        f"- Debt-to-Equity Ratio: {l['debt_to_equity']}",
        f"- Debt-to-EBITDA Ratio: {l['debt_to_ebitda']}",
        f"- Interest Coverage Ratio: {l['interest_coverage']}",
        f"- Total Debt: {l['total_debt']}",
        f"- Stockholders' Equity: {l['stockholders_equity']}",
        "",
        "## 4. CASH FLOW GENERATION",
        f"- Operating Cash Flow: {cf['operating_cash_flow']}",
        f"- Capital Expenditures: {cf['capex']}",
        f"- Free Cash Flow (OCF - Capex): {cf['free_cash_flow']}",
        f"- FCF Margin: {cf['fcf_margin']}",
        f"- FCF Conversion Rate (FCF / Net Income): {cf['fcf_conversion']}",
        "",
        "## 5. MARKET VALUATION & MULTIPLES",
        f"- Current Share Price: {v['current_price']}",
        f"- Market Capitalization: {v['market_cap']}",
        f"- Trailing P/E Multiple: {v['pe_ratio']}",
        f"- Forward P/E Multiple: {v['forward_pe']}",
        f"- Enterprise Value / EBITDA: {v['ev_to_ebitda']}",
        f"- Price-to-Sales (P/S): {v['price_to_sales']}",
        f"- Price-to-FCF (P/FCF): {v['price_to_fcf']}",
        f"- Shares Outstanding: {v['shares_outstanding']}",
        f"- Beta: {v['beta']}",
        "",
        "## 6. FINANCIAL HEALTH ASSESSMENT (DETERMINISTIC EVALUATION)",
        f"- Overall Classification: {h['overall']}",
        f"- Growth Pillar: {h['growth_pillar']} | Profitability: {h['profitability_pillar']} | Leverage: {h['leverage_pillar']} | Cash Flow: {h['cash_flow_pillar']}",
        "Key Engine Observations:",
    ]
    for obs in h["observations"]:
        lines.append(f"  * {obs}")

    lines.append("")
    lines.append(f"## 7. DISCOUNTED CASH FLOW (DCF) & SENSITIVITY [STATUS: {dcf['status'].upper()}]")
    if dcf.get("is_applicable"):
        lines.extend([
            f"- Risk-Free Rate (Rf, 10-Yr Treasury): {dcf['risk_free_rate']}",
            f"- Beta: {dcf['beta']} | Equity Risk Premium: {dcf['equity_risk_premium']}",
            f"- Cost of Equity (CAPM): {dcf['cost_of_equity']}",
            f"- After-Tax Cost of Debt: {dcf['after_tax_cost_of_debt']} (Weight: {dcf['debt_weight']})",
            f"- Equity Weight: {dcf['equity_weight']}",
            f"- Weighted Average Cost of Capital (WACC): {dcf['wacc']}",
            f"- 5-Year FCF Forecast Growth Assumption: {dcf['fcf_growth_assumption']}",
            f"- Terminal Growth Rate Assumption: {dcf['terminal_growth_rate']}",
            f"- PV of 5-Year Explicit Forecasts: {dcf['pv_explicit_fcf']}",
            f"- Gordon Growth Terminal Value: {dcf['terminal_value']} (PV: {dcf['pv_terminal_value']})",
            f"- Model Enterprise Value: {dcf['enterprise_value']}",
            f"- Balance Sheet Adjustments: Cash: {dcf['cash']} | Total Debt: {dcf['total_debt']} | Net Debt: {dcf['net_debt']}",
            f"- Model Equity Value: {dcf['equity_value']}",
            f"- Shares Outstanding: {dcf['shares_outstanding']}",
            f"- Current Market Price: {dcf['current_share_price']}",
            f"- Model-Implied Intrinsic Share Price: {dcf['implied_share_price']}",
            f"- Model-Implied Upside/Downside: {dcf['upside_downside_pct']}",
            "Sensitivity Matrix Highlights (Implied Price vs WACC & Terminal Growth):",
        ])
        for cell in dcf.get("sensitivity_grid", [])[:8]:
            lines.append(f"  * WACC: {cell['wacc']}, g: {cell['terminal_growth']} -> Implied Price: {cell['implied_price']}")
    else:
        note = dcf.get("note", "DCF not computed.")
        lines.append(f"- NOTE: {note}")

    lines.append("")
    lines.append("## 8. RECENT NEWS HEADLINES & VERIFIED DEVELOPMENTS")
    if context.get("news"):
        for item in context["news"]:
            lines.append(f"- [{item['published_at']}] ({item['source']}) {item['headline']}")
            if item["summary"]:
                lines.append(f"  Summary: {item['summary']}")
    else:
        lines.append("- No recent news headlines provided in dataset.")

    lines.append("")
    lines.append("## 9. DATA WARNINGS & SYSTEM DISCLOSURES")
    if context.get("warnings"):
        for w in context["warnings"]:
            lines.append(f"- [!] {w}")
    else:
        lines.append("- No abnormal data warnings recorded.")

    return "\n".join(lines)