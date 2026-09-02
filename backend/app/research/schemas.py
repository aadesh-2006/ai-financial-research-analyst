"""Pydantic schemas for structured LLM investment research reports."""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """Source provenance tracking information for facts and market observations."""
    provider: str = Field(description="Data provider or filing authority (e.g. SEC_EDGAR, yfinance)")
    title: str = Field(description="Document title, filing description, or news headline")
    url: Optional[str] = Field(default=None, description="Direct URL if available")
    published_at: Optional[str] = Field(default=None, description="Filing or article publication timestamp")
    source_type: str = Field(
        default="filing",
        description="Type of source: 'filing', 'market_data', 'news', or 'valuation_model'",
    )


class FinancialSnapshot(BaseModel):
    """Executive financial performance summary."""
    summary: str = Field(description="High-level overview of historical growth, revenue, and margins")
    key_points: List[str] = Field(description="Key quantitative milestones and bullet points")
    revenue_growth_yoy_pct: Optional[float] = Field(
        default=None, description="Deterministic revenue YoY growth % anchored to financial engine"
    )
    operating_margin_pct: Optional[float] = Field(
        default=None, description="Deterministic operating margin % anchored to financial engine"
    )
    net_margin_pct: Optional[float] = Field(
        default=None, description="Deterministic net margin % anchored to financial engine"
    )
    free_cash_flow: Optional[float] = Field(
        default=None, description="Deterministic latest annual Free Cash Flow in native currency"
    )


class ValuationAssessment(BaseModel):
    """Synthesis of market multiples and trading levels."""
    summary: str = Field(description="Qualitative assessment of P/E, EV/EBITDA, P/S relative to performance")
    multiples_summary: str = Field(description="Concise description of key trading multiples")
    key_points: List[str] = Field(description="Core valuation takeaways and observations")
    current_share_price: Optional[float] = Field(default=None, description="Deterministic current market price")
    pe_ratio: Optional[float] = Field(default=None, description="Deterministic trailing P/E multiple")
    forward_pe: Optional[float] = Field(default=None, description="Deterministic forward P/E multiple")
    price_to_sales: Optional[float] = Field(default=None, description="Deterministic Price-to-Sales multiple")
    ev_to_ebitda: Optional[float] = Field(default=None, description="Deterministic EV/EBITDA multiple")
    price_to_book: Optional[float] = Field(
        default=None, description="Price-to-Book multiple (None if not available in valuation engine)"
    )


class FinancialHealthAssessment(BaseModel):
    """Interpretation of balance sheet solvency, leverage, and cash conversion."""
    summary: str = Field(description="Synthesis of financial stability, debt obligations, and cash buffer")
    overall_rating: str = Field(description="Engine health rating (e.g. Strong, Moderate, Cautious)")
    observations: List[str] = Field(description="Pillar observations across growth, margin, leverage, cash flow")


class DCFInterpretation(BaseModel):
    """Rigorous qualitative interpretation of deterministic DCF valuation and sensitivity."""
    summary: str = Field(description="Explanation of DCF model assumptions (WACC, terminal growth, FCF projection)")
    valuation_signal: str = Field(
        description="Qualitative signal indicating how market price compares to model-implied value without guarantees"
    )
    sensitivity_observation: str = Field(
        description="Discussion of valuation dispersion across WACC and Terminal Growth rate scenarios"
    )
    model_wacc_pct: Optional[float] = Field(
        default=None, description="Deterministic WACC % from engine (None for financial institutions)"
    )
    model_terminal_growth_pct: Optional[float] = Field(
        default=None, description="Deterministic terminal growth % from engine (None for financial institutions)"
    )
    model_implied_share_price: Optional[float] = Field(
        default=None, description="Deterministic implied share price from engine (None for financial institutions)"
    )
    model_upside_downside_pct: Optional[float] = Field(
        default=None,
        description="Deterministic model-implied upside/downside percentage from engine (None for financial institutions)",
    )


class NewsMarketContext(BaseModel):
    """Contextual corporate events and sentiment from verified news."""
    summary: str = Field(description="Synthesis of recent news developments and operational context")
    relevant_headlines: List[str] = Field(description="List of verified headlines evaluated")


class ReportConfidence(BaseModel):
    """Confidence evaluation based on data availability, filing recency, and assumptions."""
    level: str = Field(description="Confidence rating: 'High', 'Medium', or 'Cautious'")
    rationale: str = Field(description="Justification based on data completeness and forecast uncertainty")


class ResearchReport(BaseModel):
    """Institutional-style investment research report generated via grounded LLM synthesis."""
    ticker: str = Field(description="Company ticker symbol")
    company_name: str = Field(description="Official company name")
    executive_summary: str = Field(description="High-level executive briefing for investment committees")
    investment_thesis: str = Field(description="Core fundamental investment thesis and narrative")
    financial_snapshot: FinancialSnapshot
    valuation_assessment: ValuationAssessment
    strengths: List[str] = Field(description="Key competitive advantages, balance sheet strengths, and growth drivers")
    risks: List[str] = Field(description="Key fundamental, macroeconomic, leverage, or execution risks")
    catalysts: List[str] = Field(description="Potential positive drivers, product launches, or market expansions")
    concerns: List[str] = Field(description="Vulnerabilities, margin pressures, or balance sheet cautions")
    financial_health_assessment: FinancialHealthAssessment
    dcf_interpretation: DCFInterpretation
    news_and_market_context: NewsMarketContext
    conclusion: str = Field(description="Final balanced synthesis and key monitorables")
    confidence: ReportConfidence
    limitations: List[str] = Field(description="Methodological limitations, model assumptions, and data caveats")
    sources: List[ResearchSource] = Field(description="List of verified data sources and citations")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when research report was generated",
    )
    model_name: Optional[str] = Field(default=None, description="LLM model identifier used for synthesis")
    disclaimer: str = Field(
        default=(
            "This research report is generated automatically by an AI financial research analyst "
            "for institutional informational and educational purposes only. It does not constitute "
            "financial, investment, legal, or tax advice. Valuation figures represent model-implied "
            "mathematical derivations based on explicit assumptions and do not guarantee future returns."
        ),
        description="Standard legal and institutional disclaimer",
    )