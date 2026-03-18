"""Tests for quantum_grants.data.grant_enricher."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from quantum_grants.data.grant_enricher import (
    ENRICHMENT_DATA,
    enrich_grant,
    enrich_grants,
    find_enrichment_match,
)


# ---------------------------------------------------------------------------
# find_enrichment_match tests
# ---------------------------------------------------------------------------

class TestFuzzyMatching:
    """Verify the case-insensitive contains matching logic."""

    def test_exact_name_match(self):
        grant = {"name": "Hedley Foundation", "funder": "Hedley Foundation"}
        result = find_enrichment_match(grant)
        assert result is not None
        assert result["maxAmount"] == 5000

    def test_partial_name_match(self):
        """Grant name contains the enrichment key as a substring."""
        grant = {
            "name": "The Clothworkers' Foundation – Open Grants",
            "grantName": "The Clothworkers' Foundation – Open Grants",
            "funder": "The Clothworkers' Foundation – Open Grants",
        }
        result = find_enrichment_match(grant)
        assert result is not None
        assert result["maxAmount"] == 15000

    def test_case_insensitive_match(self):
        grant = {"name": "GARFIELD WESTON FOUNDATION", "funder": "garfield weston"}
        result = find_enrichment_match(grant)
        assert result is not None

    def test_no_match_returns_none(self):
        grant = {"name": "Totally Unknown Funder XYZ", "funder": "Nobody"}
        result = find_enrichment_match(grant)
        assert result is None

    def test_matches_on_funder_field(self):
        grant = {"name": "Some Programme", "funder": "UnLtd Awards"}
        result = find_enrichment_match(grant)
        assert result is not None
        assert result["maxAmount"] == 8000

    def test_matches_on_grant_name_field(self):
        grant = {"name": "", "grantName": "Sport England Movement Fund", "funder": ""}
        result = find_enrichment_match(grant)
        assert result is not None
        assert result["maxAmount"] == 50000


# ---------------------------------------------------------------------------
# enrich_grant tests
# ---------------------------------------------------------------------------

class TestEnrichGrant:
    """Verify that enrich_grant only fills missing/zero fields."""

    def test_fills_zero_amounts(self):
        grant = {"name": "Test", "minAmount": 0, "maxAmount": 0, "amountMin": 0, "amountMax": 0}
        enrichment = {"minAmount": 5000, "maxAmount": 50000}
        updated = enrich_grant(grant, enrichment)
        assert "minAmount" in updated
        assert "maxAmount" in updated
        assert grant["minAmount"] == 5000.0
        assert grant["maxAmount"] == 50000.0
        assert grant["amountMin"] == 5000.0
        assert grant["amountMax"] == 50000.0

    def test_does_not_overwrite_nonzero_amounts(self):
        grant = {"name": "Test", "minAmount": 999, "maxAmount": 888, "amountMin": 999, "amountMax": 888}
        enrichment = {"minAmount": 5000, "maxAmount": 50000}
        updated = enrich_grant(grant, enrichment)
        assert "minAmount" not in updated
        assert "maxAmount" not in updated
        assert grant["minAmount"] == 999
        assert grant["maxAmount"] == 888

    def test_fills_missing_deadline(self):
        grant = {"name": "Test"}
        enrichment = {"deadline": "Rolling"}
        updated = enrich_grant(grant, enrichment)
        assert "deadline" in updated
        assert grant["deadline"] == "Rolling"

    def test_does_not_overwrite_existing_deadline(self):
        grant = {"name": "Test", "deadline": "2026-Q2"}
        enrichment = {"deadline": "Rolling"}
        updated = enrich_grant(grant, enrichment)
        assert "deadline" not in updated
        assert grant["deadline"] == "2026-Q2"

    def test_fills_supports_startup(self):
        grant = {"name": "Test"}
        enrichment = {"supportsStartup": True}
        updated = enrich_grant(grant, enrichment)
        assert "supportsStartup" in updated
        assert grant["supportsStartup"] is True

    def test_does_not_overwrite_existing_supports_startup(self):
        grant = {"name": "Test", "supportsStartup": False}
        enrichment = {"supportsStartup": True}
        updated = enrich_grant(grant, enrichment)
        assert "supportsStartup" not in updated
        assert grant["supportsStartup"] is False

    def test_handles_none_amounts_as_missing(self):
        grant = {"name": "Test", "minAmount": None, "maxAmount": None}
        enrichment = {"minAmount": 1000, "maxAmount": 5000}
        updated = enrich_grant(grant, enrichment)
        assert "minAmount" in updated
        assert "maxAmount" in updated

    def test_does_not_fill_zero_enrichment(self):
        """If the enrichment value itself is 0, don't bother writing it."""
        grant = {"name": "Test", "minAmount": 0, "maxAmount": 0}
        enrichment = {"minAmount": 0, "maxAmount": 0}
        updated = enrich_grant(grant, enrichment)
        assert "minAmount" not in updated
        assert "maxAmount" not in updated


# ---------------------------------------------------------------------------
# enrich_grants integration test
# ---------------------------------------------------------------------------

class TestEnrichGrantsIntegration:
    """End-to-end test using a temp file with sample grants."""

    SAMPLE_GRANTS = [
        {
            "name": "Hedley Foundation",
            "grantName": "Hedley Foundation",
            "funder": "Hedley Foundation",
            "minAmount": 0,
            "maxAmount": 0,
            "amountMin": 0,
            "amountMax": 0,
        },
        {
            "name": "Already Funded Grant",
            "grantName": "Already Funded Grant",
            "funder": "Sport England Movement Fund",
            "minAmount": 999,
            "maxAmount": 8888,
            "amountMin": 999,
            "amountMax": 8888,
            "deadline": "2026-Q1",
        },
        {
            "name": "No Match Grant",
            "grantName": "No Match Grant",
            "funder": "Unknown Funder",
            "minAmount": 0,
            "maxAmount": 0,
            "amountMin": 0,
            "amountMax": 0,
        },
    ]

    def test_enriches_sample_data(self, tmp_path):
        grants_file = tmp_path / "grants.json"
        grants_file.write_text(json.dumps(self.SAMPLE_GRANTS))

        result = enrich_grants(grants_path=grants_file, save=True)

        assert result["total"] == 3
        assert result["enriched_count"] >= 1  # Hedley should match
        assert result["skipped"] >= 1  # No Match should be skipped

        # Verify file was saved
        saved = json.loads(grants_file.read_text())
        hedley = saved[0]
        assert hedley["maxAmount"] == 5000.0
        assert hedley["minAmount"] == 250.0

        # Verify non-zero values were NOT overwritten
        sport = saved[1]
        assert sport["minAmount"] == 999
        assert sport["maxAmount"] == 8888

    def test_no_save_mode(self, tmp_path):
        grants_file = tmp_path / "grants.json"
        original = copy.deepcopy(self.SAMPLE_GRANTS)
        grants_file.write_text(json.dumps(original))

        enrich_grants(grants_path=grants_file, save=False)

        # File should be unchanged
        saved = json.loads(grants_file.read_text())
        assert saved[0]["maxAmount"] == 0
