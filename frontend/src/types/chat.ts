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

export interface ChatRequest {
  scenario_id: string;
  message: string;
  /** 1-indexed count of user messages sent so far, including this one.
   * See backend/app/schemas.py's ChatRequest.turn_number docstring. */
  turn_number: number;
}

export interface ChatResponse {
  reply: string;
  phase: Phase;
  tactic: Tactic;
  detected_signals: DetectedSignal[];
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
