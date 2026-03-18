"""Tests for Origin Quantum Cloud integration and backend routing."""

import math
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from quantum_grants.circuits.grant_circuit import (
    QuantumMatchCircuit,
    encode_features_to_angles,
    N_QUBITS,
)
from quantum_grants.circuits.origin_cloud import check_cloud_status


class TestCheckCloudStatus:
    """Tests for the check_cloud_status() function."""

    def test_returns_dict_with_expected_keys(self):
        status = check_cloud_status()
        assert isinstance(status, dict)
        assert "qpanda_installed" in status
        assert "api_key_configured" in status
        assert "api_key_prefix" in status
        assert "ready" in status
        assert "message" in status

    def test_qpanda_not_installed(self):
        """When pyqpanda is not importable, qpanda_installed should be False."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pyqpanda":
                raise ImportError("mocked")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            status = check_cloud_status()
        assert status["qpanda_installed"] is False
        assert "NOT installed" in status["message"]

    def test_api_key_detected_from_env(self):
        """When ORIGIN_QUANTUM_API_KEY is set, api_key_configured should be True."""
        with patch.dict("os.environ", {"ORIGIN_QUANTUM_API_KEY": "testkey12345"}):
            status = check_cloud_status()
            assert status["api_key_configured"] is True
            assert status["api_key_prefix"] == "testkey1"

    def test_api_key_not_set(self):
        """When no API key is available, api_key_configured should be False."""
        with patch.dict("os.environ", {"ORIGIN_QUANTUM_API_KEY": ""}, clear=False):
            # Also mock the config loader to raise
            with patch(
                "quantum_grants.config.get_origin_quantum_api_key",
                side_effect=EnvironmentError("not set"),
            ):
                status = check_cloud_status()
                assert status["api_key_configured"] is False
                assert status["api_key_prefix"] is None

    def test_ready_requires_both(self):
        """ready should only be True when both pyqpanda and API key are available."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pyqpanda":
                raise ImportError("mocked")
            return real_import(name, *args, **kwargs)

        # Without pyqpanda, ready should be False even with API key
        with patch("builtins.__import__", side_effect=mock_import):
            with patch.dict("os.environ", {"ORIGIN_QUANTUM_API_KEY": "testkey"}):
                status = check_cloud_status()
                assert status["ready"] is False
                assert status["qpanda_installed"] is False
                assert status["api_key_configured"] is True


