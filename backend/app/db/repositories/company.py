"""Repository for Company entity operations."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Company


class CompanyRepository:
    """Manages database persistence for Company records."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_ticker(self, ticker: str) -> Optional[Company]:
        """Lookup company by unique normalized ticker symbol."""
        stmt = select(Company).where(Company.ticker == ticker.strip().upper())
        return self.db.scalars(stmt).first()

    def get_by_id(self, company_id: int) -> Optional[Company]:
        """Lookup company by primary key."""
        return self.db.get(Company, company_id)

    def upsert(
        self,
        ticker: str,
        company_name: str,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        currency: str = "USD",
        website: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Company:
        """
        Creates or updates a Company record.
        Maintains unique identity while refreshing sector, industry, and profile details.
        """
        norm_ticker = ticker.strip().upper()
        company = self.get_by_ticker(norm_ticker)

        if not company:
            company = Company(
                ticker=norm_ticker,
                company_name=company_name,
                sector=sector,
                industry=industry,
                currency=currency,
                website=website,
                description=description,
            )
            self.db.add(company)
        else:
            company.company_name = company_name
            if sector is not None:
                company.sector = sector
            if industry is not None:
                company.industry = industry
            if currency:
                company.currency = currency
            if website is not None:
                company.website = website
            if description is not None:
                company.description = description

        self.db.commit()
        self.db.refresh(company)
        return company

    def list_recent(self, limit: int = 20) -> List[Company]:
        """Returns companies ordered by most recent update."""
        stmt = select(Company).order_by(Company.updated_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())