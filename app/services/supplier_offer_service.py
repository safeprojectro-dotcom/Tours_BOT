from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import SupplierOfferLifecycle
from app.models.supplier import SupplierOffer
from app.repositories.supplier import SupplierOfferRepository
from app.schemas.supplier_admin import SupplierOfferCreate, SupplierOfferRead, SupplierOfferUpdate


class SupplierOfferNotFoundError(Exception):
    pass


class SupplierOfferReadinessError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOfferImmutableError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOfferLifecycleNotAllowedError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SupplierOfferService:
    def __init__(self) -> None:
        self._offers = SupplierOfferRepository()

    def _to_read(self, row: SupplierOffer) -> SupplierOfferRead:
        return SupplierOfferRead.model_validate(row, from_attributes=True)

    def _readiness_violation(self, offer: SupplierOffer) -> str | None:
        if not offer.title.strip():
            return "Title is required for publish-readiness."
        if not offer.description.strip():
            return "Description is required for publish-readiness."
        if not (offer.program_text or "").strip():
            return "Program text is required for publish-readiness."
        if offer.seats_total <= 0:
            return "Capacity (seats_total) must be greater than zero for publish-readiness."
        if offer.base_price is None:
            return "base_price is required for publish-readiness."
        if not (offer.currency or "").strip():
            return "currency is required for publish-readiness."
        if not (offer.vehicle_label or "").strip() and not (offer.transport_notes or "").strip():
            return "Provide vehicle_label and/or transport_notes for publish-readiness."
        if offer.return_datetime < offer.departure_datetime:
            return "return_datetime must not be before departure_datetime."
        return None

    def _ensure_consistent_ready_state(self, offer: SupplierOffer) -> None:
        if offer.lifecycle_status != SupplierOfferLifecycle.READY_FOR_MODERATION:
            return
        violation = self._readiness_violation(offer)
        if violation:
            raise SupplierOfferReadinessError(violation)

    def list_offers(self, session: Session, *, supplier_id: int, limit: int = 100, offset: int = 0) -> list[SupplierOfferRead]:
        rows = self._offers.list_for_supplier(session, supplier_id=supplier_id, limit=limit, offset=offset)
        return [self._to_read(r) for r in rows]

    def get_offer(self, session: Session, *, supplier_id: int, offer_id: int) -> SupplierOfferRead:
        row = self._offers.get_for_supplier(session, supplier_id=supplier_id, offer_id=offer_id)
        if row is None:
            raise SupplierOfferNotFoundError
        return self._to_read(row)

    def create_offer(self, session: Session, *, supplier_id: int, payload: SupplierOfferCreate) -> SupplierOfferRead:
        if payload.return_datetime < payload.departure_datetime:
            raise SupplierOfferReadinessError("return_datetime must not be before departure_datetime.")
        row = SupplierOffer(
            supplier_id=supplier_id,
            supplier_reference=payload.supplier_reference,
            title=payload.title,
            description=payload.description,
            program_text=payload.program_text,
            departure_datetime=payload.departure_datetime,
            return_datetime=payload.return_datetime,
            transport_notes=payload.transport_notes,
            vehicle_label=payload.vehicle_label,
            seats_total=payload.seats_total,
            base_price=payload.base_price,
            currency=payload.currency,
            service_composition=payload.service_composition,
            sales_mode=payload.sales_mode,
            payment_mode=payload.payment_mode,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)

    def _apply_update(self, row: SupplierOffer, payload: SupplierOfferUpdate) -> None:
        data = payload.model_dump(exclude_unset=True)
        new_lifecycle = data.pop("lifecycle_status", None)
        for key, value in data.items():
            setattr(row, key, value)
        if new_lifecycle is not None:
            self._assert_supplier_lifecycle(row, new_lifecycle)
            if new_lifecycle == SupplierOfferLifecycle.READY_FOR_MODERATION:
                violation = self._readiness_violation(row)
                if violation:
                    raise SupplierOfferReadinessError(violation)
            row.lifecycle_status = new_lifecycle

    def _assert_supplier_may_mutate(self, row: SupplierOffer) -> None:
        if row.lifecycle_status in (
            SupplierOfferLifecycle.APPROVED,
            SupplierOfferLifecycle.PUBLISHED,
        ):
            raise SupplierOfferImmutableError(
                "This offer is under platform publication control and cannot be edited via supplier admin.",
            )

    def _assert_supplier_lifecycle(self, row: SupplierOffer, new_status: SupplierOfferLifecycle) -> None:
        if new_status in (
            SupplierOfferLifecycle.APPROVED,
            SupplierOfferLifecycle.REJECTED,
            SupplierOfferLifecycle.PUBLISHED,
        ):
            raise SupplierOfferLifecycleNotAllowedError(
                "Suppliers cannot set moderation or publication statuses.",
            )
        allowed_pairs = {
            (SupplierOfferLifecycle.DRAFT, SupplierOfferLifecycle.DRAFT),
            (SupplierOfferLifecycle.DRAFT, SupplierOfferLifecycle.READY_FOR_MODERATION),
            (SupplierOfferLifecycle.READY_FOR_MODERATION, SupplierOfferLifecycle.DRAFT),
            (SupplierOfferLifecycle.READY_FOR_MODERATION, SupplierOfferLifecycle.READY_FOR_MODERATION),
            (SupplierOfferLifecycle.REJECTED, SupplierOfferLifecycle.DRAFT),
            (SupplierOfferLifecycle.REJECTED, SupplierOfferLifecycle.REJECTED),
            (SupplierOfferLifecycle.REJECTED, SupplierOfferLifecycle.READY_FOR_MODERATION),
        }
        key = (row.lifecycle_status, new_status)
        if key not in allowed_pairs:
            raise SupplierOfferLifecycleNotAllowedError(
                "Lifecycle transition is not allowed for suppliers in the current state.",
            )

    def update_offer(
        self,
        session: Session,
        *,
        supplier_id: int,
        offer_id: int,
        payload: SupplierOfferUpdate,
    ) -> SupplierOfferRead:
        row = self._offers.get_for_supplier(session, supplier_id=supplier_id, offer_id=offer_id)
        if row is None:
            raise SupplierOfferNotFoundError
        self._assert_supplier_may_mutate(row)
        self._apply_update(row, payload)
        if row.return_datetime < row.departure_datetime:
            raise SupplierOfferReadinessError("return_datetime must not be before departure_datetime.")
        self._ensure_consistent_ready_state(row)
        session.add(row)
        session.flush()
        session.refresh(row)
        return self._to_read(row)
