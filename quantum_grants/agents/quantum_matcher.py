"""
Agent 9: Quantum Grant Matcher

Matches CIC profiles to relevant UK grants using a quantum-classical
hybrid circuit. Fetches live grants from Convex, encodes features,
runs the variational quantum circuit, and returns ranked matches.

Pipeline position:
  Agent 1 (Research) → Agent 9 (Quantum Matcher) → Agent 2 (Deadline)
                                                  → Agent 10 (Writer)

Input:  CIC profile dict
Output: Top-K grants ranked by quantum match score
"""

from __future__ import annotations

import json
import time
import hashlib
import numpy as np
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from quantum_grants.circuits.grant_circuit import QuantumMatchCircuit
from quantum_grants.convex_integration.client import ConvexClient, QuantumMatchResult
from quantum_grants.config import DATA_DIR


# --- CIC Profile (real-world input) ---

@dataclass
class CICProfile:
    """A real CIC/charity profile for matching."""
    org_id: str
    org_name: str
    legal_structure: str  # "cic", "charity", "cio", "clg", "community_group"
    sectors: list[str]
    themes: list[str]
    region: str
    annual_turnover: float
    years_operating: float
    staff_count: int = 0
    has_safeguarding_policy: bool = False
    has_financial_controls: bool = False
    previous_grants: int = 0
    beneficiaries: list[str] = field(default_factory=list)


# --- Feature Encoding (real grants → quantum features) ---

STRUCTURE_MAP = {
    "cic": ["cic", "social_enterprise", "community_group"],
    "charity": ["charity", "cio"],
    "cio": ["charity", "cio"],
    "clg": ["cic", "social_enterprise"],
    "community_group": ["community_group", "social_enterprise"],
}

REGION_MAP = {
    "UK-wide": None,  # matches everything
    "England": [
        "north_east", "north_west", "yorkshire", "east_midlands",
        "west_midlands", "east", "london", "south_east", "south_west",
        "London", "South East", "South West", "North East", "North West",
        "Yorkshire", "East Midlands", "West Midlands", "East of England",
    ],
    "Wales": ["wales", "Wales"],
    "Scotland": ["scotland", "Scotland"],
    "Northern Ireland": ["northern_ireland", "Northern Ireland"],
}


def _region_match(grant_regions: list[str], cic_region: str) -> bool:
    """Check if a CIC's region is covered by the grant's regions."""
    for gr in grant_regions:
        if gr in ("UK-wide", "UK", "Nationwide"):
            return True
        if gr.lower() == cic_region.lower():
            return True
        mapped = REGION_MAP.get(gr, [])
        if mapped and cic_region.lower() in [r.lower() for r in mapped]:
            return True
    return False


