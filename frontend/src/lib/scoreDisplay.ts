import type { SessionOutcome } from "../types/chat";

// Status colors, not categorical — a score is a "how well did you do"
// quality signal, not a distinct series to tell apart from its neighbors
// (see the dataviz skill: "when a series means good/bad it wears status
// tokens"). Reusing the exact same three tokens DifficultyBadge already
// uses for Easy/Medium/Hard, so every score display (Scorecard, History)
// reads as the same design system rather than each inventing its own.
//
// Shared between Scorecard.tsx and HistoryPage.tsx — this is what
// "reusing the same design tokens" concretely means, not just visually
// matching colors by eye.

export function statusColor(score: number): string {
  if (score >= 70) return "#10b981"; // emerald-500
  if (score >= 40) return "#f59e0b"; // amber-500
  return "#f43f5e"; // rose-500
}

export function statusTextClass(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-rose-400";
}

export const OUTCOME_LABELS: Record<SessionOutcome, string> = {
  deal_reached: "Deal reached",
  walked_away: "Walked away",
  turn_limit_reached: "Turn limit reached",
};
