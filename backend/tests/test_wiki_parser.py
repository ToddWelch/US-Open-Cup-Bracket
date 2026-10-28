"""Tests for the Wikipedia wikitext parser (parse_wiki_box, map_wiki_sections).

Covers score-based winner detection (bold markup is ignored), penalty
shootouts from the penaltyscore field and from the score text, the AET
field, exact section-heading matching, and the no-score return path.
"""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.scraper import map_wiki_sections, parse_wiki_box


def make_box(team1, team2, score, date="1 January 2026"):
    """Build a minimal wikitext football box for testing."""
    return f"""
| date = {date}
| team1 = {team1}
| score = {score}
| team2 = {team2}
}}}}"""


EN_DASH = chr(0x2013)

# A 2026 quarterfinal box as it appears on the article (copied 2026-10-28):
# level score, shootout in the penaltyscore field, and the LOSER in bold.
# The article writes scores with en dashes; "@" stands in for them here
# because the repo keeps dash characters out of source.
STL_HOU_QF_2026 = """
|date = May 19
|time = 8:00 PM ET
|team1 = [[St. Louis City SC]] {{Flagicon|Missouri}}
|score = 2@2
|report= https://www.mlssoccer.com/competitions/u-s-open-cup/2026/matches/stlvshou-05-19-2026/
|team2 = {{flagicon|Texas}} '''[[Houston Dynamo FC]]'''
|goals1 =
*[[Marcel Hartel|Hartel]] {{goal|10||51|pen.}}
|goals2 =
*[[Mateusz Bogusz|Bogusz]] {{goal|11}}
*[[Artur (footballer, born 1996)|Artur]] {{goal|42}}
|aet = yes
|penalties1 =
*[[Eduard Löwen|Löwen]] {{pengoal}}
|penaltyscore = 4@2
|penalties2 =
*{{penmiss}} [[Guilherme (footballer, born 1995)|Guilherme]]
|stadium = [[Energizer Park]]
}}""".replace("@", EN_DASH)


class TestScoreDecidesWinner:
    def test_home_win(self):
        result = parse_wiki_box(make_box("FC Dallas", "Austin FC", "2 - 1"))
        assert result["winner"] == "FC Dallas"

    def test_away_win(self):
        result = parse_wiki_box(make_box("FC Dallas", "Austin FC", "1 - 2"))
        assert result["winner"] == "Austin FC"

    def test_bold_loser_is_ignored(self):
        """The 2026 article bolds the losing team; the score still decides."""
        box = make_box("[[Orlando City SC]]", "'''[[Atlanta United FC]]'''", f"4{EN_DASH}1")
        result = parse_wiki_box(box)
        assert result["home"] == "Orlando City SC"
        assert result["away"] == "Atlanta United FC"
        assert result["winner"] == "Orlando City SC"

    def test_level_score_without_shootout_has_no_winner(self):
        """A draw with no shootout score is undecided, even with one team bolded."""
        result = parse_wiki_box(make_box("'''FC Dallas'''", "Austin FC", "2 - 2"))
        assert result["winner"] is None


class TestPenaltyShootout:
    def test_penaltyscore_field_decides_level_match(self):
        result = parse_wiki_box(STL_HOU_QF_2026)
        assert result["homeScore"] == 2
        assert result["awayScore"] == 2
        assert result["note"] == "PEN"
        assert result["winner"] == "St. Louis City SC"

    def test_inline_shootout_in_score_text(self):
        box = make_box("FC Dallas", "'''Austin FC'''", "1 - 1 (pen. 4 - 2)")
        result = parse_wiki_box(box)
        assert result["note"] == "PEN"
        assert result["winner"] == "FC Dallas"

    def test_inline_shootout_away_win(self):
        result = parse_wiki_box(make_box("FC Dallas", "Austin FC", "0 - 0 (pen. 3 - 5)"))
        assert result["winner"] == "Austin FC"


class TestExtraTime:
    def test_aet_field_sets_note(self):
        box = make_box("FC Dallas", "Austin FC", "2 - 1") + "\n|aet = yes"
        result = parse_wiki_box(box)
        assert result["note"] == "AET"
        assert result["winner"] == "FC Dallas"


class TestEmptyFieldDoesNotReadNextLine:
    def test_empty_penaltyscore_is_ignored(self):
        """An empty |penaltyscore = must not capture the following line."""
        box = make_box("FC Dallas", "Austin FC", "1 - 1") + "\n|penaltyscore = \n|attendance = 3-2"
        result = parse_wiki_box(box)
        assert result["note"] is None
        assert result["winner"] is None


class TestNoScorePathHasWinnerKey:
    def test_no_score_path_has_winner_key(self):
        """When score has no digit match, return dict should still have winner: None."""
        box = make_box("FC Dallas", "Austin FC", "TBD")
        result = parse_wiki_box(box)
        assert result is not None
        assert "winner" in result
        assert result["winner"] is None


class TestSectionMapping:
    # Section headings of the 2026 article (fetched 2026-10-28)
    SECTIONS_2026 = [
        ("1", "Schedule"), ("7", "Early rounds"), ("8", "First round"),
        ("9", "Second round"), ("10", "Round of 32 and 16"), ("11", "Bracket"),
        ("12", "Round of 32"), ("13", "Teams"), ("14", "Round of 16"),
        ("15", "Quarterfinals and beyond"), ("16", "Quarterfinals"),
        ("17", "Semifinals"), ("18", "Final"), ("20", "Top goalscorers"),
    ]

    def test_exact_headings_map_to_rounds(self):
        sections = [{"index": i, "line": line} for i, line in self.SECTIONS_2026]
        assert map_wiki_sections(sections) == {
            0: "8", 1: "9", 2: "12", 3: "14", 4: "16", 5: "17", 6: "18",
        }

    def test_semifinals_heading_is_not_the_final(self):
        """Before the Final section existed, substring matching mapped the
        Final to the Semifinals section and showed a semifinal as the Final."""
        sections = [{"index": "17", "line": "Semifinals"}]
        assert map_wiki_sections(sections) == {5: "17"}
