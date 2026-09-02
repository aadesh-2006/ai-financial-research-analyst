import React from "react";
import { AnalyzeResponse } from "../../api/types";
import { formatCurrency, formatMultiple, formatPercent } from "../../utils/formatters";
import { MetricCard } from "../common/MetricCard";

interface FinancialSnapshotProps {
  analysis: AnalyzeResponse;
}

export const FinancialSnapshot: React.FC<FinancialSnapshotProps> = ({ analysis }) => {
  const g = analysis.growth;
  const p = analysis.profitability;
  const cf = analysis.cash_flow;
  const l = analysis.leverage;
  const curr = analysis.currency;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight">
            Financial & Operational Snapshot
          </h3>
          <p className="text-xs text-terminal-muted">
            Deterministic calculations derived from SEC EDGAR Form 10-K filings.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4">
        <MetricCard
          label="Revenue YoY"
          value={formatPercent(g.revenue_growth_yoy, 1, true)}
          subValue={`3Y CAGR: ${formatPercent(g.revenue_cagr_3yr, 1)}`}
          trend={
            g.revenue_growth_yoy !== null
              ? g.revenue_growth_yoy > 0
                ? "up"
                : "down"
              : "neutral"
          }
          formula="(Revenue_t - Revenue_{t-1}) / Revenue_{t-1}"
        />

        <MetricCard
          label="Operating Margin"
          value={formatPercent(p.operating_margin, 1)}
          subValue={`Gross: ${formatPercent(p.gross_margin, 1)}`}
          trend={
            p.operating_margin !== null
              ? p.operating_margin > 0.15
                ? "up"
                : "neutral"
              : "neutral"
          }
          formula="Operating Income / Revenue"
        />

        <MetricCard
          label="Net Margin"
          value={formatPercent(p.net_margin, 1)}
          subValue={`ROE: ${formatPercent(p.roe, 1)}`}
          formula="Net Income / Revenue"
        />

        <MetricCard
          label="Free Cash Flow"
          value={formatCurrency(cf.free_cash_flow, curr)}
          subValue={`OCF: ${formatCurrency(cf.operating_cash_flow, curr)}`}
          trend={
            cf.free_cash_flow !== null
              ? cf.free_cash_flow > 0
                ? "up"
                : "down"
              : "neutral"
          }
          formula="Operating Cash Flow - Capital Expenditures"
        />

        <MetricCard
          label="FCF Conversion"
          value={formatPercent(cf.fcf_conversion, 1)}
          subValue={`FCF Margin: ${formatPercent(cf.fcf_margin, 1)}`}
          formula="Free Cash Flow / Net Income"
        />

        <MetricCard
          label="Debt-to-Equity"
          value={formatMultiple(l.debt_to_equity)}
          subValue={`Debt/EBITDA: ${formatMultiple(l.debt_to_ebitda)}`}
          formula="Total Debt / Stockholders' Equity"
        />

        <MetricCard
          label="Total Debt"
          value={formatCurrency(l.total_debt, curr)}
          subValue={`Equity: ${formatCurrency(l.stockholders_equity, curr)}`}
          formula="Short-Term Debt + Long-Term Debt"
        />

        <MetricCard
          label="Total Cash"
          value={formatCurrency(analysis.dcf?.cash, curr)}
          subValue={`Net Debt: ${formatCurrency(analysis.dcf?.net_debt, curr)}`}
          formula="Cash, Cash Equivalents & Marketable Securities"
        />

        <MetricCard
          label="ROIC"
          value={formatPercent(p.roic, 1)}
          subValue="Return on Invested Capital"
          formula="NOPAT / Invested Capital"
        />

        <MetricCard
          label="Interest Coverage"
          value={formatMultiple(l.interest_coverage)}
          subValue="EBIT / Interest Expense"
          formula="Operating Income / Net Interest Expense"
        />
      </div>
    </div>
  );
};