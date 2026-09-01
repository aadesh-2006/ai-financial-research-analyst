"""News client for retrieving recent corporate headlines and summaries."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
import yfinance as yf

from app.config import settings
from app.schemas.financial import DataWarning, NewsArticle
from app.utils.logging import logger


class NewsClient:
    """Client for fetching and normalizing corporate news from yfinance and Finnhub."""

    def __init__(self):
        self.finnhub_api_key = settings.finnhub_api_key

    def get_company_news(
        self, ticker: str, limit: int = 5
    ) -> tuple[List[NewsArticle], List[DataWarning]]:
        """
        Retrieves top recent news articles for the specified ticker.
        Returns:
            (List[NewsArticle], List[DataWarning])
        """
        clean_ticker = ticker.strip().upper()
        warnings: List[DataWarning] = []

        # 1. Try Finnhub if API key is provided
        if self.finnhub_api_key:
            try:
                articles = self._fetch_finnhub_news(clean_ticker, limit)
                if articles:
                    return articles, warnings
            except Exception as e:
                logger.warning(f"Finnhub news query failed for {clean_ticker}: {e}")
                warnings.append(
                    DataWarning(
                        provider="Finnhub",
                        field="news",
                        message=f"Finnhub news lookup failed: {str(e)}",
                    )
                )

        # 2. Primary / Default: yfinance news feed
        try:
            logger.info(f"Querying yfinance news for {clean_ticker}")
            t = yf.Ticker(clean_ticker)
            raw_news = t.news or []
            
            articles: List[NewsArticle] = []
            for item in raw_news:
                if len(articles) >= limit:
                    break

                # Handle modern nested 'content' structure or legacy flat structure
                content = item.get("content", item)
                
                title = content.get("title")
                if not title:
                    continue

                # URL extraction
                url = None
                canonical = content.get("canonicalUrl")
                if isinstance(canonical, dict):
                    url = canonical.get("url")
                elif isinstance(canonical, str):
                    url = canonical
                elif "link" in content:
                    url = content.get("link")

                # Publisher / Source
                provider = content.get("provider")
                source_name = None
                if isinstance(provider, dict):
                    source_name = provider.get("displayName")
                elif isinstance(provider, str):
                    source_name = provider
                elif "publisher" in content:
                    source_name = content.get("publisher")

                # Timestamp normalization
                pub_time = content.get("pubDate")
                if not pub_time and "providerPublishTime" in content:
                    try:
                        ts = int(content["providerPublishTime"])
                        pub_time = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                    except (ValueError, TypeError):
                        pub_time = None

                summary = content.get("summary")

                article = NewsArticle(
                    headline=title.strip(),
                    source=source_name,
                    url=url,
                    published_at=pub_time,
                    summary=summary.strip() if summary else None,
                )
                articles.append(article)

            if not articles:
                warnings.append(
                    DataWarning(
                        provider="yfinance",
                        field="news",
                        message=f"No recent news articles returned for {clean_ticker}.",
                    )
                )

            return articles, warnings

        except Exception as e:
            logger.warning(f"News collection failed for {clean_ticker}: {e}")
            warnings.append(
                DataWarning(
                    provider="yfinance",
                    field="news",
                    message=f"Failed to fetch news: {str(e)}",
                )
            )
            return [], warnings

    def _fetch_finnhub_news(self, ticker: str, limit: int) -> List[NewsArticle]:
        """Optional Finnhub news query."""
        today = datetime.now().strftime("%Y-%m-%d")
        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": ticker,
            "from": today,
            "to": today,
            "token": self.finnhub_api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        
        items = resp.json()
        results: List[NewsArticle] = []
        for item in items[:limit]:
            results.append(
                NewsArticle(
                    headline=item.get("headline", ""),
                    source=item.get("source"),
                    url=item.get("url"),
                    published_at=datetime.fromtimestamp(
                        item.get("datetime", 0), tz=timezone.utc
                    ).isoformat(),
                    summary=item.get("summary"),
                )
            )
        return results
