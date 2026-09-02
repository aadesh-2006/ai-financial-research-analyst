import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ResearchMemo } from "../components/dashboard/ResearchMemo";
import { ResearchReport } from "../api/types";

describe("ResearchMemo Component", () => {
  const mockReport: ResearchReport = {
    ticker: "AAPL",
    company_name: "Apple Inc.",
    generated_at: "2026-09-02T18:00:00Z",
    executive_summary: "Apple demonstrates formidable cash generation and operating efficiency.",
    investment_thesis: "Unrivaled global device ecosystem and growing services mix.",
    financial_snapshot: {
      summary: "Stable high margins.",
      key_points: ["30% operating margin"],
    },
    valuation_assessment: {
      summary: "Trading at historical multiple premium.",
      multiples_summary: "32.5x P/E",
      key_points: ["High ROIC justifies premium"],
    },
    strengths: ["Brand moat", "Ecosystem lock-in"],
    risks: ["App Store antitrust litigation"],
    catalysts: ["Generative AI silicon integration"],
    concerns: ["China smartphone market share pressure"],
    financial_health_assessment: {
      summary: "Investment grade balance sheet.",
      overall_rating: "Strong",
      observations: ["Low net leverage"],
    },
    dcf_interpretation: {
      summary: "Intrinsic valuation closely tracks current market pricing.",
      valuation_signal: "Fairly valued under baseline 8.5% WACC",
      sensitivity_observation: "Moderate dispersion",
    },
    news_and_market_context: {
      summary: "Recent product launches.",
      relevant_headlines: ["Apple introduces M4 iPad Pro"],
    },
    conclusion: "Solid fundamental compounder.",
    confidence: {
      level: "High",
      rationale: "Comprehensive 10-K audited statements.",
    },
    limitations: ["Model relies on historical free cash flow growth."],
    sources: [
      {
        provider: "SEC_EDGAR",
        title: "SEC Form 10-K (2024)",
        url: "https://www.sec.gov/edgar/browse/?CIK=0000320193",
        source_type: "filing",
      },
    ],
    disclaimer: "Standard research disclaimer.",
  };

  it("renders trigger button when report has not been generated yet", () => {
    const handleGenerate = vi.fn();
    render(
      <ResearchMemo
        report={null}
        isLoading={false}
        error={null}
        onGenerate={handleGenerate}
        ticker="AAPL"
      />
    );

    const button = screen.getByRole("button", { name: /Generate Research Memo/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleGenerate).toHaveBeenCalled();
  });

  it("shows loading state when generating report", () => {
    render(
      <ResearchMemo
        report={null}
        isLoading={true}
        error={null}
        onGenerate={vi.fn()}
        ticker="AAPL"
      />
    );

    expect(screen.getByText(/Synthesizing Grounded Research Memo for AAPL/i)).toBeInTheDocument();
  });

  it("displays error banner if API key is missing or synthesis fails", () => {
    render(
      <ResearchMemo
        report={null}
        isLoading={false}
        error="OPENAI_API_KEY is not configured."
        errorCode="OPENAI_API_KEY_MISSING"
        onGenerate={vi.fn()}
        ticker="AAPL"
      />
    );

    expect(screen.getByText(/OPENAI_API_KEY_MISSING/i)).toBeInTheDocument();
    expect(screen.getByText(/OPENAI_API_KEY is not configured/i)).toBeInTheDocument();
  });

  it("renders complete investment memo when report is supplied", () => {
    render(
      <ResearchMemo
        report={mockReport}
        isLoading={false}
        error={null}
        onGenerate={vi.fn()}
        ticker="AAPL"
      />
    );

    expect(screen.getByText(/Apple demonstrates formidable cash generation/i)).toBeInTheDocument();
    expect(screen.getByText(/Unrivaled global device ecosystem/i)).toBeInTheDocument();
    expect(screen.getByText(/Brand moat/i)).toBeInTheDocument();
    expect(screen.getByText(/App Store antitrust litigation/i)).toBeInTheDocument();
    expect(screen.getByText(/Generative AI silicon integration/i)).toBeInTheDocument();
    expect(screen.getByText(/Confidence: High/i)).toBeInTheDocument();
    expect(screen.getByText(/\[SEC_EDGAR\]/i)).toBeInTheDocument();
  });
});