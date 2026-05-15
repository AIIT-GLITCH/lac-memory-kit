#!/usr/bin/env python3
"""review.py — interactive review loop for pending promotions.

Run as:
    python -m lac.review --root ./memory

Walks every file in memory/pending_promotions/ and lets you:
    a — approve into proposed_tier (or override with t)
    r — reject (moves to rejected_promotions/)
    s — skip (leave for tomorrow)
    t — pick a different tier
    q — quit

Locked tiers (identity, keeper) cannot be approved here. The keeper
populates those by hand.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .promotion import Promotion, ALLOWED_TIERS
from .keeper import LOCKED_TIERS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Review pending memory promotions")
    ap.add_argument("--root", default="./memory",
                    help="Memory root (same as Memory(root=...))")
    args = ap.parse_args(argv)

    promo = Promotion(memory_root=args.root)
    items = promo.list_pending()
    if not items:
        print("no pending promotions.")
        return 0

    print(f"{len(items)} pending. q to quit, s to skip, a/r/t for action.\n")
    for path in items:
        try:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [skip — bad json] {Path(path).name}: {e}")
            continue
        print("─" * 72)
        print(f"file:    {Path(path).name}")
        print(f"topic:   {doc.get('topic')}")
        print(f"valence: {doc.get('valence')}  "
              f"intensity: {doc.get('intensity')}  "
              f"novelty: {doc.get('novelty')}")
        print(f"tier:    {doc.get('proposed_tier', 'knowledge')}")
        body = (doc.get("body") or "").strip()
        print(f"body:    {body[:500]}{'…' if len(body) > 500 else ''}")
        sys.stdout.write("\n[a]pprove  [r]eject  [s]kip  [t]ier  [q]uit > ")
        sys.stdout.flush()
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nquit.")
            return 0
        if choice in ("q", "quit"):
            return 0
        if choice in ("s", "skip", ""):
            continue
        if choice in ("r", "reject"):
            sys.stdout.write("  reason (optional) > ")
            sys.stdout.flush()
            reason = input().strip()
            promo.reject(path, reason=reason)
            print("→ rejected.\n")
            continue
        tier = doc.get("proposed_tier", "knowledge")
        if choice in ("t", "tier"):
            sys.stdout.write(f"  tier ({sorted(ALLOWED_TIERS)}): ")
            sys.stdout.flush()
            tier = input().strip()
        if tier in LOCKED_TIERS:
            print(f"  ✗ tier {tier!r} is locked. Skipping.")
            continue
        if tier not in ALLOWED_TIERS:
            print(f"  ✗ unknown tier {tier!r}. Skipping.")
            continue
        target = promo.approve(path, tier=tier)
        if target:
            print(f"→ approved → {target}\n")
        else:
            print("  ✗ approve failed.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
