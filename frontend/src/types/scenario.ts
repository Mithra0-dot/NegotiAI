export type Difficulty = "Easy" | "Medium" | "Hard";

/**
 * Static display shape for the scenario picker. This mirrors the shape a
 * future `/scenarios` API response will have, so ScenarioPicker/ScenarioCard
 * can be pointed at the backend later without changing their props.
 *
 * Full persona/goal/constraint config (target & walk-away values, opening
 * tactic, etc.) belongs in the backend's `personas/` configs once the
 * negotiation agent feature is built — this type only carries what the
 * picker card needs to display.
 */
export interface Scenario {
  id: string;
  name: string;
  /** 1-2 line persona blurb shown on the card. */
  blurb: string;
  difficulty: Difficulty;
  /** Short hint at the opponent's negotiating style, e.g. "Data-driven, cites market rates". */
  opponentStyleHint: string;
}
