"""Bearer token auth for supplier-admin routes (hashed credentials in DB — no global shared secret)."""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.supplier import Supplier
from app.repositories.supplier import SupplierApiCredentialRepository


def hash_supplier_api_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def require_supplier(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> Supplier:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials.")
    raw = authorization[7:].strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials.")
    digest = hash_supplier_api_token(raw)
    cred = SupplierApiCredentialRepository().find_active_by_token_hash(db, token_hash=digest)
    if cred is None or cred.supplier is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    return cred.supplier


SupplierAuth = Annotated[Supplier, Depends(require_supplier)]
