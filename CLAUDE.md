# CLAUDE.md

## Global rules pointer

Behavior rules, orchestrator process, agent system, coding discipline,
and infrastructure gotchas live in the global Claude config:

- `/home/todd/.claude/CLAUDE.md` (always-loaded rule book)
- `/home/todd/.claude/persona-rules.md` (Todd's identity + personal-style layer)

This file (`/home/todd/projects/US-Open-Bracket/CLAUDE.md`) holds
US-Open-Bracket-specific guidance only: a Flask + React single-page app
displaying the Lamar Hunt U.S. Open Cup bracket (2027 on the root URL,
past seasons archived at /<year>) in an NCAA-style tournament tree, with
auto-updating scores from ESPN and Wikipedia, deployed on Railway at
usopencup.welchproductsllc.com.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask + React single-page app displaying the Lamar Hunt U.S. Open Cup bracket in an NCAA-style tournament tree. The root URL shows the current season (2027); each finished season is a frozen archive at `/<year>` (`/2026`). Scores auto-update from ESPN with Wikipedia as backup. Deployed on Railway at `usopencup.welchproductsllc.com`.

## Architecture

- **Seasons**: one config per season in `backend/season_data/<year>.json` (round names, sizes, dates, ESPN slugs, entry round, team tiers), loaded and checked by `backend/seasons.py`. `CURRENT_YEAR` there picks the root season. A finished season adds `<year>-bracket.json` (served as-is, never scraped) and `backend/templates/seasons/<year>_head.html` and `_noscript.html` (its page title, description and share card, swapped into `index.html` between the `season-head` and `season-noscript` markers).
- **Backend** (Flask): `backend/app.py` serves API (`/api/bracket?season=<year>`) + static React build + `/<year>` archive pages. `backend/scraper.py` scrapes ESPN (primary) and Wikipedia (backup), checks new data before saving (`validate_bracket`) and alerts Slack on ESPN failure (no-data alerts only between the First Round and the Final). `backend/scheduler.py` runs APScheduler for periodic scraping. State stored in `backend/data/bracket.json` (flat file, no DB), stamped with its season.
- **Articles**: Markdown posts in `backend/content/posts/`, validated at startup by `backend/articles.py` and served server-side by `backend/article_routes.py` (`/news`, `/<season>/<slug>`, `/api/articles`, `/robots.txt`, `/sitemap.xml`) with Jinja templates in `backend/templates/`. Writer brief for new posts: `docs/grok-content-brief.md`. Public copy follows Todd's voice: no em or en dashes, no Oxford comma, no hype.
- **Plans**: `docs/2027-rollover-plan.md` (2027 rollover, built 2026-11-18; its Status section lists what is left).
- **Frontend** (React + Vite): Single-component SVG bracket with foreignObject HTML cells. All styles are inline (no CSS framework). Build output goes to `frontend/dist/`.
- **Reference implementation**: `usopen-bracket.jsx` in the repo root is the working reference for the bracket UI. Adapt it for the Vite/React project structure.

## Development Commands

```bash
# Backend
cd backend && pip install -r ../requirements.txt && python app.py

# Frontend (dev with API proxy to Flask)
cd frontend && npm install && npm run dev

# Frontend build
cd frontend && npm run build

# Deploy (Railway auto-deploys from main)
git push
```

## Key Constraints

- **No em dashes** anywhere in the codebase or UI text
- **bracket.json must never be overwritten with less data** than it currently has
- Scraper must gracefully handle page structure changes (log error, keep existing data)
- Flask serves both the API and static React build in a single process
- Default zoom is 100% (the "L" preset)

## Tournament Structure

7 rounds in both seasons, with a 32-match First Round split into an upper bracket (matches 1-16) and lower bracket (matches 17-32), displayed simultaneously on one scrollable page (no tabs). The entry round (`entryRound` in the season config) is special: new teams join there, so it has the same number of slots as the round before it (not half). 2026: 80 teams, MLS clubs enter in the Round of 32 after a Second Round. 2027: 96 teams, the 27 U.S.-based MLS clubs and 5 seeded USL Championship clubs enter in the Round of 64, and there is no Second Round. Semifinals converge to a centered Final box.

## Tier System

Teams are classified into 6 tiers with colored badges: MLS (red), USL-C (blue), USL1 (green), MLSNP (purple), USL2 (orange), AM/Amateur (gray). Classification lists live in each season's config (`tiers`) and reach the page through `/api/bracket`. The `getTier()` function uses case-insensitive substring matching (MLS NEXT Pro exact match); a team in no list gets the amateur badge.

## Visual Design

Dark green color palette (background #070f0b, accent #4ade80). Progressive font and cell sizing - earlier rounds are smaller/denser, later rounds get larger. SVG bracket with L-shaped connector lines. Semi-to-Final connectors use highlighted green styling.
