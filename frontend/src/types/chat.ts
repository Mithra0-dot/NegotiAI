/** Mirrors backend/app/schemas.py — keep these in sync by hand for now. */
export interface ChatRequest {
  scenario_id: string;
  message: string;
}

export interface ChatResponse {
  reply: string;
}

/** One bubble in the chat transcript. Not persisted anywhere yet — lives
 * only in ChatPage's React state and is lost on refresh (no DB in this pass). */
export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}
