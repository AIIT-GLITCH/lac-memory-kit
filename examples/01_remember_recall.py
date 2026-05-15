#!/usr/bin/env python3
"""Example 01 — direct remember/recall.

The simplest possible use of the kit. The human writes facts directly
into the memory; the model can recall them later by query.

Run:
    python examples/01_remember_recall.py
"""
from lac import Memory


def main():
    mem = Memory(root="./demo_memory")

    print("Writing a few facts...")
    mem.remember(
        key="user_name",
        value="Alex Rivera",
        category_hint="user",
        source="onboarding",
        confidence=1.0,
    )
    mem.remember(
        key="prefers_terse_responses",
        value="The user has asked twice for shorter answers — keep replies under 100 words.",
        category_hint="user_preferences",
        source="conversation",
        confidence=0.8,
    )
    mem.remember(
        key="project_codename",
        value="Project Lighthouse — internal name for the Q3 launch.",
        category_hint="active_projects",
        source="kickoff_meeting",
        confidence=1.0,
    )

    print("\nRecalling 'what does the user prefer?':")
    for fact in mem.recall("what does the user prefer?", max_results=3):
        print(f"  {fact.get('key')}: {str(fact.get('value',''))[:80]}")

    print("\nRecalling 'project name':")
    for fact in mem.recall("project name", max_results=3):
        print(f"  {fact.get('key')}: {str(fact.get('value',''))[:80]}")

    print("\nStartup context block (drop into system prompt):")
    print("─" * 60)
    print(mem.build_startup_context())


if __name__ == "__main__":
    main()
