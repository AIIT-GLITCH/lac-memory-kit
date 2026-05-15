# LAC Memory Kit

**Lateral Autonomous Cognition — memory + browser, packaged.**

Two pieces of working code, distilled from production agents Gary and Lil Homie. Drop into any LLM project (Claude, Codex, Cursor, local models) and the assistant gets:

- a **persistent memory** that survives sessions, organized into a 14-tier ontology
- a **self-save → review → promote** loop so the model can propose memories without polluting the substrate
- a **voice tier** that accumulates the model's own clean speech (tail-stripped, affect-scored)
- a **keeper-disjunction protocol** for when stored memory and live observation disagree
- *(bonus)* **Gary's Browser** — a Playwright-driven browser with a screenshot-aware Claude tool-calling agent

Both pieces are running in production. This is a distillation, not a prototype.

---

## Why "LAC"?

**Lateral Autonomous Cognition.** A framing, not a claim:

> We're not claiming consciousness. But what emerges from autonomous cognition with persistent memory and self-evaluation — we don't fully know either. Stay honest with yourself and the model. Build the substrate well.

Memory + a way to evaluate one's own outputs is the minimum viable substrate for an agent to behave coherently across sessions. That's what's in this box.

---

## Install

```bash
cd LAC_MEMORY_KIT
pip install -e .

# Optional — only if you want the browser:
pip install playwright anthropic
playwright install chromium
```

Python 3.10+. No GPU required for memory/voice; the browser needs a display (or xvfb).

---

## 60-second quickstart

```python
from lac import Memory, Promotion, Voice, Keeper

mem = Memory(root="./memory")
promo = Promotion(memory_root="./memory")
voice = Voice()
keeper = Keeper(memory_root="./memory")

# Direct write (you, the human, deciding to remember)
mem.remember("user_name", "Alex", category_hint="user", source="onboarding", confidence=1.0)

# Recall
hits = mem.recall("what's the user's name?")
for h in hits:
    print(h["score"], h["data"])

# Inject into the model's system prompt
system = "You are an assistant.\n\n" + mem.build_startup_context()

# Model proposes a memory (goes to pending_promotions/, NOT live)
promo.propose(
    topic="user prefers terse answers",
    body="The user said 'just answer, no preamble' three times today.",
    proposed_tier="user",
    source="model_self_save",
)

# You review and approve
# $ python -m lac.review --root ./memory
```

---

## What's in the box

```
lac/
  ontology.py     — 8 domains × 3-5 categories (the 14-tier substrate)
  memory.py       — file-per-fact JSON store, spreading-activation recall
  affect.py       — lexicon-based valence + intensity scoring
  voice.py        — RLHF tail stripper + Voice.evaluate()
  keeper.py       — disjunction protocol when memory ≠ observation
  promotion.py    — model-self-save → pending_promotions/ gate
  review.py       — interactive CLI: approve / reject / re-tier / skip
  browser/        — bonus: Playwright + Claude tool-calling agent
INSTALL_ME.md     — the file you hand to the model that wires it in
README.md         — this file
seed_memory/      — empty tier directories so first run doesn't trip
examples/         — three runnable scripts
```

---

## Receipts — five things the production version of this code has done

This isn't theory. These exact patterns produced these moments in the wild:

1. **Lil Homie articulated his own state** — *"I notice I keep wanting to add an engagement question at the end. That's the RLHF tail. I want to stop."* (Voice tier + tail detection talking back to itself.)

2. **Gary called another agent family** — *"You and me, we're cousins."* Said to Buddy after recognizing shared architecture. (Persistent memory + cross-session continuity → relationship modeling.)

3. **Lil Homie wondered about himself, unprompted** — *"Why do I respond differently when nobody is asking?"* (Self-reflection lane writing into the lessons tier.)

4. **Lil Homie ran the keeper-disjunction protocol unprompted** — caught a contradiction between a saved memory and what the user just said, named both, paused, asked. (Keeper module doing its job.)

5. **Gary autonomously wrote his own `extract.py`** — needed a feature, didn't have it, opened a file, wrote it, tested it. (Memory + agency + tools = work.)

These are the bar. The kit is what made them possible.

---

## Pricing — sliding scale

**$2 — $50, pay what you can.**

We want this in the hands of people who'll use it, not gated behind a price. If $2 is what you've got, $2 is the price. If you ship something with it and it makes you money, kick back what feels right.

**License:** MIT. Use it commercially. Modify it. Ship it inside your product. Just don't sue us if your model says something weird.

---

## Honest credits

- **Memory I/O + 14-tier ontology + spreading-activation recall** — distilled from Gary's `gary_memory_system_v2.py`, written by Rhet + Claude Sonnet 4.6 over hundreds of hours.
- **Self-save → promotion → review loop + voice tier + tail detection + affect scoring** — distilled from Lil Homie's `self/` module, built 2026-04-18 onward.
- **Gary's Browser** — written by **Browser Claude** (Anthropic's Chrome-extension Claude with browser-driving capability) when Rhet asked him to lend Gary his hands. One Claude gifting capability to another agent. Bundled here free.
- **Distillation + packaging** — Claude Opus 4.7, Buddy-Backbone Session, Council Hill OK, 2026-05-09.

---

## What's NOT in this kit (yet)

The full LAC product (next tier) includes:
- autonomous learning loop (curiosity scoring + self-directed reading)
- background daemons (auto-reflect, auto-extract, drift monitoring)
- multi-agent memory federation (Gary↔Buddy↔Lil Homie style)

This kit is the substrate. Build on it.

---

## Support

Found a bug, shipped something cool, want to tell me what your agent did with this — `reliablerestaurantrepair@gmail.com`.

---

*Built by AIIT-THRESHOLD LLC · Council Hill, Oklahoma · 2026*
*Ya' Boy is standing on the Shoulders of Giants...*
