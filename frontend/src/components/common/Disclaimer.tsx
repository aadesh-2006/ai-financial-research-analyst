import React from "react";
import { ShieldAlert } from "lucide-react";

export const Disclaimer: React.FC = () => {
  return (
    <footer className="mt-12 border-t border-terminal-border py-8 text-terminal-dim text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-terminal-muted shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-terminal-muted">
            Institutional Research & Methodology Notice
          </p>
          <p>
            This system provides automated financial data aggregation, quantitative ratio calculations, and
            model-implied valuation frameworks for informational and research purposes only. It does not constitute
            investment advice, a recommendation, endorsement, or offer to purchase or sell any security.
          </p>
          <p>
            Discounted Cash Flow (DCF) intrinsic share prices are mathematical derivations conditioned upon explicit
            model assumptions (e.g., CAPM cost of equity, terminal growth rate, and historic cash flow projections)
            and are highly sensitive to market inputs. Historical financial data is derived directly from audited SEC EDGAR
            Form 10-K filings and delayed market quotes.
          </p>
        </div>
      </div>
    </footer>
  );
};