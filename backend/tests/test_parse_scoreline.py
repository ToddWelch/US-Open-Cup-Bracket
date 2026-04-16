"""Tests for the parse_scoreline function in the US Soccer fallback parser."""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.scraper import parse_scoreline


class TestStandardScore:
    def test_basic_score(self):
        result = parse_scoreline("FC Tulsa 3 - 1 Forward Madison FC")
        assert result is not None
        assert result["home"] == "FC Tulsa"
        assert result["away"] == "Forward Madison FC"
        assert result["homeScore"] == 3
        assert result["awayScore"] == 1
        assert result["note"] is None


class TestPenalties:
    def test_pk_singular_notation(self):
        result = parse_scoreline("Team A 1 (4) - 1 (2) Team B (PK)")
        assert result is not None
        assert result["note"] == "PEN"

    def test_penalty_parentheticals(self):
        result = parse_scoreline(
            "New England Revolution 1 (3) - 1 (1) Rhode Island FC"
        )
        assert result is not None
        assert result["home"] == "New England Revolution"
        assert result["away"] == "Rhode Island FC"
        assert result["homeScore"] == 1
        assert result["awayScore"] == 1
        assert result["homePen"] == 3
        assert result["awayPen"] == 1
        assert result["note"] == "PEN"


class TestForfeit:
    def test_forfeit_notation(self):
        result = parse_scoreline(
            "South Georgia Tormenta FC 0 - 1 FC America CFL Spurs (Forfeit)"
        )
        assert result is not None
        assert result["note"] == "FF"
        # Away team name should be clean (no notation text appended)
        assert result["away"] == "FC America CFL Spurs"
        assert result["home"] == "South Georgia Tormenta FC"
        assert result["homeScore"] == 0
        assert result["awayScore"] == 1


class TestAET:
    def test_aet_notation(self):
        result = parse_scoreline("Team A 2 - 1 Team B (AET)")
        assert result is not None
        assert result["note"] == "AET"
        assert result["home"] == "Team A"
        assert result["away"] == "Team B"
        assert result["homeScore"] == 2
        assert result["awayScore"] == 1


class TestAETAndPKs:
    def test_aet_and_pks(self):
        """When AET & PKs notation is present, PKs takes precedence."""
        result = parse_scoreline(
            "Team A 1 (3) - 1 (1) Team B (AET & PKs)"
        )
        assert result is not None
        assert result["note"] == "PEN"
        assert result["homeScore"] == 1
        assert result["awayScore"] == 1
        assert result["homePen"] == 3
        assert result["awayPen"] == 1


class TestInconsistentSpacing:
    def test_tight_spacing(self):
        """Handles missing/extra spaces around the dash."""
        result = parse_scoreline("Pittsburgh Riverhounds SC 2- 1 Steel City FC")
        assert result is not None
        assert result["home"] == "Pittsburgh Riverhounds SC"
        assert result["away"] == "Steel City FC"
        assert result["homeScore"] == 2
        assert result["awayScore"] == 1


class TestTeamNamesWithDigits:
    def test_leading_digits_in_team_name(self):
        result = parse_scoreline("1904 FC 2 - 1 Sporting KC")
        assert result is not None
        assert result["home"] == "1904 FC"
        assert result["homeScore"] == 2
        assert result["away"] == "Sporting KC"
        assert result["awayScore"] == 1


class TestEmptyInput:
    def test_empty_string(self):
        assert parse_scoreline("") is None

    def test_whitespace_only(self):
        assert parse_scoreline("   ") is None

    def test_none_input(self):
        assert parse_scoreline(None) is None


class TestNoScore:
    def test_walkover_text_only(self):
        """Text without a proper scoreline should return None."""
        assert parse_scoreline("Team A walkover") is None

    def test_no_dash(self):
        assert parse_scoreline("FC Tulsa vs Forward Madison FC") is None
