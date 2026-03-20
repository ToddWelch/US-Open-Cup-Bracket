import json
import os
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRACKET_FILE = os.path.join(DATA_DIR, "bracket.json")
SCHEDULE_URL = "https://www.ussoccer.com/us-open-cup/schedule"

ROUND_META = [
    {"name": "First Round", "schedule": "Mar 17-19"},
    {"name": "Second Round", "schedule": "Mar 31 / Apr 1"},
    {"name": "Round of 32", "schedule": "Apr 14-15"},
    {"name": "Round of 16", "schedule": "Apr 28-29"},
    {"name": "Quarterfinals", "schedule": "May 19-20"},
    {"name": "Semifinals", "schedule": "Sep 15-16"},
    {"name": "Final", "schedule": "Oct 21"},
]


def load_existing():
    if not os.path.exists(BRACKET_FILE):
        return None
    try:
        with open(BRACKET_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_bracket(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BRACKET_FILE, "w") as f:
        json.dump(data, f, indent=2)


def count_matches(data):
    total = 0
    if data and "rounds" in data:
        for r in data["rounds"]:
            total += len(r.get("matches", []))
    return total


def scrape_bracket():
    existing = load_existing()

    try:
        resp = requests.get(SCHEDULE_URL, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; USOpenCupBracket/1.0)"
        })
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Scrape failed: %s", e)
        if existing:
            existing["scrapeStatus"] = "stale"
            save_bracket(existing)
        return

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        matches = parse_matches(soup)
    except Exception as e:
        logger.warning("Parse failed: %s", e)
        if existing:
            existing["scrapeStatus"] = "error"
            save_bracket(existing)
        return

    if not matches:
        logger.warning("No matches parsed from page")
        if existing:
            existing["scrapeStatus"] = "stale"
            save_bracket(existing)
        return

    # Build rounds from flat match list
    new_data = build_bracket(matches)

    # Never overwrite with less data
    if existing and count_matches(new_data) < count_matches(existing):
        logger.warning(
            "New data has fewer matches (%d vs %d), keeping existing",
            count_matches(new_data), count_matches(existing)
        )
        existing["scrapeStatus"] = "stale"
        save_bracket(existing)
        return

    new_data["scrapeStatus"] = "ok"
    new_data["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    save_bracket(new_data)
    logger.info("Bracket updated with %d matches", count_matches(new_data))


def parse_matches(soup):
    """Parse match rows from the US Soccer schedule page.

    This is a best-effort parser. The page structure may change,
    so we handle failures gracefully.
    """
    matches = []

    # Look for table rows or match containers
    # The exact selectors may need adjustment based on the live page
    rows = soup.select("table tbody tr")
    if not rows:
        rows = soup.select(".schedule-list .match, .match-row, [data-match]")

    for row in rows:
        try:
            cells = row.find_all("td") if row.name == "tr" else None
            if cells and len(cells) >= 3:
                match = parse_table_row(cells)
                if match:
                    matches.append(match)
        except Exception as e:
            logger.debug("Skipping row: %s", e)
            continue

    return matches


def parse_table_row(cells):
    """Parse a table row into a match dict."""
    text = [c.get_text(strip=True) for c in cells]

    # Try to find "Team A X - Y Team B" pattern
    for t in text:
        parts = t.split(" - ")
        if len(parts) == 2:
            # Attempt to split "Team Name Score" from each side
            left = parts[0].rsplit(" ", 1)
            right = parts[1].split(" ", 1)
            if len(left) == 2 and len(right) == 2:
                try:
                    home_score = int(left[1])
                    away_score = int(right[0])
                    return {
                        "home": left[0].strip(),
                        "away": right[1].strip(),
                        "homeScore": home_score,
                        "awayScore": away_score,
                        "date": None,
                        "note": None,
                    }
                except ValueError:
                    continue

    return None


def build_bracket(matches):
    """Organize flat matches into round structure."""
    # For now, put all matches into rounds based on count
    # R1 = first 32, R2 = next 16, etc.
    rounds = []
    idx = 0
    round_sizes = [32, 16, 16, 8, 4, 2, 1]

    for i, size in enumerate(round_sizes):
        round_matches = matches[idx:idx + size] if idx < len(matches) else []
        rounds.append({
            "name": ROUND_META[i]["name"],
            "schedule": ROUND_META[i]["schedule"],
            "matches": round_matches,
        })
        idx += size

    return {"rounds": rounds}
