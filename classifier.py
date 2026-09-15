"""
classifier.py - Lightweight "AI classification" engine for the City
Complaint Tracker.

This module inspects a complaint's issue type and free-text description
and derives:
    - severity        (Low / Medium / High / Critical)
    - department       (which city department should own it)
    - sla_hours        (response-time window tied to severity)
    - priority score/label (severity + duplicate pressure + backlog age)

It is implemented as a deterministic keyword/rule engine so the MVP runs
fully offline with zero external dependencies and no API key required -
important since the app must start locally with `python app.py`.

The engine is intentionally isolated behind `classify_complaint()` so it
can later be swapped for a real hosted LLM call (e.g. the Anthropic API)
without touching any other part of the app: keep the same return shape
{"severity": ..., "department": ..., "sla_hours": ...} and app.py will
keep working unmodified.
"""
from config import Config

# Keywords are checked from most to least severe; first match wins.
_SEVERITY_KEYWORDS = {
    "Critical": [
        "gas leak", "gas smell", "fire", "explosion", "live wire",
        "exposed wire", "downed wire", "electrocut", "collapse",
        "sinkhole", "flooding", "flood", "sewage overflow", "raw sewage",
        "child injured", "injury", "injured", "accident", "hit and run",
        "trapped",
    ],
    "High": [
        "no power", "power outage", "outage", "blocking road",
        "blocking traffic", "leaking", "leak", "hazard", "hazardous",
        "dangerous", "danger", "overflowing", "large pothole", "deep hole",
        "broken glass", "sparking", "smoke",
    ],
    "Medium": [
        "broken", "damaged", "cracked", "not working", "malfunction",
        "flickering", "smell", "odor", "noise", "graffiti", "pothole",
    ],
}


def _detect_severity(issue_type, description):
    text = (description or "").lower()
    for level in ("Critical", "High", "Medium"):
        if any(keyword in text for keyword in _SEVERITY_KEYWORDS[level]):
            return level
    return "Low"


def _detect_department(issue_type):
    return Config.DEPARTMENT_MAP.get(issue_type, "General Services")


def classify_complaint(issue_type, description):
    """
    Return the AI-assisted classification for a new complaint.

    Returns:
        {
            "severity": "Low" | "Medium" | "High" | "Critical",
            "department": str,
            "sla_hours": int,
        }
    """
    severity = _detect_severity(issue_type, description)
    department = _detect_department(issue_type)
    sla_hours = Config.SLA_HOURS[severity]
    return {
        "severity": severity,
        "department": department,
        "sla_hours": sla_hours,
    }


def compute_priority(severity, duplicate_count=0, age_hours=0):
    """
    Combine severity, duplicate-report pressure, and backlog age into a
    single 0-100 priority score plus a human-readable label.

    - Severity contributes a base weight (10-90).
    - Each duplicate report of the same underlying issue adds pressure
      (capped) since multiple residents reporting the same problem is a
      signal it needs attention sooner.
    - Complaints that have been sitting untouched for a while gain a
      small aging bonus so nothing is silently forgotten.
    """
    base = Config.SEVERITY_WEIGHT.get(severity, 10)
    duplicate_bonus = min(duplicate_count * 5, 20)
    aging_bonus = min(int(age_hours // 24) * 2, 10)

    score = min(base + duplicate_bonus + aging_bonus, 100)

    label = "Low"
    for threshold, name in Config.PRIORITY_THRESHOLDS:
        if score >= threshold:
            label = name
            break

    return score, label
