"""Normalized financial data schemas."""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CompanyProfile(BaseModel):
    """Normalized company identity and classification."""
    ticker: str
    name: str
    cik: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    currency: str = "USD"


class HistoricalFinancial(BaseModel):
    """Annual financial statement line items normalized from SEC EDGAR."""
    fiscal_year: int
    period: str = "FY"
    filing_date: Optional[str] = None
    form: str = "10-K"
    
    # Income Statement
    revenue: Optional[float] = Field(default=None, description="Total Revenue / Sales in native currency")
    operating_income: Optional[float] = Field(default=None, description="Operating Income (EBIT)")
    net_income: Optional[float] = Field(default=None, description="Net Income attributable to shareholders")
    
    # Cash Flow Statement
    operating_cash_flow: Optional[float] = Field(default=None, description="Net Cash from Operating Activities")
    capex: Optional[float] = Field(default=None, description="Capital Expenditures (positive cash outflow)")
    free_cash_flow: Optional[float] = Field(default=None, description="Operating Cash Flow - Capex")
    
    # Balance Sheet
    total_assets: Optional[float] = Field(default=None, description="Total Assets")
    total_liabilities: Optional[float] = Field(default=None, description="Total Liabilities")
    total_debt: Optional[float] = Field(default=None, description="Short-Term + Long-Term Debt")
    stockholders_equity: Optional[float] = Field(default=None, description="Stockholders' Equity")
    cash_and_equivalents: Optional[float] = Field(default=None, description="Cash & Cash Equivalents")
    
    source: str = "SEC_EDGAR"
    currency: str = "USD"


class MarketData(BaseModel):
    """Normalized trading and valuation market metrics from yfinance."""
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    market_cap: Optional[float] = None
    shares_outstanding: Optional[float] = None
    beta: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    enterprise_value: Optional[float] = None
    dividend_yield: Optional[float] = None
    total_cash: Optional[float] = Field(default=None, description="Total Cash & Short Term Investments")
    total_debt: Optional[float] = Field(default=None, description="Total Debt reported by market quote")
    source: str = "yfinance"
    currency: str = "USD"


class NewsArticle(BaseModel):
    """Normalized recent corporate news article."""
    headline: str
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None
    summary: Optional[str] = None


class DataWarning(BaseModel):
    """Informational note about missing, non-standard, or partial data."""
    provider: str
    field: str
    message: str


class CompanyData(BaseModel):
    """Complete normalized data bundle for a public company."""
    ticker: str
    company_profile: CompanyProfile
    historical_financials: List[HistoricalFinancial] = Field(default_factory=list)
    market_data: MarketData
    news: List[NewsArticle] = Field(default_factory=list)
    data_warnings: List[DataWarning] = Field(default_factory=list)
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()
