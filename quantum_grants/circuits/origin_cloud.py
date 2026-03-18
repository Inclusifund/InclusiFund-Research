"""
Origin Quantum Cloud interface.

Connects to Origin Quantum's cloud platform for running circuits
on real quantum hardware and high-fidelity simulators.

API key loaded from .env (never hardcoded).
"""

from __future__ import annotations

from typing import Optional
from quantum_grants.config import get_origin_quantum_api_key


def check_cloud_status() -> dict:
    """
    Check the status of Origin Quantum Cloud dependencies.

    Returns a dict with:
    - qpanda_installed: bool
    - api_key_configured: bool
    - api_key_prefix: str or None (first 8 chars for verification)
    - ready: bool (True only if both qpanda and API key are available)
    - message: str (human-readable status summary)
    """
    import os

    # Check pyqpanda
    try:
        import pyqpanda  # noqa: F401
        qpanda_installed = True
    except ImportError:
        qpanda_installed = False

    # Check API key
    api_key = os.environ.get("ORIGIN_QUANTUM_API_KEY", "")
    if not api_key:
        try:
            from quantum_grants.config import get_origin_quantum_api_key
            api_key = get_origin_quantum_api_key()
        except Exception:
            api_key = ""

    api_key_configured = bool(api_key)
    api_key_prefix = api_key[:8] if api_key else None

    ready = qpanda_installed and api_key_configured

    # Build message
    parts = []
    if qpanda_installed:
        parts.append("pyqpanda: installed")
    else:
        parts.append("pyqpanda: NOT installed (pip install pyqpanda)")
    if api_key_configured:
        parts.append(f"API key: configured ({api_key_prefix}...)")
    else:
        parts.append("API key: NOT configured (set ORIGIN_QUANTUM_API_KEY)")
    if ready:
        parts.append("Status: READY for cloud execution")
    else:
        parts.append("Status: cloud execution unavailable, numpy fallback active")

    return {
        "qpanda_installed": qpanda_installed,
        "api_key_configured": api_key_configured,
        "api_key_prefix": api_key_prefix,
        "ready": ready,
        "message": " | ".join(parts),
    }


class OriginQuantumCloud:
    """
    Interface to Origin Quantum Cloud services.

    Supports:
    - Cloud simulator (high qubit count, noiseless)
    - Real quantum hardware (limited qubits, noisy)
    - Hybrid quantum-classical jobs

    Usage:
        cloud = OriginQuantumCloud()
        cloud.connect()
        result = cloud.run_circuit(circuit_def, shots=1000)
    """

    def __init__(self):
        self._api_key: Optional[str] = None
        self._connected = False
        self._qpanda_available = self._check_qpanda()

    @staticmethod
    def _check_qpanda() -> bool:
        try:
            import pyqpanda  # noqa: F401
            return True
        except ImportError:
            return False

    def connect(self) -> bool:
        """Establish connection to Origin Quantum Cloud."""
        self._api_key = get_origin_quantum_api_key()

        if self._qpanda_available:
            import pyqpanda as pq
            self._machine = pq.QCloud()
            self._machine.init_qvm(self._api_key)
            self._connected = True
            print("Connected to Origin Quantum Cloud via QPanda")
            return True
        else:
            print(
                "QPanda not installed. API key loaded but cannot connect.\n"
                "Install pyqpanda to use Origin Quantum Cloud:\n"
                "  pip install pyqpanda\n"
                "\n"
                "Or use the Origin Quantum Cloud Jupyter environment\n"
                "where pyqpanda is pre-installed."
            )
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def run_circuit_cloud(
        self,
        n_qubits: int,
        circuit_builder: callable,
        shots: int = 1000,
        backend: str = "simulator",
    ) -> dict:
        """
        Run a circuit on Origin Quantum Cloud.

        Args:
            n_qubits: Number of qubits
            circuit_builder: Function that builds the circuit given (machine, qubits, cbits)
            shots: Number of measurement shots
            backend: "simulator" or "real_hardware"

        Returns:
            Dict of measurement results {bitstring: count}
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")

        import pyqpanda as pq

        qubits = self._machine.qAlloc_many(n_qubits)
        cbits = self._machine.cAlloc_many(n_qubits)

        prog = circuit_builder(self._machine, qubits, cbits)

        if backend == "simulator":
            result = self._machine.full_amplitude_measure(prog, shots)
        else:
            result = self._machine.real_chip_measure(prog, shots)

        return result

    def get_available_backends(self) -> list[str]:
        """List available quantum backends."""
        if not self._connected:
            return ["numpy_local"]
        return ["simulator", "real_hardware", "numpy_local"]

    def disconnect(self) -> None:
        """Clean up cloud connection."""
        if self._connected and self._qpanda_available:
            self._machine.finalize()
        self._connected = False


def create_grant_matching_cloud_circuit():
    """
    Factory for building the grant matching circuit on Origin Quantum Cloud.

    Returns a circuit builder function compatible with OriginQuantumCloud.run_circuit_cloud().

    This is designed to be uploaded to the Origin Quantum Cloud Jupyter notebook
    at console.originqc.com.cn.
    """

    def build_circuit(machine, qubits, cbits):
        """Build the variational grant matching circuit."""
        import pyqpanda as pq

        prog = pq.QProg()

        # Feature encoding (placeholder — angles will be set per input)
        for i, q in enumerate(qubits):
            prog << pq.RY(q, 0.0)  # Will be parameterised

        # Ansatz layer 1
        for q in qubits:
            prog << pq.RX(q, 0.0)
            prog << pq.RY(q, 0.0)
            prog << pq.RZ(q, 0.0)

        # Entanglement
        for i in range(len(qubits) - 1):
            prog << pq.CNOT(qubits[i], qubits[i + 1])

        # Ansatz layer 2
        for q in qubits:
            prog << pq.RX(q, 0.0)
            prog << pq.RY(q, 0.0)
            prog << pq.RZ(q, 0.0)

        # Measurement
        for q, c in zip(qubits, cbits):
            prog << pq.Measure(q, c)

        return prog

    return build_circuit
