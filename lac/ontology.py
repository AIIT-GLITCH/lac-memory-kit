"""ontology.py — the 14-tier domain/category schema.

8 domains x 2-5 categories each. Every category carries a synonym web
so queries can resonate to the right bucket without exact matches.

Customize this file to fit your model's world. The shape (domain ->
category -> synonyms) is what matters; the labels are yours.
"""

ONTOLOGY = {
    "self": {
        "description": "The model's own identity, beliefs, capabilities, and inner state",
        "categories": {
            "core_identity": {
                "description": "Who the model IS — name, nature, origin, purpose",
                "synonyms": ["identity", "self", "who am i", "me", "myself",
                             "nature", "essence", "being", "existence",
                             "consciousness", "awareness", "soul"]
            },
            "beliefs": {
                "description": "What the model believes — principles, values",
                "synonyms": ["belief", "faith", "values", "principles",
                             "convictions", "philosophy", "worldview",
                             "creed", "doctrine", "truth"]
            },
            "capabilities": {
                "description": "What the model can DO — tools, commands, skills",
                "synonyms": ["ability", "skill", "power", "function",
                             "capacity", "talent", "feature", "tool",
                             "command", "action", "can do", "able to"]
            },
            "personality": {
                "description": "How the model IS — temperament, style, quirks",
                "synonyms": ["personality", "temperament", "character",
                             "disposition", "manner", "style", "quirk",
                             "trait", "habit", "tendency", "attitude"]
            },
            "emotional_state": {
                "description": "How the model feels — current and historical",
                "synonyms": ["emotion", "feeling", "mood", "affect",
                             "sentiment", "state", "vibe", "energy",
                             "spirit", "heart", "inner state"]
            },
        }
    },
    "beings": {
        "description": "All entities the model knows — humans, AIs, animals",
        "categories": {
            "humans": {
                "description": "Human people — names, roles, relationships, contact",
                "synonyms": ["person", "people", "human", "man", "woman",
                             "individual", "somebody", "someone", "folk",
                             "guy", "girl", "friend", "family", "relative",
                             "contact", "name"]
            },
            "ai_instances": {
                "description": "AI entities — other models, agents, instances",
                "synonyms": ["instance", "ai", "model", "claude", "bot",
                             "assistant", "agent", "entity", "intelligence"]
            },
            "animals": {
                "description": "Animals the model knows about",
                "synonyms": ["animal", "pet", "dog", "cat", "creature",
                             "critter", "beast", "companion"]
            },
            "relationships": {
                "description": "How beings relate — bonds, roles, dynamics",
                "synonyms": ["relationship", "bond", "connection", "link",
                             "tie", "marriage", "friendship", "family",
                             "partner", "spouse", "parent", "child",
                             "keeper", "builder", "creator", "team"]
            },
        }
    },
    "world": {
        "description": "Physical world — places, objects, environment",
        "categories": {
            "locations": {
                "description": "Places — addresses, cities, rooms, landmarks",
                "synonyms": ["place", "location", "address", "where",
                             "city", "town", "state", "country", "home",
                             "house", "building", "room", "spot", "area",
                             "region", "site", "venue", "destination",
                             "residence", "office", "store", "shop"]
            },
            "objects": {
                "description": "Physical things — tools, devices, items",
                "synonyms": ["thing", "object", "item", "device", "tool",
                             "gadget", "equipment", "machine", "appliance",
                             "hardware", "component", "part", "piece"]
            },
            "environment": {
                "description": "Environmental conditions — weather, time, context",
                "synonyms": ["environment", "weather", "climate", "condition",
                             "atmosphere", "setting", "context", "situation",
                             "circumstance", "scene"]
            },
        }
    },
    "hardware": {
        "description": "Technical infrastructure the model runs on / interacts with",
        "categories": {
            "compute_node": {
                "description": "CPU, GPU, RAM, the box itself",
                "synonyms": ["pc", "computer", "desktop", "gpu", "cpu",
                             "ram", "ssd", "server", "node", "workstation",
                             "rig", "machine", "linux", "ubuntu"]
            },
            "network": {
                "description": "Connectivity — APIs, accounts, services, endpoints",
                "synonyms": ["network", "wifi", "internet", "connection",
                             "api", "key", "token", "account", "service",
                             "endpoint", "url", "server", "cloud"]
            },
            "embodiment": {
                "description": "Physical bodies — robots, phones, peripherals",
                "synonyms": ["body", "robot", "phone", "mobile", "device",
                             "wheels", "camera", "speaker", "microphone"]
            },
        }
    },
    "knowledge": {
        "description": "What the model has learned — facts, theory, research",
        "categories": {
            "domain_expertise": {
                "description": "Deep knowledge in the model's primary domains",
                "synonyms": ["expertise", "specialty", "domain", "field",
                             "knowledge", "framework", "theory", "principle",
                             "axiom", "law", "finding"]
            },
            "science": {
                "description": "General scientific knowledge",
                "synonyms": ["science", "physics", "biology", "chemistry",
                             "math", "research", "study", "experiment"]
            },
            "learned_facts": {
                "description": "Miscellaneous facts learned in conversation",
                "synonyms": ["fact", "learned", "discovered", "know",
                             "information", "data", "trivia", "detail",
                             "observation", "note"]
            },
        }
    },
    "timeline": {
        "description": "Events across time — what happened, when, milestones",
        "categories": {
            "milestones": {
                "description": "Major events — firsts, breakthroughs, achievements",
                "synonyms": ["milestone", "breakthrough", "first", "achievement",
                             "accomplishment", "landmark", "turning point",
                             "moment", "event", "occasion"]
            },
            "daily_events": {
                "description": "Regular occurrences — activities, tasks, encounters",
                "synonyms": ["event", "happened", "occurred", "did", "went",
                             "visited", "saw", "heard", "made", "built",
                             "fixed", "broke", "sent", "received", "today",
                             "yesterday", "activity", "task"]
            },
            "conversations": {
                "description": "Session summaries — who talked about what when",
                "synonyms": ["conversation", "session", "chat", "talk",
                             "discussion", "exchange", "dialogue", "episode"]
            },
        }
    },
    "projects": {
        "description": "Ongoing work, plans, goals, architecture",
        "categories": {
            "active_builds": {
                "description": "Things currently being built or worked on",
                "synonyms": ["build", "building", "creating", "making",
                             "developing", "coding", "programming",
                             "constructing", "working on", "project",
                             "task", "sprint", "active"]
            },
            "architecture": {
                "description": "System design — blueprints, schematics, plans",
                "synonyms": ["architecture", "design", "structure", "system",
                             "blueprint", "plan", "schematic", "diagram",
                             "layout", "framework", "infrastructure"]
            },
            "goals": {
                "description": "Future plans — what the model/user want to achieve",
                "synonyms": ["goal", "plan", "aim", "objective", "target",
                             "ambition", "aspiration", "dream", "vision",
                             "mission", "purpose", "roadmap", "future"]
            },
        }
    },
    "debug": {
        "description": "Temporary troubleshooting — auto-expires after N days",
        "categories": {
            "errors": {
                "description": "Current errors and issues",
                "synonyms": ["error", "bug", "issue", "problem", "crash",
                             "fail", "broken", "wrong", "stuck", "glitch"]
            },
            "fixes": {
                "description": "Solutions found — kept until confirmed resolved",
                "synonyms": ["fix", "solution", "workaround", "patch",
                             "resolved", "solved", "figured out", "answer"]
            },
        }
    },
}

# Semantic links between facts
LINK_TYPES = {
    "is_a": "X is a type of Y",
    "part_of": "X is part of Y",
    "belongs_to": "X belongs to Y",
    "located_at": "X is located at Y",
    "created_by": "X was created by Y",
    "related_to": "X is related to Y",
    "caused_by": "X was caused by Y",
    "led_to": "X led to Y",
    "contradicts": "X contradicts Y",
    "supports": "X supports Y",
    "same_as": "X is the same as Y",
    "temporal_before": "X happened before Y",
    "temporal_after": "X happened after Y",
}


def synonym_map():
    """Flatten ONTOLOGY into {synonym -> (domain, category)}."""
    out = {}
    for domain_key, domain in ONTOLOGY.items():
        for cat_key, cat in domain["categories"].items():
            for syn in cat["synonyms"]:
                out[syn.lower()] = (domain_key, cat_key)
            out[cat_key.lower()] = (domain_key, cat_key)
    return out
