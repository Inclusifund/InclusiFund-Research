#!/usr/bin/env python3
"""
Fix corrupted sector data in the Convex grants database.

Finds grants with sectors starting with '"' (literal double-quote)
and patches them via the updateGrant mutation.

Usage:
    python3 scripts/fix_corrupted_sectors.py          # Dry run (default)
    python3 scripts/fix_corrupted_sectors.py --execute # Push fixes to Convex
"""

import json
import sys
import urllib.request
import urllib.error

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud"
QUERY_ENDPOINT = f"{CONVEX_URL}/api/query"
MUTATION_ENDPOINT = f"{CONVEX_URL}/api/mutation"

# Mapping: bad sector → cleaned sector (None = delete)
SECTOR_FIXES = {
    '"Community Wellbeing': "Community Wellbeing",
    '"Elderly Support': "Elderly Support",
    '"Human Rights': "Human Rights",
    '"Mental Health': "Mental Health",
    '"Peacebuilding': "Peacebuilding",
    '"Youth Entrepreneurship': "Youth Entrepreneurship",
}

# Prefixes that indicate junk/non-sector data — delete entirely
JUNK_PREFIXES = [
    '"Category',
    '"Eligibility:',
    '"Important Notice',
    '"Pre-seed and Seed',
    '"Stage:',
]


def fetch_all_grants():
    """Fetch all grants from Convex."""
    payload = json.dumps({"path": "grants:getAllGrants", "args": {}}).encode()
    req = urllib.request.Request(
        QUERY_ENDPOINT, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if data.get("status") != "success":
        raise RuntimeError(f"Query failed: {data.get('errorMessage', 'unknown')}")
    return data["value"]


def update_grant_sectors(grant_id, new_sectors):
    """Patch a grant's sectors via updateGrant mutation."""
    payload = json.dumps({
        "path": "grants:updateGrant",
        "args": {"id": grant_id, "sectors": new_sectors},
    }).encode()
    req = urllib.request.Request(
        MUTATION_ENDPOINT, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if data.get("status") != "success":
        raise RuntimeError(f"Update failed for {grant_id}: {data.get('errorMessage', 'unknown')}")
    return data


def clean_sector(sector):
    """
    Returns (cleaned_sector, action) where action is one of:
    - ("keep", sector) — no change needed
    - ("fix", new_sector) — stripped the quote
    - ("delete", None) — junk/non-sector, remove it
    """
    if not sector.startswith('"'):
        return ("keep", sector)

    # Check exact match fixes first
    if sector in SECTOR_FIXES:
        return ("fix", SECTOR_FIXES[sector])

    # Check junk prefixes
    for prefix in JUNK_PREFIXES:
        if sector.startswith(prefix):
            return ("delete", None)

    # Unknown quote-prefixed sector — strip the quote as fallback
    stripped = sector.lstrip('"').strip()
    if stripped:
        return ("fix", stripped)
    return ("delete", None)


def main():
    execute = "--execute" in sys.argv

    print("Fetching all grants from Convex...")
    grants = fetch_all_grants()
    print(f"Fetched {len(grants)} grants\n")

    affected = []
    for grant in grants:
        grant_id = grant.get("_id", "")
        name = grant.get("name", "Unknown")
        sectors = grant.get("sectors", [])

        cleaned_sectors = []
        changes = []
        for sector in sectors:
            action, result = clean_sector(sector)
            if action == "keep":
                cleaned_sectors.append(sector)
            elif action == "fix":
                cleaned_sectors.append(result)
                changes.append(f"  FIX: {repr(sector)} -> {repr(result)}")
            elif action == "delete":
                changes.append(f"  DEL: {repr(sector)}")

        if changes:
            affected.append({
                "id": grant_id,
                "name": name,
                "old_sectors": sectors,
                "new_sectors": cleaned_sectors,
                "changes": changes,
            })

    if not affected:
        print("No corrupted sectors found. Database is clean.")
        return

    print(f"Found {len(affected)} grants with corrupted sectors:\n")
    for item in affected:
        print(f"  {item['name']}")
        for change in item["changes"]:
            print(f"    {change}")
        print(f"    Result: {item['new_sectors']}")
        print()

    if not execute:
        print("--- DRY RUN ---")
        print("Run with --execute to push fixes to Convex.")
        return

    print("Pushing fixes to Convex...\n")
    success = 0
    failed = 0
    for item in affected:
        try:
            update_grant_sectors(item["id"], item["new_sectors"])
            print(f"  Fixed: {item['name']}")
            success += 1
        except Exception as e:
            print(f"  FAILED: {item['name']} — {e}")
            failed += 1

    print(f"\nDone. {success} fixed, {failed} failed.")


if __name__ == "__main__":
    main()
