export type VerificationMode = 'QUICK_CHECK' | 'DEEP_CHECK';

export type ClaimVolatility = 'HIGH' | 'MEDIUM' | 'LOW';

export type ClaimStatus =
  | 'LIKELY_CURRENT'
  | 'POTENTIALLY_STALE'
  | 'CONFLICTING_EVIDENCE'
  | 'UNVERIFIED'
  | 'NOT_TIME_SENSITIVE';

export type VerificationStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL' | 'FAILED';

export interface Source {
  id: string;
  title: string;
  url: string;
  domain: string;
  snippet: string;
  published_date?: string | null;
  relevance_score: number;
  credibility_heuristic: 'HIGH' | 'MEDIUM' | 'LOW';
  supports_claim?: boolean | null;
}

export interface ClaimEvaluation {
  id: string;
  claim_text: string;
  claim_type: string;
  volatility: ClaimVolatility;
  status: ClaimStatus;
  freshness_score: number;
  confidence_score: number;
  temporal_risk_score: number;
  recheck_interval_days: number;
  last_checked_at?: string;
  search_query: string;
  explanation: string;
  evidence_summary: string;
  sources: Source[];
}

export interface VerificationResponse {
  run_id: string;
  original_answer: string;
  question?: string | null;
  mode: VerificationMode;
  status: VerificationStatus;
  overall_score: number;
  confidence_score: number;
  overall_temporal_risk: number;
  total_claims: number;
  likely_current_count: number;
  potentially_stale_count: number;
  conflicting_count: number;
  unverified_count: number;
  not_time_sensitive_count: number;
  report_summary: string;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
  claims: ClaimEvaluation[];
}

export interface HistoryItem {
  id: string;
  question?: string | null;
  original_answer_snippet: string;
  mode: string;
  status: string;
  overall_score: number;
  confidence_score: number;
  overall_temporal_risk?: number;
  total_claims: number;
  potentially_stale_count: number;
  conflicting_count: number;
  created_at: string;
}

export interface ClaimDiff {
  claim_text: string;
  status_a: string;
  status_b: string;
  freshness_a: number;
  freshness_b: number;
  temporal_risk_a: number;
  temporal_risk_b: number;
  sources_count_a: number;
  sources_count_b: number;
  status_changed: boolean;
  risk_delta: number;
}

export interface ComparisonResult {
  run_a_id: string;
  run_b_id: string;
  created_at_a: string;
  created_at_b: string;
  overall_score_a: number;
  overall_score_b: number;
  score_delta: number;
  temporal_risk_a: number;
  temporal_risk_b: number;
  risk_delta: number;
  claims_diff: ClaimDiff[];
  summary: string;
}

export interface HealthInfo {
  status: string;
  app_name: string;
  version: string;
  database_connected: boolean;
  providers: {
    bifrost: {
      configured: boolean;
      base_url: string;
      model: string;
      provider: string;
    };
    tavily: {
      configured: boolean;
      base_url: string;
    };
  };
}
