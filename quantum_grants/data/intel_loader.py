"""
Load pre-quantum funding intelligence into structured format.

Parses the real funding research (funder longlists, eligibility data,
fit ratings) from the pre-quantum-skills-intel folder to build
domain-informed synthetic training data.

NOTE: This extracts STRUCTURAL patterns (eligibility criteria, grant
ranges, fit dimensions) but does NOT use real client identifiers
in training data sent to quantum cloud.
"""

from __future__ import annotations

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from quantum_grants.config import FUNDING_INTEL_DIR, PRE_VAULT_RESEARCH


@dataclass
class FunderProfile:
    """Extracted funder profile from intel research."""
    name: str
    grant_min: int
    grant_max: int
    cic_eligible: Optional[bool]
    startup_eligible: Optional[bool]
    fit_rating: str  # HIGH, MEDIUM, LOW, FUTURE
    focus_areas: list[str] = field(default_factory=list)
    deadline_info: str = ""
    notes: str = ""


@dataclass
class FundingLandscape:
    """Aggregate domain knowledge from intel."""
    funders: list[FunderProfile]
    eligibility_dimensions: list[str]
    grant_size_distribution: dict[str, int]  # size_band -> count
    fit_rating_distribution: dict[str, int]  # rating -> count


def parse_fit_rating(text: str) -> str:
    """Extract fit rating from text."""
    text_upper = text.upper().strip()
    for rating in ["HIGH", "MEDIUM", "LOW", "FUTURE", "DO NOT PURSUE"]:
        if rating in text_upper:
            return rating
    return "UNKNOWN"


def parse_grant_range(text: str) -> tuple[int, int]:
    """Extract min/max grant amounts from text like '£5k–£10k'."""
    amounts = re.findall(r"£([\d,.]+)\s*([kmb])?", text.lower())
    parsed = []
    for amount_str, suffix in amounts:
        amount = float(amount_str.replace(",", ""))
        if suffix == "k":
            amount *= 1_000
        elif suffix == "m":
            amount *= 1_000_000
        elif suffix == "b":
            amount *= 1_000_000_000
        parsed.append(int(amount))

    if len(parsed) >= 2:
        return min(parsed), max(parsed)
    elif len(parsed) == 1:
        return 0, parsed[0]
    return 0, 0


def parse_bool_eligibility(text: str) -> Optional[bool]:
    """Parse 'Yes', 'No', 'Likely', etc. into bool or None."""
    text_lower = text.lower().strip()
    if text_lower.startswith("yes") or text_lower.startswith("likely"):
        return True
    if text_lower.startswith("no") or text_lower.startswith("unlikely"):
        return False
    return None


def load_funder_longlist(filepath: Path) -> list[FunderProfile]:
    """Parse a funder longlist markdown table into FunderProfile objects."""
    funders = []

    with open(filepath) as f:
        content = f.read()

    table_pattern = re.compile(
        r"\|\s*(\d+)\s*\|"          # index
        r"\s*([^|]+)\|"             # funder name
        r"\s*([^|]+)\|"             # grant range
        r"\s*([^|]+)\|"             # CIC eligible
        r"\s*([^|]+)\|"             # startup eligible
        r"\s*([^|]+)\|"             # deadline
        r"\s*([^|]+)\|"             # fit rating
    )

    for match in table_pattern.finditer(content):
        _, name, grant_range, cic_elig, startup_elig, deadline, fit = match.groups()

        grant_min, grant_max = parse_grant_range(grant_range)

        funders.append(FunderProfile(
            name=name.strip(),
            grant_min=grant_min,
            grant_max=grant_max,
            cic_eligible=parse_bool_eligibility(cic_elig),
            startup_eligible=parse_bool_eligibility(startup_elig),
            fit_rating=parse_fit_rating(fit),
            deadline_info=deadline.strip(),
        ))

    return funders


def load_all_intel() -> FundingLandscape:
    """Load all available funding intelligence."""
    all_funders: list[FunderProfile] = []

    longlist_files = list(FUNDING_INTEL_DIR.glob("*longlist*.md"))
    for filepath in longlist_files:
        funders = load_funder_longlist(filepath)
        all_funders.extend(funders)

    grant_sizes: dict[str, int] = {"micro": 0, "small": 0, "medium": 0, "large": 0}
    for f in all_funders:
        if f.grant_max <= 5_000:
            grant_sizes["micro"] += 1
        elif f.grant_max <= 25_000:
            grant_sizes["small"] += 1
        elif f.grant_max <= 150_000:
            grant_sizes["medium"] += 1
        else:
            grant_sizes["large"] += 1

    fit_dist: dict[str, int] = {}
    for f in all_funders:
        fit_dist[f.fit_rating] = fit_dist.get(f.fit_rating, 0) + 1

    eligibility_dimensions = [
        "legal_structure",       # CIC/charity/CIO
        "startup_stage",         # pre-revenue, early, established
        "geographic_region",     # London borough, region
        "annual_turnover",       # income thresholds
        "track_record",          # years operating, previous grants
        "beneficiary_group",     # age, demographic
        "sector_focus",          # housing, youth, arts, etc.
        "safeguarding_policy",   # policy requirements
        "governance_standards",  # board composition
        "match_funding",         # co-funding requirements
    ]

    return FundingLandscape(
        funders=all_funders,
        eligibility_dimensions=eligibility_dimensions,
        grant_size_distribution=grant_sizes,
        fit_rating_distribution=fit_dist,
    )


def intel_summary() -> str:
    """Print a summary of loaded intelligence."""
    landscape = load_all_intel()
    lines = [
        f"Funders loaded: {len(landscape.funders)}",
        f"Eligibility dimensions: {len(landscape.eligibility_dimensions)}",
        f"Grant size distribution: {landscape.grant_size_distribution}",
        f"Fit rating distribution: {landscape.fit_rating_distribution}",
        "",
        "Top HIGH-fit funders:",
    ]
    for f in landscape.funders:
        if f.fit_rating == "HIGH":
            lines.append(f"  - {f.name}: £{f.grant_min:,}–£{f.grant_max:,}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(intel_summary())
