"""Canned replies for MOCK_LLM=true — dev/demo mode, no API credits.

Kept as data (pools) separate from the wiring in llm.py, same config-vs-
logic split as personas/ and strategies/. Keyed by Tactic only: since the
strategy state machine already turns escalation/easing into a *tactic*
change (see strategies/default.py's select_tactic), varying replies by
tactic is exactly what makes that escalation visibly show up in mock mode.

Templates (other than SILENCE) now cite a number via app.mock_numbers'
concession_value() — bounded, randomized movement from this persona's own
target toward its walk-away point as the negotiation progresses. See
app/mock_numbers.py's docstring for the "mock/demo data, not real
negotiation intelligence" scope note that applies here too. SILENCE stays
number-free on purpose: its whole point (see prompts.py's
TACTIC_INSTRUCTIONS) is withholding a position, not revealing one.
"""

import random

from app.mock_numbers import concession_value
from app.personas.models import PersonaInternal
from app.scoring.outcome_detection import TURN_LIMIT
from app.strategies.models import Tactic

# How far toward walk_away this tactic is plausibly willing to move by
# the end of a negotiation — see app/mock_numbers.py's concession_value().
# Not present for SILENCE: that tactic never cites a number at all.
TACTIC_CONCESSION_RANGE: dict[Tactic, tuple[float, float]] = {
    Tactic.ANCHORING: (0.00, 0.08),
    Tactic.DEADLINE_PRESSURE: (0.05, 0.20),
    Tactic.GOOD_COP_BAD_COP: (0.20, 0.45),
}

REPLY_POOLS: dict[Tactic, list[str]] = {
    Tactic.ANCHORING: [
        "Let's be straightforward — my number is {value} {unit}, and "
        "I don't plan to move first.",
        "I'll put my position on the table plainly: {value} {unit} is "
        "my anchor, and it's a strong one.",
        "Being {trait} about this, I'd rather set the terms now than "
        "negotiate against myself — {value} {unit} is where I'm starting.",
    ],
    Tactic.SILENCE: [
        "Tell me more about what's driving your position — I want to "
        "understand before I say anything more.",
        "I'm listening. What matters most to you here?",
        "Being {trait}, I'd rather hear your reasoning first before I "
        "commit to anything.",
    ],
    Tactic.DEADLINE_PRESSURE: [
        "I need to move on this soon — can we get to {value} {unit} today?",
        "There's a clock running on this from my side. {value} {unit} "
        "works, but only if we close it out before that changes things.",
        "Being {trait}, I don't love dragging this out — {value} {unit} "
        "is what it would take to wrap up now.",
    ],
    Tactic.GOOD_COP_BAD_COP: [
        "I hear you, and I want this to work for both of us — I could "
        "do {value} {unit} to find some middle ground.",
        "Being {trait}, I'd rather we land somewhere we're both "
        "comfortable with — {value} {unit} feels fair to me.",
        "Let's take a step back — would {value} {unit} make this feel "
        "fair to you?",
    ],
}


def generate_mock_reply(persona: PersonaInternal, tactic: Tactic, turn_number: int) -> str:
    """Picks a random template from `tactic`'s pool and fills in a random
    personality trait (and, for every tactic but SILENCE, a bounded,
    randomized number via concession_value() — see module docstring),
    prefixed `[mock]` so it's never mistaken for real model output (same
    convention as the earlier `[stub]` labels)."""
    template = random.choice(REPLY_POOLS[tactic])
    trait = random.choice(persona.personality_traits)

    if tactic is Tactic.SILENCE:
        return f"[mock] {template.format(trait=trait)}"

    value = concession_value(
        persona.constraints, turn_number, TACTIC_CONCESSION_RANGE[tactic], TURN_LIMIT
    )
    text = template.format(trait=trait, value=value, unit=persona.constraints.unit)
    return f"[mock] {text}"
