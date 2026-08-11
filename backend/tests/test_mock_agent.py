"""Unit tests for MOCK_LLM dev/demo mode.

Uses the real salary-negotiation persona as a stand-in, same as
test_strategy.py — these tests only care about mock-reply mechanics, not
persona content.
"""

import app.agent.llm as llm_module
from app.agent.llm import generate_reply
from app.agent.mock import REPLY_POOLS, generate_mock_reply
from app.config import settings
from app.personas import get_persona
from app.strategies.models import Phase, Tactic

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None

_MOCK_PREFIX = "[mock] "


def _expected_variants(tactic: Tactic) -> set[str]:
    """Every fully-rendered string generate_mock_reply could produce for
    this tactic and persona, given the known template/trait pools."""
    return {
        template.format(trait=trait)
        for template in REPLY_POOLS[tactic]
        for trait in PERSONA.personality_traits
    }


def test_mock_reply_has_prefix_and_is_nonempty():
    reply = generate_mock_reply(PERSONA, Tactic.ANCHORING)
    assert reply.startswith(_MOCK_PREFIX)
    assert reply.strip() != _MOCK_PREFIX.strip()


def test_mock_reply_stays_within_its_tactic_pool():
    for tactic in Tactic:
        expected = _expected_variants(tactic)
        # Run several times — the pool + trait choice is random, so a
        # single draw wouldn't exercise the variety at all.
        for _ in range(20):
            reply = generate_mock_reply(PERSONA, tactic)
            body = reply.removeprefix(_MOCK_PREFIX)
            assert body in expected, f"{body!r} not in {tactic} pool"


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
        )
    except AgentError:
        pass
    assert reached_llm["called"] is True
