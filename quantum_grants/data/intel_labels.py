"""
Generate labelled training pairs from funder policy characteristics.

Uses publicly available funder eligibility rules (structure requirements,
income thresholds, startup-friendliness) to compute match labels for
grant-organisation pairs.  No client-specific data is stored here.

Label ranges:
    HIGH / VERY STRONG / STRONG / TIER 1  -> 0.85 - 0.95
    MEDIUM / MODERATE / TIER 2            -> 0.50 - 0.65
    LOW                                   -> 0.15 - 0.30
    DO NOT PURSUE / NOT ELIGIBLE          -> 0.0
    FUTURE / CONDITIONAL                  -> 0.35 - 0.45
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class IntelLabel:
    """A single funder-client label from human research."""
    funder_name: str
    client_id: str
    fit_rating: str       # raw rating text
    label: float          # numeric label in [0, 1]
    source_file: str = ""


# ---------------------------------------------------------------------------
# Rating -> label mapping
# ---------------------------------------------------------------------------

_RATING_LABEL_MAP: dict[str, float] = {
    # High band (0.85-0.95)
    "VERY STRONG": 0.95,
    "VERY HIGH":   0.95,
    "HIGH":        0.90,
    "STRONG":      0.90,
    "TIER 1":      0.90,
    # Medium band (0.50-0.65)
    "MODERATE-HIGH":  0.65,
    "MODERATE-GOOD":  0.60,
    "MEDIUM":         0.58,
    "MODERATE":       0.55,
    "TIER 2":         0.58,
    # Future band (0.35-0.45)
    "FUTURE":       0.40,
    "CONDITIONAL":  0.40,
    "TIER 3":       0.38,
    "TIER 4":       0.35,
    # Low band (0.15-0.30)
    "LOW":           0.22,
    "LOW-MODERATE":  0.30,
    "MODERATE-LOW":  0.30,
    # Zero band
    "DO NOT PURSUE":  0.0,
    "NOT ELIGIBLE":   0.0,
    "NOT APPLICABLE": 0.0,
}


def rating_to_label(raw_rating: str) -> float:
    """Convert a raw fit rating string to a numeric label."""
    text = raw_rating.strip().upper()
    # Try exact match first
    if text in _RATING_LABEL_MAP:
        return _RATING_LABEL_MAP[text]
    # Try prefix matches (longest first)
    for key in sorted(_RATING_LABEL_MAP, key=len, reverse=True):
        if key in text:
            return _RATING_LABEL_MAP[key]
    return 0.50  # default unknown


# ---------------------------------------------------------------------------
# Blocked funders (from domain knowledge / MEMORY.md)
# ---------------------------------------------------------------------------

# Maps: funder_name_fragment -> { blocked_structures, reason }
BLOCKED_FUNDERS: dict[str, dict] = {
    "garfield weston": {
        "blocked_structures": {"cic"},
        "reason": "CICs explicitly excluded",
    },
    "henry smith": {
        "min_age_months": 18,
        "min_income": 50_000,
        "reason": "Needs 18 months + £50k income",
    },
    "masonic": {
        "min_income": 25_000,
        "reason": "Needs £25k income",
    },
    "lloyds bank": {
        "min_income": 25_000,
        "blocked_structures": {"cic"},
        "reason": "Charity/CIO only, needs £25k income",
    },
    "the fore": {
        "needs_accounts": True,
        "reason": "Needs accounts + lottery element",
    },
    "tudor trust": {
        "invitation_only": True,
        "reason": "Invitation only",
    },
    "pears": {
        "invitation_only": True,
        "reason": "Invitation only",
    },
    "burdett trust": {
        "closed": True,
        "reason": "Strategy review, not accepting applications",
    },
    "john lyon": {
        "blocked_regions": {"merton", "wimbledon"},
        "reason": "Geography - not in beneficial area",
    },
    "lankelly chase": {
        "closed": True,
        "reason": "Winding down, closing by 2028",
    },
}


def is_funder_blocked(funder_name: str, legal_structure: str,
                      region: str = "", annual_turnover: float = 0,
                      years_operating: float = 0) -> bool:
    """Check if a funder is blocked for a given client profile."""
    fn_lower = funder_name.lower()
    for fragment, rules in BLOCKED_FUNDERS.items():
        if fragment not in fn_lower:
            continue
        # Structural block
        blocked_structs = rules.get("blocked_structures", set())
        if legal_structure.lower() in blocked_structs:
            return True
        # Income block
        min_income = rules.get("min_income", 0)
        if min_income > 0 and annual_turnover < min_income:
            return True
        # Age block
        min_age = rules.get("min_age_months", 0)
        if min_age > 0 and (years_operating * 12) < min_age:
            return True
        # Invitation only
        if rules.get("invitation_only"):
            return True
        # Closed
        if rules.get("closed"):
            return True
        # Region block
        blocked_regions = rules.get("blocked_regions", set())
        if blocked_regions and region.lower() in blocked_regions:
            return True
    return False


# ---------------------------------------------------------------------------
# Characteristic-based funder policies (public eligibility info)
# ---------------------------------------------------------------------------

# Maps funder name fragments to their known public characteristics.
# These are used to compute match labels based on org profile traits
# (structure, age, income) rather than client-specific assessments.
FUNDER_CHARACTERISTICS: dict[str, dict] = {
    "awards for all": {
        "startup_friendly": True,
        "max_amount": 10_000,
        "no_accounts_ok": True,
    },
    "nlcf": {
        "startup_friendly": True,
        "max_amount": 500_000,
        "prefers_lived_experience": True,
    },
    "national lottery community fund": {
        "startup_friendly": True,
        "max_amount": 500_000,
        "prefers_lived_experience": True,
    },
    "unltd": {
        "startup_friendly": True,
        "max_amount": 8_000,
        "no_accounts_ok": True,
    },
    "sir halley stewart": {
        "startup_friendly": True,
        "max_amount": 60_000,
        "first_funder": True,
    },
    "garfield weston": {
        "min_accounts_years": 1,
        "blocked_structures": {"cic"},
    },
    "henry smith": {
        "min_age_months": 18,
        "min_income": 50_000,
    },
    "esmee fairbairn": {
        "min_income": 25_000,
        "prefers_established": True,
    },
    "comic relief": {
        "min_income": 25_000,
        "prefers_established": True,
    },
    "paul hamlyn": {
        "min_income": 25_000,
        "prefers_established": True,
    },
    "bbc children in need": {
        "startup_friendly": True,
        "requires_youth_focus": True,
    },
}


def compute_characteristic_label(
    grant_name: str,
    grant_funder: str,
    legal_structure: str = "",
    annual_turnover: float = 0,
    years_operating: float = 0,
) -> Optional[float]:
    """
    Compute a label based on funder characteristics vs org profile.

    Uses publicly available funder eligibility rules to estimate fit.
    Returns a label in [0, 1] if a matching funder policy is found,
    or None to fall back to heuristics.
    """
    combined = f"{grant_name} {grant_funder}".lower()

    for fragment, chars in FUNDER_CHARACTERISTICS.items():
        if fragment not in combined:
            continue

        # Check hard blocks
        blocked_structs = chars.get("blocked_structures", set())
        if legal_structure.lower() in blocked_structs:
            return 0.0

        min_income = chars.get("min_income", 0)
        if min_income > 0 and annual_turnover < min_income:
            return 0.2  # low fit, income too low

        min_age = chars.get("min_age_months", 0)
        if min_age > 0 and (years_operating * 12) < min_age:
            return 0.2  # low fit, too young

        # Startup-friendly funders are high fit for startups
        if chars.get("startup_friendly") and years_operating < 2:
            return 0.85

        # No accounts requirement met by pre-revenue orgs
        if chars.get("no_accounts_ok") and annual_turnover == 0:
            return 0.80

        # Prefers established but org is a startup
        if chars.get("prefers_established") and years_operating < 2:
            return 0.35

        # First-funder friendly
        if chars.get("first_funder") and years_operating < 2:
            return 0.85

        # Default: decent match if no blockers triggered
        return 0.60

    return None


# ---------------------------------------------------------------------------
# Funder name matching
# ---------------------------------------------------------------------------

def funder_name_matches(grant_name: str, intel_funder: str) -> bool:
    """
    Check if a Convex grant name/funder matches an intel funder name.

    Uses case-insensitive substring matching with some normalisation.
    """
    gn = grant_name.lower().strip()
    inf = intel_funder.lower().strip()

    # Direct substring match either direction
    if inf in gn or gn in inf:
        return True

    # Handle common abbreviations
    _abbreviations = {
        "nlcf": "national lottery community fund",
        "bbc cin": "bbc children in need",
        "gla vru": "gla violence reduction",
        "gla": "greater london authority",
        "phf": "paul hamlyn foundation",
    }
    for abbr, full in _abbreviations.items():
        if abbr in inf and full in gn:
            return True
        if abbr in gn and full in inf:
            return True

    # Word overlap: if all words in the shorter string appear in the longer
    inf_words = set(inf.split())
    gn_words = set(gn.split())
    # Remove very common words
    stopwords = {"the", "foundation", "fund", "trust", "charity", "programme",
                 "grant", "grants", "for", "of", "and", "&", "-", "uk"}
    inf_sig = inf_words - stopwords
    gn_sig = gn_words - stopwords

    if inf_sig and gn_sig:
        # Check if significant words overlap
        overlap = inf_sig & gn_sig
        shorter = min(len(inf_sig), len(gn_sig))
        if shorter > 0 and len(overlap) / shorter >= 0.5:
            return True

    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_blocked_label(grant_name: str, grant_funder: str,
                      legal_structure: str, region: str = "",
                      annual_turnover: float = 0,
                      years_operating: float = 0) -> Optional[float]:
    """
    Check if a funder is blocked for a client profile.

    Returns 0.0 if blocked, None if not blocked.
    """
    combined = f"{grant_name} {grant_funder}".lower()
    for fragment in BLOCKED_FUNDERS:
        if fragment in combined:
            if is_funder_blocked(
                combined, legal_structure, region,
                annual_turnover, years_operating
            ):
                return 0.0
    return None
