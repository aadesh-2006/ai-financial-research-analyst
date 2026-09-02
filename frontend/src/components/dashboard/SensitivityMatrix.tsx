import React from "react";
import { Grid } from "lucide-react";
import { SensitivityTable } from "../../api/types";
import { formatCurrency, formatPercent } from "../../utils/formatters";

interface SensitivityMatrixProps {
  sensitivityTable: SensitivityTable | null | undefined;
  baseWacc?: number | null;
  baseTerminalGrowth?: number | null;
  currency?: string;
}

export const SensitivityMatrix: React.FC<SensitivityMatrixProps> = ({
  sensitivityTable,
  baseWacc,
  baseTerminalGrowth,
  currency = "USD",
}) => {
  if (
    !sensitivityTable ||
    !sensitivityTable.wacc_range?.length ||
    !sensitivityTable.growth_range?.length ||
    !sensitivityTable.cells?.length
  ) {
    return null;
  }

  const { wacc_range, growth_range, cells } = sensitivityTable;

  // Build cell lookup map keyed by "wacc_g" rounded to 4 decimals to avoid float mismatch
  const cellMap = new Map<string, { price: number | null; upside: number | null }>();
  for (const c of cells) {
    const key = `${c.wacc.toFixed(4)}_${c.terminal_growth.toFixed(4)}`;
    cellMap.set(key, { price: c.implied_share_price, upside: c.upside_pct });
  }

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Grid className="w-4 h-4 text-sky-400" />
            <h3 className="text-base font-bold text-white tracking-tight">
              2D Valuation Sensitivity Matrix
            </h3>
          </div>
          <p className="text-xs text-terminal-muted mt-1">
            Model-implied share price sensitivity across discount rates (WACC) and terminal growth rates (g).
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-center font-mono text-xs border border-slate-800 rounded-xl overflow-hidden">
          <thead className="bg-slate-900 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 text-left text-terminal-dim uppercase bg-slate-950/60 border-r border-slate-800">
                WACC \ Terminal g
              </th>
              {growth_range.map((g) => (
                <th key={g} className="py-3 px-3 text-sky-400 font-semibold border-r border-slate-800/40 last:border-r-0">
                  {formatPercent(g, 1)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {wacc_range.map((w) => (
              <tr key={w} className="hover:bg-slate-800/20 transition-colors">
                <td className="py-3 px-4 text-left font-semibold text-sky-400 bg-slate-950/40 border-r border-slate-800">
                  {formatPercent(w, 1)}
                </td>
                {growth_range.map((g) => {
                  const key = `${w.toFixed(4)}_${g.toFixed(4)}`;
                  const cell = cellMap.get(key);
                  const isBaseCase =
                    baseWacc !== undefined &&
                    baseWacc !== null &&
                    baseTerminalGrowth !== undefined &&
                    baseTerminalGrowth !== null &&
                    Math.abs(w - baseWacc) < 0.001 &&
                    Math.abs(g - baseTerminalGrowth) < 0.001;

                  if (!cell || cell.price === null) {
                    return (
                      <td
                        key={g}
                        className="py-3 px-3 text-terminal-dim border-r border-slate-800/40 last:border-r-0 bg-slate-900/40"
                      >
                        —
                      </td>
                    );
                  }

                  const isPositive = (cell.upside ?? 0) >= 0;

                  return (
                    <td
                      key={g}
                      className={`py-2.5 px-3 border-r border-slate-800/40 last:border-r-0 transition-colors ${
                        isBaseCase
                          ? "bg-sky-500/15 ring-2 ring-sky-400/50 rounded"
                          : isPositive
                          ? "bg-emerald-950/20 text-emerald-300"
                          : "bg-rose-950/20 text-rose-300"
                      }`}
                    >
                      <div className="font-bold text-white text-xs">
                        {formatCurrency(cell.price, currency, false)}
                      </div>
                      <div
                        className={`text-[10px] font-medium ${
                          isPositive ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {formatPercent(
                          cell.upside !== null ? cell.upside / 100 : null,
                          1,
                          true
                        )}
                      </div>
                      {isBaseCase && (
                        <div className="text-[9px] uppercase tracking-wider text-sky-400 font-semibold mt-0.5">
                          Base Case
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};