import { AnalyzeResponse, ErrorResponse, HealthResponse, ResearchReport } from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(status: number, code: string, message: string, details?: any) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(options.headers || {}),
      },
    });

    if (!response.ok) {
      let errorCode = "UNKNOWN_ERROR";
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
      let details: any = null;

      try {
        const errorJson: ErrorResponse = await response.json();
        if (errorJson?.error) {
          errorCode = errorJson.error.code || errorCode;
          errorMessage = errorJson.error.message || errorMessage;
          details = errorJson.error.details;
        }
      } catch {
        // Response was not JSON
      }

      throw new ApiClientError(response.status, errorCode, errorMessage, details);
    }

    return (await response.json()) as T;
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new ApiClientError(504, "CLIENT_TIMEOUT", "Request timed out after 60 seconds.");
    }
    if (err instanceof ApiClientError) {
      throw err;
    }
    throw new ApiClientError(
      0,
      "NETWORK_ERROR",
      `Unable to connect to backend server at ${API_BASE_URL}. Ensure FastAPI is running.`
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health", { method: "GET" });
}

export async function analyzeCompany(ticker: string): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ ticker: ticker.trim().toUpperCase() }),
  });
}

export async function generateResearch(ticker: string): Promise<ResearchReport> {
  return request<ResearchReport>("/api/research", {
    method: "POST",
    body: JSON.stringify({ ticker: ticker.trim().toUpperCase() }),
  });
}