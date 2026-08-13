"""Shared math for realistic, bounded random number movement in mock/demo
negotiation text — used by both app/agent/mock.py (the opponent's mock
replies) and eval/mock_user.py (the simulated user's mock replies), so
the two share one formula instead of drifting apart. `eval/` already
depends on `app/` one-directionally elsewhere in this project, so this
lives here rather than in eval/.

This exists purely to give MOCK_LLM=true sessions *some* realistic,
bounded score variance to demo/statistically-compare without spending
API credits — every line built from it is still prefixed `[mock]`
(existing convention, app/agent/mock.py's generate_mock_reply /
eval/mock_user.py's generate_mock_user_message), and it is explicitly
NOT a claim of real negotiation intelligence:

- This is a pure per-call formula, not a stateful simulation. There's no
  "current offer" tracked between turns — each call recomputes an
  independent random draw, weighted by how far into the negotiation this
  turn is (`turn_number`). A session's numbers trend in the right
  direction on average, but aren't a perfectly smooth monotonic curve —
  acceptable for demo/bounded-variance purposes, not a model of rational
  bargaining.
- The mock user's turn-by-turn *closing* decision (accept / walk away —
  see eval/user_types.py's ClosingTendency, used by eval/mock_user.py) is
  a completely separate random process from the numeric movement here.
  The two aren't coupled into "a deal closes when the numbers converge"
  — a session can plausibly close on a number that, read literally,
  looks like a bad deal for one side. That's a known simplification, not
  a bug: building real convergence logic would be building an actual
  negotiation simulator, which is out of scope for a MOCK_LLM stand-in.
"""

import random

from app.personas.models import Constraints


def concession_value(
    constraints: Constraints,
    turn_number: int,
    concession_range: tuple[float, float],
    turn_limit: int,
) -> float:
    """Returns a number starting at `constraints.target` on turn 1 and
    drifting toward `constraints.walk_away` as `turn_number` approaches
    `turn_limit`, scaled by `concession_range` (min_fraction,
    max_fraction — how far toward walk_away this tactic/user-type is
    plausibly willing to move). Each call draws its own random fraction
    within that band, weighted by progress — see module docstring for
    why this is deliberately not a persistent, perfectly monotonic curve.

    Direction-agnostic: works the same whether walk_away is numerically
    above or below target (e.g. a hiring manager conceding *up* from a
    low anchor vs. a landlord conceding *down* from a high one) — it's
    just linear interpolation between this side's own two reference
    points, whichever direction that line happens to go.
    """
    progress = min(1.0, max(0.0, (turn_number - 1) / max(1, turn_limit - 1)))
    low, high = concession_range
    fraction = random.uniform(low, high) * progress
    value = constraints.target + fraction * (constraints.walk_away - constraints.target)
    return _round_for_unit(value, constraints.unit)


def _round_for_unit(value: float, unit: str) -> float:
    """Whole numbers for USD-style units, one decimal for percentages.
    Deliberately simple — not attempting "nice round number" realism
    (nearest 500/1000, etc.), see module docstring's scope note."""
    if "%" in unit:
        return round(value, 1)
    return round(value)
