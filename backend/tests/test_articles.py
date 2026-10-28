"""Tests for the articles loader, renderer and routes.

The real posts in backend/content/posts are loaded and checked here, so a
bad post (missing field, dash character, long title tag) fails the suite
before it can fail a deploy.
"""

import os
import re
import sys

import pytest
from flask import Flask

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend import articles
from backend.articles import ArticleError, build_article, load_articles, render_markdown

EN_DASH = chr(0x2013)


def make_post(body="Body text.", source="Example | https://example.com/a", **overrides):
    fields = {
        "title": "Test Post",
        "meta_description": "A short description.",
        "target_phrase": "test phrase",
        "season": "2026",
        "slug": "test-post",
        "published": "2026-10-28",
        "status": "published",
    }
    fields.update(overrides)
    lines = [f"{k}: {v}" for k, v in fields.items() if v is not None]
    if source is not None:
        lines.append(f"source: {source}")
    return "---\n" + "\n".join(lines) + f"\n---\n\n# {fields['title']}\n\n{body}\n"


class TestRealPosts:
    def test_all_posts_load_and_four_are_published(self):
        posts = load_articles()
        published = [a for a in posts if a.is_published]
        assert {a.path for a in published} >= {
            "/2026/final", "/2026/cupsets", "/2027/format-and-schedule", "/2027/draw",
        }

    def test_broken_site_link_fails_the_load(self, tmp_path):
        (tmp_path / "a.md").write_text(make_post(body="See [the draw](/2027/drw)."))
        with pytest.raises(ArticleError, match="links to /2027/drw"):
            load_articles(str(tmp_path))

    def test_broken_absolute_link_to_this_site_fails_the_load(self, tmp_path):
        body = f"See [the draw]({articles.SITE_URL}/2027/drw) and [the bracket]({articles.SITE_URL}/)."
        (tmp_path / "a.md").write_text(make_post(body=body))
        with pytest.raises(ArticleError, match="links to /2027/drw"):
            load_articles(str(tmp_path))

    @pytest.mark.parametrize("prefix", [
        "http://usopencup.welchproductsllc.com",
        "https://USOPENCUP.welchproductsllc.com",
        "https://www.usopencup.welchproductsllc.com",
        "https://usopencup.welchproductsllc.com:443",
    ])
    def test_broken_link_variants_to_this_site_fail_the_load(self, tmp_path, prefix):
        (tmp_path / "a.md").write_text(make_post(body=f"See [the draw]({prefix}/2027/drw)."))
        with pytest.raises(ArticleError, match="links to /2027/drw"):
            load_articles(str(tmp_path))

    def test_valid_absolute_link_to_this_site_loads(self, tmp_path):
        (tmp_path / "a.md").write_text(make_post(body=f"See [the news]({articles.SITE_URL}/news)."))
        assert len(load_articles(str(tmp_path))) == 1

    def test_published_post_cannot_link_to_a_draft(self, tmp_path):
        (tmp_path / "a.md").write_text(make_post(body="See [next](/2026/next-one)."))
        (tmp_path / "b.md").write_text(make_post(slug="next-one", status="draft"))
        with pytest.raises(ArticleError, match="links to /2026/next-one"):
            load_articles(str(tmp_path))


class TestWriterBrief:
    BRIEF = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "grok-content-brief.md")

    def test_brief_example_post_passes_validation(self):
        """The example in the writer brief must stay a valid draft, so the
        agent following it produces files the site accepts."""
        text = open(self.BRIEF, encoding="utf-8").read()
        example = re.search(r"```markdown\n(.*?)```", text, re.S).group(1)
        a = build_article(example, "brief-example.md")
        assert a.status == "draft"
        assert a.path == "/2027/first-round-pairings"

    def test_brief_lists_every_published_post(self):
        text = open(self.BRIEF, encoding="utf-8").read()
        for a in load_articles():
            if a.is_published:
                assert f"`{a.path}`" in text, f"brief is missing {a.path}"

    def test_brief_has_no_dash_characters(self):
        text = open(self.BRIEF, encoding="utf-8").read()
        assert chr(0x2013) not in text and chr(0x2014) not in text


