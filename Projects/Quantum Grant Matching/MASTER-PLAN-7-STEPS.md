# Quantum Grant Matching — Revised 7-Step R&D Plan

> **Revised:** 2026-03-11
> **Status:** Active
> **Origin Quantum Cloud:** Connected (API key in .env)
> **Pre-quantum Intel:** 49 research files + 2 skills + 5 funding longlists loaded
> **Vault:** R&D only — NO client data in quantum cloud

---

## What Changed from Original Plan

The pre-quantum funding intel provides **real domain knowledge** that eliminates guesswork:

| Gap (Before) | Filled By (Intel) |
|---|---|
| Generic eligibility features | Real 10-dimension eligibility model from funder longlists |
| Random synthetic data | Intel-informed synthetic data matching real UK grant structure |
| Unknown feature importance | Fit rating patterns (HIGH/MED/LOW) from 22+ real funders |
| No validation reference | Real funder longlist tables as ground truth for scoring |
| No sector knowledge | CIC governance, asset lock, funding gaps research |
| No intermediation model | 77% intermediary funding flow analysis |

---

## The 7 Steps

### Step 1: Domain-Informed Feature Engineering
**Status:** Ready to execute
**Intel sources:** All 49 pre-vault research files

Build the feature encoder using the **10 eligibility dimensions** extracted from real funder research:

| # | Feature | Source | Encoding |
|---|---------|--------|----------|
| 1 | Legal structure | Funder longlist CIC eligibility column | One-hot → angle |
| 2 | Startup stage | "Startup Eligible?" column + turnover thresholds | Ordinal → angle |
| 3 | Geographic region | London boroughs, UK regions from intel | Binary → angle |
| 4 | Annual turnover | Real thresholds (£25k, £150k, £1.5m from longlists) | Log-normalised → angle |
| 5 | Track record | Years operating + previous grants | Normalised → angle |
| 6 | Beneficiary group | Age cohorts from funding gap analysis (16-21, 25-40) | Embedding → angle |
| 7 | Sector focus | Housing, youth, arts, mental health from intel | Overlap score → angle |
| 8 | Safeguarding policy | Binary from CIC governance research | Binary → angle |
| 9 | Governance standards | Board composition, CIC regulator requirements | Score → angle |
| 10 | Match funding | Funder requirements from longlists | Binary → angle |

**Output:** `quantum_grants/models/feature_encoder.py` (upgraded from 6 → 10 features)

**Key file:** `quantum_grants/data/intel_loader.py` — parses real funder longlists

---

### Step 2: Intel-Informed Synthetic Data Generation
**Status:** Ready to execute
**Intel sources:** Funder longlists, funding gap analysis, intermediation analysis

Generate training data that matches **real UK grant structure**:

- **Grant profiles** based on real funder characteristics (BBC CiN, Henry Smith, Ubele, Commonweal, etc.)
- **CIC profiles** based on real patterns (pre-revenue Black-led CIC, established charity, etc.)
- **Eligibility rules** from actual funder criteria (income thresholds, track record requirements)
- **Fit ratings** calibrated against real HIGH/MEDIUM/LOW distributions

**Key insight from intel:**
- 22 funders identified for one CIC → ~6 HIGH, ~5 MEDIUM, ~6 LOW, ~3 FUTURE
- This gives us a realistic class distribution (~27% high match rate)
- Much better than random synthetic data

**Output:** `quantum_grants/data/synthetic.py` (upgraded with intel-informed generator)

---

### Step 3: Quantum Circuit Design (6 → 10 qubits)
**Status:** Ready — numpy simulation local, QPanda on Origin QC Cloud
**Platform:** Origin Quantum Cloud (Jupyter workspace "Funding Project" running)

Expand circuit from 6 to 10 qubits to match the 10-feature model:

```
10 qubits → 10 eligibility dimensions
2-3 ansatz layers → ~90 trainable parameters
Linear CNOT chain → captures feature correlations
Z-expectation → match probability
```

