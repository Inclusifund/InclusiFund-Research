"""
Convex integration for quantum grant matching.

Connects to the live InclusiFund Convex backend to fetch real grant data
and stage quantum matching results for production sync.

Production deployment: terrific-bloodhound-927.convex.cloud
Public query functions: grants:listGrants, grants:getAllGrants, grants:searchGrants
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from quantum_grants.config import get_convex_url, DATA_DIR


logger = logging.getLogger(__name__)

CONVEX_QUERY_ENDPOINT = "/api/query"
CONVEX_MUTATION_ENDPOINT = "/api/mutation"


@dataclass
class ConvexGrant:
    """A grant record from the live Convex database."""
    _id: str
    name: str
    funder: str
    minAmount: float
    maxAmount: float
    status: str
    sectors: list[str]
    regions: list[str]
    applicationDifficulty: int
    supportsStartup: bool
    supportsGrowth: bool
    supportsScale: bool
    website: str
    description: str
    deadline: Optional[str] = None


@dataclass
class QuantumMatchResult:
    """Result payload for quantum matching scores."""
    grant_id: str
    org_id: str
    quantum_score: float
    eligibility_score: float
    alignment_score: float
    capacity_score: float
    is_recommended: bool
    circuit_params_hash: str
    computed_at: str
    model_version: str = "0.1.0-alpha"


class ConvexClient:
    """
    Client for the InclusiFund Convex backend.

    Fetches live grants via HTTP query API and stages quantum
    matching results locally for production sync.
    """

    def __init__(self, convex_url: Optional[str] = None):
        self.convex_url = convex_url or get_convex_url()
        self.staging_dir = Path(DATA_DIR) / "convex_staging"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._grants_cache: Optional[list[dict]] = None

    def _query(self, path: str, args: Optional[dict] = None) -> list[dict]:
        """Execute a Convex query via HTTP API."""
        import urllib.request

        url = f"{self.convex_url}{CONVEX_QUERY_ENDPOINT}"
        payload = json.dumps({"path": path, "args": args or {}}).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        if data.get("status") != "success":
            raise RuntimeError(f"Convex query failed: {data.get('errorMessage', 'unknown')}")
        return data["value"]

    def fetch_open_grants(self) -> list[dict]:
        """Fetch all open grants from the live database."""
        return self._query("grants:listGrants")

    def fetch_all_grants(self) -> list[dict]:
        """Fetch all grants (including closed/paused)."""
        grants = self._query("grants:getAllGrants")
        self._grants_cache = grants
        # Save locally for offline use
        cache_path = Path(DATA_DIR) / "live_grants.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(grants, f, indent=2)
        return grants

    def search_grants(
        self,
        sectors: Optional[list[str]] = None,
        regions: Optional[list[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        cic_stage: Optional[str] = None,
    ) -> list[dict]:
        """Search and filter grants."""
        args = {}
        if sectors:
            args["sectors"] = sectors
        if regions:
            args["regions"] = regions
        if min_amount is not None:
            args["minAmount"] = min_amount
        if max_amount is not None:
            args["maxAmount"] = max_amount
        if cic_stage:
            args["cicStage"] = cic_stage
        return self._query("grants:searchGrants", args)

    def load_cached_grants(self) -> list[dict]:
        """Load grants from local cache (offline mode)."""
        cache_path = Path(DATA_DIR) / "live_grants.json"
        if not cache_path.exists():
            raise FileNotFoundError(
                "No cached grants. Run fetch_all_grants() first."
            )
        with open(cache_path) as f:
            return json.load(f)

    def to_convex_grants(self, raw: list[dict]) -> list[ConvexGrant]:
        """Convert raw Convex records to typed dataclass instances."""
        results = []
        for g in raw:
            results.append(ConvexGrant(
                _id=g.get("_id", ""),
                name=g.get("name", "Unnamed"),
                funder=g.get("funder", "Unknown"),
                minAmount=g.get("minAmount", 0),
                maxAmount=g.get("maxAmount", 0),
                status=g.get("status", "Unknown"),
                sectors=g.get("sectors", []),
                regions=g.get("regions", []),
                applicationDifficulty=g.get("applicationDifficulty", 3),
                supportsStartup=g.get("supportsStartup", False),
                supportsGrowth=g.get("supportsGrowth", False),
                supportsScale=g.get("supportsScale", False),
                website=g.get("website", ""),
                description=g.get("description", ""),
                deadline=g.get("deadline"),
            ))
        return results

    # --- Staging quantum match results ---

    def store_match(self, result: QuantumMatchResult) -> dict:
        """Stage a quantum match result locally."""
        record = asdict(result)
        record["_synced"] = False
        record["_source"] = "quantum_matcher"

        filename = f"{result.grant_id}_{result.org_id}.json"
        filepath = self.staging_dir / filename
        with open(filepath, "w") as f:
            json.dump(record, f, indent=2)
        return {"status": "staged", "path": str(filepath)}

    def batch_store(self, results: list[QuantumMatchResult]) -> dict:
        """Stage a batch of quantum match results."""
        staged = [self.store_match(r) for r in results]
        manifest = {
            "batch_size": len(results),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "staged_files": [s["path"] for s in staged],
            "ready_for_sync": False,
        }
        manifest_path = self.staging_dir / "batch_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        return manifest

    def get_staged_count(self) -> int:
        """Count results waiting to sync."""
        return len(list(self.staging_dir.glob("*.json"))) - (
            1 if (self.staging_dir / "batch_manifest.json").exists() else 0
        )

    def sync_to_convex(self) -> dict:
        """
        Push all staged (unsynced) match results to the Convex backend.

        Reads JSON files from convex_staging/, pushes each via the HTTP
        mutation API, and marks successfully synced files with _synced=True.

        Returns a summary dict with counts and any errors encountered.
        """
        import urllib.request
        import urllib.error

        staged_files = [
            p for p in self.staging_dir.glob("*.json")
            if p.name != "batch_manifest.json"
        ]

        summary = {
            "total_staged": 0,
            "synced": 0,
            "already_synced": 0,
            "failed": 0,
            "errors": [],
        }

        unsynced = []
        for filepath in staged_files:
            with open(filepath) as f:
                data = json.load(f)
            if data.get("_synced"):
                summary["already_synced"] += 1
                continue
            unsynced.append((filepath, data))

        summary["total_staged"] = len(unsynced)

        for filepath, data in unsynced:
            # Map local field names to Convex mutation arg names
            mutation_args = {
                "grantId": data["grant_id"],
                "orgId": data["org_id"],
                "quantumScore": data["quantum_score"],
                "eligibilityScore": data["eligibility_score"],
                "alignmentScore": data["alignment_score"],
                "capacityScore": data["capacity_score"],
                "isRecommended": data["is_recommended"],
                "circuitParamsHash": data["circuit_params_hash"],
                "computedAt": data["computed_at"],
                "modelVersion": data.get("model_version", "0.1.0-alpha"),
            }

            payload = json.dumps({
                "path": "quantumMatches:upsertMatch",
                "args": mutation_args,
            }).encode()

            url = f"{self.convex_url}{CONVEX_MUTATION_ENDPOINT}"
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read())

                if resp_data.get("status") == "success":
                    # Mark file as synced
                    data["_synced"] = True
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    summary["synced"] += 1
                else:
                    error_msg = resp_data.get("errorMessage", "unknown error")
                    logger.warning("Convex mutation failed for %s: %s", filepath.name, error_msg)
                    summary["failed"] += 1
                    summary["errors"].append({
                        "file": filepath.name,
                        "error": error_msg,
                    })
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as exc:
                logger.warning("Sync failed for %s: %s", filepath.name, exc)
                summary["failed"] += 1
                summary["errors"].append({
                    "file": filepath.name,
                    "error": str(exc),
                })

        # Update manifest if it exists
        manifest_path = self.staging_dir / "batch_manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            manifest["ready_for_sync"] = summary["failed"] > 0
            manifest["last_sync_attempt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            manifest["last_sync_summary"] = {
                "synced": summary["synced"],
                "failed": summary["failed"],
            }
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

        return summary

    @staticmethod
    def production_schema() -> dict:
        """The Convex schema for quantum match results (future table)."""
        return {
            "table": "quantumMatches",
            "fields": {
                "grantId": "string",
                "orgId": "string",
                "quantumScore": "float64",
                "eligibilityScore": "float64",
                "alignmentScore": "float64",
                "capacityScore": "float64",
                "isRecommended": "boolean",
                "circuitParamsHash": "string",
                "computedAt": "string",
                "modelVersion": "string",
            },
            "indexes": [
                {"name": "by_grant", "fields": ["grantId"]},
                {"name": "by_org", "fields": ["orgId"]},
                {"name": "by_score", "fields": ["quantumScore"]},
            ],
        }
