"""Unit tests for the strategy state machine's adaptive select_tactic().

Uses the real salary-negotiation persona (opening_tactic_tag=ANCHORING)
as a stand-in — these tests only care about select_tactic's decision
logic, not persona content.
"""

from app.classifier.models import DetectedSignal, SignalType
from app.personas import get_persona
from app.strategies.default import select_tactic
from app.strategies.models import Phase, Tactic

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None


def _signal(signal_type: SignalType) -> DetectedSignal:
    return DetectedSignal(signal_type=signal_type, matched_phrases=["x"])


def test_unforced_concession_escalates_regardless_of_phase():
    # Even in OPENING, where the phase default is the persona's own tactic
    # (anchoring), an unforced concession should escalate to pressure.
    tactic = select_tactic(
        PERSONA, Phase.OPENING, [_signal(SignalType.UNFORCED_CONCESSION)]
    )
    assert tactic is Tactic.DEADLINE_PRESSURE


def test_premature_agreement_escalates():
    tactic = select_tactic(
        PERSONA, Phase.PROBING, [_signal(SignalType.PREMATURE_AGREEMENT)]
    )
    assert tactic is Tactic.DEADLINE_PRESSURE


def test_holding_firm_in_bargaining_eases_off():
    tactic = select_tactic(PERSONA, Phase.BARGAINING, [])
    assert tactic is Tactic.GOOD_COP_BAD_COP


def test_holding_firm_in_closing_eases_off():
    tactic = select_tactic(PERSONA, Phase.CLOSING, [])
    assert tactic is Tactic.GOOD_COP_BAD_COP


def test_holding_firm_in_opening_or_probing_keeps_phase_default():
    # Easing off only applies to bargaining/closing — opening still uses
    # the persona's natural tactic, probing still goes quiet.
    assert select_tactic(PERSONA, Phase.OPENING, []) is Tactic.ANCHORING
    assert select_tactic(PERSONA, Phase.PROBING, []) is Tactic.SILENCE


def test_non_concession_signals_dont_escalate_or_ease():
    # Hedging/urgency alone shouldn't trigger the escalate path, and their
    # presence blocks the "zero signals" ease-off path too.
    tactic = select_tactic(PERSONA, Phase.BARGAINING, [_signal(SignalType.HEDGING)])
    assert tactic is Tactic.ANCHORING  # phase default, unchanged


def test_concession_signal_takes_priority_over_ease_off():
    # Both conditions could apply in theory (bargaining phase); escalate
    # must win when a concession signal is present.
    tactic = select_tactic(
        PERSONA, Phase.BARGAINING, [_signal(SignalType.UNFORCED_CONCESSION)]
    )
    assert tactic is Tactic.DEADLINE_PRESSURE
