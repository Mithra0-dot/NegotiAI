"""Unit tests for the rule-based concession-signal classifier.

One positive case per signal type, plus a neutral-message case asserting
no false positives. Run with `pytest` from backend/ (or anywhere with
backend/ on the path — no package install needed, `app` is importable
directly since these tests run from the repo's backend/ directory).
"""

from app.classifier import SignalType, classify_message


def _signal_types(text: str) -> set[SignalType]:
    return {s.signal_type for s in classify_message(text)}


def test_hedging_detected():
    result = classify_message("Maybe I could accept a bit less, I guess.")
    types = {s.signal_type for s in result}
    assert SignalType.HEDGING in types

    hedging = next(s for s in result if s.signal_type == SignalType.HEDGING)
    assert "Maybe" in hedging.matched_phrases
    assert "I guess" in hedging.matched_phrases


def test_unforced_concession_detected():
    result = classify_message("Maybe I could accept a bit less, I guess.")
    types = {s.signal_type for s in result}
    assert SignalType.UNFORCED_CONCESSION in types


def test_urgency_detected():
    types = _signal_types("I really need this ASAP, I can't wait much longer.")
    assert SignalType.URGENCY in types


def test_premature_agreement_detected():
    types = _signal_types("Sounds good, deal!")
    assert SignalType.PREMATURE_AGREEMENT in types


def test_neutral_message_has_no_signals():
    result = classify_message("What's your budget range for this role?")
    assert result == []


def test_message_can_trigger_multiple_signal_types():
    types = _signal_types("I guess I could accept that, sounds good!")
    assert SignalType.HEDGING in types
    assert SignalType.UNFORCED_CONCESSION in types
    assert SignalType.PREMATURE_AGREEMENT in types


def test_matching_is_case_insensitive():
    types = _signal_types("MAYBE we can work something out.")
    assert SignalType.HEDGING in types
