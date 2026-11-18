"""Tests for the season rollover: the season configs, the frozen 2026
archive, the API per season, the /2026 page and the sitemap.
"""

import os
import shutil
import sys

import pytest

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import scheduler, scraper, seasons

REPO = os.path.join(os.path.dirname(__file__), "..", "..")


class TestConfigs:
    def test_current_season_is_2027_and_2026_is_archived(self):
        assert seasons.CURRENT_YEAR == 2027
        assert seasons.archived_years() == [2026]

    def test_2027_shape(self):
        s = seasons.get(2027)
        assert [r["size"] for r in s["rounds"]] == [32, 32, 16, 8, 4, 2, 1]
        assert s["entryRound"] == 1
        assert s["teams"] == 96

    def test_2026_shape_is_unchanged(self):
        s = seasons.get(2026)
        assert [r["size"] for r in s["rounds"]] == [32, 16, 16, 8, 4, 2, 1]
        assert s["entryRound"] == 2

    def test_season_files_have_no_dashes(self):
        """Round names, schedules and team names in these files are public copy."""
        from backend.articles import BANNED_CHARS
        for name in os.listdir(seasons.SEASON_DIR):
            with open(os.path.join(seasons.SEASON_DIR, name), encoding="utf-8") as f:
                text = f.read()
            assert not any(ch in text for ch in BANNED_CHARS), name

    def test_every_season_has_page_copy(self):
        """The page's description section is per season; a new season with
        no entry in SEASON_COPY would show no description at all."""
        with open(os.path.join(REPO, "frontend", "src", "App.jsx"), encoding="utf-8") as f:
            app = f.read()
        for year in seasons.SEASONS:
            assert f"{year}: Season{year}Copy" in app, year

    def test_2027_tiers_cover_all_27_us_mls_clubs(self):
        mls = seasons.get(2027)["tiers"]["MLS"]
        # Two clubs are listed under both spellings sources use
        assert len(mls) - 2 == 27


class TestArchive2026:
    def test_archive_is_complete_and_passes_the_data_checks(self):
        data = seasons.load_archive(2026)
        assert [len(r["matches"]) for r in data["rounds"]] == [32, 16, 16, 8, 4, 2, 1]
        assert all(m["winner"] for r in data["rounds"] for m in r["matches"])
        assert scraper.validate_bracket(data, seasons.get(2026)) == []
        final = data["rounds"][6]["matches"][0]
        assert final["winner"] == "St. Louis CITY SC" and final["note"] == "PEN"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """The real app.py with an empty data folder, no startup scrape and no
    scheduler, serving the source index.html as its built page."""
    data_dir = tmp_path_factory.mktemp("data")
    static = tmp_path_factory.mktemp("dist")
    shutil.copy(os.path.join(REPO, "frontend", "index.html"), static / "index.html")

    saved = (scraper.DATA_DIR, scraper.BRACKET_FILE, scraper.scrape_bracket, scheduler.init_scheduler)
    scraper.DATA_DIR = str(data_dir)
    scraper.BRACKET_FILE = str(data_dir / "bracket.json")
    scraper.scrape_bracket = lambda season=None: None
    scheduler.init_scheduler = lambda: None
    try:
        from backend import app as app_module
        app_module.app.static_folder = str(static)
        yield app_module.app.test_client()
    finally:
        scraper.DATA_DIR, scraper.BRACKET_FILE, scraper.scrape_bracket, scheduler.init_scheduler = saved


class TestApi:
    def test_root_bracket_is_2027_and_empty_before_any_scrape(self, client):
        data = client.get("/api/bracket").get_json()
        assert data["season"] == 2027
        assert data["seasonInfo"]["current"] is True
        assert data["seasonInfo"]["archives"] == [2026]
        assert [r["name"] for r in data["rounds"]][1] == "Round of 64"
        assert all(r["matches"] == [] for r in data["rounds"])

    def test_2026_bracket_comes_from_the_archive(self, client):
        data = client.get("/api/bracket?season=2026").get_json()
        assert data["seasonInfo"]["current"] is False
        assert data["seasonInfo"]["entryLabels"] == {"top": "MLS Team", "bottom": "R2 Winner"}
        assert data["rounds"][6]["matches"][0]["winner"] == "St. Louis CITY SC"

    def test_unknown_season_is_404(self, client):
        assert client.get("/api/bracket?season=2025").status_code == 404


class TestSeasonPages:
    def test_2026_page_has_its_own_title_canonical_and_card(self, client):
        r = client.get("/2026")
        body = r.get_data(as_text=True)
        assert r.status_code == 200
        assert "<title>2026 U.S. Open Cup Bracket and Results</title>" in body
        assert '<link rel="canonical" href="https://usopencup.welchproductsllc.com/2026" />' in body
        assert "og-image-2026.png" in body
        assert "2027 U.S. Open Cup Bracket" not in body
        assert '<a href="/">the 2027 bracket</a>' in body
        assert '<div id="root"></div>' in body

    def test_root_page_is_2027(self, client):
        body = client.get("/").get_data(as_text=True)
        assert "<title>2027 U.S. Open Cup Bracket, Schedule and Results</title>" in body
        assert '<a href="/2026">the 2026 bracket and results</a>' in body

    def test_current_year_url_redirects_to_root(self, client):
        """Temporary (302): /2027 becomes the 2027 archive once the season ends."""
        r = client.get("/2027")
        assert r.status_code == 302 and r.headers["Location"].endswith("/")

    def test_unknown_year_is_404(self, client):
        assert client.get("/2025").status_code == 404

    def test_articles_still_win_over_season_pages(self, client):
        assert client.get("/2026/final").status_code == 200

    def test_sitemap_lists_the_archive(self, client):
        sitemap = client.get("/sitemap.xml").get_data(as_text=True)
        assert "<loc>https://usopencup.welchproductsllc.com/2026</loc>" in sitemap

    def test_page_without_markers_fails_instead_of_serving_2027_copy(self, client, tmp_path):
        from backend import app as app_module
        (tmp_path / "index.html").write_text("<html><head><title>x</title></head><body></body></html>")
        saved = app_module.app.static_folder
        app_module.app.static_folder = str(tmp_path)
        try:
            assert client.get("/2026").status_code == 500
        finally:
            app_module.app.static_folder = saved
