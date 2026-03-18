#!/usr/bin/env python3
"""
Backfill eligibility and opportunityType for existing Convex grants.

For grants missing these fields:
- Generates a concise eligibility summary from description, sectors, and support flags
- Assigns opportunityType = "grant" (the default for records that predate the new types)
- Saves enrichment data to grants_eligibility_backfill.json
- Applies updates via the adminGrants:updateGrant mutation
"""

import urllib.request
import json
import sys
import os
import re
from datetime import datetime

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud"
QUERY_URL = f"{CONVEX_URL}/api/query"
MUTATION_URL = f"{CONVEX_URL}/api/mutation"

BACKFILL_PATH = (
    "/Users/royalreece/Projects/AntiGravity/InclusiFund-Research/"
    "Data/Quantum/grants_eligibility_backfill.json"
)


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
    if "value" in result:
        return result["value"]
    raise RuntimeError(f"Failed to fetch grants: {result}")


def generate_eligibility(grant):
    """Generate a concise eligibility summary from grant fields."""
    parts = []

    desc = grant.get("description", "")
    sectors = grant.get("sectors", [])
    regions = grant.get("regions", [])
    supports_startup = grant.get("supportsStartup", False)
    supports_growth = grant.get("supportsGrowth", False)
    supports_scale = grant.get("supportsScale", False)
    min_amt = grant.get("minAmount", 0)
    max_amt = grant.get("maxAmount", 0)

    # Stage eligibility
    stages = []
    if supports_startup:
        stages.append("startup")
    if supports_growth:
        stages.append("growth")
    if supports_scale:
        stages.append("scale-up")
    if stages:
        parts.append(f"Open to {', '.join(stages)} organisations")
    else:
        parts.append("Open to established organisations")

    # Extract eligibility hints from description
    desc_lower = desc.lower()

    # Organisation type hints
    org_types = []
    if "cic" in desc_lower or "community interest" in desc_lower:
        org_types.append("CICs")
    if "charit" in desc_lower:
        org_types.append("charities")
    if "social enterprise" in desc_lower or "social enterprises" in desc_lower:
        org_types.append("social enterprises")
    if "vcse" in desc_lower:
        org_types.append("VCSE organisations")
    if "sme" in desc_lower:
        org_types.append("SMEs")
    if "black" in desc_lower and ("led" in desc_lower or "found" in desc_lower):
        org_types.append("Black-led organisations")
    if "women" in desc_lower or "female" in desc_lower:
        org_types.append("women-led organisations")
    if "lgbtq" in desc_lower:
        org_types.append("LGBTQ+ organisations")
    if "disabled" in desc_lower or "disability" in desc_lower:
        org_types.append("disability-focused organisations")

    if org_types:
        parts.append(f"Eligible: {', '.join(org_types)}")

    # Sector focus
    if sectors:
        if len(sectors) <= 4:
            parts.append(f"Sectors: {', '.join(sectors)}")
        else:
            parts.append(f"Sectors: {', '.join(sectors[:3])} and {len(sectors) - 3} more")

    # Geographic focus
    if regions:
        region_str = ", ".join(regions)
        if region_str != "UK-wide":
            parts.append(f"Region: {region_str}")

    # Funding range hint
    if max_amt > 0:
        if min_amt > 0:
            parts.append(f"Funding: £{min_amt:,.0f}–£{max_amt:,.0f}")
        else:
            parts.append(f"Funding: up to £{max_amt:,.0f}")

    # Look for specific eligibility phrases in description
    for pattern in [
        r"(?:open to|eligible for|aimed at|designed for|targeting)\s+([^.]+)",
        r"(?:must be|applicants? (?:must|should))\s+([^.]+)",
    ]:
        match = re.search(pattern, desc_lower)
        if match:
            hint = match.group(1).strip()
            # Avoid duplicating what we already have
            if len(hint) < 100 and hint not in " ".join(parts).lower():
                parts.append(hint.capitalize())
                break

    return ". ".join(parts)


def determine_opportunity_type(grant):
    """Determine the opportunity type for a grant that's missing it."""
    # Existing grants without opportunityType are standard grants
    desc_lower = grant.get("description", "").lower()
    name_lower = grant.get("name", "").lower()

    # Check for contract indicators
    if any(kw in desc_lower for kw in ["contract for", "procurement", "tender", "framework"]):
        if "framework" in desc_lower or "framework" in name_lower:
            return "procurement"
        return "contract"

    # Check for accelerator indicators
    if any(kw in desc_lower for kw in ["accelerator", "incubat", "bootcamp"]):
        return "accelerator"

    # Check for competition indicators
    if any(kw in desc_lower for kw in ["competition", "challenge prize", "award"]):
        if "grant" not in desc_lower:
            return "competition"

    # Check for investment indicators
    if any(kw in desc_lower for kw in ["investment", "loan", "equity", "blended"]):
        return "social_investment"

    # Default for historical records
    return "grant"


