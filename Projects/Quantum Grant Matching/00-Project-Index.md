# Quantum Grant Matching — Project Index

> **Status:** R&D / Experimental
> **Vault:** InclusiFund-Research (NOT production)
> **Created:** 2026-03-11
> **Data:** SYNTHETIC ONLY

---

## Overview

Quantum-classical hybrid system for matching grant opportunities to applicant organisations. Uses variational quantum circuits (VQCs) to encode multi-dimensional compatibility scoring.

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Grant +    │────▶│  Classical       │────▶│  Quantum     │
│   Applicant  │     │  Feature Encoder │     │  Circuit     │
│   Data       │     │  (6-dim vector)  │     │  (6 qubits)  │
└──────────────┘     └──────────────────┘     └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  Classical   │
                                              │  Calibration │
                                              │  Layer       │
                                              └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  Match Score  │
                                              │  [0, 1]      │
                                              └──────────────┘
```

## Key Links

- **Python code:** `quantum_grants/`
- **Notebooks:** `notebooks/01_quantum_grant_matching.ipynb`
- **Training logs:** `Research/Training Logs/`
- **Agents:** [[Agent-9-Quantum-Matcher]]
- **Research notes:** `Research/Quantum Research/`
- **Synthetic data:** `Data/Quantum/`

## Feature Vector

| Index | Feature | Range | Description |
|-------|---------|-------|-------------|
| 0 | Eligibility | {0, 1} | Hard eligibility criteria pass/fail |
| 1 | Sector overlap | [0, 1] | Applicant sector in grant's eligible list |
| 2 | Theme overlap | [0, 1] | Jaccard similarity of themes |
| 3 | Capacity | [0, 1] | Composite organisational readiness |
| 4 | Turnover ratio | [0, 1] | Applicant turnover / grant max |
| 5 | Experience | [0, 1] | Years operating / 30 |

## R&D Phases

### Phase 1: Foundation (Current)
- [x] Folder structure created
- [x] Synthetic data generator
- [x] Quantum circuit (numpy simulation)
- [x] Feature encoder
- [x] Hybrid matcher
- [x] Training loop
- [x] Convex integration placeholder
- [x] Jupyter notebook
- [ ] Install Origin Quantum SDK
- [ ] Run first training

### Phase 2: Optimisation (Weeks 2-3)
- [ ] Hyperparameter sweep
- [ ] Classical baseline comparison
- [ ] Quantum advantage measurement
- [ ] Origin Quantum Cloud experiments
- [ ] Larger synthetic datasets

### Phase 3: Production Migration
- [ ] Connect to production Convex backend
- [ ] Replace synthetic data with anonymised real data
- [ ] Integration with Agent 9 (production swarm)
- [ ] Performance benchmarks

## Safety Notes

- This vault contains NO client data
- All data is synthetic/generated
- Safe for cloud quantum computing
- Origin Quantum Cloud receives only numerical vectors
- Production migration requires separate approval
