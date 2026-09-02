import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { App } from "../App";
import * as apiClient from "../api/client";
import { AnalyzeResponse } from "../api/types";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return {
    ...actual,
    checkHealth: vi.fn(),
    analyzeCompany: vi.fn(),
    generateResearch: vi.fn(),
  };
});

describe("App Integration", () => {
  const mockAnalysis: AnalyzeResponse = {
    ticker: "AAPL",
    company_name: "Apple Inc.",
    sector: "Technology",
    industry: "Consumer Electronics",
    currency: "USD",
    description: "Designs mobile communication devices.",
    website: "https://www.apple.com",
    growth: {
      revenue_growth_yoy: 0.08,
      revenue_cagr_3yr: 0.07,
      net_income_growth_yoy: 0.10,
      fcf_growth_yoy: 0.12,
      revenue_growth_series: [],
      net_income_growth_series: [],
      fcf_growth_series: [],
    },
    profitability: {
      gross_margin: 0.45,
      operating_margin: 0.30,
      net_margin: 0.25,
      roe: 1.60,
      roic: 0.42,
    },
    leverage: {
      debt_to_equity: 1.75,
      debt_to_ebitda: 0.85,
      interest_coverage: 25.0,
      total_debt: 105_000_000_000,
      stockholders_equity: 60_000_000_000,
    },
    cash_flow: {
      operating_cash_flow: 115_000_000_000,
      capex: 10_000_000_000,
      free_cash_flow: 105_000_000_000,
      fcf_margin: 0.27,
      fcf_conversion: 1.05,
    },
    valuation: {
      pe_ratio: 32.5,
      forward_pe: 28.0,
      ev_to_ebitda: 24.0,
      price_to_sales: 8.5,
      price_to_fcf: 31.4,
      market_cap: 3_300_000_000_000,
      enterprise_value: 3_340_000_000_000,
      price_to_book: null,
    },
    dcf: {
      ticker: "AAPL",
      status: "calculated",
      wacc: 0.085,
      terminal_growth_rate: 0.025,
      implied_share_price: 210.5,
      current_share_price: 220.0,
      upside_downside_pct: -4.3,
      projections: [],
    },
    historical_trends: [
      {
        fiscal_year: 2024,
        revenue: 390_000_000_000,
        revenue_growth: 0.08,
        operating_income: 120_000_000_000,
        operating_margin: 0.3,
        net_income: 100_000_000_000,
        net_margin: 0.25,
        operating_cash_flow: 115_000_000_000,
        free_cash_flow: 105_000_000_000,
        fcf_margin: 0.27,
      },
    ],
    health: {
      overall: "Strong",
      growth_pillar: "Strong",
      profitability_pillar: "Strong",
      leverage_pillar: "Moderate",
      cash_flow_pillar: "Strong",
      key_observations: ["High free cash flow generation"],
    },
    news: [
      {
        headline: "Apple reveals next-gen chips",
        source: "Bloomberg",
        url: "https://bloomberg.com/apple",
        published_at: "2026-09-01T12:00:00Z",
      },
    ],
    warnings: [],
    analyzed_at: "2026-09-02T18:00:00Z",
  };

  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(apiClient.checkHealth).mockResolvedValue({
      status: "ok",
      service: "ai-financial-research-analyst",
    });
  });

  it("renders initial greeting when no company has been analyzed", async () => {
    render(<App />);
    expect(screen.getByText(/Financial Research Terminal Ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Deterministic Truth/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/FastAPI API Active/i)).toBeInTheDocument();
    });
  });

  it("handles successful ticker analysis and renders company dashboard", async () => {
    vi.mocked(apiClient.analyzeCompany).mockResolvedValue(mockAnalysis);

    render(<App />);

    const input = screen.getByPlaceholderText(/Enter public stock ticker/i);
    fireEvent.change(input, { target: { value: "AAPL" } });
    fireEvent.submit(screen.getByRole("button", { name: /Analyze Company/i }));

    await waitFor(() => {
      expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
      expect(screen.getByText("32.50x")).toBeInTheDocument();
      expect(screen.getByText("$210.50")).toBeInTheDocument();
      expect(screen.getByText(/Apple reveals next-gen chips/i)).toBeInTheDocument();
    });
  });

  it("displays error banner when ticker lookup fails", async () => {
    vi.mocked(apiClient.analyzeCompany).mockRejectedValue(
      new apiClient.ApiClientError(404, "TICKER_NOT_FOUND", "Ticker 'INVALID' not found in SEC EDGAR.")
    );

    render(<App />);

    const input = screen.getByPlaceholderText(/Enter public stock ticker/i);
    fireEvent.change(input, { target: { value: "INVALID" } });
    fireEvent.submit(screen.getByRole("button", { name: /Analyze Company/i }));

    await waitFor(() => {
      expect(screen.getByText(/TICKER_NOT_FOUND/i)).toBeInTheDocument();
      expect(screen.getByText(/Ticker 'INVALID' not found/i)).toBeInTheDocument();
    });
  });
});