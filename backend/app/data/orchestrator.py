"""Data ingestion orchestrator combining SEC EDGAR, yfinance, and news sources."""
import argparse
import json
import sys
from typing import Optional

from app.data.news_client import NewsClient
from app.data.sec_edgar import SECEdgarClient
from app.data.yfinance_client import YFinanceClient
from app.schemas.financial import (
    CompanyData,
    CompanyProfile,
    DataWarning,
    MarketData,
)
from app.utils.logging import logger


class DataOrchestrator:
    """Orchestrates data collection from multiple sources into normalized CompanyData."""

    def __init__(
        self,
        sec_client: Optional[SECEdgarClient] = None,
        yf_client: Optional[YFinanceClient] = None,
        news_client: Optional[NewsClient] = None,
    ):
        self.sec_client = sec_client or SECEdgarClient()
        self.yf_client = yf_client or YFinanceClient()
        self.news_client = news_client or NewsClient()

    def get_company_data(self, ticker: str) -> CompanyData:
        """
        Coordinates full ingestion and normalization pipeline for a ticker symbol.
        Handles provider failures gracefully with descriptive warnings.
        """
        clean_ticker = ticker.strip().upper()
        logger.info(f"Starting data ingestion pipeline for ticker: {clean_ticker}")
        all_warnings: list[DataWarning] = []

        # 1. Fetch market data & profile from yfinance
        market_data: Optional[MarketData] = None
        yf_profile: Optional[CompanyProfile] = None
        try:
            market_data, yf_profile, yf_warnings = self.yf_client.get_market_data(clean_ticker)
            all_warnings.extend(yf_warnings)
        except Exception as e:
            logger.error(f"yfinance error during orchestration for {clean_ticker}: {e}")
            all_warnings.append(
                DataWarning(provider="yfinance", field="all", message=str(e))
            )

        # 2. Fetch SEC EDGAR financials
        sec_financials = []
        sec_name: Optional[str] = None
        cik: Optional[str] = None
        try:
            cik = self.sec_client.resolve_cik(clean_ticker)
            if cik:
                facts = self.sec_client.get_company_facts(cik)
                if facts:
                    sec_financials, sec_warnings, sec_name = self.sec_client.parse_financials(facts)
                    all_warnings.extend(sec_warnings)
                else:
                    all_warnings.append(
                        DataWarning(
                            provider="SEC_EDGAR",
                            field="company_facts",
                            message=f"No company facts available from SEC for CIK {cik}.",
                        )
                    )
            else:
                all_warnings.append(
                    DataWarning(
                        provider="SEC_EDGAR",
                        field="cik",
                        message=f"Could not resolve CIK for ticker {clean_ticker}.",
                    )
                )
        except Exception as e:
            logger.error(f"SEC EDGAR error during orchestration for {clean_ticker}: {e}")
            all_warnings.append(
                DataWarning(provider="SEC_EDGAR", field="all", message=str(e))
            )

        # 3. Fetch News
        news_articles = []
        try:
            news_articles, news_warnings = self.news_client.get_company_news(clean_ticker)
            all_warnings.extend(news_warnings)
        except Exception as e:
            logger.warning(f"News collection failed for {clean_ticker}: {e}")
            all_warnings.append(
                DataWarning(provider="news", field="all", message=str(e))
            )

        # Validate that we have at least SOME data
        if not market_data and not sec_financials:
            raise ValueError(
                f"Failed to retrieve data for ticker '{clean_ticker}'. "
                f"Verify the ticker symbol is valid and public."
            )

        # 4. Construct unified CompanyProfile
        company_name = (
            sec_name
            or (yf_profile.name if yf_profile else None)
            or clean_ticker
        )
        sector = yf_profile.sector if yf_profile else None
        industry = yf_profile.industry if yf_profile else None
        description = yf_profile.description if yf_profile else None
        website = yf_profile.website if yf_profile else None
        currency = (
            (market_data.currency if market_data else None)
            or (yf_profile.currency if yf_profile else None)
            or "USD"
        )

        profile = CompanyProfile(
            ticker=clean_ticker,
            name=company_name,
            cik=cik,
            sector=sector,
            industry=industry,
            description=description,
            website=website,
            currency=currency,
        )

        # Ensure market_data object exists
        final_market_data = market_data or MarketData(
            source="unavailable",
            currency=currency,
        )

        company_data = CompanyData(
            ticker=clean_ticker,
            company_profile=profile,
            historical_financials=sec_financials,
            market_data=final_market_data,
            news=news_articles,
            data_warnings=all_warnings,
        )

        logger.info(
            f"Pipeline complete for {clean_ticker}: "
            f"{len(sec_financials)} annual periods, "
            f"{len(news_articles)} news articles, "
            f"{len(all_warnings)} warnings."
        )

        return company_data


