import React from "react";
import { AlertCircle, RefreshCw, XCircle } from "lucide-react";

interface ErrorBannerProps {
  code?: string;
  message: string;
  details?: any;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  code,
  message,
  details,
  onRetry,
  onDismiss,
}) => {
  return (
    <div className="bg-rose-950/40 border border-rose-500/40 rounded-xl p-4 sm:p-5 my-4 text-rose-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="font-semibold text-rose-100">Operation Failed</span>
              {code && (
                <span className="font-mono text-xs bg-rose-900/60 border border-rose-500/30 text-rose-300 px-2 py-0.5 rounded">
                  {code}
                </span>
              )}
            </div>
            <p className="text-sm text-rose-200/90">{message}</p>
            {details && (
              <div className="mt-2 text-xs font-mono bg-black/40 p-2 rounded border border-rose-900/40 max-h-32 overflow-y-auto">
                {typeof details === "string" ? details : JSON.stringify(details, null, 2)}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-1 text-xs font-medium bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 px-3 py-1.5 rounded-lg border border-rose-500/40 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-rose-400 hover:text-rose-200 p-1 transition-colors"
              aria-label="Dismiss error"
            >
              <XCircle className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};