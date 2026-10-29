import json
import os
import re
import logging
import tempfile
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRACKET_FILE = os.path.join(DATA_DIR, "bracket.json")

_write_lock = threading.Lock()

# ESPN public API for US Open Cup
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/usa.open/scoreboard"
SEASON_YEAR = "2026"

# Match dates are shown in Eastern Time (an 8pm ET kickoff is the next day in UTC)
EASTERN = ZoneInfo("America/New_York")

# Wikipedia API for structured match data
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_PAGE = "2026_U.S._Open_Cup"

# Fallback: US Soccer schedule page
USSOCCER_URL = "https://www.ussoccer.com/us-open-cup/schedule"

# Slack webhook for alerts (set via environment variable)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Round metadata. "dates" feeds the game-day check; "espnSlug" is the
# season.slug ESPN puts on each event of that round (verified live 2026-10-28).
ROUND_META = [
    {"name": "First Round", "schedule": "Mar 17-19", "dates": "20260317-20260325", "espnSlug": "first-round"},
    {"name": "Second Round", "schedule": "Mar 31 / Apr 1", "dates": "20260331-20260402", "espnSlug": "second-round"},
    {"name": "Round of 32", "schedule": "Apr 14-15", "dates": "20260414-20260416", "espnSlug": "round-of-32"},
    {"name": "Round of 16", "schedule": "Apr 28-29", "dates": "20260428-20260430", "espnSlug": "round-of-16"},
    {"name": "Quarterfinals", "schedule": "May 19-20", "dates": "20260519-20260521", "espnSlug": "quarterfinals"},
    {"name": "Semifinals", "schedule": "Sep 15-16", "dates": "20260915-20260917", "espnSlug": "semifinals"},
    {"name": "Final", "schedule": "Oct 21", "dates": "20261021-20261022", "espnSlug": "final"},
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
    """Write bracket data atomically using a temp file and os.replace.
    A threading lock prevents concurrent writes from the scheduler and
    request handlers clobbering each other."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with _write_lock:
        fd = None
        try:
            fd = tempfile.NamedTemporaryFile(
                dir=DATA_DIR, mode="w", suffix=".tmp", delete=False
            )
            json.dump(data, fd, indent=2)
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()
            os.replace(fd.name, BRACKET_FILE)
        except Exception:
            if fd is not None:
                try:
                    os.unlink(fd.name)
                except OSError:
                    pass
            raise


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
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
        # Status code only; resp.url is the webhook
        if resp.status_code >= 400:
            logger.error("Slack alert rejected: HTTP %d", resp.status_code)
        else:
            logger.info("Slack alert sent")
    except Exception as e:
        # Type only: requests exception text includes the request URL, and
        # the webhook URL is the secret
        logger.error("Slack alert failed: %s", type(e).__name__)


def has_games_today(bracket_data):
    """Check whether any games are scheduled or live today (Eastern Time).

    Accepts pre-loaded bracket data to avoid a redundant file read.
    Returns True if polling should proceed, False to skip.
    """
    from zoneinfo import ZoneInfo

    et = ZoneInfo("America/New_York")
    today = datetime.now(et).strftime("%Y%m%d")

    # No data yet: default to polling so we pick up initial results
    if bracket_data is None:
        return True

    rounds = bracket_data.get("rounds", [])
    any_game_time = False

    for rnd in rounds:
        for m in rnd.get("matches", []):
            # Any live game means we should keep polling (handles past-midnight)
            if m.get("status") == "live":
                return True

            # Check individual match gameTime (ISO string) in Eastern Time
            gt = m.get("gameTime")
            if gt:
                any_game_time = True
                try:
                    dt = datetime.fromisoformat(gt.replace("Z", "+00:00"))
                    if dt.astimezone(et).strftime("%Y%m%d") == today:
                        return True
                except (ValueError, TypeError):
                    pass

    # If ESPN has provided gameTime data, trust it over broad date ranges
    if any_game_time:
        return False

    # Fall back to ROUND_META date ranges (only when no gameTime data exists)
    for meta in ROUND_META:
        date_range = meta.get("dates", "")
        if "-" in date_range:
            parts = date_range.split("-")
            if len(parts) == 2 and parts[0] <= today <= parts[1]:
                return True

    return False


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
    all_results = {}

    for name, fetcher in sources:
        try:
            result = fetcher()
            if result:
                source_results.append({"name": name, "status": "ok", "matches": len(result)})
                all_results[name] = result
            else:
                source_results.append({"name": name, "status": "no_data", "matches": 0})
        except Exception as e:
            # Only the exception type is stored; the file is served publicly
            source_results.append({"name": name, "status": "error", "error": type(e).__name__, "matches": 0})
            logger.warning("%s failed: %s", name, e)

    # Select the source with the most matches. On ties, preserve priority
    # order (ESPN > Wikipedia > ussoccer.com) since sources are iterated in
    # that order and max() with key is stable.
    matches = []
    source_used = None
    if all_results:
        priority_order = [name for name, _ in sources]
        best_name = max(
            all_results,
            key=lambda n: (len(all_results[n]), -priority_order.index(n)),
        )
        matches = all_results[best_name]
        source_used = best_name

        # Log comparison across all sources
        comparison = ", ".join(
            f"{name}={len(all_results[name])}" if name in all_results else f"{name}=0"
            for name, _ in sources
        )
        logger.info(
            "Source comparison: %s. Using %s (%d matches)",
            comparison, source_used, len(matches),
        )

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

def espn_params():
    """Query params for the season scoreboard (verified live 2026-10-28).

    ESPN answers a date range (dates=YYYYMMDD-YYYYMMDD) with HTTP 400, so the
    whole season is requested by year in one call.
    """
    return {"dates": SEASON_YEAR, "limit": 500}


def fetch_espn():
    """Fetch every match of the season from ESPN's public scoreboard API.

    Each event is placed in its round by ESPN's season.slug, so the flat list
    comes back in bracket round order whatever order ESPN sends it in. Request
    and response errors propagate so scrape_bracket records them as an error.
    """
    resp = requests.get(ESPN_BASE, params=espn_params(), timeout=15)
    resp.raise_for_status()
    events = resp.json().get("events", [])

    slug_to_round = {meta["espnSlug"]: i for i, meta in enumerate(ROUND_META)}
    by_round = [[] for _ in ROUND_META]
    for event in events:
        slug = (event.get("season") or {}).get("slug")
        if slug not in slug_to_round:
            logger.warning("ESPN: skipping event %s with unknown round slug %r", event.get("id"), slug)
            continue
        match = parse_espn_event(event)
        if match:
            match["round"] = slug_to_round[slug]
            by_round[slug_to_round[slug]].append(match)

    for meta, round_matches in zip(ROUND_META, by_round):
        if round_matches:
            logger.info("ESPN: %d matches for %s", len(round_matches), meta["name"])

    return [m for round_matches in by_round for m in round_matches]


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
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(EASTERN)
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

    section_map = map_wiki_sections(sections)

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
                for m in matches:
                    m["round"] = round_idx
                all_matches.extend(matches)
            else:
                logger.warning("Wikipedia: no match boxes in section %s (%s)", section_idx, ROUND_META[round_idx]["name"])

        except Exception as e:
            logger.warning("Wikipedia fetch failed for section %s: %s", section_idx, e)
            continue

    return all_matches


# Section headings that hold each round's match boxes
WIKI_ROUND_TITLES = {
    "first round": 0,
    "second round": 1,
    "round of 32": 2,
    "round of 16": 3,
    "quarterfinals": 4,
    "quarter-finals": 4,
    "semifinals": 5,
    "semi-finals": 5,
    "final": 6,
}


def map_wiki_sections(sections):
    """Map round index to Wikipedia section index by exact heading match.

    Substring matching put "Semifinals" and "Quarterfinals and beyond" in the
    Final slot, so a heading must equal a round title to count.
    """
    section_map = {}
    for s in sections:
        title = s.get("line", "").strip().lower()
        if title in WIKI_ROUND_TITLES:
            section_map[WIKI_ROUND_TITLES[title]] = s["index"]
    return section_map


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


def _hyphenate(text):
    """Turn the en and em dashes Wikipedia uses in scores into hyphens."""
    return text.replace(chr(0x2013), "-").replace(chr(0x2014), "-")


def parse_wiki_box(box):
    """Parse a single football box collapsible template.

    The winner comes from the score, then from the penalty shootout score.
    Bold markup is ignored: the 2026 article bolds the losing team in every
    box, so it does not mark the winner.
    """
    def extract(field):
        # [ \t]* stops an empty field from capturing the next line
        m = re.search(rf'\|\s*{field}\s*=[ \t]*([^\n]*)', box)
        value = m.group(1).strip() if m else ""
        return value or None

    def score_pair(text):
        m = re.search(r'(\d+)\s*-\s*(\d+)', _hyphenate(text))
        return (int(m.group(1)), int(m.group(2))) if m else None

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
    if "a.e.t" in score_clean.lower() or "aet" in score_clean.lower() or (extract("aet") or "").lower() == "yes":
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
            "winner": None,
        }

    home_score = int(score_match.group(1))
    away_score = int(score_match.group(2))

    # Shootout score: the penaltyscore field, or a second score after the
    # first inside the score field, as in "1 - 1 (pen. 4 - 2)"
    pen_raw = extract("penaltyscore")
    if pen_raw:
        pens = score_pair(pen_raw)
    elif note == "PEN":
        pens = score_pair(score_clean[score_match.end():])
    else:
        pens = None
    if pens:
        note = "PEN"

    winner = None
    if home_score != away_score:
        winner = home if home_score > away_score else away
    elif pens and pens[0] != pens[1]:
        winner = home if pens[0] > pens[1] else away

    return {
        "home": home,
        "away": away,
        "homeScore": home_score,
        "awayScore": away_score,
        "date": date_raw,
        "note": note,
        "winner": winner,
    }


# ─── US SOCCER SUPPLEMENTAL (BEST-EFFORT) ────────────────────────────

# Regex for trailing notation such as (Forfeit), (AET), (AET & PKs), (PKs), (PEN)
_NOTATION_RE = re.compile(
    r'\s*\((?:Forfeit|FF|AET\s*&\s*PKs|AET|PKs?|PEN)\)\s*$',
    re.IGNORECASE,
)

# Also handle trailing "w/o" or "walkover" text
_WALKOVER_RE = re.compile(r'\s+(?:w/o|walkover)\s*$', re.IGNORECASE)

# Scoreline regex: HomeTeam <score> [(<pen>)] - <score> [(<pen>)] AwayTeam
_SCORELINE_RE = re.compile(
    r'^(.+?)\s+(\d+)\s*(?:\((\d+)\))?\s*-\s*(\d+)\s*(?:\((\d+)\))?\s+(.+?)$'
)


def parse_scoreline(text):
    """Parse a single scoreline string into a match dict.

    Handles notation like (Forfeit), (AET), (AET & PKs), (PEN), and
    penalty shootout scores in parentheses. Returns None if the text
    cannot be parsed.
    """
    if not text or not text.strip():
        return None

    # Normalize whitespace: collapse runs of spaces, strip edges
    cleaned = re.sub(r'\s+', ' ', text).strip()

    # Strip and capture trailing notation BEFORE applying scoreline regex.
    # This prevents notation text from polluting the away team name.
    notation_text = None
    notation_match = _NOTATION_RE.search(cleaned)
    if notation_match:
        notation_text = notation_match.group(0).strip().strip('()')
        cleaned = cleaned[:notation_match.start()].strip()
    else:
        walkover_match = _WALKOVER_RE.search(cleaned)
        if walkover_match:
            notation_text = walkover_match.group(0).strip()
            cleaned = cleaned[:walkover_match.start()].strip()

    # Apply the scoreline regex to the cleaned (notation-free) text
    m = _SCORELINE_RE.match(cleaned)
    if not m:
        return None

    home_name = m.group(1).strip()
    home_score = int(m.group(2))
    home_pen = int(m.group(3)) if m.group(3) else None
    away_score = int(m.group(4))
    away_pen = int(m.group(5)) if m.group(5) else None
    away_name = m.group(6).strip()

    # Determine the note field from captured notation and penalty scores
    note = None
    if notation_text:
        nt_lower = notation_text.lower()
        if 'forfeit' in nt_lower or nt_lower == 'ff':
            note = "FF"
        elif 'pk' in nt_lower or nt_lower == 'pen':
            note = "PEN"
        elif 'aet' in nt_lower:
            # "AET & PKs" already handled above via 'pks' check;
            # plain "AET" falls here
            note = "AET"
        elif 'w/o' in nt_lower or 'walkover' in nt_lower:
            note = "FF"

    # If penalty score groups are present but no notation was found, infer PEN
    if (home_pen is not None or away_pen is not None) and note is None:
        note = "PEN"

    # If penalty scores are present alongside AET notation, upgrade to PEN
    # because penalty kicks take precedence in describing the result
    if note == "AET" and (home_pen is not None or away_pen is not None):
        note = "PEN"

    return {
        "home": home_name,
        "away": away_name,
        "homeScore": home_score,
        "awayScore": away_score,
        "homePen": home_pen,
        "awayPen": away_pen,
        "date": None,
        "note": note,
    }


def fetch_ussoccer():
    """Best-effort scrape of ussoccer.com schedule page.

    This is a supplemental source, not a reliable fallback. The page
    structure changes frequently and the parser may return zero matches.
    ESPN and Wikipedia are the primary and backup sources respectively.
    """
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
    """Best-effort parse of match data from ussoccer.com schedule page.

    Tries multiple CSS selectors in priority order to handle page
    structure changes gracefully. This parser is supplemental; the
    page layout shifts often and may yield zero usable rows.
    """
    selectors = [
        ("table tbody tr", "table"),
        (".schedule-list .match, .match-row, [data-match]", "list"),
    ]

    for selector, label in selectors:
        rows = soup.select(selector)
        if not rows:
            continue

        logger.info("ussoccer.com: using '%s' selector (%d elements)", label, len(rows))
        matches = []

        for row in rows:
            try:
                if row.name == "tr":
                    cells = row.find_all("td")
                    if cells and len(cells) >= 1:
                        match = parse_ussoccer_row(cells)
                        if match:
                            matches.append(match)
                else:
                    # Non-table element: extract text and try parse_scoreline
                    text = row.get_text(" ", strip=True)
                    match = parse_scoreline(text)
                    if match:
                        matches.append(match)
            except Exception as e:
                logger.debug("Skipping ussoccer row: %s", e)
                continue

        if matches:
            return matches

    logger.warning("ussoccer.com: no selectors produced matches")
    return []


def parse_ussoccer_row(cells):
    """Parse a table row from ussoccer.com into a match dict.

    Tries joining all cell text for parse_scoreline, then falls back to
    individual cell text. Also checks for bold tags to detect the winner.
    """
    # Strategy 1: join all cell text and try parse_scoreline
    joined = " ".join(c.get_text(strip=True) for c in cells)
    match = parse_scoreline(joined)

    # Strategy 2: try each cell individually
    if not match:
        for cell in cells:
            text = cell.get_text(strip=True)
            match = parse_scoreline(text)
            if match:
                break

    if not match:
        return None

    # Bold-tag winner detection: check raw BeautifulSoup Tag objects for <b>
    # tags. The bolded text might wrap a team name, a score, or both. We
    # extract it and match against home/away names to set a winner field.
    winner = None
    for cell in cells:
        bold_tag = cell.find("b")
        if bold_tag:
            bold_text = bold_tag.get_text(strip=True)
            if bold_text and match.get("home") and bold_text in match["home"]:
                winner = match["home"]
                break
            if bold_text and match.get("away") and bold_text in match["away"]:
                winner = match["away"]
                break

    if winner:
        match["winner"] = winner

    return match


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


def _reorder_1to1_round(anchor_matches, matches):
    """Reorder matches so matches[i] shares a team with anchor_matches[i].

    Used for the R2->R32 transition where each R2 winner feeds into one R32
    match (1:1 mapping, not the usual 2:1 reduction). The frontend renders
    it as R2[i] connecting to R32[i]. build_bracket passes R32 (already in
    bracket order) as the anchor and R2 as the matches, so R2[i] becomes the
    match whose winner plays in R32[i].

    Returns a new list with corrected ordering, or the original list unchanged
    if reordering cannot be determined.
    """
    if len(anchor_matches) != len(matches):
        return matches

    # Build lookup: team name -> index in matches
    team_to_idx = {}
    for idx, match in enumerate(matches):
        for field in ("home", "away"):
            name = match.get(field, "")
            if name and name != "TBD":
                team_to_idx[name] = idx

    reordered = [None] * len(matches)
    used = set()

    for i, anchor in enumerate(anchor_matches):
        # Candidate teams from the anchor match, winner first
        winner = anchor.get("winner")
        candidates = [winner] if winner else []
        for field in ("home", "away"):
            name = anchor.get(field, "")
            if name and name != "TBD" and name not in candidates:
                candidates.append(name)

        # Find which match contains any candidate
        for cand in candidates:
            if cand in team_to_idx:
                m_idx = team_to_idx[cand]
                if m_idx not in used:
                    reordered[i] = matches[m_idx]
                    used.add(m_idx)
                    break

    # Fill remaining slots with unmatched matches
    unmatched = [j for j in range(len(matches)) if j not in used]
    for i in range(len(reordered)):
        if reordered[i] is None and unmatched:
            reordered[i] = matches[unmatched.pop(0)]

    if any(m is None for m in reordered):
        logger.warning("1:1 reordering produced None entries, keeping original order")
        return matches

    logger.info("1:1 round reordered successfully (%d matches)", len(reordered))
    return reordered


def build_bracket(matches):
    """Organize flat matches into round structure.

    Matches tagged with a "round" index (ESPN, Wikipedia) are grouped on it,
    so a missing or unparseable match cannot shift later rounds. Untagged
    matches (ussoccer.com) are sliced by fixed round sizes in list order.
    """
    rounds = []
    round_sizes = [32, 16, 16, 8, 4, 2, 1]

    if matches and all(isinstance(m.get("round"), int) for m in matches):
        grouped = [[m for m in matches if m["round"] == i] for i in range(len(round_sizes))]
    else:
        if matches:
            logger.warning("Matches carry no round tag; slicing by fixed round sizes")
        grouped = []
        idx = 0
        for size in round_sizes:
            grouped.append(matches[idx:idx + size])
            idx += size

    for i, size in enumerate(round_sizes):
        if len(grouped[i]) > size:
            logger.warning("%s has %d matches, more than the %d expected", ROUND_META[i]["name"], len(grouped[i]), size)
        rounds.append({
            "name": ROUND_META[i]["name"],
            "schedule": ROUND_META[i]["schedule"],
            "matches": grouped[i],
        })

    # Put every round in bracket order, working back from the Final: each
    # feeder round is reordered to line up with the round after it, which
    # is already in its final order. Reordering forward (R32 to R16, then
    # R32 again to R2) undid earlier alignments and drew connector lines
    # between matches that never fed each other.
    #   2:1 rounds: feeder[2i] and feeder[2i+1] feed next[i]
    #   R2 (idx 1) -> R32 (idx 2), the MLS entry round, is 1:1: R2[i] feeds R32[i]
    for feeder_idx in range(len(rounds) - 2, -1, -1):
        next_idx = feeder_idx + 1
        feeder_round = rounds[feeder_idx]["matches"]
        next_round = rounds[next_idx]["matches"]

        if not feeder_round or not next_round:
            continue

        try:
            if feeder_idx == 1:
                if len(feeder_round) == len(next_round):
                    rounds[feeder_idx]["matches"] = _reorder_1to1_round(next_round, feeder_round)
                else:
                    logger.warning(
                        "Skipping 1:1 reorder for rounds %d->%d: %d feeder matches but %d next",
                        feeder_idx, next_idx, len(feeder_round), len(next_round)
                    )
            elif len(feeder_round) == 2 * len(next_round):
                rounds[feeder_idx]["matches"] = _reorder_feeder_round(feeder_round, next_round)
            else:
                logger.warning(
                    "Skipping reorder for rounds %d->%d: expected %d feeder matches but got %d",
                    feeder_idx, next_idx, 2 * len(next_round), len(feeder_round)
                )
        except Exception as e:
            logger.error("Reordering failed for rounds %d->%d: %s", feeder_idx, next_idx, e)
            # Keep original order on any unexpected error

    return {"rounds": rounds}
