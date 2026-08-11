"""System prompt construction for the negotiation agent.

Kept separate from llm.py (which owns the actual API call) so the prompt
text — the part most likely to get tuned/reworded — is easy to find and
diff on its own, consistent with this project's config-vs-logic split
(see personas/, strategies/).
"""

from app.classifier.models import DetectedSignal, SignalType
from app.personas.models import PersonaInternal
from app.strategies.models import Phase, Tactic

TACTIC_INSTRUCTIONS: dict[Tactic, str] = {
    Tactic.ANCHORING: (
        "Open with a strong, self-serving number or position and hold to "
        "it — don't move first."
    ),
    Tactic.SILENCE: (
        "Ask probing questions and hold back your own position; let the "
        "user reveal more before you commit to anything."
    ),
    Tactic.DEADLINE_PRESSURE: (
        "Create urgency — reference a deadline, a competing option, or a "
        "closing timeline to push for a decision now."
    ),
    Tactic.GOOD_COP_BAD_COP: (
        "Soften your tone, show warmth or flexibility, and look for a "
        "collaborative angle rather than pure pressure."
    ),
}

# Tells the LLM *why* select_tactic escalated or eased off, so its tone
# matches the tactic instead of just following an enum value blind.
SIGNAL_GUIDANCE: dict[SignalType, str] = {
    SignalType.UNFORCED_CONCESSION: (
        "they just gave ground without being pushed — press your "
        "advantage rather than reciprocating."
    ),
    SignalType.PREMATURE_AGREEMENT: (
        "they're agreeing very quickly — there may be room to get more "
        "before closing."
    ),
    SignalType.HEDGING: (
        "they sound uncertain — you may be able to push for a firmer "
        "commitment."
    ),
    SignalType.URGENCY: (
        "they seem anxious about time — you can use that urgency to your "
        "advantage."
    ),
}


def build_system_prompt(
    persona: PersonaInternal,
    phase: Phase,
    tactic: Tactic,
    detected_signals: list[DetectedSignal],
) -> str:
    """Builds the full system prompt for one /chat turn.

    Uses the *internal* persona (goals + numeric constraints included) —
    this is backend-only context so the LLM can negotiate realistically
    from real numbers, never returned to the client verbatim. Unrelated
    to the PersonaPublic/PersonaInternal split in schemas.py, which is
    about what goes in the HTTP response, not the model's private
    context.
    """
    lines = [
        "You are role-playing as the opposing party in a negotiation "
        "training simulation.",
        "Stay fully in character — natural, realistic negotiation "
        "dialogue only. No meta-commentary about \"phases,\" \"tactics,\" "
        "or being an AI. Keep replies concise (2-4 sentences), like a "
        "real conversational negotiation message.",
        "",
        f"Your role: {persona.role_description}",
        f"Your personality: {', '.join(persona.personality_traits)}",
        f"Your typical opening approach: {persona.opening_tactic}",
        "",
        "Your private negotiating position (this is what you're "
        "actually trying to get — reveal it strategically through "
        "dialogue if it serves your tactic, never as a flat data dump):",
        f"- Goals: {'; '.join(persona.goals)}",
        f"- Ideal outcome: {persona.constraints.target} {persona.constraints.unit}",
        f"- Walk-away point: {persona.constraints.walk_away} {persona.constraints.unit}",
        "",
        f"Negotiation phase: {phase.value}",
        f"Your tactic for this turn: {tactic.value} — {TACTIC_INSTRUCTIONS[tactic]}",
    ]

    if detected_signals:
        labels = ", ".join(s.signal_type.value for s in detected_signals)
        guidance = " ".join(
            SIGNAL_GUIDANCE[s.signal_type] for s in detected_signals
        )
        lines += [
            "",
            f"Signals detected in the user's last message: {labels}. {guidance}",
        ]

    return "\n".join(lines)
