"""
Hybrid quantum-classical grant matcher.

Combines the quantum circuit's output with a classical post-processing
layer for final match scoring and ranking.
"""

from __future__ import annotations

import numpy as np
from typing import Optional

from quantum_grants.circuits.grant_circuit import QuantumMatchCircuit
from quantum_grants.models.feature_encoder import encode_pair, MatchFeatures
from quantum_grants.data.synthetic import SyntheticGrant, SyntheticApplicant


class HybridGrantMatcher:
    """
    Two-stage matcher:
    1. Quantum circuit produces a raw compatibility score
    2. Classical layer applies calibration and threshold

    The classical layer learns a simple affine transformation:
        final_score = sigmoid(w * quantum_score + b)
    """

    def __init__(self, n_layers: int = 2, threshold: float = 0.5):
        self.circuit = QuantumMatchCircuit(n_layers=n_layers)
        self.threshold = threshold
        self.classical_weight = 1.0
        self.classical_bias = 0.0

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def predict_score(self, grant: SyntheticGrant, applicant: SyntheticApplicant) -> float:
        """Predict match score for a single pair."""
        features = encode_pair(grant, applicant)
        quantum_score = self.circuit.forward(features.to_array())
        calibrated = self._sigmoid(
            self.classical_weight * quantum_score + self.classical_bias
        )
        return float(calibrated)

    def predict_match(self, grant: SyntheticGrant, applicant: SyntheticApplicant) -> bool:
        """Binary match prediction."""
        return self.predict_score(grant, applicant) >= self.threshold

    def rank_grants(
        self,
        grants: list[SyntheticGrant],
        applicant: SyntheticApplicant,
        top_k: Optional[int] = None,
    ) -> list[tuple[SyntheticGrant, float]]:
        """Rank grants by compatibility with an applicant."""
        scored = [(g, self.predict_score(g, applicant)) for g in grants]
        scored.sort(key=lambda x: x[1], reverse=True)
        if top_k:
            scored = scored[:top_k]
        return scored

    def rank_applicants(
        self,
        grant: SyntheticGrant,
        applicants: list[SyntheticApplicant],
        top_k: Optional[int] = None,
    ) -> list[tuple[SyntheticApplicant, float]]:
        """Rank applicants by compatibility with a grant."""
        scored = [(a, self.predict_score(grant, a)) for a in applicants]
        scored.sort(key=lambda x: x[1], reverse=True)
        if top_k:
            scored = scored[:top_k]
        return scored

    def get_params(self) -> dict:
        """Export all trainable parameters."""
        return {
            "quantum_params": self.circuit.params.tolist(),
            "classical_weight": self.classical_weight,
            "classical_bias": self.classical_bias,
            "threshold": self.threshold,
        }

    def set_params(self, params: dict) -> None:
        """Load trainable parameters."""
        self.circuit.params = np.array(params["quantum_params"])
        self.classical_weight = params["classical_weight"]
        self.classical_bias = params["classical_bias"]
        self.threshold = params["threshold"]
