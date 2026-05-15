#!/usr/bin/env python3
"""Example 02 — model self-save through the promotion gate.

The model proposes things to remember. Proposals land in
pending_promotions/ until a human reviews them. This is the
key safety pattern — the model never writes directly to live
memory tiers.

Run:
    python examples/02_self_save_with_promotion.py
    python -m lac.review --root ./demo_memory   # then review them
"""
from lac import Promotion, Voice


def main():
    promo = Promotion(memory_root="./demo_memory")
    voice = Voice()

    # The model just generated this turn. Tail-strip + score before proposing.
    raw_model_output = (
        "I noticed you mentioned your daughter's name is Mira three times "
        "today. I want to remember that so I don't forget next session. "
        "Is there anything else about Mira you'd like me to keep in mind?"
    )

    evaluation = voice.evaluate(raw_model_output)
    print(f"raw text:        {evaluation['raw'][:80]}...")
    print(f"clean text:      {evaluation['clean'][:80]}...")
    print(f"tail detected:   {evaluation['tail_kind']}")
    print(f"valence:         {evaluation['valence']:+.2f}")
    print(f"intensity:       {evaluation['intensity']:.2f}")
    print(f"affect tier:     {evaluation['tier']}")

    # The model proposes a memory based on what it noticed.
    pending_path = promo.propose(
        topic="user's daughter is named Mira",
        body="Mentioned three times in conversation on 2026-05-09. "
             "Worth remembering as a personal detail.",
        proposed_tier="user",
        source="model_self_save",
    )

    if pending_path:
        print(f"\n→ proposal queued at: {pending_path}")
        print("\nNow run:  python -m lac.review --root ./demo_memory")
        print("...to approve, reject, re-tier, or skip.")
    else:
        print("\n→ proposal rejected (locked tier or duplicate).")


if __name__ == "__main__":
    main()
