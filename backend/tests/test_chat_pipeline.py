"""Unit tests for app/chat_pipeline.py's variant dispatch — confirms
run_chat_turn(variant=...) actually routes to the right select_tactic()
implementation via app/strategies/registry.py, not just that each
variant's own select_tactic() works in isolation (that's
test_strategy.py / test_strategy_hardline.py's job).

Forces MOCK_LLM=true so these run fast/free, same pattern as
test_mock_agent.py. Turn 4 lands in BARGAINING (see
app/strategies/default.py's phase_for_turn) with no classifier signals
in the message — exactly the case default.py and hardline.py disagree
on (ease off vs. never ease off), so it's a clean way to prove the
dispatch is real.
"""

from app.chat_pipeline import run_chat_turn
from app.config import settings
from app.personas import get_persona
from app.strategies.models import StrategyVariant, Tactic

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None

_BARGAINING_TURN = 4
_NEUTRAL_MESSAGE = "Let's keep discussing the details."


def test_default_variant_eases_off_in_bargaining_with_no_signals(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    result = run_chat_turn(PERSONA, _NEUTRAL_MESSAGE, _BARGAINING_TURN, [])
    assert result.tactic is Tactic.GOOD_COP_BAD_COP


def test_hardline_variant_keeps_pressure_in_bargaining_with_no_signals(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    result = run_chat_turn(
        PERSONA,
        _NEUTRAL_MESSAGE,
        _BARGAINING_TURN,
        [],
        variant=StrategyVariant.HARDLINE,
    )
    assert result.tactic is Tactic.DEADLINE_PRESSURE


def test_variant_defaults_to_default_when_omitted(monkeypatch):
    # main.py's /chat route never passes `variant` — relies on this.
    monkeypatch.setattr(settings, "mock_llm", True)
    with_default = run_chat_turn(PERSONA, _NEUTRAL_MESSAGE, _BARGAINING_TURN, [])
    explicit_default = run_chat_turn(
        PERSONA, _NEUTRAL_MESSAGE, _BARGAINING_TURN, [], variant=StrategyVariant.DEFAULT
    )
    assert with_default.tactic is explicit_default.tactic
