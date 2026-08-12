"""API response shape for GET /sessions.

Deliberately doesn't expose the dedicated-column duplication that exists
at the DB layer (outcome/overall_score/final_outcome_value living both as
their own columns and inside score_details) — the response just returns
the full `score`, which already has all of that.
"""

from datetime import datetime

from pydantic import BaseModel

from app.scoring.models import SessionScore


class SessionHistoryItem(BaseModel):
    id: int
    scenario_id: str
    created_at: datetime
    score: SessionScore
