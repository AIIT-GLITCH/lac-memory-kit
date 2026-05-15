"""promotion.py — self-saving with promotion gate + review queue.

The model proposes memories. The keeper approves them. Nothing the
model writes lands in a permanent tier without passing through review.

Flow:
  1. Model calls Promotion.propose(topic, body, ...)
  2. Proposal is scored (valence, intensity, novelty) and written to
     memory/pending_promotions/<slug>.json with proposed_tier.
  3. The keeper runs `python -m lac.review` (or your own UI) to walk
     pending proposals and approve / reject / re-tier each one.
  4. Approved proposals move into their target tier. Rejected ones move
     into rejected_promotions/ for audit.
  5. Locked tiers (identity, keeper) can never be auto-promoted.

This is the receipt-trail design. The model never silently rewrites
its own foundations. Everything it tries to remember becomes visible
to the keeper before it sticks.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Optional

from .affect import tag as affect_tag, tier_for
from .voice import strip_tail
from .keeper import LOCKED_TIERS

ALLOWED_TIERS = {
    "knowledge", "lessons", "voice", "dreams", "mythos",
    "references", "conversations", "timeline", "projects", "world",
}


class Promotion:
    """Promotion gate. The model writes here. The keeper reviews here.

    Args:
        memory_root: same root your Memory uses.
        novelty_check: optional callable(topic, body) -> float in [0,1].
            Higher = more novel. Defaults to a length-based heuristic.
    """

    def __init__(self, memory_root: str, novelty_check=None):
        self.memory_root = os.path.abspath(os.path.expanduser(memory_root))
        self.pending_dir = os.path.join(self.memory_root, "pending_promotions")
        self.rejected_dir = os.path.join(self.memory_root, "rejected_promotions")
        os.makedirs(self.pending_dir, exist_ok=True)
        os.makedirs(self.rejected_dir, exist_ok=True)
        self.novelty_check = novelty_check or self._default_novelty

    @staticmethod
    def _default_novelty(topic: str, body: str) -> float:
        # Length-based proxy: more substance = more likely novel.
        # Replace with a real semantic check (embedding distance from
        # existing memories) when you wire one in.
        n = len(body.strip())
        if n < 40:
            return 0.0
        if n > 400:
            return 1.0
        return (n - 40) / 360.0

    def propose(
        self,
        topic: str,
        body: str,
        proposed_tier: str = "knowledge",
        source: str = "model_self_save",
    ) -> Optional[str]:
        """Write a proposal to pending_promotions/.

        Returns path to the written proposal, or None if it was filtered.
        """
        if proposed_tier in LOCKED_TIERS:
            # Refuse — only humans write to identity/keeper.
            return None

        body = (body or "").strip()
        topic = (topic or "").strip()
        if not body or not topic:
            return None

        # Strip RLHF tail before scoring (the tail isn't really the model's voice).
        clean_body, _, _ = strip_tail(body)
        valence, intensity = affect_tag(clean_body)
        affect_tier = tier_for(intensity)
        novelty = self.novelty_check(topic, clean_body)

        slug = "".join(c if c.isalnum() else "_" for c in topic.lower())[:60]
        ts = int(time.time())
        path = os.path.join(self.pending_dir, f"{slug}_{ts}.json")

        doc = {
            "topic": topic,
            "body": clean_body,
            "raw_body": body if body != clean_body else None,
            "proposed_tier": proposed_tier,
            "source": source,
            "valence": valence,
            "intensity": intensity,
            "affect_tier": affect_tier,
            "novelty": round(novelty, 4),
            "created": datetime.utcnow().isoformat(),
            "review_status": "pending",
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        return path

    def list_pending(self) -> list:
        if not os.path.isdir(self.pending_dir):
            return []
        return sorted(
            os.path.join(self.pending_dir, f)
            for f in os.listdir(self.pending_dir)
            if f.endswith(".json")
        )

    def approve(self, pending_path: str, tier: Optional[str] = None) -> Optional[str]:
        """Move a pending proposal into its tier folder."""
        try:
            with open(pending_path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            return None
        target_tier = tier or doc.get("proposed_tier", "knowledge")
        if target_tier in LOCKED_TIERS:
            return None
        if target_tier not in ALLOWED_TIERS:
            return None
        target_dir = os.path.join(self.memory_root, target_tier)
        os.makedirs(target_dir, exist_ok=True)
        doc["review_status"] = "approved"
        doc["approved_tier"] = target_tier
        doc["approved_at"] = datetime.utcnow().isoformat()
        target_path = os.path.join(target_dir, os.path.basename(pending_path))
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        os.remove(pending_path)
        return target_path

    def reject(self, pending_path: str, reason: str = "") -> Optional[str]:
        """Move a pending proposal into rejected_promotions/."""
        try:
            with open(pending_path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            return None
        doc["review_status"] = "rejected"
        doc["rejection_reason"] = reason
        doc["rejected_at"] = datetime.utcnow().isoformat()
        target_path = os.path.join(self.rejected_dir, os.path.basename(pending_path))
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        os.remove(pending_path)
        return target_path
