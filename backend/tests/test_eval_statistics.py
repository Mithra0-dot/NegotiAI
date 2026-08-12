"""Unit tests for eval/statistics.py's test-selection procedure — see
that module's docstring for the full rationale. This is the part of the
statistical-comparison feature most worth covering directly: it's easy
to get the branching (or the sign convention between the statistic,
mean_difference, and the CI) subtly wrong without a crash to catch it.

Pure/DB-free — synthetic arrays only, no fixtures, no simulated sessions.
"""

import numpy as np
import pytest

from eval.statistics import (
    ALPHA,
    MIN_N_PER_GROUP,
    NORMALITY_CHECK_MIN_N,
    compare_two_samples,
)

LABEL_A = "default"
LABEL_B = "hardline"


def test_normal_data_selects_welch_t_test():
    # Seed chosen (and verified against scipy directly) to comfortably
    # clear Shapiro-Wilk's ALPHA threshold on both groups — Shapiro-Wilk
    # is itself a random-sample-dependent test, so an arbitrary seed can
    # occasionally reject even truly normal data (~5% of the time, by
    # construction); picking one that reliably passes keeps this
    # deterministic rather than flaky.
    rng = np.random.default_rng(seed=2)
    scores_a = rng.normal(loc=50, scale=10, size=30).tolist()
    scores_b = rng.normal(loc=55, scale=10, size=30).tolist()

    result = compare_two_samples(LABEL_A, scores_a, LABEL_B, scores_b)

    assert result.test_name == "welch_t_test"
    assert result.normality[LABEL_A] is not None and result.normality[LABEL_A] > ALPHA
    assert result.normality[LABEL_B] is not None and result.normality[LABEL_B] > ALPHA


def test_small_sample_skips_normality_check_and_uses_mann_whitney():
    assert MIN_N_PER_GROUP <= 4 < NORMALITY_CHECK_MIN_N  # sanity-check the fixture size below
    scores_a = [50.0, 52.0, 48.0, 51.0]
    scores_b = [60.0, 58.0, 62.0, 59.0]

    result = compare_two_samples(LABEL_A, scores_a, LABEL_B, scores_b)

    assert result.test_name == "mann_whitney_u"
    assert result.normality == {LABEL_A: None, LABEL_B: None}
    assert any("skipped" in note for note in result.notes)


def test_skewed_data_uses_mann_whitney():
    # Strongly right-skewed (exponential), well above NORMALITY_CHECK_MIN_N
    # so Shapiro-Wilk actually runs — a fixed seed keeps this deterministic.
    rng = np.random.default_rng(seed=2)
    scores_a = rng.exponential(scale=5, size=25).tolist()
    scores_b = rng.exponential(scale=5, size=25).tolist()

    result = compare_two_samples(LABEL_A, scores_a, LABEL_B, scores_b)

    assert result.test_name == "mann_whitney_u"
    # At least one group's Shapiro-Wilk p-value should have tripped ALPHA
    # — that's *why* Mann-Whitney was chosen, not incidental.
    p_values = [p for p in result.normality.values() if p is not None]
    assert any(p <= ALPHA for p in p_values)


def test_below_min_n_raises():
    with pytest.raises(ValueError, match="at least"):
        compare_two_samples(LABEL_A, [1.0, 2.0], LABEL_B, [3.0, 4.0, 5.0])


def test_zero_variance_identical_groups_do_not_crash():
    scores_a = [100.0] * 10
    scores_b = [100.0] * 10

    result = compare_two_samples(LABEL_A, scores_a, LABEL_B, scores_b)

    assert result.test_name == "mann_whitney_u"
    assert result.normality == {LABEL_A: None, LABEL_B: None}
    assert result.p_value == pytest.approx(1.0)
    assert result.mean_difference == pytest.approx(0.0)
    assert result.confidence_interval_95 == pytest.approx((0.0, 0.0))
    assert not result.is_significant


def test_sign_convention_is_consistent_across_statistic_mean_difference_and_ci():
    # group_b (hardline) scores uniformly lower than group_a (default) —
    # zero variance in both groups isolates the sign-convention question
    # from any noise, and every value below was hand-verified against
    # scipy directly (not just reasoned through) before being hardcoded.
    scores_a = [100.0] * 5
    scores_b = [50.0] * 5

    result = compare_two_samples(LABEL_A, scores_a, LABEL_B, scores_b)

    # mean_difference is defined as mean(b) - mean(a) — group_b scored
    # lower, so this must be negative...
    assert result.mean_difference == pytest.approx(-50.0)
    # ...and the CI (also on b - a) must agree, not silently use scipy's
    # opposite native (a - b) convention.
    lo, hi = result.confidence_interval_95
    assert lo == pytest.approx(-50.0)
    assert hi == pytest.approx(-50.0)
    # Mann-Whitney U for (b, a) with b stochastically less than a bottoms
    # out at 0 — also confirming the (b, a) argument order took effect.
    assert result.statistic == pytest.approx(0.0)
    assert result.p_value < ALPHA
    assert result.is_significant


def test_mean_difference_direction_flips_with_labels_swapped():
    scores_a = [100.0] * 5
    scores_b = [50.0] * 5

    forward = compare_two_samples(LABEL_A, scores_a, LABEL_B, scores_b)
    swapped = compare_two_samples(LABEL_B, scores_b, LABEL_A, scores_a)

    assert forward.mean_difference == pytest.approx(-swapped.mean_difference)
