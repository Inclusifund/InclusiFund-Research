#!/usr/bin/env python3
"""
Push CSR and Social Investment opportunities to Convex database.
Researched 2026-03-18 from live UK sources.

Usage:
    python3 scripts/push_csr_social_investment_2026.py          # Dry run
    python3 scripts/push_csr_social_investment_2026.py --execute # Push to Convex
"""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud"
QUERY_ENDPOINT = f"{CONVEX_URL}/api/query"
MUTATION_ENDPOINT = f"{CONVEX_URL}/api/mutation"

# Convex function paths (adminGrants for mutations, grants for queries)
QUERY_FN = "grants:getAllGrants"
MUTATION_FN = "adminGrants:addGrant"

SAVE_PATH = "/Users/royalreece/Projects/AntiGravity/Inclusi-funding Vault/InclusiFund-Vault/Research/csr-monitoring/csr_and_social_investment_2026.json"

# ─── CSR PROGRAMMES (10) ───

CSR_OPPORTUNITIES = [
    {
        "name": "Aviva Foundation Communities Fund",
        "funder": "Aviva Foundation",
        "minAmount": 1000,
        "maxAmount": 25000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Financial Inclusion", "Community Development", "Environment", "Wellbeing"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://communitiesfund.avivafoundation.org.uk/",
        "description": "Supports small, local organisations (income up to £1m) helping people take control of their financial wellbeing or protect places in a changing climate. Over £5m available in 2026.",
        "opportunityType": "csr",
        "eligibility": "Registered charity, CIC, or community group with annual income under £1m"
    },
    {
        "name": "Aviva Foundation Financial Futures Fund",
        "funder": "Aviva Foundation",
        "minAmount": 25000,
        "maxAmount": 200000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Financial Inclusion", "Social Care", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.aviva.com/sustainability/aviva-foundation/",
        "description": "Supports larger charities (income £1m+) delivering bold, long-term solutions to help people build financial resilience. Part of Aviva's refreshed 2026 grant-making programme.",
        "opportunityType": "csr",
        "eligibility": "Registered charity with annual income over £1m"
    },
    {
        "name": "Tesco Stronger Starts Community Grants",
        "funder": "Tesco / Groundwork",
        "minAmount": 500,
        "maxAmount": 1500,
        "deadline": "Rolling (quarterly rounds)",
        "status": "Open",
        "sectors": ["Young People", "Education", "Wellbeing", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 1,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://tescostrongerstarts.org.uk/",
        "description": "Grants of £500-£1,500 for schools, charities and not-for-profit organisations supporting children and young people. Projects voted on by customers via blue token scheme in local Tesco stores.",
        "opportunityType": "csr",
        "eligibility": "Registered charity, school, or not-for-profit organisation"
    },
    {
        "name": "Santander Foundation Financial & Digital Empowerment Fund",
        "funder": "Santander Foundation",
        "minAmount": 5000,
        "maxAmount": 10000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Financial Inclusion", "Digital Health", "Education", "Employment"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.santander.co.uk/about-santander/media-centre/press-releases/santander-foundation-launches-ps18million-fund",
        "description": "£1.8m fund supporting UK charities and CICs working to build people's digital and financial skills. Community Plus (up to £5k) and Learn & Grow (up to £10k) streams.",
        "opportunityType": "csr",
        "eligibility": "Registered charity or CIC"
    },
    {
        "name": "Lloyds Bank Foundation Racial Equity Grants",
        "funder": "Lloyds Bank Foundation",
        "minAmount": 10000,
        "maxAmount": 75000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community Development", "Social Care", "Education", "Employment"],
        "regions": ["England", "Wales"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.lloydsbankfoundation.org.uk/funding",
        "description": "Unrestricted grants for small charities and CICs led by and working with people who face inequity because of their race or ethnicity. Three-year funding plus tailored development support.",
        "opportunityType": "csr",
        "eligibility": "Registered charity with annual income £25k-£500k, operating in England/Wales"
    },
    {
        "name": "Garfield Weston Foundation Main Grants",
        "funder": "Garfield Weston Foundation",
        "minAmount": 1000,
        "maxAmount": 100000,
        "deadline": "Rolling (no deadlines)",
        "status": "Open",
        "sectors": ["Community Development", "Arts", "Education", "Environment", "Wellbeing", "Young People"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://garfieldweston.org/what-we-fund/",
        "description": "One of the UK's largest independent grant-makers, distributing around £100m annually across a wide range of charitable activities. No deadlines, trustees make decisions year-round.",
        "opportunityType": "csr",
        "eligibility": "Registered charity"
    },
    {
        "name": "Esmee Fairbairn Foundation Grants",
        "funder": "Esmee Fairbairn Foundation",
        "minAmount": 30000,
        "maxAmount": 500000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Arts", "Creative Industries", "Environment", "Social Enterprise", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://esmeefairbairn.org.uk/our-support/grants/",
        "description": "Unrestricted, core and project grants. Median grant £150k over 3 years. Focus on creative, fair and green futures. Minimum grant £30k.",
        "opportunityType": "csr",
        "eligibility": "Registered charity or CIC with established track record"
    },
    {
        "name": "Big Give Christmas Challenge 2026",
        "funder": "Big Give / Multiple Champions",
        "minAmount": 5000,
        "maxAmount": 50000,
        "deadline": "2026-05-11",
        "status": "Open",
        "sectors": ["Community Development", "Social Care", "Young People", "Wellbeing", "Education"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://biggive.org/charities/",
        "description": "UK's biggest match funding campaign. Champion funders double every public donation during campaign week (1-8 Dec 2026). Applications open 11 May. Charities must secure a Champion match funder.",
        "opportunityType": "csr",
        "eligibility": "UK registered charity with a Champion match funder"
    },
    {
        "name": "Nationwide Community Grants Programme",
        "funder": "Nationwide Building Society",
        "minAmount": 10000,
        "maxAmount": 60000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Housing", "Community Development", "Financial Inclusion"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://nationwidecommunitygrants.co.uk/",
        "description": "Grants of £10k-£60k over one or two years for housing-focused charities across the UK. Focus on access to decent affordable homes, community-led housing, and private rented sector improvements.",
        "opportunityType": "csr",
        "eligibility": "Registered charity focused on housing issues"
    },
    {
        "name": "Cadbury Foundation Community Grants",
        "funder": "Cadbury Foundation",
        "minAmount": 500,
        "maxAmount": 5000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community Development", "Young People", "Education", "Environment"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.cadbury.co.uk/about/impact/cadbury-foundation/",
        "description": "Grants supporting charitable work in the UK, with focus on community development, education, young people and the environment. Simple application process.",
        "opportunityType": "csr",
        "eligibility": "Registered charity"
    },
]

# ─── SOCIAL INVESTMENT PROGRAMMES (10) ───

SOCIAL_INVESTMENT_OPPORTUNITIES = [
    {
        "name": "CAF Venturesome Impact Fund",
        "funder": "Charities Aid Foundation",
        "minAmount": 50000,
        "maxAmount": 1000000,
        "deadline": "Rolling (evergreen fund)",
        "status": "Open",
        "sectors": ["Social Enterprise", "Community Development", "Healthcare", "Education"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.cafonline.org/services-for-charities/funding-for-charities/social-investment/venturesome-impact-fund",
        "description": "Unsecured loans £50k-£1m at 5.5% fixed interest over 3-10 years. For organisations with turnover under £500k, blended finance available: 70% loan / 30% grant. Evergreen fund, always open.",
        "opportunityType": "social_investment",
        "eligibility": "Charities, social enterprises and community groups in the UK"
    },
    {
        "name": "Social Investment Business - Community Enterprise Fund",
        "funder": "Social Investment Business",
        "minAmount": 5000,
        "maxAmount": 50000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community Development", "Social Enterprise", "Wellbeing", "Environment"],
        "regions": ["England", "Wales"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.sibgroup.org.uk/funds/community-enterprise-fund/",
        "description": "Blended loan and grant fund of up to £50k for community organisations transforming their local area. Available to charities and social enterprises in England and Wales.",
        "opportunityType": "social_investment",
        "eligibility": "Charities and social enterprises based in England and Wales"
    },
    {
        "name": "Social Investment Business - Community Builders Fund",
        "funder": "Social Investment Business",
        "minAmount": 100000,
        "maxAmount": 1500000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Community Development", "Housing", "Social Enterprise"],
        "regions": ["England", "Wales", "Scotland"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.sibgroup.org.uk/funds/community-builders-fund/",
        "description": "£17m fund providing loans of £100k-£1.5m for UK charities and social enterprises. Launched 2025, supporting organisations building community infrastructure and assets.",
        "opportunityType": "social_investment",
        "eligibility": "Charities and social enterprises in England, Wales and Scotland"
    },
    {
        "name": "Social Investment Business - Energy Resilience Fund",
        "funder": "Social Investment Business",
        "minAmount": 10000,
        "maxAmount": 200000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Environment", "Community Development", "Social Enterprise"],
        "regions": ["England", "Wales", "Scotland"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.sibgroup.org.uk/funding/",
        "description": "£15m blended package (40% grant, 60% loan) for charities and social enterprises to improve energy resilience. Retrofit, insulation, and renewable energy projects.",
        "opportunityType": "social_investment",
        "eligibility": "Charities and social enterprises in England, Wales and Scotland"
    },
    {
        "name": "Foundation Scotland Social Investment Fund",
        "funder": "Foundation Scotland",
        "minAmount": 10000,
        "maxAmount": 250000,
        "deadline": "Rolling (always open)",
        "status": "Open",
        "sectors": ["Social Enterprise", "Community Development", "Environment", "Wellbeing"],
        "regions": ["Scotland"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.foundationscotland.org.uk/apply-for-funding/funding-available/social-investment-fund",
        "description": "Blended grant and loan investment (up to 25% as grant). Investments of £10k-£250k for social enterprises, community organisations and charities across Scotland. Loans typically over 10 years.",
        "opportunityType": "social_investment",
        "eligibility": "Social enterprises, community organisations and charities operating in Scotland"
    },
    {
        "name": "Resonance Enterprise Investment Fund",
        "funder": "Resonance",
        "minAmount": 25000,
        "maxAmount": 500000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Social Enterprise", "Healthcare", "Wellbeing", "Environment", "Community Development"],
        "regions": ["England"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://resonance.ltd.uk/get-investment/enterprise-growth-funds/resonance-enterprise-investment-fund",
        "description": "£10m fund backing social enterprises tackling pressing challenges: health, wellbeing, economic inequality, low-carbon transition. Initial focus on South West, North West, West Midlands. B Corp certified investor.",
        "opportunityType": "social_investment",
        "eligibility": "Social enterprises in England, particularly South West, North West and West Midlands"
    },
    {
        "name": "Key Fund - Northern Impact Fund",
        "funder": "Key Fund",
        "minAmount": 5000,
        "maxAmount": 300000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Social Enterprise", "Community Development", "Employment", "Environment"],
        "regions": ["North East", "Yorkshire", "East Midlands", "West Midlands"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://thekeyfund.co.uk/",
        "description": "Flexible loans and grants for community and social enterprises. Northern Impact Fund offers 20% of loan value as grant. Energy funding stream offers up to 40% as grant. Investments from £5k-£300k.",
        "opportunityType": "social_investment",
        "eligibility": "Community and social enterprises operating in North of England and Midlands"
    },
    {
        "name": "NatWest Social & Community Capital",
        "funder": "NatWest",
        "minAmount": 10000,
        "maxAmount": 500000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Social Enterprise", "Community Development", "Housing", "Employment", "Wellbeing"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.natwest.com/business/loans-and-finance/social-and-community-capital.html",
        "description": "Loans and support for social enterprises, charities and community organisations. Part of NatWest's £10bn social housing funding ambition. Includes mentoring and business support alongside finance.",
        "opportunityType": "social_investment",
        "eligibility": "Social enterprises, charities and community organisations"
    },
    {
        "name": "UnLtd Social Entrepreneur Awards",
        "funder": "UnLtd",
        "minAmount": 500,
        "maxAmount": 18000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Social Enterprise", "Innovation", "Community Development", "Young People", "Wellbeing"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://unltd.org.uk/awards/",
        "description": "Starting Up and Scaling Up awards for social entrepreneurs aged 16+. Scaling Up offers £8k-£18k plus 12 months mentoring. At least 50% of awards support disabled and/or Black, Asian or minority ethnic entrepreneurs.",
        "opportunityType": "social_investment",
        "eligibility": "Social entrepreneurs aged 16+ based in the UK"
    },
    {
        "name": "Esmee Fairbairn Foundation Social Investment",
        "funder": "Esmee Fairbairn Foundation",
        "minAmount": 50000,
        "maxAmount": 1000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Social Enterprise", "Arts", "Creative Industries", "Environment", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://esmeefairbairn.org.uk/our-support/social-investment/",
        "description": "Social investment programme alongside grants, using repayable finance to achieve impact goals. Focus on creative, fair and green futures. For established organisations with social mission.",
        "opportunityType": "social_investment",
        "eligibility": "Established charities and social enterprises with clear social mission"
    },
]

ALL_OPPORTUNITIES = CSR_OPPORTUNITIES + SOCIAL_INVESTMENT_OPPORTUNITIES


def fetch_all_grants():
    """Fetch existing grants from Convex to check for duplicates."""
    payload = json.dumps({
        "path": QUERY_FN,
        "args": {},
    }).encode()
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
    """Add a single grant to Convex via adminGrants:addGrant mutation."""
    payload = json.dumps({
        "path": MUTATION_FN,
        "args": grant_data,
    }).encode("utf-8")
    req = urllib.request.Request(
        MUTATION_ENDPOINT, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    status = data.get("status", "unknown")
    if status != "success" and "value" not in data:
        raise RuntimeError(f"Add failed: {data.get('errorMessage', data)}")
    return data


def save_local(opportunities, path):
    """Save opportunities to local JSON file."""
    with open(path, "w") as f:
        json.dump(opportunities, f, indent=2, default=str)
    print(f"Saved {len(opportunities)} opportunities to {path}")


def main():
    execute = "--execute" in sys.argv

    # Save locally regardless of execute flag
    save_local(ALL_OPPORTUNITIES, SAVE_PATH)

    # Also save to Data/Quantum in the research repo
    repo_path = "/Users/royalreece/Projects/AntiGravity/InclusiFund-Research/Data/Quantum/csr_social_investment_2026.json"
    save_local(ALL_OPPORTUNITIES, repo_path)

    print(f"\n{'='*60}")
    print(f"CSR & Social Investment Opportunities - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*60}")
    print(f"\nCSR Programmes:            {len(CSR_OPPORTUNITIES)}")
    print(f"Social Investment:         {len(SOCIAL_INVESTMENT_OPPORTUNITIES)}")
    print(f"Total:                     {len(ALL_OPPORTUNITIES)}")

    # Print summary
    print(f"\n{'─'*60}")
    print("CSR PROGRAMMES:")
    print(f"{'─'*60}")
    for opp in CSR_OPPORTUNITIES:
        amt = f"£{opp['minAmount']:,.0f}-£{opp['maxAmount']:,.0f}"
        print(f"  {opp['name']}")
        print(f"    Funder: {opp['funder']} | Amount: {amt} | Deadline: {opp['deadline']}")

    print(f"\n{'─'*60}")
    print("SOCIAL INVESTMENT:")
    print(f"{'─'*60}")
    for opp in SOCIAL_INVESTMENT_OPPORTUNITIES:
        amt = f"£{opp['minAmount']:,.0f}-£{opp['maxAmount']:,.0f}"
        print(f"  {opp['name']}")
        print(f"    Funder: {opp['funder']} | Amount: {amt} | Deadline: {opp['deadline']}")

    if not execute:
        print(f"\n{'='*60}")
        print("DRY RUN — Add --execute to push to Convex")
        print(f"{'='*60}")
        return

    # Fetch existing for duplicate check
    print(f"\nFetching existing grants for duplicate check...")
    try:
        existing = fetch_all_grants()
        existing_names = {g.get("name", "").lower().strip() for g in existing}
        print(f"Found {len(existing)} existing grants")
    except Exception as e:
        print(f"Warning: Could not fetch existing grants: {e}")
        existing_names = set()

    # Push to Convex
    pushed = 0
    skipped = 0
    failed = 0

    for opp in ALL_OPPORTUNITIES:
        name_lower = opp["name"].lower().strip()
        if name_lower in existing_names:
            print(f"  SKIP (duplicate): {opp['name']}")
            skipped += 1
            continue

        # Build Convex-compatible payload (strict validator — only accepted fields)
        grant_data = {
            "name": opp["name"],
            "funder": opp["funder"],
            "minAmount": float(opp["minAmount"]),
            "maxAmount": float(opp["maxAmount"]),
            "deadline": opp["deadline"],
            "status": opp["status"],
            "sectors": opp["sectors"],
            "regions": opp["regions"],
            "applicationDifficulty": float(opp["applicationDifficulty"]),
            "supportsStartup": opp["supportsStartup"],
            "supportsGrowth": opp["supportsGrowth"],
            "supportsScale": opp["supportsScale"],
            "website": opp["website"],
            "description": opp["description"],
            "opportunityType": opp.get("opportunityType", "grant"),
            "eligibility": opp.get("eligibility", ""),
        }

        try:
            add_grant(grant_data)
            print(f"  PUSHED: {opp['name']}")
            pushed += 1
            time.sleep(0.3)  # Rate limit
        except Exception as e:
            print(f"  FAILED: {opp['name']} — {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {pushed} pushed, {skipped} skipped (duplicates), {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
