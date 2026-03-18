"""Tests for the quantum grant pipeline (Convex integration)."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from quantum_grants.pipeline import (
    QuantumPipeline,
    PipelineResult,
    normalise_grant,
    get_client,
)
from quantum_grants.agents.quantum_matcher import CICProfile, GrantMatch
from quantum_grants.training.real_data_trainer import DEMO_PROFILES


# --- normalise_grant ---

class TestNormaliseGrant:
    def test_new_schema_passthrough(self):
        g = normalise_grant({
            "name": "Test Grant",
            "maxAmount": 10000,
            "minAmount": 500,
            "sectors": ["Health"],
            "regions": ["London"],
        })
        assert g["name"] == "Test Grant"
        assert g["maxAmount"] == 10000
        assert g["sectors"] == ["Health"]
        assert g["regions"] == ["London"]

    def test_old_schema_mapped(self):
        g = normalise_grant({
            "grantName": "Old Grant",
            "amountMax": 25000,
            "amountMin": 1000,
            "eligibleSectors": ["Arts"],
            "geographicFocus": "Wales",
        })
        assert g["name"] == "Old Grant"
        assert g["maxAmount"] == 25000
        assert g["minAmount"] == 1000
        assert g["sectors"] == ["Arts"]
        assert g["regions"] == ["Wales"]

    def test_both_schemas_prefers_new(self):
        g = normalise_grant({
            "name": "New Name",
            "grantName": "Old Name",
            "maxAmount": 5000,
            "amountMax": 9999,
        })
        assert g["name"] == "New Name"
        assert g["maxAmount"] == 5000

    def test_defaults_applied(self):
        g = normalise_grant({})
        assert g["maxAmount"] == 0
        assert g["sectors"] == []
        assert g["regions"] == []
        assert g["description"] == ""
        assert g["supportsStartup"] is False
        assert g["applicationDifficulty"] == 3

    def test_string_region_becomes_list(self):
        g = normalise_grant({"regions": "Scotland"})
        assert g["regions"] == ["Scotland"]

    def test_geographicfocus_string_becomes_list(self):
        g = normalise_grant({"geographicFocus": "UK-wide"})
        assert g["regions"] == ["UK-wide"]


# --- get_client ---

class TestGetClient:
    def test_get_by_profile(self):
        profile = CICProfile(
            org_id="DIRECT",
            org_name="Direct",
            legal_structure="cic",
            sectors=[],
            themes=[],
            region="London",
            annual_turnover=0,
            years_operating=1,
        )
        assert get_client(profile) is profile

    def test_non_profile_raises(self):
        with pytest.raises(TypeError, match="Expected a CICProfile"):
            get_client("NONEXISTENT-999")


# --- Pipeline (offline / mocked Convex) ---

MOCK_GRANTS = [
    {
        "_id": "grant-001",
        "name": "Youth Wellbeing Fund",
        "funder": "NLCF",
        "maxAmount": 10000,
        "minAmount": 500,
        "sectors": ["Youth Services", "Health & Wellbeing"],
        "regions": ["UK-wide"],
        "description": "Supporting youth mental health and wellbeing projects",
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://example.com/youth",
    },
    {
        "_id": "grant-002",
        "name": "Community Arts Programme",
        "funder": "ACE",
        "maxAmount": 50000,
        "minAmount": 5000,
        "sectors": ["Arts & Culture", "Community Development"],
        "regions": ["England"],
        "description": "Arts-led community engagement and creative wellbeing",
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://example.com/arts",
    },
    {
        "_id": "grant-003",
        "grantName": "Environment Legacy",
        "funder": "Defra",
        "amountMax": 100000,
        "amountMin": 10000,
        "eligibleSectors": ["Environment", "Sustainability"],
        "geographicFocus": "England",
        "description": "Environmental conservation for rural communities",
        "status": "Closed",
        "supportsStartup": False,
        "supportsGrowth": False,
        "supportsScale": True,
        "applicationDifficulty": 5,
        "website": "https://example.com/env",
    },
]

# Use the first demo profile as the test profile
TEST_PROFILE = DEMO_PROFILES[0]
# Use the environmental co-op demo profile for old-schema test
TEST_ENV_PROFILE = DEMO_PROFILES[2]


@pytest.fixture
def mock_pipeline(tmp_path):
    """Pipeline with mocked Convex and temp output dir."""
    with patch.object(
        QuantumPipeline, "_load_latest_model", return_value=False
    ):
        pipeline = QuantumPipeline(use_cache=True)

    pipeline.output_dir = tmp_path / "runs"
    pipeline.output_dir.mkdir()

    # Mock grant fetching to return our test grants
    pipeline.fetch_grants = MagicMock(return_value=[
        normalise_grant(g) for g in MOCK_GRANTS
    ])

    return pipeline


class TestQuantumPipeline:
    def test_run_single_client(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE, top_k=10)

        assert isinstance(result, PipelineResult)
        assert result.org_id == TEST_PROFILE.org_id
        assert result.total_grants_scored == 3
        assert len(result.matches) <= 10
        assert all(isinstance(m, GrantMatch) for m in result.matches)
        # Scores should be in [0, 1]
        for m in result.matches:
            assert 0 <= m.quantum_score <= 1

    def test_run_saves_output(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE)
        assert Path(result.output_path).exists()

        with open(result.output_path) as f:
            data = json.load(f)
        assert data["org_id"] == TEST_PROFILE.org_id
        assert "matches" in data

    def test_recommended_subset(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE)
        for m in result.recommended:
            assert m.quantum_score >= mock_pipeline.matcher.threshold

    def test_deadline_agent_output(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE)
        deadline_out = result.for_deadline_agent()
        assert isinstance(deadline_out, list)
        if deadline_out:
            item = deadline_out[0]
            assert "grant_id" in item
            assert "grant_name" in item
            assert "funder" in item
            assert "quantum_score" in item

    def test_writer_agent_output(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE)
        writer_out = result.for_writer_agent()
        assert isinstance(writer_out, list)
        if writer_out:
            item = writer_out[0]
            assert "grant_id" in item
            assert "eligibility" in item
            assert "sector_overlap" in item
            assert "theme_overlap" in item
            assert "capacity" in item
            assert "min_amount" in item
            assert "max_amount" in item

    def test_run_with_profile_directly(self, mock_pipeline):
        profile = CICProfile(
            org_id="ADHOC-001",
            org_name="Ad Hoc CIC",
            legal_structure="cic",
            sectors=["Youth Services"],
            themes=["wellbeing"],
            region="London",
            annual_turnover=5000,
            years_operating=1,
        )
        result = mock_pipeline.run(profile)
        assert result.org_id == "ADHOC-001"

    def test_summary_format(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE)
        text = mock_pipeline.summary(result)
        assert TEST_PROFILE.org_id in text
        assert "Quantum Pipeline" in text
        assert "Grants scored:" in text

    def test_to_dict_roundtrip(self, mock_pipeline):
        result = mock_pipeline.run(TEST_PROFILE)
        d = result.to_dict()
        assert d["org_id"] == TEST_PROFILE.org_id
        assert d["total_grants_scored"] == 3
        assert len(d["matches"]) == len(result.matches)

    def test_normalised_grants_injected(self, mock_pipeline):
        """Ensures old-schema grants get normalised before scoring."""
        result = mock_pipeline.run(TEST_ENV_PROFILE)
        # grant-003 uses old schema -- if normalised, it should appear
        grant_names = [m.grant_name for m in result.matches]
        assert "Environment Legacy" in grant_names


# --- Blocked funder filtering ---

BLOCKED_FUNDER_GRANTS = [
    {
        "_id": "grant-blocked-gw",
        "name": "Garfield Weston Foundation Grant",
        "funder": "Garfield Weston",
        "maxAmount": 50000,
        "minAmount": 5000,
        "sectors": ["Community Development"],
        "regions": ["UK-wide"],
        "description": "Supporting community organisations",
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 3,
        "website": "https://example.com/gw",
    },
    {
        "_id": "grant-blocked-hs",
        "name": "Henry Smith Charity Grant",
        "funder": "Henry Smith",
        "maxAmount": 60000,
        "minAmount": 10000,
        "sectors": ["Health & Wellbeing"],
        "regions": ["UK-wide"],
        "description": "Supporting disadvantaged communities",
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://example.com/hs",
    },
    {
        "_id": "grant-safe",
        "name": "Youth Wellbeing Fund",
        "funder": "NLCF",
        "maxAmount": 10000,
        "minAmount": 500,
        "sectors": ["Youth Services", "Health & Wellbeing"],
        "regions": ["UK-wide"],
        "description": "Supporting youth mental health",
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://example.com/youth",
    },
]


@pytest.fixture
def blocked_pipeline(tmp_path):
    """Pipeline with blocked funder grants for filtering tests."""
    with patch.object(
        QuantumPipeline, "_load_latest_model", return_value=False
    ):
        pipeline = QuantumPipeline(use_cache=True)

    pipeline.output_dir = tmp_path / "runs"
    pipeline.output_dir.mkdir()

    pipeline.fetch_grants = MagicMock(return_value=[
        normalise_grant(g) for g in BLOCKED_FUNDER_GRANTS
    ])

    return pipeline


class TestBlockedFunderFiltering:
    def test_garfield_weston_blocked_for_cic(self, blocked_pipeline):
        """Garfield Weston should be filtered out for CIC orgs."""
        profile = CICProfile(
            org_id="TEST-CIC",
            org_name="Test CIC",
            legal_structure="cic",
            sectors=["Community Development"],
            themes=["wellbeing"],
            region="London",
            annual_turnover=10000,
            years_operating=2,
        )
        result = blocked_pipeline.run(profile, top_k=20)
        funder_names = [m.funder for m in result.matches]
        assert "Garfield Weston" not in funder_names

    def test_garfield_weston_not_blocked_for_charity(self, blocked_pipeline):
        """Garfield Weston should NOT be filtered for registered charities."""
        profile = CICProfile(
            org_id="TEST-CHARITY",
            org_name="Test Charity",
            legal_structure="charity",
            sectors=["Community Development"],
            themes=["wellbeing"],
            region="London",
            annual_turnover=100000,
            years_operating=5,
        )
        result = blocked_pipeline.run(profile, top_k=20)
        funder_names = [m.funder for m in result.matches]
        assert "Garfield Weston" in funder_names

    def test_henry_smith_blocked_for_young_org(self, blocked_pipeline):
        """Henry Smith should be filtered for orgs under 18 months old."""
        profile = CICProfile(
            org_id="TEST-YOUNG",
            org_name="Young Charity",
            legal_structure="charity",
            sectors=["Health & Wellbeing"],
            themes=["wellbeing"],
            region="London",
            annual_turnover=0,
            years_operating=0.5,
        )
        result = blocked_pipeline.run(profile, top_k=20)
        funder_names = [m.funder for m in result.matches]
        assert "Henry Smith" not in funder_names

    def test_blocked_count_reported(self, blocked_pipeline):
        """blocked_count should reflect the number of filtered grants."""
        profile = CICProfile(
            org_id="TEST-CIC-2",
            org_name="Test CIC 2",
            legal_structure="cic",
            sectors=["Community Development", "Health & Wellbeing"],
            themes=["wellbeing"],
            region="London",
            annual_turnover=0,
            years_operating=0.5,
        )
        result = blocked_pipeline.run(profile, top_k=20)
        # Garfield Weston (CIC blocked) + Henry Smith (age + income blocked)
        # should both be filtered
        assert result.blocked_count >= 2
        assert "blocked_count" in result.to_dict()
        assert result.to_dict()["blocked_count"] == result.blocked_count
