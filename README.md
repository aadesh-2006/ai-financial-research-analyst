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
                                     │    (Structured Results)       │
                                     └───────────────────────────────┘
```

---

## 2. Milestone 3: DCF Valuation & WACC Methodology

The DCF valuation engine is implemented as deterministic Python logic. It produces a **model-implied intrinsic value** based on grounded assumptions. It does **not** claim to provide an absolute market forecast or investment advice.

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

### B. Sector-Aware DCF Gating (Commercial Banks & Financials)
- **Financial Institutions (e.g., JPM)**: Commercial banks do not report conventional Capex or standard industrial Free Cash Flow. Bank balance sheets intermediate capital via interest spreads, deposits, and statutory capital ratios.
- **Defensive Handling**: The engine automatically detects financial sector SIC codes and company profiles, marking the DCF status as `not_applicable` with warning code `SectorNotSupportedForDCF`.
- **Alternative Guidance**: The engine recommends evaluating financial institutions through Price-to-Earnings (P/E), Price-to-Book (P/B), and Return on Equity (ROE) benchmarking rather than forcing an invalid DCF.

---

### C. 2D Sensitivity Matrix
To understand how intrinsic valuation fluctuates across macroeconomic scenarios, the engine computes a 2D matrix:
- **WACC Scenarios**: 6.0%, 7.0%, 8.0%, 9.0%, 10.0%, 11.0%, 12.0%
- **Terminal Growth Scenarios**: 1.0%, 1.5%, 2.0%, 2.5%, 3.0%, 3.5%
- **Mathematical Guardrail**: If \(g \ge WACC\), Gordon Growth is mathematically undefined. The cell returns `None` without crashing.

---

## 3. Financial Methodology & Formula Reference

| Category | Metric | Formula / Methodology | Required Inputs |
| :--- | :--- | :--- | :--- |
| **Valuation** | **Cost of Equity** | \(R_f + \beta \times ERP\) | \(R_f\), \(\beta\), \(ERP\) |
| **Valuation** | **WACC** | \(W_e \times K_e + W_d \times K_{d, after-tax}\) | \(K_e\), \(K_d\), Market Equity, Debt |
| **Valuation** | **Terminal Value** | \((FCF_5 \times (1 + g)) / (WACC - g)\) | Year 5 FCF, WACC, \(g < WACC\) |
| **Valuation** | **Enterprise Value** | \(PV(Explicit\,FCF) + PV(Terminal\,Value)\) | 5-Yr Projections, TV, WACC |
| **Valuation** | **Equity Value** | \(Enterprise\,Value - (Total\,Debt - Cash)\) | EV, Total Debt, Cash |
| **Valuation** | **Implied Price** | \(Equity\,Value / Shares\,Outstanding\) | Equity Value, Shares Outstanding |
| **Growth** | **Revenue YoY** | \((Revenue_t - Revenue_{t-1}) / Revenue_{t-1}\) | Consecutive annual revenues |
| **Growth** | **3-Yr Rev CAGR** | \((Revenue_t / Revenue_{t-3})^{1/3} - 1\) | Revenues across 3-year span |
| **Profitability**| **Operating Margin**| \(Operating\,Income / Revenue\) | Operating Income, Revenue |
| **Profitability**| **Net Margin** | \(Net\,Income / Revenue\) | Net Income, Revenue |
| **Profitability**| **ROE** | \(Net\,Income / ((Equity_t + Equity_{t-1}) / 2)\) | Net Income, 2-period Equity |
| **Leverage** | **Debt-to-Equity** | \(Total\,Debt / Stockholders'\,Equity\) | Total Debt, Equity |
| **Cash Flow** | **Free Cash Flow** | \(Operating\,Cash\,Flow - Capital\,Expenditure\) | OCF, Capex |
| **Cash Flow** | **FCF Conversion** | \(Free\,Cash\,Flow / Net\,Income\) | FCF, Net Income |

---

## 4. Local Execution & CLI Commands

### Run Full Financial & DCF Analysis on any Ticker
```powershell
# Windows PowerShell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m app.financial.engine AAPL

# Test company with overrides:
.\.venv\Scripts\python.exe -m app.financial.engine MSFT --rf 0.045 --g 0.025

# Output complete JSON payload
.\.venv\Scripts\python.exe -m app.financial.engine NVDA --json
```

### Run Automated Test Suite (41 Tests)
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
- [ ] **Milestone 4**: LLM research layer (grounded investment memo & structured synthesis).
- [ ] **Milestone 5**: FastAPI backend endpoints (`/api/analyze`, `/api/health`).
- [ ] **Milestone 6**: React + TypeScript + Tailwind dashboard with Recharts.
- [ ] **Milestone 7**: PostgreSQL persistence and caching.
- [ ] **Milestone 8**: Error handling, resilience, and edge case hardening.
- [ ] **Milestone 9**: Docker containerization and final deployment documentation.