"""Shape for concession-signal classification results.

See CLAUDE.md's "Concession-signal classifier" MVP feature. This is the
rule-based (keyword/regex) version — a small transformer is a later
refinement, not this pass.
"""

from enum import Enum

from pydantic import BaseModel


class SignalType(str, Enum):
    UNFORCED_CONCESSION = "unforced_concession"
    HEDGING = "hedging"
    URGENCY = "urgency"
    PREMATURE_AGREEMENT = "premature_agreement"


class DetectedSignal(BaseModel):
    signal_type: SignalType
    # The actual substrings that triggered this signal — kept for
    # transparency/debugging so a classification is never a black box.
    matched_phrases: list[str]
