"""
Training loop using Convex grants and organisation profiles.

Creates labelled grant-organisation pairs using domain heuristics
(eligibility, sector fit, funder requirements) and trains the quantum
circuit on grant matching patterns.

Outputs trained weights to Data/Quantum/models/ for Agent 9.
"""

from __future__ import annotations

import json
import math
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass

from quantum_grants.circuits.grant_circuit import QuantumMatchCircuit
from quantum_grants.agents.quantum_matcher import (
    CICProfile, encode_real_pair,
    _region_match, _sector_overlap, _structure_eligible,
)
from quantum_grants.convex_integration.client import ConvexClient
from quantum_grants.data.intel_labels import (
    get_blocked_label, compute_characteristic_label,
)


# --- Demo profiles (fictional organisations for demonstration) ---

DEMO_PROFILES = [
    CICProfile(
        org_id="DEMO-001",
        org_name="Demo Youth CIC",
        legal_structure="cic",
        sectors=["Youth Services", "Health & Wellbeing", "Community Development"],
        themes=["mentoring", "young people", "mental health", "wellbeing", "disadvantage"],
        region="London",
        annual_turnover=0,
        years_operating=1,
        staff_count=3,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=0,
        beneficiaries=["children", "young people", "families"],
    ),
    CICProfile(
        org_id="DEMO-002",
        org_name="Demo Health Charity",
        legal_structure="cio",
        sectors=["Health & Wellbeing", "Community Development", "Disability"],
        themes=["health", "lived experience", "awareness", "support", "peer networks"],
        region="London",
        annual_turnover=0,
        years_operating=0.3,
        staff_count=0,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=0,
        beneficiaries=["people with long-term conditions", "families", "carers"],
    ),
    CICProfile(
        org_id="DEMO-003",
        org_name="Demo Environmental Co-op",
        legal_structure="clg",
        sectors=["Environment", "Community Development", "Education & Training"],
        themes=["sustainability", "food growing", "community", "education", "conservation"],
        region="South East",
        annual_turnover=150_000,
        years_operating=7,
        staff_count=10,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=4,
        beneficiaries=["local community", "volunteers", "visitors"],
    ),
    CICProfile(
        org_id="DEMO-004",
        org_name="Demo Wellbeing CIC",
        legal_structure="cic",
        sectors=["Health & Wellbeing", "Arts & Culture"],
        themes=["wellbeing", "creative arts", "mindfulness", "workshops", "inclusion"],
        region="South West",
        annual_turnover=0,
        years_operating=0.5,
        staff_count=2,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=0,
        beneficiaries=["adults", "communities", "young people"],
    ),
    CICProfile(
        org_id="DEMO-005",
        org_name="Demo Education Trust",
        legal_structure="charity",
        sectors=["Education & Training", "Youth Services"],
        themes=["literacy", "tutoring", "after-school", "digital skills", "disadvantage"],
        region="North West",
        annual_turnover=85_000,
        years_operating=4,
        staff_count=6,
        has_safeguarding_policy=True,
        has_financial_controls=True,
        previous_grants=3,
        beneficiaries=["children", "young people", "families"],
    ),
]


def compute_real_label(grant: dict, cic: CICProfile) -> float:
    """
    Compute a ground-truth match score for a grant-organisation pair.

    Checks the blocked funder list first (returns 0.0 for blocked pairs),
    then uses characteristic-based labels from funder policies, and falls
    back to domain heuristics:
    - Eligibility (region, structure, stage) = 35%
    - Sector/theme alignment = 30%
    - Organisational capacity = 20%
    - Amount fit = 15%
    """
    grant_name = grant.get("name", "")
    grant_funder = grant.get("funder", "")

    # --- Check blocked funders first ---
    blocked = get_blocked_label(
        grant_name, grant_funder,
        legal_structure=cic.legal_structure,
        region=cic.region,
        annual_turnover=cic.annual_turnover,
        years_operating=cic.years_operating,
    )
    if blocked is not None:
        return blocked

    # --- Check for characteristic-based label ---
    char_label = compute_characteristic_label(
        grant_name, grant_funder,
        legal_structure=cic.legal_structure,
        annual_turnover=cic.annual_turnover,
        years_operating=cic.years_operating,
    )
    if char_label is not None:
        return char_label

    # --- Heuristic fallback ---
    features = encode_real_pair(grant, cic)

    eligibility = features[0]
    sector = features[1]
    theme = features[2]
    capacity = features[3]
    turnover_ratio = features[4]

    # Alignment composite
    alignment = 0.6 * sector + 0.4 * theme

    # Amount fit bonus: penalise if grant is way too large for org
    max_amount = grant.get("maxAmount", 0)
    min_amount = grant.get("minAmount", 0)
    if max_amount > 0 and cic.annual_turnover > 0:
        ratio = cic.annual_turnover / max_amount
        amount_fit = min(ratio, 1.0) if ratio > 0.05 else 0.3
    elif max_amount > 0 and max_amount <= 20_000:
        amount_fit = 0.8  # small grants OK for pre-revenue
    elif max_amount == 0:
        amount_fit = 0.5  # unknown
    else:
        amount_fit = 0.4  # large grant, no income = risky

    # Startup penalty for grants requiring track record
    if not grant.get("supportsStartup", False) and cic.years_operating < 2:
        eligibility *= 0.2

    # CIC/charity structure check
    desc_lower = grant.get("description", "").lower()
    if "charity" in desc_lower and cic.legal_structure not in ("charity", "cio"):
        eligibility *= 0.5
    if "registered charity" in desc_lower and cic.legal_structure == "cic":
        eligibility *= 0.3

    # Composite score
    score = (
        0.35 * eligibility
        + 0.30 * alignment
        + 0.20 * capacity
        + 0.15 * amount_fit
    )

    return float(np.clip(score, 0, 1))


