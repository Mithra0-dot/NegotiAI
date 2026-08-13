"""Request/response models for the API.

Kept intentionally thin — just enough to describe /chat. ChatResponse will
grow further (scoring, etc) as later passes land.
"""

from typing import Literal

from pydantic import BaseModel

from app.classifier.models import DetectedSignal
from app.personas.models import PersonaPublic
from app.scoring.models import SessionScore
from app.strategies.models import Phase, StrategyVariant, Tactic


class ChatTurn(BaseModel):
    """One prior turn in the conversation, as the frontend already holds
    it. Sent as `history` on every /chat call so the LLM has continuity
    — there's no backend session store, so the frontend owns the
    transcript and resends it each time (no DB in this pass)."""

    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    scenario_id: str
    message: str
    # 1-indexed count of user messages sent so far in this negotiation,
    # including this one. Client-reported — there's no backend session
    # store yet (no DB), so the strategy state machine derives phase from
    # this instead of tracking it server-side. Not server-verified; fine
    # for a stub pass, revisit once real sessions/DB land.
    turn_number: int
    # Prior turns, oldest first, NOT including `message` above. Passed to
    # the LLM as conversation history so it doesn't contradict its own
    # earlier statements (its anchor number, prior concessions, etc).
    history: list[ChatTurn] = []
    # Which opponent difficulty/style preset to negotiate against — see
    # app/strategies/registry.py. Defaults to DEFAULT ("Standard" in the
    # UI) so this field is additive/backward-compatible with any caller
    # that doesn't send it.
    variant: StrategyVariant = StrategyVariant.DEFAULT


class ChatResponse(BaseModel):
    reply: str
    # Public-safe subset only (role, personality, opening tactic) — never
    # PersonaInternal, which carries goals/constraints (target/walk_away)
    # and would leak the opponent's BATNA to the client.
    persona: PersonaPublic
    # The strategy state machine's phase/tactic selection for this turn —
    # safe to expose (see PersonaPublic.opening_tactic_tag's docstring).
    phase: Phase
    tactic: Tactic
    # Concession signals detected in the user's message (rule-based, see
    # app/classifier/). Now feeds tactic selection (see
    # strategies/default.py's select_tactic) as well as being returned
    # here for the live tactic-tagging UI.
    detected_signals: list[DetectedSignal]
    # Populated only on the turn that ends the session (deal reached,
    # walk-away, or turn limit) — see app/scoring/. None while the
    # negotiation is still ongoing.
    session_score: SessionScore | None = None
