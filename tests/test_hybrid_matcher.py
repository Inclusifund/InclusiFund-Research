"""Tests for the hybrid quantum-classical matcher."""

from quantum_grants.models.hybrid_matcher import HybridGrantMatcher


class TestHybridGrantMatcher:
    def test_predict_score_in_range(self, sample_grant, sample_applicant):
        matcher = HybridGrantMatcher(n_layers=1)
        score = matcher.predict_score(sample_grant, sample_applicant)
        assert 0 <= score <= 1

    def test_predict_match_returns_bool(self, sample_grant, sample_applicant):
        matcher = HybridGrantMatcher(n_layers=1)
        result = matcher.predict_match(sample_grant, sample_applicant)
        assert isinstance(result, bool)

    def test_rank_grants(self, synthetic_dataset):
        grants, applicants, _ = synthetic_dataset
        matcher = HybridGrantMatcher(n_layers=1)
        ranked = matcher.rank_grants(grants, applicants[0], top_k=3)
        assert len(ranked) == 3
        # Scores should be descending
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_applicants(self, synthetic_dataset):
        grants, applicants, _ = synthetic_dataset
        matcher = HybridGrantMatcher(n_layers=1)
        ranked = matcher.rank_applicants(grants[0], applicants, top_k=5)
        assert len(ranked) == 5
        scores = [s for _, s in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_get_set_params_roundtrip(self):
        matcher = HybridGrantMatcher(n_layers=1)
        matcher.classical_weight = 2.5
        matcher.classical_bias = -0.3
        params = matcher.get_params()

        matcher2 = HybridGrantMatcher(n_layers=1)
        matcher2.set_params(params)
        assert matcher2.classical_weight == 2.5
        assert matcher2.classical_bias == -0.3
        assert list(matcher2.circuit.params) == list(matcher.circuit.params)
