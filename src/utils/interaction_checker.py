"""Comprehensive drug interaction utilities with API + local fallback.

Features:
- Integrates with NIH RxNav Interaction API (via api_client)
- Local sample database fallback
- Pairwise analysis with severity scoring and contraindication flags
- Alternative suggestions and formatted responses
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

from .api_client import get_interactions_by_names
from .response_format import (
    severity_from_text,
    severity_score,
    contraindicated,
    format_interaction_pair,
    format_description,
    normalize_name,
)


@dataclass
class InteractionRecord:
    a: str
    b: str
    description: str
    severity: str
    score: int
    contraindicated: bool
    source: str  # 'api' | 'local' | 'none'
    suggestions: List[str]


def _pairwise(drugs: List[str]) -> List[Tuple[str, str]]:
    norm = [normalize_name(d) for d in drugs if d and d.strip()]
    pairs: List[Tuple[str, str]] = []
    for i, a in enumerate(norm):
        for b in norm[i + 1 :]:
            if a == b:
                continue
            sa, sb = sorted((a, b))
            pairs.append((sa, sb))
    # dedupe
    seen = set()
    uniq: List[Tuple[str, str]] = []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


@lru_cache(maxsize=1)
def _load_local_db() -> Dict[str, Any]:
    data_path = Path(__file__).resolve().parents[2] / "data" / "sample_interactions.json"
    if data_path.exists():
        try:
            return json.loads(data_path.read_text())
        except Exception:
            pass
    # Fallback inline data
    return {
        "pairs": [
            {
                "a": "aspirin",
                "b": "ibuprofen",
                "severity": "major",
                "description": "Increased risk of bleeding",
                "suggest": ["acetaminophen"],
            }
        ],
        "alternatives": {"ibuprofen": ["acetaminophen"]},
    }


def _local_lookup(a: str, b: str) -> Tuple[str, str, List[str]]:
    db = _load_local_db()
    for entry in db.get("pairs", []):
        aa = normalize_name(entry.get("a", ""))
        bb = normalize_name(entry.get("b", ""))
        if {a, b} == {aa, bb}:
            return (
                entry.get("description", "Interaction data unavailable."),
                entry.get("severity", "minor"),
                entry.get("suggest", []),
            )
    return ("No known interaction", "minor", [])


def _suggest_for(drug: str) -> List[str]:
    db = _load_local_db()
    return db.get("alternatives", {}).get(normalize_name(drug), [])


def _to_record(a: str, b: str, desc: str, sev_hint: str | None, source: str, suggestions: List[str] | None = None) -> InteractionRecord:
    sev = sev_hint or severity_from_text(desc)
    return InteractionRecord(
        a=a,
        b=b,
        description=desc,
        severity=sev,
        score=severity_score(sev),
        contraindicated=contraindicated(desc),
        source=source,
        suggestions=suggestions or (list({*_suggest_for(a), *_suggest_for(b)})),
    )


def check_interactions_detailed(drugs: List[str]) -> List[InteractionRecord]:
    """Return rich interaction results using API with local fallback."""
    pairs = _pairwise(drugs)
    results: List[InteractionRecord] = []

    # First try API bulk; the client does 1 call for multiple rxcuis
    api_items = get_interactions_by_names([d for p in pairs for d in p])
    # Index by unordered pair for quick lookup
    api_map: Dict[frozenset[str], List[dict]] = {}
    for it in api_items:
        key = frozenset({normalize_name(it.a_name), normalize_name(it.b_name)})
        api_map.setdefault(key, []).append({"desc": it.description, "sev": it.severity})

    for a, b in pairs:
        key = frozenset({a, b})
        if key in api_map:
            # Combine multiple entries by picking highest severity
            best = None
            for ent in api_map[key]:
                rec = _to_record(a, b, ent["desc"], ent["sev"], source="api")
                if best is None or rec.score > best.score:
                    best = rec
            if best:
                results.append(best)
                continue

        # Local fallback
        desc, sev, sugg = _local_lookup(a, b)
        results.append(_to_record(a, b, desc, sev, source="local", suggestions=sugg))

    # Sort by severity descending
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def check_interactions(drugs: List[str]) -> Dict[str, str]:
    """Backward-compatible simple map for templates: "a + b" -> description.

    Uses detailed checker then formats as single-line descriptions with severity.
    """
    detailed = check_interactions_detailed(drugs)
    out: Dict[str, str] = {}
    for rec in detailed:
        pair = format_interaction_pair(rec.a, rec.b)
        out[pair] = format_description(rec.description, rec.severity)
    return out
