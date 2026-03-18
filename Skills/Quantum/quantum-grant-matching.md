# Skill: Quantum Grant Matching

> **Type:** R&D Skill
> **Domain:** Quantum computing + grant funding
> **Status:** Experimental

## When to Use

- Matching grants to applicants using quantum circuits
- Training quantum models on synthetic funding data
- Evaluating quantum advantage over classical baselines
- Running experiments on Origin Quantum Cloud

## Key Concepts

### Variational Quantum Circuits (VQCs)
Parameterised quantum circuits where gate angles are optimised through classical training. The quantum circuit acts as a kernel that can capture correlations in the feature space that classical methods may miss.

### Parameter-Shift Rule
Gradient estimation for quantum circuits. For each parameter θ:
```
∂f/∂θ = [f(θ + π/2) - f(θ - π/2)] / 2
```
Requires 2 circuit evaluations per parameter per gradient step.

### Angle Encoding
Maps classical features x ∈ [0,1] to rotation angles θ = πx. Each feature controls one qubit's initial state.

### Hybrid Architecture
The quantum circuit produces a raw score; a classical post-processing layer (sigmoid with learnable weight and bias) calibrates it to a probability.

## Codebase Map

```
quantum_grants/
├── circuits/grant_circuit.py    # Quantum circuit definition
├── models/
│   ├── feature_encoder.py       # Classical feature encoding
│   └── hybrid_matcher.py        # Hybrid quantum-classical matcher
├── training/trainer.py          # Training loop
├── convex_integration/client.py # Placeholder Convex client
└── data/synthetic.py            # Synthetic data generator
```

## Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| Match accuracy | Binary classification accuracy | > 75% |
| AUC-ROC | Area under ROC curve | > 0.80 |
| Quantum advantage | Accuracy gain vs classical baseline | > 2% |
| Circuit depth | Total gate count | Minimise |
| Training time | Wall-clock per epoch | < 60s |

## References

- Origin Quantum: https://originqc.com.cn/
- QPanda documentation
- Variational Quantum Eigensolver (VQE) patterns
- Quantum kernel methods for classification
