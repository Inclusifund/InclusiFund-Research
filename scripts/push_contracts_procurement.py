#!/usr/bin/env python3
"""
Push UK contracts and procurement opportunities to Convex.
Researched 2026-03-18 from Find a Tender, Contracts Finder, Crown Commercial Service.
"""

import urllib.request
import json
import os
import sys
from datetime import datetime

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud/api/mutation"

# ─── CONTRACTS ────────────────────────────────────────────────────────────────

contracts = [
    {
        "name": "Children & Young People Community Health and Wellbeing Services",
        "funder": "NHS England",
        "minAmount": 500000,
        "maxAmount": 5000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Healthcare", "Young People", "Mental Health", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/017943-2026",
        "description": "NHS contract for ongoing provision of children's community health and wellbeing services. 2-year contract with 1-year extension option. Open to CICs and social enterprises with healthcare delivery track record."
    },
    {
        "name": "Mental Health Community Support Services",
        "funder": "NHS Integrated Care Board",
        "minAmount": 200000,
        "maxAmount": 1400000,
        "deadline": "2026-04-01",
        "status": "Open",
        "sectors": ["Mental Health", "Healthcare", "Community Development", "Employment"],
        "regions": ["North West England"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/001213-2026",
        "description": "Contract for mental health community support helping people regain skills to maintain independence and gain employment. 5-year contract from April 2026 to March 2031."
    },
    {
        "name": "South West London Mental Health Support Teams",
        "funder": "NHS South West London ICB",
        "minAmount": 300000,
        "maxAmount": 2000000,
        "deadline": "2026-06-30",
        "status": "Open",
        "sectors": ["Mental Health", "Young People", "Education", "Healthcare"],
        "regions": ["London"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/020853-2026",
        "description": "Contract to provide Mental Health Support Teams working with schools and colleges across South West London, enabling children and young people to access mental health support and remain in education."
    },
    {
        "name": "Mental Health Prevention Services",
        "funder": "Local Authority / NHS Partnership",
        "minAmount": 100000,
        "maxAmount": 800000,
        "deadline": "2026-05-31",
        "status": "Open",
        "sectors": ["Mental Health", "Healthcare", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/000021-2026",
        "description": "Contract for delivery of preventive mental health services in the community. Focused on early intervention and reducing demand on acute services. Open to VCSE organisations."
    },
    {
        "name": "Care and Support at Home Services",
        "funder": "Local Authority Social Care",
        "minAmount": 100000,
        "maxAmount": 3000000,
        "deadline": "2026-06-01",
        "status": "Open",
        "sectors": ["Social Care", "Healthcare", "Disability", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/005549-2026",
        "description": "Contract for domiciliary care and support services helping older people and those with physical disabilities remain independent at home. Commencing June 2026."
    },
    {
        "name": "Step-Down Housing Service for Mental Health",
        "funder": "Hull Teaching Hospitals NHS Foundation Trust",
        "minAmount": 50000,
        "maxAmount": 500000,
        "deadline": "2026-04-30",
        "status": "Open",
        "sectors": ["Housing", "Mental Health", "Healthcare", "Social Care"],
        "regions": ["Yorkshire and Humber"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/009872-2026",
        "description": "NHS contract for step-down housing service facilitating safe discharge from acute mental health inpatient units. Includes tenancy support and accommodation access for service users."
    },
    {
        "name": "NextGen Youth Services",
        "funder": "Local Authority",
        "minAmount": 100000,
        "maxAmount": 1000000,
        "deadline": "2026-05-15",
        "status": "Open",
        "sectors": ["Young People", "Community Development", "Education", "Sport"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/012816-2026",
        "description": "Contract for delivery of next generation youth services including community-based activities, personal development programmes, and mentoring for young people."
    },
    {
        "name": "Connect to Work Supported Employment Service",
        "funder": "Dorset Council / DWP",
        "minAmount": 200000,
        "maxAmount": 1500000,
        "deadline": "2026-04-15",
        "status": "Open",
        "sectors": ["Employment", "Disability", "Mental Health", "Community Development"],
        "regions": ["South West England"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/017995-2026",
        "description": "Supported employment service in Dorset for people with disabilities and health conditions. Includes job coaching, employer engagement, and in-work support."
    },
    {
        "name": "Adult Learning Services - Multi-Lot Framework",
        "funder": "Local Authority Education",
        "minAmount": 50000,
        "maxAmount": 2000000,
        "deadline": "2026-12-01",
        "status": "Open",
        "sectors": ["Education", "Digital Health", "Creative Industries", "Employment"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/052450-2025",
        "description": "Framework for adult learning covering Digital Skills, Construction, Health & Social Care, Creative Industries, Employability Skills, and Hospitality. Multiple lots available to VCSE providers."
    },
    {
        "name": "VCSE Infrastructure Support - Ashford",
        "funder": "Ashford Borough Council",
        "minAmount": 25000,
        "maxAmount": 150000,
        "deadline": "2026-03-31",
        "status": "Open",
        "sectors": ["Social Enterprise", "Community Development", "Financial Inclusion"],
        "regions": ["South East England"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.contractsfinder.service.gov.uk/notice/14a81395-86a9-4ea6-8927-75445b7d7572",
        "description": "Contract for VCSE infrastructure support including capacity building, business advice, grant funding access assistance, and social enterprise development in Ashford borough."
    },
    {
        "name": "Short Breaks Leisure Activities for Children with Disabilities",
        "funder": "Central Bedfordshire Council",
        "minAmount": 50000,
        "maxAmount": 500000,
        "deadline": "2026-04-30",
        "status": "Open",
        "sectors": ["Disability", "Young People", "Sport", "Community Development"],
        "regions": ["East of England"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/006748-2026",
        "description": "Three-year contract for community-based leisure activities providing short breaks for children and young people with disabilities. Open to CICs, charities, and social enterprises."
    },
    {
        "name": "Homeless Family Rehousing Support",
        "funder": "Local Authority Housing",
        "minAmount": 100000,
        "maxAmount": 800000,
        "deadline": "2026-05-30",
        "status": "Open",
        "sectors": ["Housing", "Social Care", "Community Development", "Young People"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/014253-2026",
        "description": "Contract for support services helping homeless families access permanent housing. Includes tenancy readiness, resettlement support, and ongoing tenancy sustainment."
    },
    {
        "name": "Social Integration and Community Support Groups",
        "funder": "Local Authority",
        "minAmount": 10000,
        "maxAmount": 200000,
        "deadline": "2026-03-31",
        "status": "Open",
        "sectors": ["Community Development", "Mental Health", "Social Care"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.contractsfinder.service.gov.uk/Notice/4a9ff5f6-40bd-4446-8044-08f7fc2abbb2",
        "description": "Contract for delivery of social integration and community support groups reducing isolation and improving wellbeing. Open to VCSE organisations with below-threshold open procedure."
    },
    {
        "name": "Adult Social Care Transformation Delivery Partner",
        "funder": "Local Authority Social Care",
        "minAmount": 500000,
        "maxAmount": 5000000,
        "deadline": "2026-10-30",
        "status": "Open",
        "sectors": ["Social Care", "Healthcare", "Innovation", "Technology"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 5,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.contractsfinder.service.gov.uk/Notice/87659739-5dfd-4eba-9b5c-eb82c81900c0",
        "description": "Major transformation partner contract for adult social care. Includes working with VCSE sector, addressing demand complexity, and innovating delivery models."
    },
]

# ─── PROCUREMENT ──────────────────────────────────────────────────────────────

procurement = [
    {
        "name": "Digital Outcomes and Specialists 7 (DOS7)",
        "funder": "Crown Commercial Service",
        "minAmount": 0,
        "maxAmount": 10000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Technology", "Digital Health", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/017887-2026",
        "description": "CCS framework enabling public sector to procure digital, data, and technology services. Four lots: digital outcomes, capability/delivery partnerships, digital specialists, and user research. Open to SMEs and social enterprises."
    },
    {
        "name": "Construction Professional Services 2 Framework (2026-2030)",
        "funder": "Crown Commercial Service",
        "minAmount": 0,
        "maxAmount": 4200000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Housing", "Environment", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.crowncommercial.gov.uk/",
        "description": "Major CCS framework for construction professional services 2026-2030. Open to unlimited suppliers including SMEs, VCSEs, and social enterprises. Used by central government, local authorities, health, education, and housing."
    },
    {
        "name": "Technology Innovation Marketplace (DPS)",
        "funder": "Crown Commercial Service",
        "minAmount": 0,
        "maxAmount": 5000000,
        "deadline": "2029-02-15",
        "status": "Open",
        "sectors": ["Technology", "Innovation", "Digital Health"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/014316-2026",
        "description": "Dynamic Purchasing System for innovative technology products and services. Always-open DPS extended until Feb 2029. New suppliers can join at any time, making it accessible for emerging social enterprises."
    },
    {
        "name": "Sustainability Framework - Crown Estate",
        "funder": "The Crown Estate",
        "minAmount": 50000,
        "maxAmount": 2000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Environment", "Community Development", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/080802-2025",
        "description": "Multi-supplier framework for strategic sustainability advisory, social impact, climate and nature investment, and communications services. Five lots supporting net zero, nature recovery, and social impact."
    },
    {
        "name": "UK Leisure Framework 2026-2034",
        "funder": "Denbighshire Leisure Limited",
        "minAmount": 50000,
        "maxAmount": 5000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Sport", "Community Development", "Healthcare", "Young People"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/084356-2025",
        "description": "8-year framework for leisure, sport, recreation, wellbeing, health and cultural projects. Includes feasibility studies and project delivery. Open to social enterprises and CICs with sport/leisure expertise."
    },
    {
        "name": "Network of Employability Support and Training - Vocational Framework 2026-2030",
        "funder": "Department for Work and Pensions",
        "minAmount": 100000,
        "maxAmount": 3000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Employment", "Education", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/065363-2025",
        "description": "4-year vocational training framework supporting individuals to gain sector-specific skills and progress into higher-skilled roles. Flexible delivery (in-person and online). Open to VCSE training providers."
    },
    {
        "name": "L&Q Financial Inclusion Service",
        "funder": "L&Q Housing Association",
        "minAmount": 50000,
        "maxAmount": 500000,
        "deadline": "2026-06-30",
        "status": "Open",
        "sectors": ["Financial Inclusion", "Housing", "Social Care", "Community Development"],
        "regions": ["London", "South East England"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/054067-2025",
        "description": "Contract for financial inclusion services to social housing residents addressing debt, welfare benefits, and energy advice. Aimed at reducing eviction risk through specialist VCSE support."
    },
    {
        "name": "Great British Energy Advisory Services 2026-2029",
        "funder": "Great British Energy / DESNZ",
        "minAmount": 100000,
        "maxAmount": 5000000,
        "deadline": "2026-06-30",
        "status": "Open",
        "sectors": ["Environment", "Innovation", "Technology", "Community Development"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 4,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/079312-2025",
        "description": "Technical and professional advisory support to Great British Energy for the UK clean energy transition. Covers diverse technical, commercial, and organisational capabilities."
    },
    {
        "name": "ESG and Sustainability Reporting System",
        "funder": "Public Sector Body",
        "minAmount": 50000,
        "maxAmount": 500000,
        "deadline": "2026-04-30",
        "status": "Open",
        "sectors": ["Technology", "Environment", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/012719-2026",
        "description": "Procurement for ESG and sustainability system to support environmental, social, and governance reporting. Open to tech social enterprises with sustainability expertise."
    },
    {
        "name": "Net Zero Neighbourhood Community Energy Advice",
        "funder": "City of Wolverhampton Council",
        "minAmount": 50000,
        "maxAmount": 400000,
        "deadline": "2026-05-31",
        "status": "Open",
        "sectors": ["Environment", "Community Development", "Financial Inclusion", "Education"],
        "regions": ["West Midlands"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/006952-2026",
        "description": "Community energy efficiency advice and customer journey delivery partner for Net Zero Neighbourhood Project. Includes community engagement events and workshops. Well-suited to community-based social enterprises."
    },
    {
        "name": "Temporary Accommodation Solutions Framework",
        "funder": "Birmingham City Council",
        "minAmount": 100000,
        "maxAmount": 10000000,
        "deadline": "Rolling",
        "status": "Open",
        "sectors": ["Housing", "Social Care", "Community Development"],
        "regions": ["West Midlands"],
        "applicationDifficulty": 3,
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "website": "https://www.find-tender.service.gov.uk/Notice/003366-2026",
        "description": "Open framework for temporary accommodation solutions supporting the council's statutory duty to house vulnerable households. Includes private sector and registered provider partnerships."
    },
    {
        "name": "Start & Sustain Business Start-Up Support Service",
        "funder": "Local Authority / UKSPF",
        "minAmount": 50000,
        "maxAmount": 500000,
        "deadline": "2026-06-30",
        "status": "Open",
        "sectors": ["Social Enterprise", "Employment", "Community Development", "Innovation"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 3,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.find-tender.service.gov.uk/Notice/016588-2026",
        "description": "Procurement for VCSE business start-up support service. Providers deliver enterprise support, mentoring, and business diagnostics for new social enterprises and community organisations."
    },
]

# ─── PUSH TO CONVEX ──────────────────────────────────────────────────────────

def push_grant(grant_data):
    """Push a single grant/opportunity to Convex via the addGrant mutation."""
    payload = json.dumps({
        "path": "adminGrants:addGrant",
        "args": grant_data,
    })
    req = urllib.request.Request(
        CONVEX_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        status = result.get("status", "unknown")
        return status == "success" or "value" in result
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    all_opportunities = contracts + procurement

    # ── Save to JSON file ────────────────────────────────────────────────
    vault_path = (
        "/Users/royalreece/Projects/AntiGravity/Inclusi-funding Vault/"
        "InclusiFund-Vault/Research/convex-grants-db/"
        "contracts_and_procurement_2026.json"
    )
    os.makedirs(os.path.dirname(vault_path), exist_ok=True)
    with open(vault_path, "w") as f:
        json.dump(all_opportunities, f, indent=2)
    print(f"Saved {len(all_opportunities)} opportunities to:\n  {vault_path}\n")

    # Also save locally in the research repo
    local_path = (
        "/Users/royalreece/Projects/AntiGravity/InclusiFund-Research/"
        "Data/Quantum/contracts_and_procurement_2026.json"
    )
    with open(local_path, "w") as f:
        json.dump(all_opportunities, f, indent=2)
    print(f"Saved local copy to:\n  {local_path}\n")

    # ── Push to Convex ───────────────────────────────────────────────────
    print("=" * 60)
    print("PUSHING TO CONVEX")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    print(f"\n--- CONTRACTS ({len(contracts)} total) ---")
    for i, c in enumerate(contracts, 1):
        ok = push_grant(c)
        status_str = "OK" if ok else "FAIL"
        print(f"  [{status_str}] {i}. {c['name']}")
        if ok:
            success_count += 1
        else:
            fail_count += 1

    print(f"\n--- PROCUREMENT ({len(procurement)} total) ---")
    for i, p in enumerate(procurement, 1):
        ok = push_grant(p)
        status_str = "OK" if ok else "FAIL"
        print(f"  [{status_str}] {i}. {p['name']}")
        if ok:
            success_count += 1
        else:
            fail_count += 1

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total opportunities: {len(all_opportunities)}")
    print(f"    Contracts:   {len(contracts)}")
    print(f"    Procurement: {len(procurement)}")
    print(f"  Pushed to Convex:  {success_count} success, {fail_count} failed")
    print(f"  Saved to Vault:    {vault_path}")
    print(f"  Saved locally:     {local_path}")
    print(f"  Timestamp:         {datetime.now().isoformat()}")

    # Sector coverage
    all_sectors = set()
    for opp in all_opportunities:
        all_sectors.update(opp["sectors"])
    print(f"\n  Sector coverage ({len(all_sectors)} sectors):")
    for s in sorted(all_sectors):
        print(f"    - {s}")

    return success_count, fail_count


if __name__ == "__main__":
    s, f = main()
    sys.exit(0 if f == 0 else 1)
