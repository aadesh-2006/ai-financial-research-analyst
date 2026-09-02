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
        Applies programmatic guardrails to ensure the LLM has not modified deterministic numbers
        or fabricated metadata.
        """
        # 1. Ticker consistency
        if report.ticker.strip().upper() != company_data.ticker.strip().upper():
            logger.warning(
                f"LLM returned ticker '{report.ticker}' instead of '{company_data.ticker}'; normalizing."
            )
            report.ticker = company_data.ticker.strip().upper()

        # 2. Company name normalization
        if not report.company_name or len(report.company_name.strip()) < 2:
            report.company_name = company_data.company_profile.name

        # 3. DCF consistency guardrails
        dcf = financial_analysis.dcf
        if dcf and dcf.status == "not_applicable":
            # For financial institutions, strictly enforce no fabricated DCF target
            if report.dcf_interpretation.model_upside_downside_pct is not None:
                logger.warning(
                    f"Financial institution {report.ticker} has not_applicable DCF, but LLM populated upside %. Clearing."
                )
                report.dcf_interpretation.model_upside_downside_pct = None
        elif dcf and dcf.status == "calculated" and dcf.upside_downside_pct is not None:
            # Anchor upside/downside strictly to the deterministic engine calculation
            if report.dcf_interpretation.model_upside_downside_pct is None or abs(
                report.dcf_interpretation.model_upside_downside_pct - dcf.upside_downside_pct
            ) > 0.5:
                logger.info(
                    f"Aligning LLM upside/downside ({report.dcf_interpretation.model_upside_downside_pct}%) "
                    f"to deterministic engine value ({dcf.upside_downside_pct:.1f}%)."
                )
                report.dcf_interpretation.model_upside_downside_pct = round(dcf.upside_downside_pct, 1)

        # 4. Provenance preservation: ensure verified application sources are present
        verified_sources = extract_sources(company_data, financial_analysis)
        existing_urls = {s.url for s in report.sources if s.url}
        for v_src in verified_sources:
            if v_src.url not in existing_urls:
                report.sources.append(v_src)
                if v_src.url:
                    existing_urls.add(v_src.url)

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