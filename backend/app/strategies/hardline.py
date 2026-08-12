"""Strategy variant B: a more aggressive, never-eases-off tactic policy —
the counterpart to app/strategies/default.py's variant A. Built for the
simulated A/B testing infra (see eval/) to compare against the default.

Same select_tactic() signature as default.py's, so both are
interchangeable through app/strategies/registry.py's dispatch — nothing
outside the strategies/ package needs to know which one it's calling.

Differences from default.py's select_tactic(), concretely:
  - PROBING: DEADLINE_PRESSURE instead of SILENCE — skips the "let the
    user reveal themselves" step in favor of pressure from the start.
  - BARGAINING/CLOSING: always DEADLINE_PRESSURE. Default's "ease off to
    GOOD_COP_BAD_COP when the user holds firm with zero signals" branch
    is removed entirely — hardline never eases off.
  - OPENING and the concession-signal escalation are unchanged (default
    is already maximally aggressive on both — nothing to intensify).

phase_for_turn() is intentionally NOT duplicated here — phase advancement
is shared, turn-count-based infrastructure, not part of what a strategy
variant varies. Both variants import it from default.py.
"""

from app.classifier.models import DetectedSignal, SignalType
from app.personas.models import PersonaInternal
from app.strategies.models import Phase, Tactic

_CONCESSION_SIGNALS = {SignalType.UNFORCED_CONCESSION, SignalType.PREMATURE_AGREEMENT}


def _phase_default_tactic(persona: PersonaInternal, phase: Phase) -> Tactic:
    if phase is Phase.OPENING:
        return persona.opening_tactic_tag
    # PROBING, BARGAINING, and CLOSING all lean on pressure — no silence
    # step, no ease-off step.
    return Tactic.DEADLINE_PRESSURE


def select_tactic(
    persona: PersonaInternal,
    phase: Phase,
    detected_signals: list[DetectedSignal],
) -> Tactic:
    """Same concession-signal escalation as default.py's select_tactic(),
    but the phase-default policy underneath it never eases off — see
    module docstring."""
    signal_types = {s.signal_type for s in detected_signals}

    if signal_types & _CONCESSION_SIGNALS:
        return Tactic.DEADLINE_PRESSURE

    return _phase_default_tactic(persona, phase)
