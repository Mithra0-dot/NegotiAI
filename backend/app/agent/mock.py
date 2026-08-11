"""Canned replies for MOCK_LLM=true — dev/demo mode, no API credits.

Kept as data (pools) separate from the wiring in llm.py, same config-vs-
logic split as personas/ and strategies/. Keyed by Tactic only: since the
strategy state machine already turns escalation/easing into a *tactic*
change (see strategies/default.py's select_tactic), varying replies by
tactic is exactly what makes that escalation visibly show up in mock mode.
"""

import random

from app.personas.models import PersonaInternal
from app.strategies.models import Tactic

REPLY_POOLS: dict[Tactic, list[str]] = {
    Tactic.ANCHORING: [
        "Let's be straightforward — my number is where I'm starting, and "
        "I don't plan to move first.",
        "I'll put my position on the table plainly: this is my anchor, "
        "and it's a strong one.",
        "Being {trait} about this, I'd rather set the terms now than "
        "negotiate against myself.",
    ],
    Tactic.SILENCE: [
        "Tell me more about what's driving your position — I want to "
        "understand before I say anything more.",
        "I'm listening. What matters most to you here?",
        "Being {trait}, I'd rather hear your reasoning first before I "
        "commit to anything.",
    ],
    Tactic.DEADLINE_PRESSURE: [
        "I need to move on this soon — can we get to a number today?",
        "There's a clock running on this from my side. Let's close it "
        "out before that changes things.",
        "Being {trait}, I don't love dragging this out — what would it "
        "take to wrap up now?",
    ],
    Tactic.GOOD_COP_BAD_COP: [
        "I hear you, and I want this to work for both of us — let's "
        "find some middle ground.",
        "Being {trait}, I'd rather we land somewhere we're both "
        "comfortable with than dig in.",
        "Let's take a step back — what would make this feel fair to "
        "you?",
    ],
}


def generate_mock_reply(persona: PersonaInternal, tactic: Tactic) -> str:
    """Picks a random template from `tactic`'s pool and fills in a random
    personality trait, prefixed `[mock]` so it's never mistaken for real
    model output (same convention as the earlier `[stub]` labels)."""
    template = random.choice(REPLY_POOLS[tactic])
    trait = random.choice(persona.personality_traits)
    return f"[mock] {template.format(trait=trait)}"
