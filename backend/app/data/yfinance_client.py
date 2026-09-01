"""yfinance market data client and normalizer."""
import math
from typing import Any, Dict, List, Optional, Tuple

import yfinance as yf

from app.schemas.financial import CompanyProfile, DataWarning, MarketData
from app.utils.logging import logger


class YFinanceClient:
    """Client for retrieving and normalizing market prices and multiples via yfinance."""

    @staticmethod
    def _clean_float(val: Any) -> Optional[float]:
        """Sanitizes raw values, converting NaNs and invalid types to None."""
        if val is None:
            return None
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return None
            return f
        except (ValueError, TypeError):
            return None

    def _resolve_first_valid(self, info: Dict[str, Any], keys: List[str]) -> Optional[float]:
        """Iterates through keys and returns the first valid non-NaN float."""
        for k in keys:
            val = self._clean_float(info.get(k))
            if val is not None:
                return val
        return None

    def get_market_data(
        self, ticker: str
    ) -> Tuple[Optional[MarketData], Optional[CompanyProfile], List[DataWarning]]:
        """
        Retrieves real-time/delayed market quotes and valuation multiples.
        Returns:
            (MarketData, CompanyProfile, List[DataWarning])
        """
        clean_ticker = ticker.strip().upper()
        warnings: List[DataWarning] = []

        try:
            logger.info(f"Querying yfinance for {clean_ticker}")
            t = yf.Ticker(clean_ticker)
            info = t.info or {}

            # Fast validity check
            if not info or ("regularMarketPrice" not in info and "currentPrice" not in info and "symbol" not in info):
                warnings.append(
                    DataWarning(
                        provider="yfinance",
                        field="ticker",
                        message=f"No quote or company information returned by yfinance for {clean_ticker}.",
                    )
                )
                return None, None, warnings

            # Current price resolution hierarchy (handles NaN truthiness cleanly)
            price = self._resolve_first_valid(info, ["currentPrice", "regularMarketPrice", "ask", "bid"])
            prev_close = self._resolve_first_valid(info, ["regularMarketPreviousClose", "previousClose"])
            high_52 = self._clean_float(info.get("fiftyTwoWeekHigh"))
            low_52 = self._clean_float(info.get("fiftyTwoWeekLow"))
            mkt_cap = self._clean_float(info.get("marketCap"))
            shares_out = self._resolve_first_valid(info, ["sharesOutstanding", "impliedSharesOutstanding"])
            beta = self._clean_float(info.get("beta"))
            pe = self._clean_float(info.get("trailingPE"))
            fwd_pe = self._clean_float(info.get("forwardPE"))
            ev_ebitda = self._clean_float(info.get("enterpriseToEbitda"))
            ev = self._clean_float(info.get("enterpriseValue"))
            div_yield = self._clean_float(info.get("dividendYield"))
            total_cash = self._clean_float(info.get("totalCash"))
            total_debt = self._clean_float(info.get("totalDebt"))
            currency = str(info.get("currency") or "USD").upper()

            market_data = MarketData(
                current_price=price,
                previous_close=prev_close,
                fifty_two_week_high=high_52,
                fifty_two_week_low=low_52,
                market_cap=mkt_cap,
                shares_outstanding=shares_out,
                beta=beta,
                pe_ratio=pe,
                forward_pe=fwd_pe,
                ev_to_ebitda=ev_ebitda,
                enterprise_value=ev,
                dividend_yield=div_yield,
                total_cash=total_cash,
                total_debt=total_debt,
                source="yfinance",
                currency=currency,
            )

            # Extract basic company profile metadata
            name = (
                info.get("longName")
                or info.get("shortName")
                or clean_ticker
            )
            profile = CompanyProfile(
                ticker=clean_ticker,
                name=name,
                sector=info.get("sector"),
                industry=info.get("industry"),
                description=info.get("longBusinessSummary"),
                website=info.get("website"),
                currency=currency,
            )

            # Record missing metrics warnings if critical
            if price is None:
                warnings.append(
                    DataWarning(
                        provider="yfinance",
                        field="current_price",
                        message="Market price not available from yfinance.",
                    )
                )

            return market_data, profile, warnings

        except Exception as e:
            logger.error(f"Failed to retrieve market data for {clean_ticker}: {e}")
            warnings.append(
                DataWarning(
                    provider="yfinance",
                    field="market_data",
                    message=f"yfinance lookup error: {str(e)}",
                )
            )
            return None, None, warnings
