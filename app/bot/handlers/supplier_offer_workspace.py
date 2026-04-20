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
    await state.clear()
    if not offers:
        await message.answer(translate(lg, "supplier_offers_workspace_empty"))
        return
    lines = [translate(lg, "supplier_offers_workspace_title")]
    for offer in offers:
        status_label = translate(lg, _status_key(offer.lifecycle_status))
        lines.append(
            translate(
                lg,
                "supplier_offers_workspace_line",
                offer_id=str(offer.id),
                status=status_label,
                title=offer.title,
                updated_at=offer.updated_at.isoformat(timespec="minutes").replace("T", " "),
            )
        )
        if offer.lifecycle_status == SupplierOfferLifecycle.REJECTED and offer.moderation_rejection_reason:
            lines.append(
                translate(
                    lg,
                    "supplier_offers_workspace_reject_reason",
                    reason=offer.moderation_rejection_reason,
                )
            )
    await message.answer("\n\n".join(lines))
