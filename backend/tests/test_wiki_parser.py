"""Tests for the parse_wiki_box function (Wikipedia wikitext parser).

Covers bold-marker winner detection, penalty notation, and edge cases
like italic-only markup and the no-score return path.
"""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.scraper import parse_wiki_box


def make_box(team1, team2, score, date="1 January 2026"):
    """Build a minimal wikitext football box for testing."""
    return f"""
| date = {date}
| team1 = {team1}
| score = {score}
| team2 = {team2}
}}}}"""


class TestBoldWinnerDetection:
    def test_bold_team1_is_winner(self):
        """Team1 wrapped in ''' (bold) should be detected as winner."""
        box = make_box("'''FC Dallas'''", "Austin FC", "2 - 1")
        result = parse_wiki_box(box)
        assert result is not None
        assert result["winner"] == "FC Dallas"

    def test_bold_team2_is_winner(self):
        """Team2 wrapped in ''' (bold) should be detected as winner."""
        box = make_box("FC Dallas", "'''Austin FC'''", "1 - 2")
        result = parse_wiki_box(box)
        assert result is not None
        assert result["winner"] == "Austin FC"

    def test_no_bold_no_winner(self):
        """Neither team bolded means winner should be None."""
        box = make_box("FC Dallas", "Austin FC", "2 - 1")
        result = parse_wiki_box(box)
        assert result is not None
        assert result["winner"] is None

    def test_both_bold_no_winner(self):
        """Both teams bolded is ambiguous; winner should be None."""
        box = make_box("'''FC Dallas'''", "'''Austin FC'''", "2 - 2")
        result = parse_wiki_box(box)
        assert result is not None
        assert result["winner"] is None


class TestPenaltyWithBoldWinner:
    def test_penalty_with_bold_winner(self):
        """Score with (pen.) and team1 bolded: note is PEN and winner is home."""
        box = make_box(
            "'''FC Dallas'''",
            "Austin FC",
            "1 - 1 (pen. 4 - 2)",
        )
        result = parse_wiki_box(box)
        assert result is not None
        assert result["note"] == "PEN"
        assert result["winner"] == "FC Dallas"


class TestItalicDoesNotTriggerWinner:
    def test_italic_only_no_winner(self):
        """Team wrapped in '' (italic, two quotes) should NOT set winner.

        Two single quotes is italic in wikitext, not bold. The bold
        marker is three single quotes ('''). This test verifies that
        italic markup is not mistakenly detected as bold.
        """
        box = make_box("''FC Dallas''", "Austin FC", "2 - 1")
        result = parse_wiki_box(box)
        assert result is not None
        assert result["winner"] is None


class TestNoScorePathHasWinnerKey:
    def test_no_score_path_has_winner_key(self):
        """When score has no digit match, return dict should still have winner: None."""
        box = make_box("FC Dallas", "Austin FC", "TBD")
        result = parse_wiki_box(box)
        assert result is not None
        assert "winner" in result
        assert result["winner"] is None
