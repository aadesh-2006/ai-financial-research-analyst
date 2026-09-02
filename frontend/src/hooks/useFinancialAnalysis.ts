import { useState, useEffect, useCallback } from "react";
import { analyzeCompany, checkHealth, ApiClientError } from "../api/client";
import { AnalyzeResponse } from "../api/types";

export function useFinancialAnalysis() {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | undefined>(undefined);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  // Check health on mount
  useEffect(() => {
    let isMounted = true;
    checkHealth()
      .then(() => {
        if (isMounted) setIsBackendHealthy(true);
      })
      .catch(() => {
        if (isMounted) setIsBackendHealthy(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const analyze = useCallback(async (ticker: string) => {
    if (!ticker.trim()) return;

    setIsLoading(true);
    setError(null);
    setErrorCode(undefined);

    try {
      const data = await analyzeCompany(ticker);
      setAnalysis(data);
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        setError(err.message);
        setErrorCode(err.code);
      } else {
        setError(err?.message || "An unexpected error occurred.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setErrorCode(undefined);
  }, []);

  return {
    analysis,
    isLoading,
    error,
    errorCode,
    isBackendHealthy,
    analyze,
    clearError,
  };
}