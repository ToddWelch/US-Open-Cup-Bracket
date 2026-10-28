# Session Log

Newest first. Entries are never deleted.

---

## 2026-10-28 (evening): Articles live, main protected, content hardening

**Scope:** Todd's approvals: deploy PR #3, protect `main`, open a hardening PR. Build class EXTERNAL.
**Branch:** `fix/content-hardening` (PR #4). Not merged: its deploy needs Todd's approval.

### Done
- PR #3: Crash Override approved with notes on `ea52eaa`; notes fixed in `2e1d595` (rejected links and images raise, broken site links fail the load, stricter front matter and dates, four-digit year route, CI workflow); re-review approved `2e1d595`. Cross-model gate (fresh-eyes Sonnet) cleared with three MINOR findings (findings: `scratch/fresh-eyes-review-articles-and-seo-2026-10-28.md`; catch logged in `~/.claude/logs/gate-catches.md`). CI green on Python 3.11. Merged `4235420` with Todd's approval; Railway deployed it at 23:43 UTC.
- Live check: `/news`, all four articles, `/robots.txt`, `/sitemap.xml`, `/api/articles`, favicon and share image return 200; unknown slug 404; headless smoke on production clean (no console errors, no broken images, article pages fit at 400px, click-through works). The real-Chrome extension timed out on the article pages, so that check is headless only.
- Slack alerts: zero since the fix deployed (scrapes at 18:00, 20:00 and 22:00 UTC all used ESPN's 79 matches).
- Branch protection on `main` (Todd approved): PR required, `backend` check required and up to date, admins included, no force pushes or deletions, 0 required approvals (independent review stays with Crash Override).
- PR #4: dash look-alikes and dash entities (`&mdash;`, `&#8212;`, U+2012, U+2015, U+2212) rejected in posts and caught by the CI scan; FAQPage JSON-LD removed (not visible on the page); the Slack failure log prints only the exception type (the old handler logged the webhook URL, shown by a test against main); absolute links to this site get the broken-link check. 85 tests pass; the new ones fail on main.

### Next
1. Crash Override review of PR #4, CI, then Todd's deploy approval.
2. Todd: submit `https://usopencup.welchproductsllc.com/sitemap.xml` in Google Search Console.
3. Hand `docs/grok-content-brief.md` to the Grok agent; its drafts come back as PRs or files for Todd's review.
4. Early January 2027: rollover build (`docs/2027-rollover-plan.md`).

### Housekeeping
- `frontend/public/` is now tracked (favicon, share image). The untracked `frontend/public/index.html` in the main checkout is harmless: tested, Vite's built `index.html` takes precedence over it. It's a stale copy and can be deleted locally.

---

## 2026-10-28 (later): Fix deployed; articles, on-page SEO and writer brief

**Scope:** Todd's answers on the review page. Build class EXTERNAL.
**Branch:** `feat/articles-and-seo` (PR #3). Not merged: the deploy needs Todd's explicit approval, and the cross-model gate fires (first content real people read).

### Todd's decisions (2026-10-28)
- Deploy the 2026 fix: yes. Archive at `/2026`: yes. Rollover build: **January 2027**. ussoccer.com scraper: remove (in the rollover). Posts: on this site, in his writing standards. On-page fixes: follow-up PR. All four drafts approved.

### Done
- PR #2 merged (`8b7896f`, merge commit pinned to reviewed head `6d8c627`). Railway deploy `2b715c80` built, passed its healthcheck at 17:22 UTC and went live at 17:28 UTC after a slow switch (Railway lists a degraded-performance recovery incident).
- Live check: `/api/bracket` shows source ESPN, status ok, 79 matches, Final Columbus Crew 0-0 St. Louis CITY SC, winner St. Louis, PEN, October 21. Real Chrome and headless smoke: FINAL DONE 1/1, 12 cupsets, no console errors, 0 of 79 cells highlight the lower score. The new container's startup scrape sent no Slack alert (only ussoccer.com failed; it now gets HTTP 403 from Railway).
- Found: the 2026-08-06 deploy (`5b04d6f`) failed its healthcheck, so production ran the 2026-07-29 build until today.
- PR #3: server-rendered articles (`backend/articles.py`, `backend/article_routes.py`, Jinja templates), the four approved posts in `backend/content/posts/` with a voice pass (contractions, no Oxford comma), `/news`, `/api/articles`, `/robots.txt`, `/sitemap.xml`, favicon, 1200x630 share image, index.html meta and JSON-LD rewrite, bracket-page copy and news list, footer credit. Raw HTML in posts is escaped and unsafe link schemes are dropped. New dependency: `markdown==3.10` (free, pure Python, no network; 3.11.2 was under two weeks old).
- `docs/grok-content-brief.md`: brief for an AI writer to find U.S. Open Cup news and write draft posts in the site's format. A test parses its example post through the real validator.
- Tests: 58 offline pass, 2 live skipped by default.

### Next
1. Crash Override review of PR #3, then the cross-model fresh-eyes gate, then Todd's deploy approval.
2. After deploy: smoke `/news`, each article, `/sitemap.xml`; submit the sitemap in Google Search Console (Todd's account).
3. Early January 2027: rollover build (`docs/2027-rollover-plan.md`).

---

## 2026-10-28: Revive check, 2026 final-state fix, 2027 plan, SEO drafts

**Scope:** handoff `Welch-Advisory-Team/scratch/handoff-us-open-cup-bracket-revive-2026-10-28.md`. Build class EXTERNAL (public site).
**Branch:** `fix/2026-final-results`. Not merged, not deployed: deploys need Todd's explicit approval in session.

### Found (production, checked 2026-10-28)
- The 2026 tournament is over. Final October 21, 2026: Columbus Crew 0-0 St. Louis CITY SC after extra time, St. Louis won 5-3 on penalties (ESPN, Wikipedia and ussoccer.com agree).
- The live site showed the wrong final state: losers highlighted as winners in most matches, a semifinal (Columbus 2-1 Orlando) in the Final box, "St. Louis 16, Colorado 9 PEN" in the other semifinal, "0 CUPSETS", "R1 DONE", STALE status, and bracket lines joining matches that never fed each other.
- Causes: (1) ESPN's scoreboard API returns HTTP 400 for date-range queries, so ESPN produced nothing all season after some point; (2) the 2026 Wikipedia article bolds the losing team and the parser read bold as the winner; (3) Wikipedia section matching was by substring, so "Semifinals" filled the Final slot; (4) `build_bracket` reordered R32 twice, undoing the R16 alignment; (5) the "never overwrite with fewer matches" guard then kept the corrupted 79-match file because the newer Wikipedia scrape, itself wrong, had 78. Last good update was 2026-09-17.
- Railway: active deploy 2026-07-29 (`9e09bc6`), no volume, `SLACK_WEBHOOK_URL` set. A Slack alert has fired every 2 hours since ESPN broke (33 in the last ~3 days of logs).
- ussoccer.com scraper finds nothing (page is client-rendered JSON now). Wikipedia returned HTTP 429 during repeated checks.
- On-page SEO: no robots.txt, sitemap.xml or favicon (all 404); copy still says "Live" and stops at First Round highlights; no og:image.

### Done
- `d9834b4` ESPN season query by year with round from `season.slug`, Eastern Time dates; Wikipedia winners from score and shootout (bold ignored), exact section headings, empty fields no longer read the next line; `build_bracket` aligns rounds working back from the Final; progress card shows FINAL DONE.
- `ed28743` tier badge fixes: AV Alta FC (USL1), Laredo Heat SC and Little Rock Rangers (USL2). Cupsets now 12.
- Crash Override: APPROVED WITH NOTES on `e47dd22`, no blocking findings. Follow-up commit addresses the notes: matches carry a round tag and `build_bracket` groups on it (one missing event can no longer shift later rounds), live tests skip unless `LIVE_SOURCES=1`, `getTier` is case-insensitive (fixes Wikipedia's "St. Louis City SC" showing AM), null-safe ESPN `season`, only the exception type is stored in the public `sourceResults`, an error-propagation test, and doc corrections (32 pros in the 2026 First Round, not 48; six amateur First Round cupsets).
- South Georgia Tormenta FC withdrew on 2026-02-23; FC America CFL Spurs advanced by walkover, which ESPN records as 1-0. Tormenta stays out of the tier lists so the walkover is not counted as a cupset.
- Tests: 33 total (31 offline, 2 live read-only checks against ESPN and Wikipedia, run with `LIVE_SOURCES=1`). New tests fail on the old code and pass on the fix.
- Local verification: app on 127.0.0.1:8765 built 79 matches from ESPN; headless Chromium smoke (the Chrome extension could not reach the box) shows FINAL DONE, 12 cupsets, ESPN OK, Final with St. Louis highlighted on PEN, no console errors, every connector traced correct from Round 1 to the Final.
- `docs/2027-rollover-plan.md`: dated 2027 timeline, code and data changes, archive recommendation.
- `docs/seo/`: four post drafts (2026 Final, 2026 cupsets, 2027 format and schedule, 2027 draw) and the on-page fix list with replacement copy. Nothing published.

### State
- Crash Override review requested on the branch; verdict recorded in the PR.
- Production unchanged and still wrong until the PR is merged and Railway redeploys. A deploy rebuilds `bracket.json` from a fresh scrape at startup, which the fix makes correct (ESPN 79 matches).

### Next
1. Todd approves (or not) merging the PR, which auto-deploys on Railway. After deploy: check `/api/bracket` shows source ESPN, status ok, Final winner St. Louis CITY SC, and that Slack alerts stop.
2. Todd's calls on the 2027 plan and the SEO drafts (review page).
3. December 2026: build the rollover if approved. Late January to February 2027: load 2027 First Round pairings.

### Open decisions
- Deploy approval for this PR.
- Archive URL (`/2026` recommended), rollover build window (December recommended), remove the ussoccer.com scraper (recommended).
- Where the posts are published, and which drafts to keep.

### Housekeeping
- This file was untracked in the main checkout and is committed here for the first time. After merge, the untracked copy in `/home/todd/projects/US-Open-Bracket` blocks `git pull` until it is removed; its content is preserved below.
- `AGENTS.md`, `CODEX_REVIEW.md`, `frontend/public/index.html` and `samples/` are also untracked in the main checkout; left untouched. `frontend/public/index.html` would collide with the root `index.html` Vite builds from if it were ever committed; check before adding it.

### Estimate vs actual
No estimate was set at the start. Actual: about 2.5 hours of agent session time.

---

## 2026-04-16: Codex Review Remediation

**Scope:** Full remediation of two Codex reviews (original 13 items + fresh 6 items + 1 bug fix)

### Original Codex Review (13 findings, 3 phases)

#### Phase 1: Fix Live Correctness and Security
- **Fix 1 (CRITICAL):** Penalty/shootout winner parsing from ESPN
- **Fix 2 (HIGH):** Secured admin endpoints with ADMIN_KEY + POST-only
- **Fix 3 (HIGH):** Atomic bracket.json writes
- **Fix 4 (LOW):** Environment-based debug mode

#### Phase 2: Restore Scraper Resilience
- **Fix 5 (MEDIUM):** Rebuilt US Soccer parser with regex scoreline parsing
- **Fix 6 (MEDIUM):** Best-source selection by match count

#### Phase 3: Tighten Operations
- **Fix 7-11:** Game-day detection, Final box wiring, adaptive polling, non-root Docker, dependency upgrades

#### Post-deploy fix
- Removed stale `bracket.json` from git tracking (was shipping 3/25 data with every deploy)

### Fresh Codex Review V2 (6 findings + 1 bug)

#### Bug Fix: R2->R32 bracket ordering
- Added `_reorder_1to1_round()` for the MLS entry round (1:1 mapping)
- Fixed ordering: must run AFTER R1->R2 reorder so R2 is in final position
- Verified: 16/16 R32 matches align to R2 feeder winners

#### V2 Phase 1: Backup Path Correctness
- Wikipedia parser now detects penalty winners from bold (`'''`) markup
- ussoccer.com downgraded from "fallback" to "best-effort supplemental" in docs and UI
- 7 new Wikipedia parser tests (20 total backend tests)

#### V2 Phase 2: Polling Accuracy
- `has_games_today()` now gates ROUND_META fallback behind gameTime availability
- Frontend polling uses fresh fetch data instead of stale ref (eliminated race condition)

#### V2 Phase 3: Cleanup
- Package-safe try/except imports for backend modules
- Dynamic round-aware UI: header and footer adapt to current tournament stage

### Current State

- **All merged to main** and pushed (`1cf87cb`)
- 20 backend tests pass
- Frontend build succeeds (vite 6.4.2)
- `ADMIN_KEY` set in Railway

### Remaining Backlog

- Add unit tests for `has_games_today()`
- Consider displaying penalty shootout scores in UI (homePen/awayPen data captured)
- Smoke test that exercises the app end-to-end with bracket.json
