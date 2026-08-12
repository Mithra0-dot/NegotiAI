"""The only place that queries the `sessions` table directly.

Callers (main.py, tests) go through save_session()/list_sessions() rather
than touching SessionRecord/the DB session directly, so the query shapes
stay in one place.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.history.models import SessionRecord
from app.scoring.models import SessionScore


def save_session(db: DBSession, scenario_id: str, score: SessionScore) -> SessionRecord:
    record = SessionRecord(
        scenario_id=scenario_id,
        outcome=score.outcome.value,
        overall_score=score.overall_score,
        final_outcome_value=score.final_outcome_value,
        score_details=score.model_dump(mode="json"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_sessions(
    db: DBSession, scenario_id: str | None = None, limit: int = 50
) -> list[SessionRecord]:
    query = select(SessionRecord).order_by(SessionRecord.created_at.desc()).limit(limit)
    if scenario_id is not None:
        query = query.where(SessionRecord.scenario_id == scenario_id)
    return list(db.scalars(query).all())
