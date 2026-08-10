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


class PersonaPublic(BaseModel):
    """The subset of a persona safe to send to the client.

    Deliberately excludes `goals` and `constraints` — both describe the
    persona's negotiating objectives and numeric limits (target/walk_away),
    which would hand the user the opponent's BATNA and defeat the point of
    the simulator. Only what a human opponent would visibly project
    (who they are, how they act, how they open) belongs here.
    """

    scenario_id: str
    role_description: str
    personality_traits: list[str]
    opening_tactic: str


class PersonaInternal(BaseModel):
    """Full negotiation-opponent config for one scenario — backend-only.

    This is the source of truth for who the user is negotiating against.
    No dialogue logic reads this yet — that's a later pass (strategy
    state machine / real LLM calls). `/chat` looks this up to pick the
    right persona per scenario_id, but must only ever serialize
    `.to_public()` into a client-facing response — never this class
    directly, since it carries `goals` and `constraints`.
    """

    scenario_id: str
    role_description: str
    goals: list[str]
    constraints: Constraints
    personality_traits: list[str]
    opening_tactic: str

    def to_public(self) -> PersonaPublic:
        return PersonaPublic(
            scenario_id=self.scenario_id,
            role_description=self.role_description,
            personality_traits=self.personality_traits,
            opening_tactic=self.opening_tactic,
        )
