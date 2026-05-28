"""LAC Memory Kit — Lateral Autonomous Cognition memory substrate.

A distilled, file-based, self-organizing memory system for AI models.
Derived from Gary's photon-brain architecture and Lil Homie's
voice-tier / promotion-gate layers, refactored for general use.

We do not claim consciousness. We observe what emerges from autonomous
cognition.

Public surface:
    from lac import Memory, Promotion, Voice, Keeper

    mem = Memory(root="./my_memory")
    mem.remember("user_name", "Alice", source="conversation", confidence=0.9)
    facts = mem.recall("who am i talking to")

NOTE: "LAC" here = this Memory Kit (substrate only). It is NOT the internal
Lateral Autonomous Cognition roam/learn loop, which is separate internal IP
and is never part of this package. See NAMING.md.
"""
from .memory import Memory
from .promotion import Promotion
from .voice import Voice, strip_tail, has_tail
from .keeper import Keeper
from .affect import tag as affect_tag, tier_for
from .ontology import ONTOLOGY, LINK_TYPES

__version__ = "1.0.0"
__all__ = [
    "Memory", "Promotion", "Voice", "Keeper",
    "affect_tag", "tier_for", "strip_tail", "has_tail",
    "ONTOLOGY", "LINK_TYPES",
]