@dataclass
class RealTrainingConfig:
    n_layers: int = 2
    learning_rate: float = 0.03
    n_epochs: int = 30
    batch_size: int = 64
    seed: int = 42
    use_cached_grants: bool = True


def train_on_real_data(config: RealTrainingConfig | None = None) -> dict:
    """
    Train the quantum circuit on real Convex grants + client profiles.

    Returns dict with trained params, logs, and model path.
    """
    if config is None:
        config = RealTrainingConfig()

    np.random.seed(config.seed)

    print("=" * 60)
    print("QUANTUM GRANT MATCHER — REAL DATA TRAINING")
    print("=" * 60)

    # Load grants
    client = ConvexClient()
    if config.use_cached_grants:
        try:
            grants = client.load_cached_grants()
        except FileNotFoundError:
            grants = client.fetch_all_grants()
    else:
        grants = client.fetch_all_grants()

    print(f"Grants loaded: {len(grants)}")
    print(f"Client profiles: {len(DEMO_PROFILES)}")

    # Build training pairs
    pairs = []
    for grant in grants:
        for cic in DEMO_PROFILES:
            features = encode_real_pair(grant, cic)
            label = compute_real_label(grant, cic)
            pairs.append((features, label, grant.get("name", "?"), cic.org_name))

    total = len(pairs)
    positives = sum(1 for _, l, _, _ in pairs if l >= 0.5)
    print(f"Training pairs: {total}")
    print(f"Positive (score >= 0.5): {positives} ({100*positives/total:.1f}%)")
    print(f"Negative (score < 0.5): {total - positives} ({100*(total-positives)/total:.1f}%)")
    print()

    # Initialize circuit
    circuit = QuantumMatchCircuit(n_layers=config.n_layers)
    params = circuit.params.copy()
    classical_weight = 1.0
    classical_bias = 0.0

    def sigmoid(x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def forward(features, params):
        q_score = circuit._numpy_simulate(features, params)
        return float(sigmoid(classical_weight * q_score + classical_bias))

    def bce(predicted, target, eps=1e-7):
        p = np.clip(predicted, eps, 1 - eps)
        return -(target * math.log(p) + (1 - target) * math.log(1 - p))

    # Numerical gradient helper for classical params
    eps_classical = 1e-4

    def batch_loss(features_list, targets_list, q_params, cw, cb):
        """Compute average BCE loss over a batch."""
        total = 0.0
        for feat, tgt in zip(features_list, targets_list):
            q_score = circuit._numpy_simulate(feat, q_params)
            pred = float(sigmoid(cw * q_score + cb))
            total += bce(pred, tgt)
        return total / len(features_list)

    logs = []
    print()

    for epoch in range(config.n_epochs):
        t0 = time.time()

        indices = list(range(total))
        np.random.shuffle(indices)
        batch = indices[:config.batch_size]

        total_loss = 0.0
        correct = 0
        grad_accum = np.zeros_like(params)

        # Collect batch data for classical param gradient
        batch_features = []
        batch_targets = []

        for idx in batch:
            features, target, _, _ = pairs[idx]
            batch_features.append(features)
            batch_targets.append(target)

            predicted = forward(features, params)
            loss = bce(predicted, target)
            total_loss += loss

            is_match_pred = predicted >= 0.5
            is_match_true = target >= 0.5
            if is_match_pred == is_match_true:
                correct += 1

            # Parameter-shift gradient for quantum params
            grad = circuit.gradient(features, params)
            error = predicted - target
            grad_accum += error * grad

        avg_loss = total_loss / config.batch_size
        accuracy = correct / config.batch_size
        grad_accum /= config.batch_size
        params -= config.learning_rate * grad_accum

        # --- Numerical gradient for classical_weight and classical_bias ---
        # Gradient for classical_weight
        loss_w_plus = batch_loss(
            batch_features, batch_targets, params,
            classical_weight + eps_classical, classical_bias
        )
        loss_w_minus = batch_loss(
            batch_features, batch_targets, params,
            classical_weight - eps_classical, classical_bias
        )
        grad_w = (loss_w_plus - loss_w_minus) / (2 * eps_classical)

        # Gradient for classical_bias
        loss_b_plus = batch_loss(
            batch_features, batch_targets, params,
            classical_weight, classical_bias + eps_classical
        )
        loss_b_minus = batch_loss(
            batch_features, batch_targets, params,
            classical_weight, classical_bias - eps_classical
        )
        grad_b = (loss_b_plus - loss_b_minus) / (2 * eps_classical)

        # Update classical params
        classical_weight -= config.learning_rate * grad_w
        classical_bias -= config.learning_rate * grad_b

        elapsed = time.time() - t0

        log_entry = {
            "epoch": epoch + 1,
            "loss": round(avg_loss, 6),
            "accuracy": round(accuracy, 4),
            "classical_weight": round(classical_weight, 6),
            "classical_bias": round(classical_bias, 6),
            "elapsed_s": round(elapsed, 2),
        }
        logs.append(log_entry)

        print(
            f"Epoch {epoch+1:3d}/{config.n_epochs} | "
            f"Loss: {avg_loss:.4f} | "
            f"Acc: {accuracy:.2%} | "
            f"cw: {classical_weight:.4f} cb: {classical_bias:.4f} | "
            f"Time: {elapsed:.1f}s"
        )

    circuit.params = params

    # Save model
    model_dir = Path("Data/Quantum/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    model_path = model_dir / f"quantum_matcher_real_{timestamp}.json"

    model_data = {
        "quantum_params": params.tolist(),
        "classical_weight": classical_weight,
        "classical_bias": classical_bias,
        "threshold": 0.5,
        "n_layers": config.n_layers,
        "training": {
            "config": {
                "n_layers": config.n_layers,
                "learning_rate": config.learning_rate,
                "n_epochs": config.n_epochs,
                "batch_size": config.batch_size,
                "seed": config.seed,
            },
            "n_grants": len(grants),
            "n_clients": len(DEMO_PROFILES),
            "n_pairs": total,
            "final_loss": logs[-1]["loss"],
            "final_accuracy": logs[-1]["accuracy"],
            "logs": logs,
        },
    }

    with open(model_path, "w") as f:
        json.dump(model_data, f, indent=2)

    # Also save as "latest" for easy loading
    latest_path = model_dir / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(model_data, f, indent=2)

    # Score distribution analysis
    all_scores = []
    for features, _, _, _ in pairs:
        q_score = circuit._numpy_simulate(features, params)
        score = float(sigmoid(classical_weight * q_score + classical_bias))
        all_scores.append(score)
    all_scores_arr = np.array(all_scores)

    print()
    print("=" * 60)
    print("SCORE DISTRIBUTION (post-training)")
    print(f"  Min:    {all_scores_arr.min():.4f}")
    print(f"  Max:    {all_scores_arr.max():.4f}")
    print(f"  Mean:   {all_scores_arr.mean():.4f}")
    print(f"  Std:    {all_scores_arr.std():.4f}")
    print(f"  Median: {np.median(all_scores_arr):.4f}")
    # Histogram buckets
    buckets = [0, 0.2, 0.4, 0.6, 0.8, 1.01]
    bucket_labels = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
    for i in range(len(bucket_labels)):
        count = int(np.sum((all_scores_arr >= buckets[i]) & (all_scores_arr < buckets[i + 1])))
        bar = "#" * (count * 40 // len(all_scores))
        print(f"  {bucket_labels[i]}: {count:4d} {bar}")
    print(f"  Classical weight: {classical_weight:.4f}")
    print(f"  Classical bias:   {classical_bias:.4f}")
    print("=" * 60)

    print()
    print(f"Model saved: {model_path}")
    print(f"Latest link: {latest_path}")
    print(f"Final — Loss: {logs[-1]['loss']:.4f}, Accuracy: {logs[-1]['accuracy']:.2%}")

    return {
        "model_path": str(model_path),
        "latest_path": str(latest_path),
        "params": params,
        "classical_weight": classical_weight,
        "classical_bias": classical_bias,
        "logs": logs,
        "score_distribution": {
            "min": float(all_scores_arr.min()),
            "max": float(all_scores_arr.max()),
            "mean": float(all_scores_arr.mean()),
            "std": float(all_scores_arr.std()),
        },
    }


if __name__ == "__main__":
    train_on_real_data()
