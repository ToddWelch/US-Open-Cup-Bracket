import os
import sys

import pytest

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import scraper


@pytest.fixture(autouse=True)
def no_real_slack(monkeypatch):
    """No test may post to the real alert channel, whatever the environment
    holds; tests that check alerts swap in their own sender."""
    monkeypatch.setattr(scraper, "SLACK_WEBHOOK_URL", None)
    monkeypatch.setattr(scraper, "_last_alert", {})
