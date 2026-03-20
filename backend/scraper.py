import json
import os
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRACKET_FILE = os.path.join(DATA_DIR, "bracket.json")

# ESPN public API for US Open Cup
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.open/scoreboard"

# Fallback: US Soccer schedule page
USSOCCER_URL = "https://www.ussoccer.com/us-open-cup/schedule"

# Date ranges per round for ESPN queries
ROUND_META = [
    {"name": "First Round", "schedule": "Mar 17-19", "dates": "20260317-20260325"},
    {"name": "Second Round", "schedule": "Mar 31 / Apr 1", "dates": "20260331-20260402"},
    {"name": "Round of 32", "schedule": "Apr 14-15", "dates": "20260414-20260416"},
    {"name": "Round of 16", "schedule": "Apr 28-29", "dates": "20260428-20260430"},
    {"name": "Quarterfinals", "schedule": "May 19-20", "dates": "20260519-20260521"},
    {"name": "Semifinals", "schedule": "Sep 15-16", "dates": "20260915-20260917"},
    {"name": "Final", "schedule": "Oct 21", "dates": "20261021-20261022"},
]

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


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

    # Try ESPN first, then fall back to ussoccer.com
    matches = fetch_espn()

    if not matches:
        logger.info("ESPN returned no data, trying ussoccer.com fallback")
        matches = fetch_ussoccer()

    if not matches:
        logger.warning("All sources returned no data")
        if existing:
            existing["scrapeStatus"] = "stale"
            save_bracket(existing)
        return

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


# ─── ESPN API (PRIMARY) ───────────────────────────────────────────────

def fetch_espn():
    """Fetch all matches from ESPN's public scoreboard API."""
    all_matches = []

    for round_info in ROUND_META:
        try:
            url = f"{ESPN_BASE}?dates={round_info['dates']}"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            events = data.get("events", [])
            for event in events:
                match = parse_espn_event(event)
                if match:
                    all_matches.append(match)

            if events:
                logger.info("ESPN: %d matches for %s", len(events), round_info["name"])

        except requests.RequestException as e:
            logger.warning("ESPN fetch failed for %s: %s", round_info["name"], e)
            continue
        except (KeyError, ValueError) as e:
            logger.warning("ESPN parse error for %s: %s", round_info["name"], e)
            continue

    if all_matches:
        logger.info("ESPN: %d total matches fetched", len(all_matches))

    return all_matches


def parse_espn_event(event):
    """Parse a single ESPN event into our match format."""
    try:
        competition = event["competitions"][0]
        competitors = competition["competitors"]

        # ESPN lists competitors; find home/away
        home = away = None
        for team in competitors:
            entry = {
                "name": team["team"]["displayName"],
                "score": int(team.get("score", 0)) if team.get("score") is not None else None,
            }
            if team.get("homeAway") == "home":
                home = entry
            else:
                away = entry

        if not home or not away:
            return None

        status = competition.get("status", {})
        is_complete = status.get("type", {}).get("completed", False)
        state = status.get("type", {}).get("name", "")

        # Parse date
        date_str = event.get("date", "")
        date_display = None
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_display = dt.strftime("%B %d")
            except ValueError:
                pass

        # Determine note (AET, penalties, etc.)
        note = None
        detail = status.get("type", {}).get("detail", "")
        if "After Extra Time" in detail:
            note = "AET"
        elif "Penalties" in detail:
            note = "PEN"
        elif not is_complete and state != "STATUS_FINAL":
            # Future match - show date as note
            if date_display:
                note = dt.strftime("%b %d")

        return {
            "home": home["name"],
            "away": away["name"],
            "homeScore": home["score"] if is_complete else None,
            "awayScore": away["score"] if is_complete else None,
            "date": date_display,
            "note": note,
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.debug("Skipping ESPN event: %s", e)
        return None


# ─── US SOCCER FALLBACK ───────────────────────────────────────────────

def fetch_ussoccer():
    """Scrape ussoccer.com schedule page as fallback."""
    try:
        resp = requests.get(USSOCCER_URL, timeout=15, headers=BROWSER_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("ussoccer.com fetch failed: %s", e)
        return []

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        return parse_ussoccer(soup)
    except Exception as e:
        logger.warning("ussoccer.com parse failed: %s", e)
        return []


def parse_ussoccer(soup):
    """Parse match data from ussoccer.com schedule page."""
    matches = []

    rows = soup.select("table tbody tr")
    if not rows:
        rows = soup.select(".schedule-list .match, .match-row, [data-match]")

    for row in rows:
        try:
            cells = row.find_all("td") if row.name == "tr" else None
            if cells and len(cells) >= 3:
                match = parse_ussoccer_row(cells)
                if match:
                    matches.append(match)
        except Exception as e:
            logger.debug("Skipping ussoccer row: %s", e)
            continue

    if matches:
        logger.info("ussoccer.com: %d matches parsed", len(matches))

    return matches


def parse_ussoccer_row(cells):
    """Parse a table row from ussoccer.com into a match dict."""
    text = [c.get_text(strip=True) for c in cells]

    for t in text:
        parts = t.split(" - ")
        if len(parts) == 2:
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


# ─── BRACKET BUILDER ──────────────────────────────────────────────────

def build_bracket(matches):
    """Organize flat matches into round structure."""
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
