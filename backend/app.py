import json
import logging
import os
from flask import Flask, jsonify, request, send_from_directory
from scraper import scrape_bracket, send_slack_alert
from scheduler import init_scheduler

logger = logging.getLogger(__name__)

ADMIN_KEY = os.environ.get("ADMIN_KEY")

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRACKET_FILE = os.path.join(DATA_DIR, "bracket.json")


def load_bracket():
    if not os.path.exists(BRACKET_FILE):
        return None
    try:
        with open(BRACKET_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read bracket.json: %s", e)
        return None


@app.route("/api/bracket")
def api_bracket():
    data = load_bracket()
    if data is None:
        return jsonify({"error": "No bracket data available"}), 503
    return jsonify(data)


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok"})


def check_admin_key():
    """Validate the X-Admin-Key header against the ADMIN_KEY env var.
    Returns a Flask error response tuple if validation fails, or None on success."""
    if not ADMIN_KEY:
        return jsonify({"error": "Endpoint not available"}), 404
    key = request.headers.get("X-Admin-Key")
    if key != ADMIN_KEY:
        return jsonify({"error": "Forbidden"}), 403
    return None


@app.route("/api/test-alert", methods=["POST"])
def api_test_alert():
    auth_err = check_admin_key()
    if auth_err:
        return auth_err
    send_slack_alert(":test_tube: *US Open Cup Bracket - Test Alert*\nSlack integration is working.")
    return jsonify({"status": "alert sent"})


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    auth_err = check_admin_key()
    if auth_err:
        return auth_err
    scrape_bracket()
    data = load_bracket()
    if data is None:
        return jsonify({"status": "error", "message": "Scrape produced no data"}), 500
    return jsonify({
        "status": data.get("scrapeStatus"),
        "source": data.get("scrapeSource"),
        "lastScrape": data.get("lastScrape"),
        "sourceResults": data.get("sourceResults"),
    })


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


os.makedirs(DATA_DIR, exist_ok=True)

# Run initial scrape if bracket data is missing
bracket = load_bracket()
if bracket is None or not bracket.get("rounds"):
    print("No bracket data found, running initial scrape...")
    scrape_bracket()

init_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
