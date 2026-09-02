# AI Financial Research Analyst

A modular, production-quality financial intelligence platform combining multi-source SEC EDGAR/market data ingestion, deterministic quantitative valuation reasoning, and structured AI research generation.

---

## 1. System Architecture

```
                                  [ Stock Ticker (e.g. AAPL, MSFT, JPM) ]
                                                     │
                             ┌───────────────────────┼───────────────────────┐
                             ▼                       ▼                       ▼
                  ┌──────────────────────┐┌──────────────────────┐┌──────────────────────┐
                  │      SEC EDGAR       ││       yfinance       ││     News Sources     │
                  │   (Company Facts)    ││   (Quotes & Stats)   ││  (Yahoo / Finnhub)  │
                  └──────────┬───────────┘└──────────┬───────────┘└──────────┬───────────┘
                             │                       │                       │
                  - CIK Resolution        - Share Price & Mkt Cap - Top 5 Headlines
                  - Tag Fallback Matrix   - Beta & Multiples      - Source & Timestamp
                  - 5-Year 10-K Flow/Inst - Sanitize NaNs/Inf     - Snippets / URLs
                             │                       │                       │
                             └───────────────────────┼───────────────────────┘
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │       Data Orchestrator       │
                                     │      (Milestone 1 Pipeline)   │
                                     └───────────────┬───────────────┘
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │          CompanyData          │
                                     │    (Normalized Pydantic)      │
                                     └───────────────┬───────────────┘
                                                     │
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │   Financial Analysis Engine   │
                                     │  - Growth (YoY, 3Y CAGR)      │
                                     │  - Margins & Returns (ROE)    │
                                     │  - Leverage (D/E, Coverage)   │
                                     │  - Cash Flow (FCF, Conv.)     │
                                     │  - Multiples (P/S, P/FCF)     │
                                     │  - DCF & WACC Valuation       │
                                     │  - 2D Sensitivity Analysis    │
                                     │  - Financial Health Synthesis │
                                     └───────────────┬───────────────┘
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │       FinancialAnalysis       │
                                     │   (Deterministic Ground Truth)│
                                     └───────────────┬───────────────┘
                                                     │
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │    Research Context Builder   │
                                     │  - Strict 9-Section Briefing  │
                                     │  - Source Provenance Extractor│
                                     └───────────────┬───────────────┘
                                                     │
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │   OpenAI Structured Outputs   │
                                     │      (gpt-4o-mini / gpt-4o)   │
                                     │   - 11 Grounding Rules        │
                                     │   - Zero Financial Math       │
                                     └───────────────┬───────────────┘
                                                     │
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │    ResearchReport (Pydantic)  │
                                     │  - Executive Summary & Thesis │
                                     │  - Strengths, Risks, Catalysts│
                                     │  - Grounded DCF Interpretation│
                                     │  - Programmatic Guardrails    │
                                     └───────────────┬───────────────┘
                                                     │
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │       FastAPI REST API        │
                                     │  - GET  /api/health           │
                                     │  - POST /api/analyze          │
                                     │  - POST /api/research         │
                                     │  - Swagger Docs (/docs)       │
                                     └───────────────────────────────┘
```

---

## 2. Milestone 5: FastAPI Backend API Layer

The API layer is implemented as a thin, asynchronous orchestration service using FastAPI. It exposes both the deterministic financial engine and the grounded AI research layer to web clients.

### A. Endpoint Specifications & Contracts

#### 1. `GET /api/health`
Lightweight health check for liveness probes. Does **not** require external API calls or credentials.
```json
// Response: 200 OK
{
  "status": "ok",
  "service": "ai-financial-research-analyst"
}
```

#### 2. `POST /api/analyze`
Executes multi-source data ingestion and deterministic financial calculations.
- **Independence**: Fully operational **without** `OPENAI_API_KEY`.
- **Payload**:
  ```json
  { "ticker": "AAPL" }
  ```
- **Response (`AnalyzeResponse`)**: Extends `FinancialAnalysis` with company description and website. Returns full growth metrics, margin analysis, leverage ratios, cash flow conversion, market valuation multiples, financial health ratings, and model-implied DCF valuation (or `status: not_applicable` for banks like JPM).

#### 3. `POST /api/research`
Coordinates ingestion, deterministic analysis, and grounded LLM research synthesis.
- **Payload**:
  ```json
  { "ticker": "AAPL" }
  ```
- **Response (`ResearchReport`)**: Institutional investment research memo including executive summary, investment thesis, anchored quantitative snapshots, risk factors, catalysts, grounded DCF interpretation, and verified source citations.

