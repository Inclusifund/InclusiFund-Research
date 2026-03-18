#!/usr/bin/env python3
"""
CLI entry point for the InclusiFund Quantum Grant Pipeline.

Usage:
    python run_pipeline.py --profile path/to/profile.json   # From JSON file
    python run_pipeline.py --demo                            # Run with a demo profile
    python run_pipeline.py --demo --top-k 30                 # More results
    python run_pipeline.py --profile p.json --refresh        # Force-fetch from Convex
"""

import argparse
import json
import sys

from quantum_grants.pipeline import QuantumPipeline
from quantum_grants.agents.quantum_matcher import CICProfile
from quantum_grants.agents.deadline_tracker import DeadlineTracker
from quantum_grants.agents.grant_writer import GrantWriter
from quantum_grants.training.real_data_trainer import DEMO_PROFILES


def load_profile_from_json(path: str) -> CICProfile:
    """Load a CICProfile from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return CICProfile(**data)


def main():
    parser = argparse.ArgumentParser(
        description="InclusiFund Quantum Grant Pipeline"
    )
    parser.add_argument(
        "--profile", type=str, help="Path to a JSON profile file"
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run with the first demo profile (Demo Youth CIC)"
    )
    parser.add_argument(
        "--top-k", type=int, default=20, help="Max matches to return (default: 20)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5, help="Recommendation threshold (default: 0.5)"
    )
    parser.add_argument(
        "--include-closed", action="store_true", help="Include closed/paused grants"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="Force-fetch from Convex (skip cache)"
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Path to trained model JSON"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON instead of summary"
    )
    parser.add_argument(
        "--agent-output", choices=["deadline", "writer"],
        help="Emit structured output for a downstream agent"
    )
    parser.add_argument(
        "--agents", action="store_true",
        help="Also run Agent 2 (Deadline Tracker) and Agent 10 (Grant Writer)"
    )
    parser.add_argument(
        "--sync", action="store_true",
        help="After running, sync staged results to Convex backend"
    )
    parser.add_argument(
        "--backend", choices=["auto", "numpy", "cloud"], default="auto",
        help="Quantum execution backend: auto (default), numpy, or cloud"
    )

    args = parser.parse_args()

    if not args.profile and not args.demo:
        parser.print_help()
        print("\nError: provide --profile <path> or --demo", file=sys.stderr)
        sys.exit(1)

    if args.demo:
        profile = DEMO_PROFILES[0]
        print(f"Using demo profile: {profile.org_name} ({profile.org_id})")
    else:
        profile = load_profile_from_json(args.profile)

    pipeline = QuantumPipeline(
        threshold=args.threshold,
        top_k=args.top_k,
        model_path=args.model,
        use_cache=not args.refresh,
        backend=args.backend,
    )

    result = pipeline.run(
        profile,
        top_k=args.top_k,
        include_closed=args.include_closed,
    )

    if args.agent_output == "deadline":
        print(json.dumps(result.for_deadline_agent(), indent=2))
    elif args.agent_output == "writer":
        print(json.dumps(result.for_writer_agent(), indent=2))
    elif args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(pipeline.summary(result))

    if args.agents:
        print("\n--- Agent 2: Deadline Tracker ---")
        tracker = DeadlineTracker()
        deadline_report = tracker.process(result)
        print(tracker.summary(deadline_report))

        print("\n--- Agent 10: Grant Writer ---")
        writer = GrantWriter()
        briefs = writer.process(result)
        print(writer.summary(briefs))

    if args.sync:
        print("\nSyncing staged results to Convex...")
        sync_summary = pipeline.sync()
        print(f"  Synced: {sync_summary['synced']}")
        print(f"  Failed: {sync_summary['failed']}")
        if sync_summary['errors']:
            for err in sync_summary['errors']:
                print(f"  Error ({err['file']}): {err['error']}")


if __name__ == "__main__":
    main()
