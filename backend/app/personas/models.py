"""Shared shape for negotiation-opponent persona configs.

Each scenario's persona lives in its own file in this package (see
CLAUDE.md: "Keep agent persona/strategy configs in dedicated files ...
needed for the eval suite and A/B variant comparison to diff cleanly").
This module only defines the shape; the data lives next to it, one
scenario per file.
"""

from pydantic import BaseModel


class Constraints(BaseModel):
    """Numeric negotiation boundaries for a persona.

    `target` is the persona's ideal outcome; `walk_away` is the point
    beyond which they'd rather end the negotiation than concede further.
    Whether `walk_away` is numerically above or below `target` depends on
    which side of the deal the persona is on (e.g. a hiring manager's
    walk_away is a ceiling they won't exceed; a landlord's walk_away is a
    floor they won't drop below) — see the comment in each scenario file.
    """

    target: float
    walk_away: float
    unit: str


class PersonaConfig(BaseModel):
    """Static negotiation-opponent config for one scenario.

    This is the source of truth for who the user is negotiating against.
    No dialogue logic reads this yet — that's a later pass (strategy
    state machine / real LLM calls). This pass only proves /chat can look
    up the right persona for a given scenario_id.
    """

    scenario_id: str
    role_description: str
    goals: list[str]
    constraints: Constraints
    personality_traits: list[str]
    opening_tactic: str