### B. Standardized Error Handling
All errors return consistent, sanitized JSON payloads:
```json
{
  "error": {
    "code": "OPENAI_API_KEY_MISSING",
    "message": "AI research synthesis is unavailable because OPENAI_API_KEY is not configured."
  }
}
```
- **`400 Bad Request` (`INVALID_REQUEST`)**: Malformed payload, empty ticker, or invalid ticker characters.
- **`404 Not Found` (`TICKER_NOT_FOUND`)**: Upstream data providers have no record or filings for the requested symbol.
- **`502 Bad Gateway` (`UPSTREAM_DATA_ERROR` / `OPENAI_API_ERROR`)**: Upstream network failure to SEC EDGAR, market quotes, or OpenAI servers.
- **`503 Service Unavailable` (`OPENAI_API_KEY_MISSING` / `OPENAI_RATE_LIMIT`)**: Missing credentials or OpenAI quota exhaustion.
- **`504 Gateway Timeout` (`OPENAI_TIMEOUT`)**: Upstream LLM provider request timeout.
- **`500 Internal Server Error` (`INTERNAL_SERVER_ERROR`)**: Unexpected exceptions. Stack traces and internal secrets are logged server-side and never leaked.

### C. CORS Configuration
Configured via `Settings.cors_allowed_origins` in `backend/app/config.py` to allow frontend clients:
- Default development origins: `http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`.
- Strict preflight handling for `OPTIONS`, `GET`, `POST`.

---

## 3. Milestone 4: Grounded LLM Research Layer

> **Critical Design Principle:**
> The deterministic financial engine remains the **single source of truth** for all numerical analysis.
> The LLM functions exclusively as a **qualitative research synthesis layer** and is strictly prohibited from calculating financial numbers, inventing metrics, or adjusting valuation outputs.

### A. Grounding Contract & Programmatic Guardrails
The LLM integration is bound by an explicit 11-rule prompt contract and deterministic programmatic guardrails:
1. **Zero Invented Numbers**: Never invent financial metrics, prices, ratios, shares, or cash flows.
2. **Zero Financial Calculations**: The LLM is a qualitative synthesis layer, not a calculator.
3. **Preserve Deterministic Values**: Programmatic guardrails anchor quantitative snapshot fields (`revenue_growth_yoy_pct`, `operating_margin_pct`, `net_margin_pct`, `free_cash_flow`), valuation multiples (`pe_ratio`, `price_to_sales`, `ev_to_ebitda`, `current_share_price`), and DCF parameters (`model_wacc_pct`, `model_terminal_growth_pct`, `model_implied_share_price`, `model_upside_downside_pct`). Conflicting numbers generated by the LLM are programmatically aligned with the deterministic engine ground truth.
4. **Explicit Unavailability (P/B & Missing Fields)**: If a metric is not present, it is explicitly presented as unavailable. For example, Price-to-Book (P/B) is not generated by the current deterministic engine and is explicitly set to `None` / `Unavailable` rather than estimated.
5. **Zero Fabricated News / Provenance**: The final report citations are strictly populated from verified application data (`SEC_EDGAR`, `yfinance`, news articles). Any hallucinated citations or fake URLs from the LLM are discarded. Where a URL is unavailable (e.g. missing CIK), it remains `None` rather than fabricating domain links.
6. **Information Classification**: Clearly distinguish between observed audited data, market quotes, model assumptions, calculated values, and qualitative commentary.
7. **Model-Implied Valuation**: DCF output is an intrinsic derivation under explicit assumptions, not an absolute market forecast.
8. **No Guaranteed Returns**: Never present model-implied upside/downside as a promised or guaranteed return.
9. **Sensitivity Discussion**: Always evaluate the 2D sensitivity grid and discuss valuation dispersion across discount rate and growth scenarios.
10. **Financial Institution Gate**: If DCF status is `not_applicable` (e.g. commercial banks like JPM), all numeric DCF fields are strictly nullified and qualitative valuation signals are constrained to P/E and ROE.
11. **Institutional Research Tone**: Write with balanced, disciplined sell-side/buy-side research standards; never issue unsupported binary buy/sell commands.

### B. Output Schema (`ResearchReport`)
- **`executive_summary`**: High-level executive briefing for investment committees.
- **`investment_thesis`**: Fundamental thesis on competitive positioning and cash generation.
- **`financial_snapshot`**: Structured summary, key performance bullets, and anchored deterministic metrics (`revenue_growth_yoy_pct`, `operating_margin_pct`, `net_margin_pct`, `free_cash_flow`).
- **`valuation_assessment`**: Trading multiples evaluation relative to peers and history with anchored multiples (`pe_ratio`, `price_to_sales`, `ev_to_ebitda`, `current_share_price`, `price_to_book`).
- **`strengths`, `risks`, `catalysts`, `concerns`**: Granular fundamental drivers.
- **`financial_health_assessment`**: Solvent balance sheet and liquidity commentary.
- **`dcf_interpretation`**: Grounded explanation of WACC, terminal growth, sensitivity dispersion, and anchored DCF metrics (`model_wacc_pct`, `model_terminal_growth_pct`, `model_implied_share_price`, `model_upside_downside_pct`).
- **`news_and_market_context`**: Verifiable news events and operational context.
- **`confidence`**: Rated confidence level (`High`, `Medium`, `Cautious`) with rationale.
- **`limitations`**: Explicit methodological limitations, model caveats, and deterministic anchoring audit disclosures.
- **`sources`**: Authoritative list of verified SEC filings, market quotes, news articles, and models.

