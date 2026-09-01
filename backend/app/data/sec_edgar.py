"""SEC EDGAR API Client for company financials retrieval and XBRL normalization."""
import json
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.config import settings
from app.schemas.financial import DataWarning, HistoricalFinancial
from app.utils.logging import logger

# Tag hierarchies in priority order for US-GAAP concepts
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "TotalRevenuesAndOtherIncome",
    "InterestAndDividendIncomeOperating",
]

OPERATING_INCOME_TAGS = [
    "OperatingIncomeLoss",
]

NET_INCOME_TAGS = [
    "NetIncomeLoss",
    "ProfitLoss",
    "NetIncomeLossAvailableToCommonStockholdersBasic",
]

OPERATING_CASH_FLOW_TAGS = [
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
]

CAPEX_TAGS = [
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
    "PaymentsForCapitalImprovements",
    "PaymentsToAcquireProductiveAssetsAndPropertyPlantAndEquipment",
]

TOTAL_ASSETS_TAGS = [
    "Assets",
]

TOTAL_LIABILITIES_TAGS = [
    "Liabilities",
]

STOCKHOLDERS_EQUITY_TAGS = [
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "CommonStockholdersEquity",
]

# Debt components
DEBT_LONG_TERM_TAGS = ["LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations"]
DEBT_SHORT_TERM_TAGS = ["DebtCurrent", "LongTermDebtCurrent", "ShortTermBorrowings"]

# Curated CIK seed map for common enterprise tickers
PRESEEDED_CIKS: Dict[str, str] = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
    "GOOG": "0001652044",
    "META": "0001326801",
    "JPM": "0000019617",
    "XOM": "0000034088",
    "JNJ": "0000200406",
    "WMT": "0000104169",
    "TSLA": "0001318605",
    "BRK.B": "0001067983",
    "V": "0001403161",
}


