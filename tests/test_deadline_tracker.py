"""Tests for Agent 2 — Deadline Tracker."""

import json
from datetime import date
from dataclasses import dataclass
from typing import Optional

import pytest

from quantum_grants.agents.deadline_tracker import (
    DeadlineTracker,
    DeadlineEntry,
    DeadlineReport,
    parse_deadline,
    _classify_urgency,
    _sort_key,
)


# --- Minimal mock for PipelineResult ---

class MockPipelineResult:
    """Minimal stand-in for PipelineResult for testing."""

    def __init__(self, org_id: str, entries: list[dict]):
        self.org_id = org_id
        self._entries = entries

    def for_deadline_agent(self) -> list[dict]:
        return self._entries


# --- Deadline parsing tests ---

class TestParseDeadline:
    """Test the deadline string parser."""

    def test_iso_date(self):
        d, rolling = parse_deadline("2026-04-15", date(2026, 3, 12))
        assert d == date(2026, 4, 15)
        assert rolling is False

    def test_rolling_simple(self):
        d, rolling = parse_deadline("Rolling", date(2026, 3, 12))
        assert d is None
        assert rolling is True

    def test_rolling_with_text(self):
        d, rolling = parse_deadline("Rolling — no deadline", date(2026, 3, 12))
        assert d is None
        assert rolling is True

    def test_month_year(self):
        d, rolling = parse_deadline("April 2026 panel", date(2026, 3, 12))
        assert d == date(2026, 4, 30)
        assert rolling is False

    def test_season_year(self):
        d, rolling = parse_deadline("Summer 2026", date(2026, 3, 12))
        assert d == date(2026, 6, 30)
        assert rolling is False

    def test_empty_string(self):
        d, rolling = parse_deadline("", date(2026, 3, 12))
        assert d is None
        assert rolling is False

    def test_none(self):
        d, rolling = parse_deadline(None, date(2026, 3, 12))
        assert d is None
        assert rolling is False

    def test_month_without_year(self):
        """Month name without year should use the today year."""
        d, rolling = parse_deadline("December", date(2026, 3, 12))
        assert d == date(2026, 12, 31)
        assert rolling is False

    def test_spring(self):
        d, rolling = parse_deadline("Spring 2026", date(2026, 3, 12))
        assert d == date(2026, 4, 30)
        assert rolling is False


# --- Urgency classification tests ---

class TestClassifyUrgency:

    def test_rolling(self):
        assert _classify_urgency(None, is_rolling=True) == "ROLLING"

    def test_immediate(self):
        assert _classify_urgency(15, is_rolling=False) == "IMMEDIATE"
        assert _classify_urgency(0, is_rolling=False) == "IMMEDIATE"
        assert _classify_urgency(30, is_rolling=False) == "IMMEDIATE"

    def test_upcoming(self):
        assert _classify_urgency(31, is_rolling=False) == "UPCOMING"
        assert _classify_urgency(60, is_rolling=False) == "UPCOMING"
        assert _classify_urgency(90, is_rolling=False) == "UPCOMING"

    def test_monitor(self):
        assert _classify_urgency(91, is_rolling=False) == "MONITOR"
        assert _classify_urgency(365, is_rolling=False) == "MONITOR"

    def test_none_not_rolling(self):
        assert _classify_urgency(None, is_rolling=False) == "MONITOR"


# --- Sort order tests ---