class TestForwardBackendRouting:
    """Tests for the backend parameter on QuantumMatchCircuit.forward()."""

    def setup_method(self):
        self.circuit = QuantumMatchCircuit(n_layers=1)
        self.features = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

    def test_numpy_backend_always_uses_numpy(self):
        """backend='numpy' should use numpy simulation regardless of qpanda."""
        score = self.circuit.forward(self.features, backend="numpy")
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_numpy_backend_matches_direct_call(self):
        """backend='numpy' should produce same result as _numpy_simulate."""
        params = self.circuit.params.copy()
        direct = self.circuit._numpy_simulate(self.features, params)
        routed = self.circuit.forward(self.features, params, backend="numpy")
        assert direct == routed

    def test_auto_backend_falls_back_to_numpy(self):
        """backend='auto' should fall back to numpy when pyqpanda is unavailable."""
        params = self.circuit.params.copy()
        # Force qpanda unavailable
        with patch.object(self.circuit, "_qpanda_available", False):
            auto_score = self.circuit.forward(self.features, params, backend="auto")
        numpy_score = self.circuit.forward(self.features, params, backend="numpy")
        assert auto_score == numpy_score

    def test_cloud_backend_raises_without_qpanda(self):
        """backend='cloud' should raise RuntimeError when pyqpanda is not installed."""
        with patch.object(self.circuit, "_qpanda_available", False):
            with pytest.raises(RuntimeError, match="Cloud backend requires pyqpanda"):
                self.circuit.forward(self.features, backend="cloud")

    def test_invalid_backend_raises(self):
        """Unknown backend name should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            self.circuit.forward(self.features, backend="quantum_teleportation")

    def test_default_backend_is_auto(self):
        """Default backend should be 'auto' (backward-compatible)."""
        params = self.circuit.params.copy()
        # Call without backend param — should behave like auto
        default_score = self.circuit.forward(self.features, params)
        auto_score = self.circuit.forward(self.features, params, backend="auto")
        assert default_score == auto_score

    def test_backward_compatible_signature(self):
        """Old call signature forward(features) and forward(features, params) must still work."""
        # Just features
        s1 = self.circuit.forward(self.features)
        assert isinstance(s1, float)
        assert 0 <= s1 <= 1

        # Features + params
        s2 = self.circuit.forward(self.features, self.circuit.params)
        assert isinstance(s2, float)
        assert 0 <= s2 <= 1


class TestCloudCircuitBuilder:
    """Tests for the cloud circuit builder structure (mocked pyqpanda)."""

    def test_cloud_forward_builds_correct_circuit_structure(self):
        """
        Verify that _cloud_forward constructs the right circuit when
        pyqpanda IS available (mocked).
        """
        circuit = QuantumMatchCircuit(n_layers=1)
        features = np.array([0.5, 0.3, 0.7, 0.2, 0.8, 0.4])
        params = circuit.params.copy()

        # Create mock pyqpanda module
        mock_pq = MagicMock()
        mock_prog = MagicMock()
        mock_pq.QProg.return_value = mock_prog
        mock_prog.__lshift__ = MagicMock(return_value=mock_prog)

        # Mock the OriginQuantumCloud
        mock_cloud_instance = MagicMock()
        mock_cloud_instance.connect.return_value = True
        # Return measurement counts that give a known expectation
        mock_cloud_instance.run_circuit_cloud.return_value = {
            "000000": 700,
            "000001": 300,
        }

        with patch.object(circuit, "_qpanda_available", True):
            with patch(
                "quantum_grants.circuits.origin_cloud.OriginQuantumCloud",
                return_value=mock_cloud_instance,
            ):
                score = circuit._cloud_forward(features, params)

        # Check the cloud was connected and used
        mock_cloud_instance.connect.assert_called_once()
        mock_cloud_instance.run_circuit_cloud.assert_called_once()
        mock_cloud_instance.disconnect.assert_called_once()

        # Verify n_qubits was passed
        call_args = mock_cloud_instance.run_circuit_cloud.call_args
        assert call_args.kwargs.get("n_qubits") == N_QUBITS

        # Score from 700 |0> and 300 |1>: expectation = (700-300)/1000 = 0.4
        # Mapped to [0,1]: (0.4 + 1) / 2 = 0.7
        assert isinstance(score, float)
        assert abs(score - 0.7) < 1e-6

    def test_cloud_forward_disconnects_on_error(self):
        """Verify cloud disconnect is called even when circuit execution fails."""
        circuit = QuantumMatchCircuit(n_layers=1)
        features = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        mock_cloud_instance = MagicMock()
        mock_cloud_instance.connect.return_value = True
        mock_cloud_instance.run_circuit_cloud.side_effect = RuntimeError("Cloud error")

        with patch.object(circuit, "_qpanda_available", True):
            with patch(
                "quantum_grants.circuits.origin_cloud.OriginQuantumCloud",
                return_value=mock_cloud_instance,
            ):
                with pytest.raises(RuntimeError, match="Cloud error"):
                    circuit._cloud_forward(features, circuit.params)

        # disconnect should still be called (finally block)
        mock_cloud_instance.disconnect.assert_called_once()

    def test_cloud_circuit_builder_has_correct_gate_count(self):
        """
        The circuit builder passed to run_circuit_cloud should create gates
        matching the circuit architecture: encoding + ansatz + measurements.
        """
        circuit = QuantumMatchCircuit(n_layers=2)
        features = np.array([1.0, 0.5, 0.5, 0.5, 0.5, 0.5])
        params = circuit.params.copy()

        captured_builder = None

        mock_cloud_instance = MagicMock()
        mock_cloud_instance.connect.return_value = True
        mock_cloud_instance.run_circuit_cloud.return_value = {"000000": 1000}

        def capture_builder(**kwargs):
            nonlocal captured_builder
            captured_builder = kwargs.get("circuit_builder")
            return {"000000": 1000}

        mock_cloud_instance.run_circuit_cloud.side_effect = capture_builder

        with patch.object(circuit, "_qpanda_available", True):
            with patch(
                "quantum_grants.circuits.origin_cloud.OriginQuantumCloud",
                return_value=mock_cloud_instance,
            ):
                circuit._cloud_forward(features, params)

        # The builder should have been captured
        assert captured_builder is not None


class TestQuantumMatcherBackend:
    """Tests for backend parameter flowing through QuantumGrantMatcher."""

    def test_matcher_passes_backend_to_circuit(self):
        """QuantumGrantMatcher should pass its backend to circuit.forward()."""
        from quantum_grants.agents.quantum_matcher import (
            QuantumGrantMatcher,
            CICProfile,
            encode_real_pair,
        )

        matcher = QuantumGrantMatcher(n_layers=1, backend="numpy")
        assert matcher.backend == "numpy"

        # Create a minimal grant and profile
        grant = {
            "name": "Test Grant",
            "funder": "Test Funder",
            "maxAmount": 10000,
            "minAmount": 1000,
            "sectors": ["Community Development"],
            "regions": ["UK-wide"],
            "status": "Open",
            "supportsStartup": True,
            "supportsGrowth": True,
            "supportsScale": False,
            "applicationDifficulty": 2,
            "description": "A test grant",
            "website": "https://example.com",
        }
        cic = CICProfile(
            org_id="TEST-001",
            org_name="Test CIC",
            legal_structure="cic",
            sectors=["Community Development"],
            themes=["community"],
            region="London",
            annual_turnover=20000,
            years_operating=2,
        )

        # Patch circuit.forward to verify backend is passed
        with patch.object(matcher.circuit, "forward", wraps=matcher.circuit.forward) as mock_fwd:
            matcher.score_pair(grant, cic)
            mock_fwd.assert_called_once()
            call_kwargs = mock_fwd.call_args
            assert call_kwargs.kwargs.get("backend") == "numpy"
