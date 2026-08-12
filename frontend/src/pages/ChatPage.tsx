import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { scenarios } from "../data/scenarios";
import { sendChatMessage } from "../lib/api";
import { SignalTag } from "../components/SignalTag";
import { Scorecard } from "../components/Scorecard";
import type { ChatMessage, ChatTurn, SessionScore } from "../types/chat";

export function ChatPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const scenario = scenarios.find((s) => s.id === scenarioId);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionScore, setSessionScore] = useState<SessionScore | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !scenarioId || isSending || sessionScore) return;

    const turnNumber = messages.filter((m) => m.role === "user").length + 1;
    // Index of the user message we're about to append — safe to compute
    // from the current `messages` length since sends are sequential (the
    // input is disabled while isSending, so there's never a second
    // in-flight message to confuse this with). Used below to attach
    // detected_signals to this exact message once the response arrives.
    const userMessageIndex = messages.length;
    // Prior turns as the LLM needs them — same pre-send snapshot as
    // turnNumber/userMessageIndex above, so it's exactly "everything sent
    // before this message" with nothing missing or duplicated.
    const history: ChatTurn[] = messages.map((m) => ({
      role: m.role,
      text: m.text,
    }));

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const { reply, phase, tactic, detected_signals, session_score } =
        await sendChatMessage(scenarioId, text, turnNumber, history);
      setMessages((prev) => {
        const next = [...prev];
        next[userMessageIndex] = {
          ...next[userMessageIndex],
          detectedSignals: detected_signals,
        };
        next.push({ role: "assistant", text: reply, phase, tactic });
        return next;
      });
      if (session_score) {
        setSessionScore(session_score);
      }
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

      {sessionScore && <Scorecard score={sessionScore} />}

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Say something to start the negotiation.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`max-w-[80%] ${msg.role === "user" ? "ml-auto" : ""}`}>
            <div
              className={`rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-violet-600/80 text-white"
                  : "bg-slate-800 text-slate-200"
              }`}
            >
              {msg.text}
            </div>
            {msg.role === "user" && !!msg.detectedSignals?.length && (
              // Live in-session tactic tagging (CLAUDE.md MVP feature #5):
              // concession-signal classifier results for this exact
              // message, attached the moment the /chat response resolves.
              <div className="mt-1 flex flex-wrap justify-end gap-1 px-1">
                {msg.detectedSignals.map((s) => (
                  <SignalTag key={s.signal_type} signalType={s.signal_type} />
                ))}
              </div>
            )}
            {msg.role === "assistant" && msg.phase && msg.tactic && (
              // Temporary dev caption proving the strategy state machine
              // ran — not the real "Live in-session tactic tagging" MVP
              // feature (which tags the user's messages, not the agent's).
              <p className="mt-1 px-1 text-xs text-slate-600">
                phase: {msg.phase} · tactic: {msg.tactic}
              </p>
            )}
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
          placeholder={sessionScore ? "Session ended" : "Type your message…"}
          disabled={isSending || !!sessionScore}
          className="flex-1 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isSending || !!sessionScore || !input.trim()}
          className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
