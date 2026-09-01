# AI Financial Research Analyst

A modular, production-quality financial intelligence platform combining multi-source SEC EDGAR/market data ingestion, deterministic financial and quantitative reasoning, and structured AI research generation.

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
                                     │      (Milestone 2 Engine)     │
                                     │  - Growth (YoY, 3Y CAGR)      │
                                     │  - Margins & Returns (ROE)    │
                                     │  - Leverage (D/E, Coverage)   │
                                     │  - Cash Flow (FCF, Conv.)     │
                                     │  - Multiples (P/S, P/FCF)     │
                                     │  - Financial Health Synthesis │
                                     └───────────────┬───────────────┘
                                                     ▼
                                     ┌───────────────────────────────┐
                                     │       FinancialAnalysis       │
                                     │    (Structured Results)       │
                                     └───────────────────────────────┘
```

---

## 2. Milestone 2: Deterministic Financial Analysis Engine

### A. Philosophy: Pure Math, Zero LLM
Calculations are executed 100% deterministically in Python. Large Language Models (LLMs) are **never** permitted to calculate financial ratios, compute growth rates, or invent numbers. The LLM's role (in Milestone 4) is strictly qualitative interpretation of grounded, pre-calculated facts.

### B. Missing Data & Sector-Aware Handling
- **No Synthetic Numbers**: When financial line items are absent, metrics return `None` and attach an explicit explanation. Missing values are never silently replaced with zero.
- **Negative & Zero Denominator Protection**: If a base-year metric (such as Net Income or FCF) is negative or zero, percentage growth is mathematically undefined/misleading. The engine sets the growth value to `None` with an explanatory note.
- **Financial Institutions (e.g., JPM)**: Commercial banks do not report conventional Capex or standard industrial Free Cash Flow. The engine identifies financial sector entities, marks FCF as `N/A`, and evaluates banking health using Net Income and Return on Equity (ROE) without penalizing cash flow as "Weak".

---

## 3. Financial Methodology & Formula Reference

| Category | Metric | Formula / Methodology | Required Inputs |
| :--- | :--- | :--- | :--- |
| **Growth** | **Revenue Growth (YoY)** | \((Revenue_t - Revenue_{t-1}) / Revenue_{t-1}\) | Consecutive annual revenues (\(Rev_{t-1} > 0\)) |
| **Growth** | **Revenue 3-Yr CAGR** | \((Revenue_t / Revenue_{t-3})^{1/3} - 1\) | Positive revenues across 3-year span |
| **Growth** | **Net Income Growth (YoY)** | \((NetIncome_t - NetIncome_{t-1}) / NetIncome_{t-1}\) | Consecutive annual net incomes (\(NI_{t-1} > 0\)) |
| **Growth** | **Free Cash Flow Growth** | \((FCF_t - FCF_{t-1}) / FCF_{t-1}\) | Consecutive annual FCFs (\(FCF_{t-1} > 0\)) |
| **Profitability**| **Operating Margin** | \(Operating\,Income / Revenue\) | Operating Income, Revenue (\(Rev > 0\)) |
| **Profitability**| **Net Margin** | \(Net\,Income / Revenue\) | Net Income, Revenue (\(Rev > 0\)) |
| **Profitability**| **Return on Equity (ROE)** | \(Net\,Income / ((Equity_t + Equity_{t-1}) / 2)\) | Net Income, 2-period Shareholders' Equity (\(Avg > 0\)) |
| **Profitability**| **ROIC** | \(Operating\,Income / ((IC_t + IC_{t-1}) / 2)\) | Operating Income, Invested Capital (Debt + Equity) |
| **Leverage** | **Debt-to-Equity** | \(Total\,Debt / Shareholders'\,Equity\) | Total Debt, Equity (\(Equity > 0\)) |
| **Cash Flow** | **Free Cash Flow (FCF)** | \(Operating\,Cash\,Flow - Capital\,Expenditure\) | OCF, Capex |
| **Cash Flow** | **FCF Margin** | \(Free\,Cash\,Flow / Revenue\) | FCF, Revenue (\(Rev > 0\)) |
| **Cash Flow** | **FCF Conversion** | \(Free\,Cash\,Flow / Net\,Income\) | FCF, Net Income (\(NI > 0\)) |
| **Valuation** | **Price-to-Sales (P/S)** | \(Market\,Capitalization / Latest\,Annual\,Revenue\) | Market Cap, Latest Revenue (\(Rev > 0\)) |
| **Valuation** | **Price-to-FCF (P/FCF)** | \(Market\,Capitalization / Latest\,Annual\,FCF\) | Market Cap, Latest FCF (\(FCF > 0\)) |
| **Valuation** | **P/E & EV/EBITDA** | Provider-reported market multiples from yfinance | Market trading data |

---

## 4. Financial Health Synthesis

Rather than assigning an arbitrary black-box numerical score (e.g. 78/100), the engine evaluates corporate health across four transparent pillars:
1. **Growth**: Top-line expansion rate and consistency.
2. **Profitability**: Operating margins and returns on equity/capital.
3. **Leverage**: Balance sheet solvency and debt-to-equity profile.
4. **Cash Flow**: Cash conversion efficiency and FCF generation (neutralized for banks).

---

## 5. Local Execution & CLI Commands

### Run Financial Analysis on any Ticker
```powershell
# Windows PowerShell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe -m app.financial.engine AAPL

# Output complete JSON payload
.\.venv\Scripts\python.exe -m app.financial.engine MSFT --json
```

### Run Automated Test Suite
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest.exe backend/tests -v
```

---

## 6. Project Roadmap

- [x] **Milestone 0**: Environment inspection, architecture blueprint, and schema design.
- [x] **Milestone 1**: Data ingestion pipeline (SEC EDGAR, yfinance, News) & normalization.
- [x] **Milestone 2**: Deterministic financial analysis engine (growth, margins, leverage, cash flow, health).
- [ ] **Milestone 3**: Valuation engine (DCF, WACC, Terminal Value, 2D sensitivity analysis).
- [ ] **Milestone 4**: LLM research layer (grounded investment memo & structured synthesis).
- [ ] **Milestone 5**: FastAPI backend endpoints (`/api/analyze`, `/api/health`).
- [ ] **Milestone 6**: React + TypeScript + Tailwind dashboard with Recharts.
- [ ] **Milestone 7**: PostgreSQL persistence and caching.
- [ ] **Milestone 8**: Error handling, resilience, and edge case hardening.
- [ ] **Milestone 9**: Docker containerization and final deployment documentation.