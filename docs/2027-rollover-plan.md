# 2027 rollover plan

Written 2026-10-28. Recommendation only: nothing here is built until Todd approves it.

## Recommendation in one paragraph

Keep the 2026 bracket up permanently at `/2026` as a frozen archive, and put the 2027 bracket on the root URL as soon as U.S. Soccer publishes the 2027 First Round pairings (expected late January or February 2027). Build the season-config and archive work in early January 2027 (Todd's call, 2026-10-28), so the pairings announcement is a data load, not a rebuild. The 2027 tournament is a different shape (96 teams, a Round of 64, a December Final), so the rollover is real code work, not a find-and-replace of "2026".

## What is known about 2027 (sources at the bottom)

| Item | 2027 | 2026 for comparison |
|---|---|---|
| Edition | 112th | 111th |
| Teams | 96 | 80 |
| First Round | April 13-14 and April 20-21, 2027: 32 Division II/III pro teams plus 32 Open Division amateurs | March 17-19: 32 pros (USL Championship, USL League One, MLS NEXT Pro) plus 32 amateurs |
| Entry round | Round of 64, July 8-11, 2027: 32 First Round winners plus all 27 U.S.-based MLS clubs plus 5 seeded USL Championship clubs | Round of 32, April 14-15: 16 Second Round winners plus 16 MLS clubs |
| Round of 32 | Sept. 14-15, 2027 | April 14-15 |
| Round of 16 | TBC | April 28-29 |
| Quarterfinals | Nov. 23-24, 2027 | May 19-20 |
| Semifinals | Dec. 1, 2027 | Sept. 15-16 |
| Final | Dec. 15, 2027 | Oct. 21 |
| Purse | $1 million | $1 million |
| First Round pairings | "early 2027", each First Round tie geographically paired with a Round of 64 entrant | announced Jan. 27, 2026 |
| Later draws | one live draw after the Round of 64 sets the Round of 32 and Round of 16 | live draw for the Round of 32 on April 2, 2026 |

All 2027 dates are U.S. Soccer's and "subject to change." The amateur field comes from the fall 2026 Qualifying Rounds (16 slots) plus 16 byes earned in 2026 competitions. MLS NEXT Pro entrants: Carolina Core FC, Chattanooga FC and Connecticut United FC. Seeded USL Championship entrants: Players' Shield winner, playoff champion, top seed in each conference, and the USL Cup champion.

## Dated timeline

| When | What | Site state |
|---|---|---|
| Now (late Oct 2026) | Ship the 2026 correctness fix (PR `fix/2026-final-results`), needs Todd's deploy approval | 2026 complete, correct, on root |
| Oct 28, 2026 | On-page SEO fixes and the first four articles (PR #3) | same, plus `/news` |
| Early Jan 2027 | Build season config, `/2026` archive, 2027 bracket shape, scheduler and alert changes, remove the ussoccer.com scraper | same; 2027 code behind config |
| Late Jan to Feb 2027 | U.S. Soccer publishes First Round pairings | load 2027 data; root becomes 2027; 2026 moves to `/2026` |
| Before April 13, 2027 | Confirm ESPN has 2027 events and record their round slugs | live check |
| April 13-14, 20-21 | First Round | live scoring |
| July 8-11 | Round of 64 (Thursday to Sunday, so weekend afternoon games) | live scoring; fast-poll window must cover afternoons |
| After the Round of 64 | Live draw for Round of 32 and Round of 16 | bracket tree beyond the Round of 64 fills in |
| Sept. 14-15, Nov. 23-24, Dec. 1, Dec. 15 | Round of 32, Quarterfinals, Semifinals, Final | live scoring |
| After Dec. 15, 2027 | Freeze 2027 to `/2027` the same way | archive |

## What has to change in code and data

1. **Season config instead of hard-coded 2026 values.** Today 2026 is written into `backend/scraper.py` (`SEASON_YEAR`, `ROUND_META` names, schedules, date windows and ESPN slugs, `WIKI_PAGE`, the round sizes in `build_bracket`) and into `frontend/src/App.jsx` (`RNAMES`, `ROUND_SIZES`, the header "111TH EDITION . 80 TEAMS . 7 ROUNDS . $1M PURSE", "FINAL . OCT 21", the "R2 Winner" and "MLS Team" placeholders, the `nextRoundIdx === 6` "Oct 21" footer, and the article copy). Move all of it into one per-season JSON file that the API serves and both halves read.
2. **New bracket shape.** 2027 rounds are 32, 32, 16, 8, 4, 2, 1 matches (95 total). The 1:1 entry round moves from Second Round to Round of 32 (2026) to First Round to Round of 64 (2027), and there is no Second Round. `build_bracket` and the frontend layout take the round sizes and the entry-round position from config.
3. **Round tags, not positions.** The 2026 fix already tags each ESPN and Wikipedia match with its round and groups on the tag, so a missing match cannot shift later rounds. For 2027, take the round sizes from config and record the 2027 ESPN slugs (expected `first-round`, `round-of-64`, ...) when ESPN posts the fixtures, pinned in a test.
4. **Tier lists for 2027.** Rebuild the hard-coded team lists for the 2027 field (27 MLS clubs, the pro and amateur entrants), move them into the season config, and match case-insensitively. ESPN spellings differ from common ones ("St. Louis CITY SC", "Red Bull New York", "D.C. United"). In 2026, AV Alta FC had the wrong badge from a capitalization mismatch, and Laredo Heat SC and Little Rock Rangers were missing from the lists. South Georgia Tormenta FC withdrew in February; the First Round walkover shows in ESPN data as a 1-0 win for FC America CFL Spurs, so walkovers need a flag of their own.
5. **Frozen archive for 2026.** Save the verified 2026 bracket as a committed JSON file and serve `/2026` from it with no scraping. Wikipedia's 2026 article now bolds the losing team in every match box, and ESPN changed its API this year; an archive that keeps re-scraping can be corrupted again. A committed file also survives redeploys (the Railway service has no volume today, so every deploy rebuilds `bracket.json` from a fresh scrape).
6. **A real data-quality guard.** The only guard today is "never overwrite with fewer matches." It kept a corrupted 79-match file on the live site for six weeks because the newer Wikipedia scrape, itself wrong, had 78. Validate before saving instead: each winner agrees with the score or shootout, round sizes never exceed the season's shape, and every winner appears in the next round once that round is drawn.
7. **Off-season scheduler and alerts.** The scheduler scrapes every two hours all year. Since ESPN broke, it has posted a Slack alert on every run (33 in the last three days of logs), because two of three sources fail. Stop scraping between the Final and the First Round announcement, and widen the game-day fast poll (now 6pm to midnight ET) for the Thursday to Sunday Round of 64.
8. **Drop or rewrite the ussoccer.com scraper.** The schedule page is now rendered client-side from embedded JSON, so the HTML parser finds nothing, and it counts as a permanent "failed source" that makes any single real failure trigger an alert. Recommend removing it and alerting on ESPN failure directly, with Wikipedia as the backup.
9. **Wikipedia backup fixes.** The Final on Wikipedia is transcluded from a separate article (`{{:2026 U.S. Open Cup final}}`) and uses `{{Football box`, not `{{football box collapsible`, so the parser never sees it. Follow the transclusion. Also add a contact address to the User-Agent and fetch the article once instead of once per section; Wikipedia returned HTTP 429 (rate limited) during today's checks.
10. **SEO structure.** One URL per season (`/` for current, `/2026`, later `/2027`), a sitemap listing them, `robots.txt`, per-season titles and meta descriptions, and the recap articles as their own URLs. See `docs/seo/README.md`.

## Effort (agent compute time)

- Items 1 to 5 (config, shape, grouping, tiers, archive) with tests and a browser smoke: about 3 to 4 hours of agent compute, plus one Crash Override review round.
- Items 6 to 9: about 1 to 2 hours of agent compute.
- Loading 2027 pairings once published: under 1 hour of agent compute, mostly verification.

## Should 2026 stay up as an archive?

Yes. People search for past editions long after they end ("2026 U.S. Open Cup bracket", "2026 U.S. Open Cup results"). A permanent `/2026` URL keeps whatever ranking the root URL earned this year, and the 2027 page can link to it ("2026 results") so the two support each other. Cost is near zero once it is a static JSON file.

## Decisions (Todd, 2026-10-28)

1. 2026 fix: approved, merged (PR #2) and deployed 2026-10-28.
2. Archive URL: `/2026` on this subdomain.
3. Build window: **January 2027**, not December. Start early in January so the build is done before the pairings land (2026's came January 27).
4. ussoccer.com scraper: remove, as part of the rollover.
5. Articles: on this site, in Todd's writing standards. Built in PR #3 (`/news`, `/<season>/<slug>`, sitemap, robots.txt).

## Rollover checklist additions from the articles work

- When `/2026` goes live, change the bracket links in the 2026 posts from `/` to `/2026`, and the "full 2026 bracket" links in the 2027 posts.
- Regenerate `frontend/public/og-image.png` for 2027, and update the title, meta description, JSON-LD and noscript summary in `frontend/index.html`.
- Update `docs/grok-content-brief.md`: the calendar table and the existing posts table.
- The bracket page at phone width overflows by about 1250px (the SVG is wider than the screen). Pre-existing; fix it with the 2027 layout.
- The article route `/<four-digit year>/<slug>` takes priority over static files, so a file at `dist/2026/bracket.json` would return 404. Serve the frozen 2026 archive data from an API route (for example `/api/bracket?season=2026`), not a static path under `/2026/`. The `/2026` page itself (no second segment) is not affected.

## Sources

- U.S. Soccer, "Format Finalized for 2027 Lamar Hunt U.S. Open Cup Featuring All 27 U.S.-Based MLS Teams" (Sept. 2026): https://ussoccer.com/stories/2026/09/usoc/format-finalized-2027-lamar-hunt-us-open-cup-all-27-us-based-mls-teams
- TheCup.us, 2026 First Round draw (Jan. 27, 2026): https://thecup.us/2026/01/27/2026-us-open-cup-first-round-draw-announced/
- U.S. Soccer, 2026 Final recap: https://www.ussoccer.com/stories/2026/10/usoc/match-recap-st-louis-city-vs-columbus-crew-open-cup-final
- ESPN scoreboard API (`site.api.espn.com/apis/site/v2/sports/soccer/usa.open/scoreboard?dates=2026`), checked 2026-10-28
- Wikipedia, 2026 U.S. Open Cup and 2026 U.S. Open Cup final, checked 2026-10-28