**Run locally:** numpy simulation for development
**Run on cloud:** Origin Quantum Cloud Jupyter (pyqpanda pre-installed)

**Origin Quantum Cloud setup:**
1. API key stored in `.env` ✅
2. Cloud interface: `quantum_grants/circuits/origin_cloud.py` ✅
3. Your Jupyter workspace: "Funding Project" at `console.originqc.com.cn` ✅

**Output:** `quantum_grants/circuits/grant_circuit.py` (upgraded to 10 qubits)

---

### Step 4: Training on Synthetic Data
**Status:** Blocked by Step 1-3
**Compute:** Local numpy → Origin Quantum Cloud simulator

Training loop with parameter-shift gradients:

1. **Local training** (numpy, fast iteration): 20-50 epochs on 50 grants × 200 applicants
2. **Cloud validation** (Origin QC simulator): Verify results match local simulation
3. **Noise study** (Origin QC real hardware): Test robustness

**Metrics to track:**
- Binary cross-entropy loss
- Match accuracy (% correct HIGH/LOW prediction)
- AUC-ROC
- Comparison vs classical logistic regression baseline
- Training time per epoch (local vs cloud)

**Output:** `Research/Training Logs/` — JSON logs + Obsidian summaries

---

### Step 5: Classical Baseline Comparison
**Status:** Blocked by Step 4
**Goal:** Prove quantum advantage

Train equivalent classical models on the same features:
- Logistic regression (same 10 features)
- Random forest
- Simple neural network (10 → 16 → 1)

Compare on:
| Metric | Classical | Quantum | Delta |
|--------|-----------|---------|-------|
| Accuracy | ? | ? | ? |
| AUC-ROC | ? | ? | ? |
| Precision@5 | ? | ? | ? |
| Training time | ? | ? | ? |

**Key question from intel:** Can quantum circuits capture the non-linear eligibility interactions (e.g., "CIC eligible AND startup eligible AND in London" combinations) better than classical?

**Output:** `Research/Quantum Research/quantum_advantage_analysis.md`

---

### Step 6: Convex Integration (Synthetic Staging)
**Status:** Placeholder built ✅
**Production:** NOT connected — uses local JSON staging

Stage quantum results in a format ready for production Convex:

```
quantum_grants/convex_integration/
├── client.py          ← Placeholder mutations (stores to local JSON)
└── schema.py          ← Production Convex schema definition
```

**Production schema** (ready to deploy when migrating):
```typescript
// convex/schema.ts (future)
quantumMatches: defineTable({
  grantId: v.string(),
  orgId: v.string(),
  quantumScore: v.float64(),
  eligibilityScore: v.float64(),
  alignmentScore: v.float64(),
  capacityScore: v.float64(),
  isRecommended: v.boolean(),
  modelVersion: v.string(),
})
```

**Output:** Staged JSON results in `Data/Quantum/convex_staging/`

---

### Step 7: Documentation + Production Migration Prep
**Status:** Ongoing
**Gate:** Must demonstrate quantum advantage before production migration

Document everything for handoff:

1. **Research notes** → `Research/Quantum Research/`
2. **Training logs** → `Research/Training Logs/`
3. **Circuit design decisions** → `Research/Quantum Research/circuit_design_decisions.md`
4. **Quantum advantage evidence** → `Research/Quantum Research/quantum_advantage_analysis.md`
5. **Production migration plan** → `Projects/Quantum Grant Matching/migration-to-production.md`

**Migration checklist (Step 7 gate):**
- [ ] Quantum accuracy > 85%
- [ ] Quantum outperforms classical by > 3%
- [ ] Circuit runs successfully on Origin QC real hardware
- [ ] Convex schema tested with staging data
- [ ] No client data in any R&D file
- [ ] Production vault integration plan approved

---

## File Map (Updated)

