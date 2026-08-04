import axios from "axios";
import type { ReviewRequest, ReviewResponse } from "../types/review";
import { asArray } from "../utils/arrays";
import { normalizeReviewResponse } from "../utils/normalizeReview";

const BASE = "/api/v1/reviews";

export async function createReview(payload: ReviewRequest): Promise<ReviewResponse> {
  const { data } = await axios.post<Partial<ReviewResponse>>(BASE, payload);
  return normalizeReviewResponse(data);
}

export interface ProgressEvent {
  stage: "analyzing" | "refactoring" | "saving" | "done" | "error";
  findings_count?: number;
  strategy_count?: number;
  detail?: string;
  review?: Partial<ReviewResponse>;
}

/**
 * Run a review over the NDJSON progress stream, invoking `onProgress` as each
 * pipeline stage starts. Falls back to nothing special on the caller's side —
 * the resolved value matches createReview().
 */
export async function createReviewStreaming(
  payload: ReviewRequest,
  onProgress: (event: ProgressEvent) => void,
): Promise<ReviewResponse> {
  const res = await fetch(`${BASE}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* non-JSON error body — keep the status-code message */
    }
    throw new Error(detail);
  }
  if (!res.body) throw new Error("Streaming is not supported by this browser.");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: ReviewResponse | null = null;

  const handleLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    const event: ProgressEvent = JSON.parse(trimmed);
    if (event.stage === "error") throw new Error(event.detail ?? "Evaluation failed.");
    if (event.stage === "done") result = normalizeReviewResponse(event.review);
    onProgress(event);
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) handleLine(line);
  }
  handleLine(buffer);

  if (!result) throw new Error("Stream ended before a result arrived.");
  return result;
}

export async function listReviews(): Promise<ReviewResponse[]> {
  const { data } = await axios.get<Partial<ReviewResponse>[] | null>(BASE);
  return asArray<Partial<ReviewResponse>>(data).map(normalizeReviewResponse);
}

export async function getReview(id: string): Promise<ReviewResponse> {
  const { data } = await axios.get<Partial<ReviewResponse>>(`${BASE}/${id}`);
  return normalizeReviewResponse(data);
}
