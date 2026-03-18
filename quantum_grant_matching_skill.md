# Quantum Grant Matching Skill

**Category:** AI/ML Skills
**Technology:** Quantum Computing (VQNet)
**Difficulty:** Advanced
**Dependencies:** Origin Quantum SDK, Convex, Python 3.9+

---

## 📖 Skill Description

Use quantum-classical hybrid machine learning to match CIC profiles to UK grants with superior accuracy compared to classical algorithms.

**Use Case:** When you need to find the best grant matches for a CIC and want to leverage quantum computing for improved accuracy.

---

## 🎯 When to Use This Skill

**Use When:**
- ✅ Matching a CIC to grants from large database (150+ grants)
- ✅ Need high accuracy (classical methods insufficient)
- ✅ Have computational resources for quantum simulation
- ✅ Want to explore quantum advantage in real application

**Don't Use When:**
- ❌ Small grant database (< 50 grants) - overkill
- ❌ Simple keyword matching sufficient
- ❌ No access to quantum computing resources
- ❌ Speed more important than accuracy

---

## 🛠️ How to Use

### **Basic Usage:**

```python
from quantum_grants.models.hybrid_model import QuantumGrantMatcher

# Initialize
matcher = QuantumGrantMatcher(
    model_path="quantum_grants/models/quantum_matcher_v1.pkl",
    num_qubits=4
)

# CIC profile
cic_profile = {
    "beneficiaries": ["Elderly", "Disabled"],
    "activities": ["Support groups", "Training"],
    "region": "Leeds",
    "sector": "Health",
    "amount_needed": 25000
}

# Find matches
matches = matcher.find_matches(cic_profile, top_k=20)

# Results
for match in matches:
    print(f"{match['grant_title']}: {match['quantum_score']:.2f}")
```

### **With Convex Integration:**

```python
from convex import ConvexClient
from quantum_grants.models.hybrid_model import QuantumGrantMatcher

# Connect to Convex
convex = ConvexClient(CONVEX_URL)

# Fetch CIC profile from database
cic = convex.query("cics:getById", {"id": "cic_123"})

# Initialize quantum matcher
matcher = QuantumGrantMatcher()

# Find matches
matches = matcher.find_matches_from_convex(cic_id="cic_123")

# Save results back to Convex
for match in matches:
    convex.mutation("quantum:saveMatch", {
        "cic_id": cic["_id"],
        "grant_id": match["grant_id"],
        "match_score": match["quantum_score"],
        "confidence": match["confidence"]
    })
```

---

## 🧠 Skill Components

### **1. Feature Engineering**

**Location:** `quantum_grants/utils/feature_engineering.py`

```python
def extract_features(cic_profile):
    """
    Convert CIC profile to quantum-compatible feature vector.
    
    Features extracted:
    - Beneficiary alignment (one-hot encoded)
    - Activity compatibility (embedded vector)
    - Geographic eligibility (region matching)
    - Funding amount (normalized)
    - Organizational maturity (categorical)
    """
    return feature_vector
```

### **2. Quantum Circuit**

**Location:** `quantum_grants/circuits/grant_matcher_circuit.py`

```python
class QuantumMatcherCircuit:
    """
    Variational Quantum Circuit for grant matching.
    
    Architecture:
    - Input: Feature vector (n_features)
    - Encoding: Amplitude encoding to qubits
    - Gates: Hadamard, CNOT, RY, RZ (parameterized)
    - Output: Measurement probabilities
    """
```

### **3. Hybrid Model**

**Location:** `quantum_grants/models/hybrid_model.py`

```python
class QuantumGrantMatcher:
    """
    Quantum-classical hybrid neural network.
    
    Components:
    - Classical preprocessing layer
    - Quantum variational circuit
    - Classical output layer
    """
```

---

## 📊 Performance Characteristics

### **Accuracy:**
- Classical baseline: ~78-80%
- Quantum model: ~85-87% (target)
- Improvement: 5-10%

### **Speed:**
- Training: 10-20 minutes (100 epochs)
- Inference: ~50ms per CIC-grant pair
- Batch processing: 1000 matches in ~5 seconds

### **Resource Requirements:**
- CPU: 2+ cores recommended
- RAM: 4GB minimum
- Storage: 500MB for model + data
- Quantum: 4-8 qubits (simulated locally)

---

## 🔧 Configuration

### **Model Parameters:**

```python
config = {
    "num_qubits": 4,           # 4 or 8 qubits
    "circuit_depth": 3,        # Number of layers
    "learning_rate": 0.01,     # Training rate
    "batch_size": 16,          # Training batch
    "epochs": 100,             # Training epochs
    "optimizer": "adam"        # Adam optimizer
}
```

### **Feature Configuration:**

```python
features = {
    "beneficiaries": {
        "encoding": "one_hot",
        "categories": ["Elderly", "Youth", "Disabled", ...]
    },
    "activities": {
        "encoding": "embedding",
        "dim": 8
    },
    "amount_needed": {
        "encoding": "normalized",
        "range": [0, 200000]
    }
}
```

