"""Deterministic Financial Analysis Engine orchestrating all financial modules."""
import argparse
import json
import sys
from typing import List, Optional

from app.financial.cash_flow import calculate_cash_flow_analysis
from app.financial.growth import calculate_growth_analysis
from app.financial.health import evaluate_financial_health
from app.financial.leverage import calculate_leverage_analysis
from app.financial.profitability import calculate_profitability_analysis
from app.financial.schemas import FinancialAnalysis, FinancialTrend
from app.financial.valuation_metrics import calculate_valuation_metrics
from app.schemas.financial import CompanyData, HistoricalFinancial
from app.utils.logging import logger


class FinancialAnalysisEngine:
    """
    Engine executing deterministic, mathematical financial calculations across growth,
    profitability, leverage, cash flow, valuation multiples, and financial health.
    """

    @staticmethod
    def _build_historical_trends(
        financials: List[HistoricalFinancial]
    ) -> List[FinancialTrend]:
        """Generates consecutive year-by-year financial trend snapshots for charting."""
        sorted_fin = sorted(financials, key=lambda x: x.fiscal_year)
        trends: List[FinancialTrend] = []

        for i, curr in enumerate(sorted_fin):
            prev = sorted_fin[i - 1] if i > 0 else None

            # Revenue growth
            rev_growth = None
            if prev and prev.revenue is not None and prev.revenue > 0 and curr.revenue is not None:
                rev_growth = (curr.revenue - prev.revenue) / prev.revenue

            # Operating margin
            op_margin = None
            if curr.operating_income is not None and curr.revenue is not None and curr.revenue > 0:
                op_margin = curr.operating_income / curr.revenue

            # Net margin
            net_margin = None
            if curr.net_income is not None and curr.revenue is not None and curr.revenue > 0:
                net_margin = curr.net_income / curr.revenue

            # FCF margin
            fcf_margin = None
            if curr.free_cash_flow is not None and curr.revenue is not None and curr.revenue > 0:
                fcf_margin = curr.free_cash_flow / curr.revenue

            trends.append(
                FinancialTrend(
                    fiscal_year=curr.fiscal_year,
                    revenue=curr.revenue,
                    revenue_growth=rev_growth,
                    operating_income=curr.operating_income,
                    operating_margin=op_margin,
                    net_income=curr.net_income,
                    net_margin=net_margin,
                    operating_cash_flow=curr.operating_cash_flow,
                    free_cash_flow=curr.free_cash_flow,
                    fcf_margin=fcf_margin,
                )
            )

        return trends

    def analyze(self, company_data: CompanyData) -> FinancialAnalysis:
        """
        Transforms normalized CompanyData into structured, explainable FinancialAnalysis.
        Purely deterministic with zero LLM or synthetic approximations.
        """
        ticker = company_data.ticker
        name = company_data.company_profile.name
        sector = company_data.company_profile.sector
        industry = company_data.company_profile.industry
        currency = company_data.company_profile.currency or "USD"
        financials = company_data.historical_financials

        logger.info(f"Running Financial Analysis Engine for {ticker} ({sector or 'General Sector'})")

        # 1. Execute deterministic sub-analyses
        growth = calculate_growth_analysis(financials, sector=sector)
        profitability = calculate_profitability_analysis(financials, sector=sector)
        leverage = calculate_leverage_analysis(financials, sector=sector)
        cash_flow = calculate_cash_flow_analysis(financials, sector=sector)
        valuation = calculate_valuation_metrics(
            company_data.market_data, financials, sector=sector
        )

        # 2. Build structured historical trends time-series
        trends = self._build_historical_trends(financials)

        # 3. Evaluate deterministic health synthesis
        health = evaluate_financial_health(
            growth=growth,
            profitability=profitability,
            leverage=leverage,
            cash_flow=cash_flow,
            sector=sector,
        )

        # 4. Consolidate engine warnings
        all_warnings: List[str] = []
        for dw in company_data.data_warnings:
            all_warnings.append(f"[{dw.provider}] {dw.field}: {dw.message}")
        for w in health.warnings:
            all_warnings.append(f"[HEALTH] {w}")

        return FinancialAnalysis(
            ticker=ticker,
            company_name=name,
            sector=sector,
            industry=industry,
            currency=currency,
            growth=growth,
            profitability=profitability,
            leverage=leverage,
            cash_flow=cash_flow,
            valuation=valuation,
            historical_trends=trends,
            health=health,
            warnings=all_warnings,
        )


