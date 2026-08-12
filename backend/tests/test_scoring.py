"""Unit tests for session-end detection and scoring."""

from app.personas import get_persona
from app.personas.models import Constraints
from app.schemas import ChatTurn
from app.scoring.models import AnchoringResult, SessionOutcome
from app.scoring.outcome_detection import (
    TURN_LIMIT,
    check_session_end,
    detect_deal_reached,
    detect_walk_away,
)
from app.scoring.scorer import (
    _batna_discipline_score,
    _extract_final_outcome,
    _extract_numbers,
    _find_first_anchor,
    compute_session_score,
)

PERSONA = get_persona("salary-negotiation")
assert PERSONA is not None


# --- outcome_detection ---


def test_detect_deal_reached_positive():
    assert detect_deal_reached("Okay, we have a deal.")
    assert detect_deal_reached("I accept your offer at $120k")
    assert detect_deal_reached("Alright, I'll take it.")


def test_detect_deal_reached_neutral_text_is_clean():
    assert not detect_deal_reached("What's your budget range for this role?")


def test_detect_walk_away_positive():
    assert detect_walk_away("I'm walking away from this.")
    assert detect_walk_away("No deal, sorry.")
    assert detect_walk_away("I'm out.")


def test_detect_walk_away_neutral_text_is_clean():
    assert not detect_walk_away("Let's talk about the signing bonus.")


def test_check_session_end_ongoing_returns_none():
    assert check_session_end("What's the salary range?", "Let me think.", 1) is None


def test_check_session_end_deal_reached():
    outcome = check_session_end("I accept your offer.", "Great, welcome aboard!", 3)
    assert outcome is SessionOutcome.DEAL_REACHED


def test_check_session_end_walk_away_takes_priority_over_deal():
    # Contrived: message matches both — walk-away must win.
    text = "No deal, I'm walking away from this."
    outcome = check_session_end(text, "Understood.", 3)
    assert outcome is SessionOutcome.WALKED_AWAY


def test_check_session_end_turn_limit():
    outcome = check_session_end("Still thinking it over.", "Take your time.", TURN_LIMIT)
    assert outcome is SessionOutcome.TURN_LIMIT_REACHED


def test_check_session_end_below_turn_limit_is_none():
    outcome = check_session_end(
        "Still thinking it over.", "Take your time.", TURN_LIMIT - 1
    )
    assert outcome is None


# --- scorer: number extraction ---


def test_extract_numbers_handles_dollar_comma_and_k():
    assert _extract_numbers("My offer is $120,000.") == [120000.0]
    assert _extract_numbers("Let's say 95k") == [95000.0]
    assert _extract_numbers("I'd take 55%") == [55.0]


def test_extract_numbers_empty_when_none_present():
    assert _extract_numbers("Let's talk about the role.") == []


# --- scorer: anchoring ---


def test_find_first_anchor_user_first():
    transcript = [
        ChatTurn(role="user", text="I was hoping for $130,000."),
        ChatTurn(role="assistant", text="Let's discuss."),
    ]
    assert _find_first_anchor(transcript) is AnchoringResult.USER_ANCHORED_FIRST


def test_find_first_anchor_agent_first():
    transcript = [
        ChatTurn(role="assistant", text="Our band tops out at $122,000."),
        ChatTurn(role="user", text="Understood."),
    ]
    assert _find_first_anchor(transcript) is AnchoringResult.AGENT_ANCHORED_FIRST


def test_find_first_anchor_undetermined_with_no_numbers():
    transcript = [
        ChatTurn(role="user", text="Thanks for the offer."),
        ChatTurn(role="assistant", text="Of course."),
    ]
    assert _find_first_anchor(transcript) is AnchoringResult.UNDETERMINED


# --- scorer: BATNA discipline ---


def test_batna_score_higher_is_better_direction():
    constraints = Constraints(target=130_000, walk_away=115_000, unit="USD/year")
    assert _batna_discipline_score(130_000, constraints) == 100.0
    assert _batna_discipline_score(115_000, constraints) == 0.0
    # Halfway between walk_away and target.
    assert _batna_discipline_score(122_500, constraints) == 50.0


