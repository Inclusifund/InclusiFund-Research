"""Shared fixtures for quantum_grants test suite."""

import pytest
import numpy as np

from quantum_grants.data.synthetic import (
    SyntheticGrant, SyntheticApplicant, generate_dataset,
)
from quantum_grants.agents.quantum_matcher import CICProfile


@pytest.fixture
def sample_grant():
    return SyntheticGrant(
        grant_id="G-TEST",
        funder_name="Test Funder",
        programme_name="Test Programme",
        funder_type="trust",
        max_award=50_000,
        min_award=5_000,
        eligible_sectors=["youth_services", "mental_health"],
        eligible_structures=["cic", "charity"],
        eligible_regions=["london", "south_east"],
        requires_match_funding=False,
        match_percentage=0,
        annual_turnover_max=250_000,
        annual_turnover_min=0,
        priority_themes=["youth_services", "mental_health"],
        deadline_days=60,
    )


@pytest.fixture
def sample_applicant():
    return SyntheticApplicant(
        org_id="ORG-TEST",
        org_name="Test CIC",
        legal_structure="cic",
        sector="youth_services",
        region="london",
        annual_turnover=50_000,
        years_operating=3,
        staff_count=5,
        beneficiary_count=200,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        themes=["youth_services", "mental_health"],
        previous_grants=2,
    )


@pytest.fixture
def ineligible_applicant():
    """Applicant that fails hard eligibility criteria."""
    return SyntheticApplicant(
        org_id="ORG-INELIG",
        org_name="Ineligible Org",
        legal_structure="community_group",  # not in eligible_structures
        sector="criminal_justice",          # not in eligible_sectors
        region="scotland",                  # not in eligible_regions
        annual_turnover=500_000,            # over turnover max
        years_operating=0,
        staff_count=0,
        beneficiary_count=5,
        has_safeguarding_policy=False,
        has_financial_controls=False,
        themes=["environment"],
        previous_grants=0,
    )


@pytest.fixture
def sample_cic_profile():
    return CICProfile(
        org_id="CIC-TEST",
        org_name="Test Wellness CIC",
        legal_structure="cic",
        sectors=["Health & Wellbeing", "Community Development"],
        themes=["wellbeing", "mental health", "community"],
        region="London",
        annual_turnover=30_000,
        years_operating=2,
        staff_count=4,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=1,
        beneficiaries=["young people", "families"],
    )


@pytest.fixture
def sample_convex_grant():
    """A grant dict matching the Convex schema."""
    return {
        "_id": "j97test123",
        "name": "National Lottery Awards for All",
        "funder": "National Lottery Community Fund",
        "minAmount": 300,
        "maxAmount": 20_000,
        "status": "Open",
        "sectors": ["Community Development", "Health & Wellbeing", "Youth Services"],
        "regions": ["UK-wide"],
        "applicationDifficulty": 2,
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "website": "https://www.tnlcommunityfund.org.uk",
        "description": "A quick way to apply for smaller amounts of funding for community and wellbeing projects.",
        "deadline": None,
    }


@pytest.fixture
def synthetic_dataset():
    """Small deterministic dataset for testing."""
    return generate_dataset(n_grants=5, n_applicants=10, seed=99)
