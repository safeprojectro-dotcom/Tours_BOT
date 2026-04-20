"""Y2.3: narrow supplier read-side workspace for own offers/statuses."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SupplierOfferLifecycle, SupplierOnboardingStatus
from app.models.supplier import Supplier
from app.services.supplier_offer_operational_alerts import SupplierOfferOperationalAlertService
from app.services.supplier_offer_execution_link_service import SupplierOfferExecutionLinkService
from app.services.supplier_offer_service import SupplierOfferService
from app.services.supplier_onboarding_service import SupplierOnboardingService

router = Router(name="supplier-offer-workspace")
router.message.filter(F.chat.type == "private")


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _supplier_access_status(supplier: Supplier | None) -> str:
    if supplier is None:
        return "not_onboarded"
    if supplier.onboarding_status == SupplierOnboardingStatus.APPROVED:
        return "approved"
    if supplier.onboarding_status == SupplierOnboardingStatus.PENDING_REVIEW:
        return "pending"
    return "rejected"


def _gate_message_key(status_code: str) -> str:
    return {
        "not_onboarded": "supplier_offer_gate_not_onboarded",
        "pending": "supplier_offer_gate_pending",
        "rejected": "supplier_offer_gate_rejected",
    }[status_code]


def _status_key(status: SupplierOfferLifecycle) -> str:
    return f"supplier_offers_status_{status.value}"


def _offer_operational_lines(language_code: str | None, *, offer, execution_metrics=None) -> list[str]:
    """
    Return narrow, supplier-safe operational signals.

    We intentionally do not compute sold/hold/payment aggregates here because the current
    data model has no authoritative offer->Layer A execution linkage. Showing synthetic
    booking math in bot layer would be misleading.
    """
    declared_capacity = offer.seats_total if execution_metrics is None else execution_metrics.declared_capacity
    lines = [translate(language_code, "supplier_offers_operational_declared_capacity", seats_total=str(declared_capacity))]
    is_published = offer.lifecycle_status == SupplierOfferLifecycle.PUBLISHED
    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_publication_active" if is_published else "supplier_offers_operational_publication_inactive",
        )
    )
    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_progress_hint",
            hint=translate(
                language_code,
                "supplier_offers_operational_progress_published" if is_published else "supplier_offers_operational_progress_unpublished",
            ),
        )
    )
    if execution_metrics is None:
        lines.append(translate(language_code, "supplier_offers_operational_live_stats_not_available"))
        return lines

    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_occupied_capacity",
            seats=str(execution_metrics.occupied_capacity),
        )
    )
    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_remaining_capacity",
            seats=str(execution_metrics.remaining_capacity),
        )
    )
    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_active_reserved_hold_seats",
            seats=str(execution_metrics.active_reserved_hold_seats),
        )
    )
    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_confirmed_paid_seats",
            seats=str(execution_metrics.confirmed_paid_seats),
        )
    )
    lines.append(
        translate(
            language_code,
            "supplier_offers_operational_sold_out",
            value=translate(
                language_code,
                "supplier_offers_operational_yes" if execution_metrics.sold_out else "supplier_offers_operational_no",
            ),
        )
    )
    return lines


def _offer_alert_lines(language_code: str | None, *, offer) -> list[str]:
    alerts = SupplierOfferOperationalAlertService().alerts_for_offer(offer=offer)
    if not alerts:
        return []
    lines: list[str] = []
    for alert in alerts:
        lines.append(
            translate(
                language_code,
                "supplier_offers_alert_line",
                alert=translate(language_code, f"supplier_offers_alert_{alert.code}"),
            )
        )
    return lines


@router.message(Command("supplier_offers"))
async def cmd_supplier_offers(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    with SessionLocal() as session:
        user = _user_service().sync_private_user(
            session,
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            telegram_language_code=message.from_user.language_code,
        )
        session.commit()
        lg = user.preferred_language or message.from_user.language_code
        supplier = SupplierOnboardingService().get_by_telegram_user_id(session, telegram_user_id=message.from_user.id)
        status_code = _supplier_access_status(supplier)
        if status_code != "approved":
            await state.clear()
            await message.answer(translate(lg, _gate_message_key(status_code)))
            return
        offers = SupplierOfferService().list_offers(session, supplier_id=supplier.id, limit=20, offset=0)
        metrics_service = SupplierOfferExecutionLinkService()
        rendered_items: list[list[str]] = []
        for offer in offers:
            execution_metrics = None
            if offer.lifecycle_status == SupplierOfferLifecycle.PUBLISHED:
                execution_metrics = metrics_service.active_metrics_for_offer(session, offer_id=offer.id)
            one = [
                translate(
                    lg,
                    "supplier_offers_workspace_line",
                    offer_id=str(offer.id),
                    status=translate(lg, _status_key(offer.lifecycle_status)),
                    title=offer.title,
                    updated_at=offer.updated_at.isoformat(timespec="minutes").replace("T", " "),
                )
            ]
            one.extend(_offer_operational_lines(lg, offer=offer, execution_metrics=execution_metrics))
            one.extend(_offer_alert_lines(lg, offer=offer))
            if offer.lifecycle_status == SupplierOfferLifecycle.REJECTED and offer.moderation_rejection_reason:
                one.append(
                    translate(
                        lg,
                        "supplier_offers_workspace_reject_reason",
                        reason=offer.moderation_rejection_reason,
                    )
                )
            rendered_items.append(one)
    await state.clear()
    if not offers:
        await message.answer(translate(lg, "supplier_offers_workspace_empty"))
        return
    lines = [translate(lg, "supplier_offers_workspace_title")]
    for block in rendered_items:
        lines.extend(block)
    await message.answer("\n\n".join(lines))
