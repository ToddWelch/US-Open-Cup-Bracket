"""Routes for the news articles, robots.txt and sitemap.xml.

Articles are loaded once when this module is imported; an invalid post
raises there and stops the app from starting.
"""

from flask import Blueprint, Response, abort, jsonify, render_template

try:
    from .articles import SITE_URL, load_articles
except ImportError:
    from articles import SITE_URL, load_articles

bp = Blueprint("articles", __name__, template_folder="templates")

ARTICLES = load_articles()


def published_articles():
    return [a for a in ARTICLES if a.is_published]


@bp.route("/news")
def news_index():
    return render_template("news.html", articles=published_articles(), site_url=SITE_URL)


@bp.route("/<int(fixed_digits=4):season>/<slug>")
def article_page(season, slug):
    for a in published_articles():
        if a.season == season and a.slug == slug:
            related = [r for r in published_articles() if r is not a][:4]
            return render_template("article.html", article=a, related=related, site_url=SITE_URL)
    abort(404)


@bp.route("/api/articles")
def api_articles():
    return jsonify([
        {
            "title": a.title,
            "path": a.path,
            "season": a.season,
            "published": a.published.isoformat(),
            "description": a.meta_description,
        }
        for a in published_articles()
    ])


@bp.route("/robots.txt")
def robots_txt():
    body = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap_xml():
    posts = published_articles()
    newest = max((a.updated or a.published for a in posts), default=None)
    entries = [(f"{SITE_URL}/", None), (f"{SITE_URL}/news", newest)]
    entries += [(a.url, a.updated or a.published) for a in posts]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in entries:
        lines.append(f"  <url><loc>{loc}</loc>" + (f"<lastmod>{lastmod.isoformat()}</lastmod>" if lastmod else "") + "</url>")
    lines.append("</urlset>")
    return Response("\n".join(lines) + "\n", mimetype="application/xml")
