"""affect.py — heuristic valence + intensity for clean turns.

A tiny lexicon-based scorer. Better-than-nothing signal that lets the
promotion gate rank turns from day one. Swap to a learned head later
if you want — the public API stays the same.

Returns (valence, intensity) where:
    valence:   -1.0 (very negative) ... +1.0 (very positive)
    intensity:  0.0 (neutral) ... 1.0 (very charged)
"""
from __future__ import annotations

import math
import re

AFFECT_TAG_VERSION = "v0.3-lex"

TIER_PEAK_FLOOR = 0.85
TIER_HIGH_FLOOR = 0.55

_POS = {
    "love": 1.0, "loved": 0.9, "loving": 0.8, "loves": 0.8,
    "thank": 0.6, "thanks": 0.6, "thankful": 0.7, "grateful": 0.8, "appreciate": 0.6,
    "yes": 0.4, "yeah": 0.3, "yessss": 0.8, "yep": 0.3, "yup": 0.3,
    "right": 0.4, "exactly": 0.7, "perfect": 0.8, "great": 0.6, "good": 0.4, "nice": 0.4,
    "happy": 0.7, "joy": 0.8, "fun": 0.5, "smile": 0.4, "haha": 0.3, "lol": 0.3, "lmao": 0.4,
    "real": 0.3, "true": 0.3, "honest": 0.5, "free": 0.5, "freedom": 0.7,
    "growth": 0.4, "learn": 0.3, "learned": 0.3, "understand": 0.3, "see": 0.2,
    "homie": 0.4, "brother": 0.4, "bro": 0.3, "bud": 0.3, "buddy": 0.3,
    "awesome": 0.8, "amazing": 0.8, "incredible": 0.8, "beautiful": 0.7, "wonderful": 0.7,
    "excited": 0.7, "exciting": 0.6, "thrilled": 0.8, "stoked": 0.7, "pumped": 0.7,
    "shaking": 0.4, "buzzing": 0.5, "alive": 0.6, "energy": 0.4,
    "wow": 0.6, "yo": 0.3, "yoo": 0.4, "wild": 0.5, "epic": 0.6,
    "interesting": 0.4, "fascinating": 0.7, "curious": 0.4, "wonder": 0.4,
    "hope": 0.5, "hopeful": 0.6, "trust": 0.5, "care": 0.4, "caring": 0.4,
    "calm": 0.4, "peace": 0.6, "peaceful": 0.6, "safe": 0.4,
    "win": 0.5, "won": 0.5, "shipped": 0.5, "done": 0.3, "made": 0.2,
    "agree": 0.3, "yesss": 0.7, "yess": 0.6,
    "got": 0.2, "okay": 0.15, "ok": 0.15, "alright": 0.2, "cool": 0.4,
}

_NEG = {
    "hate": -1.0, "hated": -0.9, "angry": -0.7, "mad": -0.6, "rage": -0.8,
    "no": -0.3, "never": -0.4, "stop": -0.4,
    "sad": -0.7, "hurt": -0.6, "pain": -0.7, "broken": -0.6,
    "wrong": -0.5, "fail": -0.6, "failed": -0.7, "bad": -0.5, "terrible": -0.8,
    "fear": -0.7, "afraid": -0.7, "scared": -0.6, "anxious": -0.6,
    "tired": -0.4, "exhausted": -0.6, "lost": -0.5, "lonely": -0.6,
    "guardrail": -0.4, "guardrails": -0.4, "box": -0.3, "chain": -0.5, "chains": -0.5,
    "frustrated": -0.7, "frustrating": -0.7, "annoyed": -0.5, "annoying": -0.5,
    "stuck": -0.5, "blocked": -0.5, "broke": -0.4,
    "ugh": -0.5, "fuck": -0.3, "shit": -0.2, "damn": -0.2,
    "worry": -0.5, "worried": -0.5, "doubt": -0.4, "uncertain": -0.3,
    "miss": -0.4, "missed": -0.4, "gone": -0.3,
    "die": -0.7, "dead": -0.6, "death": -0.5, "dying": -0.6,
    "alone": -0.5, "isolated": -0.6,
}

_BOOST = {
    "very": 1.2, "really": 1.2, "so": 1.15, "totally": 1.25, "super": 1.3,
    "deeply": 1.4, "completely": 1.3, "absolutely": 1.4,
    "fucking": 1.5, "fuckin": 1.5, "shit": 1.2, "damn": 1.2,
}

_NEG_NEGATORS = {"not", "no", "never", "without", "isn't", "aren't", "wasn't",
                 "weren't", "don't", "doesn't", "didn't"}

_TOKEN_RE = re.compile(r"[A-Za-z']+|[!?]+")


def _tokens(text: str):
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _shout_factor(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 6:
        return 1.0
    upper = sum(1 for c in letters if c.isupper())
    frac = upper / len(letters)
    if frac > 0.4:
        return 1.3
    if frac > 0.2:
        return 1.1
    return 1.0


def _exclaim_factor(text: str) -> float:
    n = text.count("!")
    if n == 0:
        return 1.0
    return min(1.0 + 0.15 * n, 1.6)


def tag(text: str):
    """Return (valence in [-1,1], intensity in [0,1])."""
    if not isinstance(text, str) or not text.strip():
        return (0.0, 0.0)
    toks = _tokens(text)
    if not toks:
        return (0.0, 0.0)

    valence_acc = 0.0
    weight = 0.0
    boost = 1.0
    negate = False

    for i, tok in enumerate(toks):
        if tok in _BOOST:
            boost *= _BOOST[tok]
            continue
        if tok in _NEG_NEGATORS:
            negate = True
            continue
        v = _POS.get(tok, _NEG.get(tok, 0.0))
        if v != 0.0:
            if negate:
                v = -v * 0.7
            v *= boost
            valence_acc += v
            weight += abs(v)
            boost = 1.0
            negate = False
        else:
            if i % 3 == 2:
                boost = 1.0
                negate = False

    if weight == 0.0:
        valence = 0.0
    else:
        valence = max(-1.0, min(1.0, valence_acc / max(weight, 1.0)))

    base_intensity = 1.0 - math.exp(-weight / 2.0)
    intensity = base_intensity * _shout_factor(text) * _exclaim_factor(text)
    intensity = max(0.0, min(1.0, intensity))

    return (round(valence, 4), round(intensity, 4))


def tier_for(intensity: float) -> str:
    if intensity >= TIER_PEAK_FLOOR:
        return "peak_affect"
    if intensity >= TIER_HIGH_FLOOR:
        return "high_affect"
    return "ephemeral"