def main():
    """Command-line interface for running the financial analysis engine directly."""
    parser = argparse.ArgumentParser(description="Run Deterministic Financial Analysis Engine.")
    parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g. AAPL, MSFT, JPM)")
    parser.add_argument("--json", action="store_true", help="Output full JSON analysis")
    args = parser.parse_args()

    from app.data.orchestrator import DataOrchestrator

    orchestrator = DataOrchestrator()
    try:
        data = orchestrator.get_company_data(args.ticker)
    except Exception as e:
        print(f"Error retrieving company data: {e}", file=sys.stderr)
        sys.exit(1)

    engine = FinancialAnalysisEngine()
    analysis = engine.analyze(data)

    if args.json:
        print(analysis.model_dump_json(indent=2))
        return

    # Formatted terminal executive report
    g = analysis.growth
    p = analysis.profitability
    l = analysis.leverage
    cf = analysis.cash_flow
    v = analysis.valuation
    h = analysis.health

    print("\n" + "=" * 70)
    print(f" FINANCIAL ANALYSIS REPORT: {analysis.ticker} — {analysis.company_name}")
    print("=" * 70)
    print(f" Sector: {analysis.sector or 'N/A'} | Industry: {analysis.industry or 'N/A'}")
    print(f" Overall Financial Health: [{h.overall.upper()}]")
    print("-" * 70)
    print(" 1. GROWTH ANALYSIS:")
    rev_g = f"{g.revenue_growth_yoy:.1%}" if g.revenue_growth_yoy is not None else "N/A"
    cagr_str = f"{g.revenue_cagr_3yr:.1%}" if g.revenue_cagr_3yr is not None else "N/A"
    ni_g = f"{g.net_income_growth_yoy:.1%}" if g.net_income_growth_yoy is not None else "N/A"
    fcf_g = f"{g.fcf_growth_yoy:.1%}" if g.fcf_growth_yoy is not None else "N/A"
    print(f"  * Revenue YoY: {rev_g:<10} | 3-Yr Rev CAGR: {cagr_str:<10}")
    print(f"  * Net Income YoY: {ni_g:<7} | FCF YoY: {fcf_g}")
    print("-" * 70)
    print(" 2. PROFITABILITY & RETURNS:")
    op_m = f"{p.operating_margin:.1%}" if p.operating_margin is not None else "N/A"
    net_m = f"{p.net_margin:.1%}" if p.net_margin is not None else "N/A"
    roe = f"{p.roe:.1%}" if p.roe is not None else "N/A"
    roic = f"{p.roic:.1%}" if p.roic is not None else "N/A"
    print(f"  * Operating Margin: {op_m:<8} | Net Margin: {net_m:<8}")
    print(f"  * ROE (Avg Equity): {roe:<8} | ROIC: {roic}")
    print("-" * 70)
    print(" 3. LEVERAGE & SOLVENCY:")
    de = f"{l.debt_to_equity:.2f}x" if l.debt_to_equity is not None else "N/A"
    debt_str = f"${l.total_debt:,.0f}" if l.total_debt is not None else "N/A"
    equity_str = f"${l.stockholders_equity:,.0f}" if l.stockholders_equity is not None else "N/A"
    print(f"  * Debt-to-Equity: {de:<10} | Total Debt: {debt_str}")
    print(f"  * Stockholders' Equity: {equity_str}")
    print("-" * 70)
    print(" 4. CASH FLOW GENERATION:")
    fcf_str = f"${cf.free_cash_flow:,.0f}" if cf.free_cash_flow is not None else "N/A"
    fcf_m = f"{cf.fcf_margin:.1%}" if cf.fcf_margin is not None else "N/A"
    fcf_c = f"{cf.fcf_conversion:.1%}" if cf.fcf_conversion is not None else "N/A"
    print(f"  * Free Cash Flow: {fcf_str:<18} | FCF Margin: {fcf_m}")
    print(f"  * FCF Conversion (FCF/NI): {fcf_c}")
    print("-" * 70)
    print(" 5. VALUATION MULTIPLES:")
    pe = f"{v.pe_ratio:.2f}x" if v.pe_ratio is not None else "N/A"
    fwd_pe = f"{v.forward_pe:.2f}x" if v.forward_pe is not None else "N/A"
    ev_ebitda = f"{v.ev_to_ebitda:.2f}x" if v.ev_to_ebitda is not None else "N/A"
    ps = f"{v.price_to_sales:.2f}x" if v.price_to_sales is not None else "N/A"
    pfcf = f"{v.price_to_fcf:.2f}x" if v.price_to_fcf is not None else "N/A"
    print(f"  * Trailing P/E: {pe:<10} | Forward P/E: {fwd_pe:<10} | EV/EBITDA: {ev_ebitda}")
    print(f"  * Price-to-Sales: {ps:<8} | Price-to-FCF: {pfcf}")
    print("-" * 70)
    print(" 6. FINANCIAL HEALTH OBSERVATIONS:")
    print(f"  Pillars: Growth: {h.growth_pillar} | Profitability: {h.profitability_pillar} | Leverage: {h.leverage_pillar} | Cash Flow: {h.cash_flow_pillar}")
    for obs in h.key_observations:
        print(f"  * {obs}")
    if analysis.warnings:
        print("-" * 70)
        print(f" WARNINGS & CAVEATS ({len(analysis.warnings)}):")
        for w in analysis.warnings[:3]:
            print(f"  [!] {w}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()