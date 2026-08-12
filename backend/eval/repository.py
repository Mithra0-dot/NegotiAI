"""The only place that queries the `simulated_sessions` table directly.

Mirrors app/history/repository.py's shape/reasoning: callers go through
save_simulated_session()/list_simulated_sessions() rather than touching
SimulatedSessionRecord/the DB session directly.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.schemas import ChatTurn
from app.scoring.models import SessionScore
from app.strategies.models import StrategyVariant
from eval.models import SimulatedSessionRecord
from eval.user_types import UserType


def save_simulated_session(
    db: DBSession,
    scenario_id: str,
    user_type: UserType,
    variant: StrategyVariant,
    score: SessionScore,
    transcript: list[ChatTurn],
) -> SimulatedSessionRecord:
    record = SimulatedSessionRecord(
        scenario_id=scenario_id,
        user_type=user_type.value,
        variant=variant.value,
        outcome=score.outcome.value,
        overall_score=score.overall_score,
        final_outcome_value=score.final_outcome_value,
        score_details=score.model_dump(mode="json"),
        transcript=[turn.model_dump(mode="json") for turn in transcript],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_simulated_sessions(
    db: DBSession,
    scenario_id: str | None = None,
    user_type: UserType | None = None,
    variant: StrategyVariant | None = None,
    limit: int = 100,
) -> list[SimulatedSessionRecord]:
    query = (
        select(SimulatedSessionRecord)
        .order_by(SimulatedSessionRecord.created_at.desc())
        .limit(limit)
    )
    if scenario_id is not None:
        query = query.where(SimulatedSessionRecord.scenario_id == scenario_id)
    if user_type is not None:
        query = query.where(SimulatedSessionRecord.user_type == user_type.value)
    if variant is not None:
        query = query.where(SimulatedSessionRecord.variant == variant.value)
    return list(db.scalars(query).all())
