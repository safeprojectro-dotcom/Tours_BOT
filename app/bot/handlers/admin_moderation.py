"""Y28.1: Telegram admin moderation workspace (narrow operational client)."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import or_

from app.bot.constants import (
    ADMIN_OFFERS_ACTION_APPROVE,
    ADMIN_OFFERS_ACTION_CALLBACK_PREFIX,
    ADMIN_OFFERS_ACTION_CLOSE_LINK,
    ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK,
    ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK,
    ADMIN_OFFERS_ACTION_CREATE_LINK,
    ADMIN_OFFERS_EXEC_LINK_CONFIRM_PREFIX,
    ADMIN_OFFERS_EXEC_LINK_LIST_PREFIX,
    ADMIN_OFFERS_EXEC_LINK_MANUAL_PREFIX,
    ADMIN_OFFERS_EXEC_LINK_PICK_PREFIX,
    ADMIN_OFFERS_EXEC_LINK_SEARCH_LIST_PREFIX,
    ADMIN_OFFERS_EXEC_LINK_SEARCH_PREFIX,
    ADMIN_OFFERS_ACTION_LINK_STATUS,
    ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE,
    ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE,
    ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR,
    ADMIN_OFFERS_ACTION_PUBLISH,
    ADMIN_OFFERS_ACTION_REJECT,
    ADMIN_OFFERS_ACTION_REPLACE_LINK,
    ADMIN_OFFERS_ACTION_RETRACT,
    ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR,
    ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR,
    ADMIN_OFFERS_NAV_BACK,
    ADMIN_OFFERS_NAV_HOME,
    ADMIN_OFFERS_NAV_NEXT,
    ADMIN_OFFERS_NAV_PREV,
    ADMIN_OPS_ORDER_DETAIL_PREFIX,
    ADMIN_OPS_ORDERS_PAGE_PREFIX,
    ADMIN_OPS_REQUEST_DETAIL_PREFIX,
    ADMIN_OPS_REQUESTS_PAGE_PREFIX,
)
from app.bot.messages import translate
from app.bot.services import TelegramUserContextService
from app.bot.state import AdminModerationState
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import SupplierOfferLifecycle, TourStatus
from app.models.supplier import Supplier
from app.models.tour import Tour
from app.schemas.supplier_admin import SupplierOfferRead
from app.services.admin_read import AdminReadService
from app.services.custom_marketplace_request_service import (
    CustomMarketplaceRequestNotFoundError,
    CustomMarketplaceRequestService,
)
from app.services.supplier_offer_execution_link_service import (
    SupplierOfferExecutionLinkNotFoundError,
    SupplierOfferExecutionLinkService,
    SupplierOfferExecutionLinkValidationError,
)
from app.services.supplier_offer_moderation_service import (
    SupplierOfferModerationNotFoundError,
    SupplierOfferModerationService,
    SupplierOfferModerationStateError,
    SupplierOfferPublicationConfigError,
)
from app.services.supplier_offer_supplier_notification_service import SupplierOfferSupplierNotificationService

router = Router(name="admin-moderation")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

_QUEUE_LIMIT = 20
_QUEUE_MODE_MODERATION = "moderation"
_QUEUE_MODE_APPROVED = "approved"
_QUEUE_MODE_PUBLISHED = "published"
_LINK_TOUR_PAGE_SIZE = 5
_ADMIN_OPS_PAGE_SIZE = 5
_LINK_TOUR_SEARCH_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_LINK_SELECTION_ACTIONS = (
    ADMIN_OFFERS_ACTION_APPROVE,
    ADMIN_OFFERS_ACTION_REJECT,
    ADMIN_OFFERS_ACTION_PUBLISH,
    ADMIN_OFFERS_ACTION_RETRACT,
    ADMIN_OFFERS_ACTION_LINK_STATUS,
    ADMIN_OFFERS_ACTION_CLOSE_LINK,
    ADMIN_OFFERS_ACTION_CREATE_LINK,
    ADMIN_OFFERS_ACTION_REPLACE_LINK,
    ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK,
    ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK,
    ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE,
    ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE,
    ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR,
    ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR,
    ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR,
)


def _user_service() -> TelegramUserContextService:
    settings = get_settings()
    return TelegramUserContextService(supported_language_codes=settings.telegram_supported_language_codes)


def _is_admin_allowed(telegram_user_id: int) -> bool:
    return telegram_user_id in set(get_settings().telegram_admin_allowlist_ids)


def _status_key(status: SupplierOfferLifecycle) -> str:
    return f"supplier_offers_status_{status.value}"


def _action_button_rows(language_code: str | None, offer: SupplierOfferRead) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if offer.lifecycle_status == SupplierOfferLifecycle.READY_FOR_MODERATION:
        rows.append((translate(language_code, "admin_offer_action_approve"), f"{ADMIN_OFFERS_ACTION_APPROVE}:{offer.id}"))
        rows.append((translate(language_code, "admin_offer_action_reject"), f"{ADMIN_OFFERS_ACTION_REJECT}:{offer.id}"))
    if offer.lifecycle_status == SupplierOfferLifecycle.APPROVED:
        rows.append((translate(language_code, "admin_offer_action_publish"), f"{ADMIN_OFFERS_ACTION_PUBLISH}:{offer.id}"))
    if offer.lifecycle_status == SupplierOfferLifecycle.PUBLISHED:
        rows.append((translate(language_code, "admin_offer_action_retract"), f"{ADMIN_OFFERS_ACTION_RETRACT}:{offer.id}"))
        rows.append(
            (
                translate(language_code, "admin_offer_action_link_status"),
                f"{ADMIN_OFFERS_ACTION_LINK_STATUS}:{offer.id}",
            )
        )
    return rows


def _detail_keyboard(language_code: str | None, offer: SupplierOfferRead) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for title, action_payload in _action_button_rows(language_code, offer):
        kb.button(
            text=title,
            callback_data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{action_payload}",
        )
    kb.button(
        text=translate(language_code, "admin_ops_orders_button"),
        callback_data=f"{ADMIN_OPS_ORDERS_PAGE_PREFIX}0",
    )
    kb.button(
        text=translate(language_code, "admin_ops_requests_button"),
        callback_data=f"{ADMIN_OPS_REQUESTS_PAGE_PREFIX}0",
    )
    kb.button(text=translate(language_code, "admin_offer_nav_prev"), callback_data=ADMIN_OFFERS_NAV_PREV)
    kb.button(text=translate(language_code, "admin_offer_nav_next"), callback_data=ADMIN_OFFERS_NAV_NEXT)
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.button(text=translate(language_code, "admin_offer_nav_home"), callback_data=ADMIN_OFFERS_NAV_HOME)
    kb.adjust(2, 2, 2)
    return kb


def _short_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.isoformat(timespec="minutes").replace("T", " ")


def _truncate_line(value: str | None, *, max_len: int = 72) -> str:
    text = " ".join((value or "").split())
    if not text:
        return "-"
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1].rstrip()}…"


def _admin_ops_customer_display(*, customer_summary, customer_telegram_user_id: int | None, user_id: int) -> str:
    if customer_summary is not None and getattr(customer_summary, "summary_line", None):
        return _truncate_line(customer_summary.summary_line, max_len=100)
    if customer_telegram_user_id is not None:
        return f"customer: tg:{customer_telegram_user_id}"
    return f"customer: user_id:{user_id}"


def _admin_ops_orders_text(language_code: str | None, *, page: int, items: list) -> str:
    if not items:
        return translate(language_code, "admin_ops_orders_empty")
    lines = [translate(language_code, "admin_ops_orders_title", page=str(page + 1))]
    for item in items:
        lines.append(
            translate(
                language_code,
                "admin_ops_order_row",
                order_id=str(item.id),
                tour_code=item.tour_code or "-",
                status=f"{_enum_value(item.booking_status)}/{_enum_value(item.payment_status)}",
                customer=_admin_ops_customer_display(
                    customer_summary=getattr(item, "customer_summary", None),
                    customer_telegram_user_id=getattr(item, "customer_telegram_user_id", None),
                    user_id=item.user_id,
                ),
            )
        )
    return "\n".join(lines)


def _admin_ops_orders_keyboard(language_code: str | None, *, page: int, items: list, has_next: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for item in items:
        kb.button(
            text=translate(language_code, "admin_ops_order_view", order_id=str(item.id)),
            callback_data=f"{ADMIN_OPS_ORDER_DETAIL_PREFIX}{item.id}:{page}",
        )
    if page > 0:
        kb.button(text=translate(language_code, "admin_offer_nav_prev"), callback_data=f"{ADMIN_OPS_ORDERS_PAGE_PREFIX}{page - 1}")
    if has_next:
        kb.button(text=translate(language_code, "admin_offer_nav_next"), callback_data=f"{ADMIN_OPS_ORDERS_PAGE_PREFIX}{page + 1}")
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.adjust(1)
    return kb


def _admin_ops_order_detail_text(language_code: str | None, detail) -> str:
    csum = _admin_ops_customer_display(
        customer_summary=getattr(detail, "customer_summary", None),
        customer_telegram_user_id=getattr(detail, "customer_telegram_user_id", None),
        user_id=detail.user_id,
    )
    ctid = detail.customer_telegram_user_id
    return translate(
        language_code,
        "admin_ops_order_detail",
        order_id=str(detail.id),
        customer=csum,
        customer_telegram_id="-" if ctid is None else str(ctid),
        tour_id=str(detail.tour.id),
        tour_code=detail.tour.code,
        tour_title=detail.tour.title_default,
        departure=_short_dt(detail.tour.departure_datetime),
        seats=str(detail.seats_count),
        booking_status=_enum_value(detail.persistence_snapshot.booking_status),
        payment_status=_enum_value(detail.persistence_snapshot.payment_status),
        cancellation_status=_enum_value(detail.persistence_snapshot.cancellation_status),
        lifecycle=detail.lifecycle_summary,
        reservation_expires_at=_short_dt(detail.reservation_expires_at),
        created_at=_short_dt(detail.created_at),
        updated_at=_short_dt(detail.updated_at),
    )


def _admin_ops_detail_keyboard(language_code: str | None, *, list_callback: str) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=list_callback)
    kb.adjust(1)
    return kb


def _admin_ops_requests_text(language_code: str | None, *, page: int, items: list) -> str:
    if not items:
        return translate(language_code, "admin_ops_requests_empty")
    lines = [translate(language_code, "admin_ops_requests_title", page=str(page + 1))]
    for item in items:
        summary = item.operational_hints.scan_summary_line if item.operational_hints is not None else item.route_notes
        lines.append(
            translate(
                language_code,
                "admin_ops_request_row",
                request_id=str(item.id),
                status=_enum_value(item.status),
                customer=_admin_ops_customer_display(
                    customer_summary=getattr(item, "customer_summary", None),
                    customer_telegram_user_id=getattr(item, "customer_telegram_user_id", None),
                    user_id=item.user_id,
                ),
                summary=_truncate_line(summary),
            )
        )
    return "\n".join(lines)


def _admin_ops_requests_keyboard(language_code: str | None, *, page: int, items: list, has_next: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for item in items:
        kb.button(
            text=translate(language_code, "admin_ops_request_view", request_id=str(item.id)),
            callback_data=f"{ADMIN_OPS_REQUEST_DETAIL_PREFIX}{item.id}:{page}",
        )
    if page > 0:
        kb.button(text=translate(language_code, "admin_offer_nav_prev"), callback_data=f"{ADMIN_OPS_REQUESTS_PAGE_PREFIX}{page - 1}")
    if has_next:
        kb.button(text=translate(language_code, "admin_offer_nav_next"), callback_data=f"{ADMIN_OPS_REQUESTS_PAGE_PREFIX}{page + 1}")
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.adjust(1)
    return kb


def _admin_ops_request_detail_text(language_code: str | None, detail) -> str:
    request = detail.request
    bridge = detail.booking_bridge.bridge_status.value if detail.booking_bridge is not None else "-"
    travel_end = f" - {request.travel_date_end.isoformat()}" if request.travel_date_end is not None else ""
    ctid = detail.customer_telegram_user_id or request.customer_telegram_user_id
    csum = _admin_ops_customer_display(
        customer_summary=getattr(request, "customer_summary", None),
        customer_telegram_user_id=ctid,
        user_id=request.user_id,
    )
    return translate(
        language_code,
        "admin_ops_request_detail",
        request_id=str(request.id),
        customer=csum,
        customer_telegram_id="-" if ctid is None else str(ctid),
        status=_enum_value(request.status),
        request_type=_enum_value(request.request_type),
        travel_date=f"{request.travel_date_start.isoformat()}{travel_end}",
        group_size=str(request.group_size or "-"),
        route=_truncate_line(request.route_notes, max_len=300),
        selected_response=str(request.selected_supplier_response_id or "-"),
        bridge=bridge,
        created_at=_short_dt(request.created_at),
        updated_at=_short_dt(request.updated_at),
    )


def _queue_lifecycle(mode: str) -> SupplierOfferLifecycle:
    if mode == _QUEUE_MODE_APPROVED:
        return SupplierOfferLifecycle.APPROVED
    if mode == _QUEUE_MODE_PUBLISHED:
        return SupplierOfferLifecycle.PUBLISHED
    return SupplierOfferLifecycle.READY_FOR_MODERATION


def _queue_title_key(mode: str) -> str:
    if mode == _QUEUE_MODE_APPROVED:
        return "admin_offer_workspace_title_approved"
    if mode == _QUEUE_MODE_PUBLISHED:
        return "admin_offer_workspace_title_published"
    return "admin_offer_workspace_title"


def _queue_empty_key(mode: str) -> str:
    if mode == _QUEUE_MODE_APPROVED:
        return "admin_offer_workspace_empty_approved"
    if mode == _QUEUE_MODE_PUBLISHED:
        return "admin_offer_workspace_empty_published"
    return "admin_offer_workspace_empty"


def _load_queue_ids(session, *, mode: str) -> list[int]:
    items = SupplierOfferModerationService().list_offers(
        session,
        lifecycle_status=_queue_lifecycle(mode),
        limit=_QUEUE_LIMIT,
        offset=0,
    )
    return [offer.id for offer in items]


def _queue_text(language_code: str | None, *, offers: list[SupplierOfferRead], mode: str) -> str:
    lines = [translate(language_code, _queue_title_key(mode), count=str(len(offers)))]
    for offer in offers:
        lines.append(f"#{offer.id} · {translate(language_code, _status_key(offer.lifecycle_status))} · {offer.title}")
    return "\n".join(lines)


def _offer_detail_text(session, language_code: str | None, *, offer: SupplierOfferRead) -> str:
    supplier = session.get(Supplier, offer.supplier_id)
    supplier_label = supplier.display_name if supplier is not None else f"#{offer.supplier_id}"
    publication_key = (
        "admin_offer_publication_active"
        if offer.lifecycle_status == SupplierOfferLifecycle.PUBLISHED
        else "admin_offer_publication_inactive"
    )
    lines = [
        translate(language_code, "admin_offer_detail_title", offer_id=str(offer.id)),
        translate(language_code, "admin_offer_detail_supplier", supplier=supplier_label),
        translate(language_code, "admin_offer_detail_lifecycle", status=translate(language_code, _status_key(offer.lifecycle_status))),
        translate(language_code, "admin_offer_detail_publication", status=translate(language_code, publication_key)),
        translate(language_code, "admin_offer_detail_route", description=offer.description),
        translate(
            language_code,
            "admin_offer_detail_schedule",
            departure=offer.departure_datetime.isoformat(timespec="minutes").replace("T", " "),
            return_at=offer.return_datetime.isoformat(timespec="minutes").replace("T", " "),
        ),
        translate(
            language_code,
            "admin_offer_detail_price",
            price=str(offer.base_price) if offer.base_price is not None else "-",
            currency=offer.currency or "-",
            seats=str(offer.seats_total),
        ),
    ]
    if offer.moderation_rejection_reason:
        lines.append(
            translate(
                language_code,
                "admin_offer_detail_reject_reason",
                reason=offer.moderation_rejection_reason,
            )
        )
    return "\n".join(lines)


def _link_history_text(session, language_code: str | None, *, offer_id: int) -> tuple[str, bool]:
    links = SupplierOfferExecutionLinkService().list_links_for_offer(session, offer_id=offer_id)
    active = next((link for link in links if link.link_status == "active"), None)
    lines = [translate(language_code, "admin_offer_link_status_title", offer_id=str(offer_id))]
    if active is None:
        lines.append(translate(language_code, "admin_offer_link_status_none"))
    else:
        tour = session.get(Tour, active.tour_id)
        lines.append(
            translate(
                language_code,
                "admin_offer_link_status_active",
                tour_id=str(active.tour_id),
                tour_code=tour.code if tour is not None else "-",
                tour_status=getattr(tour.status, "value", str(tour.status)) if tour is not None else "-",
                sales_mode=getattr(tour.sales_mode, "value", str(tour.sales_mode)) if tour is not None else "-",
                seats_available=str(tour.seats_available) if tour is not None else "-",
                seats_total=str(tour.seats_total) if tour is not None else "-",
            )
        )

    if not links:
        lines.append(translate(language_code, "admin_offer_link_history_empty"))
    else:
        lines.append(translate(language_code, "admin_offer_link_history_title"))
        for link in links[:5]:
            lines.append(
                translate(
                    language_code,
                    "admin_offer_link_history_row",
                    link_id=str(link.id),
                    tour_id=str(link.tour_id),
                    status=link.link_status,
                    reason=link.close_reason or "-",
                    created_at=link.created_at.isoformat(timespec="minutes").replace("T", " "),
                    closed_at=link.closed_at.isoformat(timespec="minutes").replace("T", " ")
                    if link.closed_at is not None
                    else "-",
                )
            )
    return "\n".join(lines), active is not None


def _enum_value(value: object) -> str:
    return getattr(value, "value", str(value))


def _find_tour_for_link_input(session, text: str) -> Tour | None:
    normalized = text.strip()
    if normalized.isdecimal():
        return session.get(Tour, int(normalized))
    if not normalized:
        return None
    return session.query(Tour).filter(Tour.code == normalized).one_or_none()


def _parse_link_tour_search_input(text: str) -> tuple[str, date | None]:
    normalized = " ".join(text.strip().split())
    match = _LINK_TOUR_SEARCH_DATE_RE.search(normalized)
    if match is None:
        return normalized, None

    raw_date = match.group(0)
    query = " ".join(f"{normalized[: match.start()]} {normalized[match.end() :]}".split())
    try:
        return query, date.fromisoformat(raw_date)
    except ValueError:
        return query, None


def _link_tour_search_display(search_query: str, search_date: date | None) -> str:
    parts = [search_query.strip()]
    if search_date is not None:
        parts.append(search_date.isoformat())
    return " ".join(part for part in parts if part).strip()


def _has_active_execution_link(session, *, offer_id: int) -> bool:
    links = SupplierOfferExecutionLinkService().list_links_for_offer(session, offer_id=offer_id)
    return any(link.link_status == "active" for link in links)


def _link_target_preview_text(
    session,
    language_code: str | None,
    *,
    offer_id: int,
    tour: Tour,
) -> str:
    offer_row = SupplierOfferModerationService()._offers.get_any(session, offer_id=offer_id)
    offer_title = offer_row.title if offer_row is not None else f"#{offer_id}"
    offer_sales_mode = _enum_value(offer_row.sales_mode) if offer_row is not None else "-"
    return translate(
        language_code,
        "admin_offer_link_preview",
        offer_id=str(offer_id),
        offer_title=offer_title,
        offer_sales_mode=offer_sales_mode,
        tour_id=str(tour.id),
        tour_code=tour.code,
        tour_title=tour.title_default,
        tour_status=_enum_value(tour.status),
        tour_sales_mode=_enum_value(tour.sales_mode),
        seats_available=str(tour.seats_available),
        seats_total=str(tour.seats_total),
    )


def _link_confirm_keyboard(language_code: str | None, *, mode: str, offer_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    action = ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK if mode == "create" else ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK
    label_key = "admin_offer_link_confirm_create" if mode == "create" else "admin_offer_link_confirm_replace"
    kb.button(
        text=translate(language_code, label_key),
        callback_data=_link_action_callback(action, offer_id, mode),
    )
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.button(text=translate(language_code, "admin_offer_nav_home"), callback_data=ADMIN_OFFERS_NAV_HOME)
    kb.adjust(1, 2)
    return kb


def _link_action_callback(action: str, offer_id: int, *parts: object) -> str:
    if action == ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE:
        mode, page = parts
        return f"{ADMIN_OFFERS_EXEC_LINK_LIST_PREFIX}{offer_id}:{mode}:{page}"
    if action == ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE:
        mode, page = parts
        return f"{ADMIN_OFFERS_EXEC_LINK_SEARCH_LIST_PREFIX}{offer_id}:{mode}:{page}"
    if action == ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR:
        mode, tour_id = parts
        return f"{ADMIN_OFFERS_EXEC_LINK_PICK_PREFIX}{offer_id}:{mode}:{tour_id}"
    if action == ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR:
        (mode,) = parts
        return f"{ADMIN_OFFERS_EXEC_LINK_MANUAL_PREFIX}{offer_id}:{mode}"
    if action == ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR:
        (mode,) = parts
        return f"{ADMIN_OFFERS_EXEC_LINK_SEARCH_PREFIX}{offer_id}:{mode}"
    if action in (ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK, ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK):
        (mode,) = parts
        return f"{ADMIN_OFFERS_EXEC_LINK_CONFIRM_PREFIX}{offer_id}:{mode}"
    suffix = ":".join([action, str(offer_id), *(str(part) for part in parts)])
    return f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{suffix}"


def _compatible_tours_for_offer(
    session,
    *,
    offer_id: int,
    page: int,
    code_query: str | None = None,
    search_date: date | None = None,
) -> tuple[list[Tour], bool]:
    offer = SupplierOfferModerationService()._offers.get_any(session, offer_id=offer_id)
    if offer is None:
        raise SupplierOfferExecutionLinkNotFoundError
    offset = max(page, 0) * _LINK_TOUR_PAGE_SIZE
    query = (
        session.query(Tour)
        .filter(Tour.sales_mode == offer.sales_mode)
        .filter(Tour.status.notin_([TourStatus.CANCELLED, TourStatus.COMPLETED]))
        .filter(Tour.departure_datetime > datetime.now(UTC))
    )
    normalized_code_query = (code_query or "").strip()
    if normalized_code_query:
        query = query.filter(
            or_(
                Tour.code.ilike(f"%{normalized_code_query}%"),
                Tour.title_default.ilike(f"%{normalized_code_query}%"),
            )
        )
    if search_date is not None:
        start = datetime.combine(search_date, time.min, tzinfo=UTC)
        end = start + timedelta(days=1)
        query = query.filter(Tour.departure_datetime >= start).filter(Tour.departure_datetime < end)
    candidates = (
        query.order_by(Tour.departure_datetime.asc(), Tour.id.asc()).offset(offset).limit(_LINK_TOUR_PAGE_SIZE + 1).all()
    )
    return candidates[:_LINK_TOUR_PAGE_SIZE], len(candidates) > _LINK_TOUR_PAGE_SIZE


def _link_tour_candidates_text(
    language_code: str | None,
    *,
    offer_id: int,
    mode: str,
    page: int,
    tours: list[Tour],
) -> str:
    lines = [
        translate(
            language_code,
            "admin_offer_link_candidates_title",
            offer_id=str(offer_id),
            mode=mode,
            page=str(page + 1),
        )
    ]
    for tour in tours:
        lines.append(
            translate(
                language_code,
                "admin_offer_link_candidate_row",
                tour_id=str(tour.id),
                tour_code=tour.code,
                tour_title=tour.title_default,
                tour_status=_enum_value(tour.status),
                tour_sales_mode=_enum_value(tour.sales_mode),
                departure=tour.departure_datetime.isoformat(timespec="minutes").replace("T", " "),
                seats_available=str(tour.seats_available),
                seats_total=str(tour.seats_total),
            )
        )
    return "\n\n".join(lines)


def _link_tour_search_results_text(
    language_code: str | None,
    *,
    offer_id: int,
    mode: str,
    page: int,
    search_query: str,
    search_date: date | None,
    tours: list[Tour],
) -> str:
    lines = [
        translate(
            language_code,
            "admin_offer_link_search_results_title",
            offer_id=str(offer_id),
            mode=mode,
            query=search_query or "-",
            date=search_date.isoformat() if search_date is not None else "-",
            page=str(page + 1),
        )
    ]
    lines.append(
        _link_tour_candidates_text(language_code, offer_id=offer_id, mode=mode, page=page, tours=tours).split(
            "\n\n", 1
        )[1]
    )
    return "\n\n".join(lines)


def _link_tour_candidates_keyboard(
    language_code: str | None,
    *,
    offer_id: int,
    mode: str,
    page: int,
    tours: list[Tour],
    has_next: bool,
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for tour in tours:
        callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR, offer_id, mode, tour.id)
        kb.button(
            text=translate(language_code, "admin_offer_link_select_tour", tour_id=str(tour.id), tour_code=tour.code),
            callback_data=callback_data,
        )
    if page > 0:
        callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE, offer_id, mode, page - 1)
        kb.button(
            text=translate(language_code, "admin_offer_nav_prev"),
            callback_data=callback_data,
        )
    if has_next:
        callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE, offer_id, mode, page + 1)
        kb.button(
            text=translate(language_code, "admin_offer_nav_next"),
            callback_data=callback_data,
        )
    search_callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR, offer_id, mode)
    kb.button(
        text=translate(language_code, "admin_offer_link_search"),
        callback_data=search_callback_data,
    )
    callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR, offer_id, mode)
    kb.button(
        text=translate(language_code, "admin_offer_link_manual_input"),
        callback_data=callback_data,
    )
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.button(text=translate(language_code, "admin_offer_nav_home"), callback_data=ADMIN_OFFERS_NAV_HOME)
    kb.adjust(1)
    return kb


def _link_tour_search_results_keyboard(
    language_code: str | None,
    *,
    offer_id: int,
    mode: str,
    page: int,
    tours: list[Tour],
    has_next: bool,
) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for tour in tours:
        callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR, offer_id, mode, tour.id)
        kb.button(
            text=translate(language_code, "admin_offer_link_select_tour", tour_id=str(tour.id), tour_code=tour.code),
            callback_data=callback_data,
        )
    if page > 0:
        callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE, offer_id, mode, page - 1)
        kb.button(
            text=translate(language_code, "admin_offer_nav_prev"),
            callback_data=callback_data,
        )
    if has_next:
        callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE, offer_id, mode, page + 1)
        kb.button(
            text=translate(language_code, "admin_offer_nav_next"),
            callback_data=callback_data,
        )
    kb.button(
        text=translate(language_code, "admin_offer_link_new_search"),
        callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR, offer_id, mode),
    )
    kb.button(
        text=translate(language_code, "admin_offer_link_back_to_candidates"),
        callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE, offer_id, mode, 0),
    )
    kb.button(
        text=translate(language_code, "admin_offer_link_manual_input"),
        callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR, offer_id, mode),
    )
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.adjust(1)
    return kb


async def _show_link_tour_candidates(
    message,
    state: FSMContext,
    session,
    language_code: str | None,
    *,
    offer_id: int,
    mode: str,
    page: int = 0,
) -> None:
    page = max(page, 0)
    tours, has_next = _compatible_tours_for_offer(session, offer_id=offer_id, page=page)
    await state.set_state(AdminModerationState.awaiting_execution_link_tour)
    await state.update_data(
        current_offer_id=offer_id,
        pending_link_mode=mode,
        pending_link_offer_id=offer_id,
        pending_link_tour_id=None,
        pending_link_page=page,
        pending_link_code_query=None,
        pending_link_search_query=None,
        pending_link_search_date=None,
    )
    if not tours:
        kb = InlineKeyboardBuilder()
        search_callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR, offer_id, mode)
        kb.button(
            text=translate(language_code, "admin_offer_link_search"),
            callback_data=search_callback_data,
        )
        manual_callback_data = _link_action_callback(ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR, offer_id, mode)
        kb.button(
            text=translate(language_code, "admin_offer_link_manual_input"),
            callback_data=manual_callback_data,
        )
        kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
        kb.button(text=translate(language_code, "admin_offer_nav_home"), callback_data=ADMIN_OFFERS_NAV_HOME)
        kb.adjust(1)
        await message.answer(
            translate(language_code, "admin_offer_link_candidates_empty", offer_id=str(offer_id)),
            reply_markup=kb.as_markup(),
        )
        return
    await message.answer(
        _link_tour_candidates_text(language_code, offer_id=offer_id, mode=mode, page=page, tours=tours),
        reply_markup=_link_tour_candidates_keyboard(
            language_code,
            offer_id=offer_id,
            mode=mode,
            page=page,
            tours=tours,
            has_next=has_next,
        ).as_markup(),
    )


async def _show_link_tour_code_search_results(
    message,
    state: FSMContext,
    session,
    language_code: str | None,
    *,
    offer_id: int,
    mode: str,
    search_query: str,
    search_date: date | None = None,
    page: int = 0,
) -> None:
    page = max(page, 0)
    normalized_search_query = search_query.strip()
    search_display = _link_tour_search_display(normalized_search_query, search_date)
    if not search_display:
        kb = InlineKeyboardBuilder()
        kb.button(
            text=translate(language_code, "admin_offer_link_new_search"),
            callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR, offer_id, mode),
        )
        kb.button(
            text=translate(language_code, "admin_offer_link_back_to_candidates"),
            callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE, offer_id, mode, 0),
        )
        kb.button(
            text=translate(language_code, "admin_offer_link_manual_input"),
            callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR, offer_id, mode),
        )
        kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
        kb.adjust(1)
        await message.answer(
            translate(language_code, "admin_offer_link_search_empty", query=search_display),
            reply_markup=kb.as_markup(),
        )
        return
    tours, has_next = _compatible_tours_for_offer(
        session,
        offer_id=offer_id,
        page=page,
        code_query=normalized_search_query,
        search_date=search_date,
    )
    await state.set_state(AdminModerationState.awaiting_execution_link_tour)
    await state.update_data(
        current_offer_id=offer_id,
        pending_link_mode=mode,
        pending_link_offer_id=offer_id,
        pending_link_tour_id=None,
        pending_link_page=page,
        pending_link_code_query=search_display,
        pending_link_search_query=normalized_search_query,
        pending_link_search_date=search_date.isoformat() if search_date is not None else None,
    )
    if not tours:
        kb = InlineKeyboardBuilder()
        kb.button(
            text=translate(language_code, "admin_offer_link_new_search"),
            callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR, offer_id, mode),
        )
        kb.button(
            text=translate(language_code, "admin_offer_link_back_to_candidates"),
            callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE, offer_id, mode, 0),
        )
        kb.button(
            text=translate(language_code, "admin_offer_link_manual_input"),
            callback_data=_link_action_callback(ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR, offer_id, mode),
        )
        kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
        kb.adjust(1)
        await message.answer(
            translate(language_code, "admin_offer_link_search_empty", query=search_display),
            reply_markup=kb.as_markup(),
        )
        return
    await message.answer(
        _link_tour_search_results_text(
            language_code,
            offer_id=offer_id,
            mode=mode,
            page=page,
            search_query=normalized_search_query,
            search_date=search_date,
            tours=tours,
        ),
        reply_markup=_link_tour_search_results_keyboard(
            language_code,
            offer_id=offer_id,
            mode=mode,
            page=page,
            tours=tours,
            has_next=has_next,
        ).as_markup(),
    )


def _link_status_keyboard(language_code: str | None, *, offer_id: int, has_active_link: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if has_active_link:
        kb.button(
            text=translate(language_code, "admin_offer_action_replace_link"),
            callback_data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_REPLACE_LINK}:{offer_id}",
        )
        kb.button(
            text=translate(language_code, "admin_offer_action_close_link"),
            callback_data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CLOSE_LINK}:{offer_id}",
        )
    else:
        kb.button(
            text=translate(language_code, "admin_offer_action_create_link"),
            callback_data=f"{ADMIN_OFFERS_ACTION_CALLBACK_PREFIX}{ADMIN_OFFERS_ACTION_CREATE_LINK}:{offer_id}",
        )
    kb.button(text=translate(language_code, "admin_offer_nav_back"), callback_data=ADMIN_OFFERS_NAV_BACK)
    kb.button(text=translate(language_code, "admin_offer_nav_home"), callback_data=ADMIN_OFFERS_NAV_HOME)
    kb.adjust(1, 2)
    return kb


async def _deny_if_not_allowed(message: Message | CallbackQuery, *, language_code: str | None) -> bool:
    from_user = message.from_user
    if from_user is None or _is_admin_allowed(from_user.id):
        return False
    text = translate(language_code, "admin_offer_gate_denied")
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
    current_offer_id: int | None,
    queue_mode: str,
) -> None:
    await state.set_state(AdminModerationState.browsing_offer_queue)
    await state.update_data(
        queue_offer_ids=queue_ids,
        queue_index=queue_index,
        current_offer_id=current_offer_id,
        queue_mode=queue_mode,
    )


async def _show_current_offer(message: Message, state: FSMContext, *, language_code: str | None) -> None:
    data = await state.get_data()
    current_offer_id = data.get("current_offer_id")
    if not isinstance(current_offer_id, int):
        await message.answer(translate(language_code, "admin_offer_no_current"))
        return
    with SessionLocal() as session:
        offer_row = SupplierOfferModerationService()._offers.get_any(session, offer_id=current_offer_id)
        if offer_row is None:
            await message.answer(translate(language_code, "admin_offer_no_current"))
            return
        offer = SupplierOfferModerationService()._to_read(offer_row)
        detail_text = _offer_detail_text(session, language_code, offer=offer)
        await message.answer(detail_text, reply_markup=_detail_keyboard(language_code, offer).as_markup())


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
        offers = [
            SupplierOfferModerationService()._to_read(row)
            for row in [SupplierOfferModerationService()._offers.get_any(session, offer_id=oid) for oid in queue_ids]
            if row is not None
        ]
        await _store_queue_state(
            state,
            queue_ids=queue_ids,
            queue_index=0,
            current_offer_id=queue_ids[0],
            queue_mode=queue_mode,
        )
        await message.answer(_queue_text(lg, offers=offers, mode=queue_mode))
        current = offers[0]
        await message.answer(
            _offer_detail_text(session, lg, offer=current),
            reply_markup=_detail_keyboard(lg, current).as_markup(),
        )


@router.message(Command("admin_ops", "admin_offers", "admin_queue"))
async def cmd_admin_offers(message: Message, state: FSMContext) -> None:
    await _open_queue(message, state, queue_mode=_QUEUE_MODE_MODERATION)


@router.message(Command("admin_approved"))
async def cmd_admin_approved(message: Message, state: FSMContext) -> None:
    await _open_queue(message, state, queue_mode=_QUEUE_MODE_APPROVED)


@router.message(Command("admin_published"))
async def cmd_admin_published(message: Message, state: FSMContext) -> None:
    await _open_queue(message, state, queue_mode=_QUEUE_MODE_PUBLISHED)


async def _show_admin_ops_orders(message, language_code: str | None, *, page: int) -> None:
    page = max(page, 0)
    with SessionLocal() as session:
        result = AdminReadService().list_orders(
            session,
            limit=_ADMIN_OPS_PAGE_SIZE + 1,
            offset=page * _ADMIN_OPS_PAGE_SIZE,
        )
    items = result.items[:_ADMIN_OPS_PAGE_SIZE]
    has_next = len(result.items) > _ADMIN_OPS_PAGE_SIZE
    await message.answer(
        _admin_ops_orders_text(language_code, page=page, items=items),
        reply_markup=_admin_ops_orders_keyboard(
            language_code,
            page=page,
            items=items,
            has_next=has_next,
        ).as_markup(),
    )


async def _show_admin_ops_requests(message, language_code: str | None, *, page: int) -> None:
    page = max(page, 0)
    with SessionLocal() as session:
        items_full = CustomMarketplaceRequestService().list_for_admin(
            session,
            limit=_ADMIN_OPS_PAGE_SIZE + 1,
            offset=page * _ADMIN_OPS_PAGE_SIZE,
        )
    items = items_full[:_ADMIN_OPS_PAGE_SIZE]
    has_next = len(items_full) > _ADMIN_OPS_PAGE_SIZE
    await message.answer(
        _admin_ops_requests_text(language_code, page=page, items=items),
        reply_markup=_admin_ops_requests_keyboard(
            language_code,
            page=page,
            items=items,
            has_next=has_next,
        ).as_markup(),
    )


@router.message(Command("admin_orders"))
async def cmd_admin_orders(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
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
    await _show_admin_ops_orders(message, lg, page=0)


@router.message(Command("admin_requests"))
async def cmd_admin_requests(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
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
    await _show_admin_ops_requests(message, lg, page=0)


@router.callback_query(
    F.data.startswith(ADMIN_OPS_ORDERS_PAGE_PREFIX)
    | F.data.startswith(ADMIN_OPS_ORDER_DETAIL_PREFIX)
    | F.data.startswith(ADMIN_OPS_REQUESTS_PAGE_PREFIX)
    | F.data.startswith(ADMIN_OPS_REQUEST_DETAIL_PREFIX)
)
async def admin_ops_read_navigation(query: CallbackQuery, state: FSMContext) -> None:
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

    if query.data.startswith(ADMIN_OPS_ORDERS_PAGE_PREFIX):
        raw_page = query.data.removeprefix(ADMIN_OPS_ORDERS_PAGE_PREFIX)
        page = int(raw_page) if raw_page.isdigit() else 0
        await _show_admin_ops_orders(query.message, lg, page=page)
        await query.answer()
        return

    if query.data.startswith(ADMIN_OPS_REQUESTS_PAGE_PREFIX):
        raw_page = query.data.removeprefix(ADMIN_OPS_REQUESTS_PAGE_PREFIX)
        page = int(raw_page) if raw_page.isdigit() else 0
        await _show_admin_ops_requests(query.message, lg, page=page)
        await query.answer()
        return

    if query.data.startswith(ADMIN_OPS_ORDER_DETAIL_PREFIX):
        raw = query.data.removeprefix(ADMIN_OPS_ORDER_DETAIL_PREFIX).split(":")
        order_id = int(raw[0]) if raw and raw[0].isdigit() else 0
        page = int(raw[1]) if len(raw) > 1 and raw[1].isdigit() else 0
        with SessionLocal() as session:
            detail = AdminReadService().get_order_detail(session, order_id=order_id)
        if detail is None:
            await query.message.answer(translate(lg, "admin_offer_no_current"))
            await query.answer()
            return
        await query.message.answer(
            _admin_ops_order_detail_text(lg, detail),
            reply_markup=_admin_ops_detail_keyboard(
                lg,
                list_callback=f"{ADMIN_OPS_ORDERS_PAGE_PREFIX}{page}",
            ).as_markup(),
        )
        await query.answer()
        return

    if query.data.startswith(ADMIN_OPS_REQUEST_DETAIL_PREFIX):
        raw = query.data.removeprefix(ADMIN_OPS_REQUEST_DETAIL_PREFIX).split(":")
        request_id = int(raw[0]) if raw and raw[0].isdigit() else 0
        page = int(raw[1]) if len(raw) > 1 and raw[1].isdigit() else 0
        try:
            with SessionLocal() as session:
                detail = CustomMarketplaceRequestService().get_admin_detail(session, request_id=request_id)
        except CustomMarketplaceRequestNotFoundError:
            await query.message.answer(translate(lg, "admin_offer_no_current"))
            await query.answer()
            return
        await query.message.answer(
            _admin_ops_request_detail_text(lg, detail),
            reply_markup=_admin_ops_detail_keyboard(
                lg,
                list_callback=f"{ADMIN_OPS_REQUESTS_PAGE_PREFIX}{page}",
            ).as_markup(),
        )
        await query.answer()


@router.callback_query(F.data.in_({ADMIN_OFFERS_NAV_HOME, ADMIN_OFFERS_NAV_BACK, ADMIN_OFFERS_NAV_NEXT, ADMIN_OFFERS_NAV_PREV}))
async def admin_queue_navigation(query: CallbackQuery, state: FSMContext) -> None:
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
    if query.data == ADMIN_OFFERS_NAV_HOME:
        await state.clear()
        await query.message.answer(translate(lg, "admin_offer_workspace_home"))
        await query.answer()
        return
    if query.data == ADMIN_OFFERS_NAV_BACK:
        data = await state.get_data()
        queue_ids = [x for x in data.get("queue_offer_ids", []) if isinstance(x, int)]
        queue_mode = str(data.get("queue_mode") or _QUEUE_MODE_MODERATION)
        with SessionLocal() as session:
            offers = [
                SupplierOfferModerationService()._to_read(row)
                for row in [SupplierOfferModerationService()._offers.get_any(session, offer_id=oid) for oid in queue_ids]
                if row is not None
            ]
        if offers:
            await query.message.answer(_queue_text(lg, offers=offers, mode=queue_mode))
        else:
            await query.message.answer(translate(lg, _queue_empty_key(queue_mode)))
        await query.answer()
        return

    data = await state.get_data()
    queue_ids = [x for x in data.get("queue_offer_ids", []) if isinstance(x, int)]
    queue_mode = str(data.get("queue_mode") or _QUEUE_MODE_MODERATION)
    if not queue_ids:
        await query.message.answer(translate(lg, "admin_offer_no_current"))
        await query.answer()
        return
    idx_raw = data.get("queue_index", 0)
    idx = idx_raw if isinstance(idx_raw, int) else 0
    if query.data == ADMIN_OFFERS_NAV_NEXT:
        idx = (idx + 1) % len(queue_ids)
    else:
        idx = (idx - 1) % len(queue_ids)
    current_offer_id = queue_ids[idx]
    await _store_queue_state(
        state,
        queue_ids=queue_ids,
        queue_index=idx,
        current_offer_id=current_offer_id,
        queue_mode=queue_mode,
    )
    with SessionLocal() as session:
        row = SupplierOfferModerationService()._offers.get_any(session, offer_id=current_offer_id)
        if row is None:
            await query.message.answer(translate(lg, "admin_offer_no_current"))
            await query.answer()
            return
        offer = SupplierOfferModerationService()._to_read(row)
        await query.message.answer(
            _offer_detail_text(session, lg, offer=offer),
            reply_markup=_detail_keyboard(lg, offer).as_markup(),
        )
    await query.answer()


def _parse_action(data: str) -> tuple[str, int, tuple[str, ...]] | None:
    if data.startswith(ADMIN_OFFERS_EXEC_LINK_CONFIRM_PREFIX):
        parts = data.removeprefix(ADMIN_OFFERS_EXEC_LINK_CONFIRM_PREFIX).split(":")
        if len(parts) != 2:
            return None
        mode = parts[1]
        if mode == "create":
            action_name = ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK
        elif mode == "replace":
            action_name = ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK
        else:
            return None
        try:
            return action_name, int(parts[0]), ()
        except ValueError:
            return None

    compact_prefixes = {
        ADMIN_OFFERS_EXEC_LINK_LIST_PREFIX: ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE,
        ADMIN_OFFERS_EXEC_LINK_SEARCH_LIST_PREFIX: ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE,
        ADMIN_OFFERS_EXEC_LINK_PICK_PREFIX: ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR,
        ADMIN_OFFERS_EXEC_LINK_MANUAL_PREFIX: ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR,
        ADMIN_OFFERS_EXEC_LINK_SEARCH_PREFIX: ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR,
    }
    for prefix, action_name in compact_prefixes.items():
        if not data.startswith(prefix):
            continue
        parts = data.removeprefix(prefix).split(":")
        if not parts:
            return None
        try:
            return action_name, int(parts[0]), tuple(parts[1:])
        except ValueError:
            return None

    raw = data.removeprefix(ADMIN_OFFERS_ACTION_CALLBACK_PREFIX)
    for action_name in sorted(_LINK_SELECTION_ACTIONS, key=len, reverse=True):
        prefix = f"{action_name}:"
        if not raw.startswith(prefix):
            continue
        parts = raw.removeprefix(prefix).split(":")
        if not parts:
            return None
        try:
            return action_name, int(parts[0]), tuple(parts[1:])
        except ValueError:
            return None
    return None


def _refresh_queue(current_offer_id: int, *, session, mode: str) -> tuple[list[int], int, int]:
    queue_ids = _load_queue_ids(session, mode=mode)
    if queue_ids:
        if current_offer_id in queue_ids:
            idx = queue_ids.index(current_offer_id)
            return queue_ids, idx, current_offer_id
        idx = 0
        return queue_ids, idx, queue_ids[0]
    return [], 0, current_offer_id


@router.callback_query(
    F.data.startswith(ADMIN_OFFERS_ACTION_CALLBACK_PREFIX)
    | F.data.startswith(ADMIN_OFFERS_EXEC_LINK_LIST_PREFIX)
    | F.data.startswith(ADMIN_OFFERS_EXEC_LINK_SEARCH_LIST_PREFIX)
    | F.data.startswith(ADMIN_OFFERS_EXEC_LINK_PICK_PREFIX)
    | F.data.startswith(ADMIN_OFFERS_EXEC_LINK_MANUAL_PREFIX)
    | F.data.startswith(ADMIN_OFFERS_EXEC_LINK_SEARCH_PREFIX)
    | F.data.startswith(ADMIN_OFFERS_EXEC_LINK_CONFIRM_PREFIX)
)
async def admin_offer_action(query: CallbackQuery, state: FSMContext) -> None:
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
                "admin_offer_action_unavailable",
                detail=f"Unknown action payload: {query.data}",
            )
        )
        await query.answer()
        return
    action_name, offer_id, action_args = parsed
    moderation = SupplierOfferModerationService()
    try:
        with SessionLocal() as session:
            data = await state.get_data()
            queue_mode = str(data.get("queue_mode") or _QUEUE_MODE_MODERATION)
            if action_name == ADMIN_OFFERS_ACTION_REJECT:
                await state.set_state(AdminModerationState.awaiting_reject_reason)
                await state.update_data(current_offer_id=offer_id, reject_offer_id=offer_id)
                await query.message.answer(translate(lg, "admin_offer_reject_prompt", offer_id=str(offer_id)))
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_LINK_STATUS:
                text, has_active = _link_history_text(session, lg, offer_id=offer_id)
                await query.message.answer(
                    text,
                    reply_markup=_link_status_keyboard(lg, offer_id=offer_id, has_active_link=has_active).as_markup(),
                )
                await query.answer()
                return
            if action_name in (ADMIN_OFFERS_ACTION_CREATE_LINK, ADMIN_OFFERS_ACTION_REPLACE_LINK):
                mode = "create" if action_name == ADMIN_OFFERS_ACTION_CREATE_LINK else "replace"
                has_active = _has_active_execution_link(session, offer_id=offer_id)
                if mode == "create" and has_active:
                    await query.message.answer(translate(lg, "admin_offer_link_create_active_exists"))
                    await query.answer()
                    return
                if mode == "replace" and not has_active:
                    await query.message.answer(translate(lg, "admin_offer_link_close_missing"))
                    await query.answer()
                    return
                await _show_link_tour_candidates(
                    query.message,
                    state,
                    session,
                    lg,
                    offer_id=offer_id,
                    mode=mode,
                    page=0,
                )
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_LINK_TOUR_PAGE:
                if len(action_args) != 2:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                mode = action_args[0]
                try:
                    page = int(action_args[1])
                except ValueError:
                    page = 0
                if mode not in {"create", "replace"}:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                await _show_link_tour_candidates(
                    query.message,
                    state,
                    session,
                    lg,
                    offer_id=offer_id,
                    mode=mode,
                    page=page,
                )
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_LINK_TOUR_SEARCH_PAGE:
                if len(action_args) != 2:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                mode = action_args[0]
                try:
                    page = int(action_args[1])
                except ValueError:
                    page = 0
                if mode not in {"create", "replace"}:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                code_query = str(data.get("pending_link_code_query") or "").strip()
                search_query = str(data.get("pending_link_search_query") or code_query).strip()
                raw_search_date = data.get("pending_link_search_date")
                try:
                    search_date = date.fromisoformat(raw_search_date) if isinstance(raw_search_date, str) else None
                except ValueError:
                    search_date = None
                if not code_query:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                await _show_link_tour_code_search_results(
                    query.message,
                    state,
                    session,
                    lg,
                    offer_id=offer_id,
                    mode=mode,
                    search_query=search_query,
                    search_date=search_date,
                    page=page,
                )
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_SEARCH_LINK_TOUR:
                mode = action_args[0] if action_args else None
                if mode not in {"create", "replace"}:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                await state.set_state(AdminModerationState.awaiting_execution_link_tour_code_search)
                await state.update_data(
                    current_offer_id=offer_id,
                    pending_link_mode=mode,
                    pending_link_offer_id=offer_id,
                    pending_link_tour_id=None,
                    pending_link_code_query=None,
                    pending_link_search_query=None,
                    pending_link_search_date=None,
                )
                await query.message.answer(translate(lg, "admin_offer_link_search_prompt", offer_id=str(offer_id)))
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_MANUAL_LINK_TOUR:
                mode = action_args[0] if action_args else None
                if mode not in {"create", "replace"}:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                await state.set_state(AdminModerationState.awaiting_execution_link_tour)
                await state.update_data(
                    current_offer_id=offer_id,
                    pending_link_mode=mode,
                    pending_link_offer_id=offer_id,
                    pending_link_code_query=None,
                    pending_link_search_query=None,
                    pending_link_search_date=None,
                )
                await query.message.answer(translate(lg, "admin_offer_link_target_prompt", offer_id=str(offer_id)))
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_SELECT_LINK_TOUR:
                if len(action_args) != 2:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                mode = action_args[0]
                try:
                    tour_id = int(action_args[1])
                except ValueError:
                    await query.message.answer(translate(lg, "admin_offer_link_target_missing"))
                    await query.answer()
                    return
                if mode not in {"create", "replace"}:
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                service = SupplierOfferExecutionLinkService()
                service._validate_link_target(session, offer_id=offer_id, tour_id=tour_id)
                if mode == "create" and _has_active_execution_link(session, offer_id=offer_id):
                    await query.message.answer(translate(lg, "admin_offer_link_create_active_exists"))
                    await query.answer()
                    return
                tour = session.get(Tour, tour_id)
                if tour is None:
                    await query.message.answer(translate(lg, "admin_offer_link_target_missing"))
                    await query.answer()
                    return
                await state.set_state(AdminModerationState.awaiting_execution_link_tour)
                await state.update_data(
                    current_offer_id=offer_id,
                    pending_link_mode=mode,
                    pending_link_offer_id=offer_id,
                    pending_link_tour_id=tour_id,
                )
                await query.message.answer(
                    _link_target_preview_text(session, lg, offer_id=offer_id, tour=tour),
                    reply_markup=_link_confirm_keyboard(lg, mode=mode, offer_id=offer_id).as_markup(),
                )
                await query.answer()
                return
            if action_name in (ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK, ADMIN_OFFERS_ACTION_CONFIRM_REPLACE_LINK):
                mode = "create" if action_name == ADMIN_OFFERS_ACTION_CONFIRM_CREATE_LINK else "replace"
                pending_offer_id = data.get("pending_link_offer_id")
                pending_tour_id = data.get("pending_link_tour_id")
                pending_mode = data.get("pending_link_mode")
                if pending_offer_id != offer_id or pending_mode != mode or not isinstance(pending_tour_id, int):
                    await query.message.answer(translate(lg, "admin_offer_link_confirm_missing"))
                    await query.answer()
                    return
                service = SupplierOfferExecutionLinkService()
                if mode == "create":
                    service.create_link_for_offer(
                        session,
                        offer_id=offer_id,
                        tour_id=pending_tour_id,
                        link_note="telegram-admin:create",
                    )
                    done_key = "admin_offer_link_create_done"
                else:
                    service.replace_link_for_offer(
                        session,
                        offer_id=offer_id,
                        tour_id=pending_tour_id,
                        link_note="telegram-admin:replace",
                    )
                    done_key = "admin_offer_link_replace_done"
                session.commit()
                await state.set_state(AdminModerationState.browsing_offer_queue)
                await state.update_data(
                    current_offer_id=offer_id,
                    pending_link_mode=None,
                    pending_link_offer_id=None,
                    pending_link_tour_id=None,
                    pending_link_code_query=None,
                    pending_link_search_query=None,
                    pending_link_search_date=None,
                )
                await query.message.answer(
                    translate(lg, done_key, offer_id=str(offer_id), tour_id=str(pending_tour_id))
                )
                text, has_active = _link_history_text(session, lg, offer_id=offer_id)
                await query.message.answer(
                    text,
                    reply_markup=_link_status_keyboard(lg, offer_id=offer_id, has_active_link=has_active).as_markup(),
                )
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_CLOSE_LINK:
                SupplierOfferExecutionLinkService().close_active_link(
                    session,
                    offer_id=offer_id,
                    reason="unlinked",
                )
                session.commit()
                await query.message.answer(translate(lg, "admin_offer_link_close_done", offer_id=str(offer_id)))
                text, has_active = _link_history_text(session, lg, offer_id=offer_id)
                await query.message.answer(
                    text,
                    reply_markup=_link_status_keyboard(lg, offer_id=offer_id, has_active_link=has_active).as_markup(),
                )
                await query.answer()
                return
            if action_name == ADMIN_OFFERS_ACTION_APPROVE:
                moderation.approve(session, offer_id=offer_id)
                session.commit()
                try:
                    SupplierOfferSupplierNotificationService().notify_approved(session, offer_id=offer_id)
                except Exception:
                    pass
                done_key = "admin_offer_action_done_approve"
            elif action_name == ADMIN_OFFERS_ACTION_PUBLISH:
                moderation.publish(session, offer_id=offer_id)
                session.commit()
                try:
                    SupplierOfferSupplierNotificationService().notify_published(session, offer_id=offer_id)
                except Exception:
                    pass
                done_key = "admin_offer_action_done_publish"
            elif action_name == ADMIN_OFFERS_ACTION_RETRACT:
                moderation.retract_published(session, offer_id=offer_id)
                SupplierOfferExecutionLinkService().close_active_link(
                    session,
                    offer_id=offer_id,
                    reason="retracted",
                    allow_missing=True,
                )
                session.commit()
                try:
                    SupplierOfferSupplierNotificationService().notify_retracted(session, offer_id=offer_id)
                except Exception:
                    pass
                done_key = "admin_offer_action_done_retract"
            else:
                await query.message.answer(
                    translate(
                        lg,
                        "admin_offer_action_unavailable",
                        detail=f"Unknown action: {action_name}",
                    )
                )
                await query.answer()
                return
            queue_ids, idx, current_offer_id = _refresh_queue(offer_id, session=session, mode=queue_mode)
            await _store_queue_state(
                state,
                queue_ids=queue_ids,
                queue_index=idx,
                current_offer_id=current_offer_id,
                queue_mode=queue_mode,
            )
            await query.message.answer(translate(lg, done_key, offer_id=str(offer_id)))
            row = moderation._offers.get_any(session, offer_id=current_offer_id)
            if row is not None:
                offer = moderation._to_read(row)
                await query.message.answer(
                    _offer_detail_text(session, lg, offer=offer),
                    reply_markup=_detail_keyboard(lg, offer).as_markup(),
                )
            elif not queue_ids:
                await state.clear()
                await query.message.answer(translate(lg, _queue_empty_key(queue_mode)))
    except SupplierOfferExecutionLinkNotFoundError:
        await query.message.answer(translate(lg, "admin_offer_link_close_missing"))
    except (
        SupplierOfferModerationNotFoundError,
        SupplierOfferModerationStateError,
        SupplierOfferPublicationConfigError,
        SupplierOfferExecutionLinkValidationError,
    ) as exc:
        detail = getattr(exc, "message", str(exc))
        await query.message.answer(translate(lg, "admin_offer_action_unavailable", detail=detail))
    await query.answer()


@router.message(AdminModerationState.awaiting_execution_link_tour)
async def admin_offer_execution_link_tour_input(message: Message, state: FSMContext) -> None:
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
        await message.answer(translate(lg, "admin_offer_workspace_home"))
        return
    data = await state.get_data()
    offer_id = data.get("pending_link_offer_id")
    mode = data.get("pending_link_mode")
    if not isinstance(offer_id, int) or mode not in {"create", "replace"}:
        await message.answer(translate(lg, "admin_offer_link_confirm_missing"))
        return
    if folded in {"back", "inapoi", "înapoi"}:
        await state.set_state(AdminModerationState.browsing_offer_queue)
        await state.update_data(
            pending_link_mode=None,
            pending_link_offer_id=None,
            pending_link_tour_id=None,
            pending_link_code_query=None,
            pending_link_search_query=None,
            pending_link_search_date=None,
        )
        with SessionLocal() as session:
            status_text, has_active = _link_history_text(session, lg, offer_id=offer_id)
            await message.answer(
                status_text,
                reply_markup=_link_status_keyboard(lg, offer_id=offer_id, has_active_link=has_active).as_markup(),
            )
        return

    try:
        with SessionLocal() as session:
            tour = _find_tour_for_link_input(session, text)
            if tour is None:
                await message.answer(translate(lg, "admin_offer_link_target_missing"))
                return
            service = SupplierOfferExecutionLinkService()
            service._validate_link_target(session, offer_id=offer_id, tour_id=tour.id)
            if mode == "create" and _has_active_execution_link(session, offer_id=offer_id):
                await message.answer(translate(lg, "admin_offer_link_create_active_exists"))
                return
            await state.update_data(pending_link_tour_id=tour.id)
            await message.answer(
                _link_target_preview_text(session, lg, offer_id=offer_id, tour=tour),
                reply_markup=_link_confirm_keyboard(lg, mode=mode, offer_id=offer_id).as_markup(),
            )
    except SupplierOfferExecutionLinkNotFoundError:
        await message.answer(translate(lg, "admin_offer_action_unavailable", detail="Supplier offer not found."))
    except SupplierOfferExecutionLinkValidationError as exc:
        await message.answer(translate(lg, "admin_offer_action_unavailable", detail=exc.message))


@router.message(AdminModerationState.awaiting_execution_link_tour_code_search)
async def admin_offer_execution_link_tour_code_search_input(message: Message, state: FSMContext) -> None:
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
        await message.answer(translate(lg, "admin_offer_workspace_home"))
        return
    data = await state.get_data()
    offer_id = data.get("pending_link_offer_id")
    mode = data.get("pending_link_mode")
    if not isinstance(offer_id, int) or mode not in {"create", "replace"}:
        await message.answer(translate(lg, "admin_offer_link_confirm_missing"))
        return
    if folded in {"back", "inapoi", "înapoi"}:
        with SessionLocal() as session:
            await _show_link_tour_candidates(
                message,
                state,
                session,
                lg,
                offer_id=offer_id,
                mode=mode,
                page=0,
            )
        return
    if not text:
        await message.answer(translate(lg, "admin_offer_link_search_empty", query=text))
        return
    search_query, search_date = _parse_link_tour_search_input(text)
    try:
        with SessionLocal() as session:
            await _show_link_tour_code_search_results(
                message,
                state,
                session,
                lg,
                offer_id=offer_id,
                mode=mode,
                search_query=search_query,
                search_date=search_date,
                page=0,
            )
    except SupplierOfferExecutionLinkNotFoundError:
        await message.answer(translate(lg, "admin_offer_action_unavailable", detail="Supplier offer not found."))


@router.message(AdminModerationState.awaiting_reject_reason)
async def admin_offer_reject_reason(message: Message, state: FSMContext) -> None:
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
        await message.answer(translate(lg, "admin_offer_workspace_home"))
        return
    if folded in {"back", "inapoi", "înapoi"}:
        await state.set_state(AdminModerationState.browsing_offer_queue)
        await _show_current_offer(message, state, language_code=lg)
        return
    if len(text) < 3:
        await message.answer(translate(lg, "admin_offer_reject_reason_too_short"))
        return
    data = await state.get_data()
    reject_offer_id = data.get("reject_offer_id") or data.get("current_offer_id")
    if not isinstance(reject_offer_id, int):
        await message.answer(translate(lg, "admin_offer_no_current"))
        return
    moderation = SupplierOfferModerationService()
    try:
        with SessionLocal() as session:
            queue_mode = str(data.get("queue_mode") or _QUEUE_MODE_MODERATION)
            moderation.reject(session, offer_id=reject_offer_id, reason=text)
            session.commit()
            try:
                SupplierOfferSupplierNotificationService().notify_rejected(
                    session,
                    offer_id=reject_offer_id,
                    reason=text,
                )
            except Exception:
                pass
            queue_ids, idx, current_offer_id = _refresh_queue(reject_offer_id, session=session, mode=queue_mode)
            await _store_queue_state(
                state,
                queue_ids=queue_ids,
                queue_index=idx,
                current_offer_id=current_offer_id,
                queue_mode=queue_mode,
            )
            await state.update_data(reject_offer_id=None)
            await message.answer(translate(lg, "admin_offer_action_done_reject", offer_id=str(reject_offer_id)))
            row = moderation._offers.get_any(session, offer_id=current_offer_id)
            if row is not None:
                offer = moderation._to_read(row)
                await message.answer(
                    _offer_detail_text(session, lg, offer=offer),
                    reply_markup=_detail_keyboard(lg, offer).as_markup(),
                )
            elif not queue_ids:
                await state.clear()
                await message.answer(translate(lg, _queue_empty_key(queue_mode)))
    except (SupplierOfferModerationNotFoundError, SupplierOfferModerationStateError) as exc:
        detail = getattr(exc, "message", str(exc))
        await message.answer(translate(lg, "admin_offer_action_unavailable", detail=detail))
