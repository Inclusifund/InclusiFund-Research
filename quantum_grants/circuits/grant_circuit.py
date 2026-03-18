"""
Quantum circuits for grant matching.

Implements parameterised quantum circuits (PQCs) that encode
grant-applicant feature vectors into quantum states and measure
compatibility via entanglement and interference patterns.

Designed for Origin Quantum's QPanda / pyQPanda SDK.
Falls back to numpy simulation when QPanda is unavailable.
"""

from __future__ import annotations

import math
import numpy as np
from typing import Optional


# Feature vector layout:
# [0] eligibility_binary    (0 or 1)
# [1] sector_overlap        (0 to 1)
# [2] theme_overlap         (0 to 1)
# [3] capacity_normalised   (0 to 1)
# [4] turnover_ratio        (0 to 1, applicant_turnover / grant_max)
# [5] experience_normalised (0 to 1, years / 30)
FEATURE_DIM = 6
N_QUBITS = 6


def encode_features_to_angles(features: np.ndarray) -> np.ndarray:
    """Map normalised feature vector [0,1]^n to rotation angles [0, pi]."""
    return np.clip(features, 0, 1) * math.pi


def build_ansatz_params(n_layers: int = 2) -> np.ndarray:
    """Initialise variational parameters for the ansatz circuit."""
    n_params = n_layers * N_QUBITS * 3  # Rx, Ry, Rz per qubit per layer
    return np.random.uniform(0, 2 * math.pi, size=n_params)


