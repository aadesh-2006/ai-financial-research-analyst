import React from "react";
import { TrendingDown, TrendingUp, Info } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  subValue?: string;
  formula?: string;
  trend?: "up" | "down" | "neutral";
  warning?: string | null;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  formula,
  trend,
  warning,
  className = "",
}) => {
  return (
    <div
      className={`bg-terminal-card border border-terminal-border rounded-xl p-4 transition-all hover:border-terminal-borderGlow hover:shadow-lg hover:shadow-terminal-accent/5 ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="text-xs font-medium uppercase tracking-wider text-terminal-muted">
          {label}
        </span>
        {formula && (
          <div className="relative group cursor-pointer">
            <Info className="w-3.5 h-3.5 text-terminal-dim hover:text-terminal-muted transition-colors" />
            <div className="absolute right-0 bottom-full mb-1.5 hidden group-hover:block w-48 p-2 bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded shadow-xl z-20 pointer-events-none">
              {formula}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono text-terminal-text tracking-tight">
          {value}
        </span>
        {trend && trend !== "neutral" && (
          <span
            className={`inline-flex items-center text-xs font-semibold ${
              trend === "up" ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {trend === "up" ? (
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
            )}
          </span>
        )}
      </div>

      {subValue && (
        <div className="mt-1 text-xs text-terminal-dim font-mono">{subValue}</div>
      )}

      {warning && (
        <div className="mt-2 text-[11px] text-amber-400/90 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
          {warning}
        </div>
      )}
    </div>
  );
};