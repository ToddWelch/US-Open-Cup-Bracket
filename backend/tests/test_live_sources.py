"""Live checks against ESPN and Wikipedia (network required, read-only).

The 2026 tournament is complete, so its results are fixed: St. Louis CITY SC
beat Columbus Crew on penalties (0-0, 5-3) in the Final on October 21, 2026,
confirmed by ESPN, Wikipedia and ussoccer.com on 2026-10-28. These checks run
against the 2026 season config, so they keep working after the rollover.

Skipped unless LIVE_SOURCES=1, so an offline or rate-limited run (Wikipedia
returns HTTP 429 after repeated calls) does not fail the suite. Run them as
the acceptance check before any deploy that touches the scrapers:
    LIVE_SOURCES=1 python -m pytest backend/tests/test_live_sources.py
"""

import sys
import os

import pytest

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import scraper, seasons
from backend.tests.test_bracket_order import assert_bracket_topology

pytestmark = pytest.mark.skipif(os.environ.get("LIVE_SOURCES") != "1", reason="live network check; set LIVE_SOURCES=1")

ROUND_SIZES = [32, 16, 16, 8, 4, 2, 1]
SEASON_2026 = seasons.get(2026)


def test_espn_season_builds_full_bracket_with_final():
    matches = scraper.fetch_espn(SEASON_2026)
    assert len(matches) == sum(ROUND_SIZES)

    rounds = scraper.build_bracket(matches, SEASON_2026)["rounds"]
    assert [len(r["matches"]) for r in rounds] == ROUND_SIZES

    final = rounds[6]["matches"][0]
    assert {final["home"], final["away"]} == {"Columbus Crew", "St. Louis CITY SC"}
    assert final["winner"] == "St. Louis CITY SC"
    assert final["note"] == "PEN"
    assert final["date"] == "October 21"

    # Every match has a winner, and each one sits where it feeds the next round
    assert_bracket_topology(rounds)


def test_espn_2027_request_is_answered():
    """The 2027 season request must succeed before the tournament starts
    (no events yet is fine); an HTTP error here means alerts every scrape."""
    matches = scraper.fetch_espn(seasons.get(2027))
    assert isinstance(matches, list)


def test_wikipedia_winners_follow_the_score():
    matches = scraper.fetch_wikipedia(SEASON_2026)
    assert len(matches) >= 78  # the Final is transcluded from another page

    for m in matches:
        if m["homeScore"] is not None and m["homeScore"] != m["awayScore"]:
            expected = m["home"] if m["homeScore"] > m["awayScore"] else m["away"]
            assert m["winner"] == expected, m

    qf = next(m for m in matches if {m["home"], m["away"]} == {"St. Louis City SC", "Houston Dynamo FC"})
    assert qf["note"] == "PEN"
    assert qf["winner"] == "St. Louis City SC"
