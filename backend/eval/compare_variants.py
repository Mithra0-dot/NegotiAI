"""Pulls simulated_sessions grouped by variant for a scenario and runs
the statistical comparison (see eval/statistics.py) between
StrategyVariant.DEFAULT and StrategyVariant.HARDLINE. Two entry points,
both funneling through compare_variants():
  - CLI: `python -m eval.compare_variants --scenario-id ... [--user-type ...]`
  - HTTP: GET /eval/compare (see eval/router.py)
"""

import argparse

from app.db import SessionLocal
from app.personas import get_persona
from app.strategies.models import StrategyVariant
from eval.repository import list_simulated_sessions
from eval.statistics import ComparisonResult, compare_two_samples
from eval.user_types import UserType


class UnknownScenarioError(ValueError):
    """scenario_id doesn't match any known persona — see app.personas.get_persona."""


class InsufficientSessionsError(ValueError):
    """A variant group has fewer than the minimum sessions needed to
    compare (see eval.statistics.MIN_N_PER_GROUP)."""


def compare_variants(
    scenario_id: str, user_type: UserType | None = None
) -> ComparisonResult:
    """Compares overall_score between the default and hardline variants
    for `scenario_id`, optionally restricted to a single `user_type`
    (omit to pool every simulated user type together). Raises ValueError
    for an unknown scenario, or if either variant has fewer than 3
    persisted sessions to compare.

    Pulls with limit=None (see eval/repository.py's list_simulated_sessions
    docstring) — a statistical comparison needs every matching row, not
    just the most recent 100."""
    if get_persona(scenario_id) is None:
        raise UnknownScenarioError(f"Unknown scenario_id: {scenario_id!r}")

    db = SessionLocal()
    try:
        default_records = list_simulated_sessions(
            db,
            scenario_id=scenario_id,
            user_type=user_type,
            variant=StrategyVariant.DEFAULT,
            limit=None,
        )
        hardline_records = list_simulated_sessions(
            db,
            scenario_id=scenario_id,
            user_type=user_type,
            variant=StrategyVariant.HARDLINE,
            limit=None,
        )
    finally:
        db.close()

    default_scores = [r.overall_score for r in default_records]
    hardline_scores = [r.overall_score for r in hardline_records]

    # eval.statistics.compare_two_samples() enforces the same >=3-per-group
    # floor, but with generic a/b labels — checking again here gives a
    # message that actually tells the caller what to do about it.
    if len(default_scores) < 3 or len(hardline_scores) < 3:
        user_type_desc = user_type.value if user_type is not None else "any"
        raise InsufficientSessionsError(
            "Not enough simulated sessions to compare "
            f"(scenario_id={scenario_id!r}, user_type={user_type_desc!r}): "
            f"default={len(default_scores)}, hardline={len(hardline_scores)}, "
            "need at least 3 of each. Run more via `python -m eval.run_simulation`."
        )

    return compare_two_samples(
        StrategyVariant.DEFAULT.value,
        default_scores,
        StrategyVariant.HARDLINE.value,
        hardline_scores,
    )


def _print_report(
    scenario_id: str, user_type: UserType | None, result: ComparisonResult
) -> None:
    user_type_desc = user_type.value if user_type is not None else "any"
    print(f"\nscenario_id={scenario_id!r}  user_type={user_type_desc!r}\n")
    for group in (result.group_a, result.group_b):
        print(f"  {group.label:>10}: n={group.n:<4} mean={group.mean:6.2f}  std={group.std:6.2f}")

    print(f"\nTest: {result.test_name}")
    print(f"  statistic = {result.statistic:.4f}")
    print(f"  p-value   = {result.p_value:.4f}  (alpha={result.alpha})")
    verdict = "SIGNIFICANT" if result.is_significant else "not significant"
    print(f"  -> {verdict} at alpha={result.alpha}")

    print(f"\nMean difference ({result.group_b.label} - {result.group_a.label}): {result.mean_difference:.2f}")
    lo, hi = result.confidence_interval_95
    print(f"95% CI on the difference in means: [{lo:.2f}, {hi:.2f}]")

    if result.notes:
        print("\nNotes:")
        for note in result.notes:
            print(f"  - {note}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the DEFAULT vs HARDLINE strategy variants for a scenario."
    )
    parser.add_argument("--scenario-id", required=True, help="e.g. salary-negotiation")
    parser.add_argument(
        "--user-type",
        choices=[t.value for t in UserType],
        default=None,
        help="Optional filter; omit to pool all simulated user types together",
    )
    args = parser.parse_args()

    user_type = UserType(args.user_type) if args.user_type else None
    result = compare_variants(args.scenario_id, user_type)
    _print_report(args.scenario_id, user_type, result)


if __name__ == "__main__":
    main()
