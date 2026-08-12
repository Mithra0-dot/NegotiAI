/** Mirrors backend/app/schemas.py — keep these in sync by hand for now. */

/** Mirrors backend/app/strategies/models.py's Phase enum. */
export type Phase = "opening" | "probing" | "bargaining" | "closing";

/** Mirrors backend/app/strategies/models.py's Tactic enum. */
export type Tactic =
  | "anchoring"
  | "silence"
  | "deadline_pressure"
  | "good_cop_bad_cop";

/** Mirrors backend/app/classifier/models.py's SignalType enum. */
export type SignalType =
  | "unforced_concession"
  | "hedging"
  | "urgency"
  | "premature_agreement";

/** Mirrors backend/app/classifier/models.py's DetectedSignal. */
export interface DetectedSignal {
  signal_type: SignalType;
  matched_phrases: string[];
}

/** Mirrors backend/app/schemas.py's ChatTurn. */
export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
}

export interface ChatRequest {
  scenario_id: string;
  message: string;
  /** 1-indexed count of user messages sent so far, including this one.
   * See backend/app/schemas.py's ChatRequest.turn_number docstring. */
  turn_number: number;
  /** Prior turns, oldest first, NOT including `message` above — sent so
   * the LLM has conversation continuity. See ChatRequest.history's
   * docstring in schemas.py. */
  history: ChatTurn[];
}

/** Mirrors backend/app/scoring/models.py's SessionOutcome enum. */
export type SessionOutcome =
  | "deal_reached"
  | "walked_away"
  | "turn_limit_reached";

/** Mirrors backend/app/scoring/models.py's AnchoringResult enum. */
export type AnchoringResult =
  | "user_anchored_first"
  | "agent_anchored_first"
  | "undetermined";

/** Mirrors backend/app/personas/models.py's Constraints, reused here for
 * the user's own target/walk-away range. */
export interface TargetRange {
  target: number;
  walk_away: number;
  unit: string;
}

/** Mirrors backend/app/scoring/models.py's SessionScore. Present on
 * ChatResponse only on the turn that ends the session. */
export interface SessionScore {
  outcome: SessionOutcome;
  anchoring_result: AnchoringResult;
  anchoring_score: number;
  concession_pacing_ratio: number;
  concession_pacing_score: number;
  batna_discipline_score: number | null;
  final_outcome_value: number | null;
  overall_score: number;
  notes: string[];
  user_target_range: TargetRange;
}

export interface ChatResponse {
  reply: string;
  phase: Phase;
  tactic: Tactic;
  detected_signals: DetectedSignal[];
  session_score: SessionScore | null;
}

/** One bubble in the chat transcript. Not persisted anywhere yet — lives
 * only in ChatPage's React state and is lost on refresh (no DB in this pass). */
export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  /** Only set on assistant messages — the strategy state machine's
   * selection for that turn, shown as a small debug caption. */
  phase?: Phase;
  tactic?: Tactic;
  /** Only set on user messages — the concession-signal classifier's
   * result for that message, shown as live tactic tags. */
  detectedSignals?: DetectedSignal[];
}