```
InclusiFund-Research/
├── .env                                    ← Origin QC API key (NOT committed)
├── .gitignore                              ← Excludes .env, .venv, staging data
├── requirements.txt                        ← Python dependencies
│
├── pre-quantum-skills-intel/               ← YOUR INTEL (reference only)
│   ├── SKILL-funding-research copy.md      ← UK funding research skill
│   ├── SKILL_UKGOVFUND.md                  ← UK Gov funding tracker skill
│   ├── funding-intel copy/                 ← Real funding research
│   │   ├── kidz-dreams-cic--funder-longlist-2026-03-09.md
│   │   ├── vwd-alliance--funding-longlist-2026-03-09.md
│   │   ├── merton-local-funding-landscape-2026.md
│   │   └── Pre-vault-research-results/     ← 49 deep research files
│   └── convex-grants-db copy/              ← Convex schema reference
│
├── quantum_grants/                         ← PYTHON PACKAGE
│   ├── __init__.py
│   ├── config.py                           ← .env loader, paths
│   ├── circuits/
│   │   ├── grant_circuit.py                ← VQC definition (numpy + QPanda)
│   │   └── origin_cloud.py                 ← Origin QC Cloud interface
│   ├── models/
│   │   ├── feature_encoder.py              ← 10-feature encoder
│   │   └── hybrid_matcher.py               ← Quantum-classical matcher
│   ├── training/
│   │   └── trainer.py                      ← Training loop
│   ├── convex_integration/
│   │   └── client.py                       ← Placeholder Convex client
│   └── data/
│       ├── synthetic.py                    ← Intel-informed data generator
│       └── intel_loader.py                 ← Parses pre-quantum intel
│
├── notebooks/
│   └── 01_quantum_grant_matching.ipynb     ← Local experimentation
│
├── Projects/Quantum Grant Matching/
│   ├── 00-Project-Index.md
│   └── MASTER-PLAN-7-STEPS.md             ← THIS FILE
│
├── Agents/
│   └── Agent-9-Quantum-Matcher.md          ← Prototype agent spec
│
├── Skills/Quantum/
│   └── quantum-grant-matching.md           ← Skill definition
│
├── Research/
│   ├── Quantum Research/
│   │   └── 00-Research-Index.md
│   └── Training Logs/                      ← JSON training outputs
│
└── Data/Quantum/
    └── convex_staging/                     ← Staged results (gitignored)
```

---

## Execution Order

```
Week 1: Steps 1-3 (Feature engineering + data + circuit)
         ├── Run intel_loader.py to extract domain knowledge
         ├── Upgrade synthetic.py with intel-informed generator
         ├── Expand circuit to 10 qubits
         └── First local training run

Week 2: Step 4 (Training)
         ├── Local numpy training (fast iteration)
         ├── Upload to Origin QC Cloud Jupyter
         ├── Cloud simulator validation
         └── Log results to Obsidian

Week 3: Steps 5-7 (Comparison + integration + documentation)
         ├── Classical baseline comparison
         ├── Quantum advantage analysis
         ├── Convex staging test
         └── Production migration decision
```

---

## Origin Quantum Cloud Quick Reference

**Console:** `console.originqc.com.cn`
**Your workspace:** "Funding Project" (running, 1 CPU, 2GB RAM)
**API key:** `.env` → `ORIGIN_QUANTUM_API_KEY`
**SDK:** pyqpanda (pre-installed in cloud Jupyter)
**Local code:** `quantum_grants/circuits/origin_cloud.py`

### To run on cloud:
1. Open your "Funding Project" Jupyter notebook
2. Upload `quantum_grants/` folder
3. Import and run:
```python
from quantum_grants.circuits.origin_cloud import OriginQuantumCloud
cloud = OriginQuantumCloud()
cloud.connect()
```

### Safety:
- Only numerical vectors are sent to quantum cloud
- No client names, org IDs, or identifying data
- All data is synthetic or anonymised feature vectors
