"""Shared-secret gate for read-only ops queue routes (no full admin auth in MVP)."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_ops_queue_token(
    authorization: str | None = Header(default=None),
    x_ops_token: str | None = Header(default=None, alias="X-Ops-Token"),
) -> None:
    settings = get_settings()
    expected = settings.ops_queue_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ops queue API is disabled (set OPS_QUEUE_TOKEN).",
        )
    provided: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    elif x_ops_token:
        provided = x_ops_token.strip()
    if not provided:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials.")
    if len(provided) != len(expected) or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
