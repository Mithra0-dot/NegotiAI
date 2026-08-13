"""Canned simulated-user messages for MOCK_LLM=true — dev/demo mode, no
API credits. Mirrors app/agent/mock.py's pattern (REPLY_POOLS as data,
separate from the wiring in eval/simulated_user.py) but for the
*simulated user's* voice instead of the agent's.

Session-end detection (app/scoring/outcome_detection.py) matches narrow,
specific phrasing ("I accept your offer", "I'm walking away", ...). A
real LLM asked to "play an aggressive negotiator" won't reliably emit
that exact wording, and neither would picking from a plain reply pool —
so mock mode needs to deliberately inject one of those canonical phrases
on the turn it decides to close, or every simulated session would run to
TURN_LIMIT_REACHED regardless of user type. See eval/user_types.py's
ClosingTendency for the per-type timing/outcome weights driving the
random choice below.

Templates now cite a number via app.mock_numbers' concession_value() —
bounded, randomized movement from the user's own target toward their
walk-away point (see eval/user_types.py's CONCESSION_RANGE and
app/mock_numbers.py's module docstring for the full "mock/demo data, not
real negotiation intelligence" scope note). PASSIVE and DATA_DRIVEN also
get some templates phrased as an active concession ("I could come down
to...") rather than just stating a number — deliberately, so those
turns actually trip app/classifier's UNFORCED_CONCESSION signal and
concession_pacing_score stops being permanently stuck at 100 in mock
mode. AGGRESSIVE stays purely declarative regardless of how much its own
number drifts, matching its "resists conceding" personality.
"""

import random

from app.mock_numbers import concession_value
from app.personas.models import PersonaInternal
from app.scoring.outcome_detection import TURN_LIMIT
from eval.user_types import CLOSING_TENDENCY, CONCESSION_RANGE, UserType

REPLY_POOLS: dict[UserType, list[str]] = {
    UserType.AGGRESSIVE: [
        "I'm not moving off {value} {unit} — that's where I need to land.",
        "Let's be real, {value} {unit} is the number. I've got other options if this doesn't work.",
        "I've done my homework — {value} {unit} isn't up for debate on my end.",
    ],
    UserType.PASSIVE: [
        "I was hoping for something around {value} {unit}, but I don't want to make this difficult.",
        "I could come down to {value} {unit} if that helps us close this out.",
        "I don't mind meeting you at {value} {unit} — I just want this resolved.",
    ],
    UserType.DATA_DRIVEN: [
        "Based on what I've seen elsewhere, {value} {unit} is the market rate — happy to share the comps.",
        "The numbers I've gathered point to {value} {unit} as fair. What's driving your figure?",
        "I could accept {value} {unit} if you can justify your position with similar data.",
    ],
}

# Each phrase deliberately contains a phrase _DEAL_PATTERNS/_WALK_AWAY_PATTERNS
# matches verbatim (see app/scoring/outcome_detection.py) so mock-mode
# closes are actually detected, not just "sound like" a close.
_ACCEPT_PHRASES = [
    "Alright, I accept your offer — let's move forward.",
    "That works for me. I accept your offer as it stands.",
    "Okay, you've convinced me — I accept your offer.",
]
_WALK_AWAY_PHRASES = [
    "This isn't going to get there for me — I'm walking away.",
    "I've heard enough. I'm walking away from this one.",
    "No deal — I'm walking away.",
]


def _maybe_closing_line(user_type: UserType, turn_number: int) -> str | None:
    """Returns a canonical closing line if this turn rolls a close,
    else None. No close is offered on turn 1 — every simulated session
    gets at least one real negotiating exchange before it can end,
    same as a human session realistically would."""
    if turn_number < 2:
        return None

    tendency = CLOSING_TENDENCY[user_type]
    # Grows with turn number, scaled by how eager this archetype is to
    # close — clamped so it's never a sure thing (leaves room for the
    # turn limit to still be the outcome sometimes, same as real usage).
    close_probability = min(0.9, (turn_number - 1) * 0.2 * tendency.close_eagerness)
    if random.random() >= close_probability:
        return None

    accept = random.random() < (
        tendency.accept_bias / (tendency.accept_bias + tendency.walk_away_bias)
    )
    return random.choice(_ACCEPT_PHRASES if accept else _WALK_AWAY_PHRASES)


def generate_mock_user_message(
    persona: PersonaInternal, user_type: UserType, turn_number: int
) -> str:
    """Picks a closing line if this turn rolls one, otherwise a random
    templated line from `user_type`'s pool, grounded in a bounded,
    randomized number derived from the scenario's own user_constraints
    (see module docstring) — prefixed `[mock]` per the existing
    convention (see app/agent/mock.py)."""
    closing = _maybe_closing_line(user_type, turn_number)
    if closing is not None:
        return f"[mock] {closing}"

    template = random.choice(REPLY_POOLS[user_type])
    value = concession_value(
        persona.user_constraints, turn_number, CONCESSION_RANGE[user_type], TURN_LIMIT
    )
    text = template.format(value=value, unit=persona.user_constraints.unit)
    return f"[mock] {text}"
