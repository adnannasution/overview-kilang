# Overview Kilang — Refinery Reliability Executive Dashboard

Standalone FastAPI + Jinja2 + vanilla CSS app that renders the strategic
"Overview Kilang" dashboard for VP Reliability / Operation Director, live from
the PostgreSQL reliability tables.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then edit DATABASE_URL
uvicorn main:app --reload
```
Open http://localhost:8000 → redirects to `/dashboard/executive`.

- `/dashboard/executive` — the dashboard (6 tabs)
- `/dashboard/executive?period=Apr%202026` — period selector
- `/dashboard/executive/debug` — JSON diagnostics (why a KPI is live/mock)
- `/dashboard/drilldown?ru=RU6` — per-RU drill-down (stub)

The header banner shows **Live / Partial / Mockup** depending on how much of the
data resolved from the DB. With no DB it falls back to mock automatically.

## Files
| File | Purpose |
|---|---|
| `main.py` | FastAPI app + routes |
| `db.py` | PostgreSQL connection (`get_conn`, reads `DATABASE_URL`) |
| `executive_data.py` | **Live data layer** — queries, tolerant date/number parsing, RU normalizer, period logic, `methodology()`, `diagnostics()` |
| `executive_mock.py` | Mock skeleton used as per-section fallback / shape reference |
| `templates/base.html` | App shell (sidebar, topbar) |
| `templates/executive.html` | Dashboard page — 6 tabs |
| `templates/_exec_components.html` | Reusable Jinja macros (KPI card, badge, marker, scorecard row, issue item…) |
| `templates/_exec_map.html` | Realistic Indonesia SVG map + refinery markers |
| `templates/drilldown.html` | Per-RU drill-down stub |
| `static/css/style.css` | Base shell styles (light theme) |
| `static/css/executive.css` | Dashboard styles (scoped under `.exec-dash`) |
| `static/js/executive.js` | Tab switching + refresh button |
| `static/js/app.js` | Sidebar toggle |

## Tabs
Corporate Overview · Refinery Unit Overview · Critical Alerts ·
Reliability Readiness · Data Freshness · **Metodologi** (transparency: source
table + detected columns + formula per metric).

## How data resolves
`executive_data.get_executive_snapshot(period)` builds a snapshot from the mock
skeleton, then overlays live values section-by-section. Each section is wrapped
in try/except; anything that fails (missing table/column, empty, DB down) keeps
the mock value. See the **Metodologi** tab or `/dashboard/executive/debug` for
exactly what resolved.

## Dev extras
- `.gitignore` — ignores venv, `__pycache__`, `.env`, editor files.
- `.claude/settings.json` — SessionStart hook that runs `pip install -r requirements.txt`
  automatically, so the project is ready to run in Claude Code (web) sessions.
"# overview-kilang" 
