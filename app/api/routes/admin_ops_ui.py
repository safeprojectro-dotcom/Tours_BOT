"""A1: internal HTML surfaces for Mode 3 custom requests — read-only shell; data from existing admin APIs."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])

_OPS_HTML = Path(__file__).resolve().parents[2] / "admin" / "custom_requests_ops.html"


@router.get("/admin/ui/custom-requests", response_class=HTMLResponse)
def admin_custom_requests_ops_console() -> HTMLResponse:
    """Static operational console; authenticate via token in page (sessionStorage) for API calls."""
    body = _OPS_HTML.read_text(encoding="utf-8")
    return HTMLResponse(content=body)
