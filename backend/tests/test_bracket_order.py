"""Tests for build_bracket ordering: whatever order the source lists matches
in, each round must line up with the next so the connector lines join the
matches that actually fed each other.
"""

import random
import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import seasons
from backend.scraper import build_bracket

SEASON_2026 = seasons.get(2026)
SEASON_2027 = seasons.get(2027)


def teams(match):
    return {match["home"], match["away"]}


def assert_bracket_topology(rounds, entry_round=2):
    """The round before the entry round feeds it 1:1 (2026: R2[i] feeds
    R32[i]; 2027: R1[i] feeds R64[i]); every other round feeds the next 2:1,
    so round[2i] and round[2i+1] feed next[i]."""
    for idx in range(len(rounds) - 1):
        current = rounds[idx]["matches"]
        nxt = rounds[idx + 1]["matches"]
        for i, m in enumerate(nxt):
            if idx == entry_round - 1:
                feeders = [current[i]]
            else:
                feeders = [current[2 * i], current[2 * i + 1]]
            for f in feeders:
                assert f["winner"] in teams(m), (rounds[idx]["name"], f, rounds[idx + 1]["name"], m)


def make_match(home, away, winner):
    return {"home": home, "away": away, "homeScore": 1 if winner == home else 0,
            "awayScore": 1 if winner == away else 0, "winner": winner}


def build_true_bracket():
    """A full 2026-shaped bracket (32/16/16/8/4/2/1) in bracket order."""
    r1 = [make_match(f"T{2 * i}", f"T{2 * i + 1}", f"T{2 * i}") for i in range(32)]
    r2 = [make_match(r1[2 * i]["winner"], r1[2 * i + 1]["winner"], r1[2 * i + 1]["winner"]) for i in range(16)]
    r32 = [make_match(f"MLS{i}", r2[i]["winner"], f"MLS{i}" if i % 3 else r2[i]["winner"]) for i in range(16)]
    rounds = [r1, r2, r32]
    while len(rounds[-1]) > 1:
        prev = rounds[-1]
        rounds.append([make_match(prev[2 * i]["winner"], prev[2 * i + 1]["winner"], prev[2 * i]["winner"])
                       for i in range(len(prev) // 2)])
    return rounds


def shuffled_flat(true_rounds, seed=2026, tag_rounds=False):
    rng = random.Random(seed)
    flat = []
    for idx, r in enumerate(true_rounds):
        shuffled = [dict(m, round=idx) if tag_rounds else dict(m) for m in r]
        rng.shuffle(shuffled)
        flat.extend(shuffled)
    return flat


def build_true_bracket_2027():
    """A full 2027-shaped bracket (32/32/16/8/4/2/1) in bracket order: each
    First Round winner meets one Round of 64 entrant."""
    r1 = [make_match(f"P{i}", f"A{i}", f"P{i}" if i % 4 else f"A{i}") for i in range(32)]
    r64 = [make_match(f"MLS{i}", r1[i]["winner"], f"MLS{i}" if i % 5 else r1[i]["winner"]) for i in range(32)]
    rounds = [r1, r64]
    while len(rounds[-1]) > 1:
        prev = rounds[-1]
        rounds.append([make_match(prev[2 * i]["winner"], prev[2 * i + 1]["winner"], prev[2 * i + 1]["winner"])
                       for i in range(len(prev) // 2)])
    return rounds


def test_shuffled_rounds_are_put_in_bracket_order():
    rounds = build_bracket(shuffled_flat(build_true_bracket()), SEASON_2026)["rounds"]

    assert [len(r["matches"]) for r in rounds] == [32, 16, 16, 8, 4, 2, 1]
    assert_bracket_topology(rounds)


def test_2027_shuffled_rounds_are_put_in_bracket_order():
    """2027 has a Round of 64 fed 1:1 by the First Round, and no Second Round."""
    data = build_bracket(shuffled_flat(build_true_bracket_2027(), tag_rounds=True), SEASON_2027)
    rounds = data["rounds"]

    assert data["season"] == 2027
    assert [r["name"] for r in rounds][:3] == ["First Round", "Round of 64", "Round of 32"]
    assert [len(r["matches"]) for r in rounds] == [32, 32, 16, 8, 4, 2, 1]
    assert_bracket_topology(rounds, entry_round=1)


def test_2027_empty_bracket_has_every_round():
    """Before the pairings are out the page still needs the round names and dates."""
    data = build_bracket([], SEASON_2027)
    assert [r["name"] for r in data["rounds"]] == [
        "First Round", "Round of 64", "Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Final"]
    assert all(r["matches"] == [] for r in data["rounds"])
    assert data["rounds"][-1]["schedule"] == "Dec 15"


def test_tagged_matches_stay_in_their_round_when_one_is_missing():
    """Slicing by position let one missing First Round match push a
    semifinal into the Final slot; round tags keep every match in place."""
    true_rounds = build_true_bracket()
    flat = shuffled_flat(true_rounds, tag_rounds=True)
    flat = [m for m in flat if not (m["round"] == 0 and m["home"] == "T0")]

    rounds = build_bracket(flat, SEASON_2026)["rounds"]

    assert [len(r["matches"]) for r in rounds] == [31, 16, 16, 8, 4, 2, 1]
    assert rounds[6]["matches"][0]["home"] == true_rounds[6][0]["home"]
    assert rounds[6]["matches"][0]["away"] == true_rounds[6][0]["away"]
