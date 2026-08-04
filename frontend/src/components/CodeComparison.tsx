import { useState } from "react";

interface Props {
  original: string;
  refactored: string;
  language: string;
}

type Tab = "side" | "original" | "refactored";

export default function CodeComparison({ original, refactored, language }: Props) {
  const [tab, setTab] = useState<Tab>("side");
  const tabs: { id: Tab; label: string }[] = [
    { id: "side", label: "Side by Side" },
    { id: "original", label: "Original" },
    { id: "refactored", label: "Refactored" },
  ];

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-white">
          Code Comparison <span className="text-sm font-normal text-slate-400">({language})</span>
        </h2>
        <div className="flex gap-1 rounded-lg bg-slate-950 p-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                tab === t.id ? "bg-teal-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      <div className={`mt-4 grid gap-3 ${tab === "side" ? "md:grid-cols-2" : "grid-cols-1"}`}>
        {(tab === "side" || tab === "original") && <CodePane title="Original" code={original} />}
        {(tab === "side" || tab === "refactored") && (
          <CodePane title="AI Refactored" code={refactored} accent />
        )}
      </div>
    </section>
  );
}

function CodePane({ title, code, accent }: { title: string; code: string; accent?: boolean }) {
  return (
    <div className="min-w-0 overflow-hidden rounded-xl border border-slate-800">
      <div
        className={`px-3 py-2 text-xs font-semibold uppercase tracking-wide ${
          accent ? "bg-teal-950/60 text-teal-300" : "bg-slate-950 text-slate-400"
        }`}
      >
        {title}
      </div>
      <pre className="max-h-96 overflow-auto bg-slate-950/80 p-3 font-mono text-xs leading-relaxed text-slate-200">
        <code>{code}</code>
      </pre>
    </div>
  );
}
