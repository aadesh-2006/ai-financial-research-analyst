"""FastAPI route definitions for the financial intelligence platform."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    HealthResponse,
    ResearchRequest,
    CompanySummary,
    AnalysisSnapshotSummary,
    ResearchReportSummary,
)
from app.data.orchestrator import DataOrchestrator
from app.db.session import get_db
from app.db.repositories import (
    CompanyRepository,
    AnalysisRepository,
    ResearchRepository,
)
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


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    """Dependency provider for CompanyRepository."""
    return CompanyRepository(db)


def get_analysis_repo(db: Session = Depends(get_db)) -> AnalysisRepository:
    """Dependency provider for AnalysisRepository."""
    return AnalysisRepository(db)


def get_research_repo(db: Session = Depends(get_db)) -> ResearchRepository:
    """Dependency provider for ResearchRepository."""
    return ResearchRepository(db)


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
        500: {"model": ErrorResponse, "description": "Database persistence error"},
        502: {"model": ErrorResponse, "description": "Upstream SEC EDGAR or market data provider error"},
    },
    summary="Deterministic Financial Analysis & DCF Valuation",
    description=(
        "Collects public financial statements and quotes, calculates growth, margins, leverage, "
        "cash flow conversion, market multiples, financial health ratings, and model-implied DCF valuation. "
        "Persists the company and analysis snapshot in PostgreSQL."
    ),
)
async def analyze_company(
    payload: AnalyzeRequest,
    orchestrator: DataOrchestrator = Depends(get_orchestrator),
    engine: FinancialAnalysisEngine = Depends(get_financial_engine),
    company_repo: CompanyRepository = Depends(get_company_repo),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
) -> AnalyzeResponse:
    """
    Exposes deterministic quantitative financial analysis.
    Pure mathematical calculations from SEC EDGAR and market quotes with PostgreSQL persistence.
    """
    logger.info(f"Received API analysis request for ticker: {payload.ticker}")
    company_data = orchestrator.get_company_data(payload.ticker)
    analysis = engine.analyze(company_data)
    response_obj = AnalyzeResponse.from_analysis(
        analysis, company_data.company_profile, company_data.news[:5]
    )

    # Persist Company identity
    company = company_repo.upsert(
        ticker=response_obj.ticker,
        company_name=response_obj.company_name,
        sector=response_obj.sector,
        industry=response_obj.industry,
        currency=response_obj.currency,
        website=response_obj.website,
        description=response_obj.description,
    )

    # Parse ISO timestamp for snapshot
    try:
        analyzed_ts = datetime.fromisoformat(response_obj.analyzed_at)
    except Exception:
        analyzed_ts = None

    # Persist Analysis Snapshot
    analysis_repo.create_snapshot(
        company_id=company.id,
        dcf_status=response_obj.dcf.status if response_obj.dcf else "none",
        health_rating=response_obj.health.overall if response_obj.health else "Unknown",
        payload=response_obj.model_dump(),
        analyzed_at=analyzed_ts,
        current_share_price=response_obj.dcf.current_share_price if response_obj.dcf else None,
        implied_share_price=response_obj.dcf.implied_share_price if response_obj.dcf else None,
        upside_downside_pct=response_obj.dcf.upside_downside_pct if response_obj.dcf else None,
        wacc=response_obj.dcf.wacc if response_obj.dcf else None,
    )

    return response_obj


@router.post(
    "/research",
    response_model=ResearchReport,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Malformed or invalid ticker request"},
        404: {"model": ErrorResponse, "description": "Ticker data not found"},
        500: {"model": ErrorResponse, "description": "Database persistence error"},
        502: {"model": ErrorResponse, "description": "Upstream data or LLM communication error"},
        503: {"model": ErrorResponse, "description": "OPENAI_API_KEY missing or service unavailable"},
        504: {"model": ErrorResponse, "description": "Upstream LLM timeout"},
    },
    summary="Grounded AI Investment Research Memo",
    description=(
        "Executes data ingestion, deterministic financial and DCF analysis, and grounded LLM "
        "synthesis into an institutional investment research report. Persists report and citations."
    ),
)
async def generate_research(
    payload: ResearchRequest,
    orchestrator: DataOrchestrator = Depends(get_orchestrator),
    engine: FinancialAnalysisEngine = Depends(get_financial_engine),
    research_service: ResearchService = Depends(get_research_service),
    company_repo: CompanyRepository = Depends(get_company_repo),
    research_repo: ResearchRepository = Depends(get_research_repo),
) -> ResearchReport:
    """
    Generates a structured, grounded investment research report.
    Consumes deterministic financial metrics and synthesizes qualitative insights with DB persistence.
    """
    logger.info(f"Received API research request for ticker: {payload.ticker}")
    company_data = orchestrator.get_company_data(payload.ticker)
    analysis = engine.analyze(company_data)
    report = research_service.generate_report(
        company_data=company_data,
        financial_analysis=analysis,
    )

    # Persist Company identity
    company = company_repo.upsert(
        ticker=report.ticker,
        company_name=report.company_name,
        sector=company_data.company_profile.sector,
        industry=company_data.company_profile.industry,
        currency=company_data.company_profile.currency,
        website=company_data.company_profile.website,
        description=company_data.company_profile.description,
    )

    try:
        generated_ts = datetime.fromisoformat(report.generated_at)
    except Exception:
        generated_ts = None

    # Persist Report & Normalized Citations
    research_repo.create_report(
        company_id=company.id,
        payload=report.model_dump(),
        sources=[s.model_dump() for s in report.sources],
        confidence_level=report.confidence.level if report.confidence else None,
        valuation_signal=(
            report.dcf_interpretation.valuation_signal
            if report.dcf_interpretation
            else None
        ),
        generated_at=generated_ts,
    )

    return report


# ---------------------------------------------------------------------------
# History and Read-Only Persistence Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/companies",
    response_model=List[CompanySummary],
    status_code=status.HTTP_200_OK,
    summary="List Recently Analyzed Companies",
    description="Returns a list of all tracked and analyzed companies with latest snapshot metrics.",
)
async def list_companies(
    company_repo: CompanyRepository = Depends(get_company_repo),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
    limit: int = 20,
) -> List[CompanySummary]:
    """Returns recently analyzed companies with their latest status."""
    companies = company_repo.list_recent(limit=limit)
    summaries: List[CompanySummary] = []

    for c in companies:
        latest = analysis_repo.get_latest_by_ticker(c.ticker)
        summaries.append(
            CompanySummary(
                id=c.id,
                ticker=c.ticker,
                company_name=c.company_name,
                sector=c.sector,
                industry=c.industry,
                currency=c.currency,
                website=c.website,
                last_analyzed_at=latest.analyzed_at.isoformat() if latest else None,
                latest_share_price=float(latest.current_share_price) if latest and latest.current_share_price else None,
                latest_implied_price=float(latest.implied_share_price) if latest and latest.implied_share_price else None,
                latest_health=latest.health_rating if latest else None,
                dcf_status=latest.dcf_status if latest else None,
            )
        )

    return summaries


@router.get(
    "/companies/{ticker}/analyses",
    response_model=List[AnalysisSnapshotSummary],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Company ticker not found"},
    },
    summary="List Analysis Snapshots for a Company",
    description="Returns chronological analysis snapshots recorded for the given ticker.",
)
async def list_company_analyses(
    ticker: str,
    company_repo: CompanyRepository = Depends(get_company_repo),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
    limit: int = 50,
) -> List[AnalysisSnapshotSummary]:
    """Returns analysis history snapshots for a given company ticker."""
    clean_ticker = ticker.strip().upper()
    company = company_repo.get_by_ticker(clean_ticker)
    if not company:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TICKER_NOT_FOUND",
            message=f"No analysis history found for company ticker '{clean_ticker}'.",
        )

    snapshots = analysis_repo.list_by_ticker(clean_ticker, limit=limit)
    return [
        AnalysisSnapshotSummary(
            id=s.id,
            ticker=clean_ticker,
            analyzed_at=s.analyzed_at.isoformat(),
            current_share_price=float(s.current_share_price) if s.current_share_price else None,
            implied_share_price=float(s.implied_share_price) if s.implied_share_price else None,
            upside_downside_pct=float(s.upside_downside_pct) if s.upside_downside_pct else None,
            wacc=float(s.wacc) if s.wacc else None,
            dcf_status=s.dcf_status,
            health_rating=s.health_rating,
            payload=s.payload,
        )
        for s in snapshots
    ]


@router.get(
    "/companies/{ticker}/research",
    response_model=List[ResearchReportSummary],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Company ticker not found"},
    },
    summary="List Research Reports for a Company",
    description="Returns historical AI research reports generated for the given ticker.",
)
async def list_company_research(
    ticker: str,
    company_repo: CompanyRepository = Depends(get_company_repo),
    research_repo: ResearchRepository = Depends(get_research_repo),
    limit: int = 50,
) -> List[ResearchReportSummary]:
    """Returns research memo history for a given company ticker."""
    clean_ticker = ticker.strip().upper()
    company = company_repo.get_by_ticker(clean_ticker)
    if not company:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TICKER_NOT_FOUND",
            message=f"No research report history found for company ticker '{clean_ticker}'.",
        )

    reports = research_repo.list_by_ticker(clean_ticker, limit=limit)
    return [
        ResearchReportSummary(
            id=r.id,
            ticker=clean_ticker,
            generated_at=r.generated_at.isoformat(),
            confidence_level=r.confidence_level,
            valuation_signal=r.valuation_signal,
            executive_summary=r.payload.get("executive_summary") if isinstance(r.payload, dict) else None,
            sources_count=len(r.sources),
            payload=r.payload,
        )
        for r in reports
    ]