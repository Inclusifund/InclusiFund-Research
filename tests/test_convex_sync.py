"""Tests for Convex sync functionality."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from quantum_grants.convex_integration.client import (
    ConvexClient,
    QuantumMatchResult,
)


def _make_client(tmp_path):
    """Create a ConvexClient with staging dir pointed at tmp_path."""
    client = ConvexClient.__new__(ConvexClient)
    client.convex_url = "https://test-deployment.convex.cloud"
    client.staging_dir = tmp_path / "staging"
    client.staging_dir.mkdir()
    client._grants_cache = None
    return client


def _stage_match(client, grant_id="G-0001", org_id="ORG-001", score=0.85):
    """Stage a single match result and return its file path."""
    result = QuantumMatchResult(
        grant_id=grant_id,
        org_id=org_id,
        quantum_score=score,
        eligibility_score=0.9,
        alignment_score=0.7,
        capacity_score=0.6,
        is_recommended=True,
        circuit_params_hash="abc123",
        computed_at="2026-03-12T00:00:00",
        model_version="0.2.0",
    )
    status = client.store_match(result)
    return Path(status["path"])


class TestSyncReadsStaged:
    """sync_to_convex() reads staged files correctly."""

    def test_reads_unsynced_files(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")
        _stage_match(client, "G-0002")

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            summary = client.sync_to_convex()

        assert summary["total_staged"] == 2
        assert summary["synced"] == 2

    def test_skips_already_synced(self, tmp_path):
        client = _make_client(tmp_path)
        path = _stage_match(client, "G-0001")

        # Mark as synced manually
        with open(path) as f:
            data = json.load(f)
        data["_synced"] = True
        with open(path, "w") as f:
            json.dump(data, f)

        summary = client.sync_to_convex()

        assert summary["total_staged"] == 0
        assert summary["already_synced"] == 1
        assert summary["synced"] == 0

    def test_skips_batch_manifest(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")

        # Create a batch manifest
        manifest = {"batch_size": 1, "ready_for_sync": False}
        with open(client.staging_dir / "batch_manifest.json", "w") as f:
            json.dump(manifest, f)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            summary = client.sync_to_convex()

        # Only the match file, not the manifest
        assert summary["total_staged"] == 1
        assert summary["synced"] == 1

    def test_sends_correct_payload(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001", "ORG-001", 0.85)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            client.sync_to_convex()

        # Inspect the request that was sent
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data)

        assert payload["path"] == "quantumMatches:upsertMatch"
        assert payload["args"]["grantId"] == "G-0001"
        assert payload["args"]["orgId"] == "ORG-001"
        assert payload["args"]["quantumScore"] == 0.85
        assert payload["args"]["isRecommended"] is True
        assert payload["args"]["modelVersion"] == "0.2.0"


class TestSyncHandlesFailures:
    """Handles mutation failures gracefully."""

    def test_http_error_does_not_crash(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")

        with patch("urllib.request.urlopen") as mock_urlopen:
            from urllib.error import URLError
            mock_urlopen.side_effect = URLError("Connection refused")

            summary = client.sync_to_convex()

        assert summary["failed"] == 1
        assert summary["synced"] == 0
        assert len(summary["errors"]) == 1
        assert "Connection refused" in summary["errors"][0]["error"]

    def test_mutation_error_response(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "status": "error",
                "errorMessage": "Function not found: quantumMatches:upsertMatch",
            }).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            summary = client.sync_to_convex()

        assert summary["failed"] == 1
        assert summary["synced"] == 0
        assert "Function not found" in summary["errors"][0]["error"]

    def test_partial_failure(self, tmp_path):
        """One succeeds, one fails — both are handled correctly."""
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")
        _stage_match(client, "G-0002")

        call_count = 0

        def mock_urlopen_side_effect(req, timeout=None):
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            if call_count == 1:
                mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            else:
                from urllib.error import URLError
                raise URLError("timeout")
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=mock_urlopen_side_effect):
            summary = client.sync_to_convex()

        assert summary["synced"] == 1
        assert summary["failed"] == 1


class TestSyncMarksFiles:
    """Marks files as synced after successful push."""

    def test_marks_synced_true(self, tmp_path):
        client = _make_client(tmp_path)
        path = _stage_match(client, "G-0001")

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            client.sync_to_convex()

        with open(path) as f:
            data = json.load(f)
        assert data["_synced"] is True

    def test_does_not_mark_on_failure(self, tmp_path):
        client = _make_client(tmp_path)
        path = _stage_match(client, "G-0001")

        with patch("urllib.request.urlopen") as mock_urlopen:
            from urllib.error import URLError
            mock_urlopen.side_effect = URLError("fail")

            client.sync_to_convex()

        with open(path) as f:
            data = json.load(f)
        assert data["_synced"] is False

    def test_updates_manifest_on_sync(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")

        # Create manifest
        manifest = {"batch_size": 1, "ready_for_sync": False}
        manifest_path = client.staging_dir / "batch_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            client.sync_to_convex()

        with open(manifest_path) as f:
            updated = json.load(f)
        assert "last_sync_attempt" in updated
        assert updated["last_sync_summary"]["synced"] == 1
        # ready_for_sync is False when no failures
        assert updated["ready_for_sync"] is False


class TestStagedCountAfterSync:
    """Staged count reflects synced state."""

    def test_staged_count_decreases(self, tmp_path):
        client = _make_client(tmp_path)
        _stage_match(client, "G-0001")
        _stage_match(client, "G-0002")

        assert client.get_staged_count() == 2

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"status": "success"}).encode()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            summary = client.sync_to_convex()

        assert summary["synced"] == 2

        # Files still exist but are marked synced —
        # get_staged_count counts all JSON files (regardless of _synced),
        # so we verify via a re-sync that finds 0 unsynced
        re_summary = client.sync_to_convex()
        assert re_summary["total_staged"] == 0
        assert re_summary["already_synced"] == 2

    def test_empty_staging_returns_zeros(self, tmp_path):
        client = _make_client(tmp_path)
        summary = client.sync_to_convex()
        assert summary["total_staged"] == 0
        assert summary["synced"] == 0
        assert summary["failed"] == 0
