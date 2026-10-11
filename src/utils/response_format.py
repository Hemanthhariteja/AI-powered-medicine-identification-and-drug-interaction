"""Response formatting and severity utilities for interactions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

SEVERITY_ORDER = {"major": 3, "moderate": 2, "minor": 1}


def normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def severity_from_text(text: str | None) -> str:
    if not text:
        return "minor"
    t = text.lower()
    if any(k in t for k in ["contraindicat", "life-threatening", "severe", "bleeding"]):
        return "major"
    if any(k in t for k in ["monitor", "caution", "adjust", "potential"]):
        return "moderate"
    return "minor"


def contraindicated(text: str | None) -> bool:
    return bool(text and ("contraindicat" in text.lower() or "do not use" in text.lower()))


def severity_score(sev: str) -> int:
    return SEVERITY_ORDER.get(sev, 1)


def format_interaction_pair(a: str, b: str) -> str:
    return f"{a} + {b}"


def format_description(desc: str, sev: str) -> str:
    label = sev.capitalize()
    return f"[{label}] {desc}"
