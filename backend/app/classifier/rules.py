"""Keyword/regex patterns per signal type — data only, no matching logic.

Kept separate from classifier.py so tuning these patterns "diffs cleanly"
(same rationale as personas/ and strategies/ being config-only files —
see CLAUDE.md's conventions). Every pattern is matched case-insensitively
with word boundaries; a message can trigger more than one signal type.
"""

import re

from app.classifier.models import SignalType

SIGNAL_PATTERNS: dict[SignalType, list[re.Pattern[str]]] = {
    SignalType.HEDGING: [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"\bmaybe\b",
            r"\bi guess\b",
            r"\bi think\b",
            r"\bsort of\b",
            r"\bkind of\b",
            r"\bnot sure\b",
            r"\bi suppose\b",
            r"\bperhaps\b",
            r"\bpossibly\b",
        ]
    ],
    SignalType.URGENCY: [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"\basap\b",
            r"\bas soon as possible\b",
            r"\bimmediately\b",
            r"\bright away\b",
            r"\burgent(ly)?\b",
            r"\bi really need\b",
            r"\bcan'?t wait\b",
            r"\brunning out of time\b",
            r"\bdesperate(ly)?\b",
        ]
    ],
    SignalType.PREMATURE_AGREEMENT: [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"\bsounds good\b",
            r"\bi agree\b",
            r"\bdeal\b",
            r"\bthat works\b",
            r"\bi accept\b",
            r"\blet'?s finalize\b",
            r"\bworks for me\b",
            r"\bi'?m in\b",
        ]
    ],
    SignalType.UNFORCED_CONCESSION: [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"\bi (can|could) (go|come down|lower|drop|flex)\b",
            r"\bi'?m willing to\b",
            r"\bi don'?t mind\b",
            r"\bi (can|could) live with\b",
            r"\bi'?ll accept\b",
            r"\bi (can|could) accept\b",
            r"\bi'?m ok(ay)? with less\b",
        ]
    ],
}
