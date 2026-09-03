"""Comprehensive test suite for the data ingestion and normalization pipeline."""
import math
from unittest.mock import MagicMock, patch
import pytest

from app.data.news_client import NewsClient
from app.data.orchestrator import DataOrchestrator
from app.data.sec_edgar import SECEdgarClient
from app.data.yfinance_client import YFinanceClient
from app.schemas.financial import (
    CompanyData,
    CompanyProfile,
    HistoricalFinancial,
    MarketData,
    NewsArticle,
)


# ==============================================================================
# 1. TICKER & SCHEMA NORMALIZATION TESTS
# ==============================================================================

def test_ticker_normalization():
    """Validates that tickers are stripped of whitespace and capitalized."""
    cd = CompanyData(
        ticker="  msft  ",
        company_profile=CompanyProfile(ticker="MSFT", name="Microsoft"),
        market_data=MarketData(),
    )
    assert cd.ticker == "MSFT"


def test_company_data_schema_roundtrip():
    """Validates that CompanyData serializes to JSON and deserializes identically."""
    profile = CompanyProfile(ticker="NVDA", name="NVIDIA Corporation", sector="Technology")
    market = MarketData(current_price=125.5, market_cap=3000000000000.0, beta=1.65)
    hist = HistoricalFinancial(
        fiscal_year=2024,
        revenue=60922000000.0,
        net_income=29760000000.0,
        operating_cash_flow=28090000000.0,
        capex=1500000000.0,
        free_cash_flow=26590000000.0,
    )
    news = NewsArticle(headline="NVIDIA Announces New Architecture", source="Reuters")

    cd = CompanyData(
        ticker="NVDA",
        company_profile=profile,
        historical_financials=[hist],
        market_data=market,
        news=[news],
    )

    json_str = cd.model_dump_json()
    reconstructed = CompanyData.model_validate_json(json_str)

    assert reconstructed.ticker == "NVDA"
    assert reconstructed.historical_financials[0].free_cash_flow == 26590000000.0
    assert reconstructed.market_data.beta == 1.65
    assert len(reconstructed.news) == 1


# ==============================================================================
# 2. SEC EDGAR CLIENT & PARSING TESTS
# ==============================================================================

def test_sec_cik_resolution_preseeded():
    """Verifies that pre-seeded tickers resolve without network calls."""
    client = SECEdgarClient()
    assert client.resolve_cik("AAPL") == "0000320193"
    assert client.resolve_cik("msft") == "0000789019"
    assert client.resolve_cik("JPM") == "0000019617"


def test_sec_parsing_standard_corporate():
    """Verifies parsing of standard corporate 10-K facts into HistoricalFinancial."""
    client = SECEdgarClient()
    mock_facts = {
        "entityName": "Mock Corp",
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 1000000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-15",
                            }
                        ]
                    }
                },
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 300000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-15",
                            }
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 220000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-15",
                            }
                        ]
                    }
                },
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 350000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-15",
                            }
                        ]
                    }
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 50000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-15",
                            }
                        ]
                    }
                },
                "Assets": {
                    "units": {
                        "USD": [
                            {
                                "end": "2023-12-31",
                                "val": 2000000.0,
                                "fy": 2023,
                                "form": "10-K",
                                "filed": "2024-02-15",
                            }
                        ]
                    }
                },
            }
        },
    }

    financials, warnings, name = client.parse_financials(mock_facts)
    assert name == "Mock Corp"
    assert len(financials) == 1
    f = financials[0]
    assert f.fiscal_year == 2023
    assert f.revenue == 1000000.0
    assert f.operating_income == 300000.0
    assert f.net_income == 220000.0
    assert f.operating_cash_flow == 350000.0
    assert f.capex == 50000.0
    # Deterministic FCF calculation check
    assert f.free_cash_flow == 300000.0
    assert f.total_assets == 2000000.0


