import React, { useState } from "react";
import { Search, Loader2, Sparkles } from "lucide-react";

interface TickerSearchProps {
  onSearch: (ticker: string) => void;
  isLoading: boolean;
  currentTicker?: string;
}

const POPULAR_TICKERS = [
  { symbol: "AAPL", name: "Apple" },
  { symbol: "NVDA", name: "Nvidia" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "JPM", name: "JPMorgan (Bank Gate)" },
];

export const TickerSearch: React.FC<TickerSearchProps> = ({
  onSearch,
  isLoading,
  currentTicker = "",
}) => {
  const [inputVal, setInputVal] = useState(currentTicker);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = inputVal.trim().toUpperCase();
    if (clean) {
      onSearch(clean);
    }
  };

  const handleSelectQuick = (ticker: string) => {
    setInputVal(ticker);
    onSearch(ticker);
  };

  return (
    <div className="w-full bg-terminal-card border border-terminal-border rounded-2xl p-4 sm:p-6 shadow-xl mb-6">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 items-center">
        <div className="relative w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-terminal-dim" />
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value.toUpperCase())}
            placeholder="Enter public stock ticker (e.g. AAPL, NVDA, MSFT, JPM)..."
            disabled={isLoading}
            className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-xl pl-11 pr-4 py-3 text-sm font-mono text-terminal-text placeholder:text-terminal-dim transition-all outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !inputVal.trim()}
          className="w-full sm:w-auto shrink-0 flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed text-slate-950 font-semibold text-sm px-6 py-3 rounded-xl transition-all shadow-lg shadow-sky-500/10"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Analyze Company</span>
            </>
          )}
        </button>
      </form>

      <div className="flex items-center gap-2 mt-4 text-xs flex-wrap">
        <span className="text-terminal-dim font-mono">Quick Benchmarks:</span>
        {POPULAR_TICKERS.map((t) => (
          <button
            key={t.symbol}
            onClick={() => handleSelectQuick(t.symbol)}
            disabled={isLoading}
            className="font-mono bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700 transition-colors disabled:opacity-50"
          >
            <span className="font-bold text-sky-400">{t.symbol}</span>
            <span className="text-terminal-dim ml-1">({t.name})</span>
          </button>
        ))}
      </div>
    </div>
  );
};