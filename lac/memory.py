"""memory.py — file-backed photon-brain memory.

Hierarchical: domain -> category -> fact.json
Each fact is its own JSON file. The whole system is just files on disk —
inspectable with `cat`, editable with `vim`, no DB to corrupt.

Recall uses spreading activation over a synonym web: a query activates
categories via synonyms, then scores every fact by word overlap +
substring match + category bonus + confidence weight + recency boost.
The most resonant memories surface first.

The architecture is from Gary (Rhet Wike, Council Hill OK). This is a
distilled, configurable port for general use.
"""
from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .ontology import ONTOLOGY, LINK_TYPES, synonym_map


class Memory:
    """File-backed photon-brain memory.

    Args:
        root: directory to store memory files. Created if missing.
        max_facts_per_category: cap when building startup context.
        debug_expiry_days: how long debug/* facts live before auto-pruning.
    """

    def __init__(
        self,
        root: str = "./memory",
        max_facts_per_category: int = 25,
        debug_expiry_days: int = 7,
    ):
        self.root = os.path.abspath(os.path.expanduser(root))
        self.max_facts_per_category = max_facts_per_category
        self.debug_expiry_days = debug_expiry_days
        self.links_file = os.path.join(self.root, "_links.json")
        self.episodes_file = os.path.join(self.root, "conversations", "episodes.json")
        self.raw_turns_file = os.path.join(self.root, "raw", "recent_turns.txt")

        self._synonym_map = synonym_map()
        self._memory_lock = threading.Lock()
        self._links_lock = threading.Lock()
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_loaded = False

        self._ensure_dirs()

    # -- filesystem layout ---------------------------------------------------

    def _ensure_dirs(self) -> None:
        for domain_key, domain in ONTOLOGY.items():
            for cat_key in domain["categories"]:
                os.makedirs(os.path.join(self.root, domain_key, cat_key), exist_ok=True)
        os.makedirs(os.path.join(self.root, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "conversations"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "pending_promotions"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "rejected_promotions"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "voice"), exist_ok=True)
        os.makedirs(os.path.join(self.root, "lessons"), exist_ok=True)

    def _fact_path(self, domain: str, category: str, key: str) -> str:
        safe_key = re.sub(r"[^\w\-]", "_", key.lower().strip())[:80]
        return os.path.join(self.root, domain, category, f"{safe_key}.json")

    # -- category resolution -------------------------------------------------

    def _resolve_category(self, text: str) -> Tuple[str, str]:
        """Resolve any synonym or keyword to (domain, category)."""
        text_lower = text.lower().strip()
        if text_lower in self._synonym_map:
            return self._synonym_map[text_lower]

        text_words = set(text_lower.split())
        best_score = 0
        best_match = ("timeline", "daily_events")  # default

        for syn, (domain, cat) in self._synonym_map.items():
            syn_words = set(syn.split())
            overlap = len(text_words & syn_words)
            if overlap > best_score:
                best_score = overlap
                best_match = (domain, cat)

        for syn, (domain, cat) in self._synonym_map.items():
            if len(syn) > 3 and syn in text_lower:
                return (domain, cat)

        return best_match

    # -- cache ---------------------------------------------------------------

    def _load_category_facts(self, domain: str, category: str) -> List[Dict[str, Any]]:
        folder = os.path.join(self.root, domain, category)
        if not os.path.isdir(folder):
            return []
        facts = []
        for fname in os.listdir(folder):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                    fact = json.load(f)
                    fact["_domain"] = domain
                    fact["_category"] = category
                    facts.append(fact)
            except Exception:
                continue
        return facts

    def _ensure_cache(self) -> None:
        if self._cache_loaded:
            return
        for domain_key, domain in ONTOLOGY.items():
            for cat_key in domain["categories"]:
                cache_key = f"{domain_key}/{cat_key}"
                self._cache[cache_key] = self._load_category_facts(domain_key, cat_key)
        self._cache_loaded = True

    # -- write ---------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        return re.sub(r"\s+", " ", text)

    @staticmethod
    def _is_junk(key: str, value: str) -> bool:
        if not value or not key:
            return True
        val = value.strip()
        if len(val) < 3:
            return True
        junk = {"yes", "no", "ok", "okay", "sure", "thanks", "thank you",
                "i don't know", "not sure", "maybe", "hello", "hey", "hi",
                "goodbye", "bye", "good", "bad", "cool", "nice", "wow"}
        return val.lower() in junk

    def _is_duplicate(self, domain: str, category: str, key: str, value: str) -> bool:
        path = self._fact_path(domain, category, key)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            existing_val = str(existing.get("value", ""))
            if existing_val == value:
                return True
            if self._normalize(existing_val) == self._normalize(value):
                return True
            if self._normalize(value) in self._normalize(existing_val):
                return True
        except Exception:
            pass
        return False

    def _save_fact(self, fact: Dict[str, Any]) -> None:
        domain = fact.get("_domain", "timeline")
        category = fact.get("_category", "daily_events")
        key = fact["key"]
        path = self._fact_path(domain, category, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        disk_fact = {k: v for k, v in fact.items() if not k.startswith("_")}
        disk_fact["domain"] = domain
        disk_fact["category"] = category

        with open(path, "w", encoding="utf-8") as f:
            json.dump(disk_fact, f, indent=2, ensure_ascii=False)

        cache_key = f"{domain}/{category}"
        if self._cache_loaded and cache_key in self._cache:
            cached = self._cache[cache_key]
            for i, existing in enumerate(cached):
                if existing.get("key") == key:
                    cached[i] = fact
                    return
            cached.append(fact)

    def remember(
        self,
        key: str,
        value: Any,
        category_hint: Optional[str] = None,
        source: str = "unknown",
        confidence: float = 0.5,
    ) -> bool:
        """Store a fact. Returns True if stored, False if junk/duplicate.

        category_hint can be any synonym, an old category name, or a keyword.
        The synonym web routes it to the right (domain, category).
        Omit it to let the system infer from key + value.
        """
        value_str = str(value).strip()
        key = key.strip()
        hint = category_hint or ""

        domain, category = self._resolve_category(f"{hint} {key} {value_str}")

        if self._is_junk(key, value_str):
            return False

        with self._memory_lock:
            if self._is_duplicate(domain, category, key, value_str):
                return False
            now = datetime.utcnow().isoformat()
            fact = {
                "key": key,
                "value": value_str,
                "domain": domain,
                "category": category,
                "created": now,
                "updated": now,
                "source": source,
                "confidence": confidence,
                "_domain": domain,
                "_category": category,
            }
            self._save_fact(fact)
            return True

    # -- recall --------------------------------------------------------------

    def recall(self, query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """Photon brain recall — query activates the semantic web.
        Returns the most resonant memories, ranked by activation level.
        """
        self._ensure_cache()
        query_lower = query.lower()
        query_words = set(query_lower.split())
        query_norm = self._normalize(query)

        activated_categories = set()
        for word in query_words:
            if word in self._synonym_map:
                domain, cat = self._synonym_map[word]
                activated_categories.add(f"{domain}/{cat}")

        scored = []
        for cache_key, facts in self._cache.items():
            for fact in facts:
                score = 0.0
                fact_key = fact.get("key", "").lower()
                fact_val = self._normalize(str(fact.get("value", "")))
                fact_words = set(fact_key.split("_")) | set(fact_val.split())

                overlap = len(query_words & fact_words)
                score += overlap * 2.0

                if query_norm in fact_val or query_norm in fact_key:
                    score += 5.0

                if cache_key in activated_categories:
                    score += 3.0

                score *= fact.get("confidence", 0.5)

                try:
                    updated = datetime.fromisoformat(fact.get("updated", "2020-01-01"))
                    days_old = (datetime.utcnow() - updated).days
                    if days_old < 7:
                        score *= 1.5
                    elif days_old < 30:
                        score *= 1.2
                except Exception:
                    pass

                if score > 0:
                    scored.append((score, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [fact for _, fact in scored[:max_results]]

    def recall_by_tier(self, domain: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all facts under a domain (or domain/category)."""
        self._ensure_cache()
        results = []
        for cache_key, facts in self._cache.items():
            d, c = cache_key.split("/", 1)
            if d != domain:
                continue
            if category and c != category:
                continue
            results.extend(facts)
        return results

    def recall_recent(self, days: int = 7, max_results: int = 50) -> List[Dict[str, Any]]:
        """Return facts updated within the last N days."""
        self._ensure_cache()
        cutoff = datetime.utcnow() - timedelta(days=days)
        out = []
        for facts in self._cache.values():
            for fact in facts:
                try:
                    updated = datetime.fromisoformat(fact.get("updated", "2020-01-01"))
                    if updated >= cutoff:
                        out.append(fact)
                except Exception:
                    continue
        out.sort(key=lambda f: f.get("updated", ""), reverse=True)
        return out[:max_results]

    # -- semantic links ------------------------------------------------------

    def _load_links(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.links_file):
            return []
        try:
            with open(self.links_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_links(self, links: List[Dict[str, Any]]) -> None:
        with open(self.links_file, "w", encoding="utf-8") as f:
            json.dump(links, f, indent=2, ensure_ascii=False)

    def add_link(self, from_key: str, to_key: str, link_type: str = "related_to") -> None:
        if link_type not in LINK_TYPES:
            link_type = "related_to"
        with self._links_lock:
            links = self._load_links()
            for link in links:
                if (link["from"] == from_key and link["to"] == to_key
                        and link["type"] == link_type):
                    return
            links.append({
                "from": from_key,
                "to": to_key,
                "type": link_type,
                "created": datetime.utcnow().isoformat()
            })
            self._save_links(links)

    def get_linked_facts(self, key: str) -> List[Dict[str, Any]]:
        links = self._load_links()
        linked_keys = set()
        for link in links:
            if link["from"] == key:
                linked_keys.add(link["to"])
            if link["to"] == key:
                linked_keys.add(link["from"])
        results = []
        self._ensure_cache()
        for facts in self._cache.values():
            for fact in facts:
                if fact.get("key") in linked_keys:
                    results.append(fact)
        return results

    # -- startup context -----------------------------------------------------

    def build_startup_context(self) -> str:
        """Build a structured text block summarizing memory.
        Inject this into your model's system prompt at session start.
        """
        self._ensure_cache()
        parts = ["=== LAC MEMORY ===\n"]
        for domain_key, domain in ONTOLOGY.items():
            domain_facts = []
            for cat_key in domain["categories"]:
                cache_key = f"{domain_key}/{cat_key}"
                facts = self._cache.get(cache_key, [])
                if not facts:
                    continue
                must_load = [f for f in facts if f.get("confidence", 0) >= 0.9]
                rest = sorted(
                    [f for f in facts if f.get("confidence", 0) < 0.9],
                    key=lambda f: f.get("updated", ""), reverse=True
                )
                remaining = max(0, self.max_facts_per_category - len(must_load))
                top = must_load + rest[:remaining]
                if top:
                    lines = [f"\n  [{cat_key.upper().replace('_', ' ')}]"]
                    for fact in top:
                        lines.append(f"    {fact.get('key', '?')}: {fact.get('value', '?')}")
                    domain_facts.append("\n".join(lines))
            if domain_facts:
                parts.append(f"\n[{domain['description'].upper()}]")
                parts.extend(domain_facts)

        if os.path.exists(self.episodes_file):
            try:
                with open(self.episodes_file, "r", encoding="utf-8") as f:
                    episodes = json.load(f)
                if episodes:
                    parts.append("\n\n[SESSION MEMORIES]")
                    for ep in episodes[-5:]:
                        ts = ep.get("date_human", ep.get("timestamp", "?"))
                        parts.append(f"\n  [{ts}]")
                        parts.append(f"    {ep.get('summary', '?')}")
            except Exception:
                pass

        if os.path.exists(self.raw_turns_file):
            try:
                with open(self.raw_turns_file, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
                if raw:
                    parts.append("\n\n[RECENT CONVERSATIONS]")
                    parts.append(raw[-2000:])
            except Exception:
                pass

        parts.append("\n\n=== END LAC MEMORY ===")
        result = "\n".join(parts)
        if len(result) < 50:
            return "No prior memory found. First session."
        return result

    # -- raw turn log --------------------------------------------------------

    def append_raw_turn(self, user_text: str, model_text: str, max_turns: int = 20) -> None:
        try:
            turns = []
            if os.path.exists(self.raw_turns_file):
                with open(self.raw_turns_file, "r", encoding="utf-8") as f:
                    raw = f.read()
                turns = [t.strip() for t in raw.split("---") if t.strip()]
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            turns.append(f"[{ts}]\nUser: {user_text}\nModel: {model_text}")
            turns = turns[-max_turns:]
            os.makedirs(os.path.dirname(self.raw_turns_file), exist_ok=True)
            with open(self.raw_turns_file, "w", encoding="utf-8") as f:
                f.write("\n---\n".join(turns))
        except Exception:
            pass

    # -- maintenance ---------------------------------------------------------

    def cleanup_stale_debug(self) -> int:
        debug_folder = os.path.join(self.root, "debug", "errors")
        if not os.path.isdir(debug_folder):
            return 0
        cutoff = (datetime.utcnow() - timedelta(days=self.debug_expiry_days)).isoformat()
        removed = 0
        for fname in os.listdir(debug_folder):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(debug_folder, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    fact = json.load(f)
                if fact.get("updated", fact.get("created", "")) < cutoff:
                    os.remove(path)
                    removed += 1
            except Exception:
                continue
        return removed

    def print_tree(self) -> None:
        self._ensure_cache()
        print("\n=== LAC MEMORY TREE ===\n")
        total = 0
        for domain_key, domain in ONTOLOGY.items():
            domain_total = 0
            for cat_key in domain["categories"]:
                cache_key = f"{domain_key}/{cat_key}"
                domain_total += len(self._cache.get(cache_key, []))
            print(f"  {domain_key}/ — {domain['description']} ({domain_total} facts)")
            for cat_key, cat_info in domain["categories"].items():
                cache_key = f"{domain_key}/{cat_key}"
                count = len(self._cache.get(cache_key, []))
                syn_count = len(cat_info["synonyms"])
                print(f"    {cat_key}/ — {cat_info['description']} ({count} facts, {syn_count} synonyms)")
            total += domain_total
        print(f"\n  TOTAL: {total} facts across {len(ONTOLOGY)} domains")
        print("=== END TREE ===\n")
