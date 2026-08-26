import os
import re
from urllib.parse import quote
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import jwt

import db
import executive_mock
import executive_data

load_dotenv()
app = FastAPI(title=os.getenv("APP_TITLE", "Pertamina Overview Kilang"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─── SSO (Central Login Service) ────────────────────────────────
# SSO_SECRET wajib sama persis dengan yang dipakai sso-login. Kalau kosong,
# fitur SSO nonaktif (app ini tetap jalan dengan login lokal seperti biasa).
SSO_SECRET    = os.getenv("SSO_SECRET", "")
SSO_LOGIN_URL = os.getenv("SSO_LOGIN_URL", "").rstrip("/")


def _verify_sso_token(token):
    """Verifikasi JWT dari sso-login, return username kalau valid."""
    if not SSO_SECRET or not token:
        return None
    try:
        payload = jwt.decode(token, SSO_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def _bootstrap_sso_session(request: Request):
    """Kalau ada cookie sso_token valid & user-nya aktif, return dict data user
    untuk diisi ke session. Return None kalau tidak ada/tidak valid."""
    username = _verify_sso_token(request.cookies.get("sso_token"))
    if not username:
        return None
    user = db.get_user_by_username(username)
    if not user or not user.get("is_active"):
        return None
    return {"username": user["username"], "role": user["role"], "via_sso": True}


def _sso_login_redirect_url(request: Request) -> str:
    """URL tujuan redirect kalau user belum login sama sekali."""
    if SSO_LOGIN_URL:
        return f"{SSO_LOGIN_URL}/login?redirect={quote(str(request.url), safe='')}"
    return f"/login?next={quote(request.url.path)}"


def _sso_logout_redirect_url() -> str:
    """URL tujuan setelah logout, supaya sesi SSO pusat ikut dihapus."""
    return f"{SSO_LOGIN_URL}/logout" if SSO_LOGIN_URL else "/login"
# ──────────────────────────────────────────────────────────────


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
    if not request.url.path.startswith("/dashboard"):
        return await call_next(request)

    user = request.session.get("user")

    # Session yang asalnya dari bootstrap SSO cuma dianggap valid selama
    # cookie sso_token masih valid & untuk user yang sama — supaya logout
    # di central login (atau di service SSO lain) langsung berlaku di
    # sini juga, tanpa nunggu session ini kedaluwarsa sendiri.
    if user and user.get("via_sso"):
        if _verify_sso_token(request.cookies.get("sso_token")) != user.get("username"):
            request.session.clear()
            user = None

    if not user:
        user = _bootstrap_sso_session(request)
        if user:
            request.session["user"] = user

    if not user:
        return RedirectResponse(_sso_login_redirect_url(request))

    return await call_next(request)


_SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not _SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY environment variable is not set. Set it before starting the app.")

app.add_middleware(
    SessionMiddleware,
    secret_key=_SESSION_SECRET_KEY,
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
    user = request.session.get("user")
    if not user:
        user = _bootstrap_sso_session(request)
        if user:
            request.session["user"] = user
    if user:
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
    # Logout dari sesi lokal saja belum cukup kalau user login lewat SSO:
    # cookie sso_token-nya masih valid, jadi /login lokal bakal langsung
    # bootstrap login lagi. Arahkan ke /logout milik sso-login supaya cookie
    # SSO-nya (domain-lebar) ikut dihapus, baru mendarat di halaman login pusat.
    return RedirectResponse(_sso_logout_redirect_url(), status_code=303)


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
