"""The per-turn negotiation pipeline: phase -> classify -> tactic -> LLM
reply -> session-end check -> score.

Extracted out of main.py's /chat route so it has no DB/HTTP dependency —
a plain function of (persona, message, turn_number, history). This lets
two very different callers share one source of truth for "what happens
on a negotiation turn": the real /chat route (one turn per HTTP request,
DB session from FastAPI's Depends) and eval/run_simulation.py's synthetic
session loop (many turns in a tight in-process loop, no HTTP round-trip
per turn — essential for running 50-100+ simulated sessions in
reasonable time). Persistence is deliberately NOT done here — callers
decide where a finished session's score gets saved (main.py saves to the
human-facing `sessions` table; eval/ saves to `simulated_sessions`).
"""

from dataclasses import dataclass

from app.agent import generate_reply
from app.classifier import classify_message
from app.classifier.models import DetectedSignal
from app.personas.models import PersonaInternal, PersonaPublic
from app.schemas import ChatTurn
from app.scoring.models import SessionScore
from app.scoring.outcome_detection import check_session_end
from app.scoring.scorer import compute_session_score
from app.strategies.default import phase_for_turn, select_tactic
from app.strategies.models import Phase, Tactic


@dataclass
class ChatTurnResult:
    reply: str
    persona_public: PersonaPublic
    phase: Phase
    tactic: Tactic
    detected_signals: list[DetectedSignal]
    # Populated only on the turn that ends the session — see
    # app/scoring/. None while the negotiation is still ongoing.
    session_score: SessionScore | None


def run_chat_turn(
    persona: PersonaInternal,
    message: str,
    turn_number: int,
    history: list[ChatTurn],
) -> ChatTurnResult:
    """Runs one negotiation turn. Raises AgentError (from app.agent) if
    the LLM call fails — callers turn that into whatever's appropriate
    for their context (main.py: HTTP 502; eval/: let the batch fail
    loudly rather than silently record a bad session)."""
    phase = phase_for_turn(turn_number)
    # Classification has to run before tactic selection — select_tactic
    # reacts to detected_signals (escalates on unforced concession /
    # premature agreement, eases off if the user is holding firm).
    detected_signals = classify_message(message)
    tactic = select_tactic(persona, phase, detected_signals)

    reply = generate_reply(
        persona=persona,
        phase=phase,
        tactic=tactic,
        detected_signals=detected_signals,
        message=message,
        history=history,
    )

    # Session-end detection only looks at this exchange (stateless — an
    # earlier turn would already have ended the session if it qualified).
    # Scoring, if the session did end here, needs the whole transcript.
    outcome = check_session_end(message, reply, turn_number)
    session_score: SessionScore | None = None
    if outcome is not None:
        transcript = [
            *history,
            ChatTurn(role="user", text=message),
            ChatTurn(role="assistant", text=reply),
        ]
        session_score = compute_session_score(persona, transcript, outcome)

    return ChatTurnResult(
        reply=reply,
        persona_public=persona.to_public(),
        phase=phase,
        tactic=tactic,
        detected_signals=detected_signals,
        session_score=session_score,
    )
