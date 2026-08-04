export type Severity = "Critical" | "High" | "Medium" | "Low";

export interface Finding {
  category: string;
  severity: Severity;
  location: string;
  description: string;
  impact: string;
}

export interface ReviewRequest {
  programming_language: string;
  source_code: string;
}

export interface ReviewResponse {
  id: string;
  programming_language: string;
  source_code: string;
  strategy_plan: string[];
  findings: Finding[];
  refactored_code: string;
  quality_score: number;
  executive_summary: string;
  created_at: string;
}
