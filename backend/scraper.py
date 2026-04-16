import json
import os
import re
import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRACKET_FILE = os.path.join(DATA_DIR, "bracket.json")

# ESPN public API for US Open Cup
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.open/scoreboard"

# Wikipedia API for structured match data
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_PAGE = "2026_U.S._Open_Cup"

# Fallback: US Soccer schedule page
USSOCCER_URL = "https://www.ussoccer.com/us-open-cup/schedule"

# Slack webhook for alerts (set via environment variable)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Round metadata with ESPN date ranges
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


def send_slack_alert(message):
    """Send an alert to Slack via incoming webhook."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping alert")
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
        logger.info("Slack alert sent")
    except Exception as e:
        logger.error("Slack alert failed: %s", e)


def scrape_espn_fast():
    """ESPN-only fast poll for live game updates. Skips Wikipedia/ussoccer."""
    existing = load_existing()
    now = datetime.now(timezone.utc)

    try:
        matches = fetch_espn()
    except Exception as e:
        logger.warning("ESPN fast poll failed: %s", e)
        return

    if not matches:
        logger.info("ESPN fast poll: no data")
        return

    new_data = build_bracket(matches)

    # Never overwrite with less data
    if existing and count_matches(new_data) < count_matches(existing):
        logger.info("ESPN fast poll: fewer matches, skipping")
        return

    new_data["lastScrape"] = now.isoformat()
    new_data["scrapeSource"] = "ESPN (live)"
    new_data["scrapeStatus"] = "ok"
    new_data["lastUpdated"] = now.isoformat()
    # Preserve source results from last full scrape
    if existing and "sourceResults" in existing:
        new_data["sourceResults"] = existing["sourceResults"]
    save_bracket(new_data)
    logger.info("ESPN fast poll: updated %d matches", count_matches(new_data))


def scrape_bracket():
    existing = load_existing()
    now = datetime.now(timezone.utc)

    # Try all sources and track results
    sources = [
        ("ESPN", fetch_espn),
        ("Wikipedia", fetch_wikipedia),
        ("ussoccer.com", fetch_ussoccer),
    ]

    source_results = []
    matches = []
    source_used = None

    for name, fetcher in sources:
        try:
            result = fetcher()
            if result:
                source_results.append({"name": name, "status": "ok", "matches": len(result)})
                if not matches:
                    matches = result
                    source_used = name
            else:
                source_results.append({"name": name, "status": "no_data", "matches": 0})
        except Exception as e:
            source_results.append({"name": name, "status": "error", "error": str(e), "matches": 0})
            logger.warning("%s failed: %s", name, e)

    # Count failures (error or no_data)
    failures = sum(1 for s in source_results if s["status"] != "ok")

    # Alert if 2+ sources failed
    if failures >= 2:
        failed_names = [s["name"] for s in source_results if s["status"] != "ok"]
        ok_names = [s["name"] for s in source_results if s["status"] == "ok"]
        msg = (
            f":warning: *US Open Cup Bracket - Data Source Alert*\n"
            f"{failures}/3 sources failed at {now.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Failed: {', '.join(failed_names)}\n"
            f"Working: {', '.join(ok_names) if ok_names else 'NONE'}\n"
        )
        if not ok_names:
            msg += ":red_circle: *All sources down - bracket data is stale*"
        send_slack_alert(msg)

    # Build scrape status metadata
    scrape_info = {
        "lastScrape": now.isoformat(),
        "scrapeSource": source_used,
        "scrapeStatus": "ok" if matches else "stale",
        "sourceResults": source_results,
    }

    if not matches:
        logger.warning("All sources returned no data")
        if existing:
            existing.update(scrape_info)
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
        if existing:
            existing.update(scrape_info)
            existing["scrapeStatus"] = "stale"
            save_bracket(existing)
        return

    new_data.update(scrape_info)
    new_data["scrapeStatus"] = "ok"
    new_data["lastUpdated"] = now.isoformat()
    save_bracket(new_data)
    logger.info("Bracket updated with %d matches from %s", count_matches(new_data), source_used)


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

    return all_matches


def parse_espn_event(event):
    """Parse a single ESPN event into our match format."""
    try:
        competition = event["competitions"][0]
        competitors = competition["competitors"]

        home = away = None
        explicit_winner = None
        for team in competitors:
            entry = {
                "name": team["team"]["displayName"],
                "score": int(team.get("score", 0)) if team.get("score") is not None else None,
            }
            if team.get("winner", False):
                explicit_winner = entry["name"]
            if team.get("homeAway") == "home":
                home = entry
            else:
                away = entry

        if not home or not away:
            return None

        status = competition.get("status", {})
        is_complete = status.get("type", {}).get("completed", False)
        state = status.get("type", {}).get("name", "")
        # ESPN uses specific states for soccer (STATUS_FIRST_HALF, STATUS_SECOND_HALF,
        # STATUS_HALFTIME, STATUS_EXTRA_TIME, STATUS_PENALTY_SHOOTOUT, etc.)
        # rather than a generic STATUS_IN_PROGRESS. Treat anything not in the
        # known non-live set as live so new states are handled automatically.
        NOT_LIVE_STATES = {
            "STATUS_SCHEDULED", "STATUS_POSTPONED", "STATUS_CANCELED",
            "STATUS_FINAL", "STATUS_FULL_TIME", "STATUS_ABANDONED",
            "STATUS_FINAL_PEN", "STATUS_FINAL_AET", "",
        }
        is_live = not is_complete and state not in NOT_LIVE_STATES

        date_str = event.get("date", "")
        date_display = None
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_display = dt.strftime("%B %d")
            except ValueError:
                pass

        note = None
        clock = None
        detail = status.get("type", {}).get("detail", "")
        if state == "STATUS_FINAL_PEN" or "Penalties" in detail:
            note = "PEN"
        elif state == "STATUS_FINAL_AET" or "After Extra Time" in detail:
            note = "AET"
        elif not is_complete and not is_live and state != "STATUS_FINAL":
            if date_display:
                note = dt.strftime("%b %d")

        # Extract clock/minute for live games
        if is_live:
            clock_val = status.get("displayClock", "")
            period = status.get("period", 0)
            if clock_val:
                clock = clock_val
            elif detail:
                clock = detail

        # Determine match status
        match_status = None
        if is_complete or state == "STATUS_FINAL":
            match_status = "ft"
        elif is_live:
            match_status = "live"

        # Include full ISO datetime for upcoming games
        game_time = None
        if date_str and not is_complete and not is_live:
            game_time = date_str

        return {
            "home": home["name"],
            "away": away["name"],
            "homeScore": home["score"] if (is_complete or is_live) else None,
            "awayScore": away["score"] if (is_complete or is_live) else None,
            "date": date_display,
            "note": note,
            "status": match_status,
            "clock": clock,
            "gameTime": game_time,
            "winner": explicit_winner if is_complete else None,
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.debug("Skipping ESPN event: %s", e)
        return None


# ─── WIKIPEDIA API (BACKUP 2) ─────────────────────────────────────────

def fetch_wikipedia():
    """Fetch match data from Wikipedia's structured wikitext."""
    all_matches = []

    # First, get current section list to find round sections
    try:
        resp = requests.get(WIKI_API, timeout=15, params={
            "action": "parse",
            "page": WIKI_PAGE,
            "prop": "sections",
            "format": "json",
        }, headers={"User-Agent": "USOpenCupBracket/1.0 (usopencup.welchproductsllc.com)"})
        resp.raise_for_status()
        sections = resp.json().get("parse", {}).get("sections", [])
    except Exception as e:
        logger.warning("Wikipedia sections fetch failed: %s", e)
        return []

    # Map round names to section indices
    round_keywords = {
        "First round": 0,
        "Second round": 1,
        "Round of 32": 2,
        "Round of 16": 3,
        "Quarterfinals": 4,
        "Quarter-finals": 4,
        "Semifinals": 5,
        "Semi-finals": 5,
        "Final": 6,
    }

    section_map = {}
    for s in sections:
        for keyword, round_idx in round_keywords.items():
            if keyword.lower() in s.get("line", "").lower():
                section_map[round_idx] = s["index"]

    if not section_map:
        logger.warning("Wikipedia: no round sections found")
        return []

    # Fetch each round section
    for round_idx, section_idx in sorted(section_map.items()):
        try:
            resp = requests.get(WIKI_API, timeout=15, params={
                "action": "parse",
                "page": WIKI_PAGE,
                "prop": "wikitext",
                "section": section_idx,
                "format": "json",
            }, headers={"User-Agent": "USOpenCupBracket/1.0 (usopencup.welchproductsllc.com)"})
            resp.raise_for_status()

            wikitext = resp.json().get("parse", {}).get("wikitext", {}).get("*", "")
            matches = parse_wiki_matches(wikitext)

            if matches:
                logger.info("Wikipedia: %d matches for %s", len(matches), ROUND_META[round_idx]["name"])
                all_matches.extend(matches)

        except Exception as e:
            logger.warning("Wikipedia fetch failed for section %s: %s", section_idx, e)
            continue

    return all_matches


