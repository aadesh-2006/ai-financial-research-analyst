import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { FinancialTrend } from "../../api/types";
import { formatPercent } from "../../utils/formatters";

interface MarginComparisonChartProps {
  trends: FinancialTrend[];
}

export const MarginComparisonChart: React.FC<MarginComparisonChartProps> = ({ trends }) => {
  if (!trends || trends.length === 0) {
    return (
      <div className="h-64 bg-terminal-card border border-terminal-border rounded-xl p-6 flex items-center justify-center text-xs text-terminal-dim font-mono">
        Margin trend history not available for this issuer.
      </div>
    );
  }

  const data = [...trends]
    .sort((a, b) => a.fiscal_year - b.fiscal_year)
    .map((t) => ({
      year: t.fiscal_year.toString(),
      operatingMargin: t.operating_margin,
      netMargin: t.net_margin,
      fcfMargin: t.fcf_margin,
    }));

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-bold text-white font-mono">
            Operating & Cash Margin Trajectory
          </h4>
          <p className="text-xs text-terminal-dim">Annual conversion efficiency (%)</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="year"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "#334155" }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#334155",
                borderRadius: "8px",
                fontSize: "12px",
                fontFamily: "monospace",
              }}
              formatter={(value: any) => [formatPercent(Number(value), 1), ""]}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
              formatter={(val) => (
                <span className="text-terminal-muted">
                  {val === "operatingMargin"
                    ? "Operating Margin"
                    : val === "netMargin"
                    ? "Net Margin"
                    : "FCF Margin"}
                </span>
              )}
            />
            <Line
              type="monotone"
              dataKey="operatingMargin"
              stroke="#38bdf8"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#38bdf8" }}
            />
            <Line
              type="monotone"
              dataKey="netMargin"
              stroke="#a855f7"
              strokeWidth={2}
              dot={{ r: 3, fill: "#a855f7" }}
            />
            <Line
              type="monotone"
              dataKey="fcfMargin"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={{ r: 3, fill: "#10b981" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};