class TestValidation:
    def test_valid_post_builds(self):
        a = build_article(make_post(), "ok.md")
        assert a.path == "/2026/test-post"
        assert a.url == articles.SITE_URL + "/2026/test-post"
        assert a.sources == [{"label": "Example", "url": "https://example.com/a"}]

    @pytest.mark.parametrize("overrides, message", [
        ({"status": "live"}, "status must be one of"),
        ({"slug": "Bad Slug"}, "slug must be"),
        ({"season": "26"}, "season must be"),
        ({"published": "October 28"}, "published must be YYYY-MM-DD"),
        ({"published": "20261028"}, "published must be YYYY-MM-DD"),
        ({"published": "2026-02-30"}, "not a real date"),
        ({"updated": "2026-10-01"}, "is before published"),
        ({"title": "x" * 61}, "title tag is 61 characters"),
        ({"meta_description": "x" * 161}, "meta_description is 161"),
        ({"udpated": "2026-10-29"}, "unknown front matter key 'udpated'"),
        ({"source": " | https://example.com/a"}, "source must be"),
        ({"source": "Example \\| https://example.com/a", "body": "x"}, None),
        ({"body": "Read [this](www.espn.com/x)."}, "not allowed in posts: www.espn.com/x"),
        ({"body": "![logo](https://example.com/a.png)"}, "not allowed in posts: image https://example.com/a.png"),
    ])
    def test_bad_post_raises(self, overrides, message):
        if message is None:
            # A copied markdown-table escape lands in the label, which is allowed text
            build_article(make_post(**overrides), "ok.md")
            return
        with pytest.raises(ArticleError, match=re.escape(message)):
            build_article(make_post(**overrides), "bad.md")

    def test_missing_field_raises(self):
        text = make_post().replace("target_phrase: test phrase\n", "")
        with pytest.raises(ArticleError, match="missing front matter: target_phrase"):
            build_article(text, "bad.md")

    def test_body_must_start_with_the_title(self):
        text = make_post().replace("# Test Post", "## Test Post")
        with pytest.raises(ArticleError, match="body must start with '# Test Post'"):
            build_article(text, "bad.md")

    def test_dashes_inside_a_source_url_do_not_end_the_front_matter(self):
        a = build_article(make_post(source="Example | https://example.com/a---b"), "ok.md")
        assert a.sources[0]["url"] == "https://example.com/a---b"

    def test_long_title_is_fine_with_short_title_tag(self):
        a = build_article(make_post(title="x" * 80, title_tag="Short tag"), "ok.md")
        assert a.title_tag == "Short tag"

    def test_en_dash_is_rejected(self):
        with pytest.raises(ArticleError, match="dash character"):
            build_article(make_post(title=f"Score 2{EN_DASH}1"), "dash.md")

    @pytest.mark.parametrize("snippet", [
        "&mdash;", "&ndash;", "&#8212;", "&#x2013;", "&horbar;", "&minus;",
        chr(0x2012), chr(0x2015), chr(0x2212), chr(0x2E3A), chr(0x2E3B), chr(0xFE58),
        # Markdown turns the escaped "&\#8212;" into "&#8212;" only when rendering,
        # so only the check on the rendered body catches this one
        "&\\#8212;",
    ])
    def test_dash_entities_and_look_alikes_are_rejected(self, snippet):
        """They render as a dash on the page, so they break the same rule."""
        with pytest.raises(ArticleError, match="dash character"):
            build_article(make_post(body=f"Columbus {snippet} St. Louis"), "dash.md")

    def test_dash_entity_in_title_is_rejected(self):
        with pytest.raises(ArticleError, match="dash character"):
            build_article(make_post(title="Final &mdash; recap"), "dash.md")

    def test_plain_hyphens_are_fine(self):
        build_article(make_post(body="Won 2-1 on April 13-14 at the semi-final."), "ok.md")

    def test_source_is_required(self):
        with pytest.raises(ArticleError, match="at least one 'source"):
            build_article(make_post(source=None), "nosource.md")

    def test_duplicate_url_is_rejected(self, tmp_path):
        (tmp_path / "a.md").write_text(make_post())
        (tmp_path / "b.md").write_text(make_post())
        with pytest.raises(ArticleError, match="already used"):
            load_articles(str(tmp_path))


