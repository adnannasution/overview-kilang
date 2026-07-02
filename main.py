import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

import executive_mock
import executive_data

load_dotenv()
app = FastAPI(title=os.getenv("APP_TITLE", "Pertamina Overview Kilang"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return RedirectResponse("/dashboard/executive")


def _executive_context(period: str) -> dict:
    # Live data from the reliability tables, with per-section fallback to mock.
    try:
        snapshot = executive_data.get_executive_snapshot(period)
    except Exception:
        snapshot = executive_mock.get_executive_snapshot()
    try:
        methodology = executive_data.methodology(period)
    except Exception:
        methodology = {"entries": [], "db": "unavailable", "period": period}
    return {"snapshot": snapshot, "methodology": methodology,
            "period": period, "title": "Overview Kilang"}


@app.get("/dashboard/executive", response_class=HTMLResponse)
async def page_executive(request: Request, period: str = ""):
    return templates.TemplateResponse(request, "executive.html", _executive_context(period))


@app.get("/dashboard/executive/fragment", response_class=HTMLResponse)
async def page_executive_fragment(request: Request, period: str = ""):
    # Same dashboard content as /dashboard/executive, without the page shell —
    # used by the period switcher to swap data in without a full reload.
    return templates.TemplateResponse(request, "_exec_content.html", _executive_context(period))


@app.get("/dashboard/executive/debug")
async def page_executive_debug(period: str = ""):
    try:
        return JSONResponse(executive_data.diagnostics(period))
    except Exception as e:
        return JSONResponse({"db": f"diagnostics failed: {e!r}"})


@app.get("/dashboard/drilldown", response_class=HTMLResponse)
async def page_drilldown(request: Request, ru: str = ""):
    return templates.TemplateResponse(request, "drilldown.html", {
        "ru": ru, "title": "Refinery Drill-down"})
