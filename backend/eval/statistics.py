"""Two-sample statistical comparison between two groups of scores — the
test-selection procedure CLAUDE.md asks for ("Apply real statistical
testing... no eyeballing results"). Pure and DB-free: takes two plain
lists of floats and two labels, returns a ComparisonResult. All the
domain-specific plumbing (pulling `default`/`hardline` groups for a
scenario out of `simulated_sessions`) lives in eval/compare_variants.py,
which calls into this module — kept separate so this file is testable
with arbitrary synthetic data, no DB/fixtures required.

--- How the test is chosen (see the approved plan for the full rationale) ---

1. Shapiro-Wilk (scipy.stats.shapiro) checks each group's normality —
   the most powerful normality test at the small-to-moderate sample
   sizes this project actually runs at (CLAUDE.md's target: 50-100+
   simulated sessions per variant; Shapiro-Wilk's valid/recommended
   range is roughly n=3-5000).
2. Below NORMALITY_CHECK_MIN_N per group, or on a zero-variance
   (constant) group, the check is skipped rather than trusted — a
   normality test on too few points, or on data with no spread at all,
   has no real power to tell you anything, so "it passed" would be a
   false signal. Skipping routes straight to the nonparametric branch.
3. If both groups clear the check (p > ALPHA): Welch's t-test
   (scipy.stats.ttest_ind(equal_var=False)) — Welch's rather than
   Student's because there's no reason to assume the two groups have
   equal variance, and Welch's costs nothing when they happen to.
   Otherwise: Mann-Whitney U (scipy.stats.mannwhitneyu) — the standard
   nonparametric analog, robust to skew/outliers/non-normality.
4. Below MIN_N_PER_GROUP, neither test is meaningful (Shapiro-Wilk is
   undefined below n=3) — compare_two_samples() raises rather than
   returning a number that looks like a real result.

The 95% confidence interval is ALWAYS Welch's t-interval on the
difference in means, independent of which branch above supplied the
p-value. This is deliberate: Mann-Whitney's own natural interval target
is a location-shift/median-based one (Hodges-Lehmann), not a difference
in means — reporting that under a "CI on the difference in means" label
would be mislabeling it. Welch's interval remains a reasonable
large/moderate-sample approximation by the CLT regardless of which test
was chosen for significance (a distinct concern from whether the raw
per-group distribution is exactly normal). Noted explicitly in the
result's `notes` so it's never misread as the other kind of interval.
"""

import warnings
from typing import Literal

import numpy as np
from pydantic import BaseModel
from scipy import stats

ALPHA = 0.05
# Shapiro-Wilk is undefined below this — see module docstring point 4.
MIN_N_PER_GROUP = 3
# Below this, Shapiro-Wilk has too little power to trust — see point 2.
NORMALITY_CHECK_MIN_N = 8
# Soft floor, not enforced — CLAUDE.md's target scale is 50-100+ per
# variant; below this the comparison still runs but is flagged as
# preliminary in `notes`.
RECOMMENDED_MIN_N = 20


class GroupSummary(BaseModel):
    label: str
    n: int
    mean: float
    std: float


class ComparisonResult(BaseModel):
    group_a: GroupSummary
    group_b: GroupSummary
    test_name: Literal["welch_t_test", "mann_whitney_u"]
    statistic: float
    p_value: float
    alpha: float
    is_significant: bool
    # group_b.mean - group_a.mean — sign convention is the caller's to
    # interpret (eval/compare_variants.py passes hardline as group_b, so
    # positive means hardline scored higher).
    mean_difference: float
    confidence_interval_95: tuple[float, float]
    # Shapiro-Wilk p-value per group, or None where the check was skipped
    # (see NORMALITY_CHECK_MIN_N / zero-variance handling above) — this is
    # what makes `test_name`'s choice inspectable rather than a black box.
    normality: dict[str, float | None]
    notes: list[str]


