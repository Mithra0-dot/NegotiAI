import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SessionHistoryItem } from "../types/chat";

// Trend-over-time = a line chart (per the dataviz skill's form heuristic).
// Its color job here is "1 categorical" — a single consistent hue, not
// per-point status coloring — because the thing being encoded is "which
// series is this" (there's only one), not "is this point good or bad".
// Mixing in status colors per-point would conflate two different color
// jobs in one chart, which the skill's collision rule warns against.
// Status colors stay where they already live: Scorecard's bars and the
// outcome pills in HistoryPage's session list.
const LINE_COLOR = "#8b5cf6"; // violet-500 — same accent as the rest of the app

interface ScoreTrendChartProps {
  sessions: SessionHistoryItem[];
}

interface TrendPoint {
  createdAt: string;
  label: string;
  overallScore: number;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function ScoreTrendChart({ sessions }: ScoreTrendChartProps) {
  // GET /sessions returns newest-first; a trend chart reads left-to-right
  // as oldest-to-newest, so reverse it here rather than push that
  // assumption onto the API.
  const data: TrendPoint[] = [...sessions]
    .reverse()
    .map((session) => ({
      createdAt: session.created_at,
      label: formatDate(session.created_at),
      overallScore: session.score.overall_score,
    }));

  return (
    <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#64748b", fontSize: 11 }}
          />
          <YAxis
            domain={[0, 100]}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#64748b", fontSize: 11 }}
            width={36}
          />
          <Tooltip
            cursor={{ stroke: "#334155", strokeWidth: 1 }}
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: "#cbd5e1" }}
            formatter={(value: unknown) => [
              Math.round(Number(value)),
              "Overall score",
            ]}
          />
          <Line
            type="monotone"
            dataKey="overallScore"
            stroke={LINE_COLOR}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            dot={{ r: 4, fill: LINE_COLOR, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
