import type {
  ChatRequest,
  ChatResponse,
  ChatTurn,
  SessionHistoryItem,
  StrategyVariant,
} from "../types/chat";

// Defaults to local dev backend; set VITE_API_BASE_URL to point at a
// deployed (Render) backend later without touching this code.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function sendChatMessage(
  scenarioId: string,
  message: string,
  turnNumber: number,
  history: ChatTurn[],
  variant: StrategyVariant,
): Promise<ChatResponse> {
  const body: ChatRequest = {
    scenario_id: scenarioId,
    message,
    turn_number: turnNumber,
    history,
    variant,
  };

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    // FastAPI's HTTPException(detail=...) — e.g. a 502 from a broken
    // agent call — is worth surfacing verbatim rather than a generic
    // status text (helps a lot when debugging a missing API key).
    const detail = await res
      .json()
      .then((data) => data?.detail as string | undefined)
      .catch(() => undefined);
    throw new Error(
      detail ?? `Chat request failed: ${res.status} ${res.statusText}`,
    );
  }

  return res.json();
}

export async function fetchSessionHistory(
  scenarioId?: string,
): Promise<SessionHistoryItem[]> {
  const url = new URL(`${API_BASE_URL}/sessions`);
  if (scenarioId) {
    url.searchParams.set("scenario_id", scenarioId);
  }

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(
      `Failed to load session history: ${res.status} ${res.statusText}`,
    );
  }

  return res.json();
}
