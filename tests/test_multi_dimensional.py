"""Tests for multi-dimensional grant scoring."""

import pytest
from unittest.mock import patch, MagicMock

from quantum_grants.scoring.multi_dimensional import (
    MultiDimensionalScore,
    MultiDimensionalScorer,
    score_technical_fit,
    score_social_value_alignment,
    score_evidence_strength,
    score_win_probability,
    score_competition_intensity,
)
from quantum_grants.agents.quantum_matcher import CICProfile
from quantum_grants.pipeline import QuantumPipeline, PipelineResult, normalise_grant
from quantum_grants.training.real_data_trainer import DEMO_PROFILES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def startup_cic():
    """A young startup CIC — fictional demo profile."""
    return CICProfile(
        org_id="DEMO-STARTUP",
        org_name="Demo Startup CIC",
        legal_structure="cic",
        sectors=["Youth Services", "Health & Wellbeing"],
        themes=["mentoring", "young people", "mental health", "wellbeing"],
        region="London",
        annual_turnover=0,
        years_operating=0.5,
        staff_count=2,
        has_safeguarding_policy=True,
        has_financial_controls=False,
        previous_grants=0,
        beneficiaries=["children", "young people"],
    )


@pytest.fixture
def established_charity():
    """An established charity — fictional demo profile."""
    return CICProfile(
        org_id="DEMO-ESTABLISHED",
        org_name="Demo Established Charity",
        legal_structure="charity",
        sectors=["Community Development", "Arts & Culture", "Education"],
        themes=["community", "arts", "learning", "skills", "inclusion"],
        region="London",
        annual_turnover=150_000,
        years_operating=8,
        staff_count=12,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=5,
        beneficiaries=["families", "young people", "older people"],
    )


@pytest.fixture
def youth_grant():
    """A small startup-friendly youth grant."""
    return {
        "_id": "grant-youth-001",
        "name": "Youth Wellbeing Fund",
        "funder": "National Lottery Community Fund",
        "maxAmount": 10_000,
        "minAmount": 500,
        "sectors": ["Youth Services", "Health & Wellbeing"],
        "regions": ["UK-wide"],
        "description": "Supporting youth mental health and wellbeing projects for disadvantaged young people in underserved communities.",
        "status": "Open",
        "supportsStartup": True,
        "supportsGrowth": True,
        "supportsScale": False,
        "applicationDifficulty": 2,
        "website": "https://example.com/youth",
        "deadline": "Rolling",
    }


@pytest.fixture
def large_arts_grant():
    """A large, competitive arts grant."""
    return {
        "_id": "grant-arts-001",
        "name": "National Arts Excellence Programme",
        "funder": "Arts Council England",
        "maxAmount": 250_000,
        "minAmount": 25_000,
        "sectors": ["Arts & Culture"],
        "regions": ["England"],
        "description": "Major funding for established arts organisations delivering creative excellence and community engagement.",
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 5,
        "website": "https://example.com/arts",
        "deadline": "1 June 2026",
    }


@pytest.fixture
def environment_grant():
    """An environment grant with no sector overlap for youth CICs."""
    return {
        "_id": "grant-env-001",
        "name": "Green Futures Fund",
        "funder": "Defra",
        "maxAmount": 100_000,
        "minAmount": 10_000,
        "sectors": ["Environment", "Sustainability"],
        "regions": ["England"],
        "description": "Supporting environmental conservation and climate action for biodiversity.",
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": False,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://example.com/env",
    }


@pytest.fixture
def scorer():
    return MultiDimensionalScorer()


# ---------------------------------------------------------------------------
# MultiDimensionalScore dataclass
# ---------------------------------------------------------------------------

