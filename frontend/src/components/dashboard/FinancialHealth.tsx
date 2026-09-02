import React from "react";
import { Activity, AlertCircle, CheckCircle2 } from "lucide-react";
import { FinancialHealth as FinancialHealthType } from "../../api/types";
import { Badge } from "../common/Badge";

interface FinancialHealthProps {
  health: FinancialHealthType;
  warnings?: string[];
}

export const FinancialHealth: React.FC<FinancialHealthProps> = ({ health, warnings = [] }) => {
  const getPillarVariant = (rating: string) => {
    switch (rating?.toLowerCase()) {
      case "strong":
        return "emerald";
      case "moderate":
        return "amber";
      default:
        return "rose";
    }
  };

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-terminal-border pb-5 mb-5">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-sky-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Deterministic Financial Health Synthesis
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-terminal-muted font-mono uppercase">Overall Rating:</span>
          <Badge
            variant={
              health.overall === "Strong"
                ? "emerald"
                : health.overall === "Moderate"
                ? "amber"
                : "rose"
            }
            size="md"
          >
            {health.overall}
          </Badge>
        </div>
      </div>

      {/* 4 Pillars Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5">
          <div className="text-xs text-terminal-muted font-mono uppercase mb-1">Growth Pillar</div>
          <Badge variant={getPillarVariant(health.growth_pillar)} size="sm">
            {health.growth_pillar}
          </Badge>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5">
          <div className="text-xs text-terminal-muted font-mono uppercase mb-1">Profitability</div>
          <Badge variant={getPillarVariant(health.profitability_pillar)} size="sm">
            {health.profitability_pillar}
          </Badge>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5">
          <div className="text-xs text-terminal-muted font-mono uppercase mb-1">Leverage & Solvency</div>
          <Badge variant={getPillarVariant(health.leverage_pillar)} size="sm">
            {health.leverage_pillar}
          </Badge>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5">
          <div className="text-xs text-terminal-muted font-mono uppercase mb-1">Cash Flow Quality</div>
          <Badge variant={getPillarVariant(health.cash_flow_pillar)} size="sm">
            {health.cash_flow_pillar}
          </Badge>
        </div>
      </div>

      {/* Observations */}
      {health.key_observations && health.key_observations.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-semibold text-terminal-dim uppercase tracking-wider mb-2 font-mono">
            Deterministic Engine Observations:
          </div>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {health.key_observations.map((obs, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>{obs}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings if any */}
      {warnings.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-xs text-amber-300">
          <div className="flex items-center gap-1.5 font-semibold mb-1">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Data Ingestion & Consistency Disclosures:</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-amber-200/90 pl-1 font-mono text-[11px]">
            {warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};