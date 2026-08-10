import type { ChatRequest, ChatResponse } from "../types/chat";

// Defaults to local dev backend; set VITE_API_BASE_URL to point at a
// deployed (Render) backend later without touching this code.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function sendChatMessage(
  scenarioId: string,
  message: string,
): Promise<ChatResponse> {
  const body: ChatRequest = { scenario_id: scenarioId, message };

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}
