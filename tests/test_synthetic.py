"""Tests for synthetic data generation."""

from quantum_grants.data.synthetic import (
    generate_dataset, generate_grant, generate_applicant,
    compute_match_label, SECTORS, REGIONS, LEGAL_STRUCTURES,
)


class TestGenerateGrant:
    def test_returns_valid_grant(self):
        g = generate_grant(0)
        assert g.grant_id == "G-0000"
        assert g.max_award >= g.min_award
        assert len(g.eligible_sectors) >= 1
        assert len(g.eligible_regions) >= 1
        assert g.funder_type in ["lottery", "trust", "government", "corporate", "community_foundation"]

    def test_sectors_from_known_list(self):
        g = generate_grant(5)
        for s in g.eligible_sectors:
            assert s in SECTORS

    def test_regions_from_known_list(self):
        g = generate_grant(5)
        for r in g.eligible_regions:
            assert r in REGIONS


class TestGenerateApplicant:
    def test_returns_valid_applicant(self):
        a = generate_applicant(0)
        assert a.org_id == "ORG-0000"
        assert a.legal_structure in LEGAL_STRUCTURES
        assert a.sector in SECTORS
        assert a.region in REGIONS
        assert a.annual_turnover >= 0

    def test_themes_from_known_list(self):
        a = generate_applicant(3)
        for t in a.themes:
            assert t in SECTORS


class TestComputeMatchLabel:
    def test_eligible_pair_produces_score(self, sample_grant, sample_applicant):
        label = compute_match_label(sample_grant, sample_applicant)
        assert 0 <= label.overall_match <= 1
        assert 0 <= label.eligibility_score <= 1
        assert 0 <= label.alignment_score <= 1
        assert 0 <= label.capacity_score <= 1
        assert isinstance(label.is_match, bool)

    def test_ineligible_pair_fails(self, sample_grant, ineligible_applicant):
        label = compute_match_label(sample_grant, ineligible_applicant)
        assert label.eligibility_score == 0.0
        assert label.is_match is False

    def test_eligible_pair_can_match(self, sample_grant, sample_applicant):
        label = compute_match_label(sample_grant, sample_applicant)
        assert label.eligibility_score > 0
        assert label.is_match is True


class TestGenerateDataset:
    def test_correct_counts(self, synthetic_dataset):
        grants, applicants, labels = synthetic_dataset
        assert len(grants) == 5
        assert len(applicants) == 10
        assert len(labels) == 50  # 5 * 10

    def test_deterministic_with_seed(self):
        g1, a1, l1 = generate_dataset(n_grants=3, n_applicants=5, seed=42)
        g2, a2, l2 = generate_dataset(n_grants=3, n_applicants=5, seed=42)
        assert g1[0].grant_id == g2[0].grant_id
        assert l1[0].overall_match == l2[0].overall_match

    def test_has_both_matches_and_non_matches(self):
        _, _, labels = generate_dataset(n_grants=10, n_applicants=20, seed=42)
        positives = sum(1 for l in labels if l.is_match)
        negatives = len(labels) - positives
        assert positives > 0, "Expected some positive matches"
        assert negatives > 0, "Expected some negative matches"
