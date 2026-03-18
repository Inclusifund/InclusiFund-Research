"""Tests for Agent 10 — Grant Writer."""

import json
from dataclasses import asdict

import pytest

from quantum_grants.agents.grant_writer import (
    GrantWriter,
    GrantBrief,
    _analyse_scores,
    _build_amount_range,
    _recommend_ask,
    _format_amount,
)


# --- Minimal mock for PipelineResult ---

class MockPipelineResult:
    """Minimal stand-in for PipelineResult for testing."""

    def __init__(self, org_id: str, entries: list[dict]):
        self.org_id = org_id
        self._entries = entries

    def for_writer_agent(self) -> list[dict]:
        return self._entries


# --- Amount formatting ---

class TestFormatAmount:

    def test_thousands(self):
        assert _format_amount(5000) == "\u00a35,000"

    def test_millions(self):
        assert _format_amount(1_500_000) == "\u00a31.5M"

    def test_small(self):
        assert _format_amount(500) == "\u00a3500"

    def test_zero(self):
        assert _format_amount(0) == "\u00a3TBC"


class TestBuildAmountRange:

    def test_normal_range(self):
        result = _build_amount_range(1000, 10000)
        assert "\u00a31,000" in result
        assert "\u00a310,000" in result

    def test_zero_min(self):
        result = _build_amount_range(0, 20000)
        assert "Up to" in result

    def test_zero_max(self):
        result = _build_amount_range(5000, 0)
        assert "From" in result

    def test_both_zero(self):
        assert _build_amount_range(0, 0) == "Amount TBC"

    def test_equal_amounts(self):
        result = _build_amount_range(5000, 5000)
        assert result == "\u00a35,000"


class TestRecommendAsk:

    def test_normal_range(self):
        ask = _recommend_ask(1000, 20000)
        # Should be around 65% of 20000 = 13000
        assert "\u00a3" in ask

    def test_both_zero(self):
        assert _recommend_ask(0, 0) == "Discuss with funder"

    def test_zero_max(self):
        ask = _recommend_ask(5000, 0)
        assert "\u00a35,000" in ask


# --- Score analysis ---

class TestAnalyseScores:

    def test_full_eligibility(self):
        item = {
            "eligibility": 1.0, "sector_overlap": 0.8,
            "theme_overlap": 0.6, "capacity": 0.8, "quantum_score": 0.85,
        }
        strengths, gaps, talking_points = _analyse_scores(item)
        assert "Full eligibility confirmed" in strengths
        assert len(gaps) == 0

    def test_low_eligibility(self):
        item = {
            "eligibility": 0.0, "sector_overlap": 0.5,
            "theme_overlap": 0.5, "capacity": 0.5, "quantum_score": 0.5,
        }
        strengths, gaps, talking_points = _analyse_scores(item)
        assert any("Eligibility not confirmed" in g for g in gaps)

    def test_low_sector_overlap(self):
        item = {
            "eligibility": 1.0, "sector_overlap": 0.1,
            "theme_overlap": 0.6, "capacity": 0.5, "quantum_score": 0.5,
        }
        strengths, gaps, talking_points = _analyse_scores(item)
        assert any("Low sector overlap" in g for g in gaps)

    def test_low_capacity(self):
        item = {
            "eligibility": 1.0, "sector_overlap": 0.6,
            "theme_overlap": 0.6, "capacity": 0.2, "quantum_score": 0.5,
        }
        strengths, gaps, talking_points = _analyse_scores(item)
        assert any("too large for current capacity" in g for g in gaps)

    def test_low_theme_overlap(self):
        item = {
            "eligibility": 1.0, "sector_overlap": 0.6,
            "theme_overlap": 0.1, "capacity": 0.5, "quantum_score": 0.5,
        }
        strengths, gaps, talking_points = _analyse_scores(item)
        assert any("Low thematic alignment" in g for g in gaps)

    def test_high_quantum_score_talking_point(self):
        item = {
            "eligibility": 1.0, "sector_overlap": 0.8,
            "theme_overlap": 0.8, "capacity": 0.9, "quantum_score": 0.85,
        }
        _, _, talking_points = _analyse_scores(item)
        assert any("Top-tier match" in tp for tp in talking_points)

    def test_strong_across_all(self):
        item = {
            "eligibility": 1.0, "sector_overlap": 0.8,
            "theme_overlap": 0.8, "capacity": 0.8, "quantum_score": 0.9,
        }
        strengths, gaps, talking_points = _analyse_scores(item)
        assert len(strengths) >= 3
        assert len(gaps) == 0


