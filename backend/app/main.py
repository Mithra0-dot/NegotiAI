"""FastAPI skeleton.

This is intentionally minimal: one health check and one stub /chat
endpoint that now runs persona lookup, the strategy state machine
(phase/tactic selection), and the rule-based concession-signal classifier
— but still doesn't call an LLM, the reply is a labeled stub. Real
dialogue generation and LangChain orchestration are later passes (see
CLAUDE.md's MVP build order).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    tactic = select_tactic(persona, phase)
    detected_signals = classify_message(request.message)

    # Stub reply, deliberately labeled as such so it's never mistaken for
    # real negotiation-agent output. Embedding the persona's role plus the
    # selected phase/tactic here makes the state machine's output visible
    # without inspecting raw JSON. detected_signals is intentionally NOT
    # reflected in the reply/tactic yet — wiring it into adaptive
    # difficulty is a later pass; for now it's observable-only, verified
    # via the response payload. Real dialogue generation also comes later.
    reply = (
        f"[stub] ({persona.role_description}) [{phase.value} / {tactic.value}] "
        f"Got your message: {request.message!r}. Real agent logic comes in a later pass."
    )
    return ChatResponse(
        reply=reply,
        persona=persona.to_public(),
        phase=phase,
        tactic=tactic,
        detected_signals=detected_signals,
    )
