"""
Configuration loader for quantum grants R&D.

Loads API keys from .env file. Never hardcodes secrets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _load_dotenv(env_path: Optional[Path] = None) -> None:
    """Load .env file into environment variables."""
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def get_origin_quantum_api_key() -> str:
    """Get Origin Quantum Cloud API key from environment."""
    key = os.environ.get("ORIGIN_QUANTUM_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "ORIGIN_QUANTUM_API_KEY not set. "
            "Add it to .env or export it in your shell."
        )
    return key


def get_convex_url() -> Optional[str]:
    """Get Convex deployment URL (None if not configured)."""
    return os.environ.get("CONVEX_URL")


# Workspace paths
WORKSPACE_ROOT = Path(__file__).parent.parent
INTEL_DIR = WORKSPACE_ROOT / "pre-quantum-skills-intel"
FUNDING_INTEL_DIR = INTEL_DIR / "funding-intel copy"
PRE_VAULT_RESEARCH = FUNDING_INTEL_DIR / "Pre-vault-research-results"
DATA_DIR = WORKSPACE_ROOT / "Data" / "Quantum"
TRAINING_LOG_DIR = WORKSPACE_ROOT / "Research" / "Training Logs"
