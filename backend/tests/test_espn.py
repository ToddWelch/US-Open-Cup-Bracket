"""Tests for the ESPN fetcher: request shape, round ordering by season slug,
and Eastern Time match dates. The live API is exercised in test_live_sources.py.
"""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import scraper


def make_event(event_id, slug, home, away, home_score, away_score, date, state="STATUS_FULL_TIME", winner=None):
    def competitor(name, side, score):
        return {"homeAway": side, "score": str(score), "winner": name == winner, "team": {"displayName": name}}

    return {
        "id": event_id,
        "date": date,
        "season": {"year": 2026, "slug": slug},
        "competitions": [{
            "competitors": [competitor(home, "home", home_score), competitor(away, "away", away_score)],
            "status": {"type": {"name": state, "completed": True, "detail": "FT"}},
        }],
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class TestRequestShape:
    def test_params_exact(self):
        """Pinned 2026-10-28: ESPN returns HTTP 400 for dates=YYYYMMDD-YYYYMMDD
        and the full season for dates=<year>. Changing this needs a live check."""
        assert scraper.espn_params() == {"dates": "2026", "limit": 500}


class TestRoundOrdering:
    def test_events_grouped_in_round_order_and_unknown_slug_skipped(self, monkeypatch):
        events = [
            make_event("f", "final", "Columbus Crew", "St. Louis CITY SC", 0, 0, "2026-10-22T00:00Z", "STATUS_FINAL_PEN", "St. Louis CITY SC"),
            make_event("x", "friendly", "A", "B", 1, 0, "2026-06-01T00:00Z", winner="A"),
            make_event("r1", "first-round", "Lexington", "Flower City Union", 9, 0, "2026-03-19T23:00Z", winner="Lexington"),
            make_event("sf", "semifinals", "Columbus Crew", "Orlando City SC", 2, 1, "2026-09-16T23:00Z", winner="Columbus Crew"),
        ]
        captured = {}

        def fake_get(url, params=None, timeout=None):
            captured["url"], captured["params"] = url, params
            return FakeResponse({"events": events})

        monkeypatch.setattr(scraper.requests, "get", fake_get)
        matches = scraper.fetch_espn()

        assert captured == {"url": scraper.ESPN_BASE, "params": scraper.espn_params()}
        assert [m["home"] for m in matches] == ["Lexington", "Columbus Crew", "Columbus Crew"]
        assert matches[-1]["winner"] == "St. Louis CITY SC"
        assert matches[-1]["note"] == "PEN"


class TestSlackAlertLogging:
    def test_failed_alert_does_not_log_the_webhook_url(self, monkeypatch, caplog):
        """requests puts the URL in its exception text; the webhook URL is a secret."""
        webhook = "https://hooks.slack.com/services/T000/B000/not-a-real-token"
        monkeypatch.setattr(scraper, "SLACK_WEBHOOK_URL", webhook)

        def failing_post(url, **kwargs):
            raise scraper.requests.ConnectionError(f"Max retries exceeded with url: {url}")

        monkeypatch.setattr(scraper.requests, "post", failing_post)
        with caplog.at_level("ERROR"):
            scraper.send_slack_alert("test")

        assert "ConnectionError" in caplog.text
        assert "hooks.slack.com" not in caplog.text


class TestErrorPropagation:
    def test_http_error_is_recorded_and_existing_bracket_kept(self, monkeypatch, tmp_path):
        """An ESPN HTTP error shows as status "error" (type name only, since
        the file is public) and never replaces the saved bracket."""
        monkeypatch.setattr(scraper, "DATA_DIR", str(tmp_path))
        monkeypatch.setattr(scraper, "BRACKET_FILE", str(tmp_path / "bracket.json"))
        monkeypatch.setattr(scraper, "SLACK_WEBHOOK_URL", None)
        existing = scraper.build_bracket([
            {"home": "A", "away": "B", "homeScore": 1, "awayScore": 0, "winner": "A", "round": 0},
        ])
        scraper.save_bracket(existing)

        class ErrorResponse:
            def raise_for_status(self):
                raise scraper.requests.HTTPError("400 Client Error: Bad Request for url: " + scraper.ESPN_BASE)

        monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: ErrorResponse())
        monkeypatch.setattr(scraper, "fetch_wikipedia", lambda: [])
        monkeypatch.setattr(scraper, "fetch_ussoccer", lambda: [])

        scraper.scrape_bracket()
        saved = scraper.load_existing()

        espn = next(s for s in saved["sourceResults"] if s["name"] == "ESPN")
        assert espn == {"name": "ESPN", "status": "error", "error": "HTTPError", "matches": 0}
        assert saved["scrapeStatus"] == "stale"
        assert saved["rounds"][0]["matches"][0]["home"] == "A"


class TestEasternDates:
    def test_evening_kickoff_keeps_eastern_date(self):
        """8pm ET on Oct 21 is 00:00 UTC on Oct 22; the bracket shows Oct 21."""
        event = make_event("f", "final", "Columbus Crew", "St. Louis CITY SC", 0, 0, "2026-10-22T00:00Z", "STATUS_FINAL_PEN", "St. Louis CITY SC")
        assert scraper.parse_espn_event(event)["date"] == "October 21"
