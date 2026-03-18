"""Tests for the classical feature encoder."""

import numpy as np

from quantum_grants.models.feature_encoder import encode_pair, encode_batch, MatchFeatures


class TestMatchFeatures:
    def test_to_array_shape(self):
        f = MatchFeatures(1.0, 0.5, 0.3, 0.8, 0.2, 0.6)
        arr = f.to_array()
        assert arr.shape == (6,)
        assert arr.dtype == np.float64

    def test_to_array_values(self):
        f = MatchFeatures(1.0, 0.5, 0.3, 0.8, 0.2, 0.6)
        arr = f.to_array()
        np.testing.assert_array_almost_equal(arr, [1.0, 0.5, 0.3, 0.8, 0.2, 0.6])


class TestEncodePair:
    def test_eligible_pair(self, sample_grant, sample_applicant):
        features = encode_pair(sample_grant, sample_applicant)
        assert features.eligibility_binary == 1.0
        assert features.sector_overlap == 1.0  # youth_services matches
        assert 0 <= features.theme_overlap <= 1
        assert 0 <= features.capacity_normalised <= 1
        assert 0 <= features.turnover_ratio <= 1
        assert 0 <= features.experience_normalised <= 1

    def test_ineligible_pair(self, sample_grant, ineligible_applicant):
        features = encode_pair(sample_grant, ineligible_applicant)
        assert features.eligibility_binary == 0.0

    def test_all_features_bounded(self, sample_grant, sample_applicant):
        features = encode_pair(sample_grant, sample_applicant)
        arr = features.to_array()
        assert np.all(arr >= 0.0)
        assert np.all(arr <= 1.0)


class TestEncodeBatch:
    def test_batch_shape(self, synthetic_dataset):
        grants, applicants, _ = synthetic_dataset
        matrix = encode_batch(grants[:2], applicants[:3])
        assert matrix.shape == (6, 6)  # 2*3 pairs, 6 features each

    def test_batch_values_bounded(self, synthetic_dataset):
        grants, applicants, _ = synthetic_dataset
        matrix = encode_batch(grants[:3], applicants[:5])
        assert np.all(matrix >= 0.0)
        assert np.all(matrix <= 1.0)
