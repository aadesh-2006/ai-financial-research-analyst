"""FastAPI route definitions for the financial intelligence platform."""
from fastapi import APIRouter, Depends, status

from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    HealthResponse,
    ResearchRequest,
)
from app.data.orchestrator import DataOrchestrator
from app.financial.engine import FinancialAnalysisEngine
from app.research.schemas import ResearchReport
from app.research.service import ResearchService
from app.utils.logging import logger


def get_orchestrator() -> DataOrchestrator:
    """Dependency provider for DataOrchestrator."""
    return DataOrchestrator()


def get_financial_engine() -> FinancialAnalysisEngine:
    """Dependency provider for FinancialAnalysisEngine."""
    return FinancialAnalysisEngine()


def get_research_service() -> ResearchService:
    """Dependency provider for ResearchService."""
    return ResearchService()


router = APIRouter(prefix="/api", tags=["Financial Analysis & Research"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns service availability status. Does not query external financial APIs or LLM keys.",
)
async def health_check() -> HealthResponse:
    """Simple health check endpoint."""
    return HealthResponse(status="ok", service="ai-financial-research-analyst")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Malformed or invalid ticker request"},
        404: {"model": ErrorResponse, "description": "Ticker data not found in public filings or market"},
        502: {"model": ErrorResponse, "description": "Upstream SEC EDGAR or market data provider error"},
    },
    summary="Deterministic Financial Analysis & DCF Valuation",
    description=(
        "Collects public financial statements and quotes, calculates growth, margins, leverage, "
        "cash flow conversion, market multiples, financial health ratings, and model-implied DCF valuation. "
        "Does NOT require OPENAI_API_KEY."
    ),
)
async def analyze_company(
    payload: AnalyzeRequest,
    orchestrator: DataOrchestrator = Depends(get_orchestrator),
    engine: FinancialAnalysisEngine = Depends(get_financial_engine),
) -> AnalyzeResponse:
    """
    Exposes deterministic quantitative financial analysis.
    Pure mathematical calculations from SEC EDGAR and market quotes.
    """
    logger.info(f"Received API analysis request for ticker: {payload.ticker}")
    company_data = orchestrator.get_company_data(payload.ticker)
    analysis = engine.analyze(company_data)
    return AnalyzeResponse.from_analysis(analysis, company_data.company_profile, company_data.news[:5])


@router.post(
    "/research",
    response_model=ResearchReport,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Malformed or invalid ticker request"},
        404: {"model": ErrorResponse, "description": "Ticker data not found"},
        502: {"model": ErrorResponse, "description": "Upstream data or LLM communication error"},
        503: {"model": ErrorResponse, "description": "OPENAI_API_KEY missing or service unavailable"},
        504: {"model": ErrorResponse, "description": "Upstream LLM timeout"},
    },
    summary="Grounded AI Investment Research Memo",
    description=(
        "Executes data ingestion, deterministic financial and DCF analysis, and grounded LLM "
        "synthesis into an institutional investment research report. Requires OPENAI_API_KEY."
    ),
)
async def generate_research(
    payload: ResearchRequest,
    orchestrator: DataOrchestrator = Depends(get_orchestrator),
    engine: FinancialAnalysisEngine = Depends(get_financial_engine),
    research_service: ResearchService = Depends(get_research_service),
) -> ResearchReport:
    """
    Generates a structured, grounded investment research report.
    Consumes deterministic financial metrics and synthesizes qualitative insights.
    """
    logger.info(f"Received API research request for ticker: {payload.ticker}")
    company_data = orchestrator.get_company_data(payload.ticker)
    analysis = engine.analyze(company_data)
    report = research_service.generate_report(
        company_data=company_data,
        financial_analysis=analysis,
    )
    return report