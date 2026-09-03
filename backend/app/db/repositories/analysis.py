"""Repository for AnalysisSnapshot operations."""
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import AnalysisSnapshot, Company


class AnalysisRepository:
    """Manages database persistence for deterministic AnalysisSnapshot records."""

    def __init__(self, db: Session):
        self.db = db

    def create_snapshot(
        self,
        company_id: int,
        dcf_status: str,
        health_rating: str,
        payload: Dict[str, Any],
        analyzed_at: Optional[datetime] = None,
        current_share_price: Optional[float] = None,
        implied_share_price: Optional[float] = None,
        upside_downside_pct: Optional[float] = None,
        wacc: Optional[float] = None,
    ) -> AnalysisSnapshot:
        """Persists a new deterministic analysis snapshot."""
        timestamp = analyzed_at or datetime.now(timezone.utc)
        snapshot = AnalysisSnapshot(
            company_id=company_id,
            analyzed_at=timestamp,
            current_share_price=current_share_price,
            implied_share_price=implied_share_price,
            upside_downside_pct=upside_downside_pct,
            wacc=wacc,
            dcf_status=dcf_status,
            health_rating=health_rating,
            payload=payload,
        )
        try:
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            return snapshot
        except Exception:
            self.db.rollback()
            raise

    def list_by_ticker(self, ticker: str, limit: int = 50) -> List[AnalysisSnapshot]:
        """Returns analysis history snapshots for a given company ticker, ordered by most recent."""
        norm_ticker = ticker.strip().upper()
        stmt = (
            select(AnalysisSnapshot)
            .join(Company)
            .where(Company.ticker == norm_ticker)
            .order_by(AnalysisSnapshot.analyzed_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_by_ticker(self, ticker: str) -> Optional[AnalysisSnapshot]:
        """Returns the most recent analysis snapshot for a given company ticker."""
        snapshots = self.list_by_ticker(ticker, limit=1)
        return snapshots[0] if snapshots else None