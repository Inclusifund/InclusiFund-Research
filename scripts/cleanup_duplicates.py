#!/usr/bin/env python3
"""
Duplicate cleanup for InclusiFund Convex grants database.
Identifies duplicates by name (case-insensitive, trimmed), keeps the newest
record (highest createdAt), and deletes the rest.
"""

import urllib.request
import json
import sys
from collections import defaultdict
from datetime import datetime

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud"
QUERY_URL = f"{CONVEX_URL}/api/query"
MUTATION_URL = f"{CONVEX_URL}/api/mutation"


def fetch_all_grants():
    """Fetch all grants from Convex."""
    payload = json.dumps({"path": "grants:getAllGrants", "args": {}})
    req = urllib.request.Request(
        QUERY_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    if result.get("status") == "success":
        return result["value"]
    # Some Convex responses return the value directly
    if "value" in result:
        return result["value"]
    raise RuntimeError(f"Failed to fetch grants: {result}")


def delete_grant(grant_id):
    """Delete a grant by Convex ID."""
    payload = json.dumps({
        "path": "adminGrants:deleteGrant",
        "args": {"id": grant_id},
    })
    req = urllib.request.Request(
        MUTATION_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        return result.get("status") == "success" or "value" in result
    except Exception as e:
        print(f"  ERROR deleting {grant_id}: {e}")
        return False


def main():
    print("=" * 60)
    print("DUPLICATE CLEANUP — InclusiFund Convex Database")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. Fetch all grants
    print("\nFetching all grants from Convex...")
    grants = fetch_all_grants()
    print(f"  Total records: {len(grants)}")

    # 2. Group by normalised name (lowercase, stripped)
    name_groups = defaultdict(list)
    for g in grants:
        key = g.get("name", "").strip().lower()
        name_groups[key].append(g)

    # 3. Find groups with more than one record
    duplicates = {k: v for k, v in name_groups.items() if len(v) > 1}

    if not duplicates:
        print("\nNo duplicates found. Database is clean.")
        return 0

    print(f"\nFound {len(duplicates)} duplicate groups:\n")

    to_delete = []
    for name_key, records in sorted(duplicates.items()):
        # Sort by createdAt descending — keep the newest
        records_sorted = sorted(
            records,
            key=lambda r: r.get("createdAt", r.get("_creationTime", 0)),
            reverse=True,
        )
        keeper = records_sorted[0]
        remove = records_sorted[1:]
        to_delete.extend(remove)

        print(f"  \"{records_sorted[0].get('name', name_key)}\" — {len(records)} copies")
        print(f"    KEEP:   {keeper['_id']} (created {keeper.get('createdAt', keeper.get('_creationTime', '?'))})")
        for r in remove:
            print(f"    DELETE: {r['_id']} (created {r.get('createdAt', r.get('_creationTime', '?'))})")

    # 4. Delete duplicates
    print(f"\n{'=' * 60}")
    print(f"Deleting {len(to_delete)} duplicate records...")
    print("=" * 60)

    success = 0
    fail = 0
    for r in to_delete:
        ok = delete_grant(r["_id"])
        status_str = "OK" if ok else "FAIL"
        print(f"  [{status_str}] {r.get('name', '?')} ({r['_id']})")
        if ok:
            success += 1
        else:
            fail += 1

    # 5. Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total records before: {len(grants)}")
    print(f"  Duplicate groups:     {len(duplicates)}")
    print(f"  Records deleted:      {success} success, {fail} failed")
    print(f"  Records remaining:    {len(grants) - success}")

    return fail


if __name__ == "__main__":
    sys.exit(main())
