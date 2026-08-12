"""Session-end detection: deal reached, walked away, or turn limit.

Deliberately separate from app/classifier/ — that package's
`premature_agreement` patterns are tuned to catch *soft*, early agreement
language for tactic escalation ("sounds good", "works for me"), not a
genuine session-ending deal. The patterns here are narrower and more
decisive on purpose, since a false positive here ends the whole session
rather than just nudging a tactic.

Known limitation (same class as the classifier's rule-based patterns):
no negation handling. "I don't want to walk away from this" would still
match `_WALK_AWAY_PATTERNS`. Explicit, decisive phrasing keeps this rare
in practice but doesn't eliminate it.
"""

import re

from app.scoring.models import SessionOutcome

TURN_LIMIT = 10

_DEAL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bwe have a deal\b",
        r"\bit'?s a deal\b",
        r"\byou'?ve got a deal\b",
        r"\bi accept your offer\b",
        r"\bi'?ll take it\b",
        r"\blet'?s finalize\b",
    ]
]

_WALK_AWAY_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bi'?m walking away\b",
        r"\bi'?m out\b",
        r"\bno deal\b",
        r"\bi have to walk away\b",
        r"\bthis isn'?t going to work\b",
        r"\bi'?m done negotiating\b",
    ]
]


def detect_deal_reached(text: str) -> bool:
    return any(p.search(text) for p in _DEAL_PATTERNS)


def detect_walk_away(text: str) -> bool:
    return any(p.search(text) for p in _WALK_AWAY_PATTERNS)


def check_session_end(
    user_message: str, agent_reply: str, turn_number: int
) -> SessionOutcome | None:
    """Checks only the *current* exchange, not prior history — stateless
    design means if an earlier turn ended the session, that turn already
    reported it; there's nothing to re-detect by rescanning old messages.
    Walk-away is checked before deal-reached so a message that (rarely)
    matches both is treated as the more decisive outcome."""
    if detect_walk_away(user_message) or detect_walk_away(agent_reply):
        return SessionOutcome.WALKED_AWAY
    if detect_deal_reached(user_message) or detect_deal_reached(agent_reply):
        return SessionOutcome.DEAL_REACHED
    if turn_number >= TURN_LIMIT:
        return SessionOutcome.TURN_LIMIT_REACHED
    return None
