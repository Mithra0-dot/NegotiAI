"""Request/response models for the API.

Kept intentionally thin for this pass — just enough to describe the /chat
stub. Once the real negotiation agent lands, ChatResponse will grow fields
like detected tactics and phase.
"""

from pydantic import BaseModel

from app.personas.models import PersonaConfig


class ChatRequest(BaseModel):
    scenario_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    # TODO: this currently exposes the full persona, including
    # constraints (target/walk_away) — fine for this verification-only
    # pass, but it leaks the opponent's BATNA to the client. Before real
    # dialogue logic ships, split this into a public-safe view (role,
    # personality, opening tactic) and keep constraints internal-only.
    persona: PersonaConfig
