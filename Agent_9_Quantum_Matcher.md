# Agent 9: Quantum Grant Matcher

**Type:** Research & Matching Agent
**Status:** 🚧 In Development
**Technology:** Quantum-Classical Hybrid (VQNet)
**Dependencies:** [[Agent_1_Research]], Convex, Origin Quantum SDK

---

## 🎯 Purpose

Use quantum computing to match CIC profiles to relevant UK grants with higher accuracy than classical algorithms.

**Input:** CIC profile (beneficiaries, activities, region, funding needs)
**Output:** Top 20 grants ranked by quantum match score
**Performance Target:** 85%+ accuracy, 5-10% better than classical

---

## 🏗️ Architecture

```
CIC Profile (Input)
    ↓
Feature Engineering
    ↓
Quantum Circuit (4-8 qubits)
    ├── Superposition layer
    ├── Entanglement layer
    └── Parameterized rotations (trainable)
    ↓
Classical Neural Network
    ↓
Match Score (0-1)
    ↓
Top 20 Grants (Ranked)
```

---

## 🔧 Implementation

### **Location:**
- Python: `quantum_grants/agents/quantum_matcher.py`
- Config: `quantum_grants/models/quantum_matcher_v1.pkl`
- Circuit: `quantum_grants/circuits/grant_matcher_circuit.py`

### **Integration Points:**

**Upstream (Receives From):**
- [[Agent_1_Research]] - Provides CIC profile data
- Convex `cics` table - CIC details
- Convex `grants` table - Available grants

**Downstream (Sends To):**
- [[Agent_10_Application_Writer]] - Matched grants for application
- Convex `quantum_matches` table - Match results storage
- [[../Data/Quantum/match_results]] - Performance tracking

---

## 📊 Algorithm

### **Step 1: Feature Extraction**

```python
def extract_cic_features(cic_profile):
    """
    Convert CIC profile to quantum-compatible features.
    
    Features (normalized 0-1):
    - Beneficiary alignment (vector embedding)
    - Activity type compatibility
    - Geographic eligibility
    - Funding amount match
    - Organizational maturity
    - Track record strength
    """
    return feature_vector  # Shape: (n_features,)
```

### **Step 2: Quantum Processing**

```python
def quantum_match(cic_features, grant_features):
    """
    Run quantum circuit to compute match probability.
    
    Circuit:
    1. Encode features in quantum states (amplitude encoding)
    2. Apply entanglement (CNOT gates)
    3. Parameterized rotations (learned during training)
    4. Measure output qubits
    
    Returns:
    - match_score: Probability of good match (0-1)
    - confidence: Quantum measurement confidence
    """
    return match_score, confidence
```

### **Step 3: Ranking & Output**

```python
def rank_grants(cic_profile, all_grants):
    """
    Rank all grants by quantum match score.
    
    1. Compute match score for each grant
    2. Sort by score (descending)
    3. Return top 20
    4. Store results in Convex
    """
    return top_20_grants
```

---

## 🧪 Training Process

### **Dataset:**
- **Grants:** 150+ UK grants from [[../Data/Quantum/grants_database]]
- **CICs:** 100+ synthetic profiles for training
- **Matches:** Historical success data (if available)

### **Training Loop:**

```python
# Documented in [[../Research/Training Logs/]]

for epoch in range(100):
    # Forward pass: Quantum circuit + classical layer
    predictions = model(cic_features, grant_features)
    
    # Loss: Binary cross-entropy (good match vs poor match)
    loss = bce_loss(predictions, labels)
    
    # Backward: Optimize quantum circuit parameters
    optimizer.step()
    
    # Log progress
    log_to_obsidian(f"Epoch {epoch}: Loss {loss}")
```

### **Hyperparameters:**
- Qubits: 4-8 (tunable)
- Learning rate: 0.01
- Optimizer: Adam
- Batch size: 16
- Epochs: 100-200

---

## 📈 Performance Metrics

