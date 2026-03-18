#!/usr/bin/env python3
"""
Push researched UK accelerators and competition/challenge fund opportunities to Convex.
Also saves to the Vault JSON archive.

Research date: 2026-03-18
"""

import urllib.request
import json
import os
import sys
from datetime import datetime

CONVEX_URL = "https://terrific-bloodhound-927.convex.cloud/api/mutation"

VAULT_PATH = "/Users/royalreece/Projects/AntiGravity/Inclusi-funding Vault/InclusiFund-Vault/Research/convex-grants-db/accelerators_and_competitions_2026.json"

# ─── ACCELERATORS & INCUBATORS ───────────────────────────────────────

accelerators = [
    {
        "name": "UnLtd Starting Up Award",
        "opportunityType": "accelerator",
        "funder": "UnLtd",
        "description": "Funding and 12 months mentoring for social entrepreneurs at idea or early stage. At least 50% of awards support disabled and/or Black, Asian or minority ethnic entrepreneurs.",
        "amountMin": 500,
        "amountMax": 8000,
        "deadline": "Rolling (limited to 650 per round)",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Community Development", "Innovation"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Innovation"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": False,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://unltd.org.uk/awards/",
        "eligibility": "Social entrepreneurs with right to live and work in UK, idea or early stage"
    },
    {
        "name": "UnLtd Scaling Up Award",
        "opportunityType": "accelerator",
        "funder": "UnLtd",
        "description": "Funding plus 12 months tailored mentoring for social entrepreneurs ready to scale their existing venture. Covers wages and living costs.",
        "amountMin": 8000,
        "amountMax": 18000,
        "deadline": "Rolling (limited to 650 per round)",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Community Development", "Innovation"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Innovation"],
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 3,
        "website": "https://unltd.org.uk/awards/",
        "eligibility": "Existing social ventures ready to scale, right to live and work in UK"
    },
    {
        "name": "CVC DIF-Allia Accelerator Challenge",
        "opportunityType": "accelerator",
        "funder": "CVC / DIF / Allia",
        "description": "Six-month accelerator for UK-based impact ventures with proven concept and early traction. Culminates in Final Pitch Day with up to 50k in prize funding for top performers.",
        "amountMin": 0,
        "amountMax": 50000,
        "deadline": "2026-04-30",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Innovation", "Environment"],
        "eligibleSectors": ["Social Enterprise", "Innovation", "Environment"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://ukbaa.org.uk/blog/2026/02/23/applications-open-for-the-fourth-year-of-the-cvc-dif-allia-accelerator-challenge/",
        "eligibility": "UK-based impact ventures with proven concept and early traction, ideally revenue-generating or raising seed round"
    },
    {
        "name": "Growth Accelerator for Social Entrepreneurs (Leicester)",
        "opportunityType": "accelerator",
        "funder": "University of Leicester / Leicester City Council",
        "description": "Fully-funded programme (worth 5,700) for social enterprises. Covers business growth, strategy, and social impact measurement. No charge to participants.",
        "amountMin": 0,
        "amountMax": 5700,
        "deadline": "2026-03-31",
        "geographicFocus": "East Midlands",
        "regions": ["East Midlands"],
        "sectors": ["Social Enterprise", "Community Development", "Education"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Education"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://le.ac.uk/school-of-business/working-with-business/growth-accelerator-for-social-entrepreneurs",
        "eligibility": "Social enterprises in Leicester/East Midlands area"
    },
    {
        "name": "SSE London Growth & Resilience Programme",
        "opportunityType": "accelerator",
        "funder": "School for Social Entrepreneurs",
        "description": "18-month programme with Set Up Grant (4-7k) and Match Trading Grant (up to 12k matching trading income increases). 60 places across 3 cohorts, April 2026 to September 2027.",
        "amountMin": 4000,
        "amountMax": 19000,
        "deadline": "2026-04-15",
        "geographicFocus": "London",
        "regions": ["London"],
        "sectors": ["Social Enterprise", "Community Development", "Financial Inclusion"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Financial Inclusion"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://www.the-sse.org/programme/london-growth-and-resilience-programme/",
        "eligibility": "London-based organisations with little or no trading history wanting to build trading income"
    },
    {
        "name": "SSE Southwark Trade Up Programme 2026",
        "opportunityType": "accelerator",
        "funder": "School for Social Entrepreneurs / Southwark LAP",
        "description": "Place-based programme for social enterprises in Southwark. Learning sessions, grants, and trading support from June 2026 to March 2027.",
        "amountMin": 0,
        "amountMax": 12000,
        "deadline": "2026-05-31",
        "geographicFocus": "London (Southwark)",
        "regions": ["London"],
        "sectors": ["Social Enterprise", "Community Development"],
        "eligibleSectors": ["Social Enterprise", "Community Development"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://www.the-sse.org/programme/southwarklap2026/",
        "eligibility": "Social enterprises based in or serving London Borough of Southwark"
    },
    {
        "name": "Hatch Enterprise Accelerator",
        "opportunityType": "accelerator",
        "funder": "Hatch Enterprise",
        "description": "Growth programme for established social businesses. 12+ hours peer learning, coaching, expert sessions on strategy, PR, branding, sales, funding, and pitching. Targeted cohorts for women and impact founders.",
        "amountMin": 0,
        "amountMax": 0,
        "deadline": "Rolling",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Community Development", "Innovation"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Innovation"],
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 2,
        "website": "https://hatchenterprise.org/our-programmes/join-the-accelerator/",
        "eligibility": "Established businesses with annual revenue over 30k and at least one paid staff member"
    },
    {
        "name": "Hatch Enterprise Incubator",
        "opportunityType": "accelerator",
        "funder": "Hatch Enterprise",
        "description": "Support programme for early-stage social entrepreneurs. Workshops, mentoring, and community for founders from underrepresented backgrounds building purpose-driven businesses.",
        "amountMin": 0,
        "amountMax": 0,
        "deadline": "Rolling",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Community Development", "Innovation"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Innovation"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": False,
        "supportsScale": False,
        "applicationDifficulty": 1,
        "website": "https://hatchenterprise.org/our-programmes/join-the-incubator/",
        "eligibility": "Early-stage social entrepreneurs, especially from underrepresented backgrounds"
    },
    {
        "name": "Bethnal Green Ventures Tech for Good (Autumn 2026)",
        "opportunityType": "accelerator",
        "funder": "Bethnal Green Ventures",
        "description": "Europe's leading tech-for-good accelerator. 60k investment plus 6 weeks intensive learning for prototype-stage ventures using technology to address social and environmental issues.",
        "amountMin": 60000,
        "amountMax": 60000,
        "deadline": "2026-07-31",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide", "London"],
        "sectors": ["Technology", "Digital Health", "Education", "Environment", "Innovation"],
        "eligibleSectors": ["Technology", "Digital Health", "Education", "Environment", "Innovation"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": False,
        "supportsScale": False,
        "applicationDifficulty": 4,
        "website": "https://www.bethnalgreenventures.com/apply",
        "eligibility": "UK-incorporated ventures at prototype stage using tech for social/environmental good. 7% equity taken."
    },
    {
        "name": "100x Impact Accelerator 2026-2027 (LSE)",
        "opportunityType": "accelerator",
        "funder": "London School of Economics / 100x Impact",
        "description": "Global impact accelerator based at LSE offering 150k unrestricted grant funding plus catalytic capital. For social ventures addressing climate, healthcare, inequality, education, democracy.",
        "amountMin": 150000,
        "amountMax": 150000,
        "deadline": "2026-06-30",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Healthcare", "Education", "Environment", "Social Enterprise", "Innovation"],
        "eligibleSectors": ["Healthcare", "Education", "Environment", "Social Enterprise", "Innovation"],
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 5,
        "website": "https://www.100ximpact.org/",
        "eligibility": "For-profit or non-profit social ventures with credible route to systems-level change. Global eligibility."
    },
    {
        "name": "NTU Social Enterprise Accelerator",
        "opportunityType": "accelerator",
        "funder": "Nottingham Trent University / UKSPF",
        "description": "Comprehensive support package for new or growing VCSE organisations. Specialised training, business diagnostics, organisational development, and access to funding. Funded by UK Shared Prosperity Fund.",
        "amountMin": 0,
        "amountMax": 5000,
        "deadline": "Rolling",
        "geographicFocus": "East Midlands",
        "regions": ["East Midlands"],
        "sectors": ["Social Enterprise", "Community Development", "Education"],
        "eligibleSectors": ["Social Enterprise", "Community Development", "Education"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://www.ntu.ac.uk/business-and-employers/financial-and-funded-support/social-enterprise-accelerator",
        "eligibility": "VCSEs in Nottinghamshire/East Midlands area"
    },
    {
        "name": "CISL Canopy Sustainability Accelerator",
        "opportunityType": "accelerator",
        "funder": "Cambridge Institute for Sustainability Leadership / BSI",
        "description": "Accelerator for early-stage sustainability startups. February to June 2026 programme with expert mentoring, online and in-person sessions in Cambridge and London.",
        "amountMin": 0,
        "amountMax": 0,
        "deadline": "2026-04-30",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Environment", "Innovation", "Technology"],
        "eligibleSectors": ["Environment", "Innovation", "Technology"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": False,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://www.cisl.cam.ac.uk/innovation/cisl-canopy-and-bsis-accelerator-programme-trust-sustainability",
        "eligibility": "Early-stage sustainability startups"
    },
]

# ─── COMPETITIONS & CHALLENGE FUNDS ──────────────────────────────────

competitions = [
    {
        "name": "Cambridge Social Innovation Prize 2026",
        "opportunityType": "competition",
        "funder": "Cambridge Centre for Social Innovation / Trinity Hall",
        "description": "Prize celebrating extraordinary social innovators creating impact through business across the UK. Up to 4 winners receive 10k each plus skills development, resources and networks.",
        "amountMin": 10000,
        "amountMax": 10000,
        "deadline": "2026-04-17",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Innovation", "Community Development"],
        "eligibleSectors": ["Social Enterprise", "Innovation", "Community Development"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://www.jbs.cam.ac.uk/centres/social-innovation/cambridge-social-innovation-prize/",
        "eligibility": "UK social innovators creating social impact through business"
    },
    {
        "name": "Stephen Lloyd Awards 2026",
        "opportunityType": "competition",
        "funder": "Stephen Lloyd Awards / Bates Wells",
        "description": "Awards for innovative early-stage ideas addressing social or environmental challenges. Winners receive 25k plus expert guidance and pro bono support. Up to 10 shortlisted receive 2.5k development grants.",
        "amountMin": 2500,
        "amountMax": 25000,
        "deadline": "2026-04-08",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Social Enterprise", "Innovation", "Environment", "Community Development"],
        "eligibleSectors": ["Social Enterprise", "Innovation", "Environment", "Community Development"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": False,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://www.stephenlloydawards.org/",
        "eligibility": "UK charities, non-profits, social enterprises, or UK residents setting up eligible entity"
    },
    {
        "name": "Go! London Open Innovation Challenge - Sport for Climate Action",
        "opportunityType": "competition",
        "funder": "Go! London / Mayor of London / Sport England",
        "description": "Challenge fund for organisations using sport and physical activity to drive climate action with young people in London. Up to 100k per project to test and scale solutions.",
        "amountMin": 0,
        "amountMax": 100000,
        "deadline": "2026-04-30",
        "geographicFocus": "London",
        "regions": ["London"],
        "sectors": ["Sport", "Young People", "Environment", "Community Development"],
        "eligibleSectors": ["Sport", "Young People", "Environment", "Community Development"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://golondon.org.uk/open-innovation-challenges/",
        "eligibility": "Non-profit lead applicant, UK registered, London-based address. For-profits can be partners."
    },
    {
        "name": "Go! London Open Innovation Challenge - Reimagining Spaces",
        "opportunityType": "competition",
        "funder": "Go! London / Mayor of London / Sport England",
        "description": "Challenge fund for solutions increasing availability of safe, inclusive spaces for sport and physical activity for young people in London. Up to 100k to test and scale.",
        "amountMin": 0,
        "amountMax": 100000,
        "deadline": "2026-04-30",
        "geographicFocus": "London",
        "regions": ["London"],
        "sectors": ["Sport", "Young People", "Community Development", "Housing"],
        "eligibleSectors": ["Sport", "Young People", "Community Development", "Housing"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://golondon.org.uk/open-innovation-challenges/",
        "eligibility": "Non-profit lead applicant, UK registered, London-based address"
    },
    {
        "name": "BFI National Lottery Creative Challenge Fund (Round 2)",
        "opportunityType": "competition",
        "funder": "BFI / National Lottery",
        "description": "Fund for UK screen organisations to create targeted project development programmes for features or immersive projects. 12-150k per programme for labs focused on producers, filmmakers, genre projects.",
        "amountMin": 12000,
        "amountMax": 150000,
        "deadline": "2026-09-09",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Film", "Creative Industries", "Arts", "Creative Tech"],
        "eligibleSectors": ["Film", "Creative Industries", "Arts", "Creative Tech"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 4,
        "website": "https://www.bfi.org.uk/get-funding-support/create-films-tv-or-new-formats-storytelling/bfi-national-lottery-creative-challenge-fund",
        "eligibility": "UK screen organisations delivering development programmes for fiction/documentary features or immersive film"
    },
    {
        "name": "Ofwat Water Discovery Challenge 2",
        "opportunityType": "competition",
        "funder": "Ofwat / Water Innovation Fund",
        "description": "Innovation challenge for fresh thinking from outside the water sector. 20 finalists get 100k seed funding plus mentoring; 10 winners get up to 550k. Total pot approx 7.5m.",
        "amountMin": 100000,
        "amountMax": 550000,
        "deadline": "2026-04-08",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Environment", "Innovation", "Technology"],
        "eligibleSectors": ["Environment", "Innovation", "Technology"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://waterinnovation.challenges.org/discovery2/",
        "eligibility": "UK registered entities from any sector. Designed for innovators outside the water industry."
    },
    {
        "name": "MSDUK Innovation Challenge 2026",
        "opportunityType": "competition",
        "funder": "MSDUK",
        "description": "Innovation competition for minority-led businesses. Finalists present at Finals in September 2026 in London. Winner receives 20k cash prize, 3 years free MSDUK membership plus mentorship.",
        "amountMin": 0,
        "amountMax": 20000,
        "deadline": "2026-06-30",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Innovation", "Technology", "Social Enterprise"],
        "eligibleSectors": ["Innovation", "Technology", "Social Enterprise"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 3,
        "website": "https://www.msduk.org.uk/programme/msduk-innovation-challenge/",
        "eligibility": "Minority-led businesses in the UK"
    },
    {
        "name": "Cambridge Climate Challenge 2026",
        "opportunityType": "competition",
        "funder": "Cambridge Zero / Carbon13 / King's Entrepreneurship Lab",
        "description": "Two-track climate innovation competition. Track 1 (new concepts): 1.5k winner, 500 runners-up. Track 2 (early ventures): 5k winner plus Carbon13 programme, 2k runners-up. Free workshops and mentoring.",
        "amountMin": 500,
        "amountMax": 5000,
        "deadline": "2026-05-01",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Environment", "Innovation", "Technology"],
        "eligibleSectors": ["Environment", "Innovation", "Technology"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": False,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://www.zero.cam.ac.uk/node/544",
        "eligibility": "Open to innovators with climate solutions. Track 1 for new concepts, Track 2 for early-stage ventures."
    },
    {
        "name": "Innovate UK Innovation Loans Round 26",
        "opportunityType": "competition",
        "funder": "Innovate UK",
        "description": "Innovation loans of 100k to 5m for close-to-market innovative projects with strong commercial potential. For UK registered SMEs with projects that drive economic and societal benefit.",
        "amountMin": 100000,
        "amountMax": 5000000,
        "deadline": "2026-04-29",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Innovation", "Technology", "Healthcare", "Environment"],
        "eligibleSectors": ["Innovation", "Technology", "Healthcare", "Environment"],
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://apply-for-innovation-funding.service.gov.uk/competition/search",
        "eligibility": "UK registered micro, small or medium sized enterprises (SMEs)"
    },
    {
        "name": "Energy Catalyst Round 11 - Early Stage",
        "opportunityType": "competition",
        "funder": "Innovate UK / UKRI",
        "description": "Funding for feasibility studies creating new or improved clean energy access in developing countries. 50-300k total costs, up to 70% funded. Part of International Science Partnerships Fund.",
        "amountMin": 50000,
        "amountMax": 300000,
        "deadline": "2026-03-25",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Environment", "Innovation", "Technology"],
        "eligibleSectors": ["Environment", "Innovation", "Technology"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 4,
        "website": "https://apply-for-innovation-funding.service.gov.uk/competition/2362/overview/640b2f4e-8571-4aef-9e2a-67e35db3db77",
        "eligibility": "UK businesses/organisations with clean energy innovation for ODA-eligible countries"
    },
    {
        "name": "UKRI Creative Industries Clusters Programme",
        "opportunityType": "competition",
        "funder": "UKRI",
        "description": "27m funding round for regions to bid for creative industries cluster development. Part of 369m UKRI investment in creative industries. Supports innovative creative businesses and regional growth.",
        "amountMin": 500000,
        "amountMax": 5000000,
        "deadline": "2026-06-30",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Creative Industries", "Arts", "Creative Tech", "Innovation"],
        "eligibleSectors": ["Creative Industries", "Arts", "Creative Tech", "Innovation"],
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 5,
        "website": "https://creativeindustriesclusters.com/",
        "eligibility": "Regional partnerships and creative industry clusters"
    },
    {
        "name": "Innovate UK Smart Grants March 2026",
        "opportunityType": "competition",
        "funder": "Innovate UK",
        "description": "Up to 25m for game-changing, commercially viable R&D projects. Successful applicants can request 100k to 2m in funding. Open to disruptive innovations across all sectors.",
        "amountMin": 100000,
        "amountMax": 2000000,
        "deadline": "2026-04-30",
        "geographicFocus": "UK-wide",
        "regions": ["UK-wide"],
        "sectors": ["Innovation", "Technology", "Healthcare", "Environment", "Creative Tech"],
        "eligibleSectors": ["Innovation", "Technology", "Healthcare", "Environment", "Creative Tech"],
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://apply-for-innovation-funding.service.gov.uk/competition/search",
        "eligibility": "UK registered businesses with game-changing R&D innovation"
    },
]

# ─── COMBINE ALL ─────────────────────────────────────────────────────

all_opportunities = accelerators + competitions

print(f"\n{'='*60}")
print(f"  UK Accelerators & Competitions Push to Convex")
print(f"  Research date: 2026-03-18")
print(f"{'='*60}")
print(f"\n  Accelerators: {len(accelerators)}")
print(f"  Competitions: {len(competitions)}")
print(f"  Total:        {len(all_opportunities)}")
print(f"{'='*60}\n")

# ─── SAVE TO VAULT ───────────────────────────────────────────────────

os.makedirs(os.path.dirname(VAULT_PATH), exist_ok=True)
with open(VAULT_PATH, "w") as f:
    json.dump(all_opportunities, f, indent=2)
print(f"[SAVED] {len(all_opportunities)} opportunities to Vault JSON")
print(f"  Path: {VAULT_PATH}\n")

# ─── PUSH TO CONVEX ─────────────────────────────────────────────────

success_count = 0
fail_count = 0

for opp in all_opportunities:
    # Build Convex-compatible payload matching adminGrants:addGrant schema exactly
    grant_data = {
        "name": opp["name"],
        "funder": opp["funder"],
        "description": opp["description"],
        "minAmount": opp["amountMin"],
        "maxAmount": opp["amountMax"],
        "deadline": opp["deadline"],
        "status": opp["status"],
        "sectors": opp["sectors"],
        "regions": opp["regions"],
        "applicationDifficulty": opp["applicationDifficulty"],
        "supportsStartup": opp["supportsStartup"],
        "supportsGrowth": opp["supportsGrowth"],
        "supportsScale": opp["supportsScale"],
        "website": opp["website"],
        "opportunityType": opp.get("opportunityType", "grant"),
        "eligibility": opp.get("eligibility", ""),
    }

    payload = json.dumps({
        "path": "adminGrants:addGrant",
        "args": grant_data,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            CONVEX_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        if result.get("status") == "success" or "value" in result:
            success_count += 1
            print(f"  [OK]   {opp['name']}")
        else:
            fail_count += 1
            print(f"  [FAIL] {opp['name']}: {result}")
    except Exception as e:
        fail_count += 1
        print(f"  [FAIL] {opp['name']}: {e}")

print(f"\n{'='*60}")
print(f"  RESULTS")
print(f"{'='*60}")
print(f"  Pushed successfully: {success_count}/{len(all_opportunities)}")
print(f"  Failed:             {fail_count}/{len(all_opportunities)}")
print(f"  Saved to Vault:     {VAULT_PATH}")
print(f"{'='*60}\n")

# ─── SUMMARY TABLE ───────────────────────────────────────────────────

print("ACCELERATORS:")
print(f"{'Name':<55} {'Funder':<30} {'Amount':<15} {'Deadline':<12}")
print("-" * 112)
for a in accelerators:
    amt = f"{a['amountMin']:,}-{a['amountMax']:,}" if a['amountMax'] > 0 else "Non-financial"
    print(f"{a['name'][:54]:<55} {a['funder'][:29]:<30} {amt:<15} {a['deadline'][:11]:<12}")

print(f"\nCOMPETITIONS & CHALLENGE FUNDS:")
print(f"{'Name':<55} {'Funder':<30} {'Amount':<15} {'Deadline':<12}")
print("-" * 112)
for c in competitions:
    amt = f"{c['amountMin']:,}-{c['amountMax']:,}" if c['amountMax'] > 0 else "Non-financial"
    print(f"{c['name'][:54]:<55} {c['funder'][:29]:<30} {amt:<15} {c['deadline'][:11]:<12}")
