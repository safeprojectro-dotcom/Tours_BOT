"""Shared-secret gate for admin read-only routes (Phase 6 Step 1 — no full RBAC yet)."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_admin_api_token(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    settings = get_settings()
    expected = settings.admin_api_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is disabled (set ADMIN_API_TOKEN).",
        )
    provided: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    elif x_admin_token:
        provided = x_admin_token.strip()
    if not provided:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials.")
    if len(provided) != len(expected) or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
