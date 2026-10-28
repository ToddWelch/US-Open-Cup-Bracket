# SEO: articles and on-page fixes

Updated 2026-10-28.

## Articles

Posts live in `backend/content/posts/` as Markdown with front matter and are served at `/<season>/<slug>`, listed at `/news` and in `/sitemap.xml`. Only `status: published` posts are served. The loader validates every post at startup (`backend/articles.py`), so a bad post stops a deploy instead of breaking a page.

| Path | Title | Target phrase | Status |
|---|---|---|---|
| `/2026/final` | St. Louis CITY SC Win the 2026 U.S. Open Cup on Penalties | 2026 U.S. Open Cup final | published (approved by Todd 2026-10-28) |
| `/2026/cupsets` | Every Cupset of the 2026 U.S. Open Cup | 2026 U.S. Open Cup upsets | published (approved 2026-10-28) |
| `/2027/format-and-schedule` | 2027 U.S. Open Cup Format and Schedule: 96 Teams, Final on December 15 | 2027 U.S. Open Cup schedule | published (approved 2026-10-28) |
| `/2027/draw` | When Is the 2027 U.S. Open Cup Draw? What to Know Before the First Round | 2027 U.S. Open Cup draw | published (approved 2026-10-28) |

Target phrases are judgment calls from how people phrase these searches. No keyword-volume data was pulled, because that needs a paid tool (Ahrefs, Semrush or similar), which would need Todd's OK first.

New posts: `docs/grok-content-brief.md` is the brief for an AI writer. It writes drafts in the same format; Todd reviews each one, sets `status: published`, and it ships through a PR like any other change.

Posts 3 and 4 depend on U.S. Soccer dates that are "subject to change." Re-check them when U.S. Soccer announces the First Round pairings.

## On-page fixes (shipped in PR #3)

| # | Issue found 2026-10-28 | Fix |
|---|---|---|
| 1 | `<title>` said "Live Tournament Bracket & Scores" | `2026 U.S. Open Cup Bracket and Results` |
| 2 | Meta description said "Live ... real-time scores" | Result-led description |
| 3 | `og:`/`twitter:` titles said "Live Scores"; no `og:image` | New titles; 1200x630 `og-image.png` |
| 4 | JSON-LD FAQ in the future tense, team counts off | Rewritten in PR #3, then removed in PR #4: Google requires marked-up content to be visible on the page (this FAQ wasn't), and shows FAQ rich results only for government and health sites since 2023 |
| 5 | Article block stopped at "First Round Highlights" | Champion summary, format, cupsets, and a news list from `/api/articles` |
| 6 | Copy and footer credited ussoccer.com | "Results come from ESPN, with Wikipedia as a backup" |
| 7 | `robots.txt` returned 404 | Served by Flask, points to the sitemap |
| 8 | `sitemap.xml` returned 404 | Lists `/`, `/news` and every published post |
| 9 | `favicon.ico` returned 404 | `favicon.svg` linked from every page |
| 10 | Bracket page content is client-rendered | Articles are server-rendered HTML; the bracket page's `noscript` block carries the result and links to the articles |

Not done: the bracket page overflows horizontally at phone width (pre-existing; part of the 2027 layout work).
