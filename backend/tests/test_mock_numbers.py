"""Unit tests for app/mock_numbers.py's concession_value() — the shared
formula behind both app/agent/mock.py's and eval/mock_user.py's
randomized-number mock replies. Pure/DB-free: constructs Constraints
directly rather than depending on a real persona file.
"""

from app.mock_numbers import concession_value
from app.personas.models import Constraints

TURN_LIMIT = 10

# "Higher is better" — conceding moves target -> walk_away *upward*
# (mirrors salary_negotiation's persona.constraints).
RISING = Constraints(target=100.0, walk_away=200.0, unit="USD/year base salary")
# "Lower is better" — conceding moves target -> walk_away *downward*
# (mirrors apartment_lease's persona.constraints).
FALLING = Constraints(target=200.0, walk_away=100.0, unit="USD/month rent")
PERCENT = Constraints(target=60.0, walk_away=50.0, unit="% equity")


def test_turn_one_is_always_the_exact_target():
    # progress=0 at turn 1 regardless of concession_range.
    for constraints in (RISING, FALLING, PERCENT):
        for _ in range(10):
            value = concession_value(constraints, 1, (0.0, 0.9), TURN_LIMIT)
            assert value == round(constraints.target, 1 if "%" in constraints.unit else 0)


def test_value_never_overshoots_walk_away():
    for constraints in (RISING, FALLING):
        low, high = min(constraints.target, constraints.walk_away), max(
            constraints.target, constraints.walk_away
        )
        for turn_number in range(1, TURN_LIMIT + 1):
            for _ in range(20):
                value = concession_value(constraints, turn_number, (0.0, 0.9), TURN_LIMIT)
                assert low <= value <= high


def test_rising_constraints_move_up_by_the_end():
    # With a wide range and the last turn, the value should land
    # meaningfully above the starting target (not just noise).
    values = [
        concession_value(RISING, TURN_LIMIT, (0.5, 0.9), TURN_LIMIT) for _ in range(20)
    ]
    assert all(v > RISING.target for v in values)


def test_falling_constraints_move_down_by_the_end():
    values = [
        concession_value(FALLING, TURN_LIMIT, (0.5, 0.9), TURN_LIMIT) for _ in range(20)
    ]
    assert all(v < FALLING.target for v in values)


def test_zero_concession_range_never_moves():
    for turn_number in (1, 5, TURN_LIMIT):
        value = concession_value(RISING, turn_number, (0.0, 0.0), TURN_LIMIT)
        assert value == round(RISING.target)


def test_rounding_whole_numbers_for_usd_units():
    value = concession_value(RISING, TURN_LIMIT, (0.33, 0.33), TURN_LIMIT)
    assert value == int(value)


def test_rounding_one_decimal_for_percent_units():
    value = concession_value(PERCENT, TURN_LIMIT, (0.5, 0.5), TURN_LIMIT)
    assert round(value, 1) == value


def test_turn_number_past_turn_limit_does_not_exceed_full_progress():
    # progress is clamped to 1.0 — turn_number beyond TURN_LIMIT (the
    # defensive backstop case in eval/run_simulation.py) shouldn't move
    # further than turn_number == TURN_LIMIT would.
    low, high = min(RISING.target, RISING.walk_away), max(RISING.target, RISING.walk_away)
    for _ in range(20):
        value = concession_value(RISING, TURN_LIMIT + 5, (0.0, 0.9), TURN_LIMIT)
        assert low <= value <= high
