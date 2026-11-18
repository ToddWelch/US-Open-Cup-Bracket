"""Tests for the ESPN fetcher: request shape, round ordering by season slug,
and Eastern Time match dates. The live API is exercised in test_live_sources.py.
"""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import scraper, seasons

SEASON_2026 = seasons.get(2026)
SEASON_2027 = seasons.get(2027)


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
        assert scraper.espn_params(SEASON_2026) == {"dates": "2026", "limit": 500}

    def test_current_season_is_2027(self):
        assert scraper.espn_params() == {"dates": "2027", "limit": 500}


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
        matches = scraper.fetch_espn(SEASON_2026)

        assert captured == {"url": scraper.ESPN_BASE, "params": scraper.espn_params(SEASON_2026)}
        assert [m["home"] for m in matches] == ["Lexington", "Columbus Crew", "Columbus Crew"]
        assert matches[-1]["winner"] == "St. Louis CITY SC"
        assert matches[-1]["note"] == "PEN"

    def test_unknown_2027_slug_is_placed_by_kickoff_date(self, monkeypatch):
        """ESPN's slug for the new Round of 64 is not known until it posts the
        games; a match on July 9, 2027 still lands in the Round of 64."""
        events = [
            make_event("a", "round-64", "Nashville SC", "Lexington SC", 2, 1, "2027-07-09T23:30Z", winner="Nashville SC"),
            make_event("b", "first-round", "Richmond Kickers", "Virginia Dream FC", 3, 0, "2027-04-14T23:00Z", winner="Richmond Kickers"),
            make_event("q", "qualifying", "X", "Y", 1, 0, "2027-02-01T20:00Z", winner="X"),
        ]
        monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: FakeResponse({"events": events}))
        matches = scraper.fetch_espn(SEASON_2027)

        assert [(m["home"], m["round"]) for m in matches] == [("Richmond Kickers", 0), ("Nashville SC", 1)]


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

    def test_rejected_alert_is_logged_as_an_error_without_the_url(self, monkeypatch, caplog):
        """A revoked or rotated webhook answers 4xx; that must not read as sent."""
        webhook = "https://hooks.slack.com/services/T000/B000/not-a-real-token"
        monkeypatch.setattr(scraper, "SLACK_WEBHOOK_URL", webhook)

        class Rejected:
            status_code = 404
            url = webhook

        monkeypatch.setattr(scraper.requests, "post", lambda url, **kwargs: Rejected())
        with caplog.at_level("INFO"):
            scraper.send_slack_alert("test")

        assert "Slack alert rejected: HTTP 404" in caplog.text
        assert "Slack alert sent" not in caplog.text
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
        monkeypatch.setattr(scraper, "fetch_wikipedia", lambda season=None: [])

        scraper.scrape_bracket()
        saved = scraper.load_existing()

        espn = next(s for s in saved["sourceResults"] if s["name"] == "ESPN")
        assert espn == {"name": "ESPN", "status": "error", "error": "HTTPError", "matches": 0}
        assert saved["scrapeStatus"] == "stale"
        assert saved["rounds"][0]["matches"][0]["home"] == "A"


def use_tmp_data(monkeypatch, tmp_path):
    monkeypatch.setattr(scraper, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(scraper, "BRACKET_FILE", str(tmp_path / "bracket.json"))
    monkeypatch.setattr(scraper, "_last_alert", {})
    alerts = []
    monkeypatch.setattr(scraper, "send_slack_alert", alerts.append)
    return alerts


class TestSeasonStates:
    def test_before_the_pairings_an_empty_bracket_is_saved_without_an_alert(self, monkeypatch, tmp_path):
        """No 2027 matches yet is normal before April: the page shows every
        round empty and nobody gets paged."""
        alerts = use_tmp_data(monkeypatch, tmp_path)
        monkeypatch.setattr(scraper, "fetch_espn", lambda season=None: [])
        monkeypatch.setattr(scraper, "fetch_wikipedia", lambda season=None: [])
        monkeypatch.setattr(scraper, "in_season", lambda season=None, today=None: False)

        scraper.scrape_bracket()
        saved = scraper.load_existing()

        assert saved["season"] == 2027
        assert saved["scrapeStatus"] == "waiting"
        assert [len(r["matches"]) for r in saved["rounds"]] == [0] * 7
        assert alerts == []

    def test_no_espn_data_during_the_tournament_alerts_once(self, monkeypatch, tmp_path):
        alerts = use_tmp_data(monkeypatch, tmp_path)
        monkeypatch.setattr(scraper, "fetch_espn", lambda season=None: [])
        monkeypatch.setattr(scraper, "fetch_wikipedia", lambda season=None: [])
        monkeypatch.setattr(scraper, "in_season", lambda season=None, today=None: True)

        scraper.scrape_bracket()
        scraper.scrape_bracket()

        assert scraper.load_existing()["scrapeStatus"] == "stale"
        assert len(alerts) == 1  # the second scrape is inside the repeat window
        assert "ESPN: no_data" in alerts[0]

    def test_data_that_fails_its_checks_never_replaces_the_bracket(self, monkeypatch, tmp_path):
        alerts = use_tmp_data(monkeypatch, tmp_path)
        good = {"home": "A", "away": "B", "homeScore": 2, "awayScore": 0, "winner": "A", "round": 0}
        scraper.save_bracket(scraper.build_bracket([good]))
        # B marked as winner of a match A won 3-0
        bad = [dict(good, homeScore=3, winner="B"), {"home": "C", "away": "D", "homeScore": 1, "awayScore": 0, "winner": "C", "round": 0}]
        monkeypatch.setattr(scraper, "fetch_espn", lambda season=None: bad)
        monkeypatch.setattr(scraper, "fetch_wikipedia", lambda season=None: [])

        scraper.scrape_bracket()
        saved = scraper.load_existing()

        assert saved["rounds"][0]["matches"] == [good]
        assert saved["scrapeStatus"] == "stale"
        assert len(alerts) == 1 and "failed checks" in alerts[0]

    def test_a_2026_file_is_not_shown_as_2027(self, monkeypatch, tmp_path):
        """A data file left from before the rollover counts as missing, so
        the first 2027 scrape starts clean instead of keeping 2026 matches."""
        use_tmp_data(monkeypatch, tmp_path)
        scraper.save_bracket(scraper.build_bracket([
            {"home": "A", "away": "B", "homeScore": 1, "awayScore": 0, "winner": "A", "round": 0}], SEASON_2026))
        assert scraper.load_existing() is None
        assert scraper.load_existing(SEASON_2026)["season"] == 2026

    def test_season_window(self):
        assert not scraper.in_season(SEASON_2027, today="20270412")
        assert scraper.in_season(SEASON_2027, today="20270413")
        assert scraper.in_season(SEASON_2027, today="20271216")
        assert not scraper.in_season(SEASON_2027, today="20271217")


class TestEasternDates:
    def test_evening_kickoff_keeps_eastern_date(self):
        """8pm ET on Oct 21 is 00:00 UTC on Oct 22; the bracket shows Oct 21."""
        event = make_event("f", "final", "Columbus Crew", "St. Louis CITY SC", 0, 0, "2026-10-22T00:00Z", "STATUS_FINAL_PEN", "St. Louis CITY SC")
        assert scraper.parse_espn_event(event)["date"] == "October 21"
