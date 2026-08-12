"""FastAPI app.

/chat runs the full per-turn pipeline via app/chat_pipeline.py (persona
lookup happens here; phase/classifier/tactic/LLM reply/scoring happen in
run_chat_turn), then does best-effort persistence of the finished session
(see app/history/). The same run_chat_turn() also powers eval/'s
synthetic-session simulator — see app/chat_pipeline.py's docstring for
why that logic lives outside this route.
"""

import logging
from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSession

from app.agent import AgentError
from app.chat_pipeline import run_chat_turn
from app.db import get_db, init_db
from app.history.repository import list_sessions, save_session
from app.history.schemas import SessionHistoryItem
from app.personas import get_persona
from app.schemas import ChatRequest, ChatResponse
from app.scoring.models import SessionScore
from eval.router import router as eval_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Iterator[None]:
    init_db()
    yield


app = FastAPI(title="NegotiAI API", lifespan=lifespan)

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
def chat(request: ChatRequest, db: DBSession = Depends(get_db)) -> ChatResponse:
    persona = get_persona(request.scenario_id)
    if persona is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario_id: {request.scenario_id!r}",
        )

    try:
        result = run_chat_turn(
            persona, request.message, request.turn_number, request.history
        )
    except AgentError as exc:
        # Surface as a clear failure, never a silent fallback to stub
        # text — a broken agent call should look broken, not like a
        # bland-but-real reply.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if result.session_score is not None:
        # Best-effort persistence: log and continue on failure rather than
        # raising. The negotiation reply + score already succeeded and are
        # meaningful on their own — a broken DB write shouldn't take that
        # down (contrast with the LLM call above, which does propagate,
        # because there the reply genuinely doesn't exist without it).
        try:
            save_session(db, request.scenario_id, result.session_score)
        except Exception:
            logger.exception(
                "Failed to persist session history for scenario_id=%r",
                request.scenario_id,
            )

    return ChatResponse(
        reply=result.reply,
        persona=result.persona_public,
        phase=result.phase,
        tactic=result.tactic,
        detected_signals=result.detected_signals,
        session_score=result.session_score,
    )


@app.get("/sessions")
def get_sessions(
    scenario_id: str | None = None,
    limit: int = 50,
    db: DBSession = Depends(get_db),
) -> list[SessionHistoryItem]:
    records = list_sessions(db, scenario_id=scenario_id, limit=limit)
    return [
        SessionHistoryItem(
            id=record.id,
            scenario_id=record.scenario_id,
            created_at=record.created_at,
            score=SessionScore(**record.score_details),
        )
        for record in records
    ]


# Simulated A/B testing infra (see CLAUDE.md: "always frame this as
# 'simulated A/B test'"). Mounted unconditionally, same single-user local
# scope as the rest of the API — no auth. See eval/router.py.
app.include_router(eval_router)
