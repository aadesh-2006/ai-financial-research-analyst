import React from "react";
import { ExternalLink, Building2, Tag, DollarSign, Calendar } from "lucide-react";
import { AnalyzeResponse } from "../../api/types";
import { formatCurrency, formatDate, formatMultiple } from "../../utils/formatters";
import { Badge } from "../common/Badge";

interface CompanyOverviewProps {
  analysis: AnalyzeResponse;
}

export const CompanyOverview: React.FC<CompanyOverviewProps> = ({ analysis }) => {
  const m = analysis.valuation;
  const currentPrice = analysis.dcf?.current_share_price ?? null;

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-terminal-border pb-6">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white">
              {analysis.company_name}
            </h2>
            <Badge variant="sky" size="md">
              {analysis.ticker}
            </Badge>
            {analysis.health?.overall && (
              <Badge
                variant={
                  analysis.health.overall === "Strong"
                    ? "emerald"
                    : analysis.health.overall === "Moderate"
                    ? "amber"
                    : "rose"
                }
                size="md"
              >
                Health: {analysis.health.overall}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-4 mt-2 text-xs text-terminal-muted flex-wrap">
            {analysis.sector && (
              <span className="flex items-center gap-1">
                <Building2 className="w-3.5 h-3.5 text-terminal-dim" />
                {analysis.sector}
              </span>
            )}
            {analysis.industry && (
              <span className="flex items-center gap-1">
                <Tag className="w-3.5 h-3.5 text-terminal-dim" />
                {analysis.industry}
              </span>
            )}
            <span className="flex items-center gap-1 font-mono">
              <DollarSign className="w-3.5 h-3.5 text-terminal-dim" />
              Currency: {analysis.currency}
            </span>
            {analysis.website && (
              <a
                href={analysis.website}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sky-400 hover:text-sky-300 transition-colors"
              >
                <span>Website</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        {/* Market Quick Stats */}
        <div className="flex items-center gap-6 bg-slate-900/80 border border-slate-800 rounded-xl p-4 shrink-0">
          <div>
            <div className="text-xs text-terminal-muted font-medium uppercase">Current Price</div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {formatCurrency(currentPrice, analysis.currency, false)}
            </div>
          </div>
          <div className="border-l border-slate-800 pl-6">
            <div className="text-xs text-terminal-muted font-medium uppercase">Market Cap</div>
            <div className="text-xl font-bold font-mono text-white">
              {formatCurrency(m.market_cap, analysis.currency)}
            </div>
          </div>
          {analysis.dcf?.beta !== undefined && (
            <div className="border-l border-slate-800 pl-6 hidden sm:block">
              <div className="text-xs text-terminal-muted font-medium uppercase">Beta</div>
              <div className="text-xl font-bold font-mono text-sky-400">
                {formatMultiple(analysis.dcf?.beta, "")}
              </div>
            </div>
          )}
        </div>
      </div>

      {analysis.description && (
        <div className="mt-4 text-xs sm:text-sm text-slate-300 leading-relaxed max-w-5xl">
          {analysis.description}
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-terminal-dim font-mono">
        <span className="flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" />
          Last Ingested Analysis: {formatDate(analysis.analyzed_at)}
        </span>
        <span>Deterministic Source: SEC EDGAR 10-K & Live Quote Feeds</span>
      </div>
    </div>
  );
};