"""FastAPI app.

/chat runs the full pipeline: persona lookup, the rule-based
concession-signal classifier, the signal-adaptive strategy state machine,
a real LLM call (LangChain + Anthropic) for the reply, and finally
session-end detection + scoring (see app/scoring/).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import AgentError, generate_reply
from app.classifier import classify_message
from app.personas import get_persona
from app.schemas import ChatRequest, ChatResponse, ChatTurn
from app.scoring.models import SessionScore
from app.scoring.outcome_detection import check_session_end
from app.scoring.scorer import compute_session_score
from app.strategies.default import phase_for_turn, select_tactic

app = FastAPI(title="NegotiAI API")

# The Vite dev server runs on 5173 by default; both localhost and 127.0.0.1
# forms are allowed since browsers treat them as distinct origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    persona = get_persona(request.scenario_id)
    if persona is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario_id: {request.scenario_id!r}",
        )

    phase = phase_for_turn(request.turn_number)
    # Classification has to run before tactic selection now — select_tactic
    # reacts to detected_signals (escalates on unforced concession /
    # premature agreement, eases off if the user is holding firm).
    detected_signals = classify_message(request.message)
    tactic = select_tactic(persona, phase, detected_signals)

    try:
        reply = generate_reply(
            persona=persona,
            phase=phase,
            tactic=tactic,
            detected_signals=detected_signals,
            message=request.message,
            history=request.history,
        )
    except AgentError as exc:
        # Surface as a clear failure, never a silent fallback to stub
        # text — a broken agent call should look broken, not like a
        # bland-but-real reply.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Session-end detection only looks at this exchange (stateless — an
    # earlier turn would already have ended the session if it qualified).
    # Scoring, if the session did end here, needs the whole transcript.
    outcome = check_session_end(request.message, reply, request.turn_number)
    session_score: SessionScore | None = None
    if outcome is not None:
        transcript = [
            *request.history,
            ChatTurn(role="user", text=request.message),
            ChatTurn(role="assistant", text=reply),
        ]
        session_score = compute_session_score(persona, transcript, outcome)

    return ChatResponse(
        reply=reply,
        persona=persona.to_public(),
        phase=phase,
        tactic=tactic,
        detected_signals=detected_signals,
        session_score=session_score,
    )
