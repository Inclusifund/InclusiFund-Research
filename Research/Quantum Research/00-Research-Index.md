# Quantum Grant Matching — Research Index

> **Started:** 2026-03-11
> **Researcher:** Reece (AntiGravity)
> **Status:** Active R&D

---

## Research Questions

1. **Can quantum circuits outperform classical methods for grant matching?**
   - Baseline: logistic regression, random forest on same features
   - Metric: AUC-ROC improvement

2. **What is the optimal circuit architecture?**
   - Number of layers vs accuracy
   - Entanglement topology (linear chain vs all-to-all)
   - Feature encoding strategy

3. **How does performance scale with real quantum hardware?**
   - Noise impact on match accuracy
   - Error mitigation strategies
   - Origin Quantum hardware vs simulator

4. **Is there a quantum advantage for multi-criteria matching?**
   - Entanglement may capture feature correlations
   - Quantum interference for non-obvious matches
   - Theoretical analysis of expressibility

## Experiment Log

| Date | Experiment | Result | Notes |
|------|-----------|--------|-------|
| 2026-03-11 | Workspace setup | Complete | Folder structure, code, notebook |
| | First synthetic training | Pending | 20 grants × 40 applicants |
| | Classical baseline | Pending | sklearn logistic regression |
| | Circuit depth study | Pending | 1, 2, 3, 4 layers |

## Literature

- [ ] Schuld & Petruccione — "Machine Learning with Quantum Computers"
- [ ] Havlíček et al. — "Supervised learning with quantum-enhanced feature spaces"
- [ ] Origin Quantum — QPanda documentation and tutorials
- [ ] Abbas et al. — "Power of quantum neural networks"

## Data Safety Checklist

- [x] Using only synthetic data
- [x] No client identifiers in any file
- [x] Cloud submissions contain only numerical vectors
- [x] Convex integration is placeholder only
- [ ] Reviewed by production team before migration
