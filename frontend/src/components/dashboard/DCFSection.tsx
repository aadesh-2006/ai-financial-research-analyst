import React from "react";
import { Calculator, AlertTriangle, ShieldCheck } from "lucide-react";
import { DCFValuation } from "../../api/types";
import { formatCurrency, formatPercent } from "../../utils/formatters";
import { Badge } from "../common/Badge";

interface DCFSectionProps {
  dcf: DCFValuation | null | undefined;
  currency?: string;
}

export const DCFSection: React.FC<DCFSectionProps> = ({ dcf, currency = "USD" }) => {
  if (!dcf) {
    return null;
  }

  // SPECIAL CASE: Financial Institution Sector Gate (e.g. JPM)
  if (dcf.status === "not_applicable") {
    return (
      <div className="bg-terminal-card border border-amber-500/30 rounded-2xl p-6 shadow-xl mb-6">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h3 className="text-base font-bold text-amber-200">
                Discounted Cash Flow (DCF) Sector Gate: Not Applicable
              </h3>
              <Badge variant="amber">Financial Institution</Badge>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed mb-3">
              Standard industrial Free Cash Flow DCF models are not applicable to commercial banks and financial institutions.
              Financial institutions intermediate capital through interest margins, deposit funding, and statutory capital reserve
              ratios rather than industrial capital expenditures.
            </p>
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs text-terminal-muted flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                Recommended Valuation Frameworks: Evaluate using Trailing & Forward P/E, Return on Equity (ROE), and regulatory Tier 1 capital ratios.
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // DCF Calculation Error or Insufficient Data
  if (dcf.status !== "calculated") {
    return (
      <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
        <div className="flex items-center gap-3 text-terminal-dim font-mono text-xs">
          <Calculator className="w-4 h-4 text-terminal-muted" />
          <span>DCF valuation could not be computed due to non-positive cash flows or incomplete historical 10-Ks.</span>
        </div>
      </div>
    );
  }

  const isUpsidePositive = (dcf.upside_downside_pct ?? 0) >= 0;

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-terminal-border pb-5 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-base font-bold text-white tracking-tight">
              Deterministic 5-Year DCF & Valuation Model
            </h3>
            <Badge variant="sky">Model-Implied</Badge>
          </div>
          <p className="text-xs text-terminal-muted">
            Bounded historical FCF projections discounted via CAPM Weighted Average Cost of Capital (WACC).
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-xs font-mono text-terminal-dim uppercase">Model Status:</span>
          <Badge variant="emerald">Computed</Badge>
        </div>
      </div>

      {/* Primary DCF Valuation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-terminal-muted font-medium uppercase mb-1">Implied Share Price</div>
          <div className="text-2xl font-bold font-mono text-sky-400">
            {formatCurrency(dcf.implied_share_price, currency, false)}
          </div>
          <div className="text-[11px] text-terminal-dim mt-1 font-mono">
            Model-Implied Equity Value / Shares
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-terminal-muted font-medium uppercase mb-1">Current Market Price</div>
          <div className="text-2xl font-bold font-mono text-white">
            {formatCurrency(dcf.current_share_price, currency, false)}
          </div>
          <div className="text-[11px] text-terminal-dim mt-1 font-mono">
            Market Observed Quote
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-terminal-muted font-medium uppercase mb-1">Model Upside / Downside</div>
          <div
            className={`text-2xl font-bold font-mono ${
              isUpsidePositive ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {formatPercent(
              dcf.upside_downside_pct !== null && dcf.upside_downside_pct !== undefined
                ? dcf.upside_downside_pct / 100
                : null,
              1,
              true
            )}
          </div>
          <div className="text-[11px] text-terminal-dim mt-1 font-mono">
            Relative to Current Price
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-terminal-muted font-medium uppercase mb-1">Discount Rate (WACC)</div>
          <div className="text-2xl font-bold font-mono text-white">
            {formatPercent(dcf.wacc, 2)}
          </div>
          <div className="text-[11px] text-terminal-dim mt-1 font-mono">
            Terminal Growth (g): {formatPercent(dcf.terminal_growth_rate, 2)}
          </div>
        </div>
      </div>

      {/* Capital Structure & Assumptions Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-black/30 border border-slate-800/80 rounded-xl p-4 mb-6 text-xs font-mono">
        <div>
          <span className="text-terminal-dim block">Risk-Free Rate (Rf):</span>
          <span className="text-slate-200 font-bold">{formatPercent(dcf.risk_free_rate, 2)}</span>
        </div>
        <div>
          <span className="text-terminal-dim block">Equity Risk Premium:</span>
          <span className="text-slate-200 font-bold">{formatPercent(dcf.equity_risk_premium, 2)}</span>
        </div>
        <div>
          <span className="text-terminal-dim block">Cost of Equity (Ke):</span>
          <span className="text-slate-200 font-bold">{formatPercent(dcf.cost_of_equity, 2)}</span>
        </div>
        <div>
          <span className="text-terminal-dim block">FCF Growth Assumption:</span>
          <span className="text-slate-200 font-bold">{formatPercent(dcf.fcf_growth_assumption, 2)}</span>
        </div>
      </div>

      {/* Explicit Projections Table */}
      {dcf.projections && dcf.projections.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-terminal-muted uppercase tracking-wider mb-3">
            5-Year Explicit Free Cash Flow Projections
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border border-slate-800 rounded-lg overflow-hidden">
              <thead className="bg-slate-900 text-terminal-dim uppercase border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Forecast Year</th>
                  <th className="py-2.5 px-3">Projected FCF</th>
                  <th className="py-2.5 px-3">Discount Factor (1 / (1+WACC)^t)</th>
                  <th className="py-2.5 px-3">Present Value (PV)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {dcf.projections.map((p) => (
                  <tr key={p.year} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2 px-3 font-semibold text-white">Year +{p.year}</td>
                    <td className="py-2 px-3">{formatCurrency(p.projected_fcf, currency, false)}</td>
                    <td className="py-2 px-3 text-terminal-dim">{p.discount_factor.toFixed(4)}</td>
                    <td className="py-2 px-3 text-emerald-400 font-medium">
                      {formatCurrency(p.present_value, currency, false)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};