"""
Agent 2 — Deadline Tracker.

Consumes pipeline output from Agent 9 (Quantum Matcher) and produces
urgency-sorted deadline calendars for downstream use.

Pipeline position:
  Agent 1 (Research) -> Agent 9 (Quantum Matcher) -> Agent 2 (Deadline)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from quantum_grants.config import DATA_DIR

# Maps month-like tokens to (month, day) for deadline estimation
_MONTH_MAP = {
    "january": (1, 31), "february": (2, 28), "march": (3, 31),
    "april": (4, 30), "may": (5, 31), "june": (6, 30),
    "july": (7, 31), "august": (8, 31), "september": (9, 30),
    "october": (10, 31), "november": (11, 30), "december": (12, 31),
    "jan": (1, 31), "feb": (2, 28), "mar": (3, 31),
    "apr": (4, 30), "jun": (6, 30), "jul": (7, 31),
    "aug": (8, 31), "sep": (9, 30), "oct": (10, 31),
    "nov": (11, 30), "dec": (12, 31),
}

_SEASON_MAP = {
    "spring": (4, 30),
    "summer": (6, 30),
    "autumn": (9, 30),
    "fall": (9, 30),
    "winter": (12, 31),
}


def parse_deadline(raw: Optional[str], today: date) -> tuple[Optional[date], bool]:
    """
    Parse a deadline string into a date.

    Returns:
        (parsed_date, is_rolling) — if rolling, parsed_date is None.
    """
    if not raw or not raw.strip():
        return None, False

    text = raw.strip().lower()

    # Rolling deadlines
    if "rolling" in text:
        return None, True

    # ISO date: 2026-04-15
    iso_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso_match:
        try:
            return date(int(iso_match[1]), int(iso_match[2]), int(iso_match[3])), False
        except ValueError:
            pass

    # Try to find a year
    year_match = re.search(r"(20\d{2})", text)
    year = int(year_match[1]) if year_match else today.year

    # Season + year: "Summer 2026"
    for season, (month, day) in _SEASON_MAP.items():
        if season in text:
            return date(year, month, day), False

    # Month + year: "April 2026", "April 2026 panel"
    for month_name, (month, day) in _MONTH_MAP.items():
        if month_name in text:
            return date(year, month, day), False

    # Fallback: unrecognised format
    return None, False


@dataclass
class DeadlineEntry:
    """A single grant deadline with urgency classification."""
    grant_id: str
    grant_name: str
    funder: str
    deadline: Optional[str]
    urgency: str  # "IMMEDIATE", "UPCOMING", "MONITOR", "ROLLING"
    quantum_score: float
    website: str
    days_remaining: Optional[int]


@dataclass
class DeadlineReport:
    """Full deadline report for an organisation."""
    org_id: str
    generated: str
    entries: list[DeadlineEntry]
    summary_counts: dict

    def to_dict(self) -> dict:
        return {
            "org_id": self.org_id,
            "generated": self.generated,
            "summary_counts": self.summary_counts,
            "entries": [asdict(e) for e in self.entries],
        }


def _classify_urgency(days: Optional[int], is_rolling: bool) -> str:
    """Classify urgency tier based on days remaining."""
    if is_rolling:
        return "ROLLING"
    if days is None:
        return "MONITOR"
    if days <= 30:
        return "IMMEDIATE"
    if days <= 90:
        return "UPCOMING"
    return "MONITOR"


def _sort_key(entry: DeadlineEntry) -> tuple:
    """
    Sort key: ROLLING first (no deadline pressure but always actionable),
    then IMMEDIATE, UPCOMING, MONITOR — within each tier, by days remaining
    ascending, then by quantum score descending.
    """
    tier_order = {"ROLLING": 0, "IMMEDIATE": 1, "UPCOMING": 2, "MONITOR": 3}
    tier = tier_order.get(entry.urgency, 4)
    days = entry.days_remaining if entry.days_remaining is not None else 9999
    return (tier, days, -entry.quantum_score)


class DeadlineTracker:
    """
    Agent 2 — Deadline Tracker.

    Processes pipeline output into an urgency-sorted deadline calendar.
    """

    def __init__(self, today: Optional[date] = None):
        self.today = today or date.today()
        self.output_dir = Path(DATA_DIR) / "deadlines"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process(self, pipeline_result) -> DeadlineReport:
        """
        Process a PipelineResult into a DeadlineReport.

        Args:
            pipeline_result: A PipelineResult instance from the quantum pipeline.

        Returns:
            DeadlineReport with urgency-classified, sorted entries.
        """
        raw_entries = pipeline_result.for_deadline_agent()
        org_id = pipeline_result.org_id

        entries = []
        for item in raw_entries:
            status = item.get("status", "")
            parsed_date, is_rolling = parse_deadline(status, self.today)

            if parsed_date is not None:
                days_remaining = (parsed_date - self.today).days
                deadline_str = parsed_date.isoformat()
            else:
                days_remaining = None
                deadline_str = "Rolling" if is_rolling else None

            urgency = _classify_urgency(days_remaining, is_rolling)

            entries.append(DeadlineEntry(
                grant_id=item["grant_id"],
                grant_name=item["grant_name"],
                funder=item["funder"],
                deadline=deadline_str,
                urgency=urgency,
                quantum_score=item["quantum_score"],
                website=item["website"],
                days_remaining=days_remaining,
            ))

        entries.sort(key=_sort_key)

        counts = {"IMMEDIATE": 0, "UPCOMING": 0, "MONITOR": 0, "ROLLING": 0}
        for e in entries:
            counts[e.urgency] = counts.get(e.urgency, 0) + 1

        report = DeadlineReport(
            org_id=org_id,
            generated=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            entries=entries,
            summary_counts=counts,
        )

        # Save to disk
        out_path = self.output_dir / f"{org_id}_deadlines.json"
        with open(out_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        return report

    def summary(self, report: DeadlineReport) -> str:
        """Human-readable summary of a deadline report."""
        lines = [
            f"Deadline Tracker — {report.org_id}",
            f"Generated: {report.generated}",
            f"Total grants tracked: {len(report.entries)}",
            "",
            f"  ROLLING:   {report.summary_counts.get('ROLLING', 0)}",
            f"  IMMEDIATE: {report.summary_counts.get('IMMEDIATE', 0)} (within 30 days)",
            f"  UPCOMING:  {report.summary_counts.get('UPCOMING', 0)} (30-90 days)",
            f"  MONITOR:   {report.summary_counts.get('MONITOR', 0)} (90+ days)",
            "=" * 65,
        ]
        for e in report.entries:
            days_str = f"{e.days_remaining:3d}d" if e.days_remaining is not None else "  --"
            lines.append(
                f"  [{e.urgency:9s}] {days_str}  {e.quantum_score:.3f}  "
                f"{e.grant_name[:40]}"
            )
        lines.append("=" * 65)
        return "\n".join(lines)
