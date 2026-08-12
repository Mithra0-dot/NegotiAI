"""SQLAlchemy ORM model for the `sessions` table.

Dedicated columns for what the history list/trend chart need to
query/sort/filter directly (scenario_id, created_at, outcome,
overall_score, final_outcome_value), plus `score_details` holding the
*entire* SessionScore payload (sub-scores, notes, user_target_range,
everything) so the history view never needs another migration to show
more detail. The dedicated columns duplicate a few of the JSON fields —
deliberate, so listing/sorting doesn't need to touch the JSON blob.

Uses the generic `JSON` type rather than Postgres-specific `JSONB` — see
app/db.py's docstring for why (test portability; no structured querying
into the JSON in this pass).
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    outcome: Mapped[str]
    overall_score: Mapped[float]
    final_outcome_value: Mapped[float | None]
    # The full SessionScore, serialized (app.scoring.models.SessionScore).
    score_details: Mapped[dict] = mapped_column(JSON)
