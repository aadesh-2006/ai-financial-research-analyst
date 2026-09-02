/**
 * TypeScript definitions strictly aligned with FastAPI backend Pydantic schemas.
 */

export interface HealthResponse {
  status: string;
  service: string;
}

export interface Metric {
  value: number | null;
  unit: "percentage" | "ratio" | "multiple" | "currency" | "index" | string;
  formula: string;
  source_fields: string[];
  status: "available" | "unavailable" | "not_applicable" | string;
  warning: string | null;
}

export interface FinancialTrend {
  fiscal_year: number;
  revenue: number | null;
  revenue_growth: number | null;
  operating_income: number | null;
  operating_margin: number | null;
  net_income: number | null;
  net_margin: number | null;
  operating_cash_flow: number | null;
  free_cash_flow: number | null;
  fcf_margin: number | null;
}

export interface GrowthAnalysis {
  revenue_growth_yoy: number | null;
  revenue_cagr_3yr: number | null;
  net_income_growth_yoy: number | null;
  fcf_growth_yoy: number | null;
  revenue_growth_series: Array<{ year: number; growth: number | null }>;
  net_income_growth_series: Array<{ year: number; growth: number | null }>;
  fcf_growth_series: Array<{ year: number; growth: number | null }>;
  metrics?: Record<string, Metric>;
}

export interface ProfitabilityAnalysis {
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  roe: number | null;
  roic: number | null;
  metrics?: Record<string, Metric>;
}

export interface LeverageAnalysis {
  debt_to_equity: number | null;
  debt_to_ebitda: number | null;
  interest_coverage: number | null;
  total_debt: number | null;
  stockholders_equity: number | null;
  metrics?: Record<string, Metric>;
}

export interface CashFlowAnalysis {
  operating_cash_flow: number | null;
  capex: number | null;
  free_cash_flow: number | null;
  fcf_margin: number | null;
  fcf_conversion: number | null;
  metrics?: Record<string, Metric>;
}

export interface ValuationMetrics {
  pe_ratio: number | null;
  forward_pe: number | null;
  ev_to_ebitda: number | null;
  price_to_sales: number | null;
  price_to_fcf: number | null;
  market_cap: number | null;
  enterprise_value: number | null;
  price_to_book?: number | null;
  metrics?: Record<string, Metric>;
}

export interface DCFProjection {
  year: number;
  projected_fcf: number;
  discount_factor: number;
  present_value: number;
}

export interface SensitivityCell {
  wacc: number;
  terminal_growth: number;
  implied_share_price: number | null;
  upside_pct: number | null;
}

export interface SensitivityTable {
  wacc_range: number[];
  growth_range: number[];
  cells: SensitivityCell[];
}

export interface DCFValuation {
  ticker: string;
  status: "calculated" | "not_applicable" | "insufficient_data" | "error" | string;
  risk_free_rate?: number | null;
  beta?: number | null;
  equity_risk_premium?: number;
  cost_of_equity?: number | null;
  pre_tax_cost_of_debt?: number | null;
  tax_rate?: number;
  after_tax_cost_of_debt?: number | null;
  market_value_equity?: number | null;
  market_value_debt?: number | null;
  equity_weight?: number | null;
  debt_weight?: number | null;
  wacc?: number | null;
  fcf_growth_assumption?: number | null;
  terminal_growth_rate?: number;
  projections?: DCFProjection[];
  pv_explicit_fcf?: number | null;
  terminal_value?: number | null;
  pv_terminal_value?: number | null;
  enterprise_value?: number | null;
  cash?: number | null;
  total_debt?: number | null;
  net_debt?: number | null;
  equity_value?: number | null;
  shares_outstanding?: number | null;
  current_share_price?: number | null;
  implied_share_price?: number | null;
  upside_downside_pct?: number | null;
  sensitivity_table?: SensitivityTable | null;
  warnings?: string[];
}

export interface FinancialHealth {
  overall: "Strong" | "Moderate" | "Cautious" | string;
  growth_pillar: string;
  profitability_pillar: string;
  leverage_pillar: string;
  cash_flow_pillar: string;
  key_observations: string[];
}

export interface AnalyzeResponse {
  ticker: string;
  company_name: string;
  sector: string | null;
  industry: string | null;
  currency: string;
  description: string | null;
  website: string | null;
  growth: GrowthAnalysis;
  profitability: ProfitabilityAnalysis;
  leverage: LeverageAnalysis;
  cash_flow: CashFlowAnalysis;
  valuation: ValuationMetrics;
  dcf: DCFValuation | null;
  historical_trends: FinancialTrend[];
  health: FinancialHealth;
  news?: Array<{ headline: string; source?: string | null; url?: string | null; published_at?: string | null }>;
  warnings: string[];
  analyzed_at: string;
}

export interface ResearchSource {
  provider: string;
  title: string;
  url: string | null;
  published_at?: string | null;
  source_type: "filing" | "market_data" | "news" | "valuation_model" | string;
}

export interface FinancialSnapshot {
  summary: string;
  key_points: string[];
  revenue_growth_yoy_pct?: number | null;
  operating_margin_pct?: number | null;
  net_margin_pct?: number | null;
  free_cash_flow?: number | null;
}

export interface ValuationAssessment {
  summary: string;
  multiples_summary: string;
  key_points: string[];
  current_share_price?: number | null;
  pe_ratio?: number | null;
  forward_pe?: number | null;
  price_to_sales?: number | null;
  ev_to_ebitda?: number | null;
  price_to_book?: number | null;
}

export interface FinancialHealthAssessment {
  summary: string;
  overall_rating: string;
  observations: string[];
}

export interface DCFInterpretation {
  summary: string;
  valuation_signal: string;
  sensitivity_observation: string;
  model_wacc_pct?: number | null;
  model_terminal_growth_pct?: number | null;
  model_implied_share_price?: number | null;
  model_upside_downside_pct?: number | null;
}

export interface NewsMarketContext {
  summary: string;
  relevant_headlines: string[];
}

export interface ReportConfidence {
  level: "High" | "Medium" | "Cautious" | string;
  rationale: string;
}

export interface ResearchReport {
  ticker: string;
  company_name: string;
  generated_at: string;
  executive_summary: string;
  investment_thesis: string;
  financial_snapshot: FinancialSnapshot;
  valuation_assessment: ValuationAssessment;
  strengths: string[];
  risks: string[];
  catalysts: string[];
  concerns: string[];
  financial_health_assessment: FinancialHealthAssessment;
  dcf_interpretation: DCFInterpretation;
  news_and_market_context: NewsMarketContext;
  conclusion: string;
  confidence: ReportConfidence;
  limitations: string[];
  sources: ResearchSource[];
  disclaimer: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: any;
}

export interface ErrorResponse {
  error: ErrorDetail;
}