import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SensitivityMatrix } from "../components/dashboard/SensitivityMatrix";
import { SensitivityTable } from "../api/types";

describe("SensitivityMatrix Component", () => {
  const mockTable: SensitivityTable = {
    wacc_range: [0.075, 0.085, 0.095],
    growth_range: [0.02, 0.025, 0.03],
    cells: [
      { wacc: 0.075, terminal_growth: 0.02, implied_share_price: 230.0, upside_pct: 4.5 },
      { wacc: 0.075, terminal_growth: 0.025, implied_share_price: 250.0, upside_pct: 13.6 },
      { wacc: 0.075, terminal_growth: 0.03, implied_share_price: 275.0, upside_pct: 25.0 },
      { wacc: 0.085, terminal_growth: 0.02, implied_share_price: 195.0, upside_pct: -11.4 },
      { wacc: 0.085, terminal_growth: 0.025, implied_share_price: 210.5, upside_pct: -4.3 },
      { wacc: 0.085, terminal_growth: 0.03, implied_share_price: 228.0, upside_pct: 3.6 },
      { wacc: 0.095, terminal_growth: 0.02, implied_share_price: 170.0, upside_pct: -22.7 },
      { wacc: 0.095, terminal_growth: 0.025, implied_share_price: 181.0, upside_pct: -17.7 },
      { wacc: 0.095, terminal_growth: 0.03, implied_share_price: null, upside_pct: null }, // Null cell
    ],
  };

  it("renders 2D grid headers and values exactly as supplied by backend", () => {
    render(
      <SensitivityMatrix
        sensitivityTable={mockTable}
        baseWacc={0.085}
        baseTerminalGrowth={0.025}
      />
    );

    expect(screen.getByText(/2D Valuation Sensitivity Matrix/i)).toBeInTheDocument();
    // Headers
    expect(screen.getByText("7.5%")).toBeInTheDocument();
    expect(screen.getByText("8.5%")).toBeInTheDocument();
    expect(screen.getByText("9.5%")).toBeInTheDocument();

    // Specific cell values
    expect(screen.getByText("$210.50")).toBeInTheDocument();
    expect(screen.getByText("-4.3%")).toBeInTheDocument();
    expect(screen.getByText(/Base Case/i)).toBeInTheDocument();

    // Null cell handles cleanly with dash
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});