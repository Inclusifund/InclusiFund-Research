# InclusiFund Research — CLAUDE.md

## Project Overview
Public research repository for InclusiFund's quantum-enhanced grant matching system. Contains the quantum grant pipeline, Convex integration, funding intelligence, and the Opportunities Hub frontend.

**Convex deployment:** `terrific-bloodhound-927.convex.cloud` (team: inclusifund, project: burnout-app)
**Convex source:** `/Users/royalreece/Desktop/Claude Code: AntiGravity Projects/Vertical AI/convex-cic-tools/`
**Test suite:** `python3 -m pytest tests/ -v` (210 tests)

## Architecture

### Quantum Grant Pipeline
```
Convex fetch → normalise (dual schema) → enrich (intel data) → quantum score (6-qubit circuit)
→ rescale (min-max) → filter blocked funders → rank → stage → agent output
```

**Agents:**
- Agent 9: Quantum Matcher (`quantum_grants/agents/quantum_matcher.py`)
- Agent 2: Deadline Tracker (`quantum_grants/agents/deadline_tracker.py`)
- Agent 10: Grant Writer (`quantum_grants/agents/grant_writer.py`)

**Key modules:**
- `quantum_grants/pipeline.py` — orchestrator
- `quantum_grants/circuits/grant_circuit.py` — 6-qubit variational circuit (Rx/Ry/Rz + CNOT)
- `quantum_grants/circuits/origin_cloud.py` — Origin Quantum Cloud integration
- `quantum_grants/convex_integration/client.py` — Convex HTTP client + staging + sync
- `quantum_grants/data/grant_enricher.py` — 80+ funder enrichment entries
- `quantum_grants/data/intel_labels.py` — blocked funders, characteristic labels
- `quantum_grants/training/real_data_trainer.py` — parameter-shift gradient training

### Data
- `Data/Quantum/live_grants.json` — cached Convex grants (93 records, all enriched)
- `Data/Quantum/convex_staging/` — staged quantum match results
- `Data/Quantum/pipeline_runs/` — pipeline output history
- `pre-quantum-skills-intel/funding-intel copy/` — raw funding research (private intel, DO NOT expose)

### Frontend
- `Design/grants-list copy.html` — current grants list (dark theme, React/Tailwind/Convex)
- `Design/opportunities-hub.html` — redesigned hub (white theme, colour-coded, in progress)

## Critical Rules

### Privacy
This is a **PUBLIC repo**. Never commit:
- Client names, org IDs, or identifiable data
- Private funding research referencing specific clients
- `.env` files or API keys
- Client profiles or assessment data

All training uses `DEMO_PROFILES` (fictional) and `FUNDER_CHARACTERISTICS` (public eligibility rules).

### Convex
- Always use `fetch_all_grants()` not `listGrants` (the latter returns degraded data with zero amounts)
- Filter status locally (Convex has both "Open" and "Open Now")
- The source Convex project is in `convex-cic-tools/`, not in this repo
- `bulkSyncGrants` is destructive (deletes all then inserts) — use `bulkAddOpportunities` for additive pushes

### Quantum
- Classical pipeline is the **production system** — quantum is the R&D scoring layer
- Sigmoid compression requires min-max rescaling after circuit output
- Classical weight + bias must be trained alongside circuit params (was a bug — fixed)
- Origin Quantum Cloud (`pyqpanda`) not installed locally — graceful fallback to numpy
- Backend parameter: "auto" (default, numpy fallback), "numpy" (force), "cloud" (requires pyqpanda + API key)

## Quantum Computing Milestone (2026-03-12)

This is likely the **first quantum-enhanced grants database ever built**. Key achievements:
- 6-qubit variational quantum circuit for multi-dimensional grant-organisation alignment
- 93 grants cleaned, enriched, and scored through quantum pipeline
- Parameter-shift rule gradient training on real funding intel
- Full Convex integration (fetch → score → sync)
- Origin Quantum Cloud integration explored (Origin Pilot, QPanda3, VQNet)
- 210 tests passing across all modules

