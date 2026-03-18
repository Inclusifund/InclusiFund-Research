"""
Training loop for the hybrid quantum-classical grant matcher.

Uses parameter-shift gradient estimation on the quantum circuit
and standard gradient descent on the classical layer.
"""

from __future__ import annotations

import json
import math
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field

from quantum_grants.circuits.grant_circuit import QuantumMatchCircuit
from quantum_grants.models.feature_encoder import encode_pair
from quantum_grants.data.synthetic import (
    SyntheticGrant, SyntheticApplicant, SyntheticMatchLabel,
    generate_dataset,
)


@dataclass
class TrainingConfig:
    n_layers: int = 2
    learning_rate: float = 0.05
    n_epochs: int = 20
    batch_size: int = 32
    seed: int = 42
    log_dir: str = "Research/Training Logs"
    n_grants: int = 20
    n_applicants: int = 40


@dataclass
class TrainingLog:
    epoch: int
    loss: float
    accuracy: float
    elapsed_seconds: float
    n_samples: int


def binary_cross_entropy(predicted: float, target: float, eps: float = 1e-7) -> float:
    p = np.clip(predicted, eps, 1 - eps)
    return -(target * math.log(p) + (1 - target) * math.log(1 - p))


def train(config: TrainingConfig | None = None) -> list[TrainingLog]:
    """Run a training loop on synthetic data."""

    if config is None:
        config = TrainingConfig()

    np.random.seed(config.seed)

    print("=" * 60)
    print("QUANTUM GRANT MATCHER — TRAINING (R&D)")
    print("=" * 60)
    print(f"Layers: {config.n_layers}")
    print(f"LR: {config.learning_rate}")
    print(f"Epochs: {config.n_epochs}")
    print(f"Dataset: {config.n_grants} grants x {config.n_applicants} applicants")
    print()

    grants, applicants, labels = generate_dataset(
        n_grants=config.n_grants,
        n_applicants=config.n_applicants,
        seed=config.seed,
    )

    label_map = {(l.grant_id, l.org_id): l for l in labels}

    circuit = QuantumMatchCircuit(n_layers=config.n_layers)
    params = circuit.params.copy()

    logs: list[TrainingLog] = []

    for epoch in range(config.n_epochs):
        t0 = time.time()

        indices = list(range(len(labels)))
        np.random.shuffle(indices)
        batch_indices = indices[: config.batch_size]

        total_loss = 0.0
        correct = 0
        grad_accum = np.zeros_like(params)

        for idx in batch_indices:
            label = labels[idx]
            grant = next(g for g in grants if g.grant_id == label.grant_id)
            applicant = next(a for a in applicants if a.org_id == label.org_id)

            features = encode_pair(grant, applicant).to_array()
            predicted = circuit.forward(features, params)
            target = label.overall_match

            loss = binary_cross_entropy(predicted, target)
            total_loss += loss

            if (predicted >= 0.5) == label.is_match:
                correct += 1

            grad = circuit.gradient(features, params)
            error = predicted - target
            grad_accum += error * grad

        avg_loss = total_loss / config.batch_size
        accuracy = correct / config.batch_size
        grad_accum /= config.batch_size

        params -= config.learning_rate * grad_accum

        elapsed = time.time() - t0

        log = TrainingLog(
            epoch=epoch + 1,
            loss=round(avg_loss, 6),
            accuracy=round(accuracy, 4),
            elapsed_seconds=round(elapsed, 2),
            n_samples=config.batch_size,
        )
        logs.append(log)

        print(
            f"Epoch {log.epoch:3d}/{config.n_epochs} | "
            f"Loss: {log.loss:.4f} | "
            f"Acc: {log.accuracy:.2%} | "
            f"Time: {log.elapsed_seconds:.1f}s"
        )

    circuit.params = params

    log_path = Path(config.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    log_file = log_path / f"training_{timestamp}.json"
    with open(log_file, "w") as f:
        json.dump(
            {
                "config": {
                    "n_layers": config.n_layers,
                    "learning_rate": config.learning_rate,
                    "n_epochs": config.n_epochs,
                    "batch_size": config.batch_size,
                    "seed": config.seed,
                },
                "logs": [
                    {
                        "epoch": l.epoch,
                        "loss": l.loss,
                        "accuracy": l.accuracy,
                        "elapsed_seconds": l.elapsed_seconds,
                    }
                    for l in logs
                ],
                "final_params": params.tolist(),
            },
            f,
            indent=2,
        )
    print(f"\nTraining log saved to: {log_file}")

    return logs


if __name__ == "__main__":
    train()
