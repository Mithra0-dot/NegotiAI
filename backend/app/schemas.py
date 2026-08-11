"""Request/response models for the API.

Kept intentionally thin for this pass — just enough to describe the /chat
stub. Once the real negotiation agent lands, ChatResponse will grow further
(scoring, etc).
"""

from pydantic import BaseModel

from app.classifier.models import DetectedSignal
from app.personas.models import PersonaPublic
from app.strategies.models import Phase, Tactic


class ChatRequest(BaseModel):
    scenario_id: str
    message: str
    # 1-indexed count of user messages sent so far in this negotiation,
    # including this one. Client-reported — there's no backend session
    # store yet (no DB), so the strategy state machine derives phase from
    # this instead of tracking it server-side. Not server-verified; fine
    # for a stub pass, revisit once real sessions/DB land.
    turn_number: int


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
    # app/classifier/). Observable only for now — not yet wired into
    # tactic selection or the (still-stub) reply text.
    detected_signals: list[DetectedSignal]