# --- Full writer integration test ---

class TestGrantWriter:

    def _make_entry(self, grant_id="g1", eligibility=1.0, sector=0.6,
                    theme=0.6, capacity=0.7, score=0.8):
        return {
            "grant_id": grant_id,
            "grant_name": f"Grant {grant_id}",
            "funder": "Test Funder",
            "min_amount": 1000,
            "max_amount": 20000,
            "quantum_score": score,
            "eligibility": eligibility,
            "sector_overlap": sector,
            "theme_overlap": theme,
            "capacity": capacity,
            "website": "https://example.com",
        }

    def test_process_produces_briefs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.grant_writer.DATA_DIR", str(tmp_path)
        )

        entries = [self._make_entry("g1"), self._make_entry("g2")]
        mock_result = MockPipelineResult("test-org", entries)

        writer = GrantWriter()
        briefs = writer.process(mock_result)

        assert len(briefs) == 2
        assert all(isinstance(b, GrantBrief) for b in briefs)
        assert briefs[0].grant_id == "g1"
        assert briefs[1].grant_id == "g2"

    def test_saves_individual_jsons(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.grant_writer.DATA_DIR", str(tmp_path)
        )

        entries = [self._make_entry("abc123")]
        mock_result = MockPipelineResult("myorg", entries)

        writer = GrantWriter()
        writer.process(mock_result)

        out_file = tmp_path / "briefs" / "myorg_abc123_brief.json"
        assert out_file.exists()

        data = json.loads(out_file.read_text())
        assert data["grant_id"] == "abc123"
        assert "strengths" in data
        assert "gaps" in data
        assert "talking_points" in data

    def test_brief_has_recommended_ask(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.grant_writer.DATA_DIR", str(tmp_path)
        )

        entries = [self._make_entry()]
        mock_result = MockPipelineResult("org1", entries)

        writer = GrantWriter()
        briefs = writer.process(mock_result)

        assert briefs[0].recommended_ask != ""
        assert "\u00a3" in briefs[0].recommended_ask

    def test_summary_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.grant_writer.DATA_DIR", str(tmp_path)
        )

        entries = [self._make_entry()]
        mock_result = MockPipelineResult("org1", entries)

        writer = GrantWriter()
        briefs = writer.process(mock_result)
        summary = writer.summary(briefs)

        assert "Grant Writer" in summary
        assert "Grant g1" in summary

    def test_empty_input(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.grant_writer.DATA_DIR", str(tmp_path)
        )

        mock_result = MockPipelineResult("empty-org", [])
        writer = GrantWriter()
        briefs = writer.process(mock_result)

        assert briefs == []
        summary = writer.summary(briefs)
        assert "No briefs generated" in summary

    def test_gaps_detected_for_weak_profile(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "quantum_grants.agents.grant_writer.DATA_DIR", str(tmp_path)
        )

        entries = [self._make_entry(
            eligibility=0.0, sector=0.1, theme=0.1, capacity=0.2, score=0.3,
        )]
        mock_result = MockPipelineResult("org1", entries)

        writer = GrantWriter()
        briefs = writer.process(mock_result)

        assert len(briefs[0].gaps) >= 3
        assert len(briefs[0].strengths) == 0
