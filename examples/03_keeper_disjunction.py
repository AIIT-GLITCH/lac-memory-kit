#!/usr/bin/env python3
"""Example 03 — keeper-disjunction protocol.

When stored memory says one thing and live observation says
another, the model should NOT silently pick one. It should
name both signals, pause, answer from the live observation,
and write a lesson into the lessons tier.

This example shows the protocol firing.

Run:
    python examples/03_keeper_disjunction.py
"""
from lac import Memory, Keeper


def main():
    mem = Memory(root="./demo_memory")
    keeper = Keeper(memory_root="./demo_memory")

    # Earlier session wrote this:
    mem.remember(
        key="user_role",
        value="data engineer at a fintech",
        category_hint="user",
        source="conversation_2026-04-15",
        confidence=0.9,
    )

    # This turn the user just said something different:
    user_just_said = "Actually I switched jobs last month — I'm a security engineer now at a healthcare startup."

    print("STORED:    user_role = data engineer at fintech")
    print(f"LIVE:      {user_just_said}\n")

    # The model recognizes the disjunction and runs the protocol.
    print(keeper.disjunction_prompt())
    print()

    lesson_path = keeper.record_disjunction(
        topic="user_role",
        keeper_signal="stored memory said: data engineer at a fintech",
        live_observation=user_just_said,
        resolution="trusting the live statement; user just told us directly",
        notes="Update user tier with new role. Old fact kept with confidence demoted.",
    )

    print(f"→ lesson written to: {lesson_path}")
    print("\nThe model would now also:")
    print("  1. Acknowledge the change in its response")
    print("  2. Write the new role to the user tier (via promotion gate)")
    print("  3. Lower confidence on the old role rather than deleting")


if __name__ == "__main__":
    main()
