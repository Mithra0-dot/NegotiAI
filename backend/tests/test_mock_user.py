"""Unit tests for eval/mock_user.py's randomized-number mock replies —
mirrors test_mock_agent.py's structure for the simulated-user side.
"""

import re

from app.classifier import classify_message
from app.classifier.models import SignalType
from app.personas import get_persona
from eval.mock_user import REPLY_POOLS, generate_mock_user_message
from eval.user_types import UserType

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None

_MOCK_PREFIX = "[mock] "


def _template_regexes(user_type: UserType) -> list[re.Pattern[str]]:
    patterns = []
    for template in REPLY_POOLS[user_type]:
        escaped = re.escape(template)
        escaped = escaped.replace(re.escape("{value}"), r"[\d.]+")
        escaped = escaped.replace(re.escape("{unit}"), re.escape(PERSONA.user_constraints.unit))
        patterns.append(re.compile(f"^{escaped}$"))
    return patterns


def test_turn_one_cites_the_exact_target():
    # turn_number=1 never rolls a closing line (see _maybe_closing_line),
    # so this is always a templated reply, and progress=0 means no
    # movement yet (see app/mock_numbers.py's concession_value).
    target_str = str(round(PERSONA.user_constraints.target))
    for user_type in UserType:
        for _ in range(10):
            reply = generate_mock_user_message(PERSONA, user_type, turn_number=1)
            assert target_str in reply, f"{user_type} turn-1 reply missing exact target: {reply!r}"


def test_reply_matches_one_of_its_type_templates_or_a_closing_line():
    for user_type in UserType:
        regexes = _template_regexes(user_type)
        for turn_number in (1, 4, 9):
            for _ in range(15):
                reply = generate_mock_user_message(PERSONA, user_type, turn_number)
                body = reply.removeprefix(_MOCK_PREFIX)
                is_template_match = any(p.match(body) for p in regexes)
                is_closing_line = (
                    "i accept your offer" in body.lower()
                    or "i'm walking away" in body.lower()
                )
                assert is_template_match or is_closing_line, (
                    f"{body!r} matched neither {user_type}'s templates nor a closing line"
                )


def test_passive_and_data_driven_sometimes_trigger_unforced_concession():
    # Low turn_number keeps the closing-line probability low (see
    # eval/mock_user.py's _maybe_closing_line) so enough template draws
    # show up in a bounded number of tries.
    for user_type in (UserType.PASSIVE, UserType.DATA_DRIVEN):
        triggered = False
        for _ in range(60):
            reply = generate_mock_user_message(PERSONA, user_type, turn_number=2)
            body = reply.removeprefix(_MOCK_PREFIX)
            signals = {s.signal_type for s in classify_message(body)}
            if SignalType.UNFORCED_CONCESSION in signals:
                triggered = True
                break
        assert triggered, f"{user_type} never triggered UNFORCED_CONCESSION across 60 draws"


def test_aggressive_never_triggers_unforced_concession():
    for _ in range(60):
        reply = generate_mock_user_message(PERSONA, UserType.AGGRESSIVE, turn_number=2)
        body = reply.removeprefix(_MOCK_PREFIX)
        signals = {s.signal_type for s in classify_message(body)}
        assert SignalType.UNFORCED_CONCESSION not in signals, (
            f"aggressive reply unexpectedly read as an unforced concession: {body!r}"
        )