def test_sec_tag_fallback_logic():
    """Verifies that when primary tags are absent, fallback concepts are utilized."""
    client = SECEdgarClient()
    mock_facts = {
        "entityName": "Fallback Inc",
        "facts": {
            "us-gaap": {
                # Revenue primary tag missing, SalesRevenueNet used instead
                "SalesRevenueNet": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 500000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-01-10",
                            }
                        ]
                    }
                },
                "ProfitLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 40000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-01-10",
                            }
                        ]
                    }
                },
            }
        },
    }

    financials, warnings, name = client.parse_financials(mock_facts)
    assert len(financials) == 1
    assert financials[0].revenue == 500000.0
    assert financials[0].net_income == 40000.0


def test_sec_parsing_financial_institution_missing_capex():
    """Verifies that missing Capex produces None for FCF and a clean warning without throwing."""
    client = SECEdgarClient()
    mock_bank_facts = {
        "entityName": "National Bank",
        "facts": {
            "us-gaap": {
                "InterestAndDividendIncomeOperating": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 80000000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-01",
                            }
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "val": 25000000.0,
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-01",
                            }
                        ]
                    }
                },
                "Assets": {
                    "units": {
                        "USD": [
                            {
                                "end": "2023-12-31",
                                "val": 500000000.0,
                                "fy": 2023,
                                "form": "10-K",
                                "filed": "2024-02-01",
                            }
                        ]
                    }
                },
            }
        },
    }

    financials, warnings, name = client.parse_financials(mock_bank_facts)
    assert len(financials) == 1
    assert financials[0].capex is None
    assert financials[0].free_cash_flow is None
    assert any("Capex not reported" in w.message for w in warnings)


# ==============================================================================
# 3. YFINANCE CLIENT NORMALIZATION TESTS
# ==============================================================================

def test_yfinance_normalization():
    """Verifies that raw yfinance info is mapped to typed MarketData."""
    client = YFinanceClient()
    mock_info = {
        "currentPrice": 150.25,
        "previousClose": 148.50,
        "fiftyTwoWeekHigh": 160.00,
        "fiftyTwoWeekLow": 120.00,
        "marketCap": 2500000000000,
        "sharesOutstanding": 16000000000,
        "beta": 1.15,
        "trailingPE": 28.5,
        "forwardPE": 24.2,
        "enterpriseToEbitda": 18.4,
        "enterpriseValue": 2550000000000,
        "longName": "Test Tech Inc",
        "sector": "Technology",
        "industry": "Software",
        "currency": "USD",
    }

    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.info = mock_info
        mock_ticker.return_value = mock_instance

        mkt, prof, warns = client.get_market_data("TEST")

        assert mkt is not None
        assert mkt.current_price == 150.25
        assert mkt.beta == 1.15
        assert mkt.pe_ratio == 28.5
        assert prof.name == "Test Tech Inc"
        assert prof.sector == "Technology"


def test_yfinance_nan_and_missing_handling():
    """Verifies that NaN and invalid values are converted safely to None."""
    client = YFinanceClient()
    mock_info = {
        "currentPrice": float("nan"),
        "trailingPE": float("inf"),
        "beta": None,
        "longName": "Loss Making Startup",
        "regularMarketPrice": 10.50,
    }

    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.info = mock_info
        mock_ticker.return_value = mock_instance

        mkt, prof, warns = client.get_market_data("TEST")

        # regularMarketPrice fallback
        assert mkt.current_price == 10.50
        # nan converted to None
        assert mkt.beta is None
        # inf converted to None
        assert mkt.pe_ratio is None


# ==============================================================================
# 4. NEWS CLIENT NORMALIZATION TESTS
# ==============================================================================

