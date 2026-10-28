"""Articles: load, validate and render the Markdown posts in content/posts.

Each post is a Markdown file with a front matter block of "key: value" lines
between two "---" lines. Posts are loaded and validated once at startup; an
invalid post raises, so a bad file fails the deploy's health check instead of
quietly disappearing from the site.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import date
from xml.etree.ElementTree import Element

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

SITE_URL = "https://usopencup.welchproductsllc.com"
POSTS_DIR = os.path.join(os.path.dirname(__file__), "content", "posts")

REQUIRED_FIELDS = ("title", "meta_description", "target_phrase", "season", "slug", "published", "status")
STATUSES = ("draft", "published")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TITLE_TAG_MAX = 60
META_DESCRIPTION_MAX = 160
# En and em dashes are banned from public copy; written as code points so
# this source file holds no dash characters itself
BANNED_CHARS = (chr(0x2013), chr(0x2014))
SAFE_LINK = re.compile(r"^(https?://|/|#|mailto:)", re.IGNORECASE)


class ArticleError(ValueError):
    """A post file is missing a field or breaks a content rule."""


@dataclass
class Article:
    title: str
    title_tag: str
    meta_description: str
    target_phrase: str
    season: int
    slug: str
    published: date
    status: str
    body_html: str
    sources: list = field(default_factory=list)
    updated: date | None = None
    filename: str = ""

    @property
    def path(self):
        return f"/{self.season}/{self.slug}"

    @property
    def url(self):
        return SITE_URL + self.path

    @property
    def is_published(self):
        return self.status == "published"


class _SafeLinks(Treeprocessor):
    """Drop href/src values that are not http(s), site-relative, anchors or mailto."""

    def run(self, root: Element):
        for el in root.iter():
            for attr in ("href", "src"):
                value = el.get(attr)
                if value is not None and not SAFE_LINK.match(value.strip()):
                    del el.attrib[attr]


class _NoRawHtml(Extension):
    """Treat raw HTML in posts as text, and keep only safe link targets."""

    def extendMarkdown(self, md):
        md.preprocessors.deregister("html_block")
        md.inlinePatterns.deregister("html")
        md.treeprocessors.register(_SafeLinks(md), "safe_links", 0)


def render_markdown(text):
    return markdown.markdown(text, extensions=["tables", _NoRawHtml()])


def parse_front_matter(text, filename):
    """Split a post into (fields, body). "source" may repeat; other keys may not."""
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ArticleError(f"{filename}: must start with a front matter block between --- lines")
    fields, sources = {}, []
    for line in parts[1].strip().splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ArticleError(f"{filename}: front matter line is not 'key: value': {line!r}")
        key, value = (s.strip() for s in line.split(":", 1))
        if key == "source":
            label, sep, link = value.rpartition("|")
            if not sep or not link.strip().startswith("https://"):
                raise ArticleError(f"{filename}: source must be 'Label | https://...': {value!r}")
            sources.append({"label": label.strip(), "url": link.strip()})
        elif key in fields:
            raise ArticleError(f"{filename}: duplicate front matter key {key!r}")
        else:
            fields[key] = value
    fields["sources"] = sources
    return fields, parts[2]


def build_article(text, filename):
    """Validate one post file and return an Article. Raises ArticleError."""
    for ch in BANNED_CHARS:
        if ch in text:
            raise ArticleError(f"{filename}: contains an en or em dash (U+{ord(ch):04X}); use a comma, colon or new sentence")
    fields, body = parse_front_matter(text, filename)

    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if missing:
        raise ArticleError(f"{filename}: missing front matter: {', '.join(missing)}")
    if fields["status"] not in STATUSES:
        raise ArticleError(f"{filename}: status must be one of {STATUSES}, got {fields['status']!r}")
    if not SLUG_RE.match(fields["slug"]):
        raise ArticleError(f"{filename}: slug must be lowercase words joined by hyphens, got {fields['slug']!r}")
    if not re.fullmatch(r"20\d\d", fields["season"]):
        raise ArticleError(f"{filename}: season must be a four-digit year, got {fields['season']!r}")
    title_tag = fields.get("title_tag") or fields["title"]
    if len(title_tag) > TITLE_TAG_MAX:
        raise ArticleError(f"{filename}: title tag is {len(title_tag)} characters; add a title_tag of {TITLE_TAG_MAX} or fewer")
    if len(fields["meta_description"]) > META_DESCRIPTION_MAX:
        raise ArticleError(f"{filename}: meta_description is {len(fields['meta_description'])} characters; keep it to {META_DESCRIPTION_MAX}")
    if not fields["sources"]:
        raise ArticleError(f"{filename}: needs at least one 'source: Label | https://...' line")
    try:
        published = date.fromisoformat(fields["published"])
        updated = date.fromisoformat(fields["updated"]) if fields.get("updated") else None
    except ValueError as e:
        raise ArticleError(f"{filename}: dates must be YYYY-MM-DD: {e}") from e

    return Article(
        title=fields["title"],
        title_tag=title_tag,
        meta_description=fields["meta_description"],
        target_phrase=fields["target_phrase"],
        season=int(fields["season"]),
        slug=fields["slug"],
        published=published,
        updated=updated,
        status=fields["status"],
        body_html=render_markdown(body),
        sources=fields["sources"],
        filename=filename,
    )


def load_articles(posts_dir=POSTS_DIR):
    """Load every .md post, newest first. Raises ArticleError on any bad post or duplicate URL."""
    articles = []
    for name in sorted(os.listdir(posts_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(posts_dir, name), encoding="utf-8") as f:
            articles.append(build_article(f.read(), name))

    seen = {}
    for a in articles:
        if a.path in seen:
            raise ArticleError(f"{a.filename}: URL {a.path} already used by {seen[a.path]}")
        seen[a.path] = a.filename

    articles.sort(key=lambda a: (a.published, a.slug), reverse=True)
    return articles
