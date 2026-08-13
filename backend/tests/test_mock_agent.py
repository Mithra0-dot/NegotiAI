"""Unit tests for MOCK_LLM dev/demo mode.

Uses the real salary-negotiation persona as a stand-in, same as
test_strategy.py — these tests only care about mock-reply mechanics, not
persona content.

Reply text is no longer a finite enumerable set (templates now embed a
randomized {value} — see app/mock_numbers.py), so pool-membership checks
are structural (regex against the template shape) rather than exact-
string-set membership.
"""

import re

import app.agent.llm as llm_module
from app.agent.llm import generate_reply
from app.agent.mock import REPLY_POOLS, generate_mock_reply
from app.config import settings
from app.personas import get_persona
from app.strategies.models import Phase, Tactic

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None

_MOCK_PREFIX = "[mock] "
_NUMBER_TACTICS = (Tactic.ANCHORING, Tactic.DEADLINE_PRESSURE, Tactic.GOOD_COP_BAD_COP)


def _tactic_regexes(tactic: Tactic) -> list[re.Pattern[str]]:
    """Converts each of `tactic`'s templates into a regex — {trait} and
    {value} become wildcards, {unit} is pinned to this persona's actual
    unit string — so a rendered reply can be checked against "did this
    come from tactic's pool" without enumerating every possible value."""
    patterns = []
    for template in REPLY_POOLS[tactic]:
        escaped = re.escape(template)
        escaped = escaped.replace(re.escape("{trait}"), r".+")
        escaped = escaped.replace(re.escape("{value}"), r"[\d.]+")
        escaped = escaped.replace(re.escape("{unit}"), re.escape(PERSONA.constraints.unit))
        patterns.append(re.compile(f"^{escaped}$"))
    return patterns


def test_mock_reply_has_prefix_and_is_nonempty():
    reply = generate_mock_reply(PERSONA, Tactic.ANCHORING, turn_number=1)
    assert reply.startswith(_MOCK_PREFIX)
    assert reply.strip() != _MOCK_PREFIX.strip()


def test_mock_reply_matches_one_of_its_tactic_templates():
    for tactic in Tactic:
        regexes = _tactic_regexes(tactic)
        # Several turn numbers and draws — the template + trait + value
        # choice is all random, so one draw wouldn't exercise the variety.
        for turn_number in (1, 4, 9):
            for _ in range(10):
                reply = generate_mock_reply(PERSONA, tactic, turn_number)
                body = reply.removeprefix(_MOCK_PREFIX)
                assert any(p.match(body) for p in regexes), f"{body!r} not in {tactic} pool"


def test_silence_never_cites_a_number():
    # SILENCE deliberately never gets a {value} — its whole point is
    # withholding a position, not revealing one (see app/agent/mock.py).
    for _ in range(15):
        reply = generate_mock_reply(PERSONA, Tactic.SILENCE, turn_number=5)
        assert not re.search(r"\d", reply)


def test_every_other_tactic_cites_a_number_by_mid_negotiation():
    for tactic in _NUMBER_TACTICS:
        for _ in range(15):
            reply = generate_mock_reply(PERSONA, tactic, turn_number=5)
            assert re.search(r"\d", reply), f"{tactic} reply had no number: {reply!r}"


def test_value_starts_at_exact_target_on_turn_one():
    # progress=0 at turn 1 (see app/mock_numbers.py's concession_value)
    # regardless of tactic's concession range — no movement yet.
    target_str = str(round(PERSONA.constraints.target))
    for tactic in _NUMBER_TACTICS:
        for _ in range(10):
            reply = generate_mock_reply(PERSONA, tactic, turn_number=1)
            assert target_str in reply, f"{tactic} turn-1 reply didn't cite the exact target: {reply!r}"


def test_different_tactics_have_disjoint_pools():
    # Sanity check on the pool data itself: no accidental copy-paste
    # sharing the same template string across tactics, which would make
    # tone-shift verification meaningless.
    seen: set[str] = set()
    for templates in REPLY_POOLS.values():
        for t in templates:
            assert t not in seen
            seen.add(t)


def test_generate_reply_takes_mock_branch_without_calling_the_llm(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)

    def _boom() -> None:
        raise AssertionError("get_llm() should not be called in mock mode")

    monkeypatch.setattr(llm_module, "get_llm", _boom)

    reply = generate_reply(
        persona=PERSONA,
        phase=Phase.OPENING,
        tactic=Tactic.ANCHORING,
        detected_signals=[],
        message="Let's talk numbers.",
        history=[],
        turn_number=1,
    )
    assert reply.startswith(_MOCK_PREFIX)


def test_generate_reply_real_path_is_untouched_when_mock_disabled(monkeypatch):
    # Confirms the mock branch doesn't leak into the default (real) path —
    # with mock_llm False, get_llm() must actually be reached (we don't
    # call the network; we just assert the real branch is the one taken).
    monkeypatch.setattr(settings, "mock_llm", False)
    reached_llm = {"called": False}

    def _fake_get_llm():
        reached_llm["called"] = True
        raise RuntimeError("stop before any real network call")

    monkeypatch.setattr(llm_module, "get_llm", _fake_get_llm)

    from app.agent.llm import AgentError

    try:
        generate_reply(
            persona=PERSONA,
            phase=Phase.OPENING,
            tactic=Tactic.ANCHORING,
            detected_signals=[],
            message="Let's talk numbers.",
            history=[],
            turn_number=1,
        )
    except AgentError:
        pass
    assert reached_llm["called"] is True
