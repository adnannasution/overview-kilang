import os
import re
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

import executive_mock
import executive_data

load_dotenv()
app = FastAPI(title=os.getenv("APP_TITLE", "Pertamina Overview Kilang"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def _render(request: Request, template: str, ctx: dict) -> HTMLResponse:
    ctx["user"] = request.session.get("user")
    return templates.TemplateResponse(request, template, ctx)


def _initials(username: str) -> str:
    local = re.sub(r'@.*', '', username)
    parts = re.split(r'[.\-_]', local)
    ini = ''.join(p[0] for p in parts if p).upper()[:2]
    return ini or (username[0].upper() if username else '')


# Auth guard — must be defined BEFORE app.add_middleware(SessionMiddleware)
# so SessionMiddleware ends up outermost (runs first) in the stack.
@app.middleware("http")
async def _auth_guard(request: Request, call_next):
    if request.url.path.startswith("/dashboard") and not request.session.get("user"):
        from urllib.parse import urlencode
        return RedirectResponse("/login?" + urlencode({"next": str(request.url.path)}))
    return await call_next(request)


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "change-me-in-production"),
    session_cookie="ok_session",
    max_age=8 * 3600,
    https_only=False,
)


@app.get("/")
async def root():
    return RedirectResponse("/dashboard/executive")


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, err: str = "", u: str = "", next: str = "/dashboard/executive"):
    if request.session.get("user"):
        return RedirectResponse(next if next.startswith("/") else "/dashboard/executive")
    step2 = bool(u and err == "1")
    return templates.TemplateResponse(request, "login.html", {
        "error": err == "1" and bool(u),
        "prefill": u,
        "initials": _initials(u) if u else "",
        "step2": step2,
        "next_url": next if next.startswith("/") else "/dashboard/executive",
    })


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(default=""),
    password: str = Form(default=""),
    next_url: str = Form(default="/dashboard/executive"),
):
    from auth import authenticate_user
    from urllib.parse import urlencode

    safe_next = next_url if next_url.startswith("/") else "/dashboard/executive"
    user = authenticate_user(username, password)
    if not user:
        params = urlencode({"err": "1", "u": username, "next": safe_next})
        return RedirectResponse(f"/login?{params}", status_code=303)
    request.session["user"] = user
    return RedirectResponse(safe_next, status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ── Dashboard routes ───────────────────────────────────────────────────────────

def _executive_context(period: str) -> dict:
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
    return _render(request, "executive.html", _executive_context(period))


@app.get("/dashboard/executive/fragment", response_class=HTMLResponse)
async def page_executive_fragment(request: Request, period: str = ""):
    return _render(request, "_exec_content.html", _executive_context(period))


@app.get("/dashboard/executive/debug")
async def page_executive_debug(period: str = ""):
    try:
        return JSONResponse(executive_data.diagnostics(period))
    except Exception as e:
        return JSONResponse({"db": f"diagnostics failed: {e!r}"})


@app.get("/dashboard/drilldown", response_class=HTMLResponse)
async def page_drilldown(request: Request, ru: str = ""):
    return _render(request, "drilldown.html", {"ru": ru, "title": "Refinery Drill-down"})