def update_grant(grant_id, fields):
    """Update a grant via the adminGrants:updateGrant mutation."""
    payload = json.dumps({
        "path": "adminGrants:updateGrant",
        "args": {"id": grant_id, **fields},
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
        print(f"  ERROR updating {grant_id}: {e}")
        return False


def main():
    print("=" * 60)
    print("ELIGIBILITY BACKFILL — InclusiFund Convex Database")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # 1. Fetch all grants
    print("\nFetching all grants from Convex...")
    grants = fetch_all_grants()
    print(f"  Total records: {len(grants)}")

    # 2. Identify records missing eligibility or opportunityType
    needs_backfill = []
    for g in grants:
        missing_eligibility = not g.get("eligibility")
        missing_type = not g.get("opportunityType")
        if missing_eligibility or missing_type:
            needs_backfill.append(g)

    print(f"  Missing eligibility: {sum(1 for g in grants if not g.get('eligibility'))}")
    print(f"  Missing opportunityType: {sum(1 for g in grants if not g.get('opportunityType'))}")
    print(f"  Total needing backfill: {len(needs_backfill)}")

    if not needs_backfill:
        print("\nAll records already have eligibility and opportunityType. Nothing to do.")
        return 0

    # 3. Generate enrichment data
    print(f"\nGenerating enrichment data for {len(needs_backfill)} records...\n")
    enrichments = []
    for g in needs_backfill:
        entry = {
            "id": g["_id"],
            "name": g.get("name", "Unknown"),
            "funder": g.get("funder", "Unknown"),
        }
        updates = {}

        if not g.get("eligibility"):
            eligibility = generate_eligibility(g)
            entry["generated_eligibility"] = eligibility
            updates["eligibility"] = eligibility

        if not g.get("opportunityType"):
            opp_type = determine_opportunity_type(g)
            entry["generated_opportunityType"] = opp_type
            updates["opportunityType"] = opp_type

        entry["updates"] = updates
        enrichments.append(entry)

    # 4. Save backfill data
    os.makedirs(os.path.dirname(BACKFILL_PATH), exist_ok=True)
    with open(BACKFILL_PATH, "w") as f:
        json.dump(enrichments, f, indent=2)
    print(f"Saved enrichment data to:\n  {BACKFILL_PATH}\n")

    # 5. Report what would be updated
    print("=" * 60)
    print("ENRICHMENT REPORT")
    print("=" * 60)

    type_counts = {}
    for e in enrichments:
        opp_type = e.get("generated_opportunityType", e.get("updates", {}).get("opportunityType", "—"))
        type_counts[opp_type] = type_counts.get(opp_type, 0) + 1

    print(f"\n  Opportunity type breakdown:")
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")

    print(f"\n  Sample enrichments:")
    for e in enrichments[:5]:
        print(f"\n  {e['name']} ({e['funder']})")
        if "generated_eligibility" in e:
            elig = e["generated_eligibility"]
            if len(elig) > 120:
                elig = elig[:117] + "..."
            print(f"    Eligibility: {elig}")
        if "generated_opportunityType" in e:
            print(f"    Type: {e['generated_opportunityType']}")

    if len(enrichments) > 5:
        print(f"\n  ... and {len(enrichments) - 5} more (see JSON file for full list)")

    # 6. Apply updates via Convex
    print(f"\n{'=' * 60}")
    print(f"APPLYING UPDATES TO CONVEX ({len(enrichments)} records)...")
    print("=" * 60)

    success = 0
    fail = 0
    for e in enrichments:
        ok = update_grant(e["id"], e["updates"])
        status_str = "OK" if ok else "FAIL"
        print(f"  [{status_str}] {e['name']}")
        if ok:
            success += 1
        else:
            fail += 1

    # 7. Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total records in DB:    {len(grants)}")
    print(f"  Records backfilled:     {success} success, {fail} failed")
    print(f"  Backfill data saved:    {BACKFILL_PATH}")

    return fail


if __name__ == "__main__":
    sys.exit(main())
