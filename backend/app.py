import json
import os
from flask import Flask, jsonify, send_from_directory
from scraper import scrape_bracket
from scheduler import init_scheduler

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BRACKET_FILE = os.path.join(DATA_DIR, "bracket.json")


def load_bracket():
    if not os.path.exists(BRACKET_FILE):
        return None
    with open(BRACKET_FILE, "r") as f:
        return json.load(f)


@app.route("/api/bracket")
def api_bracket():
    data = load_bracket()
    if data is None:
        return jsonify({"error": "No bracket data available"}), 503
    return jsonify(data)


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    # Run initial scrape if bracket data is missing
    bracket = load_bracket()
    if bracket is None or not bracket.get("rounds"):
        print("No bracket data found, running initial scrape...")
        scrape_bracket()

    init_scheduler()
    app.run(host="0.0.0.0", port=8080, debug=True)
