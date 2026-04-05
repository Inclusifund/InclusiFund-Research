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
            "Join a bigger firm's supply chain "
            "\u2014 you don't need to win the whole contract"
        )
        tips.append(
            "This pays more than grants and comes back every year "
            "if you do good work"
        )
        if any(k in funder for k in ["council", "authority", "nhs"]):
            tips.append(
                "Already know people at the council or NHS? "
                "That's your way in \u2014 use those connections"
            )
        if any(k in desc for k in ["social", "health", "housing", "treasury"]):
            tips.append(
                "If you work in health, housing, or social care already, "
                "you're ahead of most bidders"
            )
        if regions:
            region_str = regions[0] if isinstance(regions[0], str) else str(regions[0])
            tips.append(
                f"Being based in {region_str} is a real advantage here "
                "\u2014 they want local delivery"
            )

    # --- Contract scaling ---
    elif otype == "contract":
        tips.append(
            "Start small, hire as you grow "
            "\u2014 you don't need a big team on day one"
        )
        if amt > 500_000:
            tips.append(
                "Too big alone? Team up with local charities or community groups "
                "and bid together"
            )
        tips.append(
            "Contracts mean steady income, not one-off funding "
            "\u2014 think long term"
        )

    # --- Accelerators ---
    elif otype == "accelerator":
        tips.append(
            "You get money plus free coaching and contacts "
            "\u2014 two wins from one application"
        )
        if record.get("supportsStartup"):
            tips.append("Built for people just starting out \u2014 no track record needed")

    # --- Competitions ---
    elif otype == "competition":
        tips.append(
            "Your idea matters more than your history "
            "\u2014 new CICs can absolutely win these"
        )
        if diff and diff >= 4:
            tips.append("Give yourself a week to write this one \u2014 it's competitive but worth it")

    # --- CSR ---
    elif otype == "csr":
        tips.append(
            "Companies need to show social impact "
            "\u2014 pitch how your CIC helps them tick that box"
        )

    # --- Social investment ---
    elif otype == "social_investment":
        tips.append(
            "Part grant, part loan \u2014 read the terms carefully "
            "so you know what you pay back"
        )
        tips.append(
            "Good option if grants aren't enough "
            "\u2014 the loan part is usually low interest"
        )

    # --- Grant-specific (default) ---
    else:
        if amt and amt <= 10_000:
            tips.append("Small pot, quick decision \u2014 apply this week")
        elif amt and amt <= 25_000:
            tips.append("Perfect size for one focused project \u2014 keep it simple")
        elif amt and amt > 150_000:
            if "capital" in desc or "building" in desc or "refurb" in desc:
                tips.append("For buildings and equipment \u2014 not running costs")
            elif "heritage" in desc:
                tips.append("Heritage money \u2014 great if your work touches culture or history")
            elif "core" in desc:
                tips.append("Covers salaries, rent, and bills \u2014 the hardest funding to find")
        if "partnership" in desc or "collaborat" in desc:
            tips.append("They want partnerships \u2014 who could you team up with locally?")
        if "evidence" in desc or "impact" in desc:
            tips.append("Show your impact with real numbers \u2014 people helped, sessions run, lives changed")

    # --- Universal tips ---
    if diff is not None and diff <= 2:
        tips.append("Short form, quick turnaround \u2014 you could apply today")
    elif diff is not None and diff == 3:
        tips.append("Standard application \u2014 set aside a couple of hours")
    if record.get("supportsStartup"):
        tips.append("Open to brand new CICs \u2014 no trading history needed")

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
