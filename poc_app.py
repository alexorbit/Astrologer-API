"""Isolated Railway PoC adapter; upstream main.py and all calculations untouched.

Only the static test console is public. /api/v6/... uses the existing
Astrologer authentication middleware; never disable it in staging.
"""
from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse
from app.main import app as engine_app

_ROOT = Path(__file__).resolve().parent / "poc"
_STATIC = {
    "/poc": ("index.html", "text/html"),
    "/poc/app.css": ("app.css", "text/css"),
    "/poc/app.js": ("app.js", "text/javascript"),
}

async def app(scope, receive, send):
    if scope.get("type") == "http" and scope.get("method") == "GET":
        resource = _STATIC.get(scope.get("path"))
        if resource:
            filename, mime = resource
            response = FileResponse(
                _ROOT / filename, media_type=mime,
                headers={
                    "Cache-Control": "no-store",
                    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "no-referrer",
                    "X-Frame-Options": "DENY"
                })
            await response(scope, receive, send)
            return
    await engine_app(scope, receive, send)
