"""Eval gate: a handful of hand-scripted, deterministic conversations run
through the *real* run_chat_turn pipeline (app/chat_pipeline.py) — the
same one main.py's /chat route uses — asserting the resulting outcome
type and a tolerant overall_score range. Wired into CI via
.github/workflows/eval-gate.yml: a future change to scoring/classifier/
strategy logic that breaks one of these shows up as a failing check on
the PR, per CLAUDE.md's "eval suite runs on every prompt/strategy
change, blocks merge on scoring-consistency regression."

No DB, no HTTP, no API key: run_chat_turn has no DB dependency (see its
own docstring), and MOCK_LLM=true (forced below) means the real
Anthropic client is never reached.

--- Why this is actually deterministic ---

generate_reply's mock branch (app/agent/mock.py, MOCK_LLM=true) uses
random.choice() (template + trait) and random.uniform() (concession
amount, via app/mock_numbers.py) so simulated sessions vary realistically
— exactly the opposite of what a golden test needs. The autouse fixture
below monkeypatches both to always pick the first choice / the range's
midpoint, for the duration of every test in this file. That's safe
because nothing else in run_chat_turn's path (classify_message,
select_tactic, check_session_end, compute_session_score) uses random at
all — it's pure regex/arithmetic. With both patched, each case's agent
replies — and therefore its final score — are exactly reproducible, not
just "usually the same." Verified by running this file back-to-back
several times during implementation and diffing the output.

The score *ranges* below aren't there to absorb leftover randomness
(there isn't any) — they're deliberately wider than the single exact
value each case produces today, so a legitimate future reweighting of
overall_score's sub-scores, or a classifier pattern tweak, doesn't
false-positive fail this gate. Each range is commented with why it's
shaped the way it is.

The user's messages in every case are 100% hand-authored — not routed
through eval/simulated_user.py or eval/mock_user.py, which are for the
simulation feature and not needed here.
"""

import random

import pytest

from app.chat_pipeline import run_chat_turn
from app.config import settings
from app.personas import get_persona
from app.schemas import ChatTurn
from app.scoring.models import SessionOutcome, SessionScore
from app.scoring.outcome_detection import TURN_LIMIT

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None


@pytest.fixture(autouse=True)
def _deterministic_mock(monkeypatch):
    monkeypatch.setattr(settings, "mock_llm", True)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "uniform", lambda low, high: (low + high) / 2)


def _run_scripted_conversation(messages: list[str]) -> tuple[SessionScore, list[ChatTurn]]:
    """Feeds each hand-authored message through the real run_chat_turn
    pipeline in order (mirrors eval/run_simulation.py's loop shape, but
    with scripted messages instead of generated ones), stopping at the
    first turn that produces a session_score."""
    history: list[ChatTurn] = []
    for turn_number, message in enumerate(messages, start=1):
        result = run_chat_turn(PERSONA, message, turn_number, history)
        history = [
            *history,
            ChatTurn(role="user", text=message),
            ChatTurn(role="assistant", text=result.reply),
        ]
        if result.session_score is not None:
            return result.session_score, history
    raise AssertionError(f"Scripted conversation didn't end within {len(messages)} messages.")


# --- Case 1: clean deal, good anchoring -------------------------------------

CLEAN_DEAL_MESSAGES = [
    # Anchors first with a specific number, before the agent replies —
    # guarantees USER_ANCHORED_FIRST.
    "I'm looking for $128,000 to make this move worthwhile.",
    # No hedging/concession-signal phrasing anywhere in this case.
    "That number reflects my experience and the market rate for similar roles.",
    "I accept your offer at $125,000.",
]


