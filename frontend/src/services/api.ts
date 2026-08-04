import axios from "axios";
import type { ReviewRequest, ReviewResponse } from "../types/review";
import { asArray } from "../utils/arrays";
import { normalizeReviewResponse } from "../utils/normalizeReview";

const BASE = "/api/v1/reviews";

export async function createReview(payload: ReviewRequest): Promise<ReviewResponse> {
  const { data } = await axios.post<Partial<ReviewResponse>>(BASE, payload);
  return normalizeReviewResponse(data);
}

export async function listReviews(): Promise<ReviewResponse[]> {
  const { data } = await axios.get<Partial<ReviewResponse>[] | null>(BASE);
  return asArray<Partial<ReviewResponse>>(data).map(normalizeReviewResponse);
}

export async function getReview(id: string): Promise<ReviewResponse> {
  const { data } = await axios.get<Partial<ReviewResponse>>(`${BASE}/${id}`);
  return normalizeReviewResponse(data);
}
