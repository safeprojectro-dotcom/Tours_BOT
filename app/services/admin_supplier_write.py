from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.api.supplier_admin_auth import hash_supplier_api_token
from app.models.enums import SupplierOnboardingStatus
from app.models.supplier import Supplier, SupplierApiCredential
from app.repositories.supplier import SupplierRepository


class AdminSupplierDuplicateCodeError(Exception):
    pass


class AdminSupplierWriteService:
    def create_supplier_with_credential(
        self,
        session: Session,
        *,
        code: str,
        display_name: str,
        credential_label: str | None,
    ) -> tuple[Supplier, str]:
        repo = SupplierRepository()
        if repo.find_by_code(session, code=code) is not None:
            raise AdminSupplierDuplicateCodeError
        now = datetime.now(UTC)
        supplier = Supplier(
            code=code,
            display_name=display_name,
            is_active=True,
            onboarding_status=SupplierOnboardingStatus.APPROVED,
            onboarding_submitted_at=now,
            onboarding_reviewed_at=now,
        )
        session.add(supplier)
        session.flush()
        raw = secrets.token_urlsafe(32)
        session.add(
            SupplierApiCredential(
                supplier_id=supplier.id,
                token_hash=hash_supplier_api_token(raw),
                label=credential_label,
                created_at=now,
                revoked_at=None,
            )
        )
        session.flush()
        session.refresh(supplier)
        return supplier, raw