SECTOR_KEYWORDS = {
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


def _sector_overlap(grant_sectors: list[str], cic_sectors: list[str]) -> float:
    """Fuzzy keyword-based sector overlap."""
    if not grant_sectors and not cic_sectors:
        return 0.0

    grant_text = " ".join(s.lower() for s in grant_sectors)
    cic_text = " ".join(s.lower() for s in cic_sectors)

    # Find which keyword groups each side matches
    grant_groups = set()
    cic_groups = set()
    for group, keywords in SECTOR_KEYWORDS.items():
        if any(kw in grant_text for kw in keywords):
            grant_groups.add(group)
        if any(kw in cic_text for kw in keywords):
            cic_groups.add(group)

    if not grant_groups and not cic_groups:
        # Fallback: exact match
        gs = {s.lower().strip() for s in grant_sectors}
        cs = {s.lower().strip() for s in cic_sectors}
        intersection = len(gs & cs)
        union = len(gs | cs)
        return intersection / union if union > 0 else 0.0

    union = len(grant_groups | cic_groups)
    intersection = len(grant_groups & cic_groups)
    return intersection / union if union > 0 else 0.0


def _structure_eligible(grant: dict, cic: CICProfile) -> bool:
    """Check if CIC structure is likely eligible for the grant."""
    if grant.get("supportsStartup") and cic.years_operating < 2:
        return True
    if grant.get("supportsGrowth") and cic.years_operating >= 1:
        return True
    if grant.get("supportsScale") and cic.years_operating >= 3:
        return True
    # Default: allow if no stage filtering blocked
    return grant.get("supportsStartup", False) or grant.get("supportsGrowth", False)


def encode_real_pair(grant: dict, cic: CICProfile) -> np.ndarray:
    """
    Encode a real Convex grant + CIC profile into a 6D feature vector.

    All features are designed to vary across BOTH grants and CICs:
    [0] eligibility    — region + structure + stage fit
    [1] sector_overlap — Jaccard similarity of sector lists
    [2] theme_overlap  — keyword matching (description + name + sectors vs CIC themes + beneficiaries)
    [3] amount_fit     — how well grant size matches CIC scale
    [4] difficulty_fit — grant complexity vs CIC capacity
    [5] stage_fit      — grant stage support vs CIC maturity
    """
    # [0] Eligibility: region + structure
    region_ok = _region_match(grant.get("regions", []), cic.region)
    structure_ok = _structure_eligible(grant, cic)
    eligibility = 1.0 if (region_ok and structure_ok) else 0.0

    # [1] Sector overlap
    sector = _sector_overlap(grant.get("sectors", []), cic.sectors)

    # [2] Theme overlap: deep keyword matching across multiple fields
    search_text = " ".join([
        grant.get("description", ""),
        grant.get("name", ""),
        " ".join(grant.get("sectors", [])),
    ]).lower()

    match_terms = [t.lower() for t in cic.themes + cic.sectors + cic.beneficiaries]
    # Deduplicate
    match_terms = list(set(match_terms))
    if match_terms:
        hits = sum(1 for t in match_terms if t in search_text)
        theme = min(hits / max(len(match_terms), 1), 1.0)
    else:
        theme = 0.0

    # [3] Amount fit: how well grant range matches CIC scale
    max_amount = grant.get("maxAmount", 0)
    min_amount = grant.get("minAmount", 0)
    if max_amount > 0:
        if cic.annual_turnover > 0:
            # Ideal: grant max is 10-50% of turnover
            ratio = max_amount / max(cic.annual_turnover, 1)
            if 0.05 <= ratio <= 0.5:
                amount_fit = 1.0
            elif ratio < 0.05:
                amount_fit = ratio / 0.05  # too small
            else:
                amount_fit = max(0.2, 1.0 - (ratio - 0.5) / 5)  # too large
        else:
            # Pre-revenue: small grants are better
            if max_amount <= 10_000:
                amount_fit = 0.9
            elif max_amount <= 25_000:
                amount_fit = 0.7
            elif max_amount <= 100_000:
                amount_fit = 0.4
            else:
                amount_fit = 0.2
    else:
        amount_fit = 0.3  # unknown amount

    # [4] Difficulty fit: grant difficulty vs CIC capacity
    difficulty = grant.get("applicationDifficulty", 3)
    capacity = 0.0
    capacity += 0.25 * min(cic.years_operating / 10, 1.0)
    capacity += 0.25 * (1.0 if cic.has_safeguarding_policy else 0.0)
    capacity += 0.20 * (1.0 if cic.has_financial_controls else 0.0)
    capacity += 0.15 * min(cic.staff_count / 10, 1.0)
    capacity += 0.15 * min(cic.previous_grants / 5, 1.0)
    # Easy grants fit low-capacity orgs; hard grants need high capacity
    difficulty_norm = difficulty / 5.0
    difficulty_fit = 1.0 - abs(capacity - difficulty_norm)
    difficulty_fit = max(0.0, min(1.0, difficulty_fit))

    # [5] Stage fit: how well grant stage support matches CIC maturity
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

    return np.array([
        eligibility, sector, theme, amount_fit, difficulty_fit, stage_fit
    ], dtype=np.float64)


# --- Match Result ---

@dataclass
class GrantMatch:
    """A ranked grant match result."""
    rank: int
    grant_id: str
    grant_name: str
    funder: str
    min_amount: float
    max_amount: float
    quantum_score: float
    eligibility: float
    sector_overlap: float
    theme_overlap: float
    capacity: float
    status: str
    website: str


# --- Agent 9: Quantum Grant Matcher ---

class QuantumGrantMatcher:
    """
    Agent 9 — Quantum Grant Matcher.

    Uses a variational quantum circuit to score and rank live grants
    against a CIC profile. Connects to the Convex backend for real
    grant data and stages results for pipeline consumption.

    Usage:
        agent = QuantumGrantMatcher()
        matches = agent.find_matches(cic_profile, top_k=20)
        agent.stage_results(matches, cic_profile)
    """

    def __init__(
        self,
        n_layers: int = 2,
        threshold: float = 0.5,
        convex_url: Optional[str] = None,
        use_cache: bool = True,
        backend: str = "auto",
    ):
        self.circuit = QuantumMatchCircuit(n_layers=n_layers)
        self.threshold = threshold
        self.classical_weight = 1.0
        self.classical_bias = 0.0
        self.convex = ConvexClient(convex_url)
        self.use_cache = use_cache
        self.backend = backend
        self._grants: Optional[list[dict]] = None

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def _load_grants(self, include_closed: bool = False) -> list[dict]:
        """Fetch grants from Convex (with local cache fallback)."""
        if self._grants and not include_closed:
            return self._grants

        try:
            if include_closed:
                grants = self.convex.fetch_all_grants()
            else:
                grants = self.convex.fetch_open_grants()
            self._grants = grants
            return grants
        except Exception:
            if self.use_cache:
                return self.convex.load_cached_grants()
            raise

    def score_pair(self, grant: dict, cic: CICProfile) -> float:
        """Score a single grant-CIC pair using the quantum circuit."""
        features = encode_real_pair(grant, cic)
        quantum_score = self.circuit.forward(features, backend=self.backend)
        calibrated = self._sigmoid(
            self.classical_weight * quantum_score + self.classical_bias
        )
        return float(calibrated)

    def find_matches(
        self,
        cic: CICProfile,
        top_k: int = 20,
        include_closed: bool = False,
        min_score: Optional[float] = None,
    ) -> list[GrantMatch]:
        """
        Find the top-K grants for a CIC profile.

        Fetches live grants from Convex, scores each against the CIC
        using the quantum circuit, and returns ranked results.
        """
        grants = self._load_grants(include_closed=include_closed)

        scored = []
        for grant in grants:
            features = encode_real_pair(grant, cic)
            q_score = self.score_pair(grant, cic)

            if min_score and q_score < min_score:
                continue

            scored.append((grant, q_score, features))

        # Sort by quantum score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Build ranked results
        matches = []
        for rank, (grant, q_score, features) in enumerate(scored[:top_k], 1):
            matches.append(GrantMatch(
                rank=rank,
                grant_id=grant.get("_id", f"G-{rank:04d}"),
                grant_name=grant.get("name", "Unknown"),
                funder=grant.get("funder", "Unknown"),
                min_amount=grant.get("minAmount", 0),
                max_amount=grant.get("maxAmount", 0),
                quantum_score=round(q_score, 4),
                eligibility=round(float(features[0]), 4),
                sector_overlap=round(float(features[1]), 4),
                theme_overlap=round(float(features[2]), 4),
                capacity=round(float(features[3]), 4),
                status=grant.get("status", "Unknown"),
                website=grant.get("website", ""),
            ))

        return matches

    def stage_results(
        self, matches: list[GrantMatch], cic: CICProfile
    ) -> dict:
        """Stage quantum match results for Convex sync."""
        params_hash = hashlib.md5(
            self.circuit.params.tobytes()
        ).hexdigest()[:12]
        now = time.strftime("%Y-%m-%dT%H:%M:%S")

        results = []
        for m in matches:
            results.append(QuantumMatchResult(
                grant_id=m.grant_id,
                org_id=cic.org_id,
                quantum_score=m.quantum_score,
                eligibility_score=m.eligibility,
                alignment_score=(m.sector_overlap + m.theme_overlap) / 2,
                capacity_score=m.capacity,
                is_recommended=m.quantum_score >= self.threshold,
                circuit_params_hash=params_hash,
                computed_at=now,
            ))

        manifest = self.convex.batch_store(results)
        return manifest

    def summary(self, matches: list[GrantMatch]) -> str:
        """Pretty-print match results."""
        lines = [
            f"Quantum Grant Matcher — {len(matches)} matches",
            "=" * 60,
        ]
        for m in matches:
            rec = "RECOMMENDED" if m.quantum_score >= self.threshold else ""
            lines.append(
                f"  #{m.rank:2d}  {m.quantum_score:.3f}  "
                f"£{m.min_amount:,.0f}-£{m.max_amount:,.0f}  "
                f"{m.grant_name[:40]:<40s}  {rec}"
            )
        lines.append("=" * 60)
        recommended = sum(1 for m in matches if m.quantum_score >= self.threshold)
        lines.append(f"Recommended: {recommended}/{len(matches)}")
        return "\n".join(lines)

    def get_params(self) -> dict:
        """Export model parameters for checkpointing."""
        return {
            "quantum_params": self.circuit.params.tolist(),
            "classical_weight": self.classical_weight,
            "classical_bias": self.classical_bias,
            "threshold": self.threshold,
            "n_layers": self.circuit.n_layers,
        }

    def load_params(self, path: str) -> None:
        """Load model parameters from a JSON file."""
        with open(path) as f:
            params = json.load(f)
        self.circuit.params = np.array(params["quantum_params"])
        self.classical_weight = params["classical_weight"]
        self.classical_bias = params["classical_bias"]
        self.threshold = params["threshold"]

    def save_params(self, path: str) -> None:
        """Save model parameters to a JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.get_params(), f, indent=2)
