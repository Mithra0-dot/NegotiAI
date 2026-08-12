"""Runs synthetic negotiation sessions: a simulated user (see
eval/simulated_user.py) role-plays against the real negotiation agent via
the same per-turn pipeline /chat uses (app/chat_pipeline.py::run_chat_turn),
so a simulated session produces a real SessionScore exactly like a
human-driven one would — no separate/approximated scoring path.

Two entry points, both funneling through run_n_sessions():
  - CLI: `python -m eval.run_simulation --scenario-id ... --user-type ... --n ...`
  - HTTP: POST /eval/simulate (see eval/router.py)

Explicitly out of scope this pass (see the approved plan): strategy
variants, statistical significance testing, MLflow tracking. This module
only generates and stores results.
"""

import argparse
import logging

from app.chat_pipeline import run_chat_turn
from app.db import SessionLocal
from app.personas import get_persona
from app.schemas import ChatTurn
from app.scoring.models import SessionScore
from app.scoring.outcome_detection import TURN_LIMIT
from eval.models import SimulatedSessionRecord
from eval.repository import save_simulated_session
from eval.simulated_user import generate_user_message
from eval.user_types import UserType

logger = logging.getLogger(__name__)


def run_simulated_session(
    scenario_id: str, user_type: UserType
) -> tuple[SessionScore, list[ChatTurn]]:
    """Runs one full simulated session turn-by-turn until it ends (deal,
    walk-away, or turn limit — same TURN_LIMIT constant check_session_end
    already enforces, reused here rather than duplicated), alternating:
    simulated user message -> the real /chat pipeline. Returns the final
    SessionScore and the full transcript. Raises ValueError for an
    unknown scenario, or AgentError (propagated from either the
    simulated-user call or the agent's own reply) if an LLM call fails
    mid-session — the caller lets a failed session fail the whole batch
    loudly rather than silently recording a partial one."""
    persona = get_persona(scenario_id)
    if persona is None:
        raise ValueError(f"Unknown scenario_id: {scenario_id!r}")

    history: list[ChatTurn] = []
    turn_number = 0
    while True:
        turn_number += 1
        user_message = generate_user_message(persona, user_type, turn_number, history)
        result = run_chat_turn(persona, user_message, turn_number, history)
        history = [
            *history,
            ChatTurn(role="user", text=user_message),
            ChatTurn(role="assistant", text=result.reply),
        ]

        if result.session_score is not None:
            return result.session_score, history

        # Defensive backstop, not the expected path: check_session_end()
        # already forces TURN_LIMIT_REACHED once turn_number >= TURN_LIMIT,
        # so session_score should always be set by then.
        if turn_number > TURN_LIMIT:
            raise RuntimeError(
                f"Simulated session for scenario_id={scenario_id!r} "
                f"user_type={user_type.value!r} exceeded TURN_LIMIT "
                "without a session_score."
            )


def run_n_sessions(
    scenario_id: str, user_type: UserType, n: int
) -> list[SimulatedSessionRecord]:
    """Runs `n` simulated sessions and persists each one to
    `simulated_sessions` (see eval/models.py). Owns its own DB session
    (via app.db.SessionLocal) rather than taking one as a parameter, so
    it's identically callable from the CLI (no request context) and from
    POST /eval/simulate (see eval/router.py)."""
    if n < 1:
        raise ValueError("n must be at least 1")

    db = SessionLocal()
    records: list[SimulatedSessionRecord] = []
    try:
        for i in range(n):
            score, transcript = run_simulated_session(scenario_id, user_type)
            record = save_simulated_session(db, scenario_id, user_type, score, transcript)
            records.append(record)
            logger.info(
                "Simulated session %d/%d done: outcome=%s overall_score=%.1f",
                i + 1,
                n,
                score.outcome.value,
                score.overall_score,
            )
    finally:
        db.close()

    return records


def summarize(records: list[SimulatedSessionRecord]) -> dict:
    """Plain descriptive rollup — counts and a mean, no significance
    testing (that's the next pass). Shared by the CLI printout and
    POST /eval/simulate's JSON response so they never drift."""
    if not records:
        return {"count": 0, "mean_overall_score": None, "outcome_counts": {}}

    outcome_counts: dict[str, int] = {}
    for record in records:
        outcome_counts[record.outcome] = outcome_counts.get(record.outcome, 0) + 1

    return {
        "count": len(records),
        "mean_overall_score": sum(r.overall_score for r in records) / len(records),
        "outcome_counts": outcome_counts,
    }


def _print_summary(records: list[SimulatedSessionRecord]) -> None:
    summary = summarize(records)
    print(f"\n{summary['count']} simulated session(s) complete.")
    if summary["count"] == 0:
        return
    print(f"Mean overall score: {summary['mean_overall_score']:.1f}")
    print("Outcome breakdown:")
    for outcome, count in summary["outcome_counts"].items():
        print(f"  {outcome}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run N simulated negotiation sessions for a scenario + user type."
    )
    parser.add_argument("--scenario-id", required=True, help="e.g. salary-negotiation")
    parser.add_argument(
        "--user-type", required=True, choices=[t.value for t in UserType]
    )
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = run_n_sessions(args.scenario_id, UserType(args.user_type), args.n)
    _print_summary(records)


if __name__ == "__main__":
    main()
