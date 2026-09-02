import React from "react";
import { Header } from "./components/common/Header";
import { Disclaimer } from "./components/common/Disclaimer";
import { ErrorBanner } from "./components/common/ErrorBanner";
import { LoadingSkeleton, ChartSkeleton } from "./components/common/LoadingSkeleton";
import { TickerSearch } from "./components/dashboard/TickerSearch";
import { CompanyOverview } from "./components/dashboard/CompanyOverview";
import { FinancialSnapshot } from "./components/dashboard/FinancialSnapshot";
import { ValuationMultiples } from "./components/dashboard/ValuationMultiples";
import { DCFSection } from "./components/dashboard/DCFSection";
import { SensitivityMatrix } from "./components/dashboard/SensitivityMatrix";
import { FinancialHealth } from "./components/dashboard/FinancialHealth";
import { NewsSection } from "./components/dashboard/NewsSection";
import { ResearchMemo } from "./components/dashboard/ResearchMemo";
import { HistoricalTrendsChart } from "./components/charts/HistoricalTrendsChart";
import { MarginComparisonChart } from "./components/charts/MarginComparisonChart";
import { useFinancialAnalysis } from "./hooks/useFinancialAnalysis";
import { useResearchReport } from "./hooks/useResearchReport";
import { BarChart3, Binary, ShieldCheck, Sparkles } from "lucide-react";

export const App: React.FC = () => {
  const {
    analysis,
    isLoading,
    error,
    errorCode,
    isBackendHealthy,
    analyze,
    clearError,
  } = useFinancialAnalysis();

  const {
    report,
    isLoading: isReportLoading,
    error: reportError,
    errorCode: reportErrorCode,
    fetchReport,
    reset: resetReport,
  } = useResearchReport();

  // Reset research report when analyzing a new ticker
  const handleSearch = (ticker: string) => {
    resetReport();
    analyze(ticker);
  };

  return (
    <div className="min-h-screen bg-terminal-bg text-terminal-text flex flex-col font-sans">
      <Header isBackendHealthy={isBackendHealthy} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <TickerSearch
          onSearch={handleSearch}
          isLoading={isLoading}
          currentTicker={analysis?.ticker}
        />

        {error && (
          <ErrorBanner
            code={errorCode}
            message={error}
            onDismiss={clearError}
            onRetry={() => analysis?.ticker && analyze(analysis.ticker)}
          />
        )}

        {isLoading && (
          <div className="space-y-6 py-4">
            <LoadingSkeleton count={4} height="h-28" />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartSkeleton />
              <ChartSkeleton />
            </div>
            <LoadingSkeleton count={4} height="h-32" />
          </div>
        )}

        {!isLoading && !analysis && !error && (
          <div className="py-16 px-4 text-center max-w-2xl mx-auto">
            <div className="w-14 h-14 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mx-auto mb-4">
              <BarChart3 className="w-7 h-7" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-white mb-2">
              Financial Research Terminal Ready
            </h2>
            <p className="text-sm text-terminal-muted leading-relaxed mb-8">
              Search any publicly traded stock symbol above to ingest SEC EDGAR Form 10-K filings,
              evaluate deterministic margins and cash flow metrics, compute model-implied DCF valuations,
              and synthesize grounded investment research memos.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left font-mono text-xs">
              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center gap-2 text-sky-400 font-bold mb-1">
                  <Binary className="w-4 h-4" />
                  <span>Deterministic Truth</span>
                </div>
                <p className="text-terminal-dim">
                  Zero AI hallucinated math. 100% pure Python calculations derived from audited SEC facts.
                </p>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center gap-2 text-emerald-400 font-bold mb-1">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Sector Aware</span>
                </div>
                <p className="text-terminal-dim">
                  Intelligent sector gating cleanly protects financial institutions (e.g. JPM) from broken DCF models.
                </p>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center gap-2 text-purple-400 font-bold mb-1">
                  <Sparkles className="w-4 h-4" />
                  <span>Grounded LLM</span>
                </div>
                <p className="text-terminal-dim">
                  OpenAI structured output synthesis bound by 11 strict grounding rules and verified citations.
                </p>
              </div>
            </div>
          </div>
        )}

        {!isLoading && analysis && (
          <div className="space-y-6">
            {/* 1. Company Overview */}
            <CompanyOverview analysis={analysis} />

            {/* 2. Financial Snapshot */}
            <FinancialSnapshot analysis={analysis} />

            {/* 3. Recharts Visualizations */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <HistoricalTrendsChart
                trends={analysis.historical_trends}
                currency={analysis.currency}
              />
              <MarginComparisonChart trends={analysis.historical_trends} />
            </div>

            {/* 4. Valuation Multiples */}
            <ValuationMultiples analysis={analysis} />

            {/* 5. DCF Section */}
            <DCFSection dcf={analysis.dcf} currency={analysis.currency} />

            {/* 6. DCF Sensitivity Matrix */}
            <SensitivityMatrix
              sensitivityTable={analysis.dcf?.sensitivity_table}
              baseWacc={analysis.dcf?.wacc}
              baseTerminalGrowth={analysis.dcf?.terminal_growth_rate}
              currency={analysis.currency}
            />

            {/* 7. Financial Health */}
            <FinancialHealth
              health={analysis.health}
              warnings={analysis.warnings}
            />

            {/* 8. Recent News */}
            <NewsSection news={analysis.news || []} />

            {/* 9. Grounded AI Research Memo */}
            <ResearchMemo
              report={report}
              isLoading={isReportLoading}
              error={reportError}
              errorCode={reportErrorCode}
              onGenerate={() => fetchReport(analysis.ticker)}
              ticker={analysis.ticker}
            />
          </div>
        )}
      </main>

      <Disclaimer />
    </div>
  );
};