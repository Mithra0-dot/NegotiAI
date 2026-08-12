import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { scenarios } from "../data/scenarios";
import { fetchSessionHistory } from "../lib/api";
import { ScoreTrendChart } from "../components/ScoreTrendChart";
import { OUTCOME_LABELS, statusTextClass } from "../lib/scoreDisplay";
import type { SessionHistoryItem } from "../types/chat";

function scenarioName(scenarioId: string): string {
  return scenarios.find((s) => s.id === scenarioId)?.name ?? scenarioId;
}

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function HistoryPage() {
  const [scenarioFilter, setScenarioFilter] = useState<string>("");
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    fetchSessionHistory(scenarioFilter || undefined)
      .then((data) => {
        if (!cancelled) setSessions(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Something went wrong loading session history.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [scenarioFilter]);

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <header className="mb-6">
        <Link to="/" className="text-sm text-slate-500 hover:text-slate-300">
          ← Back to scenarios
        </Link>
        <div className="mt-2 flex items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold text-slate-100">
            Session history
          </h1>
          <select
            value={scenarioFilter}
            onChange={(e) => setScenarioFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
          >
            <option value="">All scenarios</option>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </header>

      {error && (
        <p className="mb-4 text-sm text-rose-400">
          {error} — is the backend running on :8000?
        </p>
      )}

      {!isLoading && !error && sessions.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
          <p className="text-sm text-slate-500">
            No sessions yet — go negotiate!
          </p>
          <Link
            to="/"
            className="mt-3 inline-block text-sm text-violet-400 hover:text-violet-300"
          >
            Pick a scenario →
          </Link>
        </div>
      )}

      {sessions.length > 0 && (
        <>
          <div className="mb-6">
            <ScoreTrendChart sessions={sessions} />
          </div>

          <ul className="space-y-2">
            {sessions.map((session) => (
              <li
                key={session.id}
                className="flex items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4"
              >
                <div>
                  <p className="text-sm font-medium text-slate-200">
                    {scenarioName(session.scenario_id)}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {formatDateTime(session.created_at)}
                  </p>
                  <span className="mt-1.5 inline-flex items-center rounded-full bg-violet-500/15 px-2 py-0.5 text-[11px] font-medium text-violet-300 ring-1 ring-inset ring-violet-500/30">
                    {OUTCOME_LABELS[session.score.outcome]}
                  </span>
                </div>
                <p
                  className={`text-2xl font-semibold ${statusTextClass(session.score.overall_score)}`}
                >
                  {Math.round(session.score.overall_score)}
                </p>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
