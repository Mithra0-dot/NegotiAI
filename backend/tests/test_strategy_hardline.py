"""Unit tests for the hardline strategy variant's select_tactic() — the
"more aggressive, never eases off" counterpart to default.py's, covered
in test_strategy.py. Mirrors that file's structure so the two are easy
to compare side by side.
"""

from app.classifier.models import DetectedSignal, SignalType
from app.personas import get_persona
from app.strategies.hardline import select_tactic
from app.strategies.models import Phase, Tactic

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None


def _signal(signal_type: SignalType) -> DetectedSignal:
    return DetectedSignal(signal_type=signal_type, matched_phrases=["x"])


def test_unforced_concession_escalates_regardless_of_phase():
    tactic = select_tactic(
        PERSONA, Phase.OPENING, [_signal(SignalType.UNFORCED_CONCESSION)]
    )
    assert tactic is Tactic.DEADLINE_PRESSURE


def test_premature_agreement_escalates():
    tactic = select_tactic(
        PERSONA, Phase.PROBING, [_signal(SignalType.PREMATURE_AGREEMENT)]
    )
    assert tactic is Tactic.DEADLINE_PRESSURE


def test_opening_still_uses_persona_tactic():
    # Unlike probing/bargaining/closing below, opening is unchanged from
    # default.py — hardline still opens in character.
    assert select_tactic(PERSONA, Phase.OPENING, []) is Tactic.ANCHORING


def test_probing_applies_pressure_instead_of_silence():
    # This is where hardline diverges from default: default.py goes
    # quiet (SILENCE) here to draw the user out.
    assert select_tactic(PERSONA, Phase.PROBING, []) is Tactic.DEADLINE_PRESSURE


def test_never_eases_off_in_bargaining_even_holding_firm():
    # default.py eases off to GOOD_COP_BAD_COP here with zero signals —
    # hardline's whole point is not doing that.
    assert select_tactic(PERSONA, Phase.BARGAINING, []) is Tactic.DEADLINE_PRESSURE


def test_never_eases_off_in_closing_even_holding_firm():
    assert select_tactic(PERSONA, Phase.CLOSING, []) is Tactic.DEADLINE_PRESSURE


def test_non_concession_signals_dont_change_the_pressure_default():
    tactic = select_tactic(PERSONA, Phase.BARGAINING, [_signal(SignalType.HEDGING)])
    assert tactic is Tactic.DEADLINE_PRESSURE
