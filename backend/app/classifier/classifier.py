"""Rule-based concession-signal classification logic.

Consumes the pattern data in rules.py — see that module's docstring for
why the two are split. Only ever looks at the user's own message text, so
(unlike persona configs) there's no leak concern in returning the full
result to the client.
"""

from app.classifier.models import DetectedSignal, SignalType
from app.classifier.rules import SIGNAL_PATTERNS


def classify_message(text: str) -> list[DetectedSignal]:
    """Return one DetectedSignal per signal type with at least one match
    in `text` (empty list if none). Each signal's `matched_phrases` lists
    every distinct substring that triggered it, in order found."""
    detected: list[DetectedSignal] = []

    for signal_type, patterns in SIGNAL_PATTERNS.items():
        matched_phrases: list[str] = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                phrase = match.group(0)
                if phrase not in matched_phrases:
                    matched_phrases.append(phrase)

        if matched_phrases:
            detected.append(
                DetectedSignal(signal_type=signal_type, matched_phrases=matched_phrases)
            )

    return detected
