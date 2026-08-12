"""Unit tests for the synthetic-session simulator (eval/).

Forces MOCK_LLM=true (autouse fixture below) so these tests run fast and
free — same monkeypatch pattern as test_mock_agent.py. Repository tests
use an in-memory SQLite engine, same fixture pattern as test_history.py.
run_n_sessions() owns its own DB session internally via app.db.SessionLocal
rather than taking one as a parameter (see eval/run_simulation.py's
docstring for why — it needs to work identically from the CLI, which has
no request context) — its fixture monkeypatches
eval.run_simulation.SessionLocal to point at the in-memory engine instead.
"""

import eval.run_simulation as run_simulation_module
import eval.simulated_user as simulated_user_module
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base
from app.personas import get_persona
from app.schemas import ChatTurn
from app.scoring.models import SessionOutcome
from app.scoring.outcome_detection import TURN_LIMIT
from app.scoring.scorer import compute_session_score
from eval import models  # noqa: F401 - registers SimulatedSessionRecord on Base
from eval.repository import list_simulated_sessions, save_simulated_session
from eval.run_simulation import run_n_sessions, run_simulated_session, summarize
from eval.user_types import UserType

SCENARIO_ID = "salary-negotiation"
PERSONA = get_persona(SCENARIO_ID)
assert PERSONA is not None


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine)
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def sqlite_session_local(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    # expire_on_commit=False, same reason as app/db.py's SessionLocal —
    # run_n_sessions() reads record attributes after its session has
    # already closed.
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(run_simulation_module, "SessionLocal", testing_session_local)
    return testing_session_local


def _sample_score_and_transcript():
    transcript = [
        ChatTurn(role="assistant", text="Our band tops out at $105,000."),
        ChatTurn(role="user", text="I accept your offer at $120,000."),
    ]
    score = compute_session_score(PERSONA, transcript, SessionOutcome.DEAL_REACHED)
    return score, transcript


# --- run_simulated_session -------------------------------------------------


def test_run_simulated_session_completes_with_a_score():
    score, transcript = run_simulated_session(SCENARIO_ID, UserType.PASSIVE)
    assert 0 <= score.overall_score <= 100
    assert transcript


def test_run_simulated_session_transcript_alternates_user_and_assistant():
    _, transcript = run_simulated_session(SCENARIO_ID, UserType.DATA_DRIVEN)
    for i, turn in enumerate(transcript):
        assert turn.role == ("user" if i % 2 == 0 else "assistant")


def test_run_simulated_session_stays_within_turn_limit():
    _, transcript = run_simulated_session(SCENARIO_ID, UserType.AGGRESSIVE)
    # Each completed turn contributes exactly one user + one assistant
    # message, so the transcript can never exceed 2x the turn limit.
    assert len(transcript) <= TURN_LIMIT * 2


def test_run_simulated_session_unknown_scenario_raises_value_error():
    with pytest.raises(ValueError):
        run_simulated_session("not-a-real-scenario", UserType.PASSIVE)


def test_all_user_types_produce_a_valid_session():
    for user_type in UserType:
        score, transcript = run_simulated_session(SCENARIO_ID, user_type)
        assert score.outcome is not None
        assert transcript


def test_run_simulated_session_never_calls_the_real_llm_in_mock_mode(monkeypatch):
    def _boom():
        raise AssertionError("get_llm() should not be called in mock mode")

    monkeypatch.setattr(simulated_user_module, "get_llm", _boom)
    _, transcript = run_simulated_session(SCENARIO_ID, UserType.AGGRESSIVE)
    assert transcript


# --- repository --------------------------------------------------------


def test_save_simulated_session_persists_and_returns_a_record(db_session):
    score, transcript = _sample_score_and_transcript()
    record = save_simulated_session(
        db_session, SCENARIO_ID, UserType.AGGRESSIVE, score, transcript
    )

    assert record.id is not None
    assert record.scenario_id == SCENARIO_ID
    assert record.user_type == "aggressive"
    assert record.outcome == "deal_reached"
    assert record.overall_score == score.overall_score
    assert record.transcript[0]["role"] == "assistant"
    assert record.score_details["anchoring_result"] == score.anchoring_result.value


def test_list_simulated_sessions_filters_by_user_type(db_session):
    score, transcript = _sample_score_and_transcript()
    save_simulated_session(db_session, SCENARIO_ID, UserType.AGGRESSIVE, score, transcript)
    save_simulated_session(db_session, SCENARIO_ID, UserType.PASSIVE, score, transcript)

    records = list_simulated_sessions(db_session, user_type=UserType.PASSIVE)
    assert len(records) == 1
    assert records[0].user_type == "passive"


def test_list_simulated_sessions_filters_by_scenario_id(db_session):
    score, transcript = _sample_score_and_transcript()
    save_simulated_session(db_session, SCENARIO_ID, UserType.AGGRESSIVE, score, transcript)
    save_simulated_session(db_session, "freelance-rate", UserType.AGGRESSIVE, score, transcript)

    records = list_simulated_sessions(db_session, scenario_id="freelance-rate")
    assert len(records) == 1
    assert records[0].scenario_id == "freelance-rate"


def test_simulated_sessions_stay_out_of_the_human_sessions_table(db_session):
    # Proves the "separate table, not a flag" design actually holds:
    # app.history.models.SessionRecord ("sessions") and
    # eval.models.SimulatedSessionRecord ("simulated_sessions") are
    # distinct tables — writing to one must never populate the other.
    from app.history.models import SessionRecord

    score, transcript = _sample_score_and_transcript()
    save_simulated_session(db_session, SCENARIO_ID, UserType.AGGRESSIVE, score, transcript)

    assert db_session.query(SessionRecord).count() == 0


# --- run_n_sessions / summarize --------------------------------------------


def test_run_n_sessions_persists_n_records(sqlite_session_local):
    records = run_n_sessions(SCENARIO_ID, UserType.PASSIVE, 3)
    assert len(records) == 3
    for record in records:
        assert record.id is not None
        assert record.scenario_id == SCENARIO_ID
        assert record.user_type == "passive"


def test_run_n_sessions_rejects_non_positive_n(sqlite_session_local):
    with pytest.raises(ValueError):
        run_n_sessions(SCENARIO_ID, UserType.PASSIVE, 0)


def test_summarize_empty_list():
    summary = summarize([])
    assert summary == {"count": 0, "mean_overall_score": None, "outcome_counts": {}}


def test_summarize_computes_mean_and_outcome_counts(sqlite_session_local):
    records = run_n_sessions(SCENARIO_ID, UserType.AGGRESSIVE, 4)
    summary = summarize(records)

    assert summary["count"] == 4
    assert sum(summary["outcome_counts"].values()) == 4
    assert summary["mean_overall_score"] == pytest.approx(
        sum(r.overall_score for r in records) / 4
    )
