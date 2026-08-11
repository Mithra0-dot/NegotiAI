"""The one strategy variant in play right now.

Structured as its own file so a future variant (e.g. `aggressive.py`,
`collaborative.py`) can be added for the simulated A/B testing stretch
feature without touching this file, personas/, or main.py.
"""

from app.classifier.models import DetectedSignal, SignalType
from app.personas.models import PersonaInternal
from app.strategies.models import Phase, Tactic

# Signals that mean the user is giving ground — worth pressing regardless
# of what phase-based logic would otherwise pick.
_CONCESSION_SIGNALS = {SignalType.UNFORCED_CONCESSION, SignalType.PREMATURE_AGREEMENT}


def phase_for_turn(turn_number: int) -> Phase:
    """Turn-count-based phase. `turn_number` is the 1-indexed count of
    user messages sent so far in this negotiation (client-reported —
    there's no backend session store yet, so this isn't server-verified;
    revisit once real sessions/DB land)."""
    if turn_number <= 1:
        return Phase.OPENING
    if turn_number <= 3:
        return Phase.PROBING
    if turn_number <= 6:
        return Phase.BARGAINING
    return Phase.CLOSING


def _phase_default_tactic(persona: PersonaInternal, phase: Phase) -> Tactic:
    """Opening and bargaining lean on the persona's natural tactic;
    probing goes quiet to draw the user out; closing always applies
    deadline pressure to force a decision."""
    if phase in (Phase.OPENING, Phase.BARGAINING):
        return persona.opening_tactic_tag
    if phase is Phase.PROBING:
        return Tactic.SILENCE
    return Tactic.DEADLINE_PRESSURE  # CLOSING


def select_tactic(
    persona: PersonaInternal,
    phase: Phase,
    detected_signals: list[DetectedSignal],
) -> Tactic:
    """Adaptive on top of the phase-default logic above: escalate to
    deadline pressure the moment the user gives ground unprompted or
    agrees too early (regardless of phase), and ease off into rapport if
    they're holding firm with zero signals deep into bargaining/closing.
    """
    signal_types = {s.signal_type for s in detected_signals}

    if signal_types & _CONCESSION_SIGNALS:
        return Tactic.DEADLINE_PRESSURE

    base = _phase_default_tactic(persona, phase)

    if not signal_types and phase in (Phase.BARGAINING, Phase.CLOSING):
        return Tactic.GOOD_COP_BAD_COP

    return base
