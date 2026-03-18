# Quantum Grant Matching Project

**Status:** 🚧 In Progress
**Started:** 2026-03-11
**Agent:** Agent 9 - Quantum Matcher
**Tech Stack:** Origin Quantum SDK, VQNet, Convex, Claude Code

---

## 🎯 Project Goal

Build a quantum-powered grant matching system that outperforms classical algorithms by 5-10% in accuracy for matching CIC profiles to relevant UK grants.

**Success Criteria:**
- [ ] Quantum model accuracy > 85%
- [ ] Outperforms classical baseline by 5%+
- [ ] Integrates with existing 8-agent swarm
- [ ] Real-time sync with Convex database
- [ ] Documented in Obsidian vault

---

## 🏗️ Architecture

```
Obsidian Vault (Knowledge Layer)
    ↓
Convex (Data Layer)
    ↓
Quantum Models (Computation Layer)
    ↓
Agent Swarm (Execution Layer)
```

**Components:**
1. **Data Source:** [[../Data/Quantum/grants_database]] - Convex backend
2. **Quantum Circuit:** [[quantum_circuit_design]] - 4-8 qubit VQC
3. **Training:** [[../Research/Training Logs/index]] - Daily progress
4. **Agent:** [[../Agents/Agent_9_Quantum_Matcher]] - Integration

---

## 📊 Current Status

### Phase 1: Setup ✅
- [x] Origin Quantum SDK installed
- [x] Obsidian structure created
- [x] Convex integration configured
- [x] Claude Code workspace ready

### Phase 2: Data Preparation 🚧
- [ ] Fetch grants from Convex
- [ ] Create feature engineering pipeline
- [ ] Generate training/test splits
- [ ] Document data schema

### Phase 3: Model Development ⏳
- [ ] Build quantum circuit (VQC)
- [ ] Implement hybrid model
- [ ] Train on grant-CIC pairs
- [ ] Benchmark vs classical

### Phase 4: Integration ⏳
- [ ] Create Agent 9 definition
- [ ] Integrate with existing swarm
- [ ] Deploy to production
- [ ] Monitor performance

---

## 🔬 Research Notes

**Key Insights:**
- [[../Research/Quantum Research/quantum_advantage_analysis]] - Where quantum helps
- [[../Research/Quantum Research/circuit_optimization]] - Qubit selection
- [[../Research/Quantum Research/feature_engineering_strategy]] - Best features

**Training Logs:**
- [[../Research/Training Logs/2026-03-11_initial_setup]]
- [[../Research/Training Logs/2026-03-12_first_training]]

---

## 📈 Performance Tracking

| Date | Model | Accuracy | Notes |
|------|-------|----------|-------|
| 2026-03-12 | Classical Baseline | TBD | Benchmark |
| 2026-03-13 | Quantum v1 (4 qubits) | TBD | First attempt |
| 2026-03-14 | Quantum v2 (8 qubits) | TBD | Scaled up |

---

## 🔗 Related Documents

**Skills:**
- [[../Skills/Quantum/quantum_grant_matching_skill]]
- [[../Skills/grant_automation_pipeline]]

**Agents:**
- [[../Agents/Agent_9_Quantum_Matcher]]
- [[../Agents/Agent_1_Research]] - Upstream
- [[../Agents/Agent_10_Application_Writer]] - Downstream

**Data:**
- [[../Data/Quantum/grants_database]]
- [[../Data/Quantum/cic_profiles]]
- [[../Data/Quantum/match_results]]

**Code:**
- `quantum_grants/models/hybrid_model.py`
- `quantum_grants/training/train_quantum.py`
- `quantum_grants/convex_integration/fetch_grants.py`

---

## 💡 Next Actions

**This Week:**
1. [ ] Run Convex data fetch
2. [ ] Build feature engineering pipeline
3. [ ] Create quantum circuit (4 qubits)
4. [ ] Train first model
5. [ ] Document results in [[../Research/Training Logs/]]

**Next Week:**
1. [ ] Optimize circuit design
2. [ ] Scale to 8 qubits
3. [ ] A/B test vs classical
4. [ ] Create Agent 9 definition

---

## 📚 Resources

**Documentation:**
- [Origin Quantum Docs](https://originqc.com.cn/en)
- [QPanda GitHub](https://github.com/OriginQ/QPanda-2)
- [VQNet Examples](https://github.com/OriginQ/VQNET2.0-tutorial)

**Internal:**
- [[quantum_circuit_design]]
- [[training_methodology]]
- [[integration_strategy]]

---

**Tags:** #quantum #grants #ai #agent9 #convex #obsidian
**Related Projects:** [[Architecture of Endurance]], [[InclusiFund CIC Tools]]
