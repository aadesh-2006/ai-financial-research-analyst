import React from "react";
import { Newspaper, ExternalLink } from "lucide-react";
import { formatDate } from "../../utils/formatters";

interface NewsItem {
  headline: string;
  source?: string | null;
  url?: string | null;
  published_at?: string | null;
}

interface NewsSectionProps {
  news: NewsItem[];
}

export const NewsSection: React.FC<NewsSectionProps> = ({ news }) => {
  if (!news || news.length === 0) {
    return null;
  }

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex items-center gap-2 mb-4 border-b border-terminal-border pb-4">
        <Newspaper className="w-4 h-4 text-sky-400" />
        <h3 className="text-base font-bold text-white tracking-tight">
          Recent Corporate News & Filings Context
        </h3>
      </div>

      <div className="space-y-3">
        {news.map((item, idx) => (
          <div
            key={idx}
            className="bg-slate-900/50 hover:bg-slate-800/40 border border-slate-800/80 rounded-xl p-3.5 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          >
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-slate-100 leading-snug">
                {item.headline}
              </h4>
              <div className="flex items-center gap-3 text-xs text-terminal-dim font-mono">
                <span>{item.source || "Financial Press"}</span>
                {item.published_at && (
                  <>
                    <span>•</span>
                    <span>{formatDate(item.published_at)}</span>
                  </>
                )}
              </div>
            </div>

            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 transition-colors font-mono self-start sm:self-center"
              >
                <span>Read Source</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};