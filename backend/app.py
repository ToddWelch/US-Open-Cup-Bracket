import hmac
import logging
import os
import re
from flask import Flask, Response, abort, jsonify, redirect, render_template, request, send_from_directory
try:
    from . import seasons
    from .scraper import build_bracket, load_existing, scrape_bracket, send_slack_alert
    from .scheduler import init_scheduler
    from .article_routes import bp as articles_bp
except ImportError:
    import seasons
    from scraper import build_bracket, load_existing, scrape_bracket, send_slack_alert
    from scheduler import init_scheduler
    from article_routes import bp as articles_bp

logger = logging.getLogger(__name__)

ADMIN_KEY = os.environ.get("ADMIN_KEY")

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")
app.register_blueprint(articles_bp)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# index.html marks the parts that differ per season; an archive page swaps
# them for its own templates/seasons/<year>_head.html and _noscript.html
SEASON_BLOCKS = {
    "head": re.compile(r"<!-- season-head:start -->.*?<!-- season-head:end -->", re.S),
    "noscript": re.compile(r"<!-- season-noscript:start -->.*?<!-- season-noscript:end -->", re.S),
}


@app.route("/api/bracket")
def api_bracket():
    year = request.args.get("season", default=seasons.CURRENT_YEAR, type=int)
    season = seasons.get(year)
    if year == seasons.CURRENT_YEAR:
        # Before the first scrape there is no file: an empty bracket, not an error
        data = load_existing(season) or build_bracket([], season)
    elif season and year in seasons.archived_years():
        data = seasons.load_archive(year)
    else:
        return jsonify({"error": "Unknown season"}), 404
    return jsonify({**data, "seasonInfo": seasons.public_info(season)})


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok"})


def check_admin_key():
    """Validate the X-Admin-Key header against the ADMIN_KEY env var.
    Returns a Flask error response tuple if validation fails, or None on success."""
    if not ADMIN_KEY:
        return jsonify({"error": "Endpoint not available"}), 404
    key = request.headers.get("X-Admin-Key")
    if not key or not hmac.compare_digest(key, ADMIN_KEY):
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
    data = load_existing()
    if data is None:
        return jsonify({"status": "error", "message": "Scrape produced no data"}), 500
    return jsonify({
        "status": data.get("scrapeStatus"),
        "source": data.get("scrapeSource"),
        "lastScrape": data.get("lastScrape"),
        "sourceResults": data.get("sourceResults"),
    })


@app.route("/<int(fixed_digits=4):year>")
def season_page(year):
    """A past season's bracket: the same page with that season's title,
    description and share card. The current season lives on the root URL."""
    if year == seasons.CURRENT_YEAR:
        return redirect("/", code=301)
    if year not in seasons.archived_years():
        abort(404)
    with open(os.path.join(app.static_folder, "index.html")) as f:
        html = f.read()
    for block, pattern in SEASON_BLOCKS.items():
        if not pattern.search(html):
            # A build that lost the markers would serve the wrong season's
            # title and description; fail instead
            raise RuntimeError(f"index.html has no season-{block} markers")
        replacement = render_template(f"seasons/{year}_{block}.html")
        html = pattern.sub(lambda _: replacement, html, count=1)
    return Response(html, mimetype="text/html")


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

# Run initial scrape if this season has no saved bracket
if load_existing() is None:
    print("No bracket data found for this season, running initial scrape...")
    scrape_bracket()

init_scheduler()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true")
    app.run(host="0.0.0.0", port=port, debug=debug)
