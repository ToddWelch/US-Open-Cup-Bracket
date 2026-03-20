# US Open Cup Bracket Tracker

## Project Overview

A standalone Flask + React single-page application that displays the 2026 Lamar Hunt U.S. Open Cup bracket in an NCAA-style tournament tree and automatically updates scores by scraping the official US Soccer schedule page.

**Deploy target:** New Railway project at `usopen.welchproductsllc.com`

## Architecture

```
usopen-cup-bracket/
  backend/
    app.py              # Flask app, serves API + static React build
    scraper.py          # Scrapes ussoccer.com/us-open-cup/schedule
    scheduler.py        # APScheduler cron to run scraper
    data/
      bracket.json      # Current bracket state (flat file, no DB needed)
  frontend/
    src/
      App.jsx           # Main bracket component (see Design section)
      index.jsx         # Entry point
      index.css         # Global styles
    public/
      index.html
    package.json
    vite.config.js
  Dockerfile
  requirements.txt
  railway.toml
  .gitignore
  README.md
```

## Tournament Structure

The 2026 US Open Cup has 7 rounds with 80 teams total:

| Round | Dates | Matches | Teams Entering |
|-------|-------|---------|----------------|
| First Round | Mar 17-19 | 32 | 48 pro (Div II/III) + 32 amateur |
| Second Round | Mar 31 / Apr 1 | 16 | 32 First Round winners |
| Round of 32 | Apr 14-15 | 16 | 16 Second Round winners + 16 MLS teams |
| Round of 16 | Apr 28-29 | 8 | |
| Quarterfinals | May 19-20 | 4 | |
| Semifinals | Sep 15-16 | 2 | |
| Final | Oct 21 | 1 | |

## Team Tier Classification

Every team gets a colored tier badge. Classification logic:

