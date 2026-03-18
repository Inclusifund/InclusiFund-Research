#!/usr/bin/env python3
"""
Standalone sync command for pushing staged quantum match results to Convex.

Usage:
    python -m quantum_grants.convex_integration.sync
    python -m quantum_grants.convex_integration.sync --dry-run
"""

import argparse
import json
import logging
import sys

from quantum_grants.convex_integration.client import ConvexClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Sync staged quantum match results to Convex backend"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be synced without actually pushing"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output sync summary as JSON"
    )
    args = parser.parse_args()

    client = ConvexClient()

    staged_count = client.get_staged_count()
    logger.info("Found %d staged result(s) in %s", staged_count, client.staging_dir)

    if staged_count == 0:
        logger.info("Nothing to sync.")
        sys.exit(0)

    if args.dry_run:
        # List unsynced files without pushing
        unsynced = []
        for filepath in client.staging_dir.glob("*.json"):
            if filepath.name == "batch_manifest.json":
                continue
            with open(filepath) as f:
                data = json.load(f)
            if not data.get("_synced"):
                unsynced.append({
                    "file": filepath.name,
                    "grant_id": data.get("grant_id"),
                    "org_id": data.get("org_id"),
                    "quantum_score": data.get("quantum_score"),
                })
        logger.info("Dry run — %d file(s) would be synced:", len(unsynced))
        for item in unsynced:
            logger.info(
                "  %s  grant=%s  org=%s  score=%.3f",
                item["file"], item["grant_id"], item["org_id"],
                item.get("quantum_score", 0),
            )
        sys.exit(0)

    summary = client.sync_to_convex()

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        logger.info("Sync complete:")
        logger.info("  Total staged: %d", summary["total_staged"])
        logger.info("  Synced:       %d", summary["synced"])
        logger.info("  Already done: %d", summary["already_synced"])
        logger.info("  Failed:       %d", summary["failed"])
        if summary["errors"]:
            logger.warning("Errors:")
            for err in summary["errors"]:
                logger.warning("  %s: %s", err["file"], err["error"])

    sys.exit(1 if summary["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
