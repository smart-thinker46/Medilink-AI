"""Non-LLM Phase 1 capabilities. Deterministic, explainable, and read-only: they flag, never change."""
from __future__ import annotations
import math
import re
import statistics
from difflib import SequenceMatcher


# ---- Patient duplicate detection -------------------------------------------------------------
def _name_tokens(name: str) -> list:
    return re.findall(r"[a-z]+", name.lower())


def _token_sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b)):
        return 0.8  # initial vs full name
    return SequenceMatcher(None, a, b).ratio()


def name_similarity(a: str, b: str) -> float:
    ta, tb = _name_tokens(a), _name_tokens(b)
    if not ta or not tb:
        return 0.0
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    total = sum(max(_token_sim(t, u) for u in long_) for t in short)
    return total / max(len(ta), len(tb)) if len(ta) == len(tb) else total / len(long_)


def _phone(p: str) -> str:
    return re.sub(r"\D", "", p or "")[-9:]  # 0712..., +254712..., 254712... all compare equal


def _dob_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return 0.7 if (len(a) == 4 or len(b) == 4) and a[:4] == b[:4] else 0.0


def find_duplicates(candidate: dict, existing: list, threshold: float = 0.8) -> list:
    """Similarity score (not a calibrated probability). Staff investigate before a new MRN is created."""
    out = []
    for p in existing:
        phone_ok = 1.0 if _phone(candidate.get("phone")) and _phone(candidate.get("phone")) == _phone(p.get("phone")) else 0.0
        score = (0.5 * name_similarity(candidate["name"], p["name"])
                 + 0.3 * _dob_score(candidate.get("dob", ""), p.get("dob", ""))
                 + 0.2 * phone_ok)
        if score >= threshold:
            out.append({"mrn": p["mrn"], "similarity": round(score, 2),
                        "action": "Review before creating a new MRN"})
    return sorted(out, key=lambda x: -x["similarity"])


# ---- Queue forecast --------------------------------------------------------------------------
def queue_forecast(queue_length: int, servers: int, avg_service_min: float, target_min: float) -> dict:
    """Simple deterministic estimate. Replace with a model trained on hospital history when available."""
    wait = math.ceil(queue_length / max(servers, 1)) * avg_service_min
    over = max(0.0, wait - target_min)
    return {"queue_length": queue_length, "servers": servers, "predicted_wait_min": round(wait),
            "target_min": target_min, "exceeds_target": over > 0, "minutes_over_target": round(over),
            "method": "queue_length / servers * avg_service_time"}


# ---- Revenue leakage -------------------------------------------------------------------------
def revenue_leakage(services: list, charges: list) -> dict:
    charged = [c["service_id"] for c in charges]
    missing = [s["id"] for s in services if s["id"] not in charged]
    dupes = sorted({sid for sid in charged if charged.count(sid) > 1})
    return {"services_completed": len(services), "charges_generated": len(charges),
            "possible_missed_charges": missing, "possible_duplicate_charges": dupes,
            "note": "Flags for billing staff to investigate. Nothing is created or modified."}


def discount_outliers(rows: list, tolerance: float = 0.35) -> list:
    """rows: [{department, baseline_pct, current_pct}]. Flags current > baseline * (1 + tolerance)."""
    return [dict(r, ratio=round(r["current_pct"] / r["baseline_pct"], 2)) for r in rows
            if r["baseline_pct"] > 0 and r["current_pct"] > r["baseline_pct"] * (1 + tolerance)]


# ---- Patient feedback themes -----------------------------------------------------------------
THEMES = {
    "Waiting time": ["wait", "waited", "queue", "long", "hours", "slow", "foleni", "subiri"],
    "Pharmacy": ["pharmacy", "drug", "medicine", "dawa"],
    "Staff behaviour": ["rude", "polite", "kind", "helpful", "attitude", "nurse", "muuguzi"],
    "Clinical care": ["doctor", "treatment", "diagnosis", "care", "daktari"],
    "Billing": ["bill", "payment", "charge", "expensive", "malipo", "cost"],
}  # starter lexicon; have Kiswahili/Sheng terms reviewed by native-speaking staff


def feedback_themes(comments: list) -> dict:
    counts = {t: 0 for t in THEMES}
    counts["Other"] = 0
    for c in comments:
        words = set(re.findall(r"\w+", c.lower()))
        hit = [t for t, kws in THEMES.items() if words & set(kws)]
        for t in hit or ["Other"]:
            counts[t] += 1
    total = sum(counts.values()) or 1
    return {t: {"count": n, "pct": round(100 * n / total)} for t, n in counts.items()}
