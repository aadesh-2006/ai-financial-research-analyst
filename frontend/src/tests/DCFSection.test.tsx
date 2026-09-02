import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DCFSection } from "../components/dashboard/DCFSection";
import { DCFValuation } from "../api/types";

describe("DCFSection Component", () => {
  const mockCorporateDCF: DCFValuation = {
    ticker: "AAPL",
    status: "calculated",
    risk_free_rate: 0.042,
    beta: 1.1,
    equity_risk_premium: 0.05,
    cost_of_equity: 0.097,
    wacc: 0.085,
    terminal_growth_rate: 0.025,
    fcf_growth_assumption: 0.065,
    current_share_price: 220.0,
    implied_share_price: 210.50,
    upside_downside_pct: -4.3,
    projections: [
      { year: 1, projected_fcf: 110_000_000_000, discount_factor: 0.9217, present_value: 101_387_000_000 },
      { year: 2, projected_fcf: 117_150_000_000, discount_factor: 0.8495, present_value: 99_518_925_000 },
    ],
  };

  it("renders standard corporate DCF with implied price, WACC, and projections", () => {
    render(<DCFSection dcf={mockCorporateDCF} currency="USD" />);

    expect(screen.getByText(/Deterministic 5-Year DCF/i)).toBeInTheDocument();
    expect(screen.getByText("$210.50")).toBeInTheDocument();
    expect(screen.getByText("$220.00")).toBeInTheDocument();
    expect(screen.getByText("-4.3%")).toBeInTheDocument();
    expect(screen.getByText("8.50%")).toBeInTheDocument();
    expect(screen.getByText(/Year \+1/i)).toBeInTheDocument();
    expect(screen.getByText(/Year \+2/i)).toBeInTheDocument();
  });

  it("safely enforces sector gate for financial institutions (not_applicable)", () => {
    const mockBankDCF: DCFValuation = {
      ticker: "JPM",
      status: "not_applicable",
      current_share_price: 200.0,
      implied_share_price: null,
      upside_downside_pct: null,
    };

    render(<DCFSection dcf={mockBankDCF} currency="USD" />);

    // Must show clear gate notice
    expect(screen.getByText(/Sector Gate: Not Applicable/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Financial Institution/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Standard industrial Free Cash Flow DCF models are not applicable/i)
    ).toBeInTheDocument();

    // Must NOT display fake implied share price or upside
    expect(screen.queryByText(/Implied Share Price/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Model Upside/i)).not.toBeInTheDocument();

    // Must guide to P/E and ROE
    expect(screen.getByText(/Evaluate using Trailing & Forward P\/E, Return on Equity/i)).toBeInTheDocument();
  });
});