def test_batna_score_lower_is_better_direction():
    # Apartment-lease style: target < walk_away (lower rent is better).
    constraints = Constraints(target=2_000, walk_away=2_200, unit="USD/month")
    assert _batna_discipline_score(2_000, constraints) == 100.0
    assert _batna_discipline_score(2_200, constraints) == 0.0
    assert _batna_discipline_score(2_100, constraints) == 50.0


def test_batna_score_clamps_outside_the_range():
    constraints = Constraints(target=130_000, walk_away=115_000, unit="USD/year")
    assert _batna_discipline_score(150_000, constraints) == 100.0  # beyond target
    assert _batna_discipline_score(100_000, constraints) == 0.0  # worse than walk_away


def test_extract_final_outcome_takes_last_number_in_transcript():
    transcript = [
        ChatTurn(role="assistant", text="We could start at $105,000."),
        ChatTurn(role="user", text="I was hoping for closer to $130,000."),
        ChatTurn(role="assistant", text="Let's meet at $120,000."),
        ChatTurn(role="user", text="I accept your offer at $120,000."),
    ]
    assert _extract_final_outcome(transcript) == 120_000.0


def test_extract_final_outcome_none_when_no_numbers():
    transcript = [ChatTurn(role="user", text="Sounds good to me.")]
    assert _extract_final_outcome(transcript) is None


# --- compute_session_score end-to-end ---


def test_compute_session_score_deal_reached_end_to_end():
    transcript = [
        ChatTurn(role="assistant", text="Our band tops out at $105,000."),
        ChatTurn(role="user", text="I was hoping for $130,000."),
        ChatTurn(role="assistant", text="I could do $120,000."),
        ChatTurn(role="user", text="I accept your offer at $120,000."),
        ChatTurn(role="assistant", text="Great, welcome aboard!"),
    ]
    score = compute_session_score(PERSONA, transcript, SessionOutcome.DEAL_REACHED)

    assert score.outcome is SessionOutcome.DEAL_REACHED
    assert score.anchoring_result is AnchoringResult.AGENT_ANCHORED_FIRST
    assert score.anchoring_score == 0.0
    assert score.final_outcome_value == 120_000.0
    assert score.batna_discipline_score is not None
    assert 0 <= score.batna_discipline_score <= 100
    assert 0 <= score.overall_score <= 100
    assert score.notes == []
    assert score.user_target_range == PERSONA.user_constraints


def test_compute_session_score_walk_away_has_no_batna_score():
    transcript = [
        ChatTurn(role="user", text="This isn't going to work for me."),
        ChatTurn(role="assistant", text="Understood, sorry we couldn't agree."),
    ]
    score = compute_session_score(PERSONA, transcript, SessionOutcome.WALKED_AWAY)

    assert score.outcome is SessionOutcome.WALKED_AWAY
    assert score.batna_discipline_score is None
    assert score.final_outcome_value is None
    assert any("not applicable" in note for note in score.notes)
    assert score.user_target_range == PERSONA.user_constraints


def test_compute_session_score_deal_reached_but_no_number_found():
    transcript = [
        ChatTurn(role="user", text="Sounds good, let's finalize."),
        ChatTurn(role="assistant", text="Great, we have a deal."),
    ]
    score = compute_session_score(PERSONA, transcript, SessionOutcome.DEAL_REACHED)

    assert score.batna_discipline_score is None
    assert score.final_outcome_value is None
    assert any("Could not extract" in note for note in score.notes)


def test_compute_session_score_concession_ratio_reflects_user_turns():
    transcript = [
        ChatTurn(role="user", text="I guess I could accept a bit less."),  # concession
        ChatTurn(role="assistant", text="Good to hear."),
        ChatTurn(role="user", text="What's the timeline for onboarding?"),  # neutral
    ]
    score = compute_session_score(PERSONA, transcript, SessionOutcome.TURN_LIMIT_REACHED)
    assert score.concession_pacing_ratio == 0.5
    assert score.concession_pacing_score == 50.0
