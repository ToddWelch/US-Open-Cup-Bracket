# CLAUDE.md

## Global rules pointer

Behavior rules, orchestrator process, agent system, coding discipline,
and infrastructure gotchas live in the global Claude config:

- `/home/todd/.claude/CLAUDE.md` (always-loaded rule book)
- `/home/todd/.claude/persona-rules.md` (Todd's identity + personal-style layer)

This file (`/home/todd/projects/US-Open-Bracket/CLAUDE.md`) holds
US-Open-Bracket-specific guidance only: a Flask + React single-page app
displaying the 2026 Lamar Hunt U.S. Open Cup bracket in an NCAA-style
tournament tree, with auto-updating scores via ussoccer.com scraping,
deployed on Railway at usopencup.welchproductsllc.com.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask + React single-page app displaying the 2026 Lamar Hunt U.S. Open Cup bracket in an NCAA-style tournament tree. Scores auto-update via scraping ussoccer.com. Deployed on Railway at `usopencup.welchproductsllc.com`.

## Architecture

- **Backend** (Flask): `backend/app.py` serves API + static React build. `backend/scraper.py` scrapes ESPN (primary), Wikipedia (backup) and ussoccer.com (returns nothing; removal planned for the 2027 rollover). `backend/scheduler.py` runs APScheduler for periodic scraping. State stored in `backend/data/bracket.json` (flat file, no DB).
- **Articles**: Markdown posts in `backend/content/posts/`, validated at startup by `backend/articles.py` and served server-side by `backend/article_routes.py` (`/news`, `/<season>/<slug>`, `/api/articles`, `/robots.txt`, `/sitemap.xml`) with Jinja templates in `backend/templates/`. Writer brief for new posts: `docs/grok-content-brief.md`. Public copy follows Todd's voice: no em or en dashes, no Oxford comma, no hype.
- **Plans**: `docs/2027-rollover-plan.md` (2027 season, build in January 2027).
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

80 teams, 7 rounds. Upper bracket (matches 1-16) and lower bracket (matches 17-32) displayed simultaneously on one scrollable page (no tabs). Round of 32 is special: MLS teams enter here, so R32 has the same number of slots as R2 (not half). Semifinals converge to a centered Final box.

## Tier System

Teams are classified into 6 tiers with colored badges: MLS (red), USL-C (blue), USL1 (green), MLSNP (purple), USL2 (orange), AM/Amateur (gray). Classification lists are hardcoded in the JSX. The `getTier()` function uses substring matching.

## Visual Design

Dark green color palette (background #070f0b, accent #4ade80). Progressive font and cell sizing - earlier rounds are smaller/denser, later rounds get larger. SVG bracket with L-shaped connector lines. Semi-to-Final connectors use highlighted green styling.
