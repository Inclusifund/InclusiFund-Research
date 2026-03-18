"""
Multi-dimensional scoring for grant-organisation matching.

Instead of a single composite match score, this module computes 5 sub-scores
that give a richer picture of grant fit:

  1. Technical Fit (0-100): capabilities vs opportunity requirements
  2. Social Value Alignment (0-100): mission alignment, community impact
  3. Evidence Strength (0-100): track record, maturity, delivery capability
  4. Win Probability (0-100): application difficulty, funder preferences
  5. Competition Intensity (0-100, inverted: lower = more competitive)

The composite score is a weighted combination:
    0.25 * technical + 0.20 * social_value + 0.20 * evidence
    + 0.25 * win_prob + 0.10 * (100 - competition)

This is the CLASSICAL production path. A quantum enhancement option exists
but the classical scoring is what runs by default.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from typing import Optional

from quantum_grants.agents.quantum_matcher import CICProfile


# ---------------------------------------------------------------------------
# Score dataclass
# ---------------------------------------------------------------------------

@dataclass
class MultiDimensionalScore:
    """Five-dimensional score for a grant-organisation pair."""
    technical_fit: float        # 0-100
    social_value_alignment: float  # 0-100
    evidence_strength: float    # 0-100
    win_probability: float      # 0-100
    competition_intensity: float  # 0-100 (inverted: lower = more competitive)
    composite: float = 0.0      # weighted combination, set by compute_composite

    # Weights for composite calculation
    WEIGHTS: dict = field(default_factory=lambda: {
        "technical_fit": 0.25,
        "social_value_alignment": 0.20,
        "evidence_strength": 0.20,
        "win_probability": 0.25,
        "competition_intensity": 0.10,
    })

    def __post_init__(self):
        if self.composite == 0.0:
            self.composite = self.compute_composite()

    def compute_composite(self, weights: Optional[dict] = None) -> float:
        """
        Compute weighted composite score.

        Competition intensity is inverted: (100 - competition) represents
        how favourable the competitive landscape is.
        """
        w = weights or self.WEIGHTS
        score = (
            w["technical_fit"] * self.technical_fit
            + w["social_value_alignment"] * self.social_value_alignment
            + w["evidence_strength"] * self.evidence_strength
            + w["win_probability"] * self.win_probability
            + w["competition_intensity"] * (100 - self.competition_intensity)
        )
        return round(min(100.0, max(0.0, score)), 2)

    def to_dict(self) -> dict:
        return {
            "technical_fit": round(self.technical_fit, 2),
            "social_value_alignment": round(self.social_value_alignment, 2),
            "evidence_strength": round(self.evidence_strength, 2),
            "win_probability": round(self.win_probability, 2),
            "competition_intensity": round(self.competition_intensity, 2),
            "composite": round(self.composite, 2),
        }

    def summary(self) -> str:
        """Human-readable summary of all dimensions."""
        lines = [
            f"  Technical Fit:         {self.technical_fit:5.1f}/100",
            f"  Social Value:          {self.social_value_alignment:5.1f}/100",
            f"  Evidence Strength:     {self.evidence_strength:5.1f}/100",
            f"  Win Probability:       {self.win_probability:5.1f}/100",
            f"  Competition Intensity: {self.competition_intensity:5.1f}/100 (lower = harder)",
            f"  ---",
            f"  Composite:             {self.composite:5.1f}/100",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sector keyword matching (shared with quantum_matcher but extended)
# ---------------------------------------------------------------------------

_SECTOR_KEYWORDS = {
    "youth": ["youth", "young people", "children", "under-26", "child"],
    "health": ["health", "wellbeing", "wellness", "mental health", "therapy", "disability"],
    "community": ["community", "social", "neighbourhood", "local", "civic"],
    "arts": ["arts", "culture", "creative", "music", "theatre", "performing"],
    "education": ["education", "training", "learning", "skills", "literacy"],
    "environment": ["environment", "climate", "nature", "green", "sustainability", "biodiversity"],
    "housing": ["housing", "homelessness", "shelter", "accommodation"],
    "employment": ["employment", "employability", "jobs", "enterprise", "business"],
    "sport": ["sport", "physical activity", "fitness", "recreation"],
    "equality": ["equality", "diversity", "inclusion", "disadvantage", "poverty"],
}

# Social value keywords that indicate mission-aligned opportunities
_SOCIAL_VALUE_KEYWORDS = [
    "social impact", "social value", "community benefit", "community impact",
    "lived experience", "disadvantage", "inequality", "deprivation",
    "underserved", "marginalised", "vulnerable", "excluded",
    "diversity", "inclusion", "equity", "justice",
    "wellbeing", "mental health", "prevention",
    "grassroots", "community-led", "co-production", "co-design",
    "social enterprise", "social innovation",
    "ethnic minority", "black-led", "minority-led",
    "empowerment", "participation", "engagement",
]


def _text_keyword_score(text: str, keywords: list[str]) -> float:
    """Score how many keywords appear in text, normalised to [0, 1]."""
    if not text or not keywords:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return min(hits / max(len(keywords), 1), 1.0)


def _sector_group_overlap(grant_sectors: list[str], cic_sectors: list[str]) -> float:
    """Jaccard-style overlap of sector groups using keyword matching."""
    if not grant_sectors and not cic_sectors:
        return 0.0

    grant_text = " ".join(s.lower() for s in grant_sectors)
    cic_text = " ".join(s.lower() for s in cic_sectors)

    grant_groups = set()
    cic_groups = set()
    for group, keywords in _SECTOR_KEYWORDS.items():
        if any(kw in grant_text for kw in keywords):
            grant_groups.add(group)
        if any(kw in cic_text for kw in keywords):
            cic_groups.add(group)

    if not grant_groups and not cic_groups:
        gs = {s.lower().strip() for s in grant_sectors}
        cs = {s.lower().strip() for s in cic_sectors}
        intersection = len(gs & cs)
        union = len(gs | cs)
        return intersection / union if union > 0 else 0.0

    union = len(grant_groups | cic_groups)
    intersection = len(grant_groups & cic_groups)
    return intersection / union if union > 0 else 0.0


def _region_match(grant_regions: list[str], cic_region: str) -> bool:
    """Check if CIC region is covered by grant regions."""
    for gr in grant_regions:
        if gr in ("UK-wide", "UK", "Nationwide"):
            return True
        if gr.lower() == cic_region.lower():
            return True
    return False


# ---------------------------------------------------------------------------
# Individual dimension scorers
# ---------------------------------------------------------------------------

def score_technical_fit(grant: dict, cic: CICProfile) -> float:
    """
    Technical Fit (0-100): How well the org's capabilities match
    the opportunity requirements.

    Components:
    - Sector overlap (40%): do the sectors align?
    - Region eligibility (20%): is the org in the right geography?
    - Stage fit (25%): does the grant support the org's maturity stage?
    - Difficulty match (15%): does the org have capacity for this grant?
    """
    # Sector overlap
    sector_overlap = _sector_group_overlap(
        grant.get("sectors", []), cic.sectors
    )

    # Region eligibility (binary but softened)
    region_ok = _region_match(grant.get("regions", []), cic.region)
    region_score = 1.0 if region_ok else 0.1

    # Stage fit
    stage_fit = 0.0
    if cic.years_operating < 1:
        stage_fit = 1.0 if grant.get("supportsStartup") else 0.1
    elif cic.years_operating < 3:
        if grant.get("supportsStartup") or grant.get("supportsGrowth"):
            stage_fit = 0.9
        else:
            stage_fit = 0.3
    else:
        if grant.get("supportsGrowth") or grant.get("supportsScale"):
            stage_fit = 0.9
        elif grant.get("supportsStartup"):
            stage_fit = 0.5
        else:
            stage_fit = 0.2

    # Difficulty match: org capacity vs grant difficulty
    difficulty = grant.get("applicationDifficulty", 3)
    capacity = 0.0
    capacity += 0.25 * min(cic.years_operating / 10, 1.0)
    capacity += 0.25 * (1.0 if cic.has_safeguarding_policy else 0.0)
    capacity += 0.20 * (1.0 if cic.has_financial_controls else 0.0)
    capacity += 0.15 * min(cic.staff_count / 10, 1.0)
    capacity += 0.15 * min(cic.previous_grants / 5, 1.0)
    difficulty_norm = difficulty / 5.0
    difficulty_fit = 1.0 - abs(capacity - difficulty_norm)
    difficulty_fit = max(0.0, min(1.0, difficulty_fit))

    score = (
        0.40 * sector_overlap
        + 0.20 * region_score
        + 0.25 * stage_fit
        + 0.15 * difficulty_fit
    )
    return round(score * 100, 2)


def score_social_value_alignment(grant: dict, cic: CICProfile) -> float:
    """
    Social Value Alignment (0-100): Mission alignment and community
    impact potential.

    Components:
    - Theme overlap (35%): keyword matching on themes + beneficiaries
    - Social value keywords in grant (30%): does the grant prioritise impact?
    - Beneficiary alignment (20%): do the target groups match?
    - Lived experience / diversity signals (15%): diversity-led indicators
    """
    # Theme overlap: deep keyword matching
    search_text = " ".join([
        grant.get("description", ""),
        grant.get("name", ""),
        " ".join(grant.get("sectors", [])),
    ]).lower()

    match_terms = list(set(
        t.lower() for t in cic.themes + cic.sectors + cic.beneficiaries
    ))
    if match_terms:
        hits = sum(1 for t in match_terms if t in search_text)
        theme_overlap = min(hits / max(len(match_terms), 1), 1.0)
    else:
        theme_overlap = 0.0

    # Social value keywords present in the grant
    social_value_score = _text_keyword_score(search_text, _SOCIAL_VALUE_KEYWORDS)

    # Beneficiary alignment: check if grant description mentions org's beneficiaries
    beneficiary_score = 0.0
    if cic.beneficiaries:
        beneficiary_hits = sum(
            1 for b in cic.beneficiaries if b.lower() in search_text
        )
        beneficiary_score = min(beneficiary_hits / len(cic.beneficiaries), 1.0)

    # Diversity / lived experience signal
    diversity_keywords = [
        "lived experience", "diversity", "black-led", "minority-led",
        "ethnic minority", "lgbtq", "disability-led", "community-led",
    ]
    diversity_score = _text_keyword_score(search_text, diversity_keywords)

    score = (
        0.35 * theme_overlap
        + 0.30 * social_value_score
        + 0.20 * beneficiary_score
        + 0.15 * diversity_score
    )
    return round(score * 100, 2)


def score_evidence_strength(grant: dict, cic: CICProfile) -> float:
    """
    Evidence Strength (0-100): Track record, org maturity,
    and delivery capability.

    Components:
    - Years operating / maturity (30%)
    - Governance (safeguarding + financial controls) (25%)
    - Staff capacity (15%)
    - Previous grants won (20%)
    - Amount fit / financial readiness (10%)
    """
    # Maturity: years operating mapped to 0-1 (10 years = max)
    maturity = min(cic.years_operating / 10, 1.0)

    # Governance
    governance = 0.0
    governance += 0.5 * (1.0 if cic.has_safeguarding_policy else 0.0)
    governance += 0.5 * (1.0 if cic.has_financial_controls else 0.0)

    # Staff capacity (10 staff = strong, normalised)
    staff_score = min(cic.staff_count / 10, 1.0)

    # Grant track record (5 previous grants = proven)
    track_record = min(cic.previous_grants / 5, 1.0)

    # Financial readiness: does the org's turnover match the grant scale?
    max_amount = grant.get("maxAmount", 0)
    if max_amount > 0 and cic.annual_turnover > 0:
        ratio = max_amount / max(cic.annual_turnover, 1)
        if 0.05 <= ratio <= 0.5:
            financial_fit = 1.0
        elif ratio < 0.05:
            financial_fit = ratio / 0.05
        else:
            financial_fit = max(0.2, 1.0 - (ratio - 0.5) / 5)
    elif cic.annual_turnover == 0 and max_amount > 0:
        # Pre-revenue: small grants still viable
        financial_fit = 0.5 if max_amount <= 10_000 else 0.2
    else:
        financial_fit = 0.3

    score = (
        0.30 * maturity
        + 0.25 * governance
        + 0.15 * staff_score
        + 0.20 * track_record
        + 0.10 * financial_fit
    )
    return round(score * 100, 2)


def score_win_probability(grant: dict, cic: CICProfile) -> float:
    """
    Win Probability (0-100): Likelihood of a successful application.

    Components:
    - Application difficulty vs capacity (30%): can the org handle it?
    - Funder preference alignment (25%): startup-friendly, etc.
    - Amount appropriateness (20%): asking for the right amount?
    - Eligibility hard-pass (25%): region + structure + stage
    """
    # Application difficulty vs org capacity
    difficulty = grant.get("applicationDifficulty", 3)
    capacity = 0.0
    capacity += 0.25 * min(cic.years_operating / 10, 1.0)
    capacity += 0.25 * (1.0 if cic.has_safeguarding_policy else 0.0)
    capacity += 0.20 * (1.0 if cic.has_financial_controls else 0.0)
    capacity += 0.15 * min(cic.staff_count / 10, 1.0)
    capacity += 0.15 * min(cic.previous_grants / 5, 1.0)

    # Easier grants = higher win prob; capacity exceeding difficulty is good
    difficulty_norm = difficulty / 5.0
    if capacity >= difficulty_norm:
        difficulty_score = 1.0
    else:
        difficulty_score = max(0.0, capacity / max(difficulty_norm, 0.01))

    # Funder preference signals
    funder_pref = 0.5  # baseline
    if grant.get("supportsStartup") and cic.years_operating < 2:
        funder_pref = 0.9  # startup-friendly funder + startup org
    elif grant.get("supportsGrowth") and 1 <= cic.years_operating < 5:
        funder_pref = 0.85
    elif grant.get("supportsScale") and cic.years_operating >= 3:
        funder_pref = 0.8
    # Mismatch penalty
    if not grant.get("supportsStartup") and cic.years_operating < 1:
        funder_pref = 0.15

    # Amount appropriateness
    max_amount = grant.get("maxAmount", 0)
    if max_amount > 0 and cic.annual_turnover > 0:
        ratio = max_amount / max(cic.annual_turnover, 1)
        if 0.05 <= ratio <= 0.5:
            amount_score = 1.0
        elif ratio < 0.05:
            amount_score = ratio / 0.05
        else:
            amount_score = max(0.15, 1.0 - (ratio - 0.5) / 3)
    elif cic.annual_turnover == 0:
        amount_score = 0.7 if max_amount <= 10_000 else 0.3
    else:
        amount_score = 0.4

    # Hard eligibility
    region_ok = _region_match(grant.get("regions", []), cic.region)
    structure_ok = True  # simplified; real blocking is in intel_labels
    if not grant.get("supportsStartup") and cic.years_operating < 1:
        structure_ok = False
    eligibility = 1.0 if (region_ok and structure_ok) else 0.0

    score = (
        0.30 * difficulty_score
        + 0.25 * funder_pref
        + 0.20 * amount_score
        + 0.25 * eligibility
    )
    return round(score * 100, 2)


def score_competition_intensity(grant: dict, cic: CICProfile) -> float:
    """
    Competition Intensity (0-100, inverted: lower = more competitive = harder).

    A HIGH score means LESS competition (favourable).
    A LOW score means MORE competition (crowded).

    Components:
    - Grant size signal (30%): larger grants attract more competition
    - Difficulty barrier (30%): harder applications have fewer applicants
    - Specificity / niche (25%): narrow eligibility = less competition
    - Funder accessibility (15%): rolling/open = more competition
    """
    max_amount = grant.get("maxAmount", 0)

    # Grant size: larger grants attract more applicants (lower score = more competition)
    if max_amount <= 5_000:
        size_score = 0.7  # small grants, moderate competition
    elif max_amount <= 25_000:
        size_score = 0.5  # mid-range, popular
    elif max_amount <= 100_000:
        size_score = 0.3  # large, very competitive
    else:
        size_score = 0.2  # major grants, highly competitive

    # Difficulty barrier: harder = fewer applicants = less competition
    difficulty = grant.get("applicationDifficulty", 3)
    difficulty_barrier = min(difficulty / 5.0, 1.0)

    # Specificity: more sectors listed = more niche = less competition
    n_sectors = len(grant.get("sectors", []))
    n_regions = len(grant.get("regions", []))
    # UK-wide grants are more competitive than regional ones
    is_national = any(
        r in ("UK-wide", "UK", "Nationwide", "England")
        for r in grant.get("regions", [])
    )
    specificity = 0.3 if is_national else 0.7
    if n_sectors > 0:
        # More specific sector targeting = less competition
        specificity = min(specificity + (n_sectors - 1) * 0.1, 1.0)

    # Funder accessibility: startup-friendly + rolling = very accessible = more competition
    accessibility_competition = 0.5  # baseline
    if grant.get("supportsStartup"):
        accessibility_competition = 0.3  # startup-friendly = more applicants
    deadline = str(grant.get("deadline", "")).lower()
    if "rolling" in deadline:
        accessibility_competition = max(0.2, accessibility_competition - 0.15)

    score = (
        0.30 * size_score
        + 0.30 * difficulty_barrier
        + 0.25 * specificity
        + 0.15 * accessibility_competition
    )
    # Scale to 0-100
    return round(score * 100, 2)


# ---------------------------------------------------------------------------
# Scorer class
# ---------------------------------------------------------------------------

class MultiDimensionalScorer:
    """
    Computes multi-dimensional scores for grant-organisation pairs.

    This is the classical production scorer. Each dimension is computed
    independently and combined into a weighted composite.

    Usage:
        scorer = MultiDimensionalScorer()
        score = scorer.score(grant_dict, cic_profile)
        print(score.summary())
    """

    def __init__(self, weights: Optional[dict] = None):
        """
        Args:
            weights: Optional custom weights for composite calculation.
                     Keys: technical_fit, social_value_alignment,
                           evidence_strength, win_probability,
                           competition_intensity.
                     Values should sum to 1.0.
        """
        self.weights = weights

    def score(self, grant: dict, cic: CICProfile) -> MultiDimensionalScore:
        """Compute all 5 dimensions for a grant-org pair."""
        technical = score_technical_fit(grant, cic)
        social_value = score_social_value_alignment(grant, cic)
        evidence = score_evidence_strength(grant, cic)
        win_prob = score_win_probability(grant, cic)
        competition = score_competition_intensity(grant, cic)

        mds = MultiDimensionalScore(
            technical_fit=technical,
            social_value_alignment=social_value,
            evidence_strength=evidence,
            win_probability=win_prob,
            competition_intensity=competition,
        )

        if self.weights:
            mds.composite = mds.compute_composite(self.weights)

        return mds

    def score_batch(
        self, grants: list[dict], cic: CICProfile
    ) -> list[tuple[dict, MultiDimensionalScore]]:
        """Score a list of grants against an org profile.

        Returns list of (grant, score) tuples sorted by composite descending.
        """
        results = [(grant, self.score(grant, cic)) for grant in grants]
        results.sort(key=lambda x: x[1].composite, reverse=True)
        return results
