"""
InclusiFund Quantum Grant Pipeline — Live Convex Integration.

Orchestrates the full matching flow:
  1. Fetch live grants from Convex (or cache)
  2. Normalise grant schema
  3. Run Quantum Matcher (Agent 9) scoring
  4. Stage results for Convex sync
  5. Emit structured output for downstream agents (Deadline, Writer)

Usage:
    from quantum_grants.pipeline import QuantumPipeline
    from quantum_grants.agents.quantum_matcher import CICProfile
    pipeline = QuantumPipeline()
    result = pipeline.run(my_profile)  # pass a CICProfile directly
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from quantum_grants.agents.quantum_matcher import (
    QuantumGrantMatcher,
    CICProfile,
    GrantMatch,
)
from quantum_grants.agents.deadline_tracker import DeadlineTracker, DeadlineReport
from quantum_grants.agents.grant_writer import GrantWriter, GrantBrief
from quantum_grants.convex_integration.client import ConvexClient
from quantum_grants.config import DATA_DIR
from quantum_grants.data.grant_enricher import enrich_grant_list
from quantum_grants.data.intel_labels import is_funder_blocked
from quantum_grants.scoring.multi_dimensional import (
    MultiDimensionalScorer,
    MultiDimensionalScore,
)


# --- Grant normaliser (handles both Convex schemas) ---

def normalise_grant(raw: dict) -> dict:
    """
    Normalise a Convex grant record so both old and new schemas work.

    The Convex DB has two naming conventions:
      Old: grantName, amountMax, amountMin, eligibleSectors, geographicFocus
      New: name, maxAmount, minAmount, sectors, regions

    This ensures the dict always has the fields Agent 9 expects.
    """
    g = dict(raw)

    # Name
    if "name" not in g and "grantName" in g:
        g["name"] = g["grantName"]

    # Amounts
    if "maxAmount" not in g and "amountMax" in g:
        g["maxAmount"] = g["amountMax"]
    if "minAmount" not in g and "amountMin" in g:
        g["minAmount"] = g["amountMin"]

    # Sectors
    if "sectors" not in g and "eligibleSectors" in g:
        g["sectors"] = g["eligibleSectors"]

    # Regions
    if "regions" not in g and "geographicFocus" in g:
        focus = g["geographicFocus"]
        g["regions"] = focus if isinstance(focus, list) else [focus]

    # Ensure regions is always a list
    if isinstance(g.get("regions"), str):
        g["regions"] = [g["regions"]]

    # Defaults for fields the matcher reads
    g.setdefault("maxAmount", 0)
    g.setdefault("minAmount", 0)
    g.setdefault("sectors", [])
    g.setdefault("regions", [])
    g.setdefault("description", "")
    g.setdefault("status", "Unknown")
    g.setdefault("supportsStartup", False)
    g.setdefault("supportsGrowth", False)
    g.setdefault("supportsScale", False)
    g.setdefault("applicationDifficulty", 3)
    g.setdefault("website", "")

    return g


def get_client(identifier: CICProfile) -> CICProfile:
    """Accept a CICProfile and return it (for pipeline compatibility)."""
    if isinstance(identifier, CICProfile):
        return identifier
    raise TypeError(
        f"Expected a CICProfile instance, got {type(identifier).__name__}. "
        "Pass a CICProfile directly to the pipeline."
    )


# --- Pipeline result ---

@dataclass
class PipelineResult:
    """Full output of a quantum pipeline run."""
    org_id: str
    org_name: str
    total_grants_scored: int
    blocked_count: int
    matches: list[GrantMatch]
    recommended: list[GrantMatch]
    staged_manifest: dict
    run_timestamp: str
    model_version: str
    output_path: str
    multi_dimensional_scores: Optional[dict[str, MultiDimensionalScore]] = None

    @property
    def recommended_count(self) -> int:
        return len(self.recommended)

    def to_dict(self) -> dict:
        d = {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "total_grants_scored": self.total_grants_scored,
            "blocked_count": self.blocked_count,
            "recommended_count": self.recommended_count,
            "run_timestamp": self.run_timestamp,
            "model_version": self.model_version,
            "output_path": self.output_path,
            "matches": [asdict(m) for m in self.matches],
            "recommended": [asdict(m) for m in self.recommended],
        }
        if self.multi_dimensional_scores:
            d["multi_dimensional_scores"] = {
                grant_id: score.to_dict()
                for grant_id, score in self.multi_dimensional_scores.items()
            }
        return d

    def for_deadline_agent(self) -> list[dict]:
        """Structured output for Agent 2 (Deadline Tracker)."""
        return [
            {
                "grant_id": m.grant_id,
                "grant_name": m.grant_name,
                "funder": m.funder,
                "website": m.website,
                "quantum_score": m.quantum_score,
                "status": m.status,
            }
            for m in self.recommended
        ]

    def for_writer_agent(self) -> list[dict]:
        """Structured output for Agent 10 (Grant Writer)."""
        return [
            {
                "grant_id": m.grant_id,
                "grant_name": m.grant_name,
                "funder": m.funder,
                "min_amount": m.min_amount,
                "max_amount": m.max_amount,
                "quantum_score": m.quantum_score,
                "eligibility": m.eligibility,
                "sector_overlap": m.sector_overlap,
                "theme_overlap": m.theme_overlap,
                "capacity": m.capacity,
                "website": m.website,
            }
            for m in self.recommended
        ]


# --- Pipeline ---

class QuantumPipeline:
    """
    Orchestrates the quantum grant matching pipeline.

    Connects Agent 9 (Quantum Matcher) to the live Convex backend
    and produces structured output for downstream pipeline agents.
    """

    def __init__(
        self,
        n_layers: int = 2,
        threshold: float = 0.5,
        top_k: int = 20,
        model_path: Optional[str] = None,
        use_cache: bool = True,
        backend: str = "auto",
    ):
        self.top_k = top_k
        self.use_cache = use_cache
        self.matcher = QuantumGrantMatcher(
            n_layers=n_layers,
            threshold=threshold,
            use_cache=use_cache,
            backend=backend,
        )
        self.convex = self.matcher.convex
        self.output_dir = Path(DATA_DIR) / "pipeline_runs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load trained weights if available
        if model_path:
            self.matcher.load_params(model_path)
        else:
            self._load_latest_model()

    def _load_latest_model(self) -> bool:
        """Load the latest trained model if it exists."""
        latest = Path(DATA_DIR) / "models" / "latest.json"
        if latest.exists():
            self.matcher.load_params(str(latest))
            return True
        return False

    def fetch_grants(self, include_closed: bool = False) -> list[dict]:
        """
        Fetch and normalise grants from Convex.

        Always uses fetch_all_grants (richer data) and filters by status
        locally, since listGrants returns degraded records with zero amounts.
        """
        try:
            raw = self.convex.fetch_all_grants()
        except Exception:
            if self.use_cache:
                raw = self.convex.load_cached_grants()
            else:
                raise

        normalised = [normalise_grant(g) for g in raw]

        # Enrich with intel data (fills missing amounts, deadlines)
        enrich_grant_list(normalised)

        if not include_closed:
            normalised = [
                g for g in normalised
                if g.get("status", "").lower() in ("open", "open now", "rolling", "active", "unknown", "")
            ]

        return normalised

    @staticmethod
    def _rescale_scores(matches: list[GrantMatch]) -> list[GrantMatch]:
        """
        Min-max rescale quantum scores to use the full [0, 1] range.

        The sigmoid calibration compresses raw circuit output into a narrow
        band (e.g. 0.53-0.71). This recovers meaningful differentiation
        while preserving relative ordering.
        """
        if len(matches) < 2:
            return matches

        scores = [m.quantum_score for m in matches]
        lo, hi = min(scores), max(scores)
        spread = hi - lo

        if spread < 1e-6:
            return matches

        for m in matches:
            m.quantum_score = round((m.quantum_score - lo) / spread, 4)

        return matches

    def run(
        self,
        client: CICProfile,
        top_k: Optional[int] = None,
        include_closed: bool = False,
        min_score: Optional[float] = None,
        multi_dimensional: bool = False,
    ) -> PipelineResult:
        """
        Run the full quantum matching pipeline for an organisation.

        Args:
            client: A CICProfile instance describing the organisation.
            top_k: Max matches to return (default: self.top_k).
            include_closed: Include closed/paused grants.
            min_score: Minimum quantum score filter.
            multi_dimensional: If True, compute 5-dimension scores alongside
                the existing quantum score. Opt-in enhancement — does not
                affect the existing single-score pipeline.

        Returns:
            PipelineResult with matches, recommendations, and agent outputs.
            If multi_dimensional=True, also includes multi_dimensional_scores.
        """
        cic = get_client(client)
        k = top_k or self.top_k
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Step 1: Fetch and normalise grants
        grants = self.fetch_grants(include_closed=include_closed)

        # Step 2: Inject normalised grants into matcher's cache
        self.matcher._grants = grants

        # Step 3: Score ALL grants (rescale needs full distribution)
        all_matches = self.matcher.find_matches(
            cic, top_k=len(grants), include_closed=include_closed,
            min_score=min_score,
        )

        # Step 3b: Rescale scores across full set for meaningful differentiation
        all_matches = self._rescale_scores(all_matches)

        # Step 3c: Re-rank and slice to top-K
        all_matches.sort(key=lambda m: m.quantum_score, reverse=True)
        for i, m in enumerate(all_matches, 1):
            m.rank = i
        matches = all_matches[:k]

        # Step 3d: Filter blocked funders
        pre_filter_count = len(matches)
        matches = [
            m for m in matches
            if not is_funder_blocked(
                f"{m.grant_name} {m.funder}",
                cic.legal_structure,
                cic.region,
                cic.annual_turnover,
                cic.years_operating,
            )
        ]
        blocked_count = pre_filter_count - len(matches)
        # Re-rank after filtering
        for i, m in enumerate(matches, 1):
            m.rank = i

        # Step 3e: Multi-dimensional scoring (opt-in)
        md_scores = None
        if multi_dimensional:
            md_scores = self._compute_multi_dimensional(grants, matches, cic)

        # Step 4: Stage results for Convex sync
        manifest = self.matcher.stage_results(matches, cic)

        # Step 5: Separate recommended from full list
        recommended = [m for m in matches if m.quantum_score >= self.matcher.threshold]

        # Step 6: Save pipeline output
        run_id = f"{cic.org_id}_{time.strftime('%Y%m%d_%H%M%S')}"
        output_path = self.output_dir / f"{run_id}.json"

        result = PipelineResult(
            org_id=cic.org_id,
            org_name=cic.org_name,
            total_grants_scored=len(grants),
            blocked_count=blocked_count,
            matches=matches,
            recommended=recommended,
            staged_manifest=manifest,
            run_timestamp=timestamp,
            model_version=self.matcher.get_params().get("model_version", "0.1.0-alpha"),
            output_path=str(output_path),
            multi_dimensional_scores=md_scores,
        )

        with open(output_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        return result

    def _compute_multi_dimensional(
        self,
        grants: list[dict],
        matches: list[GrantMatch],
        cic: CICProfile,
    ) -> dict[str, MultiDimensionalScore]:
        """
        Compute multi-dimensional scores for matched grants.

        Looks up the original grant dict for each match and runs
        the 5-dimension scorer against the org profile.
        """
        scorer = MultiDimensionalScorer()

        # Build a lookup from grant ID/name to grant dict
        grant_lookup: dict[str, dict] = {}
        for g in grants:
            gid = g.get("_id", "")
            gname = g.get("name", "")
            if gid:
                grant_lookup[gid] = g
            if gname:
                grant_lookup[gname] = g

        md_scores: dict[str, MultiDimensionalScore] = {}
        for m in matches:
            grant_dict = grant_lookup.get(m.grant_id) or grant_lookup.get(m.grant_name)
            if grant_dict:
                md_scores[m.grant_id or m.grant_name] = scorer.score(grant_dict, cic)

        return md_scores

    def run_with_agents(
        self,
        client: CICProfile,
        top_k: Optional[int] = None,
        include_closed: bool = False,
        min_score: Optional[float] = None,
    ) -> dict:
        """
        Run the full pipeline including downstream agents.

        Runs Agent 9 (Quantum Matcher), then Agent 2 (Deadline Tracker)
        and Agent 10 (Grant Writer) on the results.

        Returns:
            Dict with keys: 'pipeline_result', 'deadline_report', 'briefs'.
        """
        result = self.run(
            client,
            top_k=top_k,
            include_closed=include_closed,
            min_score=min_score,
        )

        deadline_tracker = DeadlineTracker()
        deadline_report = deadline_tracker.process(result)

        writer = GrantWriter()
        briefs = writer.process(result)

        return {
            "pipeline_result": result,
            "deadline_report": deadline_report,
            "briefs": briefs,
        }

    def sync(self) -> dict:
        """
        Push staged quantum match results to the Convex backend.

        Can be called after run() or independently at any time.

        Returns:
            Summary dict with sync counts and any errors.
        """
        return self.convex.sync_to_convex()

    def summary(self, result: PipelineResult) -> str:
        """Human-readable summary of a pipeline run."""
        lines = [
            f"Quantum Pipeline — {result.org_name} ({result.org_id})",
            f"Run: {result.run_timestamp}",
            f"Grants scored: {result.total_grants_scored}",
            f"Blocked funders removed: {result.blocked_count}",
            f"Top matches: {len(result.matches)}",
            f"Recommended: {result.recommended_count}",
            "=" * 65,
        ]
        for m in result.matches:
            tag = " << RECOMMENDED" if m.quantum_score >= self.matcher.threshold else ""
            lines.append(
                f"  #{m.rank:2d}  {m.quantum_score:.3f}  "
                f"£{m.min_amount:,.0f}-£{m.max_amount:,.0f}  "
                f"{m.grant_name[:42]:<42s}{tag}"
            )

            # Append multi-dimensional breakdown if available
            if result.multi_dimensional_scores:
                key = m.grant_id or m.grant_name
                mds = result.multi_dimensional_scores.get(key)
                if mds:
                    lines.append(
                        f"        Tech:{mds.technical_fit:4.0f}  "
                        f"Social:{mds.social_value_alignment:4.0f}  "
                        f"Evidence:{mds.evidence_strength:4.0f}  "
                        f"Win:{mds.win_probability:4.0f}  "
                        f"Comp:{mds.competition_intensity:4.0f}  "
                        f"=> {mds.composite:4.0f}"
                    )

        lines.append("=" * 65)
        lines.append(f"Output: {result.output_path}")
        return "\n".join(lines)
