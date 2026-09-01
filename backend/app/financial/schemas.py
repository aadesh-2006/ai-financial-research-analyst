"""Pydantic schemas for the deterministic financial analysis engine."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Metric(BaseModel):
    """Explainable financial metric carrying calculated value, methodology, and status."""
    value: Optional[float] = None
    unit: str = "percentage"  # percentage, ratio, multiple, currency, index
    formula: str = ""
    source_fields: List[str] = Field(default_factory=list)
    status: str = "available"  # available, unavailable, not_applicable
    warning: Optional[str] = None


class FinancialTrend(BaseModel):
    """Year-by-year financial trend snapshot for charting and historical comparisons."""
    fiscal_year: int
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    operating_income: Optional[float] = None
    operating_margin: Optional[float] = None
    net_income: Optional[float] = None
    net_margin: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    fcf_margin: Optional[float] = None


class GrowthAnalysis(BaseModel):
    """Deterministic growth metrics and historical time-series."""
    revenue_growth_yoy: Optional[float] = None
    revenue_cagr_3yr: Optional[float] = None
    net_income_growth_yoy: Optional[float] = None
    fcf_growth_yoy: Optional[float] = None
    revenue_growth_series: List[Dict[str, Any]] = Field(default_factory=list)
    net_income_growth_series: List[Dict[str, Any]] = Field(default_factory=list)
    fcf_growth_series: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Metric] = Field(default_factory=dict)


class ProfitabilityAnalysis(BaseModel):
    """Deterministic profitability, margins, and return ratios."""
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    metrics: Dict[str, Metric] = Field(default_factory=dict)


class LeverageAnalysis(BaseModel):
    """Deterministic solvency and leverage ratios."""
    debt_to_equity: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    interest_coverage: Optional[float] = None
    total_debt: Optional[float] = None
    stockholders_equity: Optional[float] = None
    metrics: Dict[str, Metric] = Field(default_factory=dict)


class CashFlowAnalysis(BaseModel):
    """Deterministic cash generation and conversion metrics."""
    operating_cash_flow: Optional[float] = None
    capex: Optional[float] = None
    free_cash_flow: Optional[float] = None
    fcf_margin: Optional[float] = None
    fcf_conversion: Optional[float] = None
    metrics: Dict[str, Metric] = Field(default_factory=dict)


class ValuationMetrics(BaseModel):
    """Trading valuation multiples combining market data and engine derivations."""
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_fcf: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    metrics: Dict[str, Metric] = Field(default_factory=dict)


class FinancialHealth(BaseModel):
    """Transparent, deterministic evaluation of company financial characteristics."""
    overall: str = "Neutral"  # Strong, Moderate, Cautious, Neutral
    growth_pillar: str = "Neutral"
    profitability_pillar: str = "Neutral"
    leverage_pillar: str = "Neutral"
    cash_flow_pillar: str = "Neutral"
    key_observations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DCFProjection(BaseModel):
    """Annual Free Cash Flow projection and discounting details."""
    year: int
    projected_fcf: float
    discount_factor: float
    present_value: float


class SensitivityCell(BaseModel):
    """Single coordinate within the 2D WACC x Terminal Growth sensitivity matrix."""
    wacc: float
    terminal_growth: float
    implied_share_price: Optional[float] = None


class SensitivityTable(BaseModel):
    """2D matrix of implied share prices across WACC and Terminal Growth rates."""
    wacc_range: List[float] = Field(default_factory=list)
    terminal_growth_range: List[float] = Field(default_factory=list)
    grid: List[List[Optional[float]]] = Field(default_factory=list)
    cells: List[SensitivityCell] = Field(default_factory=list)


class DCFValuation(BaseModel):
    """Comprehensive, deterministic Discounted Cash Flow valuation model."""
    status: str = "calculated"  # calculated, not_applicable, insufficient_data, error
    risk_free_rate: Optional[float] = None
    beta: Optional[float] = None
    equity_risk_premium: float = 0.05
    cost_of_equity: Optional[float] = None
    pre_tax_cost_of_debt: Optional[float] = None
    tax_rate: float = 0.21
    after_tax_cost_of_debt: Optional[float] = None
    market_value_equity: Optional[float] = None
    market_value_debt: Optional[float] = None
    equity_weight: Optional[float] = None
    debt_weight: Optional[float] = None
    wacc: Optional[float] = None
    fcf_growth_assumption: Optional[float] = None
    terminal_growth_rate: float = 0.025
    projections: List[DCFProjection] = Field(default_factory=list)
    pv_explicit_fcf: Optional[float] = None
    terminal_value: Optional[float] = None
    pv_terminal_value: Optional[float] = None
    enterprise_value: Optional[float] = None
    cash: Optional[float] = None
    total_debt: Optional[float] = None
    net_debt: Optional[float] = None
    equity_value: Optional[float] = None
    shares_outstanding: Optional[float] = None
    current_share_price: Optional[float] = None
    implied_share_price: Optional[float] = None
    upside_downside_pct: Optional[float] = None
    sensitivity_table: Optional[SensitivityTable] = None
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Metric] = Field(default_factory=dict)


class FinancialAnalysis(BaseModel):
    """Complete structured financial analysis bundle generated by the deterministic engine."""
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"
    growth: GrowthAnalysis
    profitability: ProfitabilityAnalysis
    leverage: LeverageAnalysis
    cash_flow: CashFlowAnalysis
    valuation: ValuationMetrics
    dcf: Optional[DCFValuation] = None
    historical_trends: List[FinancialTrend] = Field(default_factory=list)
    health: FinancialHealth
    warnings: List[str] = Field(default_factory=list)
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )