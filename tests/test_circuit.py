"""Tests for the quantum circuit."""

import numpy as np
import math

from quantum_grants.circuits.grant_circuit import (
    QuantumMatchCircuit, encode_features_to_angles, build_ansatz_params,
    FEATURE_DIM, N_QUBITS,
)


class TestEncodeFeatures:
    def test_maps_to_pi_range(self):
        features = np.array([0.0, 0.5, 1.0, 0.25, 0.75, 0.1])
        angles = encode_features_to_angles(features)
        assert angles.shape == (6,)
        np.testing.assert_almost_equal(angles[0], 0.0)
        np.testing.assert_almost_equal(angles[2], math.pi)
        np.testing.assert_almost_equal(angles[1], math.pi / 2)

    def test_clips_out_of_range(self):
        features = np.array([-0.5, 1.5, 0.5, 0.5, 0.5, 0.5])
        angles = encode_features_to_angles(features)
        assert angles[0] == 0.0
        np.testing.assert_almost_equal(angles[1], math.pi)


class TestBuildAnsatzParams:
    def test_correct_count(self):
        params = build_ansatz_params(n_layers=2)
        expected = 2 * N_QUBITS * 3  # layers * qubits * 3 gates
        assert len(params) == expected

    def test_in_range(self):
        params = build_ansatz_params(n_layers=3)
        assert np.all(params >= 0)
        assert np.all(params <= 2 * math.pi)


class TestQuantumMatchCircuit:
    def test_init(self):
        circuit = QuantumMatchCircuit(n_layers=2)
        assert circuit.n_qubits == N_QUBITS
        assert circuit.n_layers == 2
        assert len(circuit.params) == 2 * N_QUBITS * 3

    def test_numpy_forward_returns_score(self):
        circuit = QuantumMatchCircuit(n_layers=1)
        features = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        score = circuit._numpy_simulate(features, circuit.params)
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_forward_deterministic(self):
        circuit = QuantumMatchCircuit(n_layers=2)
        features = np.array([1.0, 0.7, 0.3, 0.8, 0.5, 0.2])
        params = circuit.params.copy()
        s1 = circuit.forward(features, params)
        s2 = circuit.forward(features, params)
        assert s1 == s2

    def test_different_features_different_scores(self):
        circuit = QuantumMatchCircuit(n_layers=2)
        np.random.seed(42)
        circuit.params = np.random.uniform(0, 2 * math.pi, size=len(circuit.params))
        f1 = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        f2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        s1 = circuit.forward(f1)
        s2 = circuit.forward(f2)
        assert s1 != s2

    def test_gradient_shape(self):
        circuit = QuantumMatchCircuit(n_layers=1)
        features = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        grads = circuit.gradient(features)
        assert grads.shape == circuit.params.shape

    def test_qpanda_matches_numpy(self):
        """QPanda and numpy backends should produce similar scores."""
        circuit = QuantumMatchCircuit(n_layers=1)
        if not circuit._qpanda_available:
            return  # skip if QPanda not installed
        features = np.array([0.5, 0.3, 0.7, 0.2, 0.8, 0.4])
        params = circuit.params.copy()
        numpy_score = circuit._numpy_simulate(features, params)
        qpanda_score = circuit._qpanda_forward(features, params)
        # Allow some tolerance for floating point differences
        assert abs(numpy_score - qpanda_score) < 0.05, (
            f"numpy={numpy_score:.4f} vs qpanda={qpanda_score:.4f}"
        )
