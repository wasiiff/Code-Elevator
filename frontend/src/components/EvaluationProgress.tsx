import { useEffect, useState } from "react";
import type { ProgressEvent } from "../services/api";

type Stage = ProgressEvent["stage"];

const STEPS: { key: Stage; label: string; hint: string }[] = [
  { key: "analyzing", label: "Analyzing code", hint: "Planning the review and finding issues" },
  { key: "refactoring", label: "Refactoring & scoring", hint: "Rewriting the code and rating it" },
  { key: "saving", label: "Saving review", hint: "Storing the result" },
];

const ORDER: Stage[] = ["analyzing", "refactoring", "saving", "done"];

export default function EvaluationProgress({
  stage,
  findingsCount,
}: {
  stage: Stage;
  findingsCount: number | null;
}) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = window.setInterval(() => {
      setElapsed(Math.floor((Date.now() - started) / 1000));
    }, 1000);
    return () => window.clearInterval(id);
  }, []);

  const currentIndex = ORDER.indexOf(stage);

  return (
    <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-slate-200">Evaluating…</h2>
        <span className="font-mono text-xs text-slate-500">{elapsed}s</span>
      </div>

      <ol className="space-y-3">
        {STEPS.map((step, i) => {
          const index = ORDER.indexOf(step.key);
          const done = currentIndex > index;
          const active = currentIndex === index;
          return (
            <li key={step.key} className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-semibold ${
                  done
                    ? "border-teal-500 bg-teal-500 text-slate-950"
                    : active
                      ? "border-teal-500 text-teal-400"
                      : "border-slate-700 text-slate-600"
                }`}
                aria-hidden="true"
              >
                {done ? "✓" : active ? (
                  <span className="h-2 w-2 animate-pulse rounded-full bg-teal-400" />
                ) : (
                  i + 1
                )}
              </span>
              <div className="min-w-0">
                <p
                  className={`text-sm font-medium ${
                    done ? "text-slate-400" : active ? "text-white" : "text-slate-600"
                  }`}
                >
                  {step.label}
                  {step.key === "analyzing" && findingsCount !== null && (
                    <span className="ml-2 text-xs font-normal text-teal-400">
                      {findingsCount} issue{findingsCount === 1 ? "" : "s"} found
                    </span>
                  )}
                </p>
                {active && <p className="text-xs text-slate-500">{step.hint}</p>}
              </div>
            </li>
          );
        })}
      </ol>

      <p className="mt-4 text-xs text-slate-600">
        A full review runs two AI passes and usually takes 20–40 seconds.
      </p>
    </div>
  );
}
