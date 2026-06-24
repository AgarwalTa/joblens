# JobLens

A job market analysis tool that surfaces experience inflation, title mismatches, and ATS rejection patterns using scraped data and user-submitted stories.

## Stack
Python · Flask · SQLite · BeautifulSoup · pandas · Chart.js · Render.com

## Quickstart

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # initialises DB + starts server on :5000
```

## Project Phases
- [x] Phase 1 — Flask + SQLite setup (job_posts, skills_extracted, user_stories)
- [ ] Phase 2 — Scraper (BeautifulSoup)
- [ ] Phase 3 — User story submission form
- [ ] Phase 4 — Analysis & API layer
- [ ] Phase 5 — Frontend dashboard (Chart.js)

## API
- `GET /api/status` — health check + table row counts