class SECEdgarClient:
    """Client for SEC EDGAR company facts and XBRL financials."""

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or settings.sec_user_agent
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        })
        self._last_request_time: float = 0.0
        self._cik_cache: Dict[str, str] = dict(PRESEEDED_CIKS)
        self._cache_dir = Path(".cache")
        self._cache_dir.mkdir(exist_ok=True)

    def _throttle(self) -> None:
        """Enforce SEC rate limit (max 10 requests/sec, conservative 8 req/sec)."""
        elapsed = time.time() - self._last_request_time
        min_interval = 0.125  # 8 requests per second max
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def resolve_cik(self, ticker: str) -> Optional[str]:
        """Resolves a ticker symbol to a 10-digit CIK string."""
        clean_ticker = ticker.strip().upper().replace(".", "-")
        if clean_ticker in self._cik_cache:
            return self._cik_cache[clean_ticker]

        # Check local file cache
        cache_file = self._cache_dir / "sec_tickers.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    file_cache = json.load(f)
                    self._cik_cache.update(file_cache)
                    if clean_ticker in self._cik_cache:
                        return self._cik_cache[clean_ticker]
            except Exception as e:
                logger.warning(f"Failed to read CIK cache file: {e}")

        # Fetch live mapping from SEC
        try:
            logger.info(f"Fetching CIK ticker directory from SEC EDGAR for {clean_ticker}")
            self._throttle()
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=headers,
                timeout=settings.sec_request_timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                new_cache: Dict[str, str] = {}
                for item in data.values():
                    t = str(item.get("ticker", "")).strip().upper()
                    c = str(item.get("cik_str", "")).zfill(10)
                    if t and c:
                        new_cache[t] = c
                self._cik_cache.update(new_cache)
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(self._cik_cache, f)
                except Exception as e:
                    logger.warning(f"Could not persist CIK cache file: {e}")

                return self._cik_cache.get(clean_ticker)
            else:
                logger.error(f"SEC ticker directory returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Error resolving CIK for ticker {ticker}: {e}")

        return None

    def get_company_facts(self, cik: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw company facts JSON from SEC EDGAR API."""
        padded_cik = str(cik).zfill(10)
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{padded_cik}.json"
        
        try:
            self._throttle()
            logger.info(f"Requesting SEC Company Facts for CIK {padded_cik}")
            resp = self.session.get(url, timeout=settings.sec_request_timeout)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                logger.warning(f"No SEC Company Facts found for CIK {padded_cik} (HTTP 404)")
                return None
            else:
                logger.error(f"SEC API returned HTTP {resp.status_code} for CIK {padded_cik}")
                return None
        except requests.Timeout:
            logger.error(f"Timeout querying SEC facts for CIK {padded_cik}")
            return None
        except Exception as e:
            logger.error(f"Exception fetching SEC facts for CIK {padded_cik}: {e}")
            return None

    @classmethod
    def _extract_single_tag(
        cls, us_gaap: Dict[str, Any], tag: str
    ) -> Dict[int, Tuple[float, str]]:
        """Extracts annual 10-K values for a specific tag concept."""
        if tag not in us_gaap:
            return {}
        concept_units = us_gaap[tag].get("units", {})
        entries = concept_units.get("USD", [])
        if not entries and concept_units:
            first_unit = next(iter(concept_units))
            entries = concept_units[first_unit]

        if not entries:
            return {}

        year_map: Dict[int, Tuple[float, str]] = {}
        for item in entries:
            form = item.get("form", "")
            if form not in ("10-K", "10-K/A"):
                continue

            val = item.get("val")
            filed = item.get("filed", "")
            start_str = item.get("start")
            end_str = item.get("end")

            if val is None or not end_str:
                continue

            try:
                end_date = date.fromisoformat(end_str)
                float_val = float(val)
            except (ValueError, TypeError):
                continue

            # Check if flow concept (annual duration) or instant concept
            if start_str:
                try:
                    start_date = date.fromisoformat(start_str)
                    days = (end_date - start_date).days
                    if not (330 <= days <= 395):
                        continue
                    fy_year = end_date.year
                except ValueError:
                    continue
            else:
                fy_year = end_date.year

            # Keep latest filed record for that fiscal year
            if fy_year not in year_map or filed > year_map[fy_year][1]:
                year_map[fy_year] = (float_val, filed)

        return year_map

    @classmethod
    def _extract_annual_series(
        cls, us_gaap: Dict[str, Any], tag_candidates: List[str]
    ) -> Tuple[Dict[int, Tuple[float, str]], Optional[str]]:
        """
        Extracts annual 10-K values across candidate tags, prioritizing tags
        that provide the most recent and complete historical periods.
        """
        best_map: Dict[int, Tuple[float, str]] = {}
        best_tag: Optional[str] = None
        best_max_year: int = -1

        for tag in tag_candidates:
            candidate_map = cls._extract_single_tag(us_gaap, tag)
            if not candidate_map:
                continue

            candidate_max_year = max(candidate_map.keys())
            # Prioritize candidate with more recent year, or more data points if max_year ties
            if candidate_max_year > best_max_year or (
                candidate_max_year == best_max_year and len(candidate_map) > len(best_map)
            ):
                best_max_year = candidate_max_year
                best_map = candidate_map
                best_tag = tag

        return best_map, best_tag

    def parse_financials(
        self, facts_data: Dict[str, Any]
    ) -> Tuple[List[HistoricalFinancial], List[DataWarning], Optional[str]]:
        """
        Parses SEC Company Facts JSON into normalized HistoricalFinancial models.
        Returns:
            (historical_financials, data_warnings, company_name)
        """
        warnings: List[DataWarning] = []
        if not facts_data or "facts" not in facts_data:
            warnings.append(
                DataWarning(
                    provider="SEC_EDGAR",
                    field="all",
                    message="Empty or invalid SEC Company Facts structure.",
                )
            )
            return [], warnings, None

        company_name = facts_data.get("entityName")
        facts = facts_data.get("facts", {})
        us_gaap = facts.get("us-gaap", {})

        if not us_gaap:
            warnings.append(
                DataWarning(
                    provider="SEC_EDGAR",
                    field="us-gaap",
                    message="No us-gaap taxonomy found in SEC facts payload.",
                )
            )
            return [], warnings, company_name

        # Extract annual series for each core metric using prioritized tag fallbacks
        rev_map, rev_tag = self._extract_annual_series(us_gaap, REVENUE_TAGS)
        op_inc_map, _ = self._extract_annual_series(us_gaap, OPERATING_INCOME_TAGS)
        net_inc_map, _ = self._extract_annual_series(us_gaap, NET_INCOME_TAGS)
        ocf_map, _ = self._extract_annual_series(us_gaap, OPERATING_CASH_FLOW_TAGS)
        capex_map, _ = self._extract_annual_series(us_gaap, CAPEX_TAGS)
        assets_map, _ = self._extract_annual_series(us_gaap, TOTAL_ASSETS_TAGS)
        liab_map, _ = self._extract_annual_series(us_gaap, TOTAL_LIABILITIES_TAGS)
        equity_map, _ = self._extract_annual_series(us_gaap, STOCKHOLDERS_EQUITY_TAGS)
        
        # Debt extraction
        lt_debt_map, _ = self._extract_annual_series(us_gaap, DEBT_LONG_TERM_TAGS)
        st_debt_map, _ = self._extract_annual_series(us_gaap, DEBT_SHORT_TERM_TAGS)

        # Collect all observed fiscal years with data
        all_years = set(rev_map.keys()) | set(net_inc_map.keys()) | set(assets_map.keys())
        if not all_years:
            warnings.append(
                DataWarning(
                    provider="SEC_EDGAR",
                    field="historical_financials",
                    message="No 10-K annual periods could be extracted from SEC facts.",
                )
            )
            return [], warnings, company_name

        # Take the most recent 5 fiscal years
        sorted_years = sorted(list(all_years), reverse=True)[:5]
        sorted_years.reverse()

        financials: List[HistoricalFinancial] = []
        for year in sorted_years:
            rev_val, filing_date = rev_map.get(year, (None, None))
            op_inc_val, _ = op_inc_map.get(year, (None, None))
            net_inc_val, ni_date = net_inc_map.get(year, (None, None))
            ocf_val, _ = ocf_map.get(year, (None, None))
            raw_capex, _ = capex_map.get(year, (None, None))
            assets_val, _ = assets_map.get(year, (None, None))
            liab_val, _ = liab_map.get(year, (None, None))
            equity_val, _ = equity_map.get(year, (None, None))

            # Normalize Capex as positive cash outflow
            capex_val = abs(raw_capex) if raw_capex is not None else None

            # Calculate deterministic Free Cash Flow if both OCF & Capex are present
            fcf_val = None
            if ocf_val is not None and capex_val is not None:
                fcf_val = ocf_val - capex_val

            # Compute Total Debt
            lt_debt, _ = lt_debt_map.get(year, (None, None))
            st_debt, _ = st_debt_map.get(year, (None, None))
            total_debt = None
            if lt_debt is not None or st_debt is not None:
                total_debt = (lt_debt or 0.0) + (st_debt or 0.0)

            # Date fallback
            effective_date = filing_date or ni_date

            hf = HistoricalFinancial(
                fiscal_year=year,
                period="FY",
                filing_date=effective_date,
                form="10-K",
                revenue=rev_val,
                operating_income=op_inc_val,
                net_income=net_inc_val,
                operating_cash_flow=ocf_val,
                capex=capex_val,
                free_cash_flow=fcf_val,
                total_assets=assets_val,
                total_liabilities=liab_val,
                total_debt=total_debt,
                stockholders_equity=equity_val,
                source="SEC_EDGAR",
                currency="USD",
            )
            financials.append(hf)

        # Check for sector-specific absence (e.g. Banks lacking standard Capex)
        has_capex = any(f.capex is not None for f in financials)
        if not has_capex:
            warnings.append(
                DataWarning(
                    provider="SEC_EDGAR",
                    field="capex",
                    message="Capex not reported in 10-K (common for financial institutions). Free cash flow not calculated.",
                )
            )

        return financials, warnings, company_name
