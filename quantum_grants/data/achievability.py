"""
Achievability tips module — Royal's procurement playbook.

Rule-based tip generator, support flag extractor, and framing label logic
for CIC opportunity enrichment. Makes funding look winnable, not scary.
"""

from __future__ import annotations

from typing import Any


def generate_tips(record: dict[str, Any]) -> list[str]:
    """Rule-based tip generator using Royal's procurement playbook."""
    tips: list[str] = []
    otype = record.get("opportunityType", "grant").lower()
    amt = record.get("perAwardMax") or record.get("amountMax") or 0
    diff = record.get("applicationDifficulty", 3)
    funder = (record.get("funder") or "").lower()
    desc = (record.get("description") or "").lower()
    regions = record.get("regions") or []

    # --- Procurement playbook ---
    if otype == "procurement":
        tips.append(
            "Two routes: join a main contractor's supply chain, "
            "or build an alliance and bid as lead"
        )
        tips.append(
            "These award much higher than grants "
            "\u2014 solid yearly income if you build the relationship"
        )
        if any(k in funder for k in ["council", "authority", "nhs"]):
            tips.append(
                "Know someone in the council? "
                "Those relationships are your route in"
            )
        if any(k in desc for k in ["social", "health", "housing", "treasury"]):
            tips.append(
                "Know inside workers in social housing, treasury, or health? "
                "Those relationships are your edge"
            )
        if regions:
            region_str = regions[0] if isinstance(regions[0], str) else str(regions[0])
            tips.append(
                f"Local knowledge wins \u2014 if you're active in {region_str}, "
                "you already have an advantage"
            )

    # --- Contract scaling ---
    elif otype == "contract":
        tips.append(
            "Build your team, scale fractionally, "
            "deliver across multiple locations"
        )
        if amt > 500_000:
            tips.append(
                "Alliance opportunity \u2014 partner with charities, "
                "schools, and clinics in your area"
            )
        tips.append(
            "Solid yearly income if you build good relationships "
            "and bring the team"
        )

    # --- Accelerators ---
    elif otype == "accelerator":
        tips.append("Includes structured support and mentoring")
        if record.get("supportsStartup"):
            tips.append("Designed for early-stage organisations")

    # --- Competitions ---
    elif otype == "competition":
        tips.append("Innovation-focused \u2014 strong concept matters more than track record")
        if diff and diff >= 4:
            tips.append("Competitive process \u2014 budget time for a strong application")

    # --- CSR ---
    elif otype == "csr":
        tips.append("Corporate partner angle \u2014 align your pitch to their social value goals")

    # --- Social investment ---
    elif otype == "social_investment":
        tips.append("Blended funding \u2014 part grant, part loan. Understand the repayment terms")

    # --- Grant-specific (default) ---
    else:
        if amt and amt > 150_000:
            if "capital" in desc or "building" in desc or "refurb" in desc:
                tips.append("Capital funding \u2014 for buildings, equipment, or major refurbishment")
            elif "heritage" in desc:
                tips.append("Heritage funding \u2014 for cultural and historical projects")
            elif "core" in desc:
                tips.append("Core costs funding \u2014 covers salaries, rent, and running costs")

    # --- Universal tips ---
    if diff is not None and diff <= 2:
        tips.append("Lightweight application \u2014 worth a quick bid")
    if record.get("supportsStartup"):
        tips.append("New CICs welcome")

    return tips[:3]


def extract_support_flags(description: str) -> list[str]:
    """Scan description text for support keywords."""
    flags: list[str] = []
    keywords: dict[str, list[str]] = {
        "mentoring": ["mentor", "mentoring"],
        "coaching": ["coach", "coaching"],
        "capacity-building": ["capacity build", "capacity-build"],
        "training": ["training programme", "training support"],
        "networking": ["network", "peer support"],
    }
    desc_lower = description.lower()
    for flag, terms in keywords.items():
        if any(t in desc_lower for t in terms):
            flags.append(flag)
    return flags


def get_framing_label(record: dict[str, Any]) -> str | None:
    """Return a display label to replace the raw amount, or None to show amount."""
    otype = record.get("opportunityType", "grant").lower()
    amt = record.get("amountMax") or 0
    desc = (record.get("description") or "").lower()

    if otype == "grant" and amt <= 150_000:
        return None
    if otype == "grant" and amt > 150_000:
        if "capital" in desc or "building" in desc or "refurb" in desc:
            return "Capital Grant"
        if "heritage" in desc:
            return "Heritage Fund"
        if "core" in desc:
            return "Core Costs Grant"
        return "Programme Grant"
    if otype == "procurement":
        return "Supply Chain Opportunity"
    if otype == "contract":
        return "Service Delivery Contract"
    if otype == "social_investment":
        return "Blended Funding"
    return None
