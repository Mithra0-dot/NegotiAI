"""Unit tests for eval/compare_variants.py's DB-querying/grouping layer —
pulling the right scenario_id/variant/user_type groups out of
`simulated_sessions` before handing them to eval/statistics.py (covered
independently in test_eval_statistics.py).

Same sqlite-backed fixture pattern as test_eval_simulation.py:
compare_variants() owns its own DB session via app.db.SessionLocal
(imported into eval.compare_variants's namespace), so the fixture
monkeypatches that name rather than passing a session in.
"""

import eval.compare_variants as compare_variants_module
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.strategies.models import StrategyVariant
from eval import models  # noqa: F401 - registers SimulatedSessionRecord on Base
from eval.compare_variants import (
    InsufficientSessionsError,
    UnknownScenarioError,
    compare_variants,
)
from eval.models import SimulatedSessionRecord
from eval.user_types import UserType

SCENARIO_ID = "salary-negotiation"
OTHER_SCENARIO_ID = "freelance-rate"


@pytest.fixture()
def sqlite_session_local(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    # expire_on_commit=False — same reason as test_eval_simulation.py's
    # fixture: compare_variants() reads record attributes after closing
    # its own session.
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(compare_variants_module, "SessionLocal", testing_session_local)
    return testing_session_local


def _seed(
    session_local,
    scores: list[float],
    scenario_id: str = SCENARIO_ID,
    variant: StrategyVariant = StrategyVariant.DEFAULT,
    user_type: UserType = UserType.AGGRESSIVE,
) -> None:
    db = session_local()
    try:
        for score in scores:
            db.add(
                SimulatedSessionRecord(
                    scenario_id=scenario_id,
                    user_type=user_type.value,
                    variant=variant.value,
                    outcome="deal_reached",
                    overall_score=score,
                    final_outcome_value=None,
                    score_details={},
                    transcript=[],
                )
            )
        db.commit()
    finally:
        db.close()


def test_compare_variants_pulls_correct_groups(sqlite_session_local):
    _seed(sqlite_session_local, [40.0, 42.0, 38.0, 41.0, 39.0], variant=StrategyVariant.DEFAULT)
    _seed(sqlite_session_local, [70.0, 72.0, 68.0, 71.0, 69.0], variant=StrategyVariant.HARDLINE)

    result = compare_variants(SCENARIO_ID)

    assert result.group_a.label == "default"
    assert result.group_a.n == 5
    assert result.group_a.mean == pytest.approx(40.0, abs=0.5)
    assert result.group_b.label == "hardline"
    assert result.group_b.n == 5
    assert result.group_b.mean == pytest.approx(70.0, abs=0.5)


def test_compare_variants_pools_all_user_types_when_no_filter(sqlite_session_local):
    _seed(sqlite_session_local, [50.0, 51.0, 52.0], variant=StrategyVariant.DEFAULT, user_type=UserType.AGGRESSIVE)
    _seed(sqlite_session_local, [50.0, 51.0, 52.0], variant=StrategyVariant.DEFAULT, user_type=UserType.PASSIVE)
    _seed(sqlite_session_local, [60.0, 61.0, 62.0], variant=StrategyVariant.HARDLINE, user_type=UserType.AGGRESSIVE)
    _seed(sqlite_session_local, [60.0, 61.0, 62.0], variant=StrategyVariant.HARDLINE, user_type=UserType.PASSIVE)

    result = compare_variants(SCENARIO_ID)

    assert result.group_a.n == 6
    assert result.group_b.n == 6


def test_compare_variants_respects_user_type_filter(sqlite_session_local):
    _seed(sqlite_session_local, [50.0, 51.0, 52.0], variant=StrategyVariant.DEFAULT, user_type=UserType.AGGRESSIVE)
    _seed(sqlite_session_local, [10.0, 11.0, 12.0], variant=StrategyVariant.DEFAULT, user_type=UserType.PASSIVE)
    _seed(sqlite_session_local, [60.0, 61.0, 62.0], variant=StrategyVariant.HARDLINE, user_type=UserType.AGGRESSIVE)
    _seed(sqlite_session_local, [20.0, 21.0, 22.0], variant=StrategyVariant.HARDLINE, user_type=UserType.PASSIVE)

    result = compare_variants(SCENARIO_ID, UserType.PASSIVE)

    assert result.group_a.n == 3
    assert result.group_a.mean == pytest.approx(11.0)
    assert result.group_b.n == 3
    assert result.group_b.mean == pytest.approx(21.0)


def test_compare_variants_ignores_other_scenarios(sqlite_session_local):
    _seed(sqlite_session_local, [50.0, 51.0, 52.0], scenario_id=SCENARIO_ID, variant=StrategyVariant.DEFAULT)
    _seed(sqlite_session_local, [60.0, 61.0, 62.0], scenario_id=SCENARIO_ID, variant=StrategyVariant.HARDLINE)
    # Very different scores under a different scenario_id — must not leak in.
    _seed(sqlite_session_local, [0.0, 0.0, 0.0], scenario_id=OTHER_SCENARIO_ID, variant=StrategyVariant.DEFAULT)
    _seed(sqlite_session_local, [0.0, 0.0, 0.0], scenario_id=OTHER_SCENARIO_ID, variant=StrategyVariant.HARDLINE)

    result = compare_variants(SCENARIO_ID)

    assert result.group_a.n == 3
    assert result.group_a.mean == pytest.approx(51.0)


def test_compare_variants_unknown_scenario_raises(sqlite_session_local):
    with pytest.raises(UnknownScenarioError):
        compare_variants("not-a-real-scenario")


def test_compare_variants_insufficient_sessions_raises(sqlite_session_local):
    _seed(sqlite_session_local, [50.0], variant=StrategyVariant.DEFAULT)
    _seed(sqlite_session_local, [60.0], variant=StrategyVariant.HARDLINE)

    with pytest.raises(InsufficientSessionsError, match="Run more"):
        compare_variants(SCENARIO_ID)


def test_compare_variants_insufficient_sessions_when_one_variant_missing(sqlite_session_local):
    _seed(sqlite_session_local, [50.0, 51.0, 52.0], variant=StrategyVariant.DEFAULT)
    # No hardline rows seeded at all.

    with pytest.raises(InsufficientSessionsError):
        compare_variants(SCENARIO_ID)
