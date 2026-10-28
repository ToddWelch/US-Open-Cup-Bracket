"""Articles: load, validate and render the Markdown posts in content/posts.

Each post is a Markdown file with a front matter block of "key: value" lines
between two "---" lines. Posts are loaded and validated once at startup; an
invalid post raises, so a bad file fails the deploy's health check instead of
quietly disappearing from the site.
"""

import html
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
OPTIONAL_FIELDS = ("title_tag", "updated")
STATUSES = ("draft", "published")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TITLE_TAG_MAX = 60
META_DESCRIPTION_MAX = 160
# En and em dashes are banned from public copy, along with the characters
# that render the same: figure dash, horizontal bar and minus sign. Written
# as code points so this source file holds no dash characters itself.
BANNED_CHARS = (chr(0x2012), chr(0x2013), chr(0x2014), chr(0x2015), chr(0x2212))
SAFE_LINK = re.compile(r"^(https?://|/|#|mailto:)", re.IGNORECASE)
# Site links: relative ("/2026/final") or absolute to this site
SITE_LINK = re.compile(r'href="(?:' + re.escape(SITE_URL) + r')?(/[^"#?]*)')
# Pages outside the articles that posts may link to
SITE_PAGES = {"/", "/news"}


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
    """Drop images and any href that is not http(s), site-relative, an anchor
    or mailto, recording each one in md.rejected so the caller can refuse it."""

    def run(self, root: Element):
        for parent in list(root.iter()):
            for el in list(parent):
                if el.tag == "img":
                    self.md.rejected.append(f"image {el.get('src', '')}")
                    parent.remove(el)
        for el in root.iter():
            value = el.get("href")
            if value is not None and not SAFE_LINK.match(value.strip()):
                self.md.rejected.append(value)
                del el.attrib["href"]


class _NoRawHtml(Extension):
    """Treat raw HTML in posts as text, and keep only safe link targets."""

    def extendMarkdown(self, md):
        md.preprocessors.deregister("html_block")
        md.inlinePatterns.deregister("html")
        md.treeprocessors.register(_SafeLinks(md), "safe_links", 0)


def render_markdown(text):
    """Render post Markdown. Returns (html, rejected): rejected lists the
    images and link targets that were removed from the output."""
    md = markdown.Markdown(extensions=["tables", _NoRawHtml()])
    md.rejected = []
    html = md.convert(text)
    return html, md.rejected


def parse_front_matter(text, filename):
    """Split a post into (fields, body). "source" may repeat; other keys may not."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ArticleError(f"{filename}: must start with a --- line opening the front matter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ArticleError(f"{filename}: front matter has no closing --- line")

    fields, sources = {}, []
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ArticleError(f"{filename}: front matter line is not 'key: value': {line!r}")
        key, value = (s.strip() for s in line.split(":", 1))
        if key == "source":
            label, sep, link = value.rpartition("|")
            label = label.strip()
            if not sep or not label or not link.strip().startswith("https://"):
                raise ArticleError(f"{filename}: source must be 'Label | https://...': {value!r}")
            sources.append({"label": label, "url": link.strip()})
        elif key not in REQUIRED_FIELDS + OPTIONAL_FIELDS:
            raise ArticleError(f"{filename}: unknown front matter key {key!r}")
        elif key in fields:
            raise ArticleError(f"{filename}: duplicate front matter key {key!r}")
        else:
            fields[key] = value
    fields["sources"] = sources
    return fields, "\n".join(lines[end + 1:])


def _check_no_dashes(text, filename):
    for ch in BANNED_CHARS:
        if ch in text:
            raise ArticleError(f"{filename}: contains a dash character (U+{ord(ch):04X}) or an entity for one; use a comma, colon or new sentence")


def _parse_date(value, name, filename):
    if not DATE_RE.match(value):
        raise ArticleError(f"{filename}: {name} must be YYYY-MM-DD, got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ArticleError(f"{filename}: {name} is not a real date: {value!r}") from e


def build_article(text, filename):
    """Validate one post file and return an Article. Raises ArticleError."""
    # Unescaped so an entity in the title or body (&ndash;, &#x2014;) counts too
    _check_no_dashes(html.unescape(text), filename)
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
    published = _parse_date(fields["published"], "published", filename)
    updated = _parse_date(fields["updated"], "updated", filename) if fields.get("updated") else None
    if updated and updated < published:
        raise ArticleError(f"{filename}: updated ({updated}) is before published ({published})")

    first_line = next((line for line in body.splitlines() if line.strip()), "")
    if first_line.strip() != f"# {fields['title']}":
        raise ArticleError(f"{filename}: body must start with '# {fields['title']}'")

    body_html, rejected = render_markdown(body)
    if rejected:
        raise ArticleError(f"{filename}: not allowed in posts: {', '.join(rejected)}; links must start with https://, / or #, and posts have no images")
    # Entities such as &mdash; or &#8212; only become dashes once rendered
    _check_no_dashes(html.unescape(body_html), filename)

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
        body_html=body_html,
        sources=fields["sources"],
        filename=filename,
    )


def check_site_links(articles):
    """Every site-relative link in a post must reach a real page. Published
    posts may link only to published posts; drafts may also link to drafts."""
    published = SITE_PAGES | {a.path for a in articles if a.is_published}
    everything = published | {a.path for a in articles}
    for a in articles:
        allowed = published if a.is_published else everything
        for href in SITE_LINK.findall(a.body_html):
            if href not in allowed:
                raise ArticleError(f"{a.filename}: links to {href}, which is not a published page")


def load_articles(posts_dir=POSTS_DIR):
    """Load every .md post, newest first. Raises ArticleError on any bad post,
    duplicate URL or broken site link."""
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

    check_site_links(articles)
    articles.sort(key=lambda a: (a.published, a.slug), reverse=True)
    return articles
