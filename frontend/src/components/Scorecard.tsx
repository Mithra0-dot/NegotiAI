import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { OutcomeRangeBar } from "./OutcomeRangeBar";
import type { SessionOutcome, SessionScore } from "../types/chat";

// Status colors, not categorical — each bar is a "how well did you do"
// quality signal, not a distinct series to tell apart from its neighbors
// (see the dataviz skill: "when a series means good/bad it wears status
// tokens"). Reusing the exact same three tokens DifficultyBadge already
// uses for Easy/Medium/Hard, so the scorecard reads as the same design
// system rather than introducing a new palette.
const ROW_LABEL_WIDTH = 160; // px — kept in sync with the manual BATNA row below

function statusColor(score: number): string {
  if (score >= 70) return "#10b981"; // emerald-500
  if (score >= 40) return "#f59e0b"; // amber-500
  return "#f43f5e"; // rose-500
}

function statusTextClass(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-rose-400";
}

const OUTCOME_LABELS: Record<SessionOutcome, string> = {
  deal_reached: "Deal reached",
  walked_away: "Walked away",
  turn_limit_reached: "Turn limit reached",
};

interface ScorecardProps {
  score: SessionScore;
}

export function Scorecard({ score }: ScorecardProps) {
  // BATNA discipline is deliberately NOT status-colored in a
  // Recharts row when null — it renders as its own muted row below
  // instead (see the plan: "never faked as 0"). Only include it here
  // when there's a real score to plot.
  const rows = [
    { label: "Anchoring effectiveness", value: score.anchoring_score },
    { label: "Concession pacing", value: score.concession_pacing_score },
    ...(score.batna_discipline_score !== null
      ? [{ label: "BATNA discipline", value: score.batna_discipline_score }]
      : []),
  ];

  return (
    <div className="mb-6 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Session complete
          </p>
          <span
            className={`mt-1 inline-flex items-center rounded-full bg-violet-500/15 px-2.5 py-0.5 text-xs font-medium text-violet-300 ring-1 ring-inset ring-violet-500/30`}
          >
            {OUTCOME_LABELS[score.outcome]}
          </span>
        </div>
        <div className="text-right">
          <p
            className={`text-5xl font-semibold ${statusTextClass(score.overall_score)}`}
          >
            {Math.round(score.overall_score)}
          </p>
          <p className="text-xs text-slate-500">overall score</p>
        </div>
      </div>

      <div className="mt-6" style={{ height: rows.length * 44 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={rows}
            margin={{ top: 0, right: 40, bottom: 0, left: 0 }}
          >
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis
              type="category"
              dataKey="label"
              width={ROW_LABEL_WIDTH}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "#cbd5e1", fontSize: 12 }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20} isAnimationActive={false}>
              {rows.map((row) => (
                <Cell key={row.label} fill={statusColor(row.value)} />
              ))}
              <LabelList
                dataKey="value"
                position="right"
                formatter={(label: unknown) => `${Math.round(Number(label))}`}
                fill="#e2e8f0"
                fontSize={12}
                fontWeight={600}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {score.batna_discipline_score === null && (
        <div className="flex items-center gap-3">
          <span
            className="shrink-0 text-right text-xs text-slate-400"
            style={{ width: ROW_LABEL_WIDTH }}
          >
            BATNA discipline
          </span>
          <div className="h-5 flex-1 rounded bg-slate-800" />
          <span className="w-10 shrink-0 text-right text-xs text-slate-600">
            N/A
          </span>
        </div>
      )}

      {score.notes.length > 0 && (
        <ul className="mt-3 space-y-1">
          {score.notes.map((note) => (
            <li key={note} className="text-xs text-slate-500">
              {note}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-5 border-t border-slate-800 pt-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">
          Outcome vs. your target
        </p>
        <OutcomeRangeBar
          target={score.user_target_range.target}
          walkAway={score.user_target_range.walk_away}
          finalValue={score.final_outcome_value}
          unit={score.user_target_range.unit}
        />
      </div>
    </div>
  );
}
