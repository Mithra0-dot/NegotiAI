import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { scenarios } from "../data/scenarios";
import { sendChatMessage } from "../lib/api";
import type { ChatMessage } from "../types/chat";

export function ChatPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const scenario = scenarios.find((s) => s.id === scenarioId);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !scenarioId || isSending) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const { reply } = await sendChatMessage(scenarioId, text);
      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong sending your message.",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col px-6 py-8">
      <header className="mb-4">
        <Link to="/" className="text-sm text-slate-500 hover:text-slate-300">
          ← Back to scenarios
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-slate-100">
          {scenario ? scenario.name : "Unknown scenario"}
        </h1>
        {scenario && (
          <p className="mt-1 text-sm text-slate-400">{scenario.blurb}</p>
        )}
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Say something to start the negotiation. (Stub backend — replies
            aren't real yet.)
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
              msg.role === "user"
                ? "ml-auto bg-violet-600/80 text-white"
                : "bg-slate-800 text-slate-200"
            }`}
          >
            {msg.text}
          </div>
        ))}
        {isSending && (
          <div className="max-w-[80%] rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-400">
            …
          </div>
        )}
      </div>

      {error && (
        <p className="mt-2 text-sm text-rose-400">
          {error} — is the backend running on :8000?
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message…"
          disabled={isSending}
          className="flex-1 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
