"""Research Service coordinating grounded context construction, LLM generation, and guardrail validation."""
import argparse
import json
import sys
from typing import Optional

from app.financial.engine import FinancialAnalysisEngine
from app.financial.schemas import FinancialAnalysis
from app.research.context import (
    build_research_context,
    extract_sources,
    format_context_as_text,
)
from app.research.llm import (
    LLMKeyMissingError,
    ResearchLLMError,
    call_structured_research_llm,
)
from app.research.schemas import ResearchReport
from app.schemas.financial import CompanyData
from app.utils.logging import logger


class ResearchGuardrailError(Exception):
    """Raised when the LLM output violates critical financial grounding boundaries."""
    pass


class ResearchService:
    """
    Coordinates grounded institutional investment research report generation.
    Enforces deterministic data precedence, verified citations, and hallucination guardrails.
    """

    def validate_and_align_report(
        self,
        report: ResearchReport,
        company_data: CompanyData,
        financial_analysis: FinancialAnalysis,
    ) -> ResearchReport:
        """
        Applies programmatic guardrails to ensure the LLM cannot introduce conflicting
        financial numbers, alter DCF outputs, or inject fabricated source citations.
        The deterministic FinancialAnalysis engine is the authoritative source of truth.
        """
        adjustments_made = False

        # 1. Ticker consistency
        if report.ticker.strip().upper() != company_data.ticker.strip().upper():
            logger.warning(
                f"LLM returned ticker '{report.ticker}' instead of '{company_data.ticker}'; normalizing."
            )
            report.ticker = company_data.ticker.strip().upper()
            adjustments_made = True

        # 2. Company name normalization
        if not report.company_name or len(report.company_name.strip()) < 2:
            report.company_name = company_data.company_profile.name
            adjustments_made = True

        # 3. Deterministic Financial Performance Anchors (Financial Snapshot)
        g = financial_analysis.growth
        p = financial_analysis.profitability
        cf = financial_analysis.cash_flow
        snap = report.financial_snapshot

        snap.revenue_growth_yoy_pct = (
            round(g.revenue_growth_yoy * 100.0, 1) if g.revenue_growth_yoy is not None else None
        )
        snap.operating_margin_pct = (
            round(p.operating_margin * 100.0, 1) if p.operating_margin is not None else None
        )
        snap.net_margin_pct = (
            round(p.net_margin * 100.0, 1) if p.net_margin is not None else None
        )
        snap.free_cash_flow = cf.free_cash_flow

        # 4. Deterministic Valuation Multiples Anchors (Valuation Assessment)
        v = financial_analysis.valuation
        m = company_data.market_data
        val = report.valuation_assessment

        val.current_share_price = m.current_price
        val.pe_ratio = v.pe_ratio
        val.forward_pe = v.forward_pe
        val.price_to_sales = v.price_to_sales
        val.ev_to_ebitda = v.ev_to_ebitda
        val.price_to_book = None  # Strictly unavailable in deterministic engine

        # 5. Deterministic DCF Valuation & Sensitivity Anchors
        dcf = financial_analysis.dcf
        dcf_interp = report.dcf_interpretation

        if dcf and dcf.status == "not_applicable":
            # For financial institutions, strictly enforce no fabricated DCF metrics
            if any([
                dcf_interp.model_wacc_pct is not None,
                dcf_interp.model_terminal_growth_pct is not None,
                dcf_interp.model_implied_share_price is not None,
                dcf_interp.model_upside_downside_pct is not None,
            ]):
                logger.warning(
                    f"Financial institution {report.ticker} has not_applicable DCF, but LLM populated DCF metrics. Clearing."
                )
                adjustments_made = True

            dcf_interp.model_wacc_pct = None
            dcf_interp.model_terminal_growth_pct = None
            dcf_interp.model_implied_share_price = None
            dcf_interp.model_upside_downside_pct = None

            # Neutralize any hallucinated price targets in qualitative signal
            if any(term in dcf_interp.valuation_signal.lower() for term in ["target of $", "upside of", "implied price of"]):
                dcf_interp.valuation_signal = (
                    "Traditional industrial Free Cash Flow DCF is not applicable to financial institutions. "
                    "Valuation is anchored exclusively to P/E multiples and Return on Equity (ROE)."
                )
                adjustments_made = True

        elif dcf and dcf.status == "calculated":
            # Programmatically anchor all quantitative DCF outputs to deterministic calculations
            dcf_interp.model_wacc_pct = round(dcf.wacc * 100.0, 2) if dcf.wacc is not None else None
            dcf_interp.model_terminal_growth_pct = (
                round(dcf.terminal_growth_rate * 100.0, 2) if dcf.terminal_growth_rate is not None else None
            )
            dcf_interp.model_implied_share_price = (
                round(dcf.implied_share_price, 2) if dcf.implied_share_price is not None else None
            )
            dcf_interp.model_upside_downside_pct = (
                round(dcf.upside_downside_pct, 1) if dcf.upside_downside_pct is not None else None
            )
        else:
            dcf_interp.model_wacc_pct = None
            dcf_interp.model_terminal_growth_pct = None
            dcf_interp.model_implied_share_price = None
            dcf_interp.model_upside_downside_pct = None

        # 6. Strict Provenance Grounding: authoritative sources originate only from verified data layer
        report.sources = extract_sources(company_data, financial_analysis)

        # 7. Audit disclosure
        audit_note = "All quantitative metrics programmatically anchored to deterministic FinancialAnalysis engine."
        if audit_note not in report.limitations:
            report.limitations.append(audit_note)

        return report

    def generate_report(
        self,
        company_data: CompanyData,
        financial_analysis: FinancialAnalysis,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ResearchReport:
        """
        Executes end-to-end research generation:
        1. Builds grounded context dictionary
        2. Formats markdown briefing
        3. Invokes OpenAI structured completions
        4. Validates and aligns against deterministic ground truth
        """
        ticker = company_data.ticker
        name = company_data.company_profile.name
        logger.info(f"Starting Grounded Research Report generation for {ticker}")

        # 1. Build context
        context = build_research_context(company_data, financial_analysis)

        # 2. Format context text
        context_text = format_context_as_text(context)

        # 3. Call OpenAI with structured Pydantic format
        raw_report = call_structured_research_llm(
            context_text=context_text,
            ticker=ticker,
            company_name=name,
            model=model,
            api_key=api_key,
            temperature=temperature,
        )

        # 4. Apply hallucination guardrails and source verification
        validated_report = self.validate_and_align_report(
            report=raw_report,
            company_data=company_data,
            financial_analysis=financial_analysis,
        )

        logger.info(f"Successfully generated and verified Research Report for {ticker}")
        return validated_report


def main():
    """CLI runner for generating an investment research report on any public ticker."""
    parser = argparse.ArgumentParser(description="Generate Institutional Investment Research Report.")
    parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g. AAPL, NVDA, JPM)")
    parser.add_argument("--json", action="store_true", help="Output full report as structured JSON")
    parser.add_argument("--model", type=str, default=None, help="OpenAI model override (e.g. gpt-4o)")
    args = parser.parse_args()

    from app.data.orchestrator import DataOrchestrator

    ticker = args.ticker.strip().upper()
    print(f"\n[1/3] Ingesting normalized market, SEC EDGAR, and news data for {ticker}...")
    orchestrator = DataOrchestrator()
    try:
        company_data = orchestrator.get_company_data(ticker)
    except Exception as e:
        print(f"Data ingestion failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[2/3] Running deterministic financial and DCF valuation engine...")
    engine = FinancialAnalysisEngine()
    analysis = engine.analyze(company_data)

    print(f"[3/3] Generating grounded LLM investment research memo...")
    service = ResearchService()
    try:
        report = service.generate_report(
            company_data=company_data,
            financial_analysis=analysis,
            model=args.model,
        )
    except LLMKeyMissingError as e:
        print(f"\n[!] OPENAI_API_KEY Missing:\n    {e}\n", file=sys.stderr)
        print("Note: To run live LLM synthesis, set $env:OPENAI_API_KEY='your-key'.")
        print("Deterministic financial analysis and DCF calculations remain fully operational.\n")
        sys.exit(0)
    except ResearchLLMError as e:
        print(f"\n[!] Research synthesis failed: {e}\n", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(report.model_dump_json(indent=2))
        return

    # Print formatted executive report
    print("\n" + "=" * 76)
    print(f" INSTITUTIONAL INVESTMENT RESEARCH REPORT: {report.ticker} — {report.company_name}")
    print("=" * 76)
    print(f" Confidence: [{report.confidence.level.upper()}] — {report.confidence.rationale}")
    print("-" * 76)
    print(" EXECUTIVE SUMMARY:")
    print(f"  {report.executive_summary}\n")
    print(" INVESTMENT THESIS:")
    print(f"  {report.investment_thesis}\n")
    print("-" * 76)
    print(" FINANCIAL SNAPSHOT & PERFORMANCE:")
    print(f"  {report.financial_snapshot.summary}")
    for pt in report.financial_snapshot.key_points:
        print(f"  * {pt}")
    print("\n VALUATION & MULTIPLES ASSESSMENT:")
    print(f"  {report.valuation_assessment.summary}")
    print(f"  * Multiples: {report.valuation_assessment.multiples_summary}")
    for pt in report.valuation_assessment.key_points:
        print(f"  * {pt}")
    print("\n DCF VALUATION & SENSITIVITY INTERPRETATION:")
    print(f"  {report.dcf_interpretation.summary}")
    print(f"  * Signal: {report.dcf_interpretation.valuation_signal}")
    print(f"  * Sensitivity: {report.dcf_interpretation.sensitivity_observation}")
    if report.dcf_interpretation.model_upside_downside_pct is not None:
        print(f"  * Model-Implied Upside/Downside: {report.dcf_interpretation.model_upside_downside_pct:+.1f}%")
    print("-" * 76)
    print(" CORE FUNDAMENTAL STRENGTHS:")
    for s in report.strengths:
        print(f"  [+] {s}")
    print("\n RISKS & CONCERNS:")
    for r in report.risks:
        print(f"  [-] Risk: {r}")
    for c in report.concerns:
        print(f"  [!] Concern: {c}")
    print("\n CATALYSTS:")
    for cat in report.catalysts:
        print(f"  [*] {cat}")
    print("-" * 76)
    print(" NEWS & MARKET CONTEXT:")
    print(f"  {report.news_and_market_context.summary}")
    for h in report.news_and_market_context.relevant_headlines:
        print(f"  * Headline: {h}")
    print("-" * 76)
    print(" CONCLUSION & MONITORABLES:")
    print(f"  {report.conclusion}")
    print("-" * 76)
    print(f" SOURCES & CITATIONS ({len(report.sources)} verified):")
    for src in report.sources[:5]:
        url_part = f" ({src.url})" if src.url else ""
        print(f"  - [{src.provider}] {src.title}{url_part}")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()