"""FastAPI app.

/chat now runs the full pipeline: persona lookup, the rule-based
concession-signal classifier, the (now signal-adaptive) strategy state
machine, and a real LLM call (LangChain + Anthropic) for the reply.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import AgentError, generate_reply
from app.classifier import classify_message
from app.personas import get_persona
from app.schemas import ChatRequest, ChatResponse
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

    return ChatResponse(
        reply=reply,
        persona=persona.to_public(),
        phase=phase,
        tactic=tactic,
        detected_signals=detected_signals,
    )