def _shapiro_p_value(scores: np.ndarray, notes: list[str], label: str) -> float | None:
    n = len(scores)
    if n < NORMALITY_CHECK_MIN_N:
        notes.append(
            f"{label}: skipped the Shapiro-Wilk normality check (n={n} < "
            f"{NORMALITY_CHECK_MIN_N}) — too few points for the check to "
            "carry any real power; routed toward Mann-Whitney U instead."
        )
        return None
    if np.std(scores) == 0:
        notes.append(
            f"{label}: every score is identical (zero variance) — "
            "Shapiro-Wilk is undefined here, treated as non-normal."
        )
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = stats.shapiro(scores)
    return float(result.pvalue)


def compare_two_samples(
    label_a: str,
    scores_a: list[float],
    label_b: str,
    scores_b: list[float],
) -> ComparisonResult:
    """Compares two independent samples of scores. Raises ValueError if
    either has fewer than MIN_N_PER_GROUP observations. See module
    docstring for the full test-selection procedure."""
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)

    if len(a) < MIN_N_PER_GROUP or len(b) < MIN_N_PER_GROUP:
        raise ValueError(
            f"Need at least {MIN_N_PER_GROUP} scores per group to run a "
            f"statistical comparison (got {label_a}={len(a)}, {label_b}={len(b)})."
        )

    notes: list[str] = []
    p_a = _shapiro_p_value(a, notes, label_a)
    p_b = _shapiro_p_value(b, notes, label_b)
    both_normal = p_a is not None and p_a > ALPHA and p_b is not None and p_b > ALPHA

    # Every scipy call below passes (b, a) — not (a, b) — so that both the
    # test statistic and the CI report "group_b relative to group_a",
    # matching mean_difference's mean(b) - mean(a) convention. Getting
    # this backwards is an easy, quiet bug: scipy's own convention for
    # ttest_ind(x, y) is "x minus y", so ttest_ind(a, b) would silently
    # report the opposite sign from mean_difference — a positive
    # mean_difference next to a CI entirely below zero, contradicting
    # each other. Verified against a hand-computed case, not just reasoned
    # through, before settling on this order.
    if both_normal:
        test_name: Literal["welch_t_test", "mann_whitney_u"] = "welch_t_test"
        test_result = stats.ttest_ind(b, a, equal_var=False)
    else:
        test_name = "mann_whitney_u"
        test_result = stats.mannwhitneyu(b, a)

    # Always Welch's interval on the difference in means, regardless of
    # test_name above — see module docstring. Zero-variance groups make
    # scipy emit a "catastrophic cancellation" RuntimeWarning here; the
    # result itself degrades gracefully to a zero-width interval, so the
    # warning is expected noise in that case, not a real problem.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        welch_result = stats.ttest_ind(b, a, equal_var=False)
        ci = welch_result.confidence_interval(confidence_level=1 - ALPHA)

    notes.append(
        "The 95% confidence interval is on the difference in means "
        "(Welch's t-interval), computed the same way regardless of "
        f"whether {test_name!r} was used for the significance test above."
    )
    for label, n in ((label_a, len(a)), (label_b, len(b))):
        if n < RECOMMENDED_MIN_N:
            notes.append(
                f"{label}: n={n} is below the ~{RECOMMENDED_MIN_N}+ "
                "recommended for a stable result (CLAUDE.md's target is "
                "50-100+ per variant) — treat this comparison as preliminary."
            )

    return ComparisonResult(
        group_a=GroupSummary(label=label_a, n=len(a), mean=float(np.mean(a)), std=float(np.std(a, ddof=1))),
        group_b=GroupSummary(label=label_b, n=len(b), mean=float(np.mean(b)), std=float(np.std(b, ddof=1))),
        test_name=test_name,
        statistic=float(test_result.statistic),
        p_value=float(test_result.pvalue),
        alpha=ALPHA,
        is_significant=float(test_result.pvalue) < ALPHA,
        mean_difference=float(np.mean(b) - np.mean(a)),
        confidence_interval_95=(float(ci.low), float(ci.high)),
        normality={label_a: p_a, label_b: p_b},
        notes=notes,
    )