class TestSortKey:

    def _make_entry(self, urgency, days, score):
        return DeadlineEntry(
            grant_id="g1", grant_name="Test", funder="F",
            deadline=None, urgency=urgency, quantum_score=score,
            website="", days_remaining=days,
        )

    def test_rolling_before_immediate(self):
        rolling = self._make_entry("ROLLING", None, 0.8)
        immediate = self._make_entry("IMMEDIATE", 5, 0.9)
        assert _sort_key(rolling) < _sort_key(immediate)

    def test_immediate_before_upcoming(self):
        immediate = self._make_entry("IMMEDIATE", 10, 0.5)
        upcoming = self._make_entry("UPCOMING", 50, 0.9)
        assert _sort_key(immediate) < _sort_key(upcoming)

    def test_within_tier_fewer_days_first(self):
        a = self._make_entry("IMMEDIATE", 5, 0.5)
        b = self._make_entry("IMMEDIATE", 20, 0.5)
        assert _sort_key(a) < _sort_key(b)

    def test_within_tier_same_days_higher_score_first(self):
        a = self._make_entry("IMMEDIATE", 10, 0.9)
        b = self._make_entry("IMMEDIATE", 10, 0.5)
        assert _sort_key(a) < _sort_key(b)


# --- Full tracker integration test ---

class TestDeadlineTracker:

    def test_process_produces_report(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.deadline_tracker.DATA_DIR", str(tmp_path)
        )

        entries = [
            {
                "grant_id": "g1", "grant_name": "Rolling Grant",
                "funder": "Funder A", "website": "https://a.com",
                "quantum_score": 0.85, "status": "Rolling",
            },
            {
                "grant_id": "g2", "grant_name": "April Grant",
                "funder": "Funder B", "website": "https://b.com",
                "quantum_score": 0.72, "status": "2026-04-01",
            },
            {
                "grant_id": "g3", "grant_name": "Far Grant",
                "funder": "Funder C", "website": "https://c.com",
                "quantum_score": 0.60, "status": "December 2026",
            },
        ]

        mock_result = MockPipelineResult("test-org", entries)
        tracker = DeadlineTracker(today=date(2026, 3, 12))
        report = tracker.process(mock_result)

        assert isinstance(report, DeadlineReport)
        assert report.org_id == "test-org"
        assert len(report.entries) == 3

        # Rolling should come first
        assert report.entries[0].urgency == "ROLLING"
        assert report.entries[0].grant_id == "g1"

        # April 1 is 20 days away -> IMMEDIATE
        assert report.entries[1].urgency == "IMMEDIATE"
        assert report.entries[1].days_remaining == 20

        # December is MONITOR
        assert report.entries[2].urgency == "MONITOR"

        # Check counts
        assert report.summary_counts["ROLLING"] == 1
        assert report.summary_counts["IMMEDIATE"] == 1
        assert report.summary_counts["MONITOR"] == 1

    def test_saves_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.deadline_tracker.DATA_DIR", str(tmp_path)
        )

        entries = [
            {
                "grant_id": "g1", "grant_name": "Test",
                "funder": "F", "website": "",
                "quantum_score": 0.5, "status": "Rolling",
            },
        ]

        mock_result = MockPipelineResult("org123", entries)
        tracker = DeadlineTracker(today=date(2026, 3, 12))
        tracker.process(mock_result)

        out_file = tmp_path / "deadlines" / "org123_deadlines.json"
        assert out_file.exists()

        data = json.loads(out_file.read_text())
        assert data["org_id"] == "org123"
        assert len(data["entries"]) == 1

    def test_summary_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.deadline_tracker.DATA_DIR", str(tmp_path)
        )

        entries = [
            {
                "grant_id": "g1", "grant_name": "Test Grant",
                "funder": "F", "website": "",
                "quantum_score": 0.7, "status": "Rolling",
            },
        ]

        mock_result = MockPipelineResult("org1", entries)
        tracker = DeadlineTracker(today=date(2026, 3, 12))
        report = tracker.process(mock_result)
        summary = tracker.summary(report)

        assert "Deadline Tracker" in summary
        assert "ROLLING" in summary
        assert "Test Grant" in summary

    def test_empty_input(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.deadline_tracker.DATA_DIR", str(tmp_path)
        )

        mock_result = MockPipelineResult("empty-org", [])
        tracker = DeadlineTracker(today=date(2026, 3, 12))
        report = tracker.process(mock_result)

        assert len(report.entries) == 0
        assert all(v == 0 for v in report.summary_counts.values())
