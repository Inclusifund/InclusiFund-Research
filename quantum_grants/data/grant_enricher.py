"""
Grant enricher module.

Cross-references cached Convex grant data with known funder intelligence
to fill in missing amounts, deadlines, and metadata.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project root relative to this file: quantum_grants/data/ -> project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LIVE_GRANTS_PATH = PROJECT_ROOT / "Data" / "Quantum" / "live_grants.json"

# ---------------------------------------------------------------------------
# Enrichment data extracted from funder intel files
# ---------------------------------------------------------------------------
ENRICHMENT_DATA: dict[str, dict[str, Any]] = {
    # UK trusts and foundations (public funder data)
    "Commonweal Housing": {"minAmount": 5000, "maxAmount": 10000, "deadline": "Rolling", "supportsStartup": True},
    "Lloyds Bank Foundation": {"minAmount": 25000, "maxAmount": 75000, "deadline": "Summer 2026", "supportsStartup": False},
    "Oak Foundation": {"minAmount": 0, "maxAmount": 0, "deadline": "Invitation only"},
    "Clothworkers": {"minAmount": 1000, "maxAmount": 15000, "deadline": "Rolling", "supportsStartup": True},
    "Tudor Trust": {"minAmount": 10000, "maxAmount": 100000, "deadline": "Invitation only"},
    "Esmée Fairbairn": {"minAmount": 30000, "maxAmount": 150000, "deadline": "Rolling EOI"},
    "Paul Hamlyn Foundation": {"minAmount": 10000, "maxAmount": 150000, "deadline": "Rolling"},
    "Comic Relief": {"minAmount": 1000, "maxAmount": 50000, "deadline": "Closed for 2025/26"},
    "BBC Children in Need": {"minAmount": 1000, "maxAmount": 40000, "deadline": "April 2026 panel"},
    "Ubele": {"minAmount": 50000, "maxAmount": 75000, "deadline": "Watch for Round 4", "supportsStartup": True},
    "Henry Smith": {"minAmount": 20000, "maxAmount": 70000, "deadline": "Rolling"},
    "Wimbledon Foundation": {"minAmount": 1000, "maxAmount": 10000, "deadline": "Summer 2026", "supportsStartup": True},
    "City Bridge Foundation": {"minAmount": 5000, "maxAmount": 500000, "deadline": "TBC 2026"},
    "Trust for London": {"minAmount": 40000, "maxAmount": 80000, "deadline": "Rolling"},
    "Barrow Cadbury": {"minAmount": 5000, "maxAmount": 50000, "deadline": "Rolling"},
    "AB Charitable Trust": {"minAmount": 5000, "maxAmount": 25000, "deadline": "Quarterly"},

    # Additional UK funders
    "Garfield Weston": {"minAmount": 1000, "maxAmount": 100000, "deadline": "Rolling"},
    "National Lottery Community Fund": {"minAmount": 300, "maxAmount": 500000, "deadline": "Rolling"},
    "National Lottery Awards": {"minAmount": 300, "maxAmount": 20000, "deadline": "Rolling", "supportsStartup": True},
    "National Lottery Project Grants": {"minAmount": 1000, "maxAmount": 100000, "deadline": "Rolling"},
    "Masonic Charitable Foundation": {"minAmount": 1000, "maxAmount": 60000, "deadline": "Rolling"},
    "Wolfson Foundation": {"minAmount": 25000, "maxAmount": 150000, "deadline": "1 June 2026"},
    "Sir Jules Thorn": {"minAmount": 150000, "maxAmount": 500000, "deadline": "16 March 2026"},

    # Startup-friendly funders
    "The Fore": {"minAmount": 5000, "maxAmount": 45000, "deadline": "25 March - 1 April 2026", "supportsStartup": True},
    "People's Health Trust": {"minAmount": 5000, "maxAmount": 50000, "deadline": "Rolling (area-based)", "supportsStartup": True},
    "UnLtd": {"minAmount": 500, "maxAmount": 8000, "deadline": "Rolling (85% full)", "supportsStartup": True},
    "easyfundraising": {"minAmount": 500, "maxAmount": 500, "deadline": "5 April 2026"},
    "Groundwork": {"minAmount": 500, "maxAmount": 2000, "deadline": "Open to September 2026", "supportsStartup": True},
    "Sir Halley Stewart": {"minAmount": 1000, "maxAmount": 60000, "deadline": "Rolling"},
    "Hedley Foundation": {"minAmount": 250, "maxAmount": 5000, "deadline": "Quarterly"},
    "True Colours Trust": {"minAmount": 1000, "maxAmount": 10000},
    "Matthew Good Foundation": {"minAmount": 500, "maxAmount": 5000, "deadline": "Quarterly"},

    # From Wimbledon/SW London research
    "Baobab Foundation": {"minAmount": 5000, "maxAmount": 30000, "deadline": "Watch for next round", "supportsStartup": True},
    "Jack Petchey": {"minAmount": 250, "maxAmount": 6100},
    "Mercers": {"minAmount": 5000, "maxAmount": 100000},
    "Merton Giving": {"minAmount": 500, "maxAmount": 10000, "deadline": "Autumn 2026"},

    # From Merton local landscape
    "Civic Pride": {"minAmount": 2500, "maxAmount": 10000, "deadline": "Autumn 2026"},
    "Borough of Sport": {"minAmount": 500, "maxAmount": 7000, "deadline": "Spring 2026"},

    # Additional common funders
    "Baring Foundation": {"minAmount": 10000, "maxAmount": 60000, "deadline": "Rolling"},
    "Dunhill Medical Trust": {"minAmount": 10000, "maxAmount": 100000, "deadline": "Rolling"},
    "James Tudor Foundation": {"minAmount": 10000, "maxAmount": 50000, "deadline": "Rolling"},
    "Tesco Community Grants": {"minAmount": 500, "maxAmount": 1500, "deadline": "Rolling"},
    "People's Postcode Lottery": {"minAmount": 5000, "maxAmount": 50000},
    "Screwfix Foundation": {"minAmount": 500, "maxAmount": 5000, "deadline": "Rolling"},
    "Blagrave Trust": {"minAmount": 10000, "maxAmount": 100000, "deadline": "Rolling"},
    "Trusthouse Charitable Foundation": {"minAmount": 2000, "maxAmount": 100000, "deadline": "Rolling"},
    "King Charles III Charitable Fund": {"minAmount": 1000, "maxAmount": 3000, "deadline": "Annual"},
    "Allen Lane Foundation": {"minAmount": 500, "maxAmount": 15000, "deadline": "Quarterly"},
    "Stobart Sustainability Fund": {"minAmount": 1000, "maxAmount": 25000},
    "Flight Story Fund": {"minAmount": 5000, "maxAmount": 50000},
    "Patagonia Environmental Grants": {"minAmount": 5000, "maxAmount": 20000, "deadline": "Biannual"},
    "Greggs Foundation": {"minAmount": 1000, "maxAmount": 60000, "deadline": "Rolling"},
    "Social Enterprise Boost Fund": {"minAmount": 1000, "maxAmount": 10000, "supportsStartup": True},
    "Black Artist Grant": {"minAmount": 500, "maxAmount": 5000, "supportsStartup": True},
    "Black Seed Venture Capital": {"minAmount": 10000, "maxAmount": 250000, "supportsStartup": True},
    "Immerse": {"minAmount": 5000, "maxAmount": 50000, "supportsStartup": True},
    "Pre-Seed SEIS": {"minAmount": 25000, "maxAmount": 150000, "supportsStartup": True},
    "Sport England": {"minAmount": 300, "maxAmount": 50000},
    "Football Foundation": {"minAmount": 1000, "maxAmount": 100000},
    "Veolia Environmental Trust": {"minAmount": 5000, "maxAmount": 75000},
    "Community Shares Booster": {"minAmount": 10000, "maxAmount": 100000},
    "Hugo Burge Foundation": {"minAmount": 1000, "maxAmount": 10000},
    "Kaleidoscope Investments": {"minAmount": 25000, "maxAmount": 250000},
    "ARN Foundation": {"minAmount": 5000, "maxAmount": 25000},
    "SWEF Enterprise Fund": {"minAmount": 5000, "maxAmount": 50000, "supportsStartup": True},
    "Naturesave Trust": {"minAmount": 500, "maxAmount": 5000},
    "Edith M Ellis": {"minAmount": 1000, "maxAmount": 10000},
    "Common Break Fund": {"minAmount": 1000, "maxAmount": 20000},

    # Grants with zero amounts in Convex (public data)
    "Persimmon Charitable Foundation": {"minAmount": 1000, "maxAmount": 75000, "deadline": "Rolling"},
    "Superteam UK": {"minAmount": 5000, "maxAmount": 100000},
    "Craft Scotland": {"minAmount": 500, "maxAmount": 5000},
    "Farming in Protected Landscapes": {"minAmount": 1000, "maxAmount": 100000, "deadline": "Rolling to March 2029"},
    "Social Justice Small Grants": {"minAmount": 500, "maxAmount": 5000},
    "Horizon Europe": {"minAmount": 50000, "maxAmount": 500000},
    "Micro Community Investment Fund": {"minAmount": 250, "maxAmount": 2500},
    "Steel Charitable Trust": {"minAmount": 500, "maxAmount": 50000, "deadline": "Rolling"},
    "Older People\u2019s Fund": {"minAmount": 500, "maxAmount": 25000},
    "Pre\u2011Seed SEIS": {"minAmount": 25000, "maxAmount": 150000, "supportsStartup": True},
    "All-Island Community Fund": {"minAmount": 500, "maxAmount": 10000},
}


def find_enrichment_match(grant: dict[str, Any]) -> dict[str, Any] | None:
    """
    Find the best enrichment match for a grant using fuzzy contains matching.

    Checks the grant's ``name``, ``grantName``, and ``funder`` fields against
    every key in ENRICHMENT_DATA (case-insensitive substring match).
    Returns the enrichment dict on the first match, or None.
    """
    searchable_fields = [
        grant.get("name", ""),
        grant.get("grantName", ""),
        grant.get("funder", ""),
    ]
    searchable_text = " | ".join(f.lower() for f in searchable_fields if f)

    for key, data in ENRICHMENT_DATA.items():
        if key.lower() in searchable_text:
            return data
    return None


def enrich_grant(grant: dict[str, Any], enrichment: dict[str, Any]) -> list[str]:
    """
    Apply enrichment data to a single grant, only filling missing/zero fields.

    Returns a list of field names that were updated.
    """
    updated_fields: list[str] = []

    # Amount fields: only fill if currently 0 or missing, and enrichment is non-zero
    for field in ("minAmount", "maxAmount"):
        current = grant.get(field, 0)
        new_val = enrichment.get(field, 0)
        if (current is None or current == 0) and new_val != 0:
            grant[field] = float(new_val)
            # Also sync the alternate naming (amountMin/amountMax)
            alt_field = "amountMin" if field == "minAmount" else "amountMax"
            grant[alt_field] = float(new_val)
            updated_fields.append(field)

    # Deadline: fill if missing or empty
    if enrichment.get("deadline"):
        current_deadline = grant.get("deadline")
        if not current_deadline or current_deadline == "N/A":
            grant["deadline"] = enrichment["deadline"]
            updated_fields.append("deadline")

    # supportsStartup: fill if enrichment says True and grant doesn't already have it
    if enrichment.get("supportsStartup") is not None:
        current_val = grant.get("supportsStartup")
        if current_val is None:
            grant["supportsStartup"] = enrichment["supportsStartup"]
            updated_fields.append("supportsStartup")

    return updated_fields


def enrich_grants(
    grants_path: str | Path | None = None,
    save: bool = True,
) -> dict[str, Any]:
    """
    Load grants, enrich with intel data, and optionally save back.

    Parameters
    ----------
    grants_path : path to live_grants.json (defaults to standard location)
    save : whether to write enriched data back to disk

    Returns
    -------
    dict with keys: total, enriched_count, skipped, field_updates, details
    """
    path = Path(grants_path) if grants_path else LIVE_GRANTS_PATH

    with open(path) as f:
        grants: list[dict[str, Any]] = json.load(f)

    enriched_count = 0
    skipped = 0
    field_updates: dict[str, int] = {}
    details: list[dict[str, Any]] = []

    for grant in grants:
        match = find_enrichment_match(grant)
        if match is None:
            skipped += 1
            continue

        updated = enrich_grant(grant, match)
        if updated:
            enriched_count += 1
            for field in updated:
                field_updates[field] = field_updates.get(field, 0) + 1
            details.append({
                "name": grant.get("name", "unknown"),
                "fields_updated": updated,
            })

    if save:
        with open(path, "w") as f:
            json.dump(grants, f, indent=2)

    # Compute post-enrichment stats
    non_zero_max = sum(1 for g in grants if g.get("maxAmount", 0) != 0)
    non_zero_min = sum(1 for g in grants if g.get("minAmount", 0) != 0)

    return {
        "total": len(grants),
        "enriched_count": enriched_count,
        "skipped": skipped,
        "field_updates": field_updates,
        "non_zero_maxAmount": non_zero_max,
        "non_zero_minAmount": non_zero_min,
        "details": details,
    }


def enrich_grant_list(grants: list[dict[str, Any]]) -> int:
    """Enrich a list of grant dicts in-place. Returns count of enriched grants."""
    count = 0
    for grant in grants:
        match = find_enrichment_match(grant)
        if match and enrich_grant(grant, match):
            count += 1
    return count


if __name__ == "__main__":
    result = enrich_grants()
    print(f"Total grants: {result['total']}")
    print(f"Enriched: {result['enriched_count']}")
    print(f"Skipped (no match): {result['skipped']}")
    print(f"Non-zero maxAmount: {result['non_zero_maxAmount']} / {result['total']}")
    print(f"Non-zero minAmount: {result['non_zero_minAmount']} / {result['total']}")
    print(f"Field updates: {result['field_updates']}")
    print("\nDetails:")
    for d in result["details"]:
        print(f"  {d['name']}: {d['fields_updated']}")
