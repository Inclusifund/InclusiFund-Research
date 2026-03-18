#!/usr/bin/env python3
"""
sync_dev_to_prod.py — Sync opportunity records from Convex dev to prod.

Dev:  terrific-bloodhound-927.convex.cloud
Prod: handsome-labrador-691.convex.cloud

Usage:
    python3 scripts/sync_dev_to_prod.py              # dry-run (default)
    python3 scripts/sync_dev_to_prod.py --dry-run    # explicit dry-run
    python3 scripts/sync_dev_to_prod.py --execute     # actually push to prod
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error

DEV_URL = "https://terrific-bloodhound-927.convex.cloud"
PROD_URL = "https://handsome-labrador-691.convex.cloud"

# Fields that addGrant accepts
GRANT_FIELDS = [
    "name", "funder", "minAmount", "maxAmount", "deadline", "status",
    "sectors", "regions", "applicationDifficulty", "supportsStartup",
    "supportsGrowth", "supportsScale", "website", "description",
    "opportunityType", "eligibility",
]

# Required fields (mutation will reject without these)
REQUIRED_FIELDS = [
    "name", "funder", "minAmount", "maxAmount", "status",
    "sectors", "regions", "applicationDifficulty",
    "supportsStartup", "supportsGrowth",
]

# Optional fields (include only if present and non-None)
OPTIONAL_FIELDS = [
    "deadline", "supportsScale", "website", "description",
    "opportunityType", "eligibility",
]


def convex_post(base_url: str, path: str, body: dict) -> dict:
    """POST JSON to a Convex endpoint and return parsed response."""
    url = f"{base_url}/api/{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"  HTTP {e.code} from {url}: {error_body[:200]}")
        raise
    except urllib.error.URLError as e:
        print(f"  Connection error to {url}: {e.reason}")
        raise


def fetch_all_grants(base_url: str, label: str) -> list:
    """Fetch all grants from a Convex deployment."""
    print(f"Fetching grants from {label} ({base_url})...")
    result = convex_post(base_url, "query", {
        "path": "grants:getAllGrants",
        "args": {},
    })
    # Convex wraps query results in {"value": [...], "status": "success"}
    if isinstance(result, dict) and "value" in result:
        records = result["value"]
    elif isinstance(result, list):
        records = result
    else:
        print(f"  Unexpected response shape: {str(result)[:200]}")
        records = []
    print(f"  Found {len(records)} records in {label}")
    return records


def build_grant_args(record: dict) -> dict:
    """Extract addGrant args from a dev record, stripping Convex internals."""
    args = {}
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            raise ValueError(f"Missing required field '{field}' in record: {record.get('name', '???')}")
        args[field] = record[field]
    for field in OPTIONAL_FIELDS:
        if field in record and record[field] is not None:
            args[field] = record[field]
    return args


def main():
    parser = argparse.ArgumentParser(description="Sync Convex dev → prod")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would be synced (default)")
    group.add_argument("--execute", action="store_true",
                       help="Actually push missing records to prod")
    args = parser.parse_args()

    execute = args.execute

    # 1. Fetch from both deployments
    dev_records = fetch_all_grants(DEV_URL, "DEV")
    prod_records = fetch_all_grants(PROD_URL, "PROD")

    if not dev_records:
        print("No records in dev — nothing to sync.")
        return

    # 2. Build lookup of prod names (case-insensitive)
    prod_names = {r.get("name", "").strip().lower() for r in prod_records}
    print(f"\nProd has {len(prod_names)} unique names")

    # 3. Identify missing records
    missing = []
    for r in dev_records:
        name = r.get("name", "").strip()
        if name.lower() not in prod_names:
            missing.append(r)

    print(f"Dev has {len(dev_records)} records, {len(missing)} missing from prod\n")

    if not missing:
        print("Prod is already in sync with dev. Nothing to do.")
        return

    # 4. Report / push
    if not execute:
        print("=== DRY RUN — the following records would be pushed to prod ===\n")
        for i, r in enumerate(missing, 1):
            opp_type = r.get("opportunityType", "Grant")
            funder = r.get("funder", "Unknown")
            print(f"  {i:>3}. [{opp_type}] {r['name']}  (funder: {funder})")
        print(f"\nTotal: {len(missing)} records")
        print("\nRe-run with --execute to push these to prod.")
    else:
        print(f"=== EXECUTING — pushing {len(missing)} records to prod ===\n")
        success = 0
        errors = 0
        for i, r in enumerate(missing, 1):
            name = r.get("name", "???")
            try:
                grant_args = build_grant_args(r)
                print(f"  [{i}/{len(missing)}] Pushing: {name}...", end=" ")
                result = convex_post(PROD_URL, "mutation", {
                    "path": "adminGrants:addGrant",
                    "args": grant_args,
                })
                print("OK")
                success += 1
                # Small delay to avoid hammering the API
                if i < len(missing):
                    time.sleep(0.15)
            except Exception as e:
                print(f"FAILED — {e}")
                errors += 1

        print(f"\n=== Sync complete ===")
        print(f"  Pushed:  {success}")
        print(f"  Errors:  {errors}")
        print(f"  Skipped: {len(dev_records) - len(missing)} (already in prod)")


if __name__ == "__main__":
    main()