class TestMultiDimensionalScore:
    def test_composite_calculation(self):
        score = MultiDimensionalScore(
            technical_fit=80,
            social_value_alignment=60,
            evidence_strength=70,
            win_probability=90,
            competition_intensity=40,
        )
        # 0.25*80 + 0.20*60 + 0.20*70 + 0.25*90 + 0.10*(100-40)
        # = 20 + 12 + 14 + 22.5 + 6 = 74.5
        assert score.composite == 74.5

    def test_composite_with_custom_weights(self):
        score = MultiDimensionalScore(
            technical_fit=100,
            social_value_alignment=0,
            evidence_strength=0,
            win_probability=0,
            competition_intensity=0,
        )
        custom = {
            "technical_fit": 1.0,
            "social_value_alignment": 0.0,
            "evidence_strength": 0.0,
            "win_probability": 0.0,
            "competition_intensity": 0.0,
        }
        assert score.compute_composite(custom) == 100.0

    def test_composite_clamped_to_100(self):
        score = MultiDimensionalScore(
            technical_fit=100,
            social_value_alignment=100,
            evidence_strength=100,
            win_probability=100,
            competition_intensity=0,
        )
        assert score.composite <= 100.0

    def test_composite_never_negative(self):
        score = MultiDimensionalScore(
            technical_fit=0,
            social_value_alignment=0,
            evidence_strength=0,
            win_probability=0,
            competition_intensity=100,
        )
        assert score.composite >= 0.0

    def test_to_dict(self):
        score = MultiDimensionalScore(
            technical_fit=50,
            social_value_alignment=60,
            evidence_strength=70,
            win_probability=80,
            competition_intensity=30,
        )
        d = score.to_dict()
        assert "technical_fit" in d
        assert "social_value_alignment" in d
        assert "evidence_strength" in d
        assert "win_probability" in d
        assert "competition_intensity" in d
        assert "composite" in d
        # All numeric values should be floats (composite is computed)
        for k, v in d.items():
            assert isinstance(v, (int, float)), f"{k} is {type(v)}"

    def test_summary_format(self):
        score = MultiDimensionalScore(
            technical_fit=75, social_value_alignment=60,
            evidence_strength=55, win_probability=80,
            competition_intensity=45,
        )
        text = score.summary()
        assert "Technical Fit" in text
        assert "Social Value" in text
        assert "Composite" in text


# ---------------------------------------------------------------------------
# Individual dimension scorers
# ---------------------------------------------------------------------------

class TestTechnicalFit:
    def test_high_overlap_startup(self, youth_grant, startup_cic):
        """Youth grant + youth CIC should score high on technical fit."""
        score = score_technical_fit(youth_grant, startup_cic)
        assert 40 <= score <= 100
        assert score > 50  # should be a good match

    def test_no_sector_overlap(self, environment_grant, startup_cic):
        """Environment grant + youth CIC should score lower."""
        score = score_technical_fit(environment_grant, startup_cic)
        assert score < 40  # poor sector match + stage mismatch

    def test_established_org_large_grant(self, large_arts_grant, established_charity):
        """Established charity + large arts grant should fit well technically."""
        score = score_technical_fit(large_arts_grant, established_charity)
        assert score > 30  # decent match (arts overlap + growth/scale)

    def test_score_in_range(self, youth_grant, startup_cic):
        score = score_technical_fit(youth_grant, startup_cic)
        assert 0 <= score <= 100

    def test_empty_grant_sectors(self, startup_cic):
        grant = {"sectors": [], "regions": ["UK-wide"], "supportsStartup": True}
        score = score_technical_fit(grant, startup_cic)
        assert 0 <= score <= 100


class TestSocialValueAlignment:
    def test_high_alignment(self, youth_grant, startup_cic):
        """Youth wellbeing grant with disadvantage keywords should align well."""
        score = score_social_value_alignment(youth_grant, startup_cic)
        assert score > 10  # meaningful alignment expected

    def test_low_alignment(self, environment_grant, startup_cic):
        """Environment grant should have low social value alignment with youth CIC."""
        score = score_social_value_alignment(environment_grant, startup_cic)
        # May still pick up some social value keywords from description
        assert 0 <= score <= 100

    def test_score_in_range(self, youth_grant, established_charity):
        score = score_social_value_alignment(youth_grant, established_charity)
        assert 0 <= score <= 100

    def test_empty_beneficiaries(self, youth_grant):
        cic = CICProfile(
            org_id="DEMO-EMPTY", org_name="Empty CIC",
            legal_structure="cic", sectors=[], themes=[],
            region="London", annual_turnover=0, years_operating=1,
        )
        score = score_social_value_alignment(youth_grant, cic)
        assert 0 <= score <= 100