def test_news_normalization_nested_and_flat():
    """Verifies parsing of both modern nested and legacy flat news structures."""
    client = NewsClient()
    mock_raw_news = [
        # Modern yfinance structure
        {
            "id": "1",
            "content": {
                "title": "Quarterly Earnings Beat Expectations",
                "pubDate": "2024-02-01T14:30:00Z",
                "canonicalUrl": {"url": "https://finance.yahoo.com/news/article1"},
                "provider": {"displayName": "Bloomberg"},
                "summary": "Revenue exceeded consensus estimates by 5%...",
            },
        },
        # Legacy flat structure
        {
            "title": "New Product Launch Announced",
            "providerPublishTime": 1706800000,
            "link": "https://finance.yahoo.com/news/article2",
            "publisher": "Reuters",
        },
    ]

    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.news = mock_raw_news
        mock_ticker.return_value = mock_instance

        articles, warns = client.get_company_news("TEST")

        assert len(articles) == 2
        assert articles[0].headline == "Quarterly Earnings Beat Expectations"
        assert articles[0].source == "Bloomberg"
        assert articles[0].url == "https://finance.yahoo.com/news/article1"
        assert articles[1].headline == "New Product Launch Announced"
        assert articles[1].source == "Reuters"


# ==============================================================================
# 5. ORCHESTRATOR & RESILIENCY TESTS
# ==============================================================================

def test_orchestrator_partial_failure_news_fails():
    """Verifies pipeline continues smoothly when optional news provider raises an error."""
    mock_sec = MagicMock(spec=SECEdgarClient)
    mock_sec.resolve_cik.return_value = "0000320193"
    mock_sec.get_company_facts.return_value = {"facts": {}}
    mock_sec.parse_financials.return_value = (
        [
            HistoricalFinancial(
                fiscal_year=2023,
                revenue=100.0,
                operating_income=30.0,
                net_income=25.0,
                operating_cash_flow=35.0,
                capex=5.0,
                free_cash_flow=30.0,
            )
        ],
        [],
        "Apple Inc.",
    )

    mock_yf = MagicMock(spec=YFinanceClient)
    mock_yf.get_market_data.return_value = (
        MarketData(current_price=200.0),
        CompanyProfile(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        [],
    )

    mock_news = MagicMock(spec=NewsClient)
    mock_news.get_company_news.side_effect = Exception("News API timeout")

    orchestrator = DataOrchestrator(
        sec_client=mock_sec, yf_client=mock_yf, news_client=mock_news
    )

    data = orchestrator.get_company_data("AAPL")

    assert data.ticker == "AAPL"
    assert len(data.historical_financials) == 1
    assert data.market_data.current_price == 200.0
    assert data.news == []
    assert any("News API timeout" in w.message for w in data.data_warnings)


def test_orchestrator_invalid_ticker():
    """Verifies that a completely invalid ticker raises a descriptive ValueError."""
    mock_sec = MagicMock(spec=SECEdgarClient)
    mock_sec.resolve_cik.return_value = None

    mock_yf = MagicMock(spec=YFinanceClient)
    mock_yf.get_market_data.return_value = (None, None, [])

    mock_news = MagicMock(spec=NewsClient)
    mock_news.get_company_news.return_value = ([], [])

    orchestrator = DataOrchestrator(
        sec_client=mock_sec, yf_client=mock_yf, news_client=mock_news
    )

    with pytest.raises(ValueError, match="Failed to retrieve data for ticker 'INVALID'"):
        orchestrator.get_company_data("INVALID")

# ==============================================================================
# 6. LIVE INTEGRATION TEST (AAPL)
# ==============================================================================

@pytest.mark.integration
def test_live_data_pipeline_aapl():
    """End-to-end integration test against live APIs for Apple Inc."""
    orchestrator = DataOrchestrator()
    data = orchestrator.get_company_data("AAPL")

    assert data.ticker == "AAPL"
    assert "Apple" in data.company_profile.name
    assert data.company_profile.cik == "0000320193"
    assert len(data.historical_financials) >= 3

    # If yfinance rate limit occurred from upstream provider, skip market quote assertion
    if any("Rate limited" in str(w.message) or "Too Many Requests" in str(w.message) for w in data.data_warnings):
        pytest.skip("yfinance rate-limited live market request in test environment")

    assert data.market_data.current_price is not None
    assert data.market_data.current_price > 0

    # Check latest year numbers exist and are reasonable
    latest = data.historical_financials[-1]
    assert latest.fiscal_year >= 2023
    assert latest.revenue is not None and latest.revenue > 100_000_000_000
    assert latest.operating_cash_flow is not None
    assert latest.free_cash_flow is not None