class TestRenderingIsSafe:
    def test_raw_html_is_escaped(self):
        html, rejected = render_markdown("Hello <script>alert(1)</script>\n\n<div onclick=x>hi</div>")
        assert "<script>" not in html
        assert "<div" not in html
        assert "&lt;script&gt;" in html
        assert rejected == []

    def test_javascript_links_lose_their_href_and_are_reported(self):
        html, rejected = render_markdown("[click](javascript:alert(1)) and [ok](/news) and [ext](https://ussoccer.com)")
        assert "javascript:" not in html
        assert 'href="/news"' in html
        assert 'href="https://ussoccer.com"' in html
        assert rejected == ["javascript:alert(1)"]

    def test_javascript_link_in_a_post_is_refused(self):
        with pytest.raises(ArticleError, match="not allowed in posts: javascript:alert"):
            build_article(make_post(body="[x](javascript:alert(1))"), "bad.md")

    def test_tables_render(self):
        assert "<table>" in render_markdown("| a | b |\n|---|---|\n| 1 | 2 |")[0]


@pytest.fixture
def client(tmp_path):
    """The articles blueprint on an app shaped like production: static files
    served from the root URL, so route precedence matches app.py."""
    static = tmp_path / "dist"
    (static / "assets").mkdir(parents=True)
    (static / "assets" / "app.js").write_text("console.log(1)")
    from backend.article_routes import bp
    app = Flask(__name__, static_folder=str(static), static_url_path="")
    app.register_blueprint(bp)
    return app.test_client()


class TestRoutes:
    def test_article_page(self, client):
        r = client.get("/2026/final")
        body = r.get_data(as_text=True)
        assert r.status_code == 200
        assert "<title>St. Louis CITY SC Win the 2026 U.S. Open Cup on Penalties</title>" in body
        assert '<link rel="canonical" href="https://usopencup.welchproductsllc.com/2026/final">' in body
        assert '"@type": "Article"' in body
        assert "5-3 in a penalty shootout" in body

    def test_unknown_article_is_404(self, client):
        assert client.get("/2026/not-a-post").status_code == 404

    def test_padded_year_is_404(self, client):
        assert client.get("/02026/final").status_code == 404

    def test_static_assets_still_served(self, client):
        assert client.get("/assets/app.js").status_code == 200

    def test_news_index_lists_published_posts(self, client):
        body = client.get("/news").get_data(as_text=True)
        for path in ("/2026/final", "/2026/cupsets", "/2027/format-and-schedule", "/2027/draw"):
            assert f'href="{path}"' in body

    def test_api_articles(self, client):
        data = client.get("/api/articles").get_json()
        assert {d["path"] for d in data} >= {"/2026/final", "/2027/draw"}
        assert all(set(d) == {"title", "path", "season", "published", "description"} for d in data)

    def test_robots_and_sitemap(self, client):
        robots = client.get("/robots.txt")
        assert robots.mimetype == "text/plain"
        assert "Sitemap: https://usopencup.welchproductsllc.com/sitemap.xml" in robots.get_data(as_text=True)
        sitemap = client.get("/sitemap.xml").get_data(as_text=True)
        assert "<loc>https://usopencup.welchproductsllc.com/</loc>" in sitemap
        assert "<loc>https://usopencup.welchproductsllc.com/2026/final</loc>" in sitemap

    def test_draft_is_not_served(self, client, monkeypatch):
        from backend import article_routes
        draft = build_article(make_post(slug="secret", status="draft"), "draft.md")
        monkeypatch.setattr(article_routes, "ARTICLES", article_routes.ARTICLES + [draft])
        assert client.get("/2026/secret").status_code == 404
        assert "/2026/secret" not in client.get("/sitemap.xml").get_data(as_text=True)
        assert "/2026/secret" not in client.get("/news").get_data(as_text=True)