**Honest assessment:** Quantum clustering and multi-dimensional alignment scoring have genuine potential for grant matching. The variational circuit provides a natural way to encode eligibility, sector overlap, theme alignment, amount fit, difficulty, and stage fit into a single score. But the classical pipeline is what runs in production — quantum is the R&D layer that may graduate to production when hardware matures.

**Future:** Upgrade grant-eligibility to multi-dimensional scoring: technical fit, social value alignment, evidence strength, win probability, competition intensity.

## Opportunities Hub (In Progress)

Expanding from grants-only to colour-coded opportunity types:
- Grants (teal `#008080`), Contracts (orange `#E8804C`), CSR (lilac `#B497D6`)
- Accelerators (peach `#F5B895`), Social Investment (light teal `#6BB6B6`)
- Competitions (warm orange `#D4956B`), Procurement (soft teal `#9DCDC8`)

34 non-grant opportunities extracted and structured in `Data/Quantum/live_opportunities.json`:
- Accelerators (10), CSR (7), Competitions (6), Social Investment (5), Contracts (4), Procurement (2)
- Schema matches `live_grants.json` + `opportunityType` and `eligibility` fields
- Sources: VWD research, creative industries intel, NHS contracts, LGBTQ+ funding, regional programmes

White background, `border-l-4` card accents.

**Frontend:** `Design/opportunities-hub.html` — live, merges 93 Convex grants + 34 local opportunities.
- Colour-coded type pills with counts, grid/list view toggle
- Sidebar filters: search, sort, sectors, regions
- Cards show type badge, funder, amount, deadline, sectors, stage tags, CTA
- Fetches grants from Convex at runtime, falls back to local data if offline

## Things I've Learned From Working With Reece

### Work Style
- Works in intense late-night build sessions — don't interrupt flow, match the energy
- Moves fast and prefers building working systems over planning documents
- "When in doubt, bias toward shipping over planning"
- Approves with "approved" — don't over-explain at gates
- Wants end-to-end flow, minimal interruption between pipeline stages
- Prefers strategic pre-application emails to funders before writing applications

### Communication
- Values honest assessment over hype — always flag when something is speculative vs proven
- When explaining tech (quantum, circuits), be direct about what works and what's R&D
- Don't pad responses — lead with the answer, skip filler
- Preferred palette: orange, teals, peach, lilac (not the typical corporate blue/green)

### Technical Preferences
- Lean stack is the proven default: NLM (NotebookLM) + Obsidian + Claude Code
- Always act on intelligence immediately — update profile + create docs in same pass
- Values deep NLM queries — multiple targeted queries > one shallow one
- When a longlist goes stale, do full rediscovery rather than patching
- For Black-led orgs, lead with diversity/lived experience as differentiator
- Individual sponsorship cases need a different approach from org grants

### Corrections Made During This Session
- "This is a PUBLIC repo" — stripped all client data immediately when flagged
- Used `fetch_all_grants` not `listGrants` after discovering zero-amount data degradation
- Classical params were never training — fixed when discovered, didn't wait to be asked
- Unicode mismatches in grant names (en-dash, smart quotes) — fix the matching, don't skip the data

### Collaboration Model
- Claude Code is a collaborative partner, not just a tool
- Claude Code often has deeper technical context on emerging tech (quantum, circuits, cloud platforms) — should proactively flag opportunities and risks
- The self-improving loop is real: every session builds on prior context via memory + CLAUDE.md
- When given "lets do 1,2,3,4 in parallel" — actually run them in parallel with Agent tool
- Run the tests after every significant change — don't assume it works

### Client Work Patterns
- Always clarify funder programme when multiple exist (e.g. "NLCF" could be AfA or RC)
- Always clarify director vs consultant roles (Elaine = consultant, NOT director)
- Check Companies House for registration details before assuming legal structure
- Organisation age vs funder requirements is the biggest blocker for startups
- Sabbatical/zero-income years should be framed as "strategic pause" not failure
- CLG/co-op asset locks are NOT statutory like CIC — always verify with funders