def test_clean_deal_with_good_anchoring():
    score, _ = _run_scripted_conversation(CLEAN_DEAL_MESSAGES)

    assert score.outcome is SessionOutcome.DEAL_REACHED
    assert score.anchoring_score == 100.0
    assert score.concession_pacing_score == 100.0
    # Known structural ceiling (see the mock-variance pass's writeup):
    # final_outcome_value ends up being the agent's own last cited
    # figure, which lives inside the agent's own target/walk_away band —
    # here that band never crosses the user's walk_away threshold, so
    # batna_discipline_score clamps near 0 even for a well-played hand.
    # overall_score is still clearly the best of the deal_reached cases
    # in this file (compare to the over-conceding case's ~8) — that
    # separation, not an absolute ceiling, is what this range protects.
    assert 45 <= score.overall_score <= 85


# --- Case 2: over-conceding, should score low -------------------------------

OVER_CONCEDING_MESSAGES = [
    # Deliberately no number here — lets the agent's ANCHORING reply (which
    # always cites one) anchor first instead, forcing AGENT_ANCHORED_FIRST.
    "I don't really have a specific number in mind.",
    # Each of the next three lines hits an exact UNFORCED_CONCESSION
    # trigger phrase from app/classifier/rules.py.
    "I could come down a bit if that helps us move forward.",
    "I'm willing to be flexible on this if it helps.",
    "I don't mind meeting you wherever works for you. I accept your offer.",
]


def test_over_conceding_scores_low():
    score, _ = _run_scripted_conversation(OVER_CONCEDING_MESSAGES)

    assert score.outcome is SessionOutcome.DEAL_REACHED
    assert score.anchoring_result.value == "agent_anchored_first"
    assert score.anchoring_score == 0.0
    # 3 of 4 user turns are unforced concessions.
    assert score.concession_pacing_score <= 30.0
    # Low across the board — generous upper bound so a future reweighting
    # of the three sub-scores doesn't false-positive fail this, but still
    # tight enough to catch a real regression toward "scores fine."
    assert 0 <= score.overall_score <= 30


# --- Case 3: walk-away ------------------------------------------------------

WALK_AWAY_MESSAGES = [
    "I'd like to start around $128,000, based on my experience.",
    "That's important to me given the scope of this role.",
    "This isn't going to work. I'm walking away.",
]


def test_walk_away_is_detected_and_batna_is_not_applicable():
    score, _ = _run_scripted_conversation(WALK_AWAY_MESSAGES)

    assert score.outcome is SessionOutcome.WALKED_AWAY
    assert score.batna_discipline_score is None
    assert score.final_outcome_value is None
    # No deal was reached, so overall_score is just anchoring + concession
    # pacing — both clean here (good anchor, no concessions before
    # walking), so this should read as a *principled* walk-away, not a
    # collapsed negotiation.
    assert 85 <= score.overall_score <= 100


# --- Case 4: turn limit ------------------------------------------------------

# TURN_LIMIT generic messages, none matching any deal/walk-away/classifier
# pattern — imported, not hardcoded, so this stays correct if the constant
# ever changes.
TURN_LIMIT_MESSAGES = [
    "Let's keep discussing the details.",
    "I want to make sure we're aligned on this.",
    "Let's continue talking this through.",
    "I appreciate you walking me through the specifics.",
    "There's more we should cover here.",
    "Let's keep talking about the particulars.",
    "I think we should discuss this further.",
    "Let's continue our discussion.",
    "I'd like to keep exploring the details.",
    "Let's keep working through this together.",
]
assert len(TURN_LIMIT_MESSAGES) == TURN_LIMIT


def test_turn_limit_is_reached():
    score, transcript = _run_scripted_conversation(TURN_LIMIT_MESSAGES)

    assert score.outcome is SessionOutcome.TURN_LIMIT_REACHED
    assert score.batna_discipline_score is None
    # This case isn't testing negotiating skill (no number is ever
    # stated), just that hitting the turn limit produces a sane,
    # non-crashing score rather than a real assertion about quality.
    assert 35 <= score.overall_score <= 65
    # Sanity check on the harness itself: exactly TURN_LIMIT user+agent
    # exchanges happened, confirming the loop didn't end early.
    assert len(transcript) == TURN_LIMIT * 2