### **Accuracy Metrics:**
- **Precision:** % of recommended grants that are actually good matches
- **Recall:** % of good grants found by the model
- **F1 Score:** Harmonic mean of precision and recall
- **Top-K Accuracy:** % of time best grant is in top K recommendations

### **Quantum Metrics:**
- **Circuit Depth:** Number of quantum gates
- **Qubit Count:** Number of qubits used
- **Measurement Error:** Noise in quantum measurements
- **Classical Comparison:** % improvement over baseline

### **Current Results:**
*Tracked in [[../Projects/Quantum_Grant_Matching_Project#Performance Tracking]]*

| Metric | Classical | Quantum | Improvement |
|--------|-----------|---------|-------------|
| Accuracy | TBD | TBD | TBD |
| Precision | TBD | TBD | TBD |
| Recall | TBD | TBD | TBD |
| F1 Score | TBD | TBD | TBD |

---

## 🔗 Agent Workflow Integration

### **In Grant Automation Pipeline:**

```
Agent 1 (Research) 
  → Identifies CIC needs
    ↓
Agent 9 (Quantum Matcher) ← YOU ARE HERE
  → Finds best 20 grants using quantum algorithm
    ↓
Agent 2 (Deadline Checker)
  → Filters by deadline urgency
    ↓
Agent 3 (Eligibility Validator)
  → Confirms CIC eligibility
    ↓
Agent 10 (Application Writer)
  → Generates applications for top matches
```

### **Invocation:**

```python
# In main pipeline
from agents.quantum_matcher import QuantumGrantMatcher

# Initialize
quantum_agent = QuantumGrantMatcher()

# Run
matches = quantum_agent.find_matches(cic_profile)

# Results
print(f"Found {len(matches)} quantum-optimized grant matches")
```

---

## 🛠️ Configuration

### **Environment Variables:**

```bash
export CONVEX_URL="https://your-deployment.convex.cloud"
export QUANTUM_MODEL_PATH="quantum_grants/models/quantum_matcher_v1.pkl"
export QUBIT_COUNT=4  # or 8 for higher accuracy
```

### **Obsidian Links:**

- Training logs: [[../Research/Training Logs/]]
- Circuit design: [[../Research/Quantum Research/quantum_circuit_design]]
- Performance: [[../Projects/Quantum_Grant_Matching_Project#Performance Tracking]]

---

## 📝 Development Log

### **2026-03-11: Initial Setup**
- Created agent structure
- Installed Origin Quantum SDK
- Configured Convex integration

### **2026-03-12: First Training** *(planned)*
- Build 4-qubit circuit
- Train on 100 CIC-grant pairs
- Benchmark vs classical

### **2026-03-13: Optimization** *(planned)*
- Scale to 8 qubits
- Hyperparameter tuning
- A/B testing

---

## 🚀 Next Steps

**Immediate (This Week):**
1. [ ] Fetch training data from Convex
2. [ ] Implement feature engineering
3. [ ] Build quantum circuit (4 qubits)
4. [ ] Train first model
5. [ ] Document results in [[../Research/Training Logs/]]

**Short-term (Next Week):**
1. [ ] Optimize circuit design
2. [ ] Scale to 8 qubits
3. [ ] Compare vs classical baseline
4. [ ] Integrate with main pipeline

**Long-term (Month):**
1. [ ] Deploy to production
2. [ ] Monitor real-world performance
3. [ ] Continuous model improvement
4. [ ] Expand to tender matching (AOE)

---

## 💡 Research Questions

*Documented in [[../Research/Quantum Research/]]*

1. **Qubit Count:** 4 vs 8 qubits - accuracy vs speed tradeoff?
2. **Circuit Depth:** How many layers needed for good performance?
3. **Feature Engineering:** Which grant/CIC features most important?
4. **Quantum Advantage:** Where does quantum outperform classical?

---

**Tags:** #agent #quantum #grants #matching #ai #vqnet
**Related:** [[../Projects/Quantum_Grant_Matching_Project]], [[../Skills/Quantum/quantum_grant_matching_skill]]
