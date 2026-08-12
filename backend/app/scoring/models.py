"""Shape for session-end detection + scoring results.

See CLAUDE.md's "Post-session scorecard" MVP feature — this is the
scoring layer feeding the frontend's Scorecard component.
"""

from enum import Enum

from pydantic import BaseModel

from app.personas.models import Constraints


class SessionOutcome(str, Enum):
    DEAL_REACHED = "deal_reached"
    WALKED_AWAY = "walked_away"
    TURN_LIMIT_REACHED = "turn_limit_reached"


class AnchoringResult(str, Enum):
    USER_ANCHORED_FIRST = "user_anchored_first"
    AGENT_ANCHORED_FIRST = "agent_anchored_first"
    UNDETERMINED = "undetermined"


class SessionScore(BaseModel):
    outcome: SessionOutcome

    anchoring_result: AnchoringResult
    anchoring_score: float  # 0-100: 100 user-first, 0 agent-first, 50 undetermined

    # Fraction of the user's turns (this whole session) with at least one
    # UNFORCED_CONCESSION signal detected, and the score derived from it.
    concession_pacing_ratio: float  # 0-1
    concession_pacing_score: float  # 0-100, (1 - ratio) * 100

    # None unless outcome is DEAL_REACHED and a number could be extracted
    # from the transcript — see scorer.py's docstring for why this is a
    # best-effort heuristic, not a precise reading of the actual deal.
    batna_discipline_score: float | None
    final_outcome_value: float | None

    overall_score: float  # 0-100, mean of whichever sub-scores are available
    notes: list[str]  # human-readable caveats (e.g. "no numeric anchor found")

    # The user's own target/walk-away for this scenario (from
    # PersonaInternal.user_constraints) — surfaced so the frontend can
    # plot the final outcome against it. Safe to expose: it's the user's
    # own info, not the opponent's secret.
    user_target_range: Constraints
