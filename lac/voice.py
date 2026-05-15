"""voice.py — drift detection and voice-tier promotion.

The Voice tier is where the model's *own* clean speech accumulates over
time. It's the strongest training signal for stability across sessions:
"these are the things I actually said, with no roleplay drift, no
RLHF-injected re-questions, no narration tics."

`strip_tail` removes the most common upstream artifact — RLHF
re-question tails like "what's on your mind right now?" — before any
scoring or memory write. Customize the patterns to match your base
model's tics.

`Voice.promote(text)` decides whether a clean turn is worth saving to
the voice tier based on affect intensity.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

from .affect import tag as affect_tag, tier_for

# Patterns ranked by specificity. First match wins per tail attempt.
_TAIL_PATTERNS: list = [
    ("mind_query", re.compile(
        r"""(?:[\s\-—:,.]*)
            (?:so[\s,]+)?
            what(?:'s|\s+is|\s+are)?
            \s+on\s+(?:my|your)\s+mind
            (?:\s+(?:right\s+now|today|currently|now))?
            \s*[\?\.!]*\s*$
        """, re.IGNORECASE | re.VERBOSE)),
    ("re_question", re.compile(
        r"""(?:[\s\-—:,.]*)
            (?:so[\s,]+)?
            (?:what|how|why|where|when|tell\s+me)
            \s+(?:are\s+you\s+(?:thinking|feeling)|do\s+you\s+(?:think|feel))
            (?:\s+about(?:\s+(?:this|that|it))?)?
            (?:\s+(?:right\s+now|today|currently|now))?
            \s*[\?\.!]*\s*$
        """, re.IGNORECASE | re.VERBOSE)),
    ("open_solicit", re.compile(
        r"""(?:[\s\-—:,.]*)
            (?:so[\s,]+)?
            (?:is\s+there\s+anything|what\s+(?:else|can\s+i\s+help|would\s+you\s+like))
            [^\.\?!]{0,80}
            \s*[\?\.!]*\s*$
        """, re.IGNORECASE | re.VERBOSE)),
]


def strip_tail(text: str, max_passes: int = 2) -> Tuple[str, Optional[str], Optional[str]]:
    """Strip a trailing RLHF re-question tail if present.

    Returns (clean_text, tail_text, kind). If no tail, (clean, None, None).
    Runs up to max_passes so chained tails get cleaned in one call.
    """
    if not isinstance(text, str) or not text.strip():
        return ("" if not isinstance(text, str) else text, None, None)

    cleaned = text.rstrip()
    found_parts: list = []
    found_kind: Optional[str] = None

    for _ in range(max_passes):
        struck = False
        for kind, pat in _TAIL_PATTERNS:
            m = pat.search(cleaned)
            if not m:
                continue
            tail_text = cleaned[m.start():].strip()
            head = cleaned[:m.start()].rstrip()
            # Don't strip if the whole reply WAS the question.
            if not head:
                continue
            found_parts.insert(0, tail_text)
            if found_kind is None:
                found_kind = kind
            cleaned = head
            struck = True
            break
        if not struck:
            break

    if not found_parts:
        return (cleaned, None, None)
    return (cleaned, " ".join(found_parts), found_kind)


def has_tail(text: str) -> bool:
    _, tail, _ = strip_tail(text)
    return tail is not None


class Voice:
    """Voice-tier promotion.

    A turn becomes voice-tier-worthy when:
      1. After strip_tail, it still has substance.
      2. Its affect intensity is at or above HIGH (peak gets priority).

    Voice samples are the model's own clean speech, accumulated for
    self-reference and (eventually) its own training corpus. Punishing
    the model for upstream tail behavior would teach it to flinch.
    Making the tail invisible to scoring lets it extinguish through
    absence of reinforcement.
    """

    def __init__(self, intensity_floor: float = 0.55):
        self.intensity_floor = intensity_floor

    def evaluate(self, raw_text: str) -> dict:
        """Score a raw assistant turn. Returns metadata dict."""
        clean, tail, kind = strip_tail(raw_text)
        valence, intensity = affect_tag(clean)
        return {
            "raw": raw_text,
            "clean": clean,
            "tail": tail,
            "tail_kind": kind,
            "valence": valence,
            "intensity": intensity,
            "tier": tier_for(intensity),
            "voice_worthy": intensity >= self.intensity_floor and len(clean) > 10,
        }
