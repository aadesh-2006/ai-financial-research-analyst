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
                                     └───────────────────────────────┘
```

---

## 2. Milestone 4: Grounded LLM Research Layer

> **Critical Design Principle:**
> The deterministic financial engine remains the **single source of truth** for all numerical analysis.
> The LLM functions exclusively as a **qualitative research synthesis layer** and is strictly prohibited from calculating financial numbers, inventing metrics, or adjusting valuation outputs.

### A. Grounding Contract & Safety Safeguards
The LLM integration is bound by an explicit 11-rule prompt contract and programmatic post-processing guardrails:
1. **Zero Invented Numbers**: Never invent financial metrics, prices, ratios, shares, or cash flows.
2. **Zero Financial Calculations**: The LLM is a qualitative synthesis layer, not a calculator.
3. **Preserve Deterministic Values**: Never alter or recompute supplied metrics or DCF values.
4. **Explicit Unavailability**: If a field is missing or N/A, explicitly state it is unavailable. Never guess.
5. **Zero Fabricated News / Facts**: All qualitative claims must trace to supplied news headlines or filings.
6. **Information Classification**: Clearly distinguish between observed audited data, market quotes, model assumptions, calculated values, and qualitative commentary.
7. **Model-Implied Valuation**: DCF output is an intrinsic derivation under explicit assumptions, not an absolute market forecast.
8. **No Guaranteed Returns**: Never present model-implied upside/downside as a promised or guaranteed return.
9. **Sensitivity Discussion**: Always evaluate the 2D sensitivity grid and discuss valuation dispersion across discount rate and growth scenarios.
10. **Financial Institution Gate**: If DCF status is `not_applicable` (e.g. commercial banks like JPM), never manufacture a DCF value; explain the sector gate and evaluate via P/E, P/B, and ROE.
11. **Institutional Research Tone**: Write with balanced, disciplined sell-side/buy-side research standards; never issue unsupported binary buy/sell commands.

### B. Output Schema (`ResearchReport`)
- **`executive_summary`**: High-level executive briefing for investment committees.
- **`investment_thesis`**: Fundamental thesis on competitive positioning and cash generation.
- **`financial_snapshot`**: Structured summary and key performance bullets.
- **`valuation_assessment`**: Trading multiples evaluation relative to peers and history.
- **`strengths`, `risks`, `catalysts`, `concerns`**: Granular fundamental drivers.
- **`financial_health_assessment`**: Solvent balance sheet and liquidity commentary.
- **`dcf_interpretation`**: Grounded explanation of WACC, terminal growth, and sensitivity matrix.
- **`news_and_market_context`**: Verifiable news events and operational context.
- **`confidence`**: Rated confidence level (`High`, `Medium`, `Cautious`) with rationale.
- **`limitations`**: Explicit methodological limitations and model caveats.
- **`sources`**: Verifiable list of SEC filings, market quotes, news articles, and models.

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

## 4. Local Execution & CLI Commands

### Run Grounded LLM Research Memo on any Ticker
```powershell
# Windows PowerShell
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

### Run Automated Test Suite (56 Tests)
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest.exe backend/tests -v
```

---

## 5. Project Roadmap

- [x] **Milestone 0**: Environment inspection, architecture blueprint, and schema design.
- [x] **Milestone 1**: Data ingestion pipeline (SEC EDGAR, yfinance, News) & normalization.
- [x] **Milestone 2**: Deterministic financial analysis engine (growth, margins, leverage, cash flow, health).
- [x] **Milestone 3**: Valuation engine (DCF, WACC, Terminal Value, 2D sensitivity analysis, sector gating).
- [x] **Milestone 4**: Grounded LLM research layer (OpenAI structured outputs, 11 grounding rules, memo).
- [ ] **Milestone 5**: FastAPI backend endpoints (`/api/analyze`, `/api/health`).
- [ ] **Milestone 6**: React + TypeScript + Tailwind dashboard with Recharts.
- [ ] **Milestone 7**: PostgreSQL persistence and caching.
- [ ] **Milestone 8**: Error handling, resilience, and edge case hardening.
- [ ] **Milestone 9**: Docker containerization and final deployment documentation.