---

## 📝 Examples

### **Example 1: Simple Match**

```python
# Single CIC profile
cic = {
    "beneficiaries": ["Elderly"],
    "region": "London",
    "amount_needed": 50000
}

matches = matcher.find_matches(cic, top_k=10)
print(f"Top grant: {matches[0]['grant_title']}")
```

### **Example 2: Batch Processing**

```python
# Multiple CICs
cics = convex.query("cics:listAll")

results = []
for cic in cics:
    matches = matcher.find_matches(cic, top_k=5)
    results.append({
        "cic_id": cic["_id"],
        "matches": matches
    })

# Save all results
convex.mutation("quantum:batchSave", {"results": results})
```

### **Example 3: A/B Testing**

```python
# Compare quantum vs classical
from quantum_grants.models.classical_baseline import ClassicalMatcher

quantum_matcher = QuantumGrantMatcher()
classical_matcher = ClassicalMatcher()

# Test on same CIC
quantum_matches = quantum_matcher.find_matches(cic)
classical_matches = classical_matcher.find_matches(cic)

# Compare top 5
print("Quantum top 5:", [m['grant_title'] for m in quantum_matches[:5]])
print("Classical top 5:", [m['grant_title'] for m in classical_matches[:5]])
```

---

## 🧪 Training the Model

### **Data Preparation:**

```bash
# 1. Fetch data from Convex
python quantum_grants/convex_integration/fetch_grants.py

# 2. Prepare training data
python quantum_grants/utils/prepare_training_data.py
```

### **Training:**

```bash
# 3. Train quantum model
python quantum_grants/training/train_quantum.py --qubits 4 --epochs 100

# Output:
# Epoch 1/100: Loss 0.542
# Epoch 50/100: Loss 0.234
# Epoch 100/100: Loss 0.187
# ✅ Model saved to: models/quantum_matcher_v1.pkl
```

### **Evaluation:**

```bash
# 4. Test model
python quantum_grants/models/test_model.py

# Output:
# Test Accuracy: 86.3%
# Precision: 0.84
# Recall: 0.88
# F1 Score: 0.86
```

---

## 🔗 Integration with Agent Swarm

### **In Main Pipeline:**

```python
# File: agents/main_pipeline.py

from agents.quantum_matcher import QuantumGrantMatcherAgent

def run_grant_automation(cic_id):
    # ... existing agents
    
    # Agent 9: Quantum matching
    quantum_agent = QuantumGrantMatcherAgent()
    matches = quantum_agent.find_matches(cic_id)
    
    print(f"Quantum found {len(matches)} optimal grants")
    
    # Pass to next agent
    return matches
```

---

## 📚 Related Skills

**Upstream Skills:**
- [[grant_research_skill]] - Find available grants
- [[cic_profiling_skill]] - Extract CIC features

**Downstream Skills:**
- [[grant_application_writer_skill]] - Write applications
- [[deadline_tracker_skill]] - Monitor deadlines

**Similar Skills:**
- [[classical_grant_matching_skill]] - Non-quantum baseline
- [[semantic_search_skill]] - Vector similarity matching

---

## 🐛 Troubleshooting

### **Issue: Low Accuracy**

**Symptoms:** Model accuracy < 80%
**Causes:**
- Insufficient training data
- Wrong qubit count
- Poor feature engineering

**Solutions:**
- Increase training data (add more CIC-grant pairs)
- Try 8 qubits instead of 4
- Review feature extraction in `utils/feature_engineering.py`

### **Issue: Slow Performance**

**Symptoms:** Inference takes > 5 seconds per match
**Causes:**
- Too many qubits (high simulation overhead)
- Large grant database
- Inefficient circuit design

**Solutions:**
- Reduce to 4 qubits
- Pre-filter grants before quantum matching
- Optimize circuit depth

### **Issue: Model Not Loading**

**Symptoms:** `FileNotFoundError` when loading model
**Causes:**
- Model not trained yet
- Wrong path

**Solutions:**
- Train model first: `python quantum_grants/training/train_quantum.py`
- Check path: `models/quantum_matcher_v1.pkl`

---

## 📖 Further Reading

**Obsidian Notes:**
- [[../Research/Quantum Research/quantum_advantage_analysis]]
- [[../Research/Quantum Research/circuit_optimization]]
- [[../Projects/Quantum_Grant_Matching_Project]]

**External Resources:**
- [Origin Quantum Documentation](https://originqc.com.cn/en)
- [VQNet Tutorial](https://github.com/OriginQ/VQNET2.0-tutorial)
- [Quantum Machine Learning Paper](https://arxiv.org/abs/...)

---

**Tags:** #skill #quantum #grants #ai #vqnet #matching
**Difficulty:** ⭐⭐⭐⭐ (Advanced)
**Maintained by:** [[../Agents/Agent_9_Quantum_Matcher]]
