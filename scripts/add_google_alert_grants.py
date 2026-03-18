#!/usr/bin/env python3
"""
Add 22 new grants from Google Alerts (6-week compilation, March 2026)
to the live Convex database.

Usage:
    python3 scripts/add_google_alert_grants.py          # Dry run (default)
    python3 scripts/add_google_alert_grants.py --execute # Push to Convex
"""

import json
import sys
import time
import urllib.request
import urllib.error

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud"
QUERY_ENDPOINT = f"{CONVEX_URL}/api/query"
MUTATION_ENDPOINT = f"{CONVEX_URL}/api/mutation"

# ─── 22 New Grants from Google Alerts (March 2026) ───

NEW_GRANTS = [
    # ── URGENT: Closing March 2026 ──
    {
        "name": "Skipton Building Society Charitable Foundation",
        "funder": "Skipton Building Society",
        "minAmount": 0,
        "maxAmount": 5000,
        "deadline": "2026-03-31",
        "status": "Open",
        "sectors": ["Housing", "Financial wellbeing"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.skiptonbuildingsociety.co.uk/charitable-foundation",
        "description": "Supports UK-registered charities working on housing and financial wellbeing. Up to £5,000 per grant.",
    },

    # ── CLOSING EARLY APRIL ──
    {
        "name": "Community Grants Scheme - Buildings & Outdoor Spaces",
        "funder": "Community Grants Scheme",
        "minAmount": 10000,
        "maxAmount": 75000,
        "deadline": "2026-04-02",
        "status": "Open",
        "sectors": ["Community", "Built environment", "Green spaces"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk/guidance/community-grants-scheme",
        "description": "Funding for UK not-for-profit organisations, local authorities, and environmental organisations to improve community buildings and outdoor spaces. £10,000 to £75,000.",
    },
    {
        "name": "Robotics Adoption Hubs - Central Body Launch",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "2026-04-15",
        "status": "Open",
        "sectors": ["Technology", "Innovation", "Robotics"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "Innovate UK programme to establish robotics adoption infrastructure. For tech-focused organisations and innovation hubs.",
    },

    # ── MEDIUM TERM: Summer 2026 ──
    {
        "name": "Clean Maritime Technology Projects",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 121000000,
        "deadline": "2026-07-15",
        "status": "Open",
        "sectors": ["Maritime", "Clean tech", "Environment", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "£121 million fund for clean maritime technology innovation. Ideal for tech and environmental innovation organisations.",
    },

    # ── ROLLING/ONGOING PROGRAMMES ──
    {
        "name": "Lord-Lieutenant's Fund",
        "funder": "Lord-Lieutenant's Fund",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community", "Civic"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "UK-based projects. Applications now open with no stated deadline. Announced March 17, 2026.",
    },
    {
        "name": "Bright Futures Fund",
        "funder": "Bright Futures Fund",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Youth", "Education", "Carers"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Supports young carers managing responsibilities at home. UK-based organisations eligible. Announced March 12, 2026.",
    },
    {
        "name": "Grants for New Fine Arts Projects",
        "funder": "Arts Funding Body",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Arts", "Culture"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Funding for new fine arts projects. UK-based projects only. Arts and creative sector. Announced March 13, 2026.",
    },
    {
        "name": "One Stop Community Partnership Programme",
        "funder": "One Stop",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community", "Social impact"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Social impact funding delivered in collaboration with communities. Announced March 9, 2026.",
    },
    {
        "name": "Advanced Connectivity System Integration Projects",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Technology", "Connectivity", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "Innovate UK programme for advanced connectivity system integration. Tech and connectivity sector. Announced March 10, 2026.",
    },
    {
        "name": "Projects for Young People Programme",
        "funder": "Youth Funding Body",
        "minAmount": 0,
        "maxAmount": 15000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Youth", "Community"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Up to £15,000 for community youth programmes. UK community organisations eligible. Announced March 7, 2026.",
    },
    {
        "name": "Woodroffe Benton Foundation Small Grant Programme",
        "funder": "Woodroffe Benton Foundation",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["General", "Community"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "One-off small grants for UK organisations. Announced March 5, 2026.",
    },
    {
        "name": "Community Research Grant Program",
        "funder": "Community Research Fund",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Research", "Community", "Environment"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Supports projects creating positive social and environmental impact. UK-based. Announced March 3, 2026.",
    },
    {
        "name": "Habitat and Biodiversity Grant Scheme",
        "funder": "Environmental Fund",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Environment", "Biodiversity"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Funding for sustainable environmental projects focused on habitat and biodiversity. UK-based. Announced March 2, 2026.",
    },
    {
        "name": "UK Global Screen Fund: International Co-production",
        "funder": "UK Global Screen Fund",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Film", "Screen", "Creative industries"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.bfi.org.uk/uk-global-screen-fund",
        "description": "Grants for international co-production in film and media. Cannot exceed 50% of overall UK budget. Announced March 2, 2026.",
    },
    {
        "name": "Fat Beehive Foundation - Digital Presence Grants",
        "funder": "Fat Beehive Foundation",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Digital", "Charity infrastructure"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.fatbeehive.com/foundation",
        "description": "Supports small UK charities to build digital presence and online capability. Announced February 28, 2026.",
    },
    {
        "name": "Realisation Grants Programme",
        "funder": "Arts Funding Body",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Arts", "Culture"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Funding for arts and culture projects. UK organisations eligible. Announced February 25, 2026.",
    },
    {
        "name": "Community Development Grant - Small",
        "funder": "Community Development Fund",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.gov.uk",
        "description": "Small community development grants for UK organisations. Announced February 26, 2026.",
    },

    # ── STRATEGIC INNOVATE UK OPPORTUNITIES ──
    {
        "name": "Non-Animal Drug Testing Methods",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Life sciences", "Innovation", "Health tech"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "Innovate UK programme for non-animal drug testing methods innovation. Announced March 4, 2026.",
    },
    {
        "name": "Hemp Varieties for British Farming - Innovation Programme",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 0,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Agriculture", "Innovation", "Sustainability"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "Innovate UK programme for hemp varieties for British farming. Announced March 11, 2026.",
    },
    {
        "name": "Cybersecurity Startup Programme",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 10000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Cybersecurity", "Technology", "Startup"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "£10 million additional funding for cybersecurity startup programme. Announced February 25, 2026.",
    },
    {
        "name": "Whole-System AI Strategy",
        "funder": "Innovate UK",
        "minAmount": 0,
        "maxAmount": 1600000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["AI", "Technology", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.ukri.org/councils/innovate-uk/",
        "description": "£1.6 billion whole-system AI strategy by Innovate UK. Announced February 26, 2026.",
    },
]


def fetch_all_grants():
    """Fetch all existing grants from Convex."""
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


def add_grant(grant_data):
    """Add a single grant to Convex via addGrant mutation."""
    payload = json.dumps({
        "path": "grants:addGrant",
        "args": grant_data,
    }).encode()
    req = urllib.request.Request(
        MUTATION_ENDPOINT, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if data.get("status") != "success":
        raise RuntimeError(f"Add failed: {data.get('errorMessage', 'unknown')}")
    return data


def main():
    execute = "--execute" in sys.argv

    print("Fetching existing grants for duplicate check...")
    existing = fetch_all_grants()
    existing_names = {g.get("name", "").lower().strip() for g in existing}
    print(f"Found {len(existing)} existing grants\n")

    # Check for duplicates
    to_add = []
    skipped = []
    for grant in NEW_GRANTS:
        name_lower = grant["name"].lower().strip()
        if name_lower in existing_names:
            skipped.append(grant["name"])
        else:
            to_add.append(grant)

    if skipped:
        print(f"Skipping {len(skipped)} duplicates:")
        for name in skipped:
            print(f"  - {name}")
        print()

    print(f"{len(to_add)} new grants to add:\n")
    for grant in to_add:
        amount = ""
        if grant["maxAmount"] > 0:
            amount = f" (up to £{grant['maxAmount']:,.0f})"
        deadline = grant.get("deadline", "Rolling")
        print(f"  {grant['name']}{amount} — {deadline}")
        print(f"    Sectors: {', '.join(grant['sectors'])}")

    print()

    if not execute:
        print("--- DRY RUN ---")
        print("Run with --execute to push to Convex.")
        return

    print("Adding grants to Convex...\n")
    success = 0
    failed = 0
    for grant in to_add:
        try:
            add_grant(grant)
            print(f"  Added: {grant['name']}")
            success += 1
            time.sleep(0.2)  # Rate limit courtesy
        except Exception as e:
            print(f"  FAILED: {grant['name']} — {e}")
            failed += 1

    print(f"\nDone. {success} added, {failed} failed.")
    print(f"Total grants in database: {len(existing) + success}")


if __name__ == "__main__":
    main()
