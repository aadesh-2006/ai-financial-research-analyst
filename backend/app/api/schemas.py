"""Pydantic schemas for the FastAPI backend layer."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.financial.schemas import FinancialAnalysis
from app.schemas.financial import CompanyProfile


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="ok", description="Service health status")
    service: str = Field(default="ai-financial-research-analyst", description="Service identifier")


class AnalyzeRequest(BaseModel):
    """Request payload for deterministic financial analysis."""
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Public company stock ticker symbol (e.g. AAPL, MSFT, JPM)",
        examples=["AAPL"],
    )

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Ticker symbol cannot be empty.")
        if not all(c.isalnum() or c in ".-" for c in cleaned):
            raise ValueError(f"Invalid ticker symbol format: '{v}'")
        return cleaned


class ResearchRequest(BaseModel):
    """Request payload for grounded LLM investment research memo."""
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Public company stock ticker symbol (e.g. AAPL, NVDA, JPM)",
        examples=["AAPL"],
    )

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Ticker symbol cannot be empty.")
        if not all(c.isalnum() or c in ".-" for c in cleaned):
            raise ValueError(f"Invalid ticker symbol format: '{v}'")
        return cleaned


class AnalyzeResponse(FinancialAnalysis):
    """
    API response model extending FinancialAnalysis with company profile details.
    Preserves deterministic ground truth while providing metadata for dashboard rendering.
    """
    description: Optional[str] = Field(default=None, description="Company business description")
    website: Optional[str] = Field(default=None, description="Official company website")
    news: List[Dict[str, Any]] = Field(default_factory=list, description="Recent verified market headlines")

    @classmethod
    def from_analysis(
        cls,
        analysis: FinancialAnalysis,
        profile: Optional[CompanyProfile] = None,
        news: Optional[List[Any]] = None,
    ) -> "AnalyzeResponse":
        """Factory method to cleanly build AnalyzeResponse from FinancialAnalysis and CompanyProfile."""
        data = analysis.model_dump()
        if profile:
            data["description"] = profile.description
            data["website"] = profile.website
        if news:
            data["news"] = [
                n.model_dump() if hasattr(n, "model_dump") else n for n in news
            ]
        return cls(**data)


class ErrorDetail(BaseModel):
    """Structured error payload details."""
    code: str = Field(..., description="Machine-readable application error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(default=None, description="Optional diagnostic details")


class ErrorResponse(BaseModel):
    """Standardized API error response format."""
    error: ErrorDetail