### C. Environment Configuration
The research layer is configured via environment variables or `.env`:
```ini
OPENAI_API_KEY=sk-...           # Required for live LLM synthesis
OPENAI_MODEL=gpt-4o-mini        # Default model (configurable to gpt-4o)
OPENAI_TEMPERATURE=0.2          # Low temperature for analytical consistency
OPENAI_TIMEOUT=45               # Request timeout in seconds
```
*If `OPENAI_API_KEY` is not provided, the application gracefully reports the missing key without crashing, preserving full access to deterministic data ingestion, financial ratios, and DCF calculations.*

---

## 3. Milestone 3: DCF Valuation & WACC Methodology

The DCF valuation engine is implemented as deterministic Python logic. It produces a **model-implied intrinsic value** based on grounded assumptions.

### A. Data vs. Assumptions vs. Calculated Values

| Component | Classification | Source / Value |
| :--- | :--- | :--- |
| **Beta (\(\beta\))** | Observed Data | Historical market sensitivity from yfinance |
| **Share Price & Shares Out** | Observed Data | Real-time / delayed quote from yfinance |
| **Total Debt & Cash** | Observed Data | Latest audited 10-K balance sheet & market quote |
| **Historical FCF Series** | Observed Data | Audited Operating Cash Flow - Capex (10-K) |
| **Risk-Free Rate (\(R_f\))** | Observed / Assumption | 10-Year US Treasury yield (`^TNX`), fallback = 4.20% |
| **Equity Risk Premium (\(ERP\))** | Model Assumption | 5.00% (long-term historical equity risk premium) |
| **Terminal Growth Rate (\(g\))** | Model Assumption | 2.50% (long-term sustainable GDP growth rate) |
| **Corporate Tax Rate (\(T\))** | Model Assumption | 21.0% (US statutory federal corporate tax rate) |
| **Cost of Equity (\(K_e\))** | Calculated Value | CAPM: \(K_e = R_f + \beta \times ERP\) |
| **Cost of Debt (\(K_d\))** | Calculated / Benchmark | Pre-tax: \(R_f + 1.50\%\); After-tax: \(K_d \times (1 - T)\) |
| **Capital Weights** | Calculated Value | \(W_e = E / (D + E)\); \(W_d = D / (D + E)\) |
| **WACC** | Calculated Value | \(W_e \times K_e + W_d \times K_{d, after-tax}\) |
| **5-Year FCF Projections** | Calculated Value | Bounded historical growth: \(\max(2\%, \min(\text{CAGR}, 15\%))\) |
| **Terminal Value (\(TV\))** | Calculated Value | Gordon Growth: \((FCF_5 \times (1 + g)) / (WACC - g)\) |
| **Enterprise Value (\(EV\))** | Calculated Value | \(\sum_{t=1}^5 \frac{FCF_t}{(1 + WACC)^t} + \frac{TV}{(1 + WACC)^5}\) |
| **Equity Value** | Calculated Value | \(Enterprise\,Value - (Total\,Debt - Cash)\) |
| **Implied Share Price** | Calculated Value | \(Equity\,Value / Shares\,Outstanding\) |
| **Model Upside/Downside** | Calculated Value | \(((Implied\,Price - Current\,Price) / Current\,Price) \times 100\%\) |

---

## 5. Local Execution & CLI Commands

### Start FastAPI Backend Server (Uvicorn)
```powershell
# Windows PowerShell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Access interactive documentation:
# Swagger UI: http://localhost:8000/docs
# ReDoc:      http://localhost:8000/redoc
```

### Run Grounded LLM Research Memo via CLI
```powershell
$env:PYTHONPATH="backend"

# Run end-to-end research synthesis (or graceful missing-key prompt)
.\.venv\Scripts\python.exe -m app.research AAPL

# Output complete structured JSON report:
.\.venv\Scripts\python.exe -m app.research NVDA --json
```

### Run Full Financial & DCF Analysis (Zero LLM Required)
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m app.financial.engine AAPL

# Test company with macro overrides:
.\.venv\Scripts\python.exe -m app.financial.engine MSFT --rf 0.045 --g 0.025
```

### Run Automated Test Suite (78 Tests)
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest.exe backend/tests -v
```

---

## 6. Project Roadmap

- [x] **Milestone 0**: Environment inspection, architecture blueprint, and schema design.
- [x] **Milestone 1**: Data ingestion pipeline (SEC EDGAR, yfinance, News) & normalization.
- [x] **Milestone 2**: Deterministic financial analysis engine (growth, margins, leverage, cash flow, health).
- [x] **Milestone 3**: Valuation engine (DCF, WACC, Terminal Value, 2D sensitivity analysis, sector gating).
- [x] **Milestone 4**: Grounded LLM research layer (OpenAI structured outputs, 11 grounding rules, memo).
- [x] **Milestone 5**: FastAPI backend endpoints (`/api/analyze`, `/api/health`, `/api/research`).
- [ ] **Milestone 6**: React + TypeScript + Tailwind dashboard with Recharts.
- [ ] **Milestone 7**: PostgreSQL persistence and caching.
- [ ] **Milestone 8**: Error handling, resilience, and edge case hardening.
- [ ] **Milestone 9**: Docker containerization and final deployment documentation.