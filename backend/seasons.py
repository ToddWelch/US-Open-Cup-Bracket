"""Per-season tournament settings and the frozen archives of past seasons.

Each season is one JSON file in season_data/ (round names, sizes, dates, ESPN
round slugs, team tiers). A finished season also has a committed
<year>-bracket.json, served as-is and never scraped again.
"""

import json
import os

SEASON_DIR = os.path.join(os.path.dirname(__file__), "season_data")

# The season on the root URL. Every other season with a config is an archive.
CURRENT_YEAR = 2027

_REQUIRED = ("year", "edition", "teams", "purse", "wikiPage", "entryRound", "entryLabels", "rounds", "tiers")
_ROUND_REQUIRED = ("name", "label", "short", "schedule", "dates", "espnSlug", "size")


def _load(year):
    with open(os.path.join(SEASON_DIR, f"{year}.json")) as f:
        season = json.load(f)
    missing = [k for k in _REQUIRED if k not in season]
    if missing:
        raise ValueError(f"Season {year} config is missing {missing}")
    if season["year"] != year:
        raise ValueError(f"Season file {year}.json says year {season['year']}")
    for r in season["rounds"]:
        missing = [k for k in _ROUND_REQUIRED if k not in r]
        if missing:
            raise ValueError(f"Season {year} round {r.get('name')} is missing {missing}")
    sizes = [r["size"] for r in season["rounds"]]
    entry = season["entryRound"]
    # Every round halves the field except the entry round, which pairs 1:1
    # with the round before it (new entrants join there)
    for i in range(1, len(sizes)):
        expected = sizes[i - 1] if i == entry else sizes[i - 1] // 2
        if sizes[i] != expected:
            raise ValueError(f"Season {year}: {season['rounds'][i]['name']} has {sizes[i]} matches, expected {expected}")
    if sizes[-1] != 1:
        raise ValueError(f"Season {year}: the last round must be a single Final")
    return season


def _years():
    years = []
    for name in os.listdir(SEASON_DIR):
        stem = name[:-5] if name.endswith(".json") else ""
        if stem.isdigit() and len(stem) == 4:
            years.append(int(stem))
    return sorted(years)


# Loaded once at import; a bad config stops the app from starting
SEASONS = {year: _load(year) for year in _years()}
if CURRENT_YEAR not in SEASONS:
    raise ValueError(f"No config for the current season {CURRENT_YEAR}")


def current():
    return SEASONS[CURRENT_YEAR]


def get(year):
    return SEASONS.get(year)


def archived_years():
    """Past seasons with a frozen bracket file, newest first."""
    return sorted((y for y in SEASONS if y != CURRENT_YEAR and os.path.exists(archive_path(y))), reverse=True)


def archive_path(year):
    return os.path.join(SEASON_DIR, f"{year}-bracket.json")


def load_archive(year):
    with open(archive_path(year)) as f:
        return json.load(f)


def public_info(season):
    """The settings the page needs to draw a season, served with its bracket."""
    return {
        "year": season["year"],
        "current": season["year"] == CURRENT_YEAR,
        "currentYear": CURRENT_YEAR,
        "archives": archived_years(),
        "edition": season["edition"],
        "teams": season["teams"],
        "purse": season["purse"],
        "entryRound": season["entryRound"],
        "entryLabels": season["entryLabels"],
        "rounds": [
            {k: r[k] for k in ("name", "label", "short", "schedule", "size")}
            for r in season["rounds"]
        ],
        "tiers": season["tiers"],
    }
