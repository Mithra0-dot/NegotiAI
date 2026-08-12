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
"""

import random

from app.personas.models import PersonaInternal
from eval.user_types import CLOSING_TENDENCY, UserType

REPLY_POOLS: dict[UserType, list[str]] = {
    UserType.AGGRESSIVE: [
        "I'm not moving off {target} {unit} — that's where I need to land.",
        "Let's be real, {target} {unit} is the number. I've got other options if this doesn't work.",
        "I've done my homework — {target} {unit} isn't up for debate on my end.",
    ],
    UserType.PASSIVE: [
        "I was hoping for something around {target} {unit}, but I don't want to make this difficult.",
        "Maybe {target} {unit} could work? I'm flexible if that's a stretch for you.",
        "I don't want to push too hard, but {target} {unit} would be great if possible.",
    ],
    UserType.DATA_DRIVEN: [
        "Based on what I've seen elsewhere, {target} {unit} is the market rate — happy to share the comps.",
        "The numbers I've gathered point to {target} {unit} as fair. What's driving your figure?",
        "Looking at comparable deals, {target} {unit} seems reasonable — let's talk specifics.",
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
    templated line from `user_type`'s pool grounded in the scenario's
    own user_constraints (so the message carries a real numeric anchor,
    same as a human message would), prefixed `[mock]` per the existing
    convention (see app/agent/mock.py)."""
    closing = _maybe_closing_line(user_type, turn_number)
    if closing is not None:
        return f"[mock] {closing}"

    template = random.choice(REPLY_POOLS[user_type])
    text = template.format(
        target=persona.user_constraints.target,
        unit=persona.user_constraints.unit,
    )
    return f"[mock] {text}"
