import type { Finding, ReviewResponse } from "../types/review";
import { asArray } from "./arrays";

/** Normalize API/DB payloads so list fields are always iterable arrays. */
export function normalizeReviewResponse(
  data: Partial<ReviewResponse> | null | undefined,
): ReviewResponse {
  return {
    id: data?.id ?? "",
    programming_language: data?.programming_language ?? "Unknown",
    source_code: data?.source_code ?? "",
    strategy_plan: asArray<string>(data?.strategy_plan),
    findings: asArray<Finding>(data?.findings),
    refactored_code: data?.refactored_code ?? "",
    quality_score: data?.quality_score ?? 0,
    executive_summary: data?.executive_summary ?? "",
    created_at: data?.created_at ?? new Date().toISOString(),
  };
}

/** Always returns an array — safe for UI iteration even when the API returns null/undefined. */
export function getAllReviewFindings(
  review: Partial<ReviewResponse> | null | undefined,
): Finding[] {
  return asArray<Finding>(review?.findings);
}
