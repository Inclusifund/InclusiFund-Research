"""Tests for the intel labels module."""

import pytest

from quantum_grants.data.intel_labels import (
    rating_to_label,
    funder_name_matches,
    is_funder_blocked,
    compute_characteristic_label,
    get_blocked_label,
    IntelLabel,
    BLOCKED_FUNDERS,
    FUNDER_CHARACTERISTICS,
)


class TestRatingToLabel:
    """Test rating string -> numeric label conversion."""

    def test_high_ratings(self):
        assert rating_to_label("HIGH") == 0.90
        assert rating_to_label("STRONG") == 0.90
        assert rating_to_label("VERY STRONG") == 0.95
        assert rating_to_label("TIER 1") == 0.90

    def test_medium_ratings(self):
        assert rating_to_label("MEDIUM") == 0.58
        assert rating_to_label("MODERATE") == 0.55
        assert rating_to_label("MODERATE-HIGH") == 0.65
        assert rating_to_label("MODERATE-GOOD") == 0.60
        assert rating_to_label("TIER 2") == 0.58

    def test_low_ratings(self):
        assert rating_to_label("LOW") == 0.22
        assert rating_to_label("LOW-MODERATE") == 0.30

    def test_future_ratings(self):
        assert rating_to_label("FUTURE") == 0.40
        assert rating_to_label("CONDITIONAL") == 0.40

    def test_zero_ratings(self):
        assert rating_to_label("DO NOT PURSUE") == 0.0
        assert rating_to_label("NOT ELIGIBLE") == 0.0
        assert rating_to_label("NOT APPLICABLE") == 0.0

    def test_case_insensitive(self):
        assert rating_to_label("high") == 0.90
        assert rating_to_label("Low") == 0.22
        assert rating_to_label("do not pursue") == 0.0

    def test_unknown_returns_default(self):
        assert rating_to_label("SOMETHING WEIRD") == 0.50


class TestFunderNameMatches:
    """Test fuzzy funder name matching."""

    def test_exact_substring(self):
        assert funder_name_matches("Henry Smith Charity", "Henry Smith") is True
        assert funder_name_matches("BBC Children in Need", "BBC Children in Need") is True

    def test_partial_match(self):
        assert funder_name_matches("Garfield Weston Foundation", "Garfield Weston") is True
        assert funder_name_matches("Clothworkers Foundation Open Grants", "Clothworkers") is True

    def test_no_match(self):
        assert funder_name_matches("Henry Smith Charity", "Garfield Weston") is False
        assert funder_name_matches("NLCF Awards for All", "Tudor Trust") is False

    def test_case_insensitive(self):
        assert funder_name_matches("HENRY SMITH CHARITY", "henry smith") is True

    def test_nlcf_variants(self):
        assert funder_name_matches("National Lottery Community Fund", "NLCF") is True
        assert funder_name_matches("National Lottery Awards for All", "Awards for All") is True

    def test_word_overlap(self):
        assert funder_name_matches("Wimbledon Foundation Community Fund",
                                    "Wimbledon Foundation") is True
        assert funder_name_matches("Baobab Foundation", "Baobab") is True


class TestIsBlockedFunder:
    """Test blocked funder detection."""

    def test_garfield_weston_blocks_cics(self):
        assert is_funder_blocked("Garfield Weston Foundation", "cic") is True

    def test_garfield_weston_allows_cio(self):
        assert is_funder_blocked("Garfield Weston Foundation", "cio") is False

    def test_henry_smith_blocks_low_income(self):
        assert is_funder_blocked(
            "Henry Smith Charity", "cic",
            annual_turnover=10_000, years_operating=0.5
        ) is True

    def test_henry_smith_allows_established(self):
        # Established org with enough income and age
        assert is_funder_blocked(
            "Henry Smith Charity", "cic",
            annual_turnover=100_000, years_operating=3.0
        ) is False

    def test_masonic_blocks_low_income(self):
        assert is_funder_blocked(
            "Masonic Charitable Foundation", "cio",
            annual_turnover=0
        ) is True

    def test_lloyds_blocks_cics(self):
        assert is_funder_blocked("Lloyds Bank Foundation", "cic") is True

    def test_tudor_trust_invitation_only(self):
        assert is_funder_blocked("Tudor Trust", "charity") is True

    def test_lankelly_chase_closed(self):
        assert is_funder_blocked("Lankelly Chase", "cio") is True

    def test_non_blocked_funder(self):
        assert is_funder_blocked("Commonweal Housing", "cic") is False
        assert is_funder_blocked("BBC Children in Need", "cic") is False


class TestFunderCharacteristics:
    """Test the characteristic-based funder data."""

    def test_has_entries(self):
        assert len(FUNDER_CHARACTERISTICS) > 0

    def test_startup_friendly_funders_exist(self):
        startup_friendly = [
            k for k, v in FUNDER_CHARACTERISTICS.items()
            if v.get("startup_friendly")
        ]
        assert len(startup_friendly) >= 3


class TestComputeCharacteristicLabel:
    """Test characteristic-based label computation."""

    def test_startup_friendly_funder_for_startup(self):
        label = compute_characteristic_label(
            "Awards for All", "",
            legal_structure="cic",
            annual_turnover=0,
            years_operating=0.5,
        )
        assert label is not None
        assert label >= 0.80

    def test_blocked_structure(self):
        label = compute_characteristic_label(
            "Garfield Weston Foundation", "",
            legal_structure="cic",
            annual_turnover=50_000,
            years_operating=3,
        )
        assert label == 0.0

    def test_low_income_for_income_funder(self):
        label = compute_characteristic_label(
            "Henry Smith Charity", "",
            legal_structure="cio",
            annual_turnover=5_000,
            years_operating=0.5,
        )
        assert label is not None
        assert label <= 0.30

    def test_unknown_funder_returns_none(self):
        label = compute_characteristic_label(
            "Unknown Funder XYZ", "",
            legal_structure="cic",
        )
        assert label is None

    def test_established_org_for_established_funder(self):
        label = compute_characteristic_label(
            "Esmee Fairbairn Foundation", "",
            legal_structure="charity",
            annual_turnover=100_000,
            years_operating=5,
        )
        assert label is not None
        assert label >= 0.50

    def test_startup_for_established_funder(self):
        label = compute_characteristic_label(
            "Comic Relief", "",
            legal_structure="cic",
            annual_turnover=0,
            years_operating=0.5,
        )
        assert label is not None
        assert label <= 0.40


class TestGetBlockedLabel:
    """Test blocked label lookup for grant-client pairs."""

    def test_blocked_cic_for_garfield(self):
        result = get_blocked_label(
            "Garfield Weston Foundation Grant", "",
            legal_structure="cic"
        )
        assert result == 0.0

    def test_not_blocked_cio_for_garfield(self):
        result = get_blocked_label(
            "Garfield Weston Foundation Grant", "",
            legal_structure="cio"
        )
        assert result is None

    def test_blocked_low_income_masonic(self):
        result = get_blocked_label(
            "Masonic Small Grants", "",
            legal_structure="cio",
            annual_turnover=0
        )
        assert result == 0.0

    def test_not_blocked_unrelated_funder(self):
        result = get_blocked_label(
            "Wimbledon Foundation", "",
            legal_structure="cic"
        )
        assert result is None