- **MLS** (red #C41E3A badge): Atlanta United, Austin FC, Charlotte FC, Chicago Fire FC, Colorado Rapids, Columbus Crew, D.C. United, Houston Dynamo FC, Minnesota United FC, New England Revolution, New York City FC, Orlando City SC, Red Bull New York, San Jose Earthquakes, Sporting Kansas City, St. Louis CITY SC
- **USL-C** (blue #4A90D9 badge): Charleston Battery, Detroit City FC, Hartford Athletic, Indy Eleven, Loudoun United FC, Louisville City FC, Pittsburgh Riverhounds SC, Rhode Island FC, Colorado Springs Switchbacks FC, El Paso Locomotive FC, FC Tulsa, Lexington SC, New Mexico United, Orange County SC, Phoenix Rising FC, Sacramento Republic FC, San Antonio FC
- **USL1** (green #2D7D4F badge): AV ALTA FC, Charlotte Independence, Chattanooga Red Wolves SC, FC Naples, Forward Madison FC, Greenville Triumph SC, One Knoxville SC, Portland Hearts of Pine, Richmond Kickers, Spokane Velocity FC, Union Omaha, Westchester SC
- **MLSNP** (purple #8B5CF6 badge): Carolina Core FC, Chattanooga FC
- **USL2** (orange #E08A2C badge): Vermont Green FC, Flint City Bucks, Steel City FC, Ventura County Fusion, Des Moines Menace, Northern Virginia FC, Asheville City SC, Flower City Union, West Chester United SC
- **AM** (gray #9CA3AF badge): All remaining teams (UPSL, NPSL, APSL, local qualifiers, etc.)

## Bracket Layout Design (CRITICAL)

The bracket uses an **NCAA Final Four style layout** rendered as an SVG with foreignObject for match cells.

### Overall Structure

Both upper and lower brackets visible simultaneously on one scrollable page. No tabs.

```
UPPER BRACKET (Matches 1-16)
  R1(16) -> R2(8) -> R32(8+MLS) -> R16(4) -> QF(2) -> SF(1)
                                                           \
- - - - - - - - - - - - - - - - - - - - - - [FINAL] 🏆
                                                           /
LOWER BRACKET (Matches 17-32)
  R1(16) -> R2(8) -> R32(8+MLS) -> R16(4) -> QF(2) -> SF(1)
```

### Progressive Font and Cell Sizing

Text and cells grow larger as rounds advance. Earlier rounds are denser, later rounds get more visual emphasis.

| Round | Name Font | Badge Font | Cell Width | Cell Height |
|-------|-----------|------------|------------|-------------|
| 1st Round | 10px | 7px | 172px | 36px |
| 2nd Round | 11px | 7px | 176px | 38px |
| Round of 32 | 11px | 8px | 180px | 38px |
| Round of 16 | 12px | 8px | 186px | 40px |
| Quarterfinals | 13px | 9px | 192px | 42px |
| Semifinals | 13px | 9px | 198px | 44px |
| Final | 14px | 10px | 210px | 56px |

Column X positions are computed cumulatively from these widths plus a 30px horizontal gap between columns.

### Zoom Controls

The bracket supports zooming for readability:

1. **Slider** in the header bar: range 30% to 200%, default 100%
2. **Quick presets**: Fit (55%), S (70%), M (85%), L (100%), XL (130%). Default is L (100%).
3. **Ctrl+Scroll** (mouse wheel with Ctrl/Cmd held) to zoom
4. **Pinch-to-zoom** on touch devices (two-finger gesture)
5. Current zoom percentage displayed next to the slider
6. Implementation: CSS `transform: scale(zoom)` with `transformOrigin: "top left"` on the bracket container, inside a scrollable overflow wrapper

### Key Layout Rules

1. **Both halves visible simultaneously** on one scrollable page. No tabs to switch regions.
2. **Left-to-right tree flow** with L-shaped connector lines (horizontal out, vertical to target height, horizontal into next cell).
3. **Upper bracket** sits on top, **lower bracket** below, separated by a dashed divider line.
4. **Semifinals converge to a centered Final box:**
   - Upper Semi connector goes RIGHT then DOWN to the Final
   - Lower Semi connector goes RIGHT then UP to the Final
   - Final box is vertically centered in the gap between upper and lower halves
   - Trophy emoji sits above the Final box
   - Small "UPPER" and "LOWER" labels on the converging connector lines
   - Semi-to-Final connectors use highlighted green (#4ade8040, 1.5px) vs normal connectors (#1a3a2a, 1px)
5. **Round of 32 is special:** MLS teams enter here. Each R2 winner gets paired with an MLS team. The R32 column has the SAME number of slots as R2 (8 per region), not half. Slot labels show "MLS Team" and "R2 Winner" as placeholders until the draw.
6. **Round column headers** above the bracket: "1ST ROUND", "2ND ROUND", "ROUND OF 32", "ROUND OF 16", "QUARTERS", "SEMIS", "FINAL" with date subtitles.

### Match Cell Design

Each match is a rectangle containing two rows:
- Top row: Home team tier badge + name + score
- Bottom row: Away team tier badge + name + score
- Separator: 1px #162a20 line between rows
- Winner row: green left-border accent (2px via borderLeft on the row), bold green (#4ade80) text, darker green background (#102e1c)
- Unplayed matches: "TBD" in muted italic (#2e4e3e)
- MLS placeholder slots: "MLS Team" / "R2 Winner" in italic
- Notes (AET, FF, date): tiny monospace text in the top-right area of the cell
- Score: monospace, right-aligned, fixed min-width

### Final Box Design

Larger cell (210px x 56px) with:
- An 18px header bar: "FINAL . OCT 21" in green monospace, centered, with gradient background
- Green glowing border (#4ade8060) and subtle shadow (0 0 24px #4ade8018)
- Same two-row team layout but with 14px font
- Trophy emoji (26px) centered above the box

### Color Palette

- Page background: #070f0b
- Header gradient: #0e2118 to #070f0b
- Card background: #0c1812
- Card border normal: #162a20, with winner: #2a5a3a
- Primary accent: #4ade80
- Winner highlight: text #4ade80, background #102e1c
- Muted text layers: #3e6e4e, #2e5e3e, #2a4a3a, #1e3e2e
- Divider: dashed #1a3a2a, strokeDasharray="6,4"
- Typography: system-ui sans-serif for body, monospace for stats/badges/headers

### Stats in Header

- Completion counter box: large number with "/32" suffix, "R1 DONE" label
- Upset counter box: count of AM or USL2 team wins over higher-tier opponents, orange (#E08A2C)
- Tier legend: all 6 badges with full league names

### Footer Bar

- Pending match info
- Next round info
- Source: "ussoccer.com . welchproductsllc.com"

## Backend Details

### Flask App (`app.py`)

- Serve the built React app from `frontend/dist/`
- `GET /api/bracket` returns the full bracket JSON
- `GET /api/health` basic health check
- On startup, run initial scrape if bracket.json is empty or stale

### Scraper (`scraper.py`)

**Target URL:** `https://www.ussoccer.com/us-open-cup/schedule`

The page has a table with results in format: `Team A X - Y Team B`

Scraping strategy:
1. Use `requests` + `BeautifulSoup` to fetch and parse
2. Parse each row into: `{ home, away, homeScore, awayScore, date, note }`
3. Notes for: "AET" (after extra time), "FF" (forfeit), or future date for unplayed
4. Compare new vs existing data before writing; never overwrite with less data
5. Write to `data/bracket.json`

bracket.json structure:

```json
{
  "lastUpdated": "2026-03-20T14:30:00Z",
  "scrapeStatus": "ok",
  "rounds": [
    {
      "name": "First Round",
      "schedule": "Mar 17-19",
      "matches": [
        {
          "home": "Richmond Kickers",
          "away": "Northern Virginia FC",
          "homeScore": 2,
          "awayScore": 0,
          "date": "March 17",
          "note": null
        }
      ]
    }
  ]
}
```

### Scheduler (`scheduler.py`)

APScheduler (BackgroundScheduler) integrated into Flask:
- Default: scrape every 2 hours
- Game days: every 30 minutes, 6pm-midnight ET
- Log each run with timestamp and change status

### Error Handling

- Scrape failure: log warning, keep existing data
- Never write empty/corrupted data to bracket.json
- `scrapeStatus` field: "ok", "stale", "error"

## Frontend Details

### React App (Vite)

See the Bracket Layout Design section for visual spec. Additional:

1. **Auto-refresh**: poll `/api/bracket` every 5 minutes, update if `lastUpdated` changed
2. **Responsive**: horizontal + vertical scroll, smooth touch scrolling
3. **SVG rendering** with foreignObject for HTML match cells
4. **Zoom** via CSS transform on the bracket container (see Zoom Controls section)

### Build

- Vite for bundling
- All styles inline (no CSS framework)
- Output to `frontend/dist/`

## Deployment

### Dockerfile

```dockerfile
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--chdir", "backend", "app:app"]
```

### requirements.txt

```
flask==3.1.0
requests==2.32.3
beautifulsoup4==4.13.3
apscheduler==3.11.0
gunicorn==23.0.0
```

### railway.toml

```toml
[build]
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/api/health"
healthcheckTimeout = 10
```

### Custom Domain

1. Railway project settings: add `usopen.welchproductsllc.com`
2. DNS: CNAME to Railway-provided domain
3. SSL handled automatically

## Initial Data

Seed bracket.json with First Round results. Scraper keeps it updated after that.

Upper bracket (matches 1-16):
```
Mar 17: Richmond Kickers 2-0 Northern Virginia FC
Mar 17: Rhode Island FC 4-0 CD Faialense
Mar 17: Vermont Green FC 1-0 Portland Hearts of Pine
Mar 17: Detroit City FC 5-1 Michigan Rangers
Mar 17: West Chester United SC 1-2 Loudoun United FC
Mar 17: Colorado Springs Switchbacks FC 3-0 Azteca FC
Mar 17: Indy Eleven 3-0 Des Moines Menace
Mar 17: Phoenix Rising FC 4-0 San Ramon FC
Mar 18: Chattanooga FC 2-1 Kalonji Pro-Profile
Mar 18: Asheville City SC 3-1 Greenville Triumph SC
Mar 18: Charleston Battery 2-1 Badgers FC
Mar 18: Louisville City FC 2-0 Southern Indiana FC
Mar 18: FC Naples 3-0 Red Force
Mar 18: FC Motown 0-2 Hartford Athletic
Mar 18: SC Vistula Garfield 1-3 One Knoxville SC
Mar 18: BOHFS St. Louis 0-8 Union Omaha
```

Lower bracket (matches 17-32):
```
Mar 18: Little Rock Rangers 2-4 FC Tulsa
Mar 18: San Antonio FC 6-0 ASC New Stars
Mar 18: New Mexico United 3-2 Cruizers FC
Mar 18: Sacramento Republic FC 2-0 El Farolito (AET)
Mar 18: AV ALTA FC 0-1 Valley 559 FC
Mar 18: Ventura County Fusion 1-2 Spokane Velocity FC
Mar 18: Orange County SC 3-0 Laguna United FC
Mar 19: Carolina Core FC 1-2 Virginia Dream FC
Mar 19: Charlotte Independence 4-1 Ristozi FC
Mar 19: Flint City Bucks 2-0 Forward Madison FC
Mar 19: Lexington SC 9-0 Flower City Union
Mar 19: Westchester SC 2-0 NY Renegades FC
Mar 19: Laredo Heat 0-2 El Paso Locomotive FC
Mar 19: Tennessee Tempo FC 1-0 Chattanooga Red Wolves SC
Mar 25: Pittsburgh Riverhounds SC vs Steel City FC (PENDING)
Forfeit: FC America CFL Spurs 1-0 South Georgia Tormenta FC
```

## Development Workflow

1. Clone repo, `cd usopen-cup-bracket`
2. Backend: `cd backend && pip install -r ../requirements.txt && python app.py`
3. Frontend: `cd frontend && npm install && npm run dev` (proxy API to Flask in vite.config.js)
4. Build: `cd frontend && npm run build`
5. Deploy: `git push` (Railway auto-deploys from main)

## Key Reminders

- No em dashes anywhere in the codebase or UI text
- Test scraper against live ussoccer.com page before deploying
- Scraper must gracefully handle page structure changes (log error, keep existing data)
- bracket.json must never be overwritten with less data than it currently has
- Flask serves both the API and the static React build (single process)
- The bracket artifact (.jsx file) is the working reference implementation. Adapt for Vite/React project structure.
- Default zoom is 100% (the "L" preset)
