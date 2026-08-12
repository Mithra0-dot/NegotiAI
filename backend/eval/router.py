"""POST /eval/simulate — thin HTTP wrapper over run_n_sessions() (see
eval/run_simulation.py), the same function the CLI script calls. Runs
synchronously: fine at this scale (mock-mode N=50-100 is seconds; real-
LLM mode is slower, which is expected and out of scope to optimize in
this pass — no background job queue yet, see the approved plan's "out of
scope" list).
"""

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from app.strategies.models import StrategyVariant
from eval.run_simulation import run_n_sessions, summarize
from eval.user_types import UserType

router = APIRouter(prefix="/eval", tags=["eval"])


class SimulateRequest(BaseModel):
    scenario_id: str
    user_type: UserType
    # Which agent tactic-selection policy to run against (see
    # app/strategies/registry.py) — defaults to the same variant real
    # /chat traffic uses, so omitting it reproduces today's behavior.
    variant: StrategyVariant = StrategyVariant.DEFAULT
    n: int = 10


class SimulatedSessionSummary(BaseModel):
    id: int
    variant: str
    outcome: str
    overall_score: float
    final_outcome_value: float | None


class SimulateResponse(BaseModel):
    sessions: list[SimulatedSessionSummary]
    summary: dict


@router.post("/simulate")
def simulate(request: SimulateRequest) -> SimulateResponse:
    if request.n < 1:
        raise HTTPException(status_code=422, detail="n must be at least 1")

    try:
        records = run_n_sessions(
            request.scenario_id, request.user_type, request.n, request.variant
        )
    except ValueError as exc:
        # run_simulated_session raises ValueError for an unknown
        # scenario_id — same 404 semantics as /chat's persona lookup.
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SimulateResponse(
        sessions=[
            SimulatedSessionSummary(
                id=r.id,
                variant=r.variant,
                outcome=r.outcome,
                overall_score=r.overall_score,
                final_outcome_value=r.final_outcome_value,
            )
            for r in records
        ],
        summary=summarize(records),
    )
