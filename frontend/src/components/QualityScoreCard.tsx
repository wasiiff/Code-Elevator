import type { ReviewResponse } from "../types/review";
import { asArray } from "../utils/arrays";

function scoreColor(score: number): string {
  if (score >= 80) return "bg-teal-500 text-slate-950";
  if (score >= 60) return "bg-sky-500 text-slate-950";
  if (score >= 40) return "bg-amber-400 text-slate-950";
  return "bg-rose-500 text-white";
}

interface Props {
  review: ReviewResponse;
}

export default function QualityScoreCard({ review }: Props) {
  const strategyPlan = asArray<string>(review?.strategy_plan);

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-start gap-4">
        <div
          className={`flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-2xl ${scoreColor(review.quality_score)}`}
        >
          <span className="text-2xl font-bold leading-none">{review.quality_score}</span>
          <span className="text-[10px] font-medium uppercase tracking-wide">Score</span>
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-semibold text-white">Quality Overview</h2>
          <p className="mt-1 text-sm leading-relaxed text-slate-300">
            {review.executive_summary}
          </p>
        </div>
      </div>
      <div className="mt-4 border-t border-slate-800 pt-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-teal-400">
          Strategy Plan
        </h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {strategyPlan.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
