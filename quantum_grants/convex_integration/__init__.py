"""Convex backend integration for quantum grant matching.

Connected to live InclusiFund Convex deployment:
  https://terrific-bloodhound-927.convex.cloud

Provides:
  - ConvexClient: fetch grants, stage quantum match results
  - ConvexGrant / QuantumMatchResult: typed data models
"""

from quantum_grants.convex_integration.client import (
    ConvexClient,
    ConvexGrant,
    QuantumMatchResult,
)

__all__ = ["ConvexClient", "ConvexGrant", "QuantumMatchResult"]
