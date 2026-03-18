"""
Classical feature encoder for grant-applicant pairs.

Transforms raw grant + applicant data into a normalised feature vector
suitable for quantum circuit encoding.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from quantum_grants.data.synthetic import SyntheticGrant, SyntheticApplicant


@dataclass
class MatchFeatures:
    """Normalised feature vector for a grant-applicant pair."""
    eligibility_binary: float
    sector_overlap: float
    theme_overlap: float
    capacity_normalised: float
    turnover_ratio: float
    experience_normalised: float

    def to_array(self) -> np.ndarray:
        return np.array([
            self.eligibility_binary,
            self.sector_overlap,
            self.theme_overlap,
            self.capacity_normalised,
            self.turnover_ratio,
            self.experience_normalised,
        ], dtype=np.float64)


def encode_pair(grant: SyntheticGrant, applicant: SyntheticApplicant) -> MatchFeatures:
    """Encode a grant-applicant pair into normalised features."""

    # Eligibility: binary pass/fail on hard criteria
    structure_ok = applicant.legal_structure in grant.eligible_structures
    region_ok = applicant.region in grant.eligible_regions

    turnover_ok = True
    if grant.annual_turnover_max and applicant.annual_turnover > grant.annual_turnover_max:
        turnover_ok = False
    if grant.annual_turnover_min and applicant.annual_turnover < grant.annual_turnover_min:
        turnover_ok = False

    eligibility = 1.0 if (structure_ok and region_ok and turnover_ok) else 0.0

    # Sector overlap
    sector_overlap = 1.0 if applicant.sector in grant.eligible_sectors else 0.0

    # Theme overlap (Jaccard-like)
    app_themes = set(applicant.themes)
    grant_themes = set(grant.priority_themes)
    if grant_themes:
        theme_overlap = len(app_themes & grant_themes) / len(app_themes | grant_themes)
    else:
        theme_overlap = 0.0

    # Capacity: composite of readiness indicators
    capacity = 0.0
    capacity += 0.25 * min(applicant.years_operating / 10, 1.0)
    capacity += 0.25 * (1.0 if applicant.has_safeguarding_policy else 0.0)
    capacity += 0.20 * (1.0 if applicant.has_financial_controls else 0.0)
    capacity += 0.15 * min(applicant.staff_count / 10, 1.0)
    capacity += 0.15 * min(applicant.previous_grants / 5, 1.0)

    # Turnover ratio
    if grant.annual_turnover_max and grant.annual_turnover_max > 0:
        turnover_ratio = min(applicant.annual_turnover / grant.annual_turnover_max, 1.0)
    else:
        turnover_ratio = 0.5

    # Experience
    experience = min(applicant.years_operating / 30, 1.0)

    return MatchFeatures(
        eligibility_binary=eligibility,
        sector_overlap=sector_overlap,
        theme_overlap=round(theme_overlap, 4),
        capacity_normalised=round(capacity, 4),
        turnover_ratio=round(turnover_ratio, 4),
        experience_normalised=round(experience, 4),
    )


def encode_batch(
    grants: list[SyntheticGrant],
    applicants: list[SyntheticApplicant],
) -> np.ndarray:
    """Encode all grant-applicant pairs into a feature matrix."""
    features = []
    for grant in grants:
        for applicant in applicants:
            pair_features = encode_pair(grant, applicant)
            features.append(pair_features.to_array())
    return np.array(features)
