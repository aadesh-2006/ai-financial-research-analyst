import React from "react";
import {
  Sparkles,
  Loader2,
  FileText,
  AlertTriangle,
  ExternalLink,
  Target,
  Flame,
  HelpCircle,
  TrendingUp,
} from "lucide-react";
import { ResearchReport } from "../../api/types";
import { Badge } from "../common/Badge";
import { ErrorBanner } from "../common/ErrorBanner";

interface ResearchMemoProps {
  report: ResearchReport | null;
  isLoading: boolean;
  error: string | null;
  errorCode?: string;
  onGenerate: () => void;
  ticker: string;
}

export const ResearchMemo: React.FC<ResearchMemoProps> = ({
  report,
  isLoading,
  error,
  errorCode,
  onGenerate,
  ticker,
}) => {
  return (
    <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-terminal-border pb-5 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5 text-sky-400" />
            <h3 className="text-lg font-bold text-white tracking-tight">
              Institutional AI Investment Research Memo
            </h3>
            <Badge variant="purple">OpenAI Structured Output</Badge>
          </div>
          <p className="text-xs text-terminal-muted">
            Grounded qualitative synthesis interpreting deterministic filings, ratios, news, and DCF models.
          </p>
        </div>

        {!report && (
          <button
            onClick={onGenerate}
            disabled={isLoading}
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-slate-950 font-bold text-xs px-5 py-2.5 rounded-xl transition-all shadow-lg shadow-sky-500/10 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Synthesizing Memo...</span>
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                <span>Generate Research Memo ({ticker})</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Error state */}
      {error && (
        <ErrorBanner
          code={errorCode}
          message={error}
          onRetry={onGenerate}
        />
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="py-12 flex flex-col items-center justify-center gap-4 text-center">
          <div className="relative">
            <div className="w-12 h-12 rounded-full border-2 border-sky-500/20 border-t-sky-500 animate-spin" />
            <Sparkles className="w-5 h-5 text-sky-400 absolute inset-0 m-auto" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white font-mono">
              Synthesizing Grounded Research Memo for {ticker}...
            </div>
            <p className="text-xs text-terminal-dim mt-1 max-w-md">
              Context builder assembling 9 briefing sections. OpenAI generating structured investment thesis, risk matrix, and verified citations.
            </p>
          </div>
        </div>
      )}

      {/* Empty State before generation */}
      {!report && !isLoading && !error && (
        <div className="py-8 text-center text-xs text-terminal-dim border border-dashed border-slate-800 rounded-xl">
          <FileText className="w-8 h-8 text-slate-700 mx-auto mb-2" />
          <p className="font-semibold text-slate-400">Institutional Research Memo Ready</p>
          <p className="mt-1">
            Click "Generate Research Memo" above to run qualitative LLM synthesis for {ticker}.
          </p>
        </div>
      )}

      {/* Render Report */}
      {report && (
        <div className="space-y-6">
          {/* Executive Summary & Thesis */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider">
                Executive Briefing
              </span>
              {report.confidence?.level && (
                <Badge
                  variant={
                    report.confidence.level === "High"
                      ? "emerald"
                      : report.confidence.level === "Medium"
                      ? "amber"
                      : "rose"
                  }
                >
                  Confidence: {report.confidence.level}
                </Badge>
              )}
            </div>
            <p className="text-sm text-slate-200 leading-relaxed mb-4">
              {report.executive_summary}
            </p>

            <div className="border-t border-slate-800 pt-3">
              <div className="text-xs font-mono font-semibold text-terminal-muted uppercase mb-1">
                Core Investment Thesis:
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed italic">
                "{report.investment_thesis}"
              </p>
            </div>
          </div>

          {/* Strengths, Risks, Catalysts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-xl p-4">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2 font-mono">
                <TrendingUp className="w-4 h-4" />
                <span>Fundamental Strengths</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {report.strengths.map((s, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Risks */}
            <div className="bg-rose-950/20 border border-rose-500/20 rounded-xl p-4">
              <div className="flex items-center gap-1.5 text-xs font-bold text-rose-400 uppercase tracking-wider mb-2 font-mono">
                <AlertTriangle className="w-4 h-4" />
                <span>Key Investment Risks</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {report.risks.map((r, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-rose-400">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Catalysts */}
            <div className="bg-sky-950/20 border border-sky-500/20 rounded-xl p-4">
              <div className="flex items-center gap-1.5 text-xs font-bold text-sky-400 uppercase tracking-wider mb-2 font-mono">
                <Flame className="w-4 h-4" />
                <span>Growth Catalysts</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {report.catalysts.map((c, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-sky-400">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Concerns */}
            <div className="bg-amber-950/20 border border-amber-500/20 rounded-xl p-4">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400 uppercase tracking-wider mb-2 font-mono">
                <Target className="w-4 h-4" />
                <span>Operational Concerns</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {report.concerns.map((c, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-amber-400">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* DCF Qualitative Interpretation */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <h4 className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider mb-2">
              DCF & Valuation Qualitative Synthesis
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed mb-3">
              {report.dcf_interpretation?.summary}
            </p>
            <div className="bg-black/30 border border-slate-800 p-3 rounded-lg text-xs font-mono space-y-1 text-slate-300">
              <div>
                <span className="text-terminal-dim font-bold">Valuation Signal: </span>
                <span className="text-emerald-400">{report.dcf_interpretation?.valuation_signal}</span>
              </div>
              <div>
                <span className="text-terminal-dim font-bold">Sensitivity Observation: </span>
                <span>{report.dcf_interpretation?.sensitivity_observation}</span>
              </div>
            </div>
          </div>

          {/* Sources Provenance Section */}
          <div>
            <h4 className="text-xs font-mono font-bold text-terminal-muted uppercase tracking-wider mb-3">
              Verified Source Citations & Provenance
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
              {report.sources?.map((src, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/40 border border-slate-800/80 rounded-lg p-2.5 flex items-center justify-between gap-2"
                >
                  <div className="truncate">
                    <span className="text-sky-400 font-bold">[{src.provider}] </span>
                    <span className="text-slate-300">{src.title}</span>
                  </div>
                  {src.url && (
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-400 hover:text-sky-300 shrink-0 p-1"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Limitations Notice */}
          {report.limitations && report.limitations.length > 0 && (
            <div className="text-[11px] text-terminal-dim bg-slate-950/40 border border-slate-900 p-3 rounded-xl flex items-start gap-2">
              <HelpCircle className="w-3.5 h-3.5 text-terminal-dim shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-terminal-muted">Model Caveats & Guardrails: </span>
                {report.limitations.join(" • ")}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};