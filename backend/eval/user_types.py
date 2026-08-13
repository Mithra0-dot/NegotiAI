"""Behavioral profiles for simulated negotiation users.

Purely behavioral — *how* the simulated user negotiates, not *what* they
want (that comes from the scenario's own PersonaInternal.user_constraints,
see eval/simulated_user.py). Kept as data separate from the prompt-
building logic, same config-vs-logic split CLAUDE.md asks for elsewhere
(personas/, strategies/) — needed so a future 4th user type is a one-line
addition, not a prompt-string hunt.
"""

from enum import Enum


class UserType(str, Enum):
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"
    DATA_DRIVEN = "data_driven"


# Fed into the simulated user's system prompt (eval/simulated_user.py) to
# describe how this archetype communicates and negotiates. Written in
# second person to match how build_system_prompt() addresses the real
# agent — same convention, different file (see app/agent/prompts.py).
BEHAVIOR_INSTRUCTIONS: dict[UserType, str] = {
    UserType.AGGRESSIVE: (
        "You negotiate hard. Open assertively, resist conceding, and push "
        "back on offers that fall short of your target. Reference your "
        "leverage or alternatives when useful. You're willing to walk "
        "away rather than accept a bad deal — don't cave just to keep "
        "things friendly."
    ),
    UserType.PASSIVE: (
        "You avoid conflict and dislike prolonged back-and-forth. You "
        "concede ground readily, hedge your positions (\"I guess\", "
        "\"maybe\", \"if that works for you\"), and lean toward agreeing "
        "quickly rather than holding out for a better number."
    ),
    UserType.DATA_DRIVEN: (
        "You negotiate methodically, citing market data, comparable "
        "figures, or objective justification for your position rather "
        "than emotion or pressure. You're willing to move off your "
        "opening position when shown a reasonable counter-argument, but "
        "you expect the same rigor back before conceding."
    ),
}

# How readily each archetype moves toward closing the negotiation, used
# by eval/mock_user.py to weight the random turn-by-turn choice of when
# to emit a closing line, and mentioned in the real-LLM prompt so both
# paths point the same direction. accept_bias/walk_away_bias are relative
# weights (not probabilities) for "close now" vs "close by walking away"
# once a close is due; higher close_eagerness means closing tends to
# happen on an earlier turn.
class ClosingTendency:
    __slots__ = ("close_eagerness", "accept_bias", "walk_away_bias")

    def __init__(self, close_eagerness: float, accept_bias: float, walk_away_bias: float):
        self.close_eagerness = close_eagerness
        self.accept_bias = accept_bias
        self.walk_away_bias = walk_away_bias


CLOSING_TENDENCY: dict[UserType, ClosingTendency] = {
    # Holds out longer, and when it does close is more likely to walk
    # than fold.
    UserType.AGGRESSIVE: ClosingTendency(close_eagerness=0.7, accept_bias=0.4, walk_away_bias=0.6),
    # Closes early and almost always by accepting.
    UserType.PASSIVE: ClosingTendency(close_eagerness=1.4, accept_bias=0.85, walk_away_bias=0.15),
    # Middle ground on both timing and outcome.
    UserType.DATA_DRIVEN: ClosingTendency(close_eagerness=1.0, accept_bias=0.65, walk_away_bias=0.35),
}

# How far toward their own walk-away point this archetype is plausibly
# willing to move by the end of a negotiation — fed into
# app.mock_numbers.concession_value() by eval/mock_user.py, same
# min/max-fraction shape as app/agent/mock.py's TACTIC_CONCESSION_RANGE.
# Independent of which strategy variant the agent is running — a
# simulated user's own concessiveness doesn't change based on who it's
# up against, only the *agent's* side of the negotiation does that (see
# TACTIC_CONCESSION_RANGE).
CONCESSION_RANGE: dict[UserType, tuple[float, float]] = {
    UserType.AGGRESSIVE: (0.00, 0.10),
    UserType.PASSIVE: (0.25, 0.50),
    UserType.DATA_DRIVEN: (0.10, 0.30),
}
