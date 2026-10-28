"""Tests for build_bracket ordering: whatever order the source lists matches
in, each round must line up with the next so the connector lines join the
matches that actually fed each other.
"""

import random
import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.scraper import build_bracket


def teams(match):
    return {match["home"], match["away"]}


def assert_bracket_topology(rounds):
    """R2[i] feeds R32[i] (1:1, the MLS entry round); every other round
    feeds the next 2:1, so round[2i] and round[2i+1] feed next[i]."""
    for idx in range(len(rounds) - 1):
        current = rounds[idx]["matches"]
        nxt = rounds[idx + 1]["matches"]
        for i, m in enumerate(nxt):
            if idx == 1:
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


def test_shuffled_rounds_are_put_in_bracket_order():
    true_rounds = build_true_bracket()
    rng = random.Random(2026)
    flat = []
    for r in true_rounds:
        shuffled = r[:]
        rng.shuffle(shuffled)
        flat.extend(shuffled)

    rounds = build_bracket(flat)["rounds"]

    assert [len(r["matches"]) for r in rounds] == [32, 16, 16, 8, 4, 2, 1]
    assert_bracket_topology(rounds)