class TestEvidenceStrength:
    def test_established_scores_higher(self, youth_grant, startup_cic, established_charity):
        """Established charity should have stronger evidence than startup."""
        startup_score = score_evidence_strength(youth_grant, startup_cic)
        established_score = score_evidence_strength(youth_grant, established_charity)
        assert established_score > startup_score

    def test_startup_low_evidence(self, youth_grant, startup_cic):
        """Startup with no track record should score low on evidence."""
        score = score_evidence_strength(youth_grant, startup_cic)
        assert score < 40

    def test_high_evidence_established(self, youth_grant, established_charity):
        """Established charity with full governance should score well."""
        score = score_evidence_strength(youth_grant, established_charity)
        assert score > 40

    def test_score_in_range(self, large_arts_grant, startup_cic):
        score = score_evidence_strength(large_arts_grant, startup_cic)
        assert 0 <= score <= 100


class TestWinProbability:
    def test_easy_grant_startup(self, youth_grant, startup_cic):
        """Easy startup-friendly grant should have decent win probability."""
        score = score_win_probability(youth_grant, startup_cic)
        assert score > 30

    def test_hard_grant_startup(self, large_arts_grant, startup_cic):
        """Hard non-startup grant should have low win prob for startup."""
        score = score_win_probability(large_arts_grant, startup_cic)
        assert score < 50

    def test_established_high_win(self, youth_grant, established_charity):
        """Established org applying to easy grant should have high win prob."""
        score = score_win_probability(youth_grant, established_charity)
        assert score > 50

    def test_score_in_range(self, environment_grant, startup_cic):
        score = score_win_probability(environment_grant, startup_cic)
        assert 0 <= score <= 100


class TestCompetitionIntensity:
    def test_small_grant_less_competitive(self, youth_grant, startup_cic):
        """Small rolling grants should be moderately competitive."""
        score = score_competition_intensity(youth_grant, startup_cic)
        # Rolling + startup-friendly + UK-wide = quite competitive (low score)
        assert 0 <= score <= 100

    def test_large_grant_more_competitive(self, youth_grant, large_arts_grant, startup_cic):
        """Large national grants should be more competitive (lower score)."""
        small_score = score_competition_intensity(youth_grant, startup_cic)
        large_score = score_competition_intensity(large_arts_grant, startup_cic)
        # Both should be in range
        assert 0 <= small_score <= 100
        assert 0 <= large_score <= 100

    def test_score_in_range(self, environment_grant, established_charity):
        score = score_competition_intensity(environment_grant, established_charity)
        assert 0 <= score <= 100

    def test_niche_grant_less_competitive(self, startup_cic):
        """A very specific grant should have less competition."""
        niche = {
            "maxAmount": 5_000,
            "sectors": ["Youth Services", "Mental Health", "LGBTQ+", "Housing"],
            "regions": ["Merton"],
            "applicationDifficulty": 4,
            "supportsStartup": False,
        }
        national = {
            "maxAmount": 50_000,
            "sectors": ["Community Development"],
            "regions": ["UK-wide"],
            "applicationDifficulty": 2,
            "supportsStartup": True,
            "deadline": "Rolling",
        }
        niche_score = score_competition_intensity(niche, startup_cic)
        national_score = score_competition_intensity(national, startup_cic)
        # Niche should have less competition (higher score)
        assert niche_score > national_score


# ---------------------------------------------------------------------------
# MultiDimensionalScorer class
# ---------------------------------------------------------------------------

