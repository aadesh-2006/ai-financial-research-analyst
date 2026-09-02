import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { FinancialTrend } from "../../api/types";
import { formatCurrency } from "../../utils/formatters";

interface HistoricalTrendsChartProps {
  trends: FinancialTrend[];
  currency?: string;
}

export const HistoricalTrendsChart: React.FC<HistoricalTrendsChartProps> = ({
  trends,
  currency = "USD",
}) => {
  if (!trends || trends.length === 0) {
    return (
      <div className="h-64 bg-terminal-card border border-terminal-border rounded-xl p-6 flex items-center justify-center text-xs text-terminal-dim font-mono">
        Historical multi-period trend data not available for this issuer.
      </div>
    );
  }

  // Sort ascending by fiscal year
  const data = [...trends]
    .sort((a, b) => a.fiscal_year - b.fiscal_year)
    .map((t) => ({
      year: t.fiscal_year.toString(),
      revenue: t.revenue,
      operatingIncome: t.operating_income,
      freeCashFlow: t.free_cash_flow,
    }));

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-sm font-bold text-white font-mono">
            Historical Revenue & Cash Flow Trends
          </h4>
          <p className="text-xs text-terminal-dim">Annual 10-K progression ({currency})</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
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
              tickFormatter={(val) => formatCurrency(val, currency, true)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0f172a",
                borderColor: "#334155",
                borderRadius: "8px",
                fontSize: "12px",
                fontFamily: "monospace",
              }}
              formatter={(value: any) => [formatCurrency(Number(value), currency, false), ""]}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
              formatter={(val) => (
                <span className="text-terminal-muted">
                  {val === "revenue"
                    ? "Revenue"
                    : val === "operatingIncome"
                    ? "Operating Income"
                    : "Free Cash Flow"}
                </span>
              )}
            />
            <Bar dataKey="revenue" fill="#38bdf8" radius={[4, 4, 0, 0]} maxBarSize={36} />
            <Bar dataKey="operatingIncome" fill="#818cf8" radius={[4, 4, 0, 0]} maxBarSize={36} />
            <Bar dataKey="freeCashFlow" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={36} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};