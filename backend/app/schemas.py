"""Request/response models for the API.

Kept intentionally thin for this pass — just enough to describe the /chat
stub. Once the real negotiation agent lands, ChatResponse will grow fields
like detected tactics and phase.
"""

from pydantic import BaseModel

from app.personas.models import PersonaPublic


class ChatRequest(BaseModel):
    scenario_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    # Public-safe subset only (role, personality, opening tactic) — never
    # PersonaInternal, which carries goals/constraints (target/walk_away)
    # and would leak the opponent's BATNA to the client.
    persona: PersonaPublic
