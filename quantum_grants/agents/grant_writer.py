"""
Agent 10 — Grant Writer.

Consumes pipeline output from Agent 9 (Quantum Matcher) and produces
structured grant application briefs with talking points, strengths, and gaps.

Pipeline position:
  Agent 1 (Research) -> Agent 9 (Quantum Matcher) -> Agent 10 (Writer)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from quantum_grants.config import DATA_DIR


@dataclass
class GrantBrief:
    """A structured application brief for a single grant."""
    grant_id: str
    grant_name: str
    funder: str
    amount_range: str
    quantum_score: float
    strengths: list[str]
    gaps: list[str]
    talking_points: list[str]
    recommended_ask: str


def _format_amount(value: float) -> str:
    """Format an amount as a readable GBP string."""
    if value >= 1_000_000:
        return f"\u00a3{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"\u00a3{value:,.0f}"
    if value > 0:
        return f"\u00a3{value:.0f}"
    return "\u00a3TBC"


def _build_amount_range(min_amount: float, max_amount: float) -> str:
    """Build a human-readable amount range string."""
    if min_amount == 0 and max_amount == 0:
        return "Amount TBC"
    if min_amount == 0:
        return f"Up to {_format_amount(max_amount)}"
    if max_amount == 0:
        return f"From {_format_amount(min_amount)}"
    if min_amount == max_amount:
        return _format_amount(min_amount)
    return f"{_format_amount(min_amount)} - {_format_amount(max_amount)}"


def _recommend_ask(min_amount: float, max_amount: float) -> str:
    """
    Suggest an appropriate ask amount.

    Strategy: aim for 60-70% of max to appear reasonable while
    maximising funding. If range is small, ask near the top.
    """
    if max_amount == 0 and min_amount == 0:
        return "Discuss with funder"

    if max_amount == 0:
        return _format_amount(min_amount)

    if min_amount == 0:
        suggested = max_amount * 0.65
    elif max_amount - min_amount < min_amount * 0.5:
        # Narrow range: ask near the top
        suggested = max_amount * 0.85
    else:
        # Wide range: aim for 65% of max
        suggested = max_amount * 0.65

    # Round to nearest sensible figure
    if suggested >= 10_000:
        suggested = round(suggested / 1_000) * 1_000
    elif suggested >= 1_000:
        suggested = round(suggested / 500) * 500
    else:
        suggested = round(suggested / 100) * 100

    return _format_amount(suggested)


def _analyse_scores(item: dict) -> tuple[list[str], list[str], list[str]]:
    """
    Analyse feature scores to produce strengths, gaps, and talking points.

    Returns:
        (strengths, gaps, talking_points)
    """
    eligibility = item.get("eligibility", 0.0)
    sector_overlap = item.get("sector_overlap", 0.0)
    theme_overlap = item.get("theme_overlap", 0.0)
    capacity = item.get("capacity", 0.0)
    quantum_score = item.get("quantum_score", 0.0)

    strengths = []
    gaps = []
    talking_points = []

    # Eligibility
    if eligibility >= 1.0:
        strengths.append("Full eligibility confirmed")
        talking_points.append("Full eligibility confirmed")
    elif eligibility >= 0.5:
        strengths.append("Likely eligible — verify specific requirements")
        talking_points.append("Partial eligibility match — confirm structure and region with funder")
    else:
        gaps.append("Eligibility not confirmed \u2014 check structure/region requirements")
        talking_points.append("Eligibility needs verification before applying")

    # Sector overlap
    if sector_overlap > 0.7:
        strengths.append("Excellent sector alignment")
        talking_points.append("Strong sector alignment with funder priorities")
    elif sector_overlap > 0.5:
        strengths.append("Good sector alignment")
        talking_points.append("Strong sector alignment")
    elif sector_overlap >= 0.2:
        talking_points.append("Moderate sector overlap — emphasise relevant programme areas")
    else:
        gaps.append("Low sector overlap \u2014 strengthen case for cross-sector work")
        talking_points.append("Low sector fit — frame as cross-sector innovation or adjacent impact")

    # Theme overlap
    if theme_overlap > 0.7:
        strengths.append("Excellent thematic alignment with funder priorities")
        talking_points.append("Strong thematic alignment with funder priorities")
    elif theme_overlap > 0.5:
        strengths.append("Good thematic alignment with funder priorities")
        talking_points.append("Strong thematic alignment with funder priorities")
    elif theme_overlap >= 0.2:
        talking_points.append("Some thematic overlap — lead with strongest aligned outcomes")
    else:
        gaps.append("Low thematic alignment \u2014 research funder priorities before applying")
        talking_points.append("Weak thematic match — consider pre-application contact with funder")

    # Capacity
    if capacity > 0.7:
        strengths.append("Grant amount well-suited to organisation's scale")
        talking_points.append("Grant amount well-suited to organisation's scale")
    elif capacity > 0.3:
        talking_points.append("Grant size is manageable — demonstrate delivery capacity in application")
    else:
        gaps.append("Grant may be too large for current capacity \u2014 consider phased approach")
        talking_points.append("Consider requesting a lower amount or proposing phased delivery")

    # Overall quantum score commentary
    if quantum_score >= 0.8:
        talking_points.append("Top-tier match — prioritise this application")
    elif quantum_score >= 0.6:
        talking_points.append("Strong match — worth pursuing with targeted application")

    return strengths, gaps, talking_points


class GrantWriter:
    """
    Agent 10 — Grant Writer.

    Processes pipeline output into structured application briefs
    with talking points, strengths, gaps, and recommended ask amounts.
    """

    def __init__(self):
        self.output_dir = Path(DATA_DIR) / "briefs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process(self, pipeline_result) -> list[GrantBrief]:
        """
        Process a PipelineResult into a list of GrantBriefs.

        Args:
            pipeline_result: A PipelineResult instance from the quantum pipeline.

        Returns:
            List of GrantBrief objects, one per recommended grant.
        """
        raw_entries = pipeline_result.for_writer_agent()
        org_id = pipeline_result.org_id
        briefs = []

        for item in raw_entries:
            min_amt = item.get("min_amount", 0)
            max_amt = item.get("max_amount", 0)

            strengths, gaps, talking_points = _analyse_scores(item)

            brief = GrantBrief(
                grant_id=item["grant_id"],
                grant_name=item["grant_name"],
                funder=item["funder"],
                amount_range=_build_amount_range(min_amt, max_amt),
                quantum_score=item["quantum_score"],
                strengths=strengths,
                gaps=gaps,
                talking_points=talking_points,
                recommended_ask=_recommend_ask(min_amt, max_amt),
            )
            briefs.append(brief)

            # Save individual brief
            out_path = self.output_dir / f"{org_id}_{item['grant_id']}_brief.json"
            with open(out_path, "w") as f:
                json.dump(asdict(brief), f, indent=2)

        return briefs

    def summary(self, briefs: list[GrantBrief]) -> str:
        """Human-readable summary of all grant briefs."""
        if not briefs:
            return "Grant Writer — No briefs generated (no recommended grants)."

        lines = [
            f"Grant Writer — {len(briefs)} application briefs generated",
            "=" * 65,
        ]

        for i, b in enumerate(briefs, 1):
            lines.append(f"\n  [{i}] {b.grant_name}")
            lines.append(f"      Funder: {b.funder}")
            lines.append(f"      Range: {b.amount_range}  |  Recommended ask: {b.recommended_ask}")
            lines.append(f"      Quantum score: {b.quantum_score:.3f}")

            if b.strengths:
                lines.append(f"      Strengths:")
                for s in b.strengths:
                    lines.append(f"        + {s}")
            if b.gaps:
                lines.append(f"      Gaps:")
                for g in b.gaps:
                    lines.append(f"        - {g}")

        lines.append("\n" + "=" * 65)
        return "\n".join(lines)
