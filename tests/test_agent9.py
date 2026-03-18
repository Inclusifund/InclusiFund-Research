"""Tests for Agent 9: Quantum Grant Matcher."""

import numpy as np

from quantum_grants.agents.quantum_matcher import (
    QuantumGrantMatcher, CICProfile, GrantMatch,
    encode_real_pair, _region_match, _sector_overlap, _structure_eligible,
)


class TestRegionMatch:
    def test_uk_wide_matches_anything(self):
        assert _region_match(["UK-wide"], "London") is True
        assert _region_match(["UK-wide"], "scotland") is True

    def test_exact_match(self):
        assert _region_match(["London"], "London") is True
        assert _region_match(["london"], "london") is True

    def test_no_match(self):
        assert _region_match(["Scotland"], "London") is False

    def test_england_covers_english_regions(self):
        assert _region_match(["England"], "london") is True
        assert _region_match(["England"], "south_east") is True

    def test_empty_regions(self):
        assert _region_match([], "London") is False


class TestSectorOverlap:
    def test_perfect_overlap(self):
        score = _sector_overlap(["Health", "Youth"], ["Health", "Youth"])
        assert score == 1.0

    def test_partial_overlap(self):
        score = _sector_overlap(["Health", "Youth", "Arts"], ["Health", "Education"])
        assert 0 < score < 1

    def test_no_overlap(self):
        score = _sector_overlap(["Health"], ["Education"])
        assert score == 0.0

    def test_empty_lists(self):
        assert _sector_overlap([], []) == 0.0


class TestStructureEligible:
    def test_startup_eligible(self):
        grant = {"supportsStartup": True, "supportsGrowth": False}
        cic = CICProfile(
            org_id="x", org_name="x", legal_structure="cic",
            sectors=[], themes=[], region="London",
            annual_turnover=0, years_operating=1,
        )
        assert _structure_eligible(grant, cic) is True

    def test_growth_eligible(self):
        grant = {"supportsStartup": False, "supportsGrowth": True}
        cic = CICProfile(
            org_id="x", org_name="x", legal_structure="cic",
            sectors=[], themes=[], region="London",
            annual_turnover=0, years_operating=2,
        )
        assert _structure_eligible(grant, cic) is True


class TestEncodeRealPair:
    def test_returns_6d_vector(self, sample_convex_grant, sample_cic_profile):
        features = encode_real_pair(sample_convex_grant, sample_cic_profile)
        assert features.shape == (6,)

    def test_all_bounded_0_1(self, sample_convex_grant, sample_cic_profile):
        features = encode_real_pair(sample_convex_grant, sample_cic_profile)
        assert np.all(features >= 0.0)
        assert np.all(features <= 1.0)

    def test_eligible_grant_has_eligibility_1(self, sample_convex_grant, sample_cic_profile):
        features = encode_real_pair(sample_convex_grant, sample_cic_profile)
        assert features[0] == 1.0  # UK-wide + supports startup

    def test_theme_match_from_description(self, sample_cic_profile):
        grant = {
            "regions": ["UK-wide"],
            "supportsStartup": True,
            "supportsGrowth": True,
            "sectors": [],
            "description": "Funding for community wellbeing and mental health projects",
            "maxAmount": 10000,
        }
        features = encode_real_pair(grant, sample_cic_profile)
        assert features[2] > 0  # theme_overlap should pick up "wellbeing" and "community"

    def test_zero_amount_grant(self, sample_cic_profile):
        grant = {
            "regions": ["UK-wide"],
            "supportsStartup": True,
            "sectors": [],
            "description": "",
            "maxAmount": 0,
        }
        features = encode_real_pair(grant, sample_cic_profile)
        assert abs(features[4] - 0.99) < 0.05  # difficulty_fit near 1.0 for balanced capacity vs default difficulty


class TestQuantumGrantMatcher:
    def test_score_pair_in_range(self, sample_convex_grant, sample_cic_profile):
        agent = QuantumGrantMatcher(n_layers=1)
        score = agent.score_pair(sample_convex_grant, sample_cic_profile)
        assert 0 <= score <= 1

    def test_find_matches_from_cache(self, sample_cic_profile, tmp_path):
        """Test matching using cached grants (no network)."""
        import json

        agent = QuantumGrantMatcher(n_layers=1)
        # Inject cached grants directly
        agent._grants = [
            {
                "_id": f"g{i}", "name": f"Grant {i}", "funder": "Funder",
                "minAmount": 1000, "maxAmount": 50000, "status": "Open",
                "sectors": ["Health & Wellbeing"], "regions": ["UK-wide"],
                "applicationDifficulty": 2, "supportsStartup": True,
                "supportsGrowth": True, "supportsScale": False,
                "website": "", "description": "community wellbeing support",
            }
            for i in range(10)
        ]
        matches = agent.find_matches(sample_cic_profile, top_k=5)
        assert len(matches) == 5
        assert all(isinstance(m, GrantMatch) for m in matches)
        # Ranked by score descending
        scores = [m.quantum_score for m in matches]
        assert scores == sorted(scores, reverse=True)

    def test_summary_output(self, sample_cic_profile):
        agent = QuantumGrantMatcher(n_layers=1)
        agent._grants = [
            {
                "_id": "g1", "name": "Test Grant", "funder": "Funder",
                "minAmount": 500, "maxAmount": 10000, "status": "Open",
                "sectors": [], "regions": ["UK-wide"],
                "supportsStartup": True, "supportsGrowth": True,
                "website": "", "description": "",
            }
        ]
        matches = agent.find_matches(sample_cic_profile, top_k=5)
        summary = agent.summary(matches)
        assert "Quantum Grant Matcher" in summary
        assert "Test Grant" in summary

    def test_save_load_params(self, tmp_path):
        agent = QuantumGrantMatcher(n_layers=1)
        path = str(tmp_path / "model.json")
        agent.save_params(path)

        agent2 = QuantumGrantMatcher(n_layers=1)
        agent2.load_params(path)
        np.testing.assert_array_equal(agent.circuit.params, agent2.circuit.params)
        assert agent.classical_weight == agent2.classical_weight
