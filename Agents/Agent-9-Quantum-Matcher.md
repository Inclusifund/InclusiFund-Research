# Agent 9: Quantum Grant Matcher (Prototype)

> **Status:** Prototype / R&D
> **Swarm Role:** Grant-applicant matching via quantum circuits
> **Production Equivalent:** Will integrate with InclusiFund swarm Agent 9

---

## Purpose

Uses variational quantum circuits to score grant-applicant compatibility across multiple dimensions simultaneously, potentially finding non-obvious matches that classical algorithms miss.

## Capabilities (R&D)

1. **Feature Encoding** — Transforms grant + applicant data into 6-dimensional normalised vectors
2. **Quantum Scoring** — Runs variational quantum circuits to produce compatibility scores
3. **Ranking** — Ranks grants for an applicant (or applicants for a grant) by quantum score
4. **Training** — Optimises circuit parameters using parameter-shift gradients on synthetic data

## Quantum Circuit Specification

- **Qubits:** 6 (one per feature dimension)
- **Encoding:** Angle encoding (Ry rotations)
- **Ansatz:** Hardware-efficient variational (Rx, Ry, Rz + CNOT chain)
- **Layers:** Configurable (default 2)
- **Measurement:** Z-expectation on qubit 0
- **Parameters:** `n_layers × n_qubits × 3` (default 36)

## Integration Points

| Connection | Current (R&D) | Production (Future) |
|------------|----------------|---------------------|
| Data source | Synthetic generator | Convex database |
| Compute | numpy simulation | Origin Quantum Cloud |
| Results storage | Local JSON | Convex mutations |
| Agent orchestration | Standalone | Swarm Agent 9 |

## How to Use

```python
from quantum_grants.models.hybrid_matcher import HybridGrantMatcher
from quantum_grants.data.synthetic import generate_dataset

grants, applicants, _ = generate_dataset(n_grants=50, n_applicants=100)
matcher = HybridGrantMatcher(n_layers=2)

# Rank grants for an applicant
ranked = matcher.rank_grants(grants, applicants[0], top_k=5)
for grant, score in ranked:
    print(f"{grant.programme_name}: {score:.4f}")
```

## Training

```python
from quantum_grants.training.trainer import train, TrainingConfig

config = TrainingConfig(n_epochs=20, n_grants=20, n_applicants=40)
logs = train(config)
```

## Migration Checklist

- [ ] QPanda SDK installed and tested
- [ ] Origin Quantum Cloud account configured
- [ ] Quantum advantage demonstrated on synthetic data
- [ ] Convex schema deployed to production
- [ ] Real data pipeline established (anonymised)
- [ ] Agent 9 integration tested
- [ ] Performance benchmarks documented
