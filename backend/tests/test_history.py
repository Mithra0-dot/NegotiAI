"""Unit tests for the session-history repository layer.

Runs against an in-memory SQLite engine — a fast, dependency-free test
double. The real app always talks to Postgres via app.config.settings
.database_url; see app/db.py's docstring for why this test fixture
doesn't conflict with CLAUDE.md's "must be Postgres" rule. save_session()
/list_sessions() take a DB session as a plain argument, so they work
identically against either backend.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.history import models  # noqa: F401 - registers SessionRecord on Base
from app.history.models import SessionRecord
from app.history.repository import list_sessions, save_session
from app.personas import get_persona
from app.schemas import ChatTurn
from app.scoring.models import SessionOutcome
from app.scoring.scorer import compute_session_score

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None


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


def _sample_score(outcome=SessionOutcome.DEAL_REACHED):
    transcript = [
        ChatTurn(role="assistant", text="Our band tops out at $105,000."),
        ChatTurn(role="user", text="I accept your offer at $120,000."),
    ]
    return compute_session_score(PERSONA, transcript, outcome)


def test_save_session_persists_and_returns_a_record(db_session):
    score = _sample_score()
    record = save_session(db_session, "salary-negotiation", score)

    assert record.id is not None
    assert record.scenario_id == "salary-negotiation"
    assert record.outcome == "deal_reached"
    assert record.overall_score == score.overall_score
    assert record.final_outcome_value == 120_000.0
    assert record.score_details["anchoring_result"] == score.anchoring_result.value


def test_save_session_persists_walk_away_with_null_batna(db_session):
    score = _sample_score(SessionOutcome.WALKED_AWAY)
    record = save_session(db_session, "salary-negotiation", score)

    assert record.outcome == "walked_away"
    assert record.final_outcome_value is None
    assert record.score_details["batna_discipline_score"] is None


def test_list_sessions_returns_newest_first(db_session):
    now = datetime.now(timezone.utc)
    older = SessionRecord(
        scenario_id="salary-negotiation",
        created_at=now - timedelta(hours=1),
        outcome="deal_reached",
        overall_score=50.0,
        final_outcome_value=None,
        score_details={},
    )
    newer = SessionRecord(
        scenario_id="salary-negotiation",
        created_at=now,
        outcome="deal_reached",
        overall_score=80.0,
        final_outcome_value=None,
        score_details={},
    )
    db_session.add(older)
    db_session.add(newer)
    db_session.commit()

    records = list_sessions(db_session, scenario_id="salary-negotiation")
    assert [r.overall_score for r in records] == [80.0, 50.0]


def test_list_sessions_filters_by_scenario_id(db_session):
    save_session(db_session, "salary-negotiation", _sample_score())
    save_session(db_session, "freelance-rate", _sample_score())

    records = list_sessions(db_session, scenario_id="freelance-rate")
    assert len(records) == 1
    assert records[0].scenario_id == "freelance-rate"


def test_list_sessions_no_filter_returns_all_scenarios(db_session):
    save_session(db_session, "salary-negotiation", _sample_score())
    save_session(db_session, "freelance-rate", _sample_score())

    records = list_sessions(db_session)
    assert len(records) == 2


def test_list_sessions_respects_limit(db_session):
    for _ in range(3):
        save_session(db_session, "salary-negotiation", _sample_score())

    records = list_sessions(db_session, limit=2)
    assert len(records) == 2


def test_list_sessions_empty_when_none_saved(db_session):
    assert list_sessions(db_session) == []
