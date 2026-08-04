import type { Finding, Severity } from "../types/review";
import { asArray } from "../utils/arrays";

const SEVERITY_STYLES: Record<Severity, string> = {
  Critical: "bg-rose-500/20 text-rose-300 ring-rose-500/40",
  High: "bg-orange-500/20 text-orange-300 ring-orange-500/40",
  Medium: "bg-amber-500/20 text-amber-200 ring-amber-500/40",
  Low: "bg-sky-500/20 text-sky-300 ring-sky-500/40",
};

interface Props {
  findings: Finding[];
}

export default function FindingsList({ findings }: Props) {
  const safeFindings = asArray<Finding>(findings);

  if (!safeFindings.length) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 className="text-lg font-semibold text-white">Findings</h2>
        <p className="mt-2 text-sm text-slate-400">No issues detected.</p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="text-lg font-semibold text-white">
        Findings <span className="text-slate-400">({safeFindings.length})</span>
      </h2>
      <ul className="mt-4 space-y-3">
        {safeFindings.map((f, i) => (
          <li
            key={i}
            className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ${SEVERITY_STYLES[f.severity]}`}
              >
                {f.severity}
              </span>
              <span className="text-xs font-medium text-teal-400">{f.category}</span>
              <span className="text-xs text-slate-500">{f.location}</span>
            </div>
            <p className="mt-2 text-sm text-slate-200">{f.description}</p>
            <p className="mt-1 text-xs text-slate-400">
              <span className="font-medium text-slate-300">Impact:</span> {f.impact}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
