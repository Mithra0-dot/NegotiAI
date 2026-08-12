"""Shared vocabulary for the strategy layer: negotiation phase and tactic.

Lives separately from `personas/` (see CLAUDE.md: "Keep agent
persona/strategy configs in dedicated files, e.g. personas/, strategies/")
so a persona's identity stays independent of the strategy/policy applied
to it — the eventual goal is to A/B test different strategy variants
against the *same* set of personas.
"""

from enum import Enum


class Phase(str, Enum):
    """Where the negotiation currently is. Advances purely on turn count
    for this pass — no message-content analysis yet (that's the
    concession-signal classifier, a later pass)."""

    OPENING = "opening"
    PROBING = "probing"
    BARGAINING = "bargaining"
    CLOSING = "closing"


class Tactic(str, Enum):
    """The tactic the agent leans on for a given phase."""

    ANCHORING = "anchoring"
    SILENCE = "silence"
    DEADLINE_PRESSURE = "deadline_pressure"
    GOOD_COP_BAD_COP = "good_cop_bad_cop"


class StrategyVariant(str, Enum):
    """Which tactic-selection policy is in play — the axis the simulated
    A/B testing infra (eval/) compares. Not to be confused with
    eval.user_types.UserType, which describes the *simulated user's*
    behavior, not the agent's strategy; kept named distinctly (HARDLINE,
    not e.g. AGGRESSIVE) to avoid the two being confused with each other
    in CLI args/logs. See app/strategies/registry.py for the mapping from
    each variant to its select_tactic() implementation."""

    DEFAULT = "default"
    HARDLINE = "hardline"
