"""Y29.3: Telegram admin supplier-profile moderation workspace (narrow operational client)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from app.bot.constants import (
    ADMIN_SUPPLIERS_ACTION_APPROVE,
    ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX,
    ADMIN_SUPPLIERS_ACTION_REACTIVATE,
    ADMIN_SUPPLIERS_ACTION_REJECT,
    ADMIN_SUPPLIERS_ACTION_REVOKE,
    ADMIN_SUPPLIERS_ACTION_SUSPEND,
    ADMIN_SUPPLIERS_NAV_BACK,
    ADMIN_SUPPLIERS_NAV_HOME,
    ADMIN_SUPPLIERS_NAV_NEXT,
    ADMIN_SUPPLIERS_NAV_PREV,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.bot.state import AdminSupplierModerationState
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SupplierOnboardingStatus
from app.models.supplier import Supplier
from app.services.supplier_onboarding_service import (
    SupplierOnboardingApprovalValidationError,
    SupplierOnboardingNotFoundError,
    SupplierOnboardingService,
    SupplierOnboardingStatusTransitionError,
)

router = Router(name="admin-supplier-moderation")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

_QUEUE_LIMIT = 30
_QUEUE_MODE_PENDING = "pending"
_QUEUE_MODE_OPERATIONS = "operations"


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _is_admin_allowed(telegram_user_id: int) -> bool:
    return telegram_user_id in set(get_settings().telegram_admin_allowlist_ids)


def _status_key(status: SupplierOnboardingStatus) -> str:
    return f"admin_supplier_status_{status.value}"


def _queue_title_key(mode: str) -> str:
    if mode == _QUEUE_MODE_OPERATIONS:
        return "admin_supplier_workspace_title_operations"
    return "admin_supplier_workspace_title_pending"


def _queue_empty_key(mode: str) -> str:
    if mode == _QUEUE_MODE_OPERATIONS:
        return "admin_supplier_workspace_empty_operations"
    return "admin_supplier_workspace_empty_pending"


def _queue_statuses(mode: str) -> tuple[SupplierOnboardingStatus, ...]:
    if mode == _QUEUE_MODE_OPERATIONS:
        return (
            SupplierOnboardingStatus.APPROVED,
            SupplierOnboardingStatus.SUSPENDED,
            SupplierOnboardingStatus.REVOKED,
        )
    return (SupplierOnboardingStatus.PENDING_REVIEW,)


def _load_queue_ids(session, *, mode: str) -> list[int]:
    stmt = (
        select(Supplier.id)
        .where(Supplier.onboarding_status.in_(_queue_statuses(mode)))
        .order_by(Supplier.updated_at.desc(), Supplier.id.desc())
        .limit(_QUEUE_LIMIT)
    )
    return list(session.scalars(stmt).all())


def _queue_text(language_code: str | None, *, suppliers: list[Supplier], mode: str) -> str:
    lines = [translate(language_code, _queue_title_key(mode), count=str(len(suppliers)))]
    for supplier in suppliers:
        lines.append(
            translate(
                language_code,
                "admin_supplier_workspace_line",
                supplier_id=str(supplier.id),
                status=translate(language_code, _status_key(supplier.onboarding_status)),
                display_name=supplier.display_name,
            )
        )
    return "\n".join(lines)


def _action_button_rows(language_code: str | None, supplier: Supplier) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if supplier.onboarding_status == SupplierOnboardingStatus.PENDING_REVIEW:
        rows.append((translate(language_code, "admin_supplier_action_approve"), f"{ADMIN_SUPPLIERS_ACTION_APPROVE}:{supplier.id}"))
        rows.append((translate(language_code, "admin_supplier_action_reject"), f"{ADMIN_SUPPLIERS_ACTION_REJECT}:{supplier.id}"))
    if supplier.onboarding_status == SupplierOnboardingStatus.APPROVED:
        rows.append((translate(language_code, "admin_supplier_action_suspend"), f"{ADMIN_SUPPLIERS_ACTION_SUSPEND}:{supplier.id}"))
        rows.append((translate(language_code, "admin_supplier_action_revoke"), f"{ADMIN_SUPPLIERS_ACTION_REVOKE}:{supplier.id}"))
    if supplier.onboarding_status == SupplierOnboardingStatus.SUSPENDED:
        rows.append((translate(language_code, "admin_supplier_action_reactivate"), f"{ADMIN_SUPPLIERS_ACTION_REACTIVATE}:{supplier.id}"))
        rows.append((translate(language_code, "admin_supplier_action_revoke"), f"{ADMIN_SUPPLIERS_ACTION_REVOKE}:{supplier.id}"))
    return rows


def _detail_keyboard(language_code: str | None, supplier: Supplier) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for title, action_payload in _action_button_rows(language_code, supplier):
        kb.button(
            text=title,
            callback_data=f"{ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX}{action_payload}",
        )
    kb.button(text=translate(language_code, "admin_supplier_nav_prev"), callback_data=ADMIN_SUPPLIERS_NAV_PREV)
    kb.button(text=translate(language_code, "admin_supplier_nav_next"), callback_data=ADMIN_SUPPLIERS_NAV_NEXT)
    kb.button(text=translate(language_code, "admin_supplier_nav_back"), callback_data=ADMIN_SUPPLIERS_NAV_BACK)
    kb.button(text=translate(language_code, "admin_supplier_nav_home"), callback_data=ADMIN_SUPPLIERS_NAV_HOME)
    kb.adjust(2, 2, 2)
    return kb


def _legal_summary(language_code: str | None, supplier: Supplier) -> str:
    entity = supplier.legal_entity_type.value if supplier.legal_entity_type is not None else "-"
    return translate(
        language_code,
        "admin_supplier_detail_legal_summary",
        entity=entity,
        registered_name=supplier.legal_registered_name or "-",
        registration_code=supplier.legal_registration_code or "-",
        permit=f"{supplier.permit_license_type or '-'} / {supplier.permit_license_number or '-'}",
    )


def _supplier_detail_text(language_code: str | None, *, supplier: Supplier) -> str:
    lines = [
        translate(language_code, "admin_supplier_detail_title", supplier_id=str(supplier.id)),
        translate(language_code, "admin_supplier_detail_name", display_name=supplier.display_name),
        translate(
            language_code,
            "admin_supplier_detail_telegram",
            telegram_user_id=str(supplier.primary_telegram_user_id) if supplier.primary_telegram_user_id is not None else "-",
        ),
        translate(
            language_code,
            "admin_supplier_detail_status",
            status=translate(language_code, _status_key(supplier.onboarding_status)),
        ),
        _legal_summary(language_code, supplier),
    ]
    if supplier.onboarding_rejection_reason:
        lines.append(
            translate(
                language_code,
                "admin_supplier_detail_reject_reason",
                reason=supplier.onboarding_rejection_reason,
            )
        )
    if supplier.onboarding_suspension_reason:
        lines.append(
            translate(
                language_code,
                "admin_supplier_detail_suspend_reason",
                reason=supplier.onboarding_suspension_reason,
            )
        )
    if supplier.onboarding_revocation_reason:
        lines.append(
            translate(
                language_code,
                "admin_supplier_detail_revoke_reason",
                reason=supplier.onboarding_revocation_reason,
            )
        )
    return "\n".join(lines)


async def _deny_if_not_allowed(message: Message | CallbackQuery, *, language_code: str | None) -> bool:
    from_user = message.from_user
    if from_user is None or _is_admin_allowed(from_user.id):
        return False
    text = translate(language_code, "admin_supplier_gate_denied")
    if isinstance(message, CallbackQuery):
        if message.message is not None:
            await message.message.answer(text)
        await message.answer()
    else:
        await message.answer(text)
    return True


async def _store_queue_state(
    state: FSMContext,
    *,
    queue_ids: list[int],
    queue_index: int,
    current_supplier_id: int | None,
    queue_mode: str,
) -> None:
    await state.set_state(AdminSupplierModerationState.browsing_supplier_queue)
    await state.update_data(
        supplier_queue_ids=queue_ids,
        supplier_queue_index=queue_index,
        current_supplier_id=current_supplier_id,
        supplier_queue_mode=queue_mode,
    )


async def _show_current_supplier(message: Message, state: FSMContext, *, language_code: str | None) -> None:
    data = await state.get_data()
    current_supplier_id = data.get("current_supplier_id")
    if not isinstance(current_supplier_id, int):
        await message.answer(translate(language_code, "admin_supplier_no_current"))
        return
    with SessionLocal() as session:
        supplier = session.get(Supplier, current_supplier_id)
        if supplier is None:
            await message.answer(translate(language_code, "admin_supplier_no_current"))
            return
        await message.answer(
            _supplier_detail_text(language_code, supplier=supplier),
            reply_markup=_detail_keyboard(language_code, supplier).as_markup(),
        )


async def _open_queue(message: Message, state: FSMContext, *, queue_mode: str) -> None:
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
    if await _deny_if_not_allowed(message, language_code=lg):
        await state.clear()
        return
    with SessionLocal() as session:
        queue_ids = _load_queue_ids(session, mode=queue_mode)
        if not queue_ids:
            await state.clear()
            await message.answer(translate(lg, _queue_empty_key(queue_mode)))
            return
        suppliers = [session.get(Supplier, supplier_id) for supplier_id in queue_ids]
        suppliers = [s for s in suppliers if s is not None]
        await _store_queue_state(
            state,
            queue_ids=queue_ids,
            queue_index=0,
            current_supplier_id=queue_ids[0],
            queue_mode=queue_mode,
        )
        await message.answer(_queue_text(lg, suppliers=suppliers, mode=queue_mode))
        current = suppliers[0]
        await message.answer(
            _supplier_detail_text(lg, supplier=current),
            reply_markup=_detail_keyboard(lg, current).as_markup(),
        )


@router.message(Command("admin_supplier_queue"))
async def cmd_admin_supplier_queue(message: Message, state: FSMContext) -> None:
    await _open_queue(message, state, queue_mode=_QUEUE_MODE_PENDING)


@router.message(Command("admin_suppliers"))
async def cmd_admin_suppliers(message: Message, state: FSMContext) -> None:
    await _open_queue(message, state, queue_mode=_QUEUE_MODE_OPERATIONS)


@router.callback_query(
    F.data.in_(
        {
            ADMIN_SUPPLIERS_NAV_HOME,
            ADMIN_SUPPLIERS_NAV_BACK,
            ADMIN_SUPPLIERS_NAV_NEXT,
            ADMIN_SUPPLIERS_NAV_PREV,
        }
    )
)
async def admin_supplier_navigation(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.data is None or query.message is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    if await _deny_if_not_allowed(query, language_code=lg):
        await state.clear()
        return
    if query.data == ADMIN_SUPPLIERS_NAV_HOME:
        await state.clear()
        await query.message.answer(translate(lg, "admin_supplier_workspace_home"))
        await query.answer()
        return
    if query.data == ADMIN_SUPPLIERS_NAV_BACK:
        data = await state.get_data()
        queue_ids = [x for x in data.get("supplier_queue_ids", []) if isinstance(x, int)]
        queue_mode = str(data.get("supplier_queue_mode") or _QUEUE_MODE_PENDING)
        with SessionLocal() as session:
            suppliers = [session.get(Supplier, supplier_id) for supplier_id in queue_ids]
            suppliers = [s for s in suppliers if s is not None]
        if suppliers:
            await query.message.answer(_queue_text(lg, suppliers=suppliers, mode=queue_mode))
        else:
            await query.message.answer(translate(lg, _queue_empty_key(queue_mode)))
        await query.answer()
        return

    data = await state.get_data()
    queue_ids = [x for x in data.get("supplier_queue_ids", []) if isinstance(x, int)]
    queue_mode = str(data.get("supplier_queue_mode") or _QUEUE_MODE_PENDING)
    if not queue_ids:
        await query.message.answer(translate(lg, "admin_supplier_no_current"))
        await query.answer()
        return
    idx_raw = data.get("supplier_queue_index", 0)
    idx = idx_raw if isinstance(idx_raw, int) else 0
    if query.data == ADMIN_SUPPLIERS_NAV_NEXT:
        idx = (idx + 1) % len(queue_ids)
    else:
        idx = (idx - 1) % len(queue_ids)
    current_supplier_id = queue_ids[idx]
    await _store_queue_state(
        state,
        queue_ids=queue_ids,
        queue_index=idx,
        current_supplier_id=current_supplier_id,
        queue_mode=queue_mode,
    )
    with SessionLocal() as session:
        supplier = session.get(Supplier, current_supplier_id)
        if supplier is None:
            await query.message.answer(translate(lg, "admin_supplier_no_current"))
            await query.answer()
            return
        await query.message.answer(
            _supplier_detail_text(lg, supplier=supplier),
            reply_markup=_detail_keyboard(lg, supplier).as_markup(),
        )
    await query.answer()


def _parse_action(data: str) -> tuple[str, int] | None:
    raw = data.removeprefix(ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX)
    parts = raw.rsplit(":", 1)
    if len(parts) != 2:
        return None
    action_name, supplier_id_raw = parts
    try:
        return action_name, int(supplier_id_raw)
    except ValueError:
        return None


def _refresh_queue(current_supplier_id: int, *, session, mode: str) -> tuple[list[int], int, int]:
    queue_ids = _load_queue_ids(session, mode=mode)
    if queue_ids:
        if current_supplier_id in queue_ids:
            idx = queue_ids.index(current_supplier_id)
            return queue_ids, idx, current_supplier_id
        idx = 0
        return queue_ids, idx, queue_ids[0]
    return [], 0, current_supplier_id


@router.callback_query(F.data.startswith(ADMIN_SUPPLIERS_ACTION_CALLBACK_PREFIX))
async def admin_supplier_action(query: CallbackQuery, state: FSMContext) -> None:
    if query.from_user is None or query.data is None or query.message is None:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=query.from_user.id,
            telegram_language_code=query.from_user.language_code,
        )
    if await _deny_if_not_allowed(query, language_code=lg):
        await state.clear()
        return
    parsed = _parse_action(query.data)
    if parsed is None:
        await query.message.answer(
            translate(
                lg,
                "admin_supplier_action_unavailable",
                detail=f"Unknown action payload: {query.data}",
            )
        )
        await query.answer()
        return
    action_name, supplier_id = parsed
    svc = SupplierOnboardingService()
    try:
        with SessionLocal() as session:
            data = await state.get_data()
            queue_mode = str(data.get("supplier_queue_mode") or _QUEUE_MODE_PENDING)
            if action_name in {
                ADMIN_SUPPLIERS_ACTION_REJECT,
                ADMIN_SUPPLIERS_ACTION_SUSPEND,
                ADMIN_SUPPLIERS_ACTION_REVOKE,
            }:
                await state.set_state(AdminSupplierModerationState.awaiting_reason)
                await state.update_data(
                    current_supplier_id=supplier_id,
                    reason_supplier_id=supplier_id,
                    reason_action_name=action_name,
                )
                prompt_key = {
                    ADMIN_SUPPLIERS_ACTION_REJECT: "admin_supplier_reason_prompt_reject",
                    ADMIN_SUPPLIERS_ACTION_SUSPEND: "admin_supplier_reason_prompt_suspend",
                    ADMIN_SUPPLIERS_ACTION_REVOKE: "admin_supplier_reason_prompt_revoke",
                }[action_name]
                await query.message.answer(translate(lg, prompt_key, supplier_id=str(supplier_id)))
                await query.answer()
                return

            if action_name == ADMIN_SUPPLIERS_ACTION_APPROVE:
                svc.admin_approve(session, supplier_id=supplier_id)
                done_key = "admin_supplier_action_done_approve"
            elif action_name == ADMIN_SUPPLIERS_ACTION_REACTIVATE:
                svc.admin_reactivate(session, supplier_id=supplier_id)
                done_key = "admin_supplier_action_done_reactivate"
            else:
                await query.message.answer(
                    translate(
                        lg,
                        "admin_supplier_action_unavailable",
                        detail=f"Unknown action: {action_name}",
                    )
                )
                await query.answer()
                return

            session.commit()
            queue_ids, idx, current_supplier_id = _refresh_queue(supplier_id, session=session, mode=queue_mode)
            await _store_queue_state(
                state,
                queue_ids=queue_ids,
                queue_index=idx,
                current_supplier_id=current_supplier_id,
                queue_mode=queue_mode,
            )
            await query.message.answer(translate(lg, done_key, supplier_id=str(supplier_id)))
            row = session.get(Supplier, current_supplier_id)
            if row is not None:
                await query.message.answer(
                    _supplier_detail_text(lg, supplier=row),
                    reply_markup=_detail_keyboard(lg, row).as_markup(),
                )
            elif not queue_ids:
                await state.clear()
                await query.message.answer(translate(lg, _queue_empty_key(queue_mode)))
    except (
        SupplierOnboardingNotFoundError,
        SupplierOnboardingStatusTransitionError,
        SupplierOnboardingApprovalValidationError,
    ) as exc:
        detail = getattr(exc, "message", str(exc))
        await query.message.answer(translate(lg, "admin_supplier_action_unavailable", detail=detail))
    await query.answer()


@router.message(AdminSupplierModerationState.awaiting_reason)
async def admin_supplier_reason(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not message.text:
        return
    with SessionLocal() as session:
        lg = _user_service().resolve_language(
            session,
            telegram_user_id=message.from_user.id,
            telegram_language_code=message.from_user.language_code,
        )
    if await _deny_if_not_allowed(message, language_code=lg):
        await state.clear()
        return

    text = message.text.strip()
    folded = text.casefold()
    if folded in {"home", "acasa", "acasă"}:
        await state.clear()
        await message.answer(translate(lg, "admin_supplier_workspace_home"))
        return
    if folded in {"back", "inapoi", "înapoi"}:
        await state.set_state(AdminSupplierModerationState.browsing_supplier_queue)
        await _show_current_supplier(message, state, language_code=lg)
        return
    if len(text) < 3:
        await message.answer(translate(lg, "admin_supplier_reason_too_short"))
        return

    data = await state.get_data()
    reason_supplier_id = data.get("reason_supplier_id") or data.get("current_supplier_id")
    reason_action_name = data.get("reason_action_name")
    if not isinstance(reason_supplier_id, int) or not isinstance(reason_action_name, str):
        await message.answer(translate(lg, "admin_supplier_no_current"))
        return

    svc = SupplierOnboardingService()
    try:
        with SessionLocal() as session:
            queue_mode = str(data.get("supplier_queue_mode") or _QUEUE_MODE_PENDING)
            if reason_action_name == ADMIN_SUPPLIERS_ACTION_REJECT:
                svc.admin_reject(session, supplier_id=reason_supplier_id, reason=text)
                done_key = "admin_supplier_action_done_reject"
            elif reason_action_name == ADMIN_SUPPLIERS_ACTION_SUSPEND:
                svc.admin_suspend(session, supplier_id=reason_supplier_id, reason=text)
                done_key = "admin_supplier_action_done_suspend"
            elif reason_action_name == ADMIN_SUPPLIERS_ACTION_REVOKE:
                svc.admin_revoke(session, supplier_id=reason_supplier_id, reason=text)
                done_key = "admin_supplier_action_done_revoke"
            else:
                await message.answer(
                    translate(
                        lg,
                        "admin_supplier_action_unavailable",
                        detail=f"Unknown reason action: {reason_action_name}",
                    )
                )
                return
            session.commit()
            queue_ids, idx, current_supplier_id = _refresh_queue(reason_supplier_id, session=session, mode=queue_mode)
            await _store_queue_state(
                state,
                queue_ids=queue_ids,
                queue_index=idx,
                current_supplier_id=current_supplier_id,
                queue_mode=queue_mode,
            )
            await state.update_data(reason_supplier_id=None, reason_action_name=None)
            await message.answer(translate(lg, done_key, supplier_id=str(reason_supplier_id)))
            row = session.get(Supplier, current_supplier_id)
            if row is not None:
                await message.answer(
                    _supplier_detail_text(lg, supplier=row),
                    reply_markup=_detail_keyboard(lg, row).as_markup(),
                )
            elif not queue_ids:
                await state.clear()
                await message.answer(translate(lg, _queue_empty_key(queue_mode)))
    except (
        SupplierOnboardingNotFoundError,
        SupplierOnboardingStatusTransitionError,
        SupplierOnboardingApprovalValidationError,
    ) as exc:
        detail = getattr(exc, "message", str(exc))
        await message.answer(translate(lg, "admin_supplier_action_unavailable", detail=detail))