class QuantumMatchCircuit:
    """
    Variational quantum circuit for grant-applicant compatibility.

    Architecture:
    1. Feature encoding layer (angle encoding)
    2. Variational ansatz (parameterised rotations + CNOT entanglement)
    3. Measurement of expectation value as match score

    When QPanda is available, runs on Origin Quantum hardware/simulator.
    Otherwise falls back to statevector simulation with numpy.
    """

    def __init__(self, n_layers: int = 2):
        self.n_layers = n_layers
        self.n_qubits = N_QUBITS
        self.params = build_ansatz_params(n_layers)
        self._qpanda_available = self._check_qpanda()

    @staticmethod
    def _check_qpanda() -> bool:
        try:
            import pyqpanda  # noqa: F401
            return True
        except ImportError:
            return False

    def _numpy_simulate(
        self, features: np.ndarray, params: np.ndarray
    ) -> float:
        """Statevector simulation using numpy (no QPanda dependency)."""
        n = self.n_qubits
        state = np.zeros(2**n, dtype=complex)
        state[0] = 1.0  # |000...0>

        angles = encode_features_to_angles(features)

        # Feature encoding: Ry rotations
        for qubit in range(n):
            theta = angles[qubit] if qubit < len(angles) else 0.0
            cos_half = math.cos(theta / 2)
            sin_half = math.sin(theta / 2)

            new_state = np.zeros_like(state)
            for basis in range(2**n):
                bit = (basis >> qubit) & 1
                partner = basis ^ (1 << qubit)
                if bit == 0:
                    new_state[basis] += cos_half * state[basis]
                    new_state[partner] += sin_half * state[basis]
                else:
                    new_state[basis] += cos_half * state[basis]
                    new_state[partner] -= sin_half * state[basis]
            state = new_state

        # Variational ansatz layers
        param_idx = 0
        for layer in range(self.n_layers):
            for qubit in range(n):
                for gate in range(3):  # Rx, Ry, Rz
                    theta = params[param_idx]
                    param_idx += 1
                    cos_half = math.cos(theta / 2)
                    sin_half = math.sin(theta / 2)

                    new_state = np.zeros_like(state)
                    for basis in range(2**n):
                        bit = (basis >> qubit) & 1
                        partner = basis ^ (1 << qubit)
                        if gate == 1:  # Ry
                            if bit == 0:
                                new_state[basis] += cos_half * state[basis]
                                new_state[partner] += sin_half * state[basis]
                            else:
                                new_state[basis] += cos_half * state[basis]
                                new_state[partner] -= sin_half * state[basis]
                        elif gate == 0:  # Rx
                            if bit == 0:
                                new_state[basis] += cos_half * state[basis]
                                new_state[partner] += -1j * sin_half * state[basis]
                            else:
                                new_state[basis] += cos_half * state[basis]
                                new_state[partner] += -1j * sin_half * state[basis]
                        else:  # Rz
                            phase = np.exp(-1j * theta / 2) if bit == 0 else np.exp(1j * theta / 2)
                            new_state[basis] += phase * state[basis]
                    state = new_state

            # CNOT entanglement: linear chain
            for qubit in range(n - 1):
                new_state = np.zeros_like(state)
                for basis in range(2**n):
                    control_bit = (basis >> qubit) & 1
                    if control_bit == 1:
                        flipped = basis ^ (1 << (qubit + 1))
                        new_state[flipped] += state[basis]
                    else:
                        new_state[basis] += state[basis]
                state = new_state

        # Measure: expectation value of Z on qubit 0
        expectation = 0.0
        for basis in range(2**n):
            bit0 = (basis >> 0) & 1
            sign = 1 - 2 * bit0  # +1 for |0>, -1 for |1>
            expectation += sign * abs(state[basis]) ** 2

        # Map from [-1, 1] to [0, 1]
        return (expectation + 1) / 2

    def forward(
        self,
        features: np.ndarray,
        params: Optional[np.ndarray] = None,
        backend: str = "auto",
    ) -> float:
        """
        Run circuit and return match score in [0, 1].

        Args:
            features: Feature vector of length FEATURE_DIM.
            params: Variational parameters (uses self.params if None).
            backend: Execution backend.
                - "auto": use QPanda if available, else numpy (default)
                - "numpy": always use numpy simulation
                - "cloud": use Origin Quantum Cloud (requires pyqpanda + API key)
        """
        if params is None:
            params = self.params

        if backend == "numpy":
            return self._numpy_simulate(features, params)
        elif backend == "cloud":
            return self._cloud_forward(features, params)
        elif backend == "auto":
            if self._qpanda_available:
                return self._qpanda_forward(features, params)
            return self._numpy_simulate(features, params)
        else:
            raise ValueError(
                f"Unknown backend '{backend}'. Choose from: auto, numpy, cloud"
            )

    def _qpanda_forward(self, features: np.ndarray, params: np.ndarray) -> float:
        """Run on Origin Quantum QPanda local simulator."""
        import pyqpanda as pq

        machine = pq.CPUQVM()
        machine.init_qvm()
        qubits = machine.qAlloc_many(self.n_qubits)
        cbits = machine.cAlloc_many(self.n_qubits)

        prog = pq.QProg()
        angles = encode_features_to_angles(features)

        # Feature encoding: Ry rotations
        for i in range(self.n_qubits):
            theta = float(angles[i]) if i < len(angles) else 0.0
            prog << pq.RY(qubits[i], theta)

        # Variational ansatz layers
        param_idx = 0
        for layer in range(self.n_layers):
            for i in range(self.n_qubits):
                prog << pq.RX(qubits[i], float(params[param_idx]))
                param_idx += 1
                prog << pq.RY(qubits[i], float(params[param_idx]))
                param_idx += 1
                prog << pq.RZ(qubits[i], float(params[param_idx]))
                param_idx += 1
            # CNOT entanglement: linear chain
            for i in range(self.n_qubits - 1):
                prog << pq.CNOT(qubits[i], qubits[i + 1])

        # Get probabilities via statevector
        machine.directly_run(prog)
        probs = machine.prob_run_dict(prog, qubits)

        # Expectation value of Z on qubit 0
        expectation = 0.0
        for bitstring, prob in probs.items():
            bit0 = int(bitstring[-1])  # least significant bit = qubit 0
            sign = 1 - 2 * bit0
            expectation += sign * prob

        machine.finalize()
        return (expectation + 1) / 2

    def _cloud_forward(self, features: np.ndarray, params: np.ndarray) -> float:
        """Run circuit on Origin Quantum Cloud simulator."""
        if not self._qpanda_available:
            raise RuntimeError(
                "Cloud backend requires pyqpanda. Install it with:\n"
                "  pip install pyqpanda\n\n"
                "Or use backend='numpy' for local simulation."
            )

        from quantum_grants.circuits.origin_cloud import OriginQuantumCloud

        cloud = OriginQuantumCloud()
        if not cloud.connect():
            raise ConnectionError(
                "Failed to connect to Origin Quantum Cloud. "
                "Check your ORIGIN_QUANTUM_API_KEY in .env."
            )

        angles = encode_features_to_angles(features)
        n_layers = self.n_layers

        def circuit_builder(machine, qubits, cbits):
            """Build the parameterised grant matching circuit for cloud execution."""
            import pyqpanda as pq

            prog = pq.QProg()

            # Feature encoding: Ry rotations
            for i in range(len(qubits)):
                theta = float(angles[i]) if i < len(angles) else 0.0
                prog << pq.RY(qubits[i], theta)

            # Variational ansatz layers
            param_idx = 0
            for layer in range(n_layers):
                for i in range(len(qubits)):
                    prog << pq.RX(qubits[i], float(params[param_idx]))
                    param_idx += 1
                    prog << pq.RY(qubits[i], float(params[param_idx]))
                    param_idx += 1
                    prog << pq.RZ(qubits[i], float(params[param_idx]))
                    param_idx += 1
                # CNOT entanglement: linear chain
                for i in range(len(qubits) - 1):
                    prog << pq.CNOT(qubits[i], qubits[i + 1])

            # Measurement
            for q, c in zip(qubits, cbits):
                prog << pq.Measure(q, c)

            return prog

        try:
            result = cloud.run_circuit_cloud(
                n_qubits=self.n_qubits,
                circuit_builder=circuit_builder,
                shots=1000,
                backend="simulator",
            )

            # Compute expectation value of Z on qubit 0 from measurement counts
            total_shots = sum(result.values())
            expectation = 0.0
            for bitstring, count in result.items():
                bit0 = int(bitstring[-1])  # least significant bit = qubit 0
                sign = 1 - 2 * bit0
                expectation += sign * (count / total_shots)

            return (expectation + 1) / 2
        finally:
            cloud.disconnect()

    def gradient(
        self, features: np.ndarray, params: Optional[np.ndarray] = None, shift: float = math.pi / 2
    ) -> np.ndarray:
        """Parameter-shift rule gradient estimation."""
        if params is None:
            params = self.params.copy()

        grads = np.zeros_like(params)
        for i in range(len(params)):
            params_plus = params.copy()
            params_plus[i] += shift
            params_minus = params.copy()
            params_minus[i] -= shift

            f_plus = self.forward(features, params_plus)
            f_minus = self.forward(features, params_minus)
            grads[i] = (f_plus - f_minus) / (2 * math.sin(shift))

        return grads
