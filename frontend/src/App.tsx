import { useState, type FormEvent } from "react";
import QualityScoreCard from "./components/QualityScoreCard";
import FindingsList from "./components/FindingsList";
import CodeComparison from "./components/CodeComparison";
import { createReview } from "./services/api";
import type { ReviewResponse } from "./types/review";
import { getAllReviewFindings } from "./utils/normalizeReview";

const LANGUAGES = [
  "Python",
  "JavaScript",
  "TypeScript",
  "Java",
  "C#",
  "Go",
  "Rust",
  "SQL",
];

export default function App() {
  const [language, setLanguage] = useState("Python");
  const [sourceCode, setSourceCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [review, setReview] = useState<ReviewResponse | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!sourceCode.trim()) {
      setError("Please paste source code to evaluate.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await createReview({
        programming_language: language,
        source_code: sourceCode,
      });
      setReview(result);
    } catch (err: unknown) {
      let msg = "Evaluation failed. Is the API running?";
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string | { msg?: string }[] } } };
        const detail = axiosErr.response?.data?.detail;
        if (typeof detail === "string") msg = detail;
        else if (Array.isArray(detail) && detail[0]?.msg) msg = detail[0].msg;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-teal-400">
          Intelligent Code Evaluation Assistant
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white md:text-4xl">
          Review. Refactor. Score.
        </h1>
        <p className="mt-2 max-w-2xl text-slate-400">
          Submit source code for an LCEL-powered security, performance, and clean-code
          evaluation with an AI refactor and quality score.
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"
      >
        <div className="flex flex-wrap gap-4">
          <label className="flex flex-col gap-1 text-sm text-slate-300">
            Language
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-teal-500"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="mt-4 flex flex-col gap-1 text-sm text-slate-300">
          Source Code
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            rows={12}
            placeholder="Paste code here..."
            className="rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-sm text-slate-100 outline-none focus:border-teal-500"
          />
        </label>
        {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Evaluating…
            </>
          ) : (
            "Run Evaluation"
          )}
        </button>
      </form>

      {review && (
        <div className="mt-8 space-y-6">
          <QualityScoreCard review={review} />
          <FindingsList findings={getAllReviewFindings(review)} />
          <CodeComparison
            original={review.source_code}
            refactored={review.refactored_code}
            language={review.programming_language}
          />
        </div>
      )}
    </div>
  );
}