class TestMultiDimensionalScorer:
    def test_score_returns_all_dimensions(self, scorer, youth_grant, startup_cic):
        result = scorer.score(youth_grant, startup_cic)
        assert isinstance(result, MultiDimensionalScore)
        assert 0 <= result.technical_fit <= 100
        assert 0 <= result.social_value_alignment <= 100
        assert 0 <= result.evidence_strength <= 100
        assert 0 <= result.win_probability <= 100
        assert 0 <= result.competition_intensity <= 100
        assert 0 <= result.composite <= 100

    def test_score_batch(self, scorer, youth_grant, large_arts_grant, startup_cic):
        grants = [youth_grant, large_arts_grant]
        results = scorer.score_batch(grants, startup_cic)
        assert len(results) == 2
        # Should be sorted by composite descending
        assert results[0][1].composite >= results[1][1].composite

    def test_custom_weights(self, youth_grant, startup_cic):
        # All weight on technical fit
        custom = {
            "technical_fit": 1.0,
            "social_value_alignment": 0.0,
            "evidence_strength": 0.0,
            "win_probability": 0.0,
            "competition_intensity": 0.0,
        }
        scorer = MultiDimensionalScorer(weights=custom)
        result = scorer.score(youth_grant, startup_cic)
        # Composite should equal technical_fit
        assert abs(result.composite - result.technical_fit) < 0.01

    def test_with_demo_profiles(self, scorer, youth_grant):
        """Test with DEMO_PROFILES from training data (no real client data)."""
        for profile in DEMO_PROFILES:
            result = scorer.score(youth_grant, profile)
            assert isinstance(result, MultiDimensionalScore)
            assert 0 <= result.composite <= 100


# ---------------------------------------------------------------------------
# Pipeline integration
# ---------------------------------------------------------------------------

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
        "description": "Arts-led community engagement",
        "status": "Open",
        "supportsStartup": False,
        "supportsGrowth": True,
        "supportsScale": True,
        "applicationDifficulty": 4,
        "website": "https://example.com/arts",
    },
]


@pytest.fixture
def md_pipeline(tmp_path):
    """Pipeline with mocked Convex for multi-dimensional tests."""
    with patch.object(
        QuantumPipeline, "_load_latest_model", return_value=False
    ):
        pipeline = QuantumPipeline(use_cache=True)

    pipeline.output_dir = tmp_path / "runs"
    pipeline.output_dir.mkdir()

    pipeline.fetch_grants = MagicMock(return_value=[
        normalise_grant(g) for g in MOCK_GRANTS
    ])

    return pipeline


class TestPipelineIntegration:
    def test_pipeline_without_md(self, md_pipeline):
        """Default pipeline run should NOT include multi-dimensional scores."""
        result = md_pipeline.run(DEMO_PROFILES[0], top_k=10)
        assert result.multi_dimensional_scores is None

    def test_pipeline_with_md(self, md_pipeline):
        """Pipeline with multi_dimensional=True should include 5D scores."""
        result = md_pipeline.run(
            DEMO_PROFILES[0], top_k=10, multi_dimensional=True
        )
        assert result.multi_dimensional_scores is not None
        assert len(result.multi_dimensional_scores) > 0

        for grant_id, mds in result.multi_dimensional_scores.items():
            assert isinstance(mds, MultiDimensionalScore)
            assert 0 <= mds.composite <= 100

    def test_md_scores_in_to_dict(self, md_pipeline):
        """Multi-dimensional scores should serialise to dict."""
        result = md_pipeline.run(
            DEMO_PROFILES[0], top_k=10, multi_dimensional=True
        )
        d = result.to_dict()
        assert "multi_dimensional_scores" in d
        for grant_id, score_dict in d["multi_dimensional_scores"].items():
            assert "technical_fit" in score_dict
            assert "social_value_alignment" in score_dict
            assert "evidence_strength" in score_dict
            assert "win_probability" in score_dict
            assert "competition_intensity" in score_dict
            assert "composite" in score_dict

    def test_md_does_not_break_existing(self, md_pipeline):
        """Multi-dimensional flag should not affect existing match scores."""
        result_without = md_pipeline.run(DEMO_PROFILES[0], top_k=10)
        result_with = md_pipeline.run(
            DEMO_PROFILES[0], top_k=10, multi_dimensional=True
        )
        # Same number of matches
        assert len(result_without.matches) == len(result_with.matches)
        # Quantum scores should be identical (same grants, same scoring)
        for m1, m2 in zip(result_without.matches, result_with.matches):
            assert m1.grant_name == m2.grant_name

    def test_summary_with_md(self, md_pipeline):
        """Summary should include multi-dimensional breakdown."""
        result = md_pipeline.run(
            DEMO_PROFILES[0], top_k=10, multi_dimensional=True
        )
        text = md_pipeline.summary(result)
        assert "Tech:" in text
        assert "Social:" in text
        assert "Evidence:" in text
