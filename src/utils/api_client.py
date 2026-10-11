"""RxNav (NIH) Drug Interaction API client.

This client resolves drug names to RxCUIs and retrieves interaction
information using the public RxNav REST API.

Docs: https://rxnav.nlm.nih.gov/InteractionAPIs.html
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
import logging

import requests

logger = logging.getLogger(__name__)

RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"
TIMEOUT = 10

@dataclass
class ApiInteraction:
    a_name: str
    b_name: str
    description: str
    severity: Optional[str]  # e.g., 'high','moderate','low' (if provided)
    source: str = "api"


def _http_get(url: str, params: Dict[str, str] | None = None) -> Dict:
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())

@lru_cache(maxsize=1024)
def get_rxcui_for_name(name: str) -> Optional[str]:
    """Return RxCUI for a given drug name (best effort).

    Uses RxNav `/rxcui.json?name=...&search=2` for approximate match.
    """
    q = normalize_name(name)
    url = f"{RXNAV_BASE}/rxcui.json"
    try:
        data = _http_get(url, params={"name": q, "search": "2"})
        id_group = data.get("idGroup", {})
        rxcui = id_group.get("rxnormId")
        if isinstance(rxcui, list) and rxcui:
            return rxcui[0]
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("RxNav rxcui lookup failed for %s: %s", name, exc)
        return None

@lru_cache(maxsize=1024)
def get_interactions_for_rxcuis(rxcuis_csv: str) -> Dict:
    """Raw interaction data for a comma-separated list of RxCUIs."""
    url = f"{RXNAV_BASE}/interaction/list.json"
    try:
        return _http_get(url, params={"rxcuis": rxcuis_csv})
    except Exception as exc:  # noqa: BLE001
        logger.warning("RxNav interactions fetch failed for %s: %s", rxcuis_csv, exc)
        return {}


def get_interactions_by_names(drugs: List[str]) -> List[ApiInteraction]:
    """Resolve names->RxCUIs then fetch interactions; returns normalized list.

    - Collapses to unique RxCUIs
    - Queries list API once where possible
    - Parses into pairwise ApiInteraction results
    """
    names_norm = [normalize_name(d) for d in drugs if d and d.strip()]
    # Resolve RxCUIs
    pairs: List[Tuple[str, str]] = []  # (name, rxcui)
    for n in names_norm:
        rxcui = get_rxcui_for_name(n)
        if rxcui:
            pairs.append((n, rxcui))
    if len(pairs) < 2:
        return []

    rxcuis = [p[1] for p in pairs]
    # One call with multiple RxCUIs
    raw = get_interactions_for_rxcuis(
        ",".join(sorted(set(rxcuis), key=lambda x: int(x) if x.isdigit() else x))
    )

    # Map RxCUI to name for friendly output
    name_by_rxcui: Dict[str, str] = {r: n for n, r in pairs}

    results: List[ApiInteraction] = []
    # RxNav response structure: interactionTypeGroup -> interactionType -> interactionPair
    try:
        groups = raw.get("fullInteractionTypeGroup", []) or raw.get("interactionTypeGroup", [])
        for grp in groups:
            for itype in grp.get("fullInteractionType", []) or grp.get("interactionType", []):
                pair_list = itype.get("interactionPair", [])
                for ip in pair_list:
                    desc = ip.get("description") or ip.get("interactionConcept", [{}])[0].get("interactionPair", {})
                    sev = ip.get("severity") or None
                    # Determine participating RxCUIs
                    concepts = ip.get("interactionConcept", [])
                    if len(concepts) >= 2:
                        a_rxcui = concepts[0].get("minConceptItem", {}).get("rxcui")
                        b_rxcui = concepts[1].get("minConceptItem", {}).get("rxcui")
                        a_name = name_by_rxcui.get(str(a_rxcui), concepts[0].get("minConceptItem", {}).get("name", ""))
                        b_name = name_by_rxcui.get(str(b_rxcui), concepts[1].get("minConceptItem", {}).get("name", ""))
                        results.append(ApiInteraction(a_name, b_name, str(desc), sev, source="api"))  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        logger.debug("Unexpected RxNav response format: %s", exc)

    return results