def parse_wiki_matches(wikitext):
    """Parse football box collapsible templates from wikitext."""
    matches = []

    boxes = re.split(r'\{\{football box collapsible', wikitext)

    for box in boxes[1:]:
        try:
            match = parse_wiki_box(box)
            if match:
                matches.append(match)
        except Exception as e:
            logger.debug("Skipping wiki box: %s", e)
            continue

    return matches


def parse_wiki_box(box):
    """Parse a single football box collapsible template."""
    def extract(field):
        pattern = rf'\|\s*{field}\s*=\s*(.+)'
        m = re.search(pattern, box)
        return m.group(1).strip() if m else None

    score_raw = extract("score")
    if not score_raw:
        return None

    team1_raw = extract("team1")
    team2_raw = extract("team2")
    date_raw = extract("date")

    if not team1_raw or not team2_raw:
        return None

    def clean_team(raw):
        raw = raw.replace("'''", "")
        raw = re.sub(r'\{\{[^}]+\}\}', '', raw)
        links = re.findall(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', raw)
        if links:
            name = max(links, key=len)
        else:
            name = raw
        name = re.sub(r'\([A-Za-z0-9/]+\)', '', name)
        return name.strip()

    home = clean_team(team1_raw)
    away = clean_team(team2_raw)

    score_clean = score_raw.replace('\u2013', '-').replace('\u2014', '-')
    note = None

    if "vo" in score_clean.lower() or "w/o" in score_clean.lower() or "ff" in score_clean.lower():
        note = "FF"
    if "a.e.t" in score_clean.lower() or "aet" in score_clean.lower():
        note = "AET"
    if "pen" in score_clean.lower():
        note = "PEN"

    score_match = re.search(r'(\d+)\s*-\s*(\d+)', score_clean)
    if not score_match:
        return {
            "home": home,
            "away": away,
            "homeScore": None,
            "awayScore": None,
            "date": date_raw,
            "note": date_raw,
        }

    home_score = int(score_match.group(1))
    away_score = int(score_match.group(2))

    return {
        "home": home,
        "away": away,
        "homeScore": home_score,
        "awayScore": away_score,
        "date": date_raw,
        "note": note,
    }


# ─── US SOCCER FALLBACK (BACKUP 3) ────────────────────────────────────

def fetch_ussoccer():
    """Scrape ussoccer.com schedule page as last resort."""
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

def _reorder_feeder_round(feeder_matches, next_round_matches):
    """Reorder feeder_matches so that positional pairing is correct.

    The frontend pairs feeders by position: feeder[2i] + feeder[2i+1] -> next[i].
    This function reorders feeder_matches so that each pair of feeders at
    positions [2i, 2i+1] contains the two matches whose winners appear in
    next_round_matches[i].

    Returns a new list (same length as feeder_matches) with corrected ordering,
    or the original list unchanged if reordering cannot be determined.
    """
    if not feeder_matches or not next_round_matches:
        return feeder_matches

    # Build lookup: team name -> feeder match index
    # A team can be either home or away in the feeder round
    team_to_feeder = {}
    for idx, match in enumerate(feeder_matches):
        home = match.get("home", "")
        away = match.get("away", "")
        if home and home != "TBD":
            team_to_feeder[home] = idx
        if away and away != "TBD":
            team_to_feeder[away] = idx

    # For each next-round match, find its two feeder matches
    # feeder_assignments[i] = [feeder_idx_a, feeder_idx_b] for next_round[i]
    feeder_assignments = [[] for _ in range(len(next_round_matches))]
    used_feeders = set()

    for nr_idx, nr_match in enumerate(next_round_matches):
        home = nr_match.get("home", "")
        away = nr_match.get("away", "")

        if home and home != "TBD" and home in team_to_feeder:
            f_idx = team_to_feeder[home]
            if f_idx not in used_feeders:
                feeder_assignments[nr_idx].append(f_idx)
                used_feeders.add(f_idx)

        if away and away != "TBD" and away in team_to_feeder:
            f_idx = team_to_feeder[away]
            if f_idx not in used_feeders:
                feeder_assignments[nr_idx].append(f_idx)
                used_feeders.add(f_idx)

    # Handle TBD: find unassigned feeders and assign them to next-round
    # matches that still need a feeder (have fewer than 2 assigned)
    unassigned = [i for i in range(len(feeder_matches)) if i not in used_feeders]
    for nr_idx in range(len(next_round_matches)):
        while len(feeder_assignments[nr_idx]) < 2 and unassigned:
            f_idx = unassigned.pop(0)
            feeder_assignments[nr_idx].append(f_idx)
            used_feeders.add(f_idx)

    # Validate: every next-round match should have exactly 2 feeders
    # and total assigned feeders should equal len(feeder_matches)
    total_assigned = sum(len(fa) for fa in feeder_assignments)
    if total_assigned != len(feeder_matches):
        logger.warning(
            "Feeder reordering: expected %d assignments but got %d, keeping original order",
            len(feeder_matches), total_assigned
        )
        return feeder_matches

    for nr_idx, fa in enumerate(feeder_assignments):
        if len(fa) != 2:
            logger.warning(
                "Feeder reordering: next-round match %d has %d feeders (expected 2), keeping original order",
                nr_idx, len(fa)
            )
            return feeder_matches

    # Build reordered array: for next_round[i], place feeders at [2i] and [2i+1]
    reordered = [None] * len(feeder_matches)
    for nr_idx, fa in enumerate(feeder_assignments):
        reordered[2 * nr_idx] = feeder_matches[fa[0]]
        reordered[2 * nr_idx + 1] = feeder_matches[fa[1]]

    # Final safety check: no None entries
    if any(m is None for m in reordered):
        logger.warning("Feeder reordering: produced None entries, keeping original order")
        return feeder_matches

    logger.info("Feeder round reordered successfully (%d matches)", len(reordered))
    return reordered


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

    # Reorder feeder rounds so positional pairing matches bracket topology.
    # Round transitions where reordering applies:
    #   R1 (idx 0) -> R2 (idx 1): feeder has 32 matches, next has 16
    #   R2 (idx 1) -> R32 (idx 2): SKIP, R32 is the MLS entry round (1:1 mapping)
    #   R32 (idx 2) -> R16 (idx 3): feeder has 16 matches, next has 8
    #   R16 (idx 3) -> QF (idx 4): feeder has 8, next has 4
    #   QF (idx 4) -> SF (idx 5): feeder has 4, next has 2
    reorder_pairs = [(0, 1), (2, 3), (3, 4), (4, 5)]

    for feeder_idx, next_idx in reorder_pairs:
        feeder_round = rounds[feeder_idx]["matches"]
        next_round = rounds[next_idx]["matches"]

        if not feeder_round or not next_round:
            continue

        # Only reorder if feeder has exactly 2x the matches of next round
        if len(feeder_round) != 2 * len(next_round):
            logger.warning(
                "Skipping reorder for rounds %d->%d: expected %d feeder matches but got %d",
                feeder_idx, next_idx, 2 * len(next_round), len(feeder_round)
            )
            continue

        try:
            rounds[feeder_idx]["matches"] = _reorder_feeder_round(feeder_round, next_round)
        except Exception as e:
            logger.error("Feeder reordering failed for rounds %d->%d: %s", feeder_idx, next_idx, e)
            # Keep original order on any unexpected error

    return {"rounds": rounds}
