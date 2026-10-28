"""Live checks against ESPN and Wikipedia (network required, read-only).

The 2026 tournament is complete, so its results are fixed: St. Louis CITY SC
beat Columbus Crew on penalties (0-0, 5-3) in the Final on October 21, 2026,
confirmed by ESPN, Wikipedia and ussoccer.com on 2026-10-28.
"""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import scraper
from backend.tests.test_bracket_order import assert_bracket_topology

ROUND_SIZES = [32, 16, 16, 8, 4, 2, 1]


def test_espn_season_builds_full_bracket_with_final():
    matches = scraper.fetch_espn()
    assert len(matches) == sum(ROUND_SIZES)

    rounds = scraper.build_bracket(matches)["rounds"]
    assert [len(r["matches"]) for r in rounds] == ROUND_SIZES

    final = rounds[6]["matches"][0]
    assert {final["home"], final["away"]} == {"Columbus Crew", "St. Louis CITY SC"}
    assert final["winner"] == "St. Louis CITY SC"
    assert final["note"] == "PEN"
    assert final["date"] == "October 21"

    # Every match has a winner, and each one sits where it feeds the next round
    assert_bracket_topology(rounds)


def test_wikipedia_winners_follow_the_score():
    matches = scraper.fetch_wikipedia()
    assert len(matches) >= 78  # the Final is transcluded from another page

    for m in matches:
        if m["homeScore"] is not None and m["homeScore"] != m["awayScore"]:
            expected = m["home"] if m["homeScore"] > m["awayScore"] else m["away"]
            assert m["winner"] == expected, m

    qf = next(m for m in matches if {m["home"], m["away"]} == {"St. Louis City SC", "Houston Dynamo FC"})
    assert qf["note"] == "PEN"
    assert qf["winner"] == "St. Louis City SC"