def main():
    """Command-line interface for testing the data ingestion pipeline."""
    parser = argparse.ArgumentParser(description="Test AI Financial Analyst data pipeline.")
    parser.add_argument("ticker", type=str, help="Public stock ticker symbol (e.g. AAPL, MSFT, JPM)")
    parser.add_argument("--json", action="store_true", help="Output full normalized JSON")
    args = parser.parse_args()

    orchestrator = DataOrchestrator()
    try:
        data = orchestrator.get_company_data(args.ticker)
    except Exception as e:
        print(f"Error executing pipeline: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(data.model_dump_json(indent=2))
        return

    # Formatted terminal report
    p = data.company_profile
    m = data.market_data
    print("\n" + "=" * 65)
    print(f" COMPANY DATA REPORT: {p.ticker} — {p.name}")
    print("=" * 65)
    print(f" Sector: {p.sector or 'N/A'} | Industry: {p.industry or 'N/A'}")
    print(f" CIK: {p.cik or 'N/A'} | Website: {p.website or 'N/A'}")
    print("-" * 65)
    print(f" MARKET DATA (yfinance):")
    price_str = f"${m.current_price:.2f}" if m.current_price else "N/A"
    cap_str = f"${m.market_cap:,.0f}" if m.market_cap else "N/A"
    pe_str = f"{m.pe_ratio:.2f}x" if m.pe_ratio else "N/A"
    ev_ebitda_str = f"{m.ev_to_ebitda:.2f}x" if m.ev_to_ebitda else "N/A"
    print(f" Price: {price_str} | Market Cap: {cap_str} | Beta: {m.beta or 'N/A'}")
    print(f" Trailing P/E: {pe_str} | EV/EBITDA: {ev_ebitda_str}")
    print("-" * 65)
    print(f" HISTORICAL FINANCIALS (SEC EDGAR 10-K):")
    if data.historical_financials:
        for f in data.historical_financials:
            rev = f"${f.revenue:,.0f}" if f.revenue else "N/A"
            ni = f"${f.net_income:,.0f}" if f.net_income else "N/A"
            ocf = f"${f.operating_cash_flow:,.0f}" if f.operating_cash_flow else "N/A"
            fcf = f"${f.free_cash_flow:,.0f}" if f.free_cash_flow else "N/A"
            print(f"  FY{f.fiscal_year}: Rev: {rev:<16} | NI: {ni:<15} | OCF: {ocf:<16} | FCF: {fcf}")
    else:
        print("  No 10-K historical financial data extracted.")
    print("-" * 65)
    print(f" RECENT NEWS ({len(data.news)} articles):")
    for a in data.news[:3]:
        print(f"  * {a.headline[:65]}... ({a.source or 'Unknown'})")
    if data.data_warnings:
        print("-" * 65)
        print(f" DATA WARNINGS ({len(data.data_warnings)}):")
        for w in data.data_warnings:
            print(f"  [!] [{w.provider}] {w.field}: {w.message}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
