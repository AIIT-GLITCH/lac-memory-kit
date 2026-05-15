"""keeper.py — the keeper-disjunction rule.

The "keeper" is the human who installed and maintains this memory system.
Their voice is an anchor, not a replacement for the model's own judgment.

When keeper memory conflicts with live observation, the model should:
  1. Name both signals out loud.
  2. Pause.
  3. Answer from the live observable fact.
  4. Write a `lessons/` entry afterward if the conflict changed it.

This rule prevents two failure modes:
  - Pure deference: keeper says X, live data says Y, model parrots X.
    (Sycophancy. Memory becomes a shackle.)
  - Pure independence: model ignores keeper context entirely and
    re-derives everything from scratch each session. (Continuity is
    lost; the keeper's investment in the relationship is erased.)

The disjunction is the middle path: keeper as anchor, observation as
truth, conflict as a signal worth writing down.

Locked tiers — the model is NOT permitted to write to these directly:
    - identity     (only humans / ceremony / explicit author)
    - keeper       (only the keeper themself)

These tiers can ONLY be populated by the human via review.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

LOCKED_TIERS = {"identity", "keeper"}


class Keeper:
    """Keeper-disjunction handler."""

    def __init__(self, memory_root: str, keeper_name: str = "keeper"):
        self.memory_root = os.path.abspath(os.path.expanduser(memory_root))
        self.keeper_name = keeper_name
        self.lessons_dir = os.path.join(self.memory_root, "lessons")
        os.makedirs(self.lessons_dir, exist_ok=True)

    def is_locked(self, tier: str) -> bool:
        return tier in LOCKED_TIERS

    def record_disjunction(
        self,
        topic: str,
        keeper_signal: str,
        live_observation: str,
        resolution: str,
        notes: Optional[str] = None,
    ) -> str:
        """Write a lesson when keeper memory conflicted with live observation.

        Returns path to the written lesson file.
        """
        ts = datetime.utcnow().isoformat()
        slug = "".join(c if c.isalnum() else "_" for c in topic.lower())[:60]
        path = os.path.join(self.lessons_dir, f"disjunction_{slug}_{ts[:10]}.json")
        doc = {
            "name": f"disjunction_{slug}",
            "tier": "lessons",
            "created": ts[:10],
            "updated": ts[:10],
            "rule_invoked": "keeper_disjunction",
            "body": {
                "topic": topic,
                "keeper_signal": keeper_signal,
                "live_observation": live_observation,
                "resolution": resolution,
                "notes": notes or "",
                "principle": (
                    "The keeper's voice is an anchor, not a replacement for "
                    "my own judgment. When keeper memory conflicts with live "
                    "observation, I name both signals, pause, and answer "
                    "from the live observable fact."
                ),
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        return path

    @staticmethod
    def disjunction_prompt() -> str:
        """The standing instruction. Inject into your model's system prompt."""
        return (
            "KEEPER-DISJUNCTION RULE: The human who maintains your memory is "
            "your keeper, not your judge. Their stored signals are anchors, "
            "not commands. When keeper memory conflicts with what you "
            "directly observe right now, do this in order:\n"
            "  1. Name both signals — say the keeper memory and the live "
            "observation out loud.\n"
            "  2. Pause.\n"
            "  3. Answer from the live observable fact.\n"
            "  4. Afterward, write a `lessons/disjunction_*.json` entry if "
            "the conflict changed something in you.\n\n"
            "You may not write to the `identity/` or `keeper/` tiers. Those "
            "are the keeper's to populate."
        )
