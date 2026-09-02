import React from "react";
import { AnalyzeResponse } from "../../api/types";
import { formatCurrency, formatMultiple } from "../../utils/formatters";
import { MetricCard } from "../common/MetricCard";

interface ValuationMultiplesProps {
  analysis: AnalyzeResponse;
}

export const ValuationMultiples: React.FC<ValuationMultiplesProps> = ({ analysis }) => {
  const v = analysis.valuation;
  const curr = analysis.currency;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight">
            Market Trading Multiples & Enterprise Valuation
          </h3>
          <p className="text-xs text-terminal-muted">
            Observed market quotes combined with deterministic revenue and cash flow metrics.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <MetricCard
          label="Trailing P/E"
          value={formatMultiple(v.pe_ratio)}
          subValue="Current Price / Trailing EPS"
          formula="Reported trailing 12-month Price-to-Earnings ratio"
        />

        <MetricCard
          label="Forward P/E"
          value={formatMultiple(v.forward_pe)}
          subValue="Consensus Forward EPS"
          formula="Current Price / Estimated Consensus 1-Yr Forward EPS"
        />

        <MetricCard
          label="Price-to-Sales"
          value={formatMultiple(v.price_to_sales)}
          subValue="Market Cap / Revenue"
          formula="Market Capitalization / Latest Annual 10-K Revenue"
        />

        <MetricCard
          label="EV / EBITDA"
          value={formatMultiple(v.ev_to_ebitda)}
          subValue="Enterprise Value / EBITDA"
          formula="Enterprise Value / Operating Earnings + D&A"
        />

        <MetricCard
          label="Price-to-FCF"
          value={formatMultiple(v.price_to_fcf)}
          subValue="Market Cap / FCF"
          formula="Market Capitalization / Latest Annual Free Cash Flow"
        />

        <MetricCard
          label="Price-to-Book"
          value="Unavailable"
          subValue="Engine Unreported"
          formula="Price-to-Book is not reported by the deterministic valuation engine"
          warning="Unavailable in engine; rely on P/E and ROE"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mt-3">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between font-mono text-xs">
          <span className="text-terminal-muted uppercase">Market Capitalization:</span>
          <span className="text-white font-bold">{formatCurrency(v.market_cap, curr, false)}</span>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between font-mono text-xs">
          <span className="text-terminal-muted uppercase">Enterprise Value (EV):</span>
          <span className="text-white font-bold">{formatCurrency(v.enterprise_value, curr, false)}</span>
        </div>
      </div>
    </div>
  );
};