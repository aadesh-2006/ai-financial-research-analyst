import React from "react";
import { ShieldCheck, Terminal } from "lucide-react";
import { Badge } from "./Badge";

interface HeaderProps {
  isBackendHealthy: boolean | null;
}

export const Header: React.FC<HeaderProps> = ({ isBackendHealthy }) => {
  return (
    <header className="border-b border-terminal-border bg-terminal-card/80 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold text-terminal-text tracking-tight">
                AI Financial Research Analyst
              </h1>
              <Badge variant="sky" size="sm">
                v1.0
              </Badge>
            </div>
            <p className="text-xs text-terminal-muted hidden sm:block">
              Institutional Financial Research, Deterministic Valuation & Grounded LLM Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800 px-2.5 py-1 rounded-full">
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendHealthy === null
                  ? "bg-amber-400 animate-pulse"
                  : isBackendHealthy
                  ? "bg-emerald-400"
                  : "bg-rose-400"
              }`}
            />
            <span className="text-terminal-muted font-mono">
              {isBackendHealthy === null
                ? "Connecting..."
                : isBackendHealthy
                ? "FastAPI API Active"
                : "Backend Offline"}
            </span>
          </div>

          <div className="hidden md:flex items-center gap-1 text-terminal-dim">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Deterministic Ground Truth</span>
          </div>
        </div>
      </div>
    </header>
  );
};