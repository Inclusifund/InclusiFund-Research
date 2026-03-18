#!/usr/bin/env python3
"""
Enrich cached Convex grants and export in the production schema format
for bulkSyncGrants. Normalises all grants to the new schema, enriches
missing amounts/deadlines, and writes a clean JSON ready for Convex push.
"""

import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from quantum_grants.pipeline import normalise_grant
from quantum_grants.data.grant_enricher import enrich_grant_list

DATA_DIR = PROJECT_ROOT / "Data" / "Quantum"
CACHE_PATH = DATA_DIR / "live_grants.json"
OUTPUT_PATH = DATA_DIR / "enriched_grants_for_sync.json"


def main():
    # Load raw cached grants from Convex
    with open(CACHE_PATH) as f:
        raw_grants = json.load(f)

    print(f"Loaded {len(raw_grants)} grants from cache")

    # Normalise to new schema
    normalised = [normalise_grant(g) for g in raw_grants]

    # Enrich with intel data (fills missing amounts, deadlines)
    enriched_count = enrich_grant_list(normalised)
    print(f"Enriched {enriched_count} grants with intel data")

    # Convert to production schema (matching Convex grants table)
    production_grants = []
    for g in normalised:
        grant = {
            "name": g.get("name", "Unnamed"),
            "funder": g.get("funder", "Unknown"),
            "minAmount": float(g.get("minAmount", 0)),
            "maxAmount": float(g.get("maxAmount", 0)),
            "status": g.get("status", "Open"),
            "sectors": g.get("sectors", []),
            "regions": g.get("regions", []),
            "applicationDifficulty": int(g.get("applicationDifficulty", 3)),
            "supportsStartup": bool(g.get("supportsStartup", False)),
            "supportsGrowth": bool(g.get("supportsGrowth", False)),
            "supportsScale": bool(g.get("supportsScale", False)),
            "website": g.get("website", ""),
            "description": g.get("description", ""),
        }

        # Only include deadline if present
        if g.get("deadline"):
            grant["deadline"] = g["deadline"]

        production_grants.append(grant)

    # Stats
    non_zero_max = sum(1 for g in production_grants if g["maxAmount"] > 0)
    non_zero_min = sum(1 for g in production_grants if g["minAmount"] > 0)
    with_deadline = sum(1 for g in production_grants if g.get("deadline"))
    startup_friendly = sum(1 for g in production_grants if g["supportsStartup"])

    print(f"\n--- Export Stats ---")
    print(f"Total grants: {len(production_grants)}")
    print(f"With maxAmount > 0: {non_zero_max}/{len(production_grants)}")
    print(f"With minAmount > 0: {non_zero_min}/{len(production_grants)}")
    print(f"With deadline: {with_deadline}/{len(production_grants)}")
    print(f"Startup-friendly: {startup_friendly}/{len(production_grants)}")

    # Write the Convex-ready JSON
    with open(OUTPUT_PATH, "w") as f:
        json.dump(production_grants, f, indent=2)

    print(f"\nExported to: {OUTPUT_PATH}")

    # Also write in the bulkSyncGrants arg format
    bulk_arg = {"grants": production_grants}
    bulk_path = DATA_DIR / "bulk_sync_payload.json"
    with open(bulk_path, "w") as f:
        json.dump(bulk_arg, f, indent=2)

    print(f"Bulk sync payload: {bulk_path}")


if __name__ == "__main__":
    main()
