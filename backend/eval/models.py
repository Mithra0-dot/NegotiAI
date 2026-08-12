"""SQLAlchemy ORM model for the `simulated_sessions` table.

Deliberately a separate table from app/history/models.py's `sessions`,
not a shared table with an `is_simulated` flag — see the approved plan's
"Separate storage table" rationale: keeps GET /sessions / the History
page provably human-only, and CLAUDE.md is explicit that simulated
results must never be conflated with real usage. Same column shape as
SessionRecord (dedicated columns for what's queried/sorted, plus a JSON
blob for the rest) with two additions: `user_type` (the simulated
archetype) and `transcript` (the full simulated dialogue — see this
module's read for why: a synthetic session with no visible dialogue is
hard to sanity-check later).

Uses the generic `JSON` type, same test-portability reasoning as
app/history/models.py.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SimulatedSessionRecord(Base):
    __tablename__ = "simulated_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[str] = mapped_column(index=True)
    # eval.user_types.UserType's value (e.g. "aggressive") — plain str
    # column, same convention as `outcome` below (enum stored by value).
    user_type: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    outcome: Mapped[str]
    overall_score: Mapped[float]
    final_outcome_value: Mapped[float | None]
    # The full SessionScore, serialized (app.scoring.models.SessionScore).
    score_details: Mapped[dict] = mapped_column(JSON)
    # The full simulated dialogue, oldest first: list[{"role", "text"}],
    # same shape as app.schemas.ChatTurn — lets a synthetic session's
    # score be sanity-checked against what was actually said.
    transcript: Mapped[list] = mapped_column(JSON)
