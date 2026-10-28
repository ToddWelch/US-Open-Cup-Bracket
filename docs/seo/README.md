# SEO drafts and on-page fixes

Written 2026-10-28. Everything here is a draft for Todd's review. Nothing is published, and none of it is on the live site.

## Post drafts

| # | File | Title | Target phrase | Suggested URL |
|---|---|---|---|---|
| 1 | `post-1-2026-final.md` | St. Louis CITY SC Win the 2026 U.S. Open Cup on Penalties | 2026 U.S. Open Cup final | `/2026/final` |
| 2 | `post-2-2026-cupsets.md` | Every Cupset of the 2026 U.S. Open Cup | 2026 U.S. Open Cup upsets | `/2026/cupsets` |
| 3 | `post-3-2027-format-schedule.md` | 2027 U.S. Open Cup Format and Schedule: 96 Teams, Final on December 15 | 2027 U.S. Open Cup schedule | `/2027/format-and-schedule` |
| 4 | `post-4-2027-draw.md` | When Is the 2027 U.S. Open Cup Draw? What to Know Before the First Round | 2027 U.S. Open Cup draw | `/2027/draw` |

Target phrases are judgment calls from how people phrase these searches. No keyword-volume data was pulled, because that needs a paid tool (Ahrefs, Semrush or similar), which would need Todd's OK first.

The suggested URLs assume the 2027 rollover plan (`docs/2027-rollover-plan.md`): one URL per season, with articles under it. The site has no article pages today, so publishing these on this domain needs a small build. They can also go on welchproductsllc.com or LinkedIn, but links on this domain help this site rank.

Posts 3 and 4 depend on U.S. Soccer dates that are "subject to change." Re-check them the day before publishing.

## On-page fixes (current live site)

Checked 2026-10-28 against https://usopencup.welchproductsllc.com.

| # | Issue | Fix |
|---|---|---|
| 1 | `<title>` says "Live Tournament Bracket & Scores"; the tournament is over | `2026 U.S. Open Cup Bracket and Results: St. Louis CITY SC Win` |
| 2 | Meta description says "Live ... real-time scores" | `Full 2026 Lamar Hunt U.S. Open Cup bracket and results. St. Louis CITY SC beat Columbus Crew on penalties in the October 21 Final.` |
| 3 | `og:` and `twitter:` titles say "Live Scores"; `twitter:card` is `summary_large_image` but there is no `og:image`, so shares show no picture | Update titles to match 1 and 2; add a 1200x630 image of the finished bracket as `og:image` |
| 4 | JSON-LD FAQ answers are written in the future tense ("The Final is scheduled for October 21") | Past tense with the result. Note: since 2023 Google shows FAQ rich results only for government and health sites, so this markup earns no rich result here; keep it accurate or remove it |
| 5 | Article block "First Round Highlights" was written in March and stops there | Replace with the copy below |
| 6 | Article and footer say results come from ussoccer.com; they come from ESPN, with Wikipedia as backup | Fix the sentence and the footer credit |
| 7 | `robots.txt` returns 404 | Add one that allows everything and points to the sitemap |
| 8 | `sitemap.xml` returns 404 | Add one listing `/` (and `/2026` and article URLs after the rollover) |
| 9 | `favicon.ico` returns 404 | Add a favicon |
| 10 | The bracket and article text exist only after JavaScript runs; the first HTML response has the `noscript` paragraph and JSON-LD only | Put a short static summary (champion, Final score, link to results) in `index.html` so it is in the first response |

### Replacement copy for the on-page article (fix 5 and 6)

> **2026 Lamar Hunt U.S. Open Cup Bracket and Results**
>
> St. Louis CITY SC won the 2026 Lamar Hunt U.S. Open Cup, the 111th edition of the oldest ongoing soccer competition in the United States. They beat Columbus Crew 5-3 on penalties after a 0-0 draw in the Final on October 21 at ScottsMiracle-Gro Field. It is the club's first trophy.
>
> **Tournament format**
>
> 80 teams played seven rounds of single elimination. The First Round (March 17-19) matched 48 professional teams from the USL Championship, USL League One and MLS NEXT Pro against 32 amateur qualifiers. The 32 First Round winners played a Second Round (March 31 and April 1), and the 16 Second Round winners met 16 MLS clubs in the Round of 32 (April 14-15). The Round of 16, Quarterfinals, Semifinals and Final followed.
>
> **Cupsets**
>
> Lower-division teams won 12 matches against higher-division opponents. Six came in the First Round, and three came in the Round of 32, where Colorado Springs Switchbacks FC, Louisville City FC and One Knoxville SC knocked out Sporting Kansas City, Austin FC and D.C. United.
>
> **About this bracket**
>
> Teams are color-coded by league: MLS, USL Championship, USL League One, MLS NEXT Pro, USL League Two and amateur. A cupset badge marks a lower-level team beating a higher-level one. Results come from ESPN, with Wikipedia as a backup.
