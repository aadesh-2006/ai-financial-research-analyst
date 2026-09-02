import { useState, useCallback } from "react";
import { generateResearch, ApiClientError } from "../api/client";
import { ResearchReport } from "../api/types";

export function useResearchReport() {
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | undefined>(undefined);

  const fetchReport = useCallback(async (ticker: string) => {
    if (!ticker.trim()) return;

    setIsLoading(true);
    setError(null);
    setErrorCode(undefined);

    try {
      const data = await generateResearch(ticker);
      setReport(data);
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setError(err.message);
        setErrorCode(err.code);
      } else {
        setError(err?.message || "Failed to generate research report.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setReport(null);
    setError(null);
    setErrorCode(undefined);
    setIsLoading(false);
  }, []);

  return {
    report,
    isLoading,
    error,
    errorCode,
    fetchReport,
    reset,
  };
}