from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import SupplierLegalEntityType, SupplierOnboardingStatus, SupplierServiceComposition
from app.models.supplier import Supplier
from app.repositories.supplier import SupplierRepository


class SupplierOnboardingNotFoundError(Exception):
    pass


class SupplierOnboardingApprovalValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOnboardingService:
    def __init__(self, *, supplier_repo: SupplierRepository | None = None) -> None:
        self.supplier_repo = supplier_repo or SupplierRepository()

    def get_by_telegram_user_id(self, session: Session, *, telegram_user_id: int) -> Supplier | None:
        return self.supplier_repo.find_by_primary_telegram_user_id(session, telegram_user_id=telegram_user_id)

    def submit_from_telegram(
        self,
        session: Session,
        *,
        telegram_user_id: int,
        display_name: str,
        contact_info: str,
        region: str,
        legal_entity_type: SupplierLegalEntityType,
        legal_registered_name: str,
        legal_registration_code: str,
        permit_license_type: str,
        permit_license_number: str,
        service_composition: SupplierServiceComposition,
        fleet_summary: str | None,
    ) -> tuple[Supplier, str]:
        supplier = self.get_by_telegram_user_id(session, telegram_user_id=telegram_user_id)
        now = datetime.now(UTC)
        clean_display = display_name.strip()
        clean_contact = contact_info.strip()
        clean_region = region.strip()
        clean_legal_registered_name = legal_registered_name.strip()
        clean_legal_registration_code = legal_registration_code.strip().upper()
        clean_permit_license_type = permit_license_type.strip()
        clean_permit_license_number = permit_license_number.strip()
        clean_fleet = (fleet_summary or "").strip() or None
        if supplier is None:
            code = self._generate_supplier_code(session=session, telegram_user_id=telegram_user_id)
            supplier = Supplier(
                code=code,
                display_name=clean_display,
                is_active=False,
                primary_telegram_user_id=telegram_user_id,
                onboarding_status=SupplierOnboardingStatus.PENDING_REVIEW,
                onboarding_contact_info=clean_contact,
                onboarding_region=clean_region,
                legal_entity_type=legal_entity_type,
                legal_registered_name=clean_legal_registered_name,
                legal_registration_code=clean_legal_registration_code,
                permit_license_type=clean_permit_license_type,
                permit_license_number=clean_permit_license_number,
                onboarding_service_composition=service_composition,
                onboarding_fleet_summary=clean_fleet,
                onboarding_rejection_reason=None,
                onboarding_submitted_at=now,
                onboarding_reviewed_at=None,
            )
            session.add(supplier)
            session.flush()
            return supplier, "submitted"

        if supplier.onboarding_status == SupplierOnboardingStatus.PENDING_REVIEW:
            return supplier, "already_pending"
        if supplier.onboarding_status == SupplierOnboardingStatus.APPROVED:
            return supplier, "already_approved"

        supplier.display_name = clean_display
        supplier.is_active = False
        supplier.onboarding_status = SupplierOnboardingStatus.PENDING_REVIEW
        supplier.onboarding_contact_info = clean_contact
        supplier.onboarding_region = clean_region
        supplier.legal_entity_type = legal_entity_type
        supplier.legal_registered_name = clean_legal_registered_name
        supplier.legal_registration_code = clean_legal_registration_code
        supplier.permit_license_type = clean_permit_license_type
        supplier.permit_license_number = clean_permit_license_number
        supplier.onboarding_service_composition = service_composition
        supplier.onboarding_fleet_summary = clean_fleet
        supplier.onboarding_rejection_reason = None
        supplier.onboarding_submitted_at = now
        supplier.onboarding_reviewed_at = None
        session.flush()
        return supplier, "resubmitted"

    def admin_approve(self, session: Session, *, supplier_id: int) -> Supplier:
        supplier = session.get(Supplier, supplier_id)
        if supplier is None:
            raise SupplierOnboardingNotFoundError
        if (
            supplier.onboarding_status == SupplierOnboardingStatus.PENDING_REVIEW
            and not self._has_required_legal_identity(supplier)
        ):
            raise SupplierOnboardingApprovalValidationError(
                "Supplier legal identity is incomplete; legal fields are required before approval.",
            )
        supplier.onboarding_status = SupplierOnboardingStatus.APPROVED
        supplier.is_active = True
        supplier.onboarding_rejection_reason = None
        supplier.onboarding_reviewed_at = datetime.now(UTC)
        if supplier.onboarding_submitted_at is None:
            supplier.onboarding_submitted_at = supplier.onboarding_reviewed_at
        session.flush()
        return supplier

    def admin_reject(self, session: Session, *, supplier_id: int, reason: str) -> Supplier:
        supplier = session.get(Supplier, supplier_id)
        if supplier is None:
            raise SupplierOnboardingNotFoundError
        supplier.onboarding_status = SupplierOnboardingStatus.REJECTED
        supplier.is_active = False
        supplier.onboarding_rejection_reason = reason.strip()
        supplier.onboarding_reviewed_at = datetime.now(UTC)
        if supplier.onboarding_submitted_at is None:
            supplier.onboarding_submitted_at = supplier.onboarding_reviewed_at
        session.flush()
        return supplier

    def _generate_supplier_code(self, session: Session, *, telegram_user_id: int) -> str:
        base = f"TG-{telegram_user_id}"
        if self.supplier_repo.find_by_code(session, code=base) is None:
            return base
        for idx in range(1, 1000):
            candidate = f"{base}-{idx}"
            if self.supplier_repo.find_by_code(session, code=candidate) is None:
                return candidate
        return f"{base}-{int(datetime.now(UTC).timestamp())}"

    @staticmethod
    def _has_required_legal_identity(supplier: Supplier) -> bool:
        return bool(
            supplier.legal_entity_type
            and (supplier.legal_registered_name or "").strip()
            and (supplier.legal_registration_code or "").strip()
            and (supplier.permit_license_type or "").strip()
            and (supplier.permit_license_number or "").strip()
        )
