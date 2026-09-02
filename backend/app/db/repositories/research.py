"""Repository for ResearchReportRecord and ResearchSourceRecord operations."""
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import ResearchReportRecord, ResearchSourceRecord, Company


class ResearchRepository:
    """Manages database persistence for qualitative ResearchReport records and source citations."""

    def __init__(self, db: Session):
        self.db = db

    def create_report(
        self,
        company_id: int,
        payload: Dict[str, Any],
        sources: List[Dict[str, Any]],
        confidence_level: Optional[str] = None,
        valuation_signal: Optional[str] = None,
        generated_at: Optional[datetime] = None,
    ) -> ResearchReportRecord:
        """Persists an AI research report along with its verified citation sources."""
        timestamp = generated_at or datetime.now(timezone.utc)
        report = ResearchReportRecord(
            company_id=company_id,
            generated_at=timestamp,
            confidence_level=confidence_level,
            valuation_signal=valuation_signal,
            payload=payload,
        )
        self.db.add(report)
        self.db.flush()  # Generate report.id for source foreign keys

        for s in sources:
            source_rec = ResearchSourceRecord(
                research_report_id=report.id,
                provider=s.get("provider", "UNKNOWN"),
                title=s.get("title", ""),
                url=s.get("url"),
                published_at=str(s.get("published_at")) if s.get("published_at") else None,
                source_type=s.get("source_type", "filing"),
            )
            self.db.add(source_rec)

        self.db.commit()
        self.db.refresh(report)
        return report

    def list_by_ticker(self, ticker: str, limit: int = 50) -> List[ResearchReportRecord]:
        """Returns research reports for a company ticker, ordered by most recent."""
        norm_ticker = ticker.strip().upper()
        stmt = (
            select(ResearchReportRecord)
            .join(Company)
            .where(Company.ticker == norm_ticker)
            .order_by(ResearchReportRecord.generated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_by_ticker(self, ticker: str) -> Optional[ResearchReportRecord]:
        """Returns the most recent research report for a company ticker."""
        reports = self.list_by_ticker(ticker, limit=1)
        return reports[0] if reports else None