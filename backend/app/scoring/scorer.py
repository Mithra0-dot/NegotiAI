"""Computes a SessionScore once a session has ended.

BATNA discipline is a best-effort heuristic, not a precise reading: there's
no structured offer-tracking anywhere in this app, only free text, so
"the final agreed value" is taken to be the last recognizable number
(currency amount, percentage, or plain figure) anywhere in the transcript
when a deal was reached. This can't tell whose number it is, or
distinguish a real offer from an incidental figure (a date, a rejected
earlier number) — flagged in `notes` whenever it can't find one, not
silently guessed.
"""

import re

from app.classifier import classify_message
from app.classifier.models import SignalType
from app.personas.models import Constraints, PersonaInternal
from app.schemas import ChatTurn
from app.scoring.models import AnchoringResult, SessionOutcome, SessionScore

# Generic: an optional $, a number with optional comma grouping and
# decimal, then an optional %/k suffix. Deliberately loose — a documented
# heuristic, not a precise parser (see module docstring).
_NUMBER_RE = re.compile(r"\$?(\d[\d,]*(?:\.\d+)?)\s?(%|k\b)?", re.IGNORECASE)

_ANCHORING_SCORES = {
    AnchoringResult.USER_ANCHORED_FIRST: 100.0,
    AnchoringResult.AGENT_ANCHORED_FIRST: 0.0,
    AnchoringResult.UNDETERMINED: 50.0,
}


def _extract_numbers(text: str) -> list[float]:
    values: list[float] = []
    for match in _NUMBER_RE.finditer(text):
        raw, suffix = match.groups()
        value = float(raw.replace(",", ""))
        if suffix and suffix.lower() == "k":
            value *= 1000
        values.append(value)
    return values


def _find_first_anchor(transcript: list[ChatTurn]) -> AnchoringResult:
    for turn in transcript:
        if _extract_numbers(turn.text):
            return (
                AnchoringResult.USER_ANCHORED_FIRST
                if turn.role == "user"
                else AnchoringResult.AGENT_ANCHORED_FIRST
            )
    return AnchoringResult.UNDETERMINED


def _extract_final_outcome(transcript: list[ChatTurn]) -> float | None:
    for turn in reversed(transcript):
        numbers = _extract_numbers(turn.text)
        if numbers:
            return numbers[-1]
    return None


def _concession_pacing(user_turns: list[str]) -> tuple[float, float]:
    if not user_turns:
        return 0.0, 100.0
    concession_count = sum(
        1
        for text in user_turns
        if any(
            s.signal_type is SignalType.UNFORCED_CONCESSION
            for s in classify_message(text)
        )
    )
    ratio = concession_count / len(user_turns)
    return ratio, (1 - ratio) * 100


def _batna_discipline_score(
    final_value: float, user_constraints: Constraints
) -> float:
    """0 at walk_away, 100 at target (or beyond), linear between, clamped
    to [0, 100]. Direction (higher-or-lower-is-better) is inferred from
    whether target > walk_away for this scenario's user_constraints."""
    target, walk_away = user_constraints.target, user_constraints.walk_away
    span = target - walk_away
    if span == 0:
        return 100.0
    direction = 1 if span > 0 else -1
    normalized = (final_value - walk_away) * direction / abs(span)
    return max(0.0, min(1.0, normalized)) * 100


def compute_session_score(
    persona: PersonaInternal,
    transcript: list[ChatTurn],
    outcome: SessionOutcome,
) -> SessionScore:
    notes: list[str] = []

    anchoring_result = _find_first_anchor(transcript)
    anchoring_score = _ANCHORING_SCORES[anchoring_result]
    if anchoring_result is AnchoringResult.UNDETERMINED:
        notes.append("No numeric anchor detected in either party's messages.")

    user_turns = [t.text for t in transcript if t.role == "user"]
    concession_ratio, concession_score = _concession_pacing(user_turns)

    batna_score: float | None = None
    final_value: float | None = None
    if outcome is SessionOutcome.DEAL_REACHED:
        final_value = _extract_final_outcome(transcript)
        if final_value is not None:
            batna_score = _batna_discipline_score(final_value, persona.user_constraints)
        else:
            notes.append(
                "Could not extract a final agreed value from the transcript "
                "— BATNA discipline not scored."
            )
    else:
        notes.append(
            f"No deal was reached ({outcome.value}) — BATNA discipline not applicable."
        )

    sub_scores = [anchoring_score, concession_score]
    if batna_score is not None:
        sub_scores.append(batna_score)
    overall = sum(sub_scores) / len(sub_scores)

    return SessionScore(
        outcome=outcome,
        anchoring_result=anchoring_result,
        anchoring_score=anchoring_score,
        concession_pacing_ratio=concession_ratio,
        concession_pacing_score=concession_score,
        batna_discipline_score=batna_score,
        final_outcome_value=final_value,
        overall_score=overall,
        notes=notes,
        user_target_range=persona.user_constraints,
    )
