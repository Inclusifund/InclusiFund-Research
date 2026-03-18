"""
Synthetic data generators for quantum grant matching R&D.

Generates fake but structurally realistic grant opportunities and
applicant profiles for circuit training. NO real client data.
"""

import random
from dataclasses import dataclass, field
from typing import Optional


SECTORS = [
    "youth_services", "mental_health", "housing", "education",
    "community_development", "arts_culture", "environment",
    "disability", "elderly_care", "criminal_justice",
]

LEGAL_STRUCTURES = ["cic", "charity", "cio", "social_enterprise", "community_group"]

FUNDER_TYPES = ["lottery", "trust", "government", "corporate", "community_foundation"]

GRANT_SIZES = ["micro", "small", "medium", "large"]

REGIONS = [
    "north_east", "north_west", "yorkshire", "east_midlands",
    "west_midlands", "east", "london", "south_east", "south_west",
    "wales", "scotland", "northern_ireland",
]


@dataclass
class SyntheticGrant:
    """A fake grant opportunity for training."""
    grant_id: str
    funder_name: str
    programme_name: str
    funder_type: str
    max_award: int
    min_award: int
    eligible_sectors: list[str]
    eligible_structures: list[str]
    eligible_regions: list[str]
    requires_match_funding: bool
    match_percentage: float
    annual_turnover_max: Optional[int]
    annual_turnover_min: Optional[int]
    priority_themes: list[str]
    deadline_days: int  # days from now


@dataclass
class SyntheticApplicant:
    """A fake applicant profile for training."""
    org_id: str
    org_name: str
    legal_structure: str
    sector: str
    region: str
    annual_turnover: int
    years_operating: int
    staff_count: int
    beneficiary_count: int
    has_safeguarding_policy: bool
    has_financial_controls: bool
    themes: list[str]
    previous_grants: int


@dataclass
class SyntheticMatchLabel:
    """Ground truth label for a grant-applicant pair."""
    grant_id: str
    org_id: str
    eligibility_score: float   # 0-1: hard eligibility criteria
    alignment_score: float     # 0-1: mission/theme alignment
    capacity_score: float      # 0-1: organisational readiness
    overall_match: float       # 0-1: composite score
    is_match: bool             # binary: would this succeed?


def generate_grant(idx: int) -> SyntheticGrant:
    """Generate a single synthetic grant opportunity."""
    funder_type = random.choice(FUNDER_TYPES)
    size = random.choice(GRANT_SIZES)

    award_ranges = {
        "micro": (500, 5_000),
        "small": (5_000, 25_000),
        "medium": (25_000, 150_000),
        "large": (150_000, 1_000_000),
    }
    min_a, max_a = award_ranges[size]

    n_sectors = random.randint(1, 5)
    n_regions = random.randint(1, 12)

    return SyntheticGrant(
        grant_id=f"G-{idx:04d}",
        funder_name=f"Synthetic Funder {idx}",
        programme_name=f"Programme {chr(65 + idx % 26)}",
        funder_type=funder_type,
        max_award=max_a,
        min_award=min_a,
        eligible_sectors=random.sample(SECTORS, n_sectors),
        eligible_structures=random.sample(LEGAL_STRUCTURES, random.randint(1, 4)),
        eligible_regions=random.sample(REGIONS, n_regions),
        requires_match_funding=random.random() < 0.3,
        match_percentage=random.choice([0, 0.1, 0.25, 0.5]) if random.random() < 0.3 else 0,
        annual_turnover_max=random.choice([50_000, 250_000, 1_000_000, None]),
        annual_turnover_min=random.choice([0, 5_000, 10_000, None]),
        priority_themes=random.sample(SECTORS, random.randint(1, 3)),
        deadline_days=random.randint(7, 180),
    )


def generate_applicant(idx: int) -> SyntheticApplicant:
    """Generate a single synthetic applicant."""
    return SyntheticApplicant(
        org_id=f"ORG-{idx:04d}",
        org_name=f"Synthetic Org {idx}",
        legal_structure=random.choice(LEGAL_STRUCTURES),
        sector=random.choice(SECTORS),
        region=random.choice(REGIONS),
        annual_turnover=random.randint(0, 2_000_000),
        years_operating=random.randint(0, 30),
        staff_count=random.randint(0, 50),
        beneficiary_count=random.randint(10, 5000),
        has_safeguarding_policy=random.random() > 0.15,
        has_financial_controls=random.random() > 0.1,
        themes=random.sample(SECTORS, random.randint(1, 3)),
        previous_grants=random.randint(0, 20),
    )


def compute_match_label(
    grant: SyntheticGrant, applicant: SyntheticApplicant
) -> SyntheticMatchLabel:
    """Compute a deterministic match label from grant-applicant pair."""

    # Eligibility: hard criteria
    elig = 1.0
    if applicant.legal_structure not in grant.eligible_structures:
        elig *= 0.0
    if applicant.region not in grant.eligible_regions:
        elig *= 0.0
    if grant.annual_turnover_max and applicant.annual_turnover > grant.annual_turnover_max:
        elig *= 0.0
    if grant.annual_turnover_min and applicant.annual_turnover < grant.annual_turnover_min:
        elig *= 0.0
    if not applicant.has_safeguarding_policy:
        elig *= 0.3

    # Alignment: theme/sector overlap
    sector_match = 1.0 if applicant.sector in grant.eligible_sectors else 0.2
    theme_overlap = len(set(applicant.themes) & set(grant.priority_themes))
    theme_score = min(theme_overlap / max(len(grant.priority_themes), 1), 1.0)
    alignment = 0.5 * sector_match + 0.5 * theme_score

    # Capacity: organisational readiness
    capacity = 0.0
    if applicant.years_operating >= 2:
        capacity += 0.3
    if applicant.has_financial_controls:
        capacity += 0.2
    if applicant.staff_count >= 2:
        capacity += 0.2
    if applicant.previous_grants >= 1:
        capacity += 0.15
    if applicant.beneficiary_count >= 50:
        capacity += 0.15
    capacity = min(capacity, 1.0)

    overall = 0.4 * elig + 0.35 * alignment + 0.25 * capacity
    is_match = overall >= 0.6 and elig > 0.0

    return SyntheticMatchLabel(
        grant_id=grant.grant_id,
        org_id=applicant.org_id,
        eligibility_score=round(elig, 4),
        alignment_score=round(alignment, 4),
        capacity_score=round(capacity, 4),
        overall_match=round(overall, 4),
        is_match=is_match,
    )


def generate_dataset(
    n_grants: int = 50,
    n_applicants: int = 100,
    seed: int = 42,
) -> tuple[list[SyntheticGrant], list[SyntheticApplicant], list[SyntheticMatchLabel]]:
    """Generate a complete synthetic dataset with labels."""
    random.seed(seed)

    grants = [generate_grant(i) for i in range(n_grants)]
    applicants = [generate_applicant(i) for i in range(n_applicants)]

    labels = []
    for grant in grants:
        for applicant in applicants:
            label = compute_match_label(grant, applicant)
            labels.append(label)

    positive = sum(1 for l in labels if l.is_match)
    total = len(labels)
    print(f"Generated {n_grants} grants x {n_applicants} applicants = {total} pairs")
    print(f"Positive matches: {positive} ({100*positive/total:.1f}%)")

    return grants, applicants, labels


if __name__ == "__main__":
    grants, applicants, labels = generate_dataset()
