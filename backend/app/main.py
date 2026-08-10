"""FastAPI skeleton.

This is intentionally minimal: one health check and one stub /chat
endpoint that echoes the input back instead of calling an LLM. Real
persona/strategy logic, LangChain orchestration, and the concession-signal
classifier are later passes (see CLAUDE.md's MVP build order) — this pass
only proves the frontend <-> backend wiring works end-to-end.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.personas import get_persona
from app.schemas import ChatRequest, ChatResponse

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

    # Stub reply, deliberately labeled as such so it's never mistaken for
    # real negotiation-agent output. Embedding the persona's role here
    # makes it visible (without inspecting raw JSON) that the right
    # persona was loaded for the right scenario. Real agent logic
    # (persona-driven dialogue, strategy state machine, tactic selection)
    # comes in a later pass.
    reply = (
        f"[stub] ({persona.role_description}) Got your message: "
        f"{request.message!r}. Real agent logic comes in a later pass."
    )
    return ChatResponse(reply=reply, persona=persona.to_public())
