from __future__ import annotations

import re
import json
import logging
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, unquote_plus, urlsplit

import flet as ft
import httpx

from app.models.enums import (
    CustomRequestBookingBridgeStatus,
    CustomerCommercialMode,
    PaymentStatus,
    TourSalesMode,
    TourStatus,
)
from app.schemas.custom_marketplace import (
    MiniAppCustomRequestCustomerDetailRead,
    MiniAppCustomRequestCustomerListRead,
    MiniAppCustomRequestCustomerSummaryRead,
)
from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingFacadeState,
    MiniAppBookingListItemRead,
    MiniAppBookingPrimaryCta,
    MiniAppBookingsListRead,
    MiniAppBridgeExecutionPreparationResponse,
    MiniAppBridgePaymentEligibilityRead,
    MiniAppCatalogRead,
    MiniAppReservationPreparationRead,
    MiniAppSupplierOfferActionabilityState,
    MiniAppSupplierOfferLandingRead,
    MiniAppTourDetailRead,
    MiniAppWaitlistStatusRead,
)
from app.schemas.payment import PaymentReconciliationRead
from app.schemas.prepared import (
    CatalogTourCardRead,
    OrderSummaryRead,
    PaymentEntryRead,
    ReservationPreparationSummaryRead,
)
from app.schemas.tour import BoardingPointRead
from mini_app.api_client import MiniAppApiClient
from mini_app.booking_grouping import partition_bookings_for_my_bookings_ui
from mini_app.config import get_mini_app_settings
from mini_app.custom_request_context import (
    CustomRequestPrefill,
    prefill_from_reservation_preparation,
    prefill_from_tour_detail,
)
from mini_app.custom_request_validation import (
    message_for_custom_request_422,
    validate_custom_request_form_local,
)
from mini_app.presentation_notes import booking_detail_context_note
from mini_app.rfq_bridge_logic import rfq_bridge_continue_to_payment_allowed
from mini_app.rfq_hub_cta import (
    DetailPrimaryCtaKind,
    detail_context_line_keys,
    detail_next_step_key,
    is_request_status_terminal,
    my_requests_list_summary_key,
    pick_booking_for_bridge_tour,
    request_status_user_label,
    request_type_user_label,
    resolve_detail_primary_cta,
)
from mini_app.ui_strings import hold_timer_hint as _hold_timer_hint_i18n
from mini_app.ui_strings import booking_facade_labels, payment_status_label, shell

logger = logging.getLogger(__name__)


def scrollable_page(*controls: ft.Control, padding: int = 16, spacing: float = 14) -> ft.Control:
    """
    One bounded scroll surface: SafeArea + Container + Column(expand, scroll).

    Used for full-screen bodies instead of page.scroll + inner Column without expand,
    which breaks touch scrolling on mobile WebView.
    """
    return ft.SafeArea(
        expand=True,
        content=ft.Container(
            expand=True,
            padding=padding,
            content=ft.Column(
                list(controls),
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=spacing,
            ),
        ),
    )


def _payment_status_user_label(status: PaymentStatus, lang: str | None) -> str:
    return payment_status_label(lang, status)


def _hold_timer_hint(expires_at: datetime | None, lang: str | None) -> str:
    return _hold_timer_hint_i18n(expires_at, lang, format_dt=CatalogScreen._format_datetime)


def _format_request_datetime(value: datetime) -> str:
    return CatalogScreen._format_datetime(value)


def _format_request_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _request_subject_line(
    *,
    lg: str | None,
    request_type_label: str,
    travel_start: date,
    travel_end: date | None,
    group_size: int | None,
    route_notes_preview: str | None,
) -> str:
    lead = (route_notes_preview or "").strip() or request_type_label
    parts: list[str] = [lead]
    if group_size is not None and group_size > 0:
        parts.append(shell(lg, "my_requests_subject_group", size=str(group_size)))
    start = _format_request_date(travel_start)
    end = _format_request_date(travel_end)
    if end and end != start:
        date_part = shell(lg, "my_requests_subject_dates_range", start=start, end=end)
    else:
        date_part = shell(lg, "my_requests_subject_date_single", date=start)
    parts.append(date_part)
    return " · ".join(parts)


class CatalogScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        on_open_detail: Callable[[str], None],
        on_my_bookings: Callable[[], None],
        on_my_requests: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_help: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.on_open_detail = on_open_detail
        self.on_my_bookings = on_my_bookings
        self.on_my_requests = on_my_requests
        self.on_open_settings = on_open_settings
        self.on_help = on_help
        self.on_open_custom_request = on_open_custom_request

        lg = default_language_code
        self.destination_field = ft.TextField(
            label=shell(lg, "label_destination"),
            hint_text=shell(lg, "hint_destination"),
            dense=True,
        )
        self.departure_from_field = ft.TextField(
            label=shell(lg, "label_departure_from"),
            hint_text=shell(lg, "hint_date"),
            dense=True,
        )
        self.departure_to_field = ft.TextField(
            label=shell(lg, "label_departure_to"),
            hint_text=shell(lg, "hint_date"),
            dense=True,
        )
        self.max_price_field = ft.TextField(
            label=shell(lg, "label_max_price"),
            hint_text=shell(lg, "hint_price"),
            dense=True,
        )
        self.apply_button = ft.ElevatedButton(shell(lg, "btn_apply_filters"), on_click=self._on_apply_filters)
        self.clear_button = ft.TextButton(shell(lg, "btn_clear"), on_click=self._on_clear_filters)
        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text(shell(lg, "loading_tours"))],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.summary_text = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT)
        self.empty_state = ft.Text(
            shell(lg, "empty_catalog"),
            visible=False,
        )
        self.cards_column = ft.Column(spacing=12)

    def sync_shell_labels(self) -> None:
        """Refresh UI-shell strings when `language_code` changes (e.g. after Settings)."""
        lg = self.language_code
        self.destination_field.label = shell(lg, "label_destination")
        self.destination_field.hint_text = shell(lg, "hint_destination")
        self.departure_from_field.label = shell(lg, "label_departure_from")
        self.departure_from_field.hint_text = shell(lg, "hint_date")
        self.departure_to_field.label = shell(lg, "label_departure_to")
        self.departure_to_field.hint_text = shell(lg, "hint_date")
        self.max_price_field.label = shell(lg, "label_max_price")
        self.max_price_field.hint_text = shell(lg, "hint_price")
        self.apply_button.text = shell(lg, "btn_apply_filters")
        self.clear_button.text = shell(lg, "btn_clear")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "loading_tours")
        self.empty_state.value = shell(lg, "empty_catalog")

    def build(self) -> ft.Control:
        lg = self.language_code
        return scrollable_page(
            ft.Text(shell(lg, "catalog_title"), size=26, weight=ft.FontWeight.BOLD),
            ft.Text(shell(lg, "catalog_subtitle"), color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Row(
                [
                    ft.OutlinedButton(shell(lg, "btn_my_bookings"), on_click=lambda _: self.on_my_bookings()),
                    ft.OutlinedButton(shell(lg, "btn_my_requests"), on_click=lambda _: self.on_my_requests()),
                    ft.OutlinedButton(shell(lg, "btn_language_settings"), on_click=lambda _: self.on_open_settings()),
                    ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help()),
                    ft.TextButton(shell(lg, "nav_custom_trip"), on_click=lambda _: self.on_open_custom_request()),
                ],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(shell(lg, "filters_heading"), size=18, weight=ft.FontWeight.W_600),
                        self.destination_field,
                        self.departure_from_field,
                        self.departure_to_field,
                        self.max_price_field,
                        ft.Row(
                            [self.apply_button, self.clear_button],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ],
                    spacing=12,
                ),
            ),
            self.loading_row,
            self.error_text,
            self.summary_text,
            self.empty_state,
            self.cards_column,
        )

    async def load_catalog(self) -> None:
        self.sync_shell_labels()
        try:
            max_price = self._parse_max_price()
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()

        try:
            catalog = await self.api_client.list_catalog(
                language_code=self.language_code,
                destination_query=self._clean_string(self.destination_field.value),
                departure_date_from=self._clean_string(self.departure_from_field.value),
                departure_date_to=self._clean_string(self.departure_to_field.value),
                max_price=max_price,
            )
        except httpx.HTTPStatusError as exc:
            self._show_error(self._http_error_message(exc, default="Unable to load tours right now."))
            self._render_catalog(None)
        except Exception:
            self._show_error("Unable to load tours right now.")
            self._render_catalog(None)
        else:
            self._render_catalog(catalog)
        finally:
            self._set_loading(False)
            self.page.update()

    def _render_catalog(self, catalog: MiniAppCatalogRead | None) -> None:
        self.cards_column.controls.clear()
        if catalog is None:
            self.summary_text.value = ""
            self.empty_state.visible = False
            return

        self.summary_text.value = self._build_summary(catalog)
        self.empty_state.visible = len(catalog.items) == 0
        for card in catalog.items:
            self.cards_column.controls.append(self._build_tour_card(card))

    def _build_tour_card(self, card: CatalogTourCardRead) -> ft.Control:
        lg = self.language_code
        badges = ft.Row(
            [
                self._build_badge(self._status_label(card.status.value), ft.Colors.BLUE_50, ft.Colors.BLUE_900),
                self._build_badge(
                    shell(lg, "badge_seats_available") if card.is_available else shell(lg, "badge_sold_out"),
                    ft.Colors.GREEN_50 if card.is_available else ft.Colors.RED_50,
                    ft.Colors.GREEN_900 if card.is_available else ft.Colors.RED_900,
                ),
            ],
            spacing=8,
        )
        description = card.short_description or shell(lg, "catalog_card_no_description")
        assisted_line = None
        if not card.sales_mode_policy.mini_app_catalog_reservation_allowed:
            assisted_line = ft.Text(
                shell(lg, "catalog_card_assisted_notice"),
                color=ft.Colors.TERTIARY,
                size=13,
            )
        card_children: list[ft.Control] = [
            badges,
            ft.Text(card.title, size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"{self._format_datetime(card.departure_datetime)} | "
                + shell(lg, "days_hours", n=str(card.duration_days)),
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                f"{self._format_price(card.base_price)} {card.currency} | {card.seats_available} / {card.seats_total} seats left",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ]
        if assisted_line is not None:
            card_children.append(assisted_line)
        card_children.extend(
            [
                ft.Text(description, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Row(
                    [
                        ft.TextButton(
                            shell(lg, "view_details"),
                            on_click=lambda _, code=card.code: self.on_open_detail(code),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ]
        )
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
            padding=16,
            content=ft.Column(
                card_children,
                spacing=8,
            ),
        )

    def _build_summary(self, catalog: MiniAppCatalogRead) -> str:
        applied = []
        if catalog.applied_filters.destination_query:
            applied.append(f"destination: {catalog.applied_filters.destination_query}")
        if catalog.applied_filters.departure_date_from:
            applied.append(f"from: {catalog.applied_filters.departure_date_from.isoformat()}")
        if catalog.applied_filters.departure_date_to:
            applied.append(f"to: {catalog.applied_filters.departure_date_to.isoformat()}")
        if catalog.applied_filters.max_price is not None:
            applied.append(f"max price: {catalog.applied_filters.max_price}")

        summary = f"{len(catalog.items)} tour(s) found"
        if applied:
            summary += " | " + ", ".join(applied)
        return summary

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

    def _set_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading
        self.apply_button.disabled = is_loading
        self.clear_button.disabled = is_loading

    def _on_apply_filters(self, _: ft.ControlEvent) -> None:
        self.page.run_task(self.load_catalog)

    def _on_clear_filters(self, _: ft.ControlEvent) -> None:
        self.destination_field.value = ""
        self.departure_from_field.value = ""
        self.departure_to_field.value = ""
        self.max_price_field.value = ""
        self.error_text.visible = False
        self.page.update()
        self.page.run_task(self.load_catalog)

    def _parse_max_price(self) -> Decimal | None:
        value = self._clean_string(self.max_price_field.value)
        if value is None:
            return None
        try:
            parsed = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("Max price must be a valid number.") from exc
        if parsed < 0:
            raise ValueError("Max price cannot be negative.")
        return parsed

    @staticmethod
    def _clean_string(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _format_price(value: Decimal) -> str:
        return f"{value:.2f}"

    @staticmethod
    def _status_label(status_value: str) -> str:
        return status_value.replace("_", " ").title()

    @staticmethod
    def _build_badge(text: str, background: str, foreground: str) -> ft.Control:
        return ft.Container(
            bgcolor=background,
            border_radius=999,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            content=ft.Text(text, color=foreground, size=12),
        )

    @staticmethod
    def _http_error_message(exc: httpx.HTTPStatusError, *, default: str) -> str:
        if exc.response is None:
            return default
        try:
            raw = exc.response.json().get("detail", default)
            if isinstance(raw, dict):
                return str(raw.get("message") or raw.get("code") or default)
            if isinstance(raw, str):
                return raw
            return str(raw)
        except Exception:
            return default


class TourDetailScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        dev_telegram_user_id: int,
        on_back: Callable[[], None],
        on_prepare: Callable[[str], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self._dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_prepare = on_prepare
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        self.current_tour_code: str | None = None
        self._last_detail: MiniAppTourDetailRead | None = None

        lg = default_language_code
        self.nav_back = ft.TextButton(
            shell(lg, "back_to_catalog"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back(),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "loading_tour_details")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.content_column = ft.Column(spacing=14)

    def set_tour_code(self, tour_code: str) -> None:
        self.current_tour_code = tour_code

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_catalog")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "loading_tour_details")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.loading_row,
            self.error_text,
            self.content_column,
        )

    async def load_tour_detail(self) -> None:
        self.sync_shell_labels()
        if not self.current_tour_code:
            self._show_error("Tour not found.")
            self._render_detail(None)
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()

        try:
            detail = await self.api_client.get_tour_detail(
                tour_code=self.current_tour_code,
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                message = "This tour is not available in the Mini App catalog."
            else:
                message = CatalogScreen._http_error_message(exc, default="Unable to load tour details right now.")
            self._show_error(message)
            self._render_detail(None)
        except Exception:
            self._show_error("Unable to load tour details right now.")
            self._render_detail(None)
        else:
            waitlist_status: MiniAppWaitlistStatusRead | None = None
            if not detail.is_available and detail.tour.status == TourStatus.OPEN_FOR_SALE:
                try:
                    waitlist_status = await self.api_client.get_waitlist_status(
                        tour_code=self.current_tour_code,
                        telegram_user_id=self._dev_telegram_user_id,
                    )
                except Exception:
                    waitlist_status = None
            self._render_detail(detail, waitlist_status)
        finally:
            self._set_loading(False)
            self.page.update()

    async def _request_full_bus_assistance_from_detail(self) -> None:
        lg = self.language_code
        code = self.current_tour_code
        if not code:
            return
        try:
            r = await self.api_client.post_support_request(
                telegram_user_id=self._dev_telegram_user_id,
                order_id=None,
                screen_hint="tour_detail_full_bus",
                tour_code=code,
            )
        except Exception:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        if r.recorded and r.handoff_id is not None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_success", ref=str(r.handoff_id))),
                action="OK",
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
        self.page.snack_bar.open = True
        self.page.update()

    def _render_detail(
        self,
        detail: MiniAppTourDetailRead | None,
        waitlist_status: MiniAppWaitlistStatusRead | None = None,
    ) -> None:
        self.content_column.controls.clear()
        self._last_detail = detail
        if detail is None:
            return

        badges = ft.Row(
            [
                CatalogScreen._build_badge(
                    CatalogScreen._status_label(detail.tour.status.value),
                    ft.Colors.BLUE_50,
                    ft.Colors.BLUE_900,
                ),
                CatalogScreen._build_badge(
                    shell(self.language_code, "badge_seats_available")
                    if detail.is_available
                    else shell(self.language_code, "badge_sold_out"),
                    ft.Colors.GREEN_50 if detail.is_available else ft.Colors.RED_50,
                    ft.Colors.GREEN_900 if detail.is_available else ft.Colors.RED_900,
                ),
            ],
            spacing=8,
        )

        localized = detail.localized_content
        self.content_column.controls.extend(
            [
                badges,
                ft.Text(localized.title, size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"{CatalogScreen._format_datetime(detail.tour.departure_datetime)} | "
                    + shell(self.language_code, "days_hours", n=str(detail.tour.duration_days)),
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Text(
                    f"{CatalogScreen._format_price(detail.tour.base_price)} {detail.tour.currency} | {detail.tour.seats_available} / {detail.tour.seats_total} seats left",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ]
        )

        self.content_column.controls.append(
            self._build_booking_or_waitlist_actions(detail, waitlist_status)
        )

        if localized.used_fallback:
            self.content_column.controls.append(
                ft.Text(
                    shell(self.language_code, "fallback_translation_note"),
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        overview = localized.full_description or localized.short_description
        if overview:
            self.content_column.controls.append(
                self._build_text_section(shell(self.language_code, "section_overview"), overview)
            )
        if localized.program_text:
            self.content_column.controls.append(
                self._build_text_section(shell(self.language_code, "section_program"), localized.program_text)
            )
        if localized.included_text:
            self.content_column.controls.append(
                self._build_text_section(shell(self.language_code, "section_included"), localized.included_text)
            )
        if localized.excluded_text:
            self.content_column.controls.append(
                self._build_text_section(shell(self.language_code, "section_excluded"), localized.excluded_text)
            )

        self.content_column.controls.append(
            ft.Text(shell(self.language_code, "section_boarding_points"), size=18, weight=ft.FontWeight.W_600)
        )
        if detail.boarding_points:
            for boarding_point in detail.boarding_points:
                self.content_column.controls.append(self._build_boarding_point_card(boarding_point))
        else:
            self.content_column.controls.append(
                ft.Text(shell(self.language_code, "boarding_no_details"))
            )

    def _mode2_custom_trip_block(self, detail: MiniAppTourDetailRead) -> list[ft.Control]:
        """Track 5g.5: UX bridge to existing custom-request flow (Mode 3), catalog full-bus only."""
        if detail.commercial_mode != CustomerCommercialMode.SUPPLIER_ROUTE_FULL_BUS:
            return []
        lg = self.language_code
        return [
            ft.Divider(height=12),
            ft.Text(shell(lg, "mode2_custom_trip_hint"), size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.OutlinedButton(
                shell(lg, "btn_mode2_request_custom_trip"),
                on_click=lambda _: self.on_open_custom_request(),
            ),
        ]

    def _build_booking_or_waitlist_actions(
        self,
        detail: MiniAppTourDetailRead,
        waitlist_status: MiniAppWaitlistStatusRead | None,
    ) -> ft.Control:
        lg = self.language_code
        if detail.is_available:
            if detail.sales_mode_policy.mini_app_catalog_reservation_allowed:
                return ft.Row(
                    [
                        ft.ElevatedButton(
                            shell(lg, "prepare_reservation"),
                            on_click=lambda _, code=detail.tour.code: self.on_prepare(code),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                )
            return ft.Container(
                padding=ft.padding.only(top=4),
                content=ft.Column(
                    [
                        ft.Text(shell(lg, "detail_assisted_booking_title"), weight=ft.FontWeight.W_600),
                        ft.Text(shell(lg, "detail_assisted_booking_body"), color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.FilledButton(
                            shell(lg, "btn_request_full_bus_assistance"),
                            on_click=lambda _: self.page.run_task(self._request_full_bus_assistance_from_detail),
                        ),
                        *self._mode2_custom_trip_block(detail),
                    ],
                    spacing=6,
                ),
            )
        if detail.tour.status != TourStatus.OPEN_FOR_SALE:
            return ft.Row(
                [
                    ft.Text(
                        shell(lg, "waitlist_tour_not_eligible"),
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        if waitlist_status is not None and not waitlist_status.eligible:
            return ft.Row(
                [
                    ft.Text(
                        shell(lg, "waitlist_tour_not_eligible"),
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        ws = waitlist_status
        st = ws.waitlist_status if ws is not None else None
        if ws is not None and ws.on_waitlist:
            if st == "active":
                return ft.Container(
                    padding=ft.padding.only(top=4),
                    content=ft.Column(
                        [
                            ft.Text(shell(lg, "waitlist_active_title"), weight=ft.FontWeight.W_600),
                            ft.Text(shell(lg, "waitlist_active_body"), color=ft.Colors.ON_SURFACE_VARIANT),
                            *self._mode2_custom_trip_block(detail),
                        ],
                        spacing=4,
                    ),
                )
            if st == "in_review":
                return ft.Container(
                    padding=ft.padding.only(top=4),
                    content=ft.Column(
                        [
                            ft.Text(shell(lg, "waitlist_in_review_title"), weight=ft.FontWeight.W_600),
                            ft.Text(shell(lg, "waitlist_in_review_body"), color=ft.Colors.ON_SURFACE_VARIANT),
                            *self._mode2_custom_trip_block(detail),
                        ],
                        spacing=4,
                    ),
                )
            return ft.Container(
                padding=ft.padding.only(top=4),
                content=ft.Column(
                    [
                        ft.Text(
                            shell(lg, "waitlist_status_on"),
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        *self._mode2_custom_trip_block(detail),
                    ],
                    spacing=4,
                ),
            )
        if st == "closed":
            return ft.Column(
                [
                    ft.Text(shell(lg, "waitlist_closed_body"), color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                shell(lg, "waitlist_join_cta"),
                                on_click=lambda _: self.page.run_task(self._join_waitlist_async),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    *self._mode2_custom_trip_block(detail),
                ],
                spacing=8,
            )
        return ft.Column(
            [
                ft.Text(
                    shell(lg, "waitlist_intro_sold_out"),
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            shell(lg, "waitlist_join_cta"),
                            on_click=lambda _: self.page.run_task(self._join_waitlist_async),
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                *self._mode2_custom_trip_block(detail),
            ],
            spacing=8,
        )

    async def _join_waitlist_async(self) -> None:
        if not self.current_tour_code:
            return
        lg = self.language_code
        try:
            result = await self.api_client.post_waitlist(
                tour_code=self.current_tour_code,
                telegram_user_id=self._dev_telegram_user_id,
                seats_count=1,
            )
        except Exception:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "waitlist_snackbar_error")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        outcome = result.outcome
        if outcome == "created":
            msg = shell(lg, "waitlist_snackbar_created")
        elif outcome == "already_exists":
            msg = shell(lg, "waitlist_snackbar_already")
        elif outcome == "not_eligible":
            msg = shell(lg, "waitlist_snackbar_not_eligible")
        else:
            msg = shell(lg, "waitlist_snackbar_error")
        self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), action="OK")
        self.page.snack_bar.open = True
        self.page.update()
        await self.load_tour_detail()

    def _build_text_section(self, title: str, body: str) -> ft.Control:
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border_radius=16,
            padding=16,
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.W_600),
                    ft.Text(body),
                ],
                spacing=8,
            ),
        )

    def _build_boarding_point_card(self, boarding_point: BoardingPointRead) -> ft.Control:
        lg = self.language_code
        notes = boarding_point.notes or shell(lg, "boarding_notes_fallback")
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
            padding=16,
            content=ft.Column(
                [
                    ft.Text(boarding_point.city, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(boarding_point.address),
                    ft.Text(f"{shell(lg, 'boarding_departure_time')}: {boarding_point.time.strftime('%H:%M')}"),
                    ft.Text(notes, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=6,
            ),
        )

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

    def _set_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading


class ReservationPreparationScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        dev_telegram_user_id: int,
        on_back: Callable[[str], None],
        on_reserved: Callable[[str, int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_reserved = on_reserved
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        self.current_tour_code: str | None = None
        self._last_preparation: MiniAppReservationPreparationRead | None = None

        lg = default_language_code
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "loading_reservation_options")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.selection_container = ft.Column(spacing=12)
        self.summary_container = ft.Column(spacing=12)
        self.seats_dropdown = ft.Dropdown(label=shell(lg, "label_seats"), dense=True, options=[])
        self.boarding_dropdown = ft.Dropdown(label=shell(lg, "label_boarding"), dense=True, options=[])
        self.preview_button = ft.OutlinedButton(shell(lg, "btn_preview_summary"), on_click=self._on_preview_summary)
        self.confirm_reserve_button = ft.ElevatedButton(
            shell(lg, "btn_confirm_reservation"),
            disabled=True,
            on_click=lambda _: self.page.run_task(self._confirm_reservation),
        )
        self.preparation_note = ft.Text(
            shell(lg, "prep_note", dev_id=str(dev_telegram_user_id)),
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.nav_back = ft.TextButton(
            shell(lg, "back_to_tour_details"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back(self.current_tour_code or ""),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())

    def set_tour_code(self, tour_code: str) -> None:
        self.current_tour_code = tour_code

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_tour_details")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self.seats_dropdown.label = shell(lg, "label_seats")
        self.boarding_dropdown.label = shell(lg, "label_boarding")
        self.preview_button.text = shell(lg, "btn_preview_summary")
        self.confirm_reserve_button.text = shell(lg, "btn_confirm_reservation")
        self.preparation_note.value = shell(lg, "prep_note", dev_id=str(self.dev_telegram_user_id))
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "loading_reservation_options")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.loading_row,
            self.error_text,
            self.preparation_note,
            self.selection_container,
            self.summary_container,
        )

    async def load_preparation(self) -> None:
        self.sync_shell_labels()
        if not self.current_tour_code:
            self._show_error("Tour not found.")
            self._render_preparation(None)
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()

        try:
            preparation = await self.api_client.get_tour_preparation(
                tour_code=self.current_tour_code,
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            message = CatalogScreen._http_error_message(
                exc,
                default="Unable to load reservation options right now.",
            )
            self._show_error(message)
            self._render_preparation(None)
        except Exception:
            self._show_error("Unable to load reservation options right now.")
            self._render_preparation(None)
        else:
            self._render_preparation(preparation)
        finally:
            self._set_loading(False)
            self.page.update()

    async def load_summary(self) -> None:
        if not self.current_tour_code:
            self._show_error("Tour not found.")
            return
        if not self.seats_dropdown.value or not self.boarding_dropdown.value:
            self._show_error("Choose seats and a boarding point to preview the summary.")
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()

        try:
            summary = await self.api_client.get_preparation_summary(
                tour_code=self.current_tour_code,
                seats_count=int(self.seats_dropdown.value),
                boarding_point_id=int(self.boarding_dropdown.value),
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            message = CatalogScreen._http_error_message(
                exc,
                default="Unable to build the reservation summary right now.",
            )
            self._show_error(message)
            self._render_summary(None)
        except Exception:
            self._show_error("Unable to build the reservation summary right now.")
            self._render_summary(None)
        else:
            self._render_summary(summary)
        finally:
            self._set_loading(False)
            self.page.update()

    def _render_preparation(self, preparation: MiniAppReservationPreparationRead | None) -> None:
        self.selection_container.controls.clear()
        self.summary_container.controls.clear()
        self.confirm_reserve_button.disabled = True
        self._last_preparation = preparation
        if preparation is None:
            return

        lg = self.language_code
        localized = preparation.tour.localized_content
        header_rows: list[ft.Control] = [
            ft.Text(localized.title, size=26, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"{CatalogScreen._format_datetime(preparation.tour.departure_datetime)} | "
                f"{CatalogScreen._format_price(preparation.tour.base_price)} {preparation.tour.currency}",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                f"Seats available for preparation: {preparation.tour.seats_available_snapshot}",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ]

        if not preparation.sales_mode_policy.mini_app_catalog_reservation_allowed:
            self.preparation_note.visible = False
            prep_assisted_children: list[ft.Control] = [
                ft.Text(shell(lg, "preparation_assisted_title"), weight=ft.FontWeight.W_600),
                ft.Text(shell(lg, "preparation_assisted_body"), color=ft.Colors.ON_SURFACE_VARIANT),
            ]
            if preparation.sales_mode_policy.effective_sales_mode == TourSalesMode.FULL_BUS:
                prep_assisted_children.extend(
                    [
                        ft.Divider(height=12),
                        ft.Text(shell(lg, "mode2_custom_trip_hint"), size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.OutlinedButton(
                            shell(lg, "btn_mode2_request_custom_trip"),
                            on_click=lambda _: self.on_open_custom_request(),
                        ),
                    ]
                )
            self.selection_container.controls.extend(
                header_rows
                + [
                    ft.Container(
                        padding=ft.padding.only(top=8),
                        content=ft.Column(
                            prep_assisted_children,
                            spacing=6,
                        ),
                    ),
                ]
            )
            self.seats_dropdown.options = []
            self.seats_dropdown.value = None
            self.boarding_dropdown.options = []
            self.boarding_dropdown.value = None
            return

        self.preparation_note.visible = True
        self.seats_dropdown.options = [
            ft.dropdown.Option(str(option), str(option)) for option in preparation.seat_count_options
        ]
        self.seats_dropdown.value = str(preparation.seat_count_options[0]) if preparation.seat_count_options else None
        self.boarding_dropdown.options = [
            ft.dropdown.Option(str(point.id), f"{point.city} - {point.address}")
            for point in preparation.boarding_points
        ]
        self.boarding_dropdown.value = (
            str(preparation.boarding_points[0].id) if preparation.boarding_points else None
        )

        self.selection_container.controls.extend(
            header_rows
            + [
                self.seats_dropdown,
                self.boarding_dropdown,
                ft.Row([self.preview_button], alignment=ft.MainAxisAlignment.START),
            ]
        )

    def _render_summary(self, summary: ReservationPreparationSummaryRead | None) -> None:
        self.summary_container.controls.clear()
        if summary is None:
            self.confirm_reserve_button.disabled = True
            return

        self.confirm_reserve_button.disabled = False
        lg = self.language_code
        self.summary_container.controls.extend(
            [
                ft.Text(shell(lg, "prep_summary_title"), size=20, weight=ft.FontWeight.W_600),
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    border_radius=16,
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(summary.tour.localized_content.title, size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(shell(lg, "prep_line_seats", n=str(summary.seats_count))),
                            ft.Text(
                                shell(
                                    lg,
                                    "prep_line_boarding",
                                    city=summary.boarding_point.city,
                                    addr=summary.boarding_point.address,
                                )
                            ),
                            ft.Text(
                                shell(
                                    lg,
                                    "prep_line_boarding_time",
                                    t=summary.boarding_point.time.strftime("%H:%M"),
                                )
                            ),
                            ft.Text(
                                shell(
                                    lg,
                                    "prep_line_estimated",
                                    amount=CatalogScreen._format_price(summary.estimated_total_amount),
                                    currency=summary.tour.currency,
                                )
                            ),
                            ft.Text(
                                shell(lg, "prep_hold_note"),
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Row([self.confirm_reserve_button], alignment=ft.MainAxisAlignment.START),
            ]
        )

    def _on_preview_summary(self, _: ft.ControlEvent) -> None:
        self.page.run_task(self.load_summary)

    async def _confirm_reservation(self) -> None:
        if not self.current_tour_code:
            self._show_error("Tour not found.")
            return
        if not self.seats_dropdown.value or not self.boarding_dropdown.value:
            self._show_error("Choose seats and a boarding point before confirming.")
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()

        try:
            summary = await self.api_client.create_temporary_reservation(
                tour_code=self.current_tour_code,
                telegram_user_id=self.dev_telegram_user_id,
                seats_count=int(self.seats_dropdown.value),
                boarding_point_id=int(self.boarding_dropdown.value),
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            message = CatalogScreen._http_error_message(
                exc,
                default="Unable to create a temporary reservation right now.",
            )
            self._show_error(message)
        except Exception:
            self._show_error("Unable to create a temporary reservation right now.")
        else:
            self.on_reserved(self.current_tour_code, summary.order.id)
        finally:
            self._set_loading(False)
            self.page.update()

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

    def _set_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading
        self.preview_button.disabled = is_loading
        has_summary = bool(self.summary_container.controls)
        self.confirm_reserve_button.disabled = is_loading or not has_summary


class ReservationSuccessScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        dev_telegram_user_id: int,
        on_back: Callable[[str], None],
        on_continue_to_payment: Callable[[str, int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_continue_to_payment = on_continue_to_payment
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        self.tour_code: str | None = None
        self.order_id: int | None = None

        lg = default_language_code
        self.nav_back = ft.TextButton(
            shell(lg, "back_to_preparation"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back(self.tour_code or ""),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self._heading = ft.Text(shell(lg, "reservation_confirmed_title"), size=26, weight=ft.FontWeight.BOLD)
        self._intro = ft.Text(shell(lg, "reservation_hold_intro"), color=ft.Colors.ON_SURFACE_VARIANT)
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "loading_reservation")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=10)
        self.continue_button = ft.ElevatedButton(
            shell(lg, "pay_now"),
            disabled=True,
            on_click=lambda _: self._on_continue(),
        )

    def set_context(self, *, tour_code: str, order_id: int) -> None:
        self.tour_code = tour_code
        self.order_id = order_id

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_preparation")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self._heading.value = shell(lg, "reservation_confirmed_title")
        self._intro.value = shell(lg, "reservation_hold_intro")
        self.continue_button.text = shell(lg, "pay_now")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "loading_reservation")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.loading_row,
            self.error_text,
            self._heading,
            self._intro,
            self.body_column,
            ft.Row([self.continue_button], alignment=ft.MainAxisAlignment.START),
        )

    async def load_overview(self) -> None:
        self.sync_shell_labels()
        if self.order_id is None:
            self._show_error("Missing order reference.")
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.body_column.controls.clear()
        self.continue_button.disabled = True
        self.page.update()

        try:
            overview = await self.api_client.get_reservation_overview(
                order_id=self.order_id,
                telegram_user_id=self.dev_telegram_user_id,
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            message = CatalogScreen._http_error_message(
                exc,
                default="Unable to load your reservation. It may have expired or been released.",
            )
            self._show_error(message)
        except Exception:
            self._show_error("Unable to load your reservation. It may have expired or been released.")
        else:
            self._render_overview(overview)
        finally:
            self._set_loading(False)
            self.page.update()

    def _render_overview(self, overview: OrderSummaryRead) -> None:
        order = overview.order
        expires = order.reservation_expires_at
        now = datetime.now(UTC)
        end = expires if expires is None or expires.tzinfo else expires.replace(tzinfo=UTC)
        hold_ok = expires is not None and end > now

        self.continue_button.disabled = not hold_ok
        lg = self.language_code
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(overview.tour.localized_content.title, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(shell(lg, "line_reservation_ref", id=str(order.id))),
                        ft.Text(
                            shell(
                                lg,
                                "line_amount_to_pay",
                                amount=CatalogScreen._format_price(order.total_amount),
                                currency=order.currency,
                            )
                        ),
                        ft.Text(
                            shell(
                                lg,
                                "line_payment_status",
                                status=_payment_status_user_label(order.payment_status, self.language_code),
                            ),
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(_hold_timer_hint(expires, self.language_code)),
                    ],
                    spacing=8,
                ),
            ),
        ]

    def _on_continue(self) -> None:
        if self.tour_code is not None and self.order_id is not None:
            self.on_continue_to_payment(self.tour_code, self.order_id)

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

    def _set_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading


class RfqBridgeExecutionScreen:
    """Track 5c: bridge preparation → hold → payment eligibility → existing payment-entry navigation."""

    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        language_code: str,
        dev_telegram_user_id: int,
        on_back: Callable[[], None],
        on_continue_to_payment: Callable[[str, int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_continue_to_payment = on_continue_to_payment
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        self.request_id: int | None = None
        self._bridge_prep: MiniAppBridgeExecutionPreparationResponse | None = None
        self._tour_code: str | None = None
        self._order_id: int | None = None
        self._payment_elig: MiniAppBridgePaymentEligibilityRead | None = None

        lg = language_code
        self.nav_back = ft.TextButton(
            shell(lg, "back"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back(),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self._title = ft.Text(shell(lg, "rfq_bridge_screen_title"), size=24, weight=ft.FontWeight.BOLD)
        self._intro = ft.Text(shell(lg, "rfq_bridge_intro"), size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self._request_ref = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT, visible=False)
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "rfq_bridge_loading")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.flow_column = ft.Column(spacing=12)
        self.seats_dropdown = ft.Dropdown(label=shell(lg, "label_seats"), dense=True, options=[])
        self.boarding_dropdown = ft.Dropdown(label=shell(lg, "label_boarding"), dense=True, options=[])
        self.preview_button = ft.OutlinedButton(shell(lg, "btn_preview_summary"), on_click=self._on_preview_summary)
        self.confirm_reserve_button = ft.ElevatedButton(
            shell(lg, "btn_confirm_reservation"),
            disabled=True,
            on_click=lambda _: self.page.run_task(self._confirm_bridge_reservation),
        )
        self.summary_container = ft.Column(spacing=12)
        self.continue_payment_button = ft.FilledButton(
            shell(lg, "continue_to_payment"),
            visible=False,
            disabled=True,
            on_click=lambda _: self._on_continue_payment(),
        )

    def set_request_id(self, request_id: int) -> None:
        self.request_id = request_id

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self._title.value = shell(lg, "rfq_bridge_screen_title")
        self._intro.value = shell(lg, "rfq_bridge_intro")
        self.seats_dropdown.label = shell(lg, "label_seats")
        self.boarding_dropdown.label = shell(lg, "label_boarding")
        self.preview_button.text = shell(lg, "btn_preview_summary")
        self.confirm_reserve_button.text = shell(lg, "btn_confirm_reservation")
        self.continue_payment_button.text = shell(lg, "continue_to_payment")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "rfq_bridge_loading")
        if self.request_id is not None:
            self._request_ref.value = shell(lg, "rfq_bridge_request_ref", id=str(self.request_id))

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self._title,
            self._intro,
            self._request_ref,
            self.loading_row,
            self.error_text,
            self.flow_column,
        )

    async def load_initial(self) -> None:
        self.sync_shell_labels()
        self._payment_elig = None
        self._order_id = None
        self._tour_code = None
        self._bridge_prep = None
        self.confirm_reserve_button.visible = True
        self.preview_button.disabled = False
        self.flow_column.controls.clear()
        self.summary_container.controls.clear()
        self.continue_payment_button.visible = False
        self.continue_payment_button.disabled = True
        self.error_text.visible = False
        if self.request_id is None:
            self._show_error("Missing request reference.")
            return

        self._request_ref.visible = True
        self._set_flow_loading(True)
        self.page.update()

        try:
            prep = await self.api_client.get_booking_bridge_preparation(
                request_id=self.request_id,
                telegram_user_id=self.dev_telegram_user_id,
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            closed_msg: str | None = None
            if exc.response is not None and exc.response.status_code == 404:
                try:
                    cd = await self.api_client.get_custom_request_for_customer(
                        request_id=self.request_id,
                        telegram_user_id=self.dev_telegram_user_id,
                    )
                    if cd.latest_booking_bridge_status in (
                        CustomRequestBookingBridgeStatus.SUPERSEDED,
                        CustomRequestBookingBridgeStatus.CANCELLED,
                    ):
                        closed_msg = shell(self.language_code, "rfq_bridge_closed_booking_path")
                except Exception:
                    closed_msg = None
            self._show_error(
                closed_msg
                or CatalogScreen._http_error_message(
                    exc,
                    default="Unable to load bridge booking for this request.",
                ),
            )
            self._render_empty_flow()
        except Exception:
            self._show_error("Unable to load bridge booking for this request.")
            self._render_empty_flow()
        else:
            self._bridge_prep = prep
            self._tour_code = prep.tour_code
            self.error_text.visible = False
            if not prep.self_service_available:
                self._render_blocked_preparation(prep)
            elif prep.preparation is None:
                self._show_error("Preparation is not available.")
                self._render_empty_flow()
            else:
                self._render_self_service_preparation(prep.preparation)
        finally:
            self._set_flow_loading(False)
            self.page.update()

    def _render_empty_flow(self) -> None:
        self.flow_column.controls.clear()

    def _render_blocked_preparation(self, prep: MiniAppBridgeExecutionPreparationResponse) -> None:
        lg = self.language_code
        msg = (prep.blocked_message or "").strip() or shell(lg, "rfq_bridge_payment_blocked_generic")
        code = prep.blocked_code or ""
        heading = (
            shell(lg, "rfq_bridge_platform_blocked_heading")
            if code in ("external_record", "supplier_policy_incomplete") or "policy" in code
            else shell(lg, "rfq_bridge_assisted_heading")
        )
        self.flow_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=12,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(heading, weight=ft.FontWeight.W_600),
                        ft.Text(msg, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=8,
                ),
            ),
        ]

    def _render_self_service_preparation(self, preparation: MiniAppReservationPreparationRead) -> None:
        self.summary_container.controls.clear()
        self.confirm_reserve_button.disabled = True
        self.flow_column.controls.clear()

        lg = self.language_code
        localized = preparation.tour.localized_content
        header_rows: list[ft.Control] = [
            ft.Text(localized.title, size=22, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"{CatalogScreen._format_datetime(preparation.tour.departure_datetime)} | "
                f"{CatalogScreen._format_price(preparation.tour.base_price)} {preparation.tour.currency}",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                f"Seats available for preparation: {preparation.tour.seats_available_snapshot}",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ]

        if not preparation.sales_mode_policy.mini_app_catalog_reservation_allowed:
            self.flow_column.controls.extend(
                header_rows
                + [
                    ft.Container(
                        padding=ft.padding.only(top=8),
                        content=ft.Column(
                            [
                                ft.Text(shell(lg, "preparation_assisted_title"), weight=ft.FontWeight.W_600),
                                ft.Text(shell(lg, "preparation_assisted_body"), color=ft.Colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=6,
                        ),
                    ),
                ]
            )
            self.seats_dropdown.options = []
            self.seats_dropdown.value = None
            self.boarding_dropdown.options = []
            self.boarding_dropdown.value = None
            return

        self.seats_dropdown.options = [
            ft.dropdown.Option(str(option), str(option)) for option in preparation.seat_count_options
        ]
        self.seats_dropdown.value = str(preparation.seat_count_options[0]) if preparation.seat_count_options else None
        self.boarding_dropdown.options = [
            ft.dropdown.Option(str(point.id), f"{point.city} - {point.address}")
            for point in preparation.boarding_points
        ]
        self.boarding_dropdown.value = (
            str(preparation.boarding_points[0].id) if preparation.boarding_points else None
        )

        self.flow_column.controls.extend(
            header_rows
            + [
                self.seats_dropdown,
                self.boarding_dropdown,
                ft.Row([self.preview_button], alignment=ft.MainAxisAlignment.START),
                self.summary_container,
            ]
        )

    def _on_preview_summary(self, _: ft.ControlEvent) -> None:
        self.page.run_task(self._load_summary_async)

    async def _load_summary_async(self) -> None:
        if self._tour_code is None:
            self._show_error("Tour not found.")
            return
        if not self.seats_dropdown.value or not self.boarding_dropdown.value:
            self._show_error("Choose seats and a boarding point to preview the summary.")
            return
        self._set_flow_loading(True)
        self.error_text.visible = False
        self.page.update()
        try:
            summary = await self.api_client.get_preparation_summary(
                tour_code=self._tour_code,
                seats_count=int(self.seats_dropdown.value),
                boarding_point_id=int(self.boarding_dropdown.value),
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            self._show_error(
                CatalogScreen._http_error_message(
                    exc,
                    default="Unable to build the reservation summary right now.",
                )
            )
            self._render_summary_block(None)
        except Exception:
            self._show_error("Unable to build the reservation summary right now.")
            self._render_summary_block(None)
        else:
            self._render_summary_block(summary)
        finally:
            self._set_flow_loading(False)
            self.page.update()

    def _render_summary_block(self, summary: ReservationPreparationSummaryRead | None) -> None:
        self.summary_container.controls.clear()
        if summary is None:
            self.confirm_reserve_button.disabled = True
            return
        lg = self.language_code
        self.confirm_reserve_button.disabled = False
        self.summary_container.controls.extend(
            [
                ft.Text(shell(lg, "prep_summary_title"), size=18, weight=ft.FontWeight.W_600),
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    border_radius=16,
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(summary.tour.localized_content.title, size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(shell(lg, "prep_line_seats", n=str(summary.seats_count))),
                            ft.Text(
                                shell(
                                    lg,
                                    "prep_line_boarding",
                                    city=summary.boarding_point.city,
                                    addr=summary.boarding_point.address,
                                )
                            ),
                            ft.Text(
                                shell(
                                    lg,
                                    "prep_line_boarding_time",
                                    t=summary.boarding_point.time.strftime("%H:%M"),
                                )
                            ),
                            ft.Text(
                                shell(
                                    lg,
                                    "prep_line_estimated",
                                    amount=CatalogScreen._format_price(summary.estimated_total_amount),
                                    currency=summary.tour.currency,
                                )
                            ),
                            ft.Text(
                                shell(lg, "prep_hold_note"),
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=8,
                    ),
                ),
                ft.Row([self.confirm_reserve_button], alignment=ft.MainAxisAlignment.START),
            ]
        )

    async def _confirm_bridge_reservation(self) -> None:
        if self.request_id is None or self._tour_code is None:
            self._show_error("Missing request or tour.")
            return
        if not self.seats_dropdown.value or not self.boarding_dropdown.value:
            self._show_error("Choose seats and a boarding point before confirming.")
            return
        self._set_flow_loading(True)
        self.error_text.visible = False
        self.page.update()
        try:
            summary = await self.api_client.create_booking_bridge_reservation(
                request_id=self.request_id,
                telegram_user_id=self.dev_telegram_user_id,
                seats_count=int(self.seats_dropdown.value),
                boarding_point_id=int(self.boarding_dropdown.value),
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            self._show_error(
                CatalogScreen._http_error_message(
                    exc,
                    default="Unable to create a temporary reservation right now.",
                )
            )
        except Exception:
            self._show_error("Unable to create a temporary reservation right now.")
        else:
            self._order_id = summary.order.id
            self._tour_code = self._bridge_prep.tour_code if self._bridge_prep else self._tour_code
            await self._load_post_hold_async()
        finally:
            self._set_flow_loading(False)
            self.page.update()

    async def _load_post_hold_async(self) -> None:
        if self.request_id is None or self._order_id is None:
            return
        self._set_flow_loading(True)
        self.error_text.visible = False
        self.page.update()
        overview: OrderSummaryRead | None = None
        elig: MiniAppBridgePaymentEligibilityRead | None = None
        try:
            overview = await self.api_client.get_reservation_overview(
                order_id=self._order_id,
                telegram_user_id=self.dev_telegram_user_id,
                language_code=self.language_code,
            )
        except Exception:
            overview = None
        try:
            elig = await self.api_client.get_booking_bridge_payment_eligibility(
                request_id=self.request_id,
                telegram_user_id=self.dev_telegram_user_id,
                order_id=self._order_id,
            )
        except Exception:
            elig = None
            self._show_error(shell(self.language_code, "rfq_bridge_eligibility_error"))
        self._payment_elig = elig
        self._render_post_hold(overview, elig)
        self._set_flow_loading(False)
        self.page.update()

    def _render_post_hold(
        self,
        overview: OrderSummaryRead | None,
        elig: MiniAppBridgePaymentEligibilityRead | None,
    ) -> None:
        lg = self.language_code
        self.flow_column.controls.clear()
        self.summary_container.controls.clear()
        self.preview_button.disabled = True
        self.confirm_reserve_button.visible = False

        hold_active = False
        if overview is not None:
            order = overview.order
            expires = order.reservation_expires_at
            now = datetime.now(UTC)
            end = expires if expires is None or expires.tzinfo else expires.replace(tzinfo=UTC)
            hold_active = expires is not None and end > now

        pay_ok = bool(elig and elig.payment_entry_allowed)
        show_pay_cta = rfq_bridge_continue_to_payment_allowed(
            hold_active=hold_active,
            payment_entry_allowed=pay_ok,
        )

        blocks: list[ft.Control] = [
            ft.Text(shell(lg, "rfq_bridge_hold_section_title"), weight=ft.FontWeight.W_600),
        ]
        if overview is None:
            blocks.append(
                ft.Text(
                    shell(lg, "payment_screen_unavailable_hold"),
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        else:
            order = overview.order
            blocks.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    border_radius=16,
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(overview.tour.localized_content.title, size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(shell(lg, "line_reservation_ref", id=str(order.id))),
                            ft.Text(
                                shell(
                                    lg,
                                    "line_amount_to_pay",
                                    amount=CatalogScreen._format_price(order.total_amount),
                                    currency=order.currency,
                                )
                            ),
                            ft.Text(
                                shell(
                                    lg,
                                    "line_payment_status",
                                    status=_payment_status_user_label(order.payment_status, self.language_code),
                                ),
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(_hold_timer_hint(order.reservation_expires_at, self.language_code)),
                        ],
                        spacing=8,
                    ),
                )
            )

        if overview is not None and hold_active and elig is not None and not pay_ok:
            reason = (elig.blocked_reason or "").strip() or shell(lg, "rfq_bridge_hold_active_pay_blocked")
            blocks.append(ft.Text(reason, size=13, color=ft.Colors.ON_SURFACE_VARIANT))
        elif overview is not None and hold_active and elig is None:
            blocks.append(
                ft.Text(
                    shell(lg, "rfq_bridge_eligibility_error"),
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        elif overview is not None and not hold_active:
            blocks.append(
                ft.Text(
                    shell(lg, "rfq_bridge_expired_hold"),
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        self.continue_payment_button.visible = True
        self.continue_payment_button.disabled = not show_pay_cta
        blocks.append(ft.Row([self.continue_payment_button], alignment=ft.MainAxisAlignment.START))
        self.flow_column.controls.extend(blocks)

    def _on_continue_payment(self) -> None:
        if self._tour_code is not None and self._order_id is not None:
            self.on_continue_to_payment(self._tour_code, self._order_id)

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True

    def _set_flow_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading
        self.preview_button.disabled = is_loading
        if is_loading:
            self.confirm_reserve_button.disabled = True
        else:
            has_summary = bool(self.summary_container.controls)
            self.confirm_reserve_button.disabled = not has_summary


class PaymentEntryScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        dev_telegram_user_id: int,
        on_back: Callable[[str], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_bookings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_bookings = on_open_bookings
        self.on_open_custom_request = on_open_custom_request
        self.tour_code: str | None = None
        self.order_id: int | None = None
        self._last_entry: PaymentEntryRead | None = None

        lg = default_language_code
        self.nav_back = ft.TextButton(
            shell(lg, "back_to_preparation"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back(self.tour_code or ""),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self._heading = ft.Text(shell(lg, "payment_title"), size=26, weight=ft.FontWeight.BOLD)
        self._intro = ft.Text(shell(lg, "payment_intro"), color=ft.Colors.ON_SURFACE_VARIANT)
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "starting_payment")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=10)
        self.pay_now_button = ft.ElevatedButton(shell(lg, "pay_now"), on_click=lambda _: self.page.run_task(self._pay_now_async))
        self.bookings_after_pay_button = ft.ElevatedButton(
            shell(lg, "cta_back_to_bookings"),
            visible=False,
            on_click=lambda _: self.on_open_bookings(),
        )
        self.support_note = ft.Text(
            shell(lg, "payment_support_body"),
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
            visible=False,
        )
        self.support_log_button = ft.OutlinedButton(
            shell(lg, "support_cta_log_request"),
            visible=False,
            on_click=lambda _: self.page.run_task(self._log_support_payment_async),
        )

    def set_context(self, *, tour_code: str, order_id: int) -> None:
        self.tour_code = tour_code
        self.order_id = order_id

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_preparation")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self._heading.value = shell(lg, "payment_title")
        self._intro.value = shell(lg, "payment_intro")
        self.pay_now_button.text = shell(lg, "pay_now")
        self.bookings_after_pay_button.text = shell(lg, "cta_back_to_bookings")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "starting_payment")
        self.support_note.value = shell(lg, "payment_support_body")
        self.support_log_button.text = shell(lg, "support_cta_log_request")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.loading_row,
            self.error_text,
            self._heading,
            self._intro,
            self.support_note,
            self.support_log_button,
            self.body_column,
            ft.Row([self.pay_now_button, self.bookings_after_pay_button], alignment=ft.MainAxisAlignment.START, wrap=True),
        )

    async def load_payment_entry(self) -> None:
        self.sync_shell_labels()
        if self.order_id is None:
            self._show_error("Missing order reference.")
            self.pay_now_button.visible = False
            self.bookings_after_pay_button.visible = False
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.support_note.visible = False
        self.support_log_button.visible = False
        self.body_column.controls.clear()
        self.page.update()

        try:
            entry = await self.api_client.start_payment_entry(
                order_id=self.order_id,
                telegram_user_id=self.dev_telegram_user_id,
            )
        except httpx.HTTPStatusError as exc:
            lg_err = self.language_code
            if exc.response is not None and exc.response.status_code == 400:
                self._show_error(shell(lg_err, "payment_screen_unavailable_hold"))
            else:
                self._show_error(
                    CatalogScreen._http_error_message(
                        exc,
                        default=shell(lg_err, "payment_screen_load_error_generic"),
                    )
                )
            self.pay_now_button.visible = False
            self.bookings_after_pay_button.visible = False
        except Exception:
            self._show_error(shell(self.language_code, "payment_screen_load_error_generic"))
            self.pay_now_button.visible = False
            self.bookings_after_pay_button.visible = False
        else:
            self._render_entry(entry)
        finally:
            self._set_loading(False)
            self.page.update()

    async def _log_support_payment_async(self) -> None:
        lg = self.language_code
        if self.order_id is None:
            return
        try:
            r = await self.api_client.post_support_request(
                telegram_user_id=self.dev_telegram_user_id,
                order_id=self.order_id,
                screen_hint="payment",
            )
        except Exception:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        if r.recorded and r.handoff_id is not None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_success", ref=str(r.handoff_id))),
                action="OK",
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
        self.page.snack_bar.open = True
        self.page.update()

    def _render_entry(self, entry: PaymentEntryRead) -> None:
        self._last_entry = entry
        order = entry.order
        expires = order.reservation_expires_at
        lg = self.language_code
        self.support_note.visible = True
        self.support_log_button.visible = True
        self._intro.value = shell(lg, "payment_intro_active_hold")
        expiry_line = (
            shell(lg, "line_pay_before", when=CatalogScreen._format_datetime(expires))
            if expires
            else shell(lg, "line_reservation_expiry_na")
        )
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(shell(lg, "line_reservation_ref", id=str(order.id)), weight=ft.FontWeight.W_600),
                        ft.Text(expiry_line),
                        ft.Text(_hold_timer_hint(expires, self.language_code)),
                        ft.Text(
                            shell(
                                lg,
                                "line_amount_due",
                                amount=CatalogScreen._format_price(order.total_amount),
                                currency=order.currency,
                            )
                        ),
                        ft.Text(shell(lg, "line_payment_session_ref", ref=entry.payment_session_reference)),
                        ft.Text(
                            shell(
                                lg,
                                "line_payment_status",
                                status=_payment_status_user_label(entry.payment.status, self.language_code),
                            ),
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            shell(lg, "payment_stub_notice"),
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=8,
                ),
            ),
        ]
        self.pay_now_button.visible = True
        self.pay_now_button.disabled = False
        self.bookings_after_pay_button.visible = False

    async def _pay_now_async(self) -> None:
        entry = self._last_entry
        if entry is None or self.order_id is None:
            return
        if entry.payment_url:
            self.page.launch_url(entry.payment_url)
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.page.update()
        try:
            recon = await self.api_client.complete_mock_payment(
                order_id=self.order_id,
                telegram_user_id=self.dev_telegram_user_id,
            )
        except httpx.HTTPStatusError as exc:
            lg = self.language_code
            if exc.response is not None and exc.response.status_code == 403:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(shell(lg, "payment_mock_disabled_user_message")),
                    action="OK",
                )
                self.page.snack_bar.open = True
            else:
                message = CatalogScreen._http_error_message(
                    exc,
                    default=shell(lg, "payment_confirm_error_generic"),
                )
                self._show_error(message)
        except Exception:
            self._show_error(shell(self.language_code, "payment_confirm_error_generic"))
        else:
            self._render_payment_success(recon)
        finally:
            self._set_loading(False)
            self.page.update()

    def _render_payment_success(self, recon: PaymentReconciliationRead) -> None:
        lg = self.language_code
        order = recon.order
        self.support_note.visible = False
        self.support_log_button.visible = False
        self._heading.value = shell(lg, "payment_success_title")
        self._intro.value = shell(lg, "payment_success_intro")
        self.pay_now_button.visible = False
        self.bookings_after_pay_button.visible = True
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(shell(lg, "line_reservation_ref", id=str(order.id)), weight=ft.FontWeight.W_600),
                        ft.Text(
                            shell(
                                lg,
                                "line_payment_status",
                                status=_payment_status_user_label(order.payment_status, self.language_code),
                            ),
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(shell(lg, "payment_success_booking_status"), weight=ft.FontWeight.W_500),
                    ],
                    spacing=8,
                ),
            ),
        ]

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

    def _set_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading


class MyBookingsScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        language_code: str,
        telegram_user_id: int | None,
        on_back_catalog: Callable[[], None],
        on_open_booking: Callable[[int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.telegram_user_id = telegram_user_id
        self.on_back_catalog = on_back_catalog
        self.on_open_booking = on_open_booking
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request

        lg = language_code
        self.nav_back = ft.TextButton(shell(lg, "back_to_catalog"), on_click=lambda _: self.on_back_catalog())
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self.page_title = ft.Text(shell(lg, "my_bookings_title"), size=26, weight=ft.FontWeight.BOLD)
        self.page_subtitle = ft.Text(
            shell(lg, "my_bookings_subtitle"),
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text(shell(lg, "loading_bookings"))],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.items_column = ft.Column(spacing=12)
        self.support_banner_title = ft.Text(
            shell(lg, "support_banner_title"),
            size=16,
            weight=ft.FontWeight.W_600,
            visible=False,
        )
        self.support_banner_body = ft.Text(
            shell(lg, "support_banner_body"),
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
            visible=False,
        )
        self.support_banner_button = ft.OutlinedButton(
            shell(lg, "support_cta_log_request"),
            visible=False,
            on_click=lambda _: self.page.run_task(self._log_support_my_bookings_async),
        )

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_catalog")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self.page_title.value = shell(lg, "my_bookings_title")
        self.page_subtitle.value = shell(lg, "my_bookings_subtitle")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "loading_bookings")
        self.support_banner_title.value = shell(lg, "support_banner_title")
        self.support_banner_body.value = shell(lg, "support_banner_body")
        self.support_banner_button.text = shell(lg, "support_cta_log_request")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.page_title,
            self.page_subtitle,
            self.loading_row,
            self.error_text,
            self.items_column,
            self.support_banner_title,
            self.support_banner_body,
            self.support_banner_button,
        )

    async def load_bookings(self) -> None:
        self.sync_shell_labels()
        self.loading_row.visible = True
        self.error_text.visible = False
        self.page.update()
        if self.telegram_user_id is None:
            self._show_error(shell(self.language_code, "identity_required_my_data"))
            self._render(None)
            self.loading_row.visible = False
            self.page.update()
            return
        try:
            data = await self.api_client.list_my_bookings(
                telegram_user_id=self.telegram_user_id,
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            self._show_error(CatalogScreen._http_error_message(exc, default="Unable to load bookings."))
            self._render(None)
        except Exception:
            self._show_error("Unable to load bookings.")
            self._render(None)
        else:
            self._render(data)
        finally:
            self.loading_row.visible = False
            self.page.update()

    def _render(self, data: MiniAppBookingsListRead | None) -> None:
        self.items_column.controls.clear()
        self.support_banner_title.visible = False
        self.support_banner_body.visible = False
        self.support_banner_button.visible = False
        if data is None:
            return
        lg = self.language_code
        if not data.items:
            self.items_column.controls.append(
                ft.Text(shell(lg, "no_bookings"), color=ft.Colors.ON_SURFACE_VARIANT)
            )
            return
        confirmed, active, history, history_omitted = partition_bookings_for_my_bookings_ui(data.items)
        sections: list[tuple[str, str, list[MiniAppBookingListItemRead], bool]] = [
            ("bookings_section_confirmed_title", "bookings_section_confirmed_hint", confirmed, False),
            ("bookings_section_active_title", "bookings_section_active_hint", active, False),
            ("bookings_section_history_title", "bookings_section_history_hint", history, True),
        ]
        for title_key, hint_key, bucket, is_history in sections:
            if not bucket:
                continue
            self.items_column.controls.append(
                ft.Column(
                    [
                        ft.Text(shell(lg, title_key), size=20, weight=ft.FontWeight.W_600),
                        ft.Text(shell(lg, hint_key), size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=4,
                )
            )
            for item in bucket:
                self.items_column.controls.append(self._booking_card(item))
            if is_history and history_omitted > 0:
                self.items_column.controls.append(
                    ft.Text(
                        shell(lg, "bookings_history_truncated_note", n=str(history_omitted)),
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    )
                )
        self.support_banner_title.visible = True
        self.support_banner_body.visible = True
        self.support_banner_button.visible = True

    async def _log_support_my_bookings_async(self) -> None:
        lg = self.language_code
        if self.telegram_user_id is None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "identity_required_my_data")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        try:
            r = await self.api_client.post_support_request(
                telegram_user_id=self.telegram_user_id,
                order_id=None,
                screen_hint="my_bookings",
            )
        except Exception:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        if r.recorded and r.handoff_id is not None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_success", ref=str(r.handoff_id))),
                action="OK",
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
        self.page.snack_bar.open = True
        self.page.update()

    def _booking_card(self, item: MiniAppBookingListItemRead) -> ft.Control:
        lg = self.language_code
        s = item.summary
        tour = s.tour
        title = tour.localized_content.title
        dep = CatalogScreen._format_datetime(tour.departure_datetime)
        amount = f"{CatalogScreen._format_price(s.order.total_amount)} {s.order.currency}"
        seats_line = shell(
            lg,
            "booking_seats_amount",
            amount=amount,
            n=str(s.order.seats_count),
        )
        bk_label, pay_label = booking_facade_labels(lg, item.facade_state.value)
        oid = s.order.id
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=16,
            padding=16,
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(dep, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(seats_line, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(bk_label, weight=ft.FontWeight.W_500),
                    ft.Text(pay_label, color=ft.Colors.ON_SURFACE_VARIANT, size=13),
                    ft.Row(
                        [
                            ft.FilledButton(
                                shell(lg, "booking_open"),
                                on_click=lambda _, order_id=oid: self.on_open_booking(order_id),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=6,
            ),
        )

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True


class BookingDetailScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        language_code: str,
        telegram_user_id: int | None,
        on_back_to_bookings: Callable[[], None],
        on_browse_tours: Callable[[], None],
        on_pay_now: Callable[[str, int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.telegram_user_id = telegram_user_id
        self.on_back_to_bookings = on_back_to_bookings
        self.on_browse_tours = on_browse_tours
        self.on_pay_now = on_pay_now
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        self.order_id: int | None = None
        self._last_detail: MiniAppBookingDetailRead | None = None

        lg = language_code
        self.nav_back_bookings = ft.TextButton(
            shell(lg, "cta_back_to_bookings"),
            on_click=lambda _: self.on_back_to_bookings(),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self.page_title = ft.Text(shell(lg, "booking_details_title"), size=22, weight=ft.FontWeight.BOLD)
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "loading_booking_detail")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=12)
        self.support_note = ft.Text(
            shell(lg, "booking_support_body"),
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
            visible=False,
        )
        self.support_log_button = ft.OutlinedButton(
            shell(lg, "support_cta_log_request"),
            visible=False,
            on_click=lambda _: self.page.run_task(self._log_support_booking_async),
        )

    def set_order_id(self, order_id: int) -> None:
        self.order_id = order_id

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back_bookings.text = shell(lg, "cta_back_to_bookings")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self.page_title.value = shell(lg, "booking_details_title")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "loading_booking_detail")
        self.support_note.value = shell(lg, "booking_support_body")
        self.support_log_button.text = shell(lg, "support_cta_log_request")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back_bookings, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.page_title,
            self.loading_row,
            self.error_text,
            self.body_column,
            self.support_note,
            self.support_log_button,
        )

    async def load_detail(self) -> None:
        self.sync_shell_labels()
        if self.order_id is None:
            return
        if self.telegram_user_id is None:
            self._show_error(shell(self.language_code, "identity_required_my_data"))
            self._render(None)
            self.page.update()
            return
        self.loading_row.visible = True
        self.error_text.visible = False
        self.page.update()
        try:
            detail = await self.api_client.get_booking_status(
                order_id=self.order_id,
                telegram_user_id=self.telegram_user_id,
                language_code=self.language_code,
            )
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                self._show_error("This booking was not found or you do not have access.")
            else:
                self._show_error(CatalogScreen._http_error_message(exc, default="Unable to load this booking."))
            self._render(None)
        except Exception:
            self._show_error("Unable to load this booking.")
            self._render(None)
        else:
            self._render(detail)
        finally:
            self.loading_row.visible = False
            self.page.update()

    def _render(self, detail: MiniAppBookingDetailRead | None) -> None:
        self._last_detail = detail
        self.body_column.controls.clear()
        self.support_note.visible = False
        self.support_log_button.visible = False
        if detail is None:
            return
        s = detail.summary
        order = s.order
        tour = s.tour
        bp = s.boarding_point
        boarding_lines = (
            [ft.Text(f"Boarding: {bp.city}, {bp.address} ({bp.time})", color=ft.Colors.ON_SURFACE_VARIANT)]
            if bp
            else []
        )
        timer_line = (
            [ft.Text(_hold_timer_hint(order.reservation_expires_at, self.language_code), color=ft.Colors.ON_SURFACE_VARIANT)]
            if detail.facade_state == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION
            else []
        )
        pay_hint = (
            [ft.Text(detail.payment_session_hint, size=12, color=ft.Colors.ON_SURFACE_VARIANT)]
            if detail.payment_session_hint
            else []
        )
        lg_detail = self.language_code
        bk_label, pay_label = booking_facade_labels(lg_detail, detail.facade_state.value)
        context_note = booking_detail_context_note(self.language_code, detail.facade_state)
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(shell(lg_detail, "line_reservation_ref", id=str(order.id)), weight=ft.FontWeight.W_600),
                        ft.Text(tour.localized_content.title, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{CatalogScreen._format_datetime(tour.departure_datetime)} → "
                            f"{CatalogScreen._format_datetime(tour.return_datetime)}",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            f"Seats: {order.seats_count} · Amount: "
                            f"{CatalogScreen._format_price(order.total_amount)} {order.currency}",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        *boarding_lines,
                        ft.Divider(),
                        ft.Text(bk_label, weight=ft.FontWeight.W_600),
                        ft.Text(pay_label, color=ft.Colors.ON_SURFACE_VARIANT),
                        *timer_line,
                        *pay_hint,
                    ],
                    spacing=8,
                ),
            ),
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=12,
                padding=12,
                content=ft.Text(context_note, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
            ),
        ]
        cta_row: list[ft.Control] = []
        lg = self.language_code
        if detail.primary_cta == MiniAppBookingPrimaryCta.PAY_NOW:
            cta_row.append(
                ft.FilledButton(
                    shell(lg, "cta_pay_now"),
                    on_click=lambda _: self.on_pay_now(tour.code, order.id),
                )
            )
        elif detail.primary_cta == MiniAppBookingPrimaryCta.BROWSE_TOURS:
            cta_row.append(
                ft.FilledButton(
                    shell(lg, "cta_browse_tours"),
                    on_click=lambda _: self.on_browse_tours(),
                )
            )
        else:
            cta_row.append(
                ft.OutlinedButton(
                    shell(lg, "cta_back_to_bookings"),
                    on_click=lambda _: self.on_back_to_bookings(),
                )
            )
        self.body_column.controls.append(ft.Row(cta_row, alignment=ft.MainAxisAlignment.START))
        self.support_note.visible = True
        self.support_log_button.visible = True

    async def _log_support_booking_async(self) -> None:
        lg = self.language_code
        if self.order_id is None:
            return
        if self.telegram_user_id is None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "identity_required_my_data")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        try:
            r = await self.api_client.post_support_request(
                telegram_user_id=self.telegram_user_id,
                order_id=self.order_id,
                screen_hint="booking_detail",
            )
        except Exception:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        if r.recorded and r.handoff_id is not None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_success", ref=str(r.handoff_id))),
                action="OK",
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "support_request_error")),
                action="OK",
            )
        self.page.snack_bar.open = True
        self.page.update()

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True


class MyRequestsListScreen:
    """Track 5d: customer RFQ list — read-only summaries from Layer C."""

    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        language_code: str,
        telegram_user_id: int | None,
        on_back_catalog: Callable[[], None],
        on_open_detail: Callable[[int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.telegram_user_id = telegram_user_id
        self.on_back_catalog = on_back_catalog
        self.on_open_detail = on_open_detail
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        lg = language_code
        self.nav_back = ft.TextButton(
            shell(lg, "back_to_catalog"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back_catalog(),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self._title = ft.Text(shell(lg, "my_requests_title"), size=24, weight=ft.FontWeight.BOLD)
        self._subtitle = ft.Text(shell(lg, "my_requests_subtitle"), size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "my_requests_loading")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.items_column = ft.Column(spacing=12)

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_catalog")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        self._title.value = shell(lg, "my_requests_title")
        self._subtitle.value = shell(lg, "my_requests_subtitle")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "my_requests_loading")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self._title,
            self._subtitle,
            self.loading_row,
            self.error_text,
            self.items_column,
        )

    async def load_list(self) -> None:
        self.sync_shell_labels()
        self.loading_row.visible = True
        self.error_text.visible = False
        self.items_column.controls.clear()
        self.page.update()
        if self.telegram_user_id is None:
            self.error_text.value = shell(self.language_code, "identity_required_my_data")
            self.error_text.visible = True
            self._render(None)
            self.loading_row.visible = False
            self.page.update()
            return
        try:
            data = await self.api_client.list_custom_requests_for_customer(
                telegram_user_id=self.telegram_user_id,
            )
        except httpx.HTTPStatusError as exc:
            self.error_text.value = CatalogScreen._http_error_message(
                exc,
                default=shell(self.language_code, "my_requests_error_load_list"),
            )
            self.error_text.visible = True
            self._render(None)
        except Exception:
            self.error_text.value = shell(self.language_code, "my_requests_error_load_list")
            self.error_text.visible = True
            self._render(None)
        else:
            self._render(data)
        finally:
            self.loading_row.visible = False
            self.page.update()

    def _render(self, data: MiniAppCustomRequestCustomerListRead | None) -> None:
        self.items_column.controls.clear()
        if data is None:
            return
        lg = self.language_code
        if not data.items:
            self.items_column.controls.append(
                ft.Text(shell(lg, "my_requests_empty"), color=ft.Colors.ON_SURFACE_VARIANT)
            )
            return
        n = len(data.items)
        n_closed = sum(1 for it in data.items if is_request_status_terminal(it.status))
        n_active = n - n_closed
        summary_key = my_requests_list_summary_key(n_total=n, n_active=n_active, n_closed=n_closed)
        if summary_key is not None:
            self.items_column.controls.append(
                ft.Text(
                    shell(lg, summary_key),
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        self.items_column.controls.append(
            ft.Text(shell(lg, "my_requests_list_expectation_note"), size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        )
        for item in data.items:
            self.items_column.controls.append(self._request_card(item))

    def _request_card(self, item: MiniAppCustomRequestCustomerSummaryRead) -> ft.Control:
        lg = self.language_code
        st_label = request_status_user_label(lg, item.status)
        type_label = request_type_user_label(lg, item.request_type)
        created_label = _format_request_datetime(item.created_at)
        subject = _request_subject_line(
            lg=lg,
            request_type_label=type_label,
            travel_start=item.travel_date_start,
            travel_end=item.travel_date_end,
            group_size=item.group_size,
            route_notes_preview=item.route_notes_preview,
        )
        preview_line: list[ft.Control] = [
            ft.Text(
                shell(lg, "my_requests_row_meta", type=type_label, created=created_label),
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(subject, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
        ]
        if (item.activity_preview_title or "").strip():
            preview_line.append(
                ft.Text(
                    f"{shell(lg, 'my_requests_list_activity_prefix')} {item.activity_preview_title.strip()}",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=16,
            padding=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                shell(lg, "my_requests_row_reference", id=str(item.id)),
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=999,
                                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                content=ft.Text(st_label, size=11, weight=ft.FontWeight.W_600),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    *preview_line,
                    ft.Row(
                        [
                            ft.FilledButton(
                                shell(lg, "my_requests_row_view"),
                                on_click=lambda _, rid=item.id: self.on_open_detail(rid),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=6,
            ),
        )


class MyRequestDetailScreen:
    """Track 5d: single RFQ detail + dominant CTA from existing APIs only."""

    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        language_code: str,
        telegram_user_id: int | None,
        on_back_list: Callable[[], None],
        on_open_bridge: Callable[[int], None],
        on_continue_payment: Callable[[str, int], None],
        on_open_booking: Callable[[int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_custom_request: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.telegram_user_id = telegram_user_id
        self.on_back_list = on_back_list
        self.on_open_bridge = on_open_bridge
        self.on_continue_payment = on_continue_payment
        self.on_open_booking = on_open_booking
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.on_open_custom_request = on_open_custom_request
        self.request_id: int | None = None
        self._payment_tour_code: str | None = None
        self._cta_kind: DetailPrimaryCtaKind = DetailPrimaryCtaKind.NONE
        self._cta_order_id: int | None = None

        lg = language_code
        self.nav_back = ft.TextButton(
            shell(lg, "my_requests_detail_back"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back_list(),
        )
        self.nav_help = ft.TextButton(shell(lg, "btn_help"), on_click=lambda _: self.on_help())
        self.nav_custom_trip = ft.TextButton(
            shell(lg, "nav_custom_trip"),
            on_click=lambda _: self.on_open_custom_request(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text(shell(lg, "my_requests_loading")),
            ],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=12)
        # FilledButton requires non-empty content (or icon) even when hidden — else Flet raises on build.
        self._primary_cta_button = ft.FilledButton(
            shell(lg, "my_requests_cta_continue_booking"),
            visible=False,
            on_click=lambda _: self._on_primary_cta(),
        )
        self._cta_caption = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT, visible=False)
        self._cta_block = ft.Column(
            spacing=6,
            visible=False,
            controls=[self._cta_caption, self._primary_cta_button],
        )

    def set_request_id(self, request_id: int) -> None:
        self.request_id = request_id

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "my_requests_detail_back")
        self.nav_help.text = shell(lg, "btn_help")
        self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.nav_settings.text = shell(lg, "settings")
        if self.loading_row.controls:
            self.loading_row.controls[1].value = shell(lg, "my_requests_loading")

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row(
                [self.nav_back, self.nav_help, self.nav_custom_trip, self.nav_settings],
                alignment=ft.MainAxisAlignment.START,
                wrap=True,
            ),
            self.loading_row,
            self.error_text,
            self.body_column,
            self._cta_block,
        )

    def _on_primary_cta(self) -> None:
        rid = self.request_id
        if rid is None:
            return
        kind = self._cta_kind
        oid = self._cta_order_id
        tc = self._payment_tour_code
        if kind == DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT and tc is not None and oid is not None:
            self.on_continue_payment(tc, oid)
        elif kind == DetailPrimaryCtaKind.CONTINUE_BOOKING:
            self.on_open_bridge(rid)
        elif kind == DetailPrimaryCtaKind.OPEN_BOOKING and oid is not None:
            self.on_open_booking(oid)

    async def load_detail(self) -> None:
        self.sync_shell_labels()
        self.body_column.controls.clear()
        self._primary_cta_button.visible = False
        self._cta_caption.visible = False
        self._cta_block.visible = False
        self.error_text.visible = False
        self._cta_kind = DetailPrimaryCtaKind.NONE
        self._cta_order_id = None
        self._payment_tour_code = None
        if self.request_id is None:
            return
        if self.telegram_user_id is None:
            self.error_text.value = shell(self.language_code, "identity_required_my_data")
            self.error_text.visible = True
            self.page.update()
            return
        self.loading_row.visible = True
        self.page.update()
        detail: MiniAppCustomRequestCustomerDetailRead | None = None
        bookings: MiniAppBookingsListRead | None = None
        prep: MiniAppBridgeExecutionPreparationResponse | None = None
        prep_http_not_found = False
        try:
            detail = await self.api_client.get_custom_request_for_customer(
                request_id=self.request_id,
                telegram_user_id=self.telegram_user_id,
            )
        except httpx.HTTPStatusError as exc:
            self.error_text.value = CatalogScreen._http_error_message(
                exc,
                default=shell(self.language_code, "my_requests_error_load_detail"),
            )
            self.error_text.visible = True
        except Exception:
            self.error_text.value = shell(self.language_code, "my_requests_error_load_detail")
            self.error_text.visible = True
        try:
            bookings = await self.api_client.list_my_bookings(
                telegram_user_id=self.telegram_user_id,
                language_code=self.language_code,
            )
        except Exception:
            bookings = None
        if detail is not None:
            try:
                prep = await self.api_client.get_booking_bridge_preparation(
                    request_id=self.request_id,
                    telegram_user_id=self.telegram_user_id,
                    language_code=self.language_code,
                )
            except httpx.HTTPStatusError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    prep_http_not_found = True
                prep = None
            except Exception:
                prep = None

        matching: MiniAppBookingListItemRead | None = None
        hold_order_id: int | None = None
        elig: MiniAppBridgePaymentEligibilityRead | None = None
        tour_code_for_match: str | None = None
        if prep is not None:
            tour_code_for_match = prep.tour_code
        elif detail is not None:
            tour_code_for_match = detail.latest_booking_bridge_tour_code
        if tour_code_for_match is not None and bookings is not None:
            matching = pick_booking_for_bridge_tour(bookings.items, tour_code_for_match)
            if (
                matching is not None
                and matching.facade_state == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION
            ):
                hold_order_id = matching.summary.order.id
        if prep is not None and hold_order_id is not None:
            try:
                elig = await self.api_client.get_booking_bridge_payment_eligibility(
                    request_id=self.request_id,
                    telegram_user_id=self.telegram_user_id,
                    order_id=hold_order_id,
                )
            except Exception:
                elig = None

        if prep is not None:
            self._payment_tour_code = prep.tour_code
        elif matching is not None:
            self._payment_tour_code = matching.summary.tour.code
        else:
            self._payment_tour_code = tour_code_for_match

        if detail is not None:
            self._cta_kind, self._cta_order_id = resolve_detail_primary_cta(
                prep=prep,
                payment_elig=elig,
                hold_order_id=hold_order_id,
                matching_booking=matching,
                latest_booking_bridge_status=detail.latest_booking_bridge_status,
            )
        else:
            self._cta_kind, self._cta_order_id = DetailPrimaryCtaKind.NONE, None

        if detail is not None:
            self._render_body(
                detail,
                prep,
                prep_http_not_found,
                matching,
                cta_kind=self._cta_kind,
            )
        self._sync_primary_cta_button()
        self.loading_row.visible = False
        self.page.update()

    def _render_body(
        self,
        detail: MiniAppCustomRequestCustomerDetailRead,
        prep: MiniAppBridgeExecutionPreparationResponse | None,
        prep_http_not_found: bool,
        matching: MiniAppBookingListItemRead | None,
        *,
        cta_kind: DetailPrimaryCtaKind,
    ) -> None:
        lg = self.language_code
        status_label = request_status_user_label(lg, detail.status)
        type_label = request_type_user_label(lg, detail.request_type)
        end_part = (
            shell(lg, "my_requests_detail_date_end", end=str(detail.travel_date_end))
            if detail.travel_date_end
            else ""
        )
        created_when = _format_request_datetime(detail.created_at)
        lines: list[ft.Control] = [
            ft.Text(
                shell(lg, "my_requests_detail_header_ref", id=str(detail.id)),
                size=22,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                shell(lg, "my_requests_detail_created_line", when=created_when),
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(shell(lg, "my_requests_detail_type", label=type_label)),
            ft.Text(
                shell(
                    lg,
                    "my_requests_detail_dates",
                    start=str(detail.travel_date_start),
                    end=end_part,
                )
            ),
        ]
        if detail.group_size is not None and detail.group_size > 0:
            lines.append(
                ft.Text(
                    shell(lg, "my_requests_detail_group_size", n=str(detail.group_size)),
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        lines.append(
            ft.Container(
                padding=ft.padding.only(top=8),
                content=ft.Text(
                    shell(lg, "my_requests_section_what_you_asked"),
                    weight=ft.FontWeight.W_600,
                    size=14,
                ),
            )
        )
        lines.append(
            ft.Text(
                (detail.route_notes_preview or "").strip() or shell(lg, "my_requests_route_notes_empty"),
                size=14,
                color=ft.Colors.ON_SURFACE,
            )
        )
        lines.append(
            ft.Container(
                padding=ft.padding.only(top=10),
                content=ft.Text(
                    shell(lg, "my_requests_section_current_status"),
                    weight=ft.FontWeight.W_600,
                    size=14,
                ),
            )
        )
        lines.append(ft.Text(status_label, size=14, color=ft.Colors.ON_SURFACE_VARIANT))
        lines.append(
            ft.Container(
                padding=ft.padding.only(top=10),
                content=ft.Text(
                    shell(lg, "my_requests_section_current_update"),
                    weight=ft.FontWeight.W_600,
                    size=14,
                ),
            )
        )
        if detail.activity_preview is not None:
            ap = detail.activity_preview
            title_s = (ap.title or "").strip()
            message_s = (ap.message or "").strip()
            disc_s = (ap.preview_disclaimer or "").strip()
            if title_s or message_s or disc_s:
                ap_children: list[ft.Control] = []
                if title_s:
                    ap_children.append(ft.Text(title_s, size=14, weight=ft.FontWeight.W_500))
                if message_s:
                    ap_children.append(ft.Text(message_s, size=13, color=ft.Colors.ON_SURFACE_VARIANT))
                if disc_s:
                    ap_children.append(ft.Text(disc_s, size=11, color=ft.Colors.ON_SURFACE_VARIANT))
                lines.append(
                    ft.Container(
                        padding=ft.padding.only(top=10),
                        content=ft.Column(ap_children, spacing=6),
                    )
                )
        if detail.selected_offer_summary is not None:
            sos = detail.selected_offer_summary
            lines.append(
                ft.Container(
                    padding=ft.padding.only(top=10),
                    content=ft.Column(
                        [
                            ft.Text(
                                shell(lg, "my_requests_detail_selected_offer_title"),
                                weight=ft.FontWeight.W_600,
                                size=13,
                            ),
                            *(
                                [
                                    ft.Text(
                                        shell(
                                            lg,
                                            "my_requests_detail_selected_price",
                                            amount=str(sos.quoted_price),
                                            currency=sos.quoted_currency or "",
                                        ),
                                        size=13,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    )
                                ]
                                if sos.quoted_price is not None and (sos.quoted_currency or "").strip()
                                else []
                            ),
                            *(
                                [
                                    ft.Text(
                                        shell(lg, "my_requests_detail_selected_message", text=sos.supplier_message_excerpt),
                                        size=13,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    )
                                ]
                                if (sos.supplier_message_excerpt or "").strip()
                                else []
                            ),
                            *(
                                [
                                    ft.Text(
                                        shell(
                                            lg,
                                            "my_requests_detail_selected_modes",
                                            sales=sos.declared_sales_mode or "—",
                                            payment=sos.declared_payment_mode or "—",
                                        ),
                                        size=12,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    )
                                ]
                                if sos.declared_sales_mode or sos.declared_payment_mode
                                else []
                            ),
                        ],
                        spacing=4,
                    ),
                )
            )
        ctx_key, _ = detail_context_line_keys(
            prep=prep,
            prep_http_not_found=prep_http_not_found,
            latest_booking_bridge_status=detail.latest_booking_bridge_status,
        )
        if ctx_key:
            lines.append(ft.Text(shell(lg, ctx_key), color=ft.Colors.ON_SURFACE_VARIANT))
        if prep is not None and not prep.self_service_available:
            bm = (prep.blocked_message or "").strip()
            if bm:
                lines.append(
                    ft.Container(
                        padding=ft.padding.only(top=4),
                        content=ft.Text(bm, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    )
                )
        if matching is not None:
            t = (matching.summary.tour.localized_content.title or "").strip()
            oid = matching.summary.order.id
            line = f"{t} · #{oid}" if t else f"#{oid}"
            lines.append(
                ft.Text(
                    shell(lg, "my_requests_detail_bridge_line", line=line),
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        next_key = detail_next_step_key(status=detail.status, cta_kind=cta_kind)
        next_body = (shell(lg, next_key) or "").strip() or shell(lg, "my_requests_detail_next_generic")
        lines.append(
            ft.Container(
                padding=ft.padding.only(top=10),
                content=ft.Column(
                    [
                        ft.Text(
                            shell(lg, "my_requests_detail_next_heading"),
                            weight=ft.FontWeight.W_600,
                            size=13,
                        ),
                        ft.Text(next_body, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=4,
                ),
            )
        )
        self.body_column.controls = lines

    def _sync_primary_cta_button(self) -> None:
        lg = self.language_code
        kind = self._cta_kind
        if kind == DetailPrimaryCtaKind.NONE:
            self._primary_cta_button.visible = False
            self._cta_caption.visible = False
            self._cta_block.visible = False
            return
        self._cta_block.visible = True
        self._primary_cta_button.visible = True
        self._cta_caption.visible = True
        if kind == DetailPrimaryCtaKind.CONTINUE_TO_PAYMENT:
            self._primary_cta_button.content = shell(lg, "my_requests_cta_continue_payment")
            self._cta_caption.value = shell(lg, "my_requests_cta_caption_payment")
        elif kind == DetailPrimaryCtaKind.CONTINUE_BOOKING:
            self._primary_cta_button.content = shell(lg, "my_requests_cta_continue_booking")
            self._cta_caption.value = shell(lg, "my_requests_cta_caption_booking")
        else:
            self._primary_cta_button.content = shell(lg, "my_requests_cta_open_booking")
            self._cta_caption.value = shell(lg, "my_requests_cta_caption_open_booking")


class CustomRequestScreen:
    """Track 4 / U1: structured custom request from Mini App (no order created)."""

    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        dev_telegram_user_id: int,
        on_close: Callable[[], None],
        language_code: str,
        on_continue_rfq_booking: Callable[[int], None] | None = None,
        on_open_my_requests: Callable[[], None] | None = None,
    ) -> None:
        self.page = page
        self.api_client = api_client
        self._dev_telegram_user_id = dev_telegram_user_id
        self.on_close = on_close
        self.on_continue_rfq_booking = on_continue_rfq_booking
        self.on_open_my_requests = on_open_my_requests
        self.language_code = language_code
        self._last_prefill: CustomRequestPrefill | None = None
        lg = language_code
        self.nav_back = ft.TextButton(shell(lg, "back"), icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.on_close())
        self.title = ft.Text(shell(lg, "custom_request_title"), size=26, weight=ft.FontWeight.BOLD)
        self.intro = ft.Text(shell(lg, "custom_request_intro"), size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.fields_legend = ft.Text(
            shell(lg, "custom_request_fields_legend"),
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.prefill_banner_label = ft.Text("", size=13)
        self.prefill_banner = ft.Container(
            visible=False,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=12,
            padding=12,
            content=self.prefill_banner_label,
        )
        self.request_type = ft.Dropdown(
            label=shell(lg, "custom_request_field_type"),
            width=400,
            value="group_trip",
            options=[
                ft.dropdown.Option("group_trip", shell(lg, "custom_request_opt_group_trip")),
                ft.dropdown.Option("custom_route", shell(lg, "custom_request_opt_custom_route")),
                ft.dropdown.Option("other", shell(lg, "custom_request_opt_other")),
            ],
        )
        self.start_date = ft.TextField(label=shell(lg, "custom_request_field_start"), width=400)
        self.end_date = ft.TextField(label=shell(lg, "custom_request_field_end"), width=400)
        self.route_notes = ft.TextField(
            label=shell(lg, "custom_request_field_route"),
            hint_text=shell(lg, "custom_request_field_route_hint"),
            width=400,
            multiline=True,
            min_lines=2,
            max_lines=6,
        )
        self.group_size = ft.TextField(label=shell(lg, "custom_request_field_group"), width=200)
        self.special = ft.TextField(
            label=shell(lg, "custom_request_field_special"),
            width=400,
            multiline=True,
            min_lines=2,
            max_lines=4,
        )
        self.submit_btn = ft.FilledButton(
            shell(lg, "custom_request_submit"),
            on_click=lambda _: self.page.run_task(self._submit_async),
        )
        self._submit_in_progress = False

    def apply_prefill(self, prefill: CustomRequestPrefill | None) -> None:
        """U1: optional hints from a catalog tour the user was viewing (separate Mode 3 request)."""
        lg = self.language_code
        if prefill is None:
            self._reset_form_to_defaults()
            return
        self._last_prefill = prefill
        self.request_type.value = "custom_route"
        self.start_date.value = prefill.departure_date_iso
        self.end_date.value = prefill.return_date_iso or ""
        self.route_notes.value = shell(
            lg,
            "custom_request_prefill_route_template",
            code=prefill.tour_code,
            title=prefill.tour_title,
        )
        self.group_size.value = ""
        self.special.value = ""
        self.prefill_banner_label.value = shell(lg, "custom_request_prefill_banner", code=prefill.tour_code)
        self.prefill_banner.visible = True

    def _reset_form_to_defaults(self) -> None:
        lg = self.language_code
        self._last_prefill = None
        self.request_type.value = "group_trip"
        self.start_date.value = ""
        self.end_date.value = ""
        self.route_notes.value = ""
        self.group_size.value = ""
        self.special.value = ""
        self.prefill_banner.visible = False
        self.prefill_banner_label.value = ""
        self.route_notes.hint_text = shell(lg, "custom_request_field_route_hint")

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back")
        self.title.value = shell(lg, "custom_request_title")
        self.intro.value = shell(lg, "custom_request_intro")
        self.fields_legend.value = shell(lg, "custom_request_fields_legend")
        self.request_type.label = shell(lg, "custom_request_field_type")
        keys = ("custom_request_opt_group_trip", "custom_request_opt_custom_route", "custom_request_opt_other")
        vals = ("group_trip", "custom_route", "other")
        self.request_type.options = [ft.dropdown.Option(v, shell(lg, k)) for v, k in zip(vals, keys, strict=True)]
        self.start_date.label = shell(lg, "custom_request_field_start")
        self.end_date.label = shell(lg, "custom_request_field_end")
        self.route_notes.label = shell(lg, "custom_request_field_route")
        self.route_notes.hint_text = shell(lg, "custom_request_field_route_hint")
        self.group_size.label = shell(lg, "custom_request_field_group")
        self.special.label = shell(lg, "custom_request_field_special")
        if not self._submit_in_progress:
            self.submit_btn.text = shell(lg, "custom_request_submit")
        if self._last_prefill is not None:
            self.prefill_banner_label.value = shell(
                lg,
                "custom_request_prefill_banner",
                code=self._last_prefill.tour_code,
            )

    def build(self) -> ft.Control:
        return scrollable_page(
            ft.Row([self.nav_back], alignment=ft.MainAxisAlignment.START),
            self.title,
            self.intro,
            self.fields_legend,
            self.prefill_banner,
            self.request_type,
            self.start_date,
            self.end_date,
            self.route_notes,
            self.group_size,
            self.special,
            ft.Row([self.submit_btn], alignment=ft.MainAxisAlignment.START),
        )

    def _request_type_label(self) -> str:
        lg = self.language_code
        rt = self.request_type.value or "group_trip"
        key = {
            "group_trip": "custom_request_opt_group_trip",
            "custom_route": "custom_request_opt_custom_route",
            "other": "custom_request_opt_other",
        }.get(rt, "custom_request_opt_group_trip")
        return shell(lg, key)

    def _release_submit_button(self) -> None:
        lg = self.language_code
        self._submit_in_progress = False
        self.submit_btn.disabled = False
        self.submit_btn.text = shell(lg, "custom_request_submit")

    async def _submit_async(self) -> None:
        if self._submit_in_progress:
            return
        lg = self.language_code
        route_snapshot = (self.route_notes.value or "").strip()
        excerpt = route_snapshot[:280] + ("…" if len(route_snapshot) > 280 else "")
        end_raw = (self.end_date.value or "").strip()
        start_raw = (self.start_date.value or "").strip()
        gs_raw = (self.group_size.value or "").strip()
        local_key = validate_custom_request_form_local(
            travel_date_start=start_raw,
            travel_date_end=end_raw,
            route_notes=self.route_notes.value or "",
            group_size_raw=self.group_size.value or "",
        )
        if local_key is not None:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(shell(lg, local_key)), action="OK")
            self.page.snack_bar.open = True
            self.page.update()
            return
        self._submit_in_progress = True
        self.submit_btn.disabled = True
        self.submit_btn.text = shell(lg, "custom_request_submit_sending")
        self.page.update()
        type_label = self._request_type_label()
        submitted_ok = False
        try:
            route = route_snapshot
            body: dict[str, object] = {
                "telegram_user_id": self._dev_telegram_user_id,
                "request_type": self.request_type.value or "group_trip",
                "travel_date_start": start_raw,
                "route_notes": route,
            }
            if end_raw:
                body["travel_date_end"] = end_raw
            if gs_raw:
                body["group_size"] = int(gs_raw)
            sp = (self.special.value or "").strip()
            if sp:
                body["special_conditions"] = sp
            r = await self.api_client.post_custom_request(body=body)
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 422:
                msg = message_for_custom_request_422(exc, lg)
            else:
                msg = CatalogScreen._http_error_message(exc, default=shell(lg, "custom_request_error"))
            self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), action="OK")
            self.page.snack_bar.open = True
        except Exception:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(shell(lg, "custom_request_error")),
                action="OK",
            )
            self.page.snack_bar.open = True
        else:
            submitted_ok = True
            self._reset_form_to_defaults()
            self._show_success_dialog(r.id, request_type_label=type_label, route_excerpt=excerpt or "—")
        finally:
            if not submitted_ok:
                self._release_submit_button()
            self.page.update()

    def _dismiss_dialog(self) -> None:
        self.page.dialog = None
        self._release_submit_button()
        self.page.update()

    def _show_success_dialog(self, request_id: int, *, request_type_label: str, route_excerpt: str) -> None:
        lg = self.language_code
        actions: list[ft.Control] = []
        if self.on_open_my_requests is not None:
            actions.append(
                ft.FilledButton(
                    shell(lg, "custom_request_success_cta_my_requests"),
                    on_click=self._on_success_my_requests,
                )
            )
        actions.append(
            ft.OutlinedButton(
                shell(lg, "custom_request_success_back_catalog"),
                on_click=self._on_success_back_catalog,
            )
        )
        actions.append(
            ft.TextButton(
                shell(lg, "custom_request_success_new_request"),
                on_click=self._on_success_new_request,
            )
        )
        if self.on_continue_rfq_booking is not None:
            actions.append(
                ft.OutlinedButton(
                    shell(lg, "rfq_bridge_cta_from_success"),
                    on_click=lambda e: self._on_success_continue_bridge(request_id, e),
                )
            )
        content = ft.Column(
            [
                ft.Text(shell(lg, "custom_request_success_lead")),
                ft.Text(
                    shell(lg, "custom_request_success_reference", id=str(request_id)),
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(shell(lg, "custom_request_success_summary_type", label=request_type_label), size=13),
                ft.Text(
                    shell(lg, "custom_request_success_summary_route", text=route_excerpt),
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Text(shell(lg, "custom_request_success_next"), size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            tight=True,
            spacing=8,
        )
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(shell(lg, "custom_request_success_title")),
            content=content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _on_success_back_catalog(self, _: ft.ControlEvent) -> None:
        self._dismiss_dialog()
        self.on_close()

    def _on_success_new_request(self, _: ft.ControlEvent) -> None:
        self._dismiss_dialog()

    def _on_success_my_requests(self, _: ft.ControlEvent) -> None:
        self._dismiss_dialog()
        if self.on_open_my_requests is not None:
            self.on_open_my_requests()

    def _on_success_continue_bridge(self, request_id: int, _: ft.ControlEvent) -> None:
        self._dismiss_dialog()
        if self.on_continue_rfq_booking is not None:
            self.on_continue_rfq_booking(request_id)


class SupplierOfferLandingScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        language_code: str,
        on_back_catalog: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_open_execution_tour: Callable[[str], None],
        on_open_custom_request: Callable[[], None] | None = None,
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.on_back_catalog = on_back_catalog
        self.on_open_settings = on_open_settings
        self.on_open_execution_tour = on_open_execution_tour
        self.on_open_custom_request = on_open_custom_request
        self.current_offer_id: int | None = None
        self._last_detail: MiniAppSupplierOfferLandingRead | None = None
        lg = language_code
        self.nav_back = ft.TextButton(
            shell(lg, "back_to_catalog"),
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda _: self.on_back_catalog(),
        )
        self.nav_settings = ft.TextButton(shell(lg, "settings"), on_click=lambda _: self.on_open_settings())
        self.nav_custom_trip: ft.TextButton | None = None
        if on_open_custom_request is not None:
            self.nav_custom_trip = ft.TextButton(shell(lg, "nav_custom_trip"), on_click=lambda _: on_open_custom_request())
        self.page_title = ft.Text(shell(lg, "supplier_offer_landing_title"), size=26, weight=ft.FontWeight.BOLD)
        self.subtitle = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.body_column = ft.Column(spacing=10)
        self.actionability_badge = ft.Container(
            visible=False,
            padding=8,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
            content=ft.Text("", size=13, weight=ft.FontWeight.W_600),
        )
        self.catalog_cta = ft.FilledButton(
            shell(lg, "supplier_offer_btn_browse_catalog"),
            on_click=lambda _: self.on_back_catalog(),
        )
        self.bookable_placeholder_cta = ft.OutlinedButton(
            shell(lg, "supplier_offer_actionability_cta_bookable_placeholder"),
            on_click=lambda _: self._open_execution_target(),
            visible=False,
        )
        self.fallback_hint = ft.Text(
            shell(lg, "supplier_offer_fallback_hint"),
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

    def set_offer_id(self, supplier_offer_id: int) -> None:
        self.current_offer_id = supplier_offer_id

    def _open_execution_target(self) -> None:
        detail = self._last_detail
        if detail is None:
            self.on_back_catalog()
            return
        target = (detail.execution_target_tour_code or "").strip()
        if not target:
            self.on_back_catalog()
            return
        self.on_open_execution_tour(target)

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back_to_catalog")
        self.nav_settings.text = shell(lg, "settings")
        if self.nav_custom_trip is not None:
            self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.page_title.value = shell(lg, "supplier_offer_landing_title")
        self.catalog_cta.text = shell(lg, "supplier_offer_btn_browse_catalog")
        self.bookable_placeholder_cta.text = shell(lg, "supplier_offer_actionability_cta_bookable_placeholder")
        self.fallback_hint.value = shell(lg, "supplier_offer_fallback_hint")
        detail = self._last_detail
        if detail is not None:
            self.subtitle.value = shell(lg, "supplier_offer_opened_ref", id=str(detail.supplier_offer_id))

    def build(self) -> ft.Control:
        nav_row: list[ft.Control] = [self.nav_back, self.nav_settings]
        if self.nav_custom_trip is not None:
            nav_row.append(self.nav_custom_trip)
        return scrollable_page(
            ft.Row(nav_row, alignment=ft.MainAxisAlignment.START, wrap=True),
            self.page_title,
            self.subtitle,
            self.body_column,
            ft.Container(height=8),
            self.actionability_badge,
            self.bookable_placeholder_cta,
            self.catalog_cta,
            self.fallback_hint,
        )

    async def load_offer(self) -> None:
        self.sync_shell_labels()
        lg = self.language_code
        offer_id = self.current_offer_id
        if offer_id is None:
            self.body_column.controls = [ft.Text("Offer id is missing.", color=ft.Colors.ERROR)]
            self.page.update()
            return
        self.body_column.controls = [
            ft.Row(
                [ft.ProgressRing(width=20, height=20, stroke_width=2), ft.Text(shell(lg, "supplier_offer_landing_loading"))],
                spacing=10,
            )
        ]
        self.page.update()
        try:
            detail = await self.api_client.get_supplier_offer_landing(supplier_offer_id=offer_id)
        except httpx.HTTPStatusError as exc:
            self._last_detail = None
            self.subtitle.value = shell(lg, "supplier_offer_opened_ref", id=str(offer_id))
            self.body_column.controls = [
                ft.Text(
                    CatalogScreen._http_error_message(exc, default="Could not load this supplier offer."),
                    color=ft.Colors.ERROR,
                )
            ]
            self.page.update()
            return
        except Exception:
            self._last_detail = None
            self.subtitle.value = shell(lg, "supplier_offer_opened_ref", id=str(offer_id))
            self.body_column.controls = [ft.Text("Could not load this supplier offer.", color=ft.Colors.ERROR)]
            self.page.update()
            return

        self._last_detail = detail
        self.subtitle.value = shell(lg, "supplier_offer_opened_ref", id=str(detail.supplier_offer_id))
        status = getattr(detail.publication.lifecycle_status, "value", detail.publication.lifecycle_status)
        schedule_line = (
            f"{CatalogScreen._format_datetime(detail.departure_datetime)} → "
            f"{CatalogScreen._format_datetime(detail.return_datetime)}"
        )
        if detail.base_price is not None and (detail.currency or "").strip():
            price_line = f"{detail.base_price} {detail.currency}"
        else:
            price_line = shell(lg, "supplier_offer_price_missing")
        state = detail.actionability_state
        state_value = getattr(state, "value", state)
        if state_value == MiniAppSupplierOfferActionabilityState.BOOKABLE.value:
            state_label = shell(lg, "supplier_offer_actionability_bookable")
            if detail.execution_activation_available and (detail.execution_target_tour_code or "").strip():
                hint_line = shell(lg, "supplier_offer_actionability_hint_bookable_ready")
                self.bookable_placeholder_cta.visible = True
            else:
                hint_line = shell(lg, "supplier_offer_actionability_hint_bookable")
                self.bookable_placeholder_cta.visible = False
            self.actionability_badge.bgcolor = ft.Colors.GREEN_50
        elif state_value == MiniAppSupplierOfferActionabilityState.SOLD_OUT.value:
            state_label = shell(lg, "supplier_offer_actionability_sold_out")
            hint_line = shell(lg, "supplier_offer_actionability_hint_sold_out")
            self.actionability_badge.bgcolor = ft.Colors.RED_50
            self.bookable_placeholder_cta.visible = False
        elif state_value == MiniAppSupplierOfferActionabilityState.ASSISTED_ONLY.value:
            state_label = shell(lg, "supplier_offer_actionability_assisted_only")
            hint_line = shell(lg, "supplier_offer_actionability_hint_assisted_only")
            self.actionability_badge.bgcolor = ft.Colors.AMBER_50
            self.bookable_placeholder_cta.visible = False
        else:
            state_label = shell(lg, "supplier_offer_actionability_view_only")
            hint_line = shell(lg, "supplier_offer_actionability_hint_view_only")
            self.actionability_badge.bgcolor = ft.Colors.BLUE_50
            self.bookable_placeholder_cta.visible = False
        if isinstance(self.actionability_badge.content, ft.Text):
            self.actionability_badge.content.value = state_label
        self.actionability_badge.visible = True
        blocks: list[ft.Control] = [
            ft.Text(detail.title, size=22, weight=ft.FontWeight.BOLD),
            ft.Text(shell(lg, "supplier_offer_publication_line", status=str(status)), size=12),
            ft.Container(height=4),
            ft.Text(shell(lg, "supplier_offer_actionability_title"), size=16, weight=ft.FontWeight.W_600),
            ft.Text(hint_line, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=6),
            ft.Text(shell(lg, "supplier_offer_schedule_title"), size=16, weight=ft.FontWeight.W_600),
            ft.Text(schedule_line),
            ft.Container(height=4),
            ft.Text(shell(lg, "supplier_offer_price_title"), size=16, weight=ft.FontWeight.W_600),
            ft.Text(price_line),
            ft.Container(height=4),
            ft.Text(shell(lg, "supplier_offer_section_capacity"), size=16, weight=ft.FontWeight.W_600),
            ft.Text(str(detail.seats_total)),
            ft.Container(height=4),
            ft.Text(shell(lg, "supplier_offer_section_description"), size=16, weight=ft.FontWeight.W_600),
            ft.Text(detail.description),
        ]
        if (detail.boarding_places_text or "").strip():
            blocks.extend(
                [
                    ft.Container(height=4),
                    ft.Text(shell(lg, "supplier_offer_section_boarding"), size=16, weight=ft.FontWeight.W_600),
                    ft.Text(detail.boarding_places_text),
                ]
            )
        transport = (detail.vehicle_label or "").strip() or (detail.transport_notes or "").strip()
        if transport:
            blocks.extend(
                [
                    ft.Container(height=4),
                    ft.Text(shell(lg, "supplier_offer_section_transport"), size=16, weight=ft.FontWeight.W_600),
                    ft.Text(transport),
                ]
            )
        self.body_column.controls = blocks
        self.page.update()


class HelpScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        on_close: Callable[[], None],
        on_open_custom_request: Callable[[], None] | None = None,
        language_code: str,
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.on_close = on_close
        self.on_open_custom_request = on_open_custom_request
        self.language_code = language_code
        self.body_column = ft.Column(spacing=12)
        lg = language_code
        self.nav_back = ft.TextButton(shell(lg, "back"), icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.on_close())
        self.nav_custom_trip: ft.TextButton | None = None
        if on_open_custom_request is not None:
            self.nav_custom_trip = ft.TextButton(
                shell(lg, "nav_custom_trip"),
                on_click=lambda _: on_open_custom_request(),
            )
        self.page_title = ft.Text(shell(lg, "help_title"), size=26, weight=ft.FontWeight.BOLD)
        self.intro_text = ft.Text(
            shell(lg, "help_return_note"),
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back")
        if self.nav_custom_trip is not None:
            self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.page_title.value = shell(lg, "help_title")
        self.intro_text.value = shell(lg, "help_return_note")

    def build(self) -> ft.Control:
        nav_row: list[ft.Control] = [self.nav_back]
        if self.nav_custom_trip is not None:
            nav_row.append(self.nav_custom_trip)
        return scrollable_page(
            ft.Row(nav_row, alignment=ft.MainAxisAlignment.START, wrap=True),
            self.page_title,
            self.intro_text,
            self.body_column,
        )

    async def load_content(self) -> None:
        self.sync_shell_labels()
        lg = self.language_code
        self.body_column.controls = [
            ft.Row(
                [ft.ProgressRing(width=20, height=20, stroke_width=2), ft.Text(shell(lg, "loading_help"))],
                spacing=10,
            )
        ]
        self.page.update()
        try:
            h = await self.api_client.get_help(language_code=self.language_code)
        except httpx.HTTPStatusError as exc:
            self.body_column.controls = [
                ft.Text(
                    CatalogScreen._http_error_message(exc, default="Unable to load help right now."),
                    color=ft.Colors.ERROR,
                )
            ]
        except Exception:
            self.body_column.controls = [ft.Text("Unable to load help right now.", color=ft.Colors.ERROR)]
        else:
            blocks: list[ft.Control] = [
                ft.Text(h.intro, color=ft.Colors.ON_SURFACE_VARIANT),
            ]
            for cat in h.categories:
                blocks.append(ft.Text(cat.title, size=18, weight=ft.FontWeight.W_600))
                for bullet in cat.bullets:
                    blocks.append(ft.Text(f"• {bullet}", size=14))
                blocks.append(ft.Container(height=8))
            blocks.append(
                ft.Container(
                    bgcolor=ft.Colors.AMBER_50,
                    border_radius=12,
                    padding=12,
                    content=ft.Text(h.operator_notice, color=ft.Colors.AMBER_900, size=14),
                )
            )
            blocks.append(ft.Text(h.when_to_contact_support, color=ft.Colors.ON_SURFACE_VARIANT, size=14))
            if self.on_open_custom_request is not None:
                blocks.append(ft.Container(height=8))
                blocks.append(
                    ft.Text(
                        shell(lg, "custom_request_from_help_hint"),
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    )
                )
                blocks.append(
                    ft.FilledButton(
                        shell(lg, "btn_custom_request"),
                        on_click=lambda _: self.on_open_custom_request(),
                    )
                )
            self.body_column.controls = blocks
        self.page.update()


class SettingsScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        telegram_user_id: int | None,
        on_language_applied: Callable[[str], None],
        on_close: Callable[[], None],
        language_code: str,
        on_open_custom_request: Callable[[], None] | None = None,
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.telegram_user_id = telegram_user_id
        self.on_language_applied = on_language_applied
        self.on_close = on_close
        self.language_code = language_code
        lg = language_code
        self.nav_back = ft.TextButton(shell(lg, "back"), icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.on_close())
        self.nav_custom_trip: ft.TextButton | None = None
        if on_open_custom_request is not None:
            self.nav_custom_trip = ft.TextButton(
                shell(lg, "nav_custom_trip"),
                on_click=lambda _: on_open_custom_request(),
            )
        self.page_title = ft.Text(shell(lg, "settings_title"), size=26, weight=ft.FontWeight.BOLD)
        self.intro_text = ft.Text(shell(lg, "settings_intro"), color=ft.Colors.ON_SURFACE_VARIANT)
        self.language_dropdown = ft.Dropdown(
            label=shell(language_code, "label_display_language"), dense=True, width=320, options=[]
        )
        self.hint_text = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.save_button = ft.FilledButton(
            shell(language_code, "btn_save"), on_click=lambda _: self.page.run_task(self._save_language)
        )

    def build(self) -> ft.Control:
        nav_row: list[ft.Control] = [self.nav_back]
        if self.nav_custom_trip is not None:
            nav_row.append(self.nav_custom_trip)
        return scrollable_page(
            ft.Row(nav_row, alignment=ft.MainAxisAlignment.START, wrap=True),
            self.page_title,
            self.intro_text,
            self.language_dropdown,
            self.hint_text,
            self.error_text,
            ft.Row([self.save_button], alignment=ft.MainAxisAlignment.START),
        )

    def sync_shell_labels(self) -> None:
        lg = self.language_code
        self.nav_back.text = shell(lg, "back")
        if self.nav_custom_trip is not None:
            self.nav_custom_trip.text = shell(lg, "nav_custom_trip")
        self.page_title.value = shell(lg, "settings_title")
        self.intro_text.value = shell(lg, "settings_intro")
        self.language_dropdown.label = shell(lg, "label_display_language")
        self.save_button.text = shell(lg, "btn_save")

    async def load_options(self) -> None:
        self.error_text.visible = False
        self.page.update()
        try:
            snap = await self.api_client.get_mini_app_settings(telegram_user_id=self.telegram_user_id)
        except httpx.HTTPStatusError as exc:
            self.hint_text.value = CatalogScreen._http_error_message(exc, default="Unable to load settings.")
            self.language_dropdown.options = []
        except Exception:
            self.hint_text.value = "Unable to load settings."
            self.language_dropdown.options = []
        else:
            self.language_dropdown.options = [ft.dropdown.Option(code) for code in snap.supported_languages]
            self.language_dropdown.value = snap.resolved_language
            active = snap.active_language or "not set yet"
            self.hint_text.value = (
                f"Server default: {snap.mini_app_default_language}. "
                f"Your saved preference: {active}. "
                f"Fallback still applies when a tour has no translation."
            )
        self.page.update()

    async def _save_language(self) -> None:
        code = self.language_dropdown.value
        if not code:
            self.error_text.value = "Pick a language first."
            self.error_text.visible = True
            self.page.update()
            return
        self.save_button.disabled = True
        self.error_text.visible = False
        self.page.update()
        if self.telegram_user_id is None:
            self.error_text.value = shell(self.language_code, "identity_required_my_data")
            self.error_text.visible = True
            self.save_button.disabled = False
            self.page.update()
            return
        try:
            applied = await self.api_client.post_language_preference(
                telegram_user_id=self.telegram_user_id,
                language_code=str(code),
            )
        except httpx.HTTPStatusError as exc:
            self.error_text.value = CatalogScreen._http_error_message(exc, default="Could not save language.")
            self.error_text.visible = True
        except Exception:
            self.error_text.value = "Could not save language."
            self.error_text.visible = True
        else:
            self.on_language_applied(applied)
            self.on_close()
        finally:
            self.save_button.disabled = False
            self.page.update()


class MiniAppShell:
    TOUR_ROUTE_PREFIX = "/tours/"
    TOUR_PREPARATION_ROUTE_SUFFIX = "/prepare"
    SUPPLIER_OFFER_ROUTE_PREFIX = "/supplier-offers/"

    def __init__(self, page: ft.Page) -> None:
        settings = get_mini_app_settings()
        self.page = page
        self.api_client = MiniAppApiClient(settings.normalized_api_base_url)
        self._dev_telegram_user_id = settings.mini_app_dev_telegram_user_id
        self._allow_dev_identity_fallback = settings.mini_app_allow_dev_identity_fallback
        self._identity_trace_enabled = settings.mini_app_debug_trace or settings.mini_app_identity_trace_enabled
        self._resolved_telegram_user_id = self.resolve_runtime_telegram_user_id(
            app_env=settings.app_env,
            route=page.route,
            page_url=getattr(page, "url", None),
            page_query=getattr(page, "query", None),
            dev_telegram_user_id=settings.mini_app_dev_telegram_user_id,
            allow_dev_fallback=self._allow_dev_identity_fallback,
        )
        self._trace_identity_probe(context="startup", app_env=settings.app_env)
        self._modal_return_route: str = "/"
        self.catalog_screen = CatalogScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            on_open_detail=self.open_tour_detail,
            on_my_bookings=self.open_bookings,
            on_my_requests=self.open_my_requests,
            on_open_settings=self.open_settings,
            on_help=self.open_help,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.my_bookings_screen = MyBookingsScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            telegram_user_id=self._resolved_telegram_user_id,
            on_back_catalog=self.open_catalog,
            on_open_booking=self.open_booking_detail,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.my_requests_list_screen = MyRequestsListScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            telegram_user_id=self._resolved_telegram_user_id,
            on_back_catalog=self.open_catalog,
            on_open_detail=self.open_my_request_detail,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.my_request_detail_screen = MyRequestDetailScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            telegram_user_id=self._resolved_telegram_user_id,
            on_back_list=self.open_my_requests,
            on_open_bridge=self.open_rfq_bridge_booking,
            on_continue_payment=self.open_payment_entry,
            on_open_booking=self.open_booking_detail,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.booking_detail_screen = BookingDetailScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            telegram_user_id=self._resolved_telegram_user_id,
            on_back_to_bookings=self.open_bookings,
            on_browse_tours=self.open_catalog,
            on_pay_now=self.open_payment_entry,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.tour_detail_screen = TourDetailScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back=self.open_catalog,
            on_prepare=self.open_tour_preparation,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_tour_detail,
        )
        self.reservation_preparation_screen = ReservationPreparationScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back=self.open_tour_detail,
            on_reserved=self.open_reservation_success,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.reservation_success_screen = ReservationSuccessScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back=self.open_tour_preparation,
            on_continue_to_payment=self.open_payment_entry,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.payment_entry_screen = PaymentEntryScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back=self.open_reservation_success_from_payment,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_bookings=self.open_bookings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self._custom_request_return_route: str = "/"
        self._pending_custom_request_prefill: CustomRequestPrefill | None = None
        self.help_screen = HelpScreen(
            page,
            api_client=self.api_client,
            on_close=self.close_modal,
            on_open_custom_request=self.open_custom_request_from_help,
            language_code=settings.mini_app_default_language,
        )
        self.supplier_offer_landing_screen = SupplierOfferLandingScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            on_back_catalog=self.open_catalog,
            on_open_settings=self.open_settings,
            on_open_execution_tour=self.open_tour_detail,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.rfq_bridge_execution_screen = RfqBridgeExecutionScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back=self.open_catalog,
            on_continue_to_payment=self.open_payment_entry,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self.custom_request_screen = CustomRequestScreen(
            page,
            api_client=self.api_client,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_close=self.close_custom_request,
            language_code=settings.mini_app_default_language,
            on_continue_rfq_booking=self.open_rfq_bridge_booking,
            on_open_my_requests=self.open_my_requests,
        )
        self.settings_screen = SettingsScreen(
            page,
            api_client=self.api_client,
            telegram_user_id=self._resolved_telegram_user_id,
            on_language_applied=self.apply_language,
            on_close=self.close_modal,
            language_code=settings.mini_app_default_language,
            on_open_custom_request=self.open_custom_request_from_current_route,
        )
        self._apply_resolved_identity_to_user_scoped_screens()

    def apply_language(self, code: str) -> None:
        self.catalog_screen.language_code = code
        self.tour_detail_screen.language_code = code
        self.reservation_preparation_screen.language_code = code
        self.reservation_success_screen.language_code = code
        self.my_bookings_screen.language_code = code
        self.my_requests_list_screen.language_code = code
        self.my_request_detail_screen.language_code = code
        self.booking_detail_screen.language_code = code
        self.payment_entry_screen.language_code = code
        self.help_screen.language_code = code
        self.custom_request_screen.language_code = code
        self.rfq_bridge_execution_screen.language_code = code
        self.settings_screen.language_code = code
        self.supplier_offer_landing_screen.language_code = code
        self.catalog_screen.sync_shell_labels()
        self.settings_screen.sync_shell_labels()
        self.tour_detail_screen.sync_shell_labels()
        self.reservation_preparation_screen.sync_shell_labels()
        self.reservation_success_screen.sync_shell_labels()
        self.payment_entry_screen.sync_shell_labels()
        self.my_bookings_screen.sync_shell_labels()
        self.my_requests_list_screen.sync_shell_labels()
        self.my_request_detail_screen.sync_shell_labels()
        self.booking_detail_screen.sync_shell_labels()
        self.help_screen.sync_shell_labels()
        self.custom_request_screen.sync_shell_labels()
        self.rfq_bridge_execution_screen.sync_shell_labels()
        self.supplier_offer_landing_screen.sync_shell_labels()

    async def hydrate_language_from_server(self) -> None:
        try:
            snap = await self.api_client.get_mini_app_settings(telegram_user_id=self._resolved_telegram_user_id)
        except Exception:
            return
        self.apply_language(snap.resolved_language)
        route = (self.page.route or "/").strip() or "/"
        if route in ("/", ""):
            await self.catalog_screen.load_catalog()

    def open_help(self) -> None:
        self._modal_return_route = self.page.route or "/"
        self.page.go("/help")

    def open_settings(self) -> None:
        self._modal_return_route = self.page.route or "/"
        self.page.go("/settings")

    def open_custom_request_from_help(self) -> None:
        self._pending_custom_request_prefill = None
        self._custom_request_return_route = self.page.route or "/help"
        self.page.go("/custom-request")

    def open_custom_request_from_tour_detail(self) -> None:
        code = self.tour_detail_screen.current_tour_code
        self._custom_request_return_route = (
            f"{self.TOUR_ROUTE_PREFIX}{code}" if code else "/"
        )
        self._pending_custom_request_prefill = self._build_prefill_for_tour_detail_entry()
        self.page.go("/custom-request")

    def open_custom_request_from_current_route(self) -> None:
        self._custom_request_return_route = (self.page.route or "/").strip() or "/"
        self._pending_custom_request_prefill = self._build_prefill_for_current_route()
        self.page.go("/custom-request")

    def _build_prefill_for_tour_detail_entry(self) -> CustomRequestPrefill | None:
        code = self.tour_detail_screen.current_tour_code
        detail = self.tour_detail_screen._last_detail
        if not code or detail is None or detail.tour.code != code:
            return None
        return prefill_from_tour_detail(detail)

    def _tour_code_from_customer_route(self, route: str) -> str | None:
        r = (route or "").strip()
        if not r.startswith(self.TOUR_ROUTE_PREFIX):
            return None
        tail = r.removeprefix(self.TOUR_ROUTE_PREFIX).strip("/")
        if not tail:
            return None
        if tail.endswith(self.TOUR_PREPARATION_ROUTE_SUFFIX):
            tail = tail[: -len(self.TOUR_PREPARATION_ROUTE_SUFFIX)].strip("/")
        return tail or None

    def _build_prefill_for_current_route(self) -> CustomRequestPrefill | None:
        route = (self.page.route or "").strip() or "/"
        code = self._tour_code_from_customer_route(route)
        if code is None:
            return None
        on_prepare = route.rstrip("/").endswith(self.TOUR_PREPARATION_ROUTE_SUFFIX)
        if on_prepare:
            prep = self.reservation_preparation_screen._last_preparation
            if prep is not None and prep.tour.code == code:
                return prefill_from_reservation_preparation(prep)
            return None
        detail = self.tour_detail_screen._last_detail
        if detail is not None and detail.tour.code == code:
            return prefill_from_tour_detail(detail)
        return None

    def _take_custom_request_prefill(self) -> CustomRequestPrefill | None:
        p = self._pending_custom_request_prefill
        self._pending_custom_request_prefill = None
        return p

    def close_custom_request(self) -> None:
        self.page.go(self._custom_request_return_route or "/")

    def open_rfq_bridge_booking(self, request_id: int) -> None:
        self.page.go(f"/custom-requests/{request_id}/bridge")

    def open_my_requests(self) -> None:
        self.page.go("/my-requests")

    def open_my_request_detail(self, request_id: int) -> None:
        self.page.go(f"/my-requests/{request_id}")

    def close_modal(self) -> None:
        target = self._modal_return_route or "/"
        self.page.go(target)

    def handle_route_change(self, _: ft.RouteChangeEvent) -> None:
        self._refresh_runtime_identity_from_current_context()
        self.page.views.clear()
        self.page.views.append(ft.View(route="/", controls=[self.catalog_screen.build()], padding=0, spacing=0))

        if self._is_help_route(self.page.route):
            self.page.views.append(ft.View(route="/help", controls=[self.help_screen.build()], padding=0, spacing=0))
            self.page.update()
            self.page.run_task(self.help_screen.load_content)
            return

        if self._is_custom_request_route(self.page.route):
            if not self._custom_request_return_route:
                self._custom_request_return_route = "/"
            prefill = self._take_custom_request_prefill()
            self.custom_request_screen.apply_prefill(prefill)
            self.page.views.append(
                ft.View(
                    route="/custom-request",
                    controls=[self.custom_request_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()
            return

        bridge_request_id = MiniAppShell._extract_custom_request_bridge_request_id(self.page.route)
        if bridge_request_id is not None:
            self.rfq_bridge_execution_screen.set_request_id(bridge_request_id)
            self.page.views.append(
                ft.View(
                    route=(self.page.route or "/").strip() or "/",
                    controls=[self.rfq_bridge_execution_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()
            self.page.run_task(self.rfq_bridge_execution_screen.load_initial)
            return

        my_request_detail_id = MiniAppShell._extract_my_request_detail_id(self.page.route)
        if my_request_detail_id is not None:
            self.my_request_detail_screen.set_request_id(my_request_detail_id)
            self.page.views.append(
                ft.View(
                    route="/my-requests",
                    controls=[self.my_requests_list_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=(self.page.route or "/").strip() or "/",
                    controls=[self.my_request_detail_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()

            async def _load_my_request_stack() -> None:
                await self.my_requests_list_screen.load_list()
                await self.my_request_detail_screen.load_detail()

            self.page.run_task(_load_my_request_stack)
            return

        if self._is_my_requests_list_route(self.page.route):
            self.page.views.append(
                ft.View(
                    route="/my-requests",
                    controls=[self.my_requests_list_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()
            self.page.run_task(self.my_requests_list_screen.load_list)
            return

        if self._is_settings_route(self.page.route):
            self.page.views.append(
                ft.View(route="/settings", controls=[self.settings_screen.build()], padding=0, spacing=0)
            )
            self.page.update()
            self.page.run_task(self.settings_screen.load_options)
            return

        supplier_offer_id = self._extract_supplier_offer_id(self.page.route)
        if supplier_offer_id is not None:
            self.supplier_offer_landing_screen.set_offer_id(supplier_offer_id)
            self.page.views.append(
                ft.View(
                    route=self.page.route or "/",
                    controls=[self.supplier_offer_landing_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()
            self.page.run_task(self.supplier_offer_landing_screen.load_offer)
            return

        payment_ctx = self._extract_payment_route(self.page.route)
        if payment_ctx is not None:
            tour_code, order_id = payment_ctx
            self.tour_detail_screen.set_tour_code(tour_code)
            self.reservation_preparation_screen.set_tour_code(tour_code)
            self.reservation_success_screen.set_context(tour_code=tour_code, order_id=order_id)
            self.payment_entry_screen.set_context(tour_code=tour_code, order_id=order_id)
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{tour_code}",
                    controls=[self.tour_detail_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{tour_code}{self.TOUR_PREPARATION_ROUTE_SUFFIX}",
                    controls=[self.reservation_preparation_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{tour_code}/prepare/reserved/{order_id}",
                    controls=[self.reservation_success_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=self.page.route or "/",
                    controls=[self.payment_entry_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()

            async def _load_payment_flow() -> None:
                await self.reservation_success_screen.load_overview()
                await self.payment_entry_screen.load_payment_entry()

            self.page.run_task(_load_payment_flow)
            return

        reserved_ctx = self._extract_reserved_route(self.page.route)
        if reserved_ctx is not None:
            tour_code, order_id = reserved_ctx
            self.tour_detail_screen.set_tour_code(tour_code)
            self.reservation_preparation_screen.set_tour_code(tour_code)
            self.reservation_success_screen.set_context(tour_code=tour_code, order_id=order_id)
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{tour_code}",
                    controls=[self.tour_detail_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{tour_code}{self.TOUR_PREPARATION_ROUTE_SUFFIX}",
                    controls=[self.reservation_preparation_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=self.page.route or "/",
                    controls=[self.reservation_success_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()
            self.page.run_task(self.reservation_success_screen.load_overview)
            return

        booking_order_id = self._extract_booking_detail_order_id(self.page.route)
        if booking_order_id is not None:
            self.booking_detail_screen.set_order_id(booking_order_id)
            self.page.views.append(
                ft.View(route="/bookings", controls=[self.my_bookings_screen.build()], padding=0, spacing=0)
            )
            self.page.views.append(
                ft.View(
                    route=self.page.route or "/",
                    controls=[self.booking_detail_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()

            async def _load_booking_stack() -> None:
                await self.my_bookings_screen.load_bookings()
                await self.booking_detail_screen.load_detail()

            self.page.run_task(_load_booking_stack)
            return

        if self._is_bookings_list_route(self.page.route):
            self.page.views.append(
                ft.View(route="/bookings", controls=[self.my_bookings_screen.build()], padding=0, spacing=0)
            )
            self.page.update()
            self.page.run_task(self.my_bookings_screen.load_bookings)
            return

        preparation_tour_code = self._extract_preparation_tour_code(self.page.route)
        if preparation_tour_code is not None:
            self.tour_detail_screen.set_tour_code(preparation_tour_code)
            self.reservation_preparation_screen.set_tour_code(preparation_tour_code)
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{preparation_tour_code}",
                    controls=[self.tour_detail_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.views.append(
                ft.View(
                    route=f"{self.TOUR_ROUTE_PREFIX}{preparation_tour_code}{self.TOUR_PREPARATION_ROUTE_SUFFIX}",
                    controls=[self.reservation_preparation_screen.build()],
                    padding=0,
                    spacing=0,
                )
            )
            self.page.update()
            self.page.run_task(self.reservation_preparation_screen.load_preparation)
            return

        tour_code = self._extract_tour_code(self.page.route)
        if tour_code is not None:
            self.tour_detail_screen.set_tour_code(tour_code)
            self.page.views.append(
                ft.View(route=f"{self.TOUR_ROUTE_PREFIX}{tour_code}", controls=[self.tour_detail_screen.build()], padding=0, spacing=0)
            )
            self.page.update()
            self.page.run_task(self.tour_detail_screen.load_tour_detail)
            return

        self.page.update()
        self.page.run_task(self.catalog_screen.load_catalog)

    def handle_view_pop(self, _: ft.ViewPopEvent) -> None:
        if len(self.page.views) <= 1:
            self.page.go("/")
            return
        self.page.views.pop()
        self.page.go(self.page.views[-1].route)

    def open_catalog(self) -> None:
        self.page.go("/")

    def open_bookings(self) -> None:
        self.page.go("/bookings")

    def open_booking_detail(self, order_id: int) -> None:
        self.page.go(f"/bookings/{order_id}")

    def open_tour_detail(self, tour_code: str) -> None:
        self.page.go(f"{self.TOUR_ROUTE_PREFIX}{tour_code}")

    def open_tour_preparation(self, tour_code: str) -> None:
        self.page.go(f"{self.TOUR_ROUTE_PREFIX}{tour_code}{self.TOUR_PREPARATION_ROUTE_SUFFIX}")

    def open_supplier_offer(self, supplier_offer_id: int) -> None:
        self.page.go(f"{self.SUPPLIER_OFFER_ROUTE_PREFIX}{supplier_offer_id}")

    def open_reservation_success(self, tour_code: str, order_id: int) -> None:
        self.page.go(f"{self.TOUR_ROUTE_PREFIX}{tour_code}/prepare/reserved/{order_id}")

    def open_payment_entry(self, tour_code: str, order_id: int) -> None:
        self.page.go(f"{self.TOUR_ROUTE_PREFIX}{tour_code}/prepare/payment/{order_id}")

    def open_reservation_success_from_payment(self, tour_code: str) -> None:
        payment_ctx = self._extract_payment_route(self.page.route)
        if payment_ctx is not None:
            _, order_id = payment_ctx
            self.open_reservation_success(tour_code, order_id)
            return
        self.open_tour_preparation(tour_code)

    def _apply_resolved_identity_to_user_scoped_screens(self) -> None:
        tid = self._resolved_telegram_user_id
        self.my_bookings_screen.telegram_user_id = tid
        self.booking_detail_screen.telegram_user_id = tid
        self.my_requests_list_screen.telegram_user_id = tid
        self.my_request_detail_screen.telegram_user_id = tid
        self.settings_screen.telegram_user_id = tid

    def _trace_identity_probe(self, *, context: str, app_env: str) -> None:
        if not self._identity_trace_enabled:
            return
        route = self.page.route
        page_url = getattr(self.page, "url", None)
        page_query = getattr(self.page, "query", None)
        runtime_identity = self._extract_runtime_telegram_user_id(
            route=route,
            page_url=page_url,
            page_query=page_query,
        )
        fallback_used = (
            runtime_identity is None
            and self._resolved_telegram_user_id is not None
            and self._resolved_telegram_user_id == self._dev_telegram_user_id
        )
        winning_branch = "runtime" if runtime_identity is not None else ("dev_fallback" if fallback_used else "none")
        logger.info(
            "mini_app_identity context=%s app_env=%s route=%s has_identity=%s source=%s",
            context,
            (app_env or "").strip().lower(),
            route or "/",
            self._resolved_telegram_user_id is not None,
            winning_branch,
        )

    def _refresh_runtime_identity_from_current_context(self) -> None:
        if self._resolved_telegram_user_id is not None:
            return
        settings = get_mini_app_settings()
        refreshed = self.resolve_runtime_telegram_user_id(
            app_env=settings.app_env,
            route=self.page.route,
            page_url=getattr(self.page, "url", None),
            page_query=getattr(self.page, "query", None),
            dev_telegram_user_id=self._dev_telegram_user_id,
            allow_dev_fallback=self._allow_dev_identity_fallback,
        )
        if refreshed is not None:
            self._resolved_telegram_user_id = refreshed
            self._apply_resolved_identity_to_user_scoped_screens()
            self._trace_identity_probe(context="route_refresh_resolved", app_env=settings.app_env)
        elif self._identity_trace_enabled:
            self._trace_identity_probe(context="route_refresh_unresolved", app_env=settings.app_env)

    @staticmethod
    def _parse_telegram_user_id_from_query_string(value: str | None) -> int | None:
        if not value:
            return None
        try:
            parsed = parse_qs(value, keep_blank_values=False)
        except Exception:
            return None
        for key in ("telegram_user_id", "tg_user_id", "tguid", "user_id", "tg_bridge_user_id"):
            vals = parsed.get(key)
            if not vals:
                continue
            raw = (vals[-1] or "").strip()
            if not raw.isdigit():
                continue
            n = int(raw)
            if n > 0:
                return n
        return None

    @staticmethod
    def _query_object_to_dict(page_query: object | None) -> dict[str, str]:
        if page_query is None:
            return {}
        if isinstance(page_query, Mapping):
            out: dict[str, str] = {}
            for k, v in page_query.items():
                if k is None:
                    continue
                out[str(k)] = "" if v is None else str(v)
            return out
        # Flet QueryString object exposes `to_dict` property.
        raw = getattr(page_query, "to_dict", None)
        if isinstance(raw, Mapping):
            out: dict[str, str] = {}
            for k, v in raw.items():
                if k is None:
                    continue
                out[str(k)] = "" if v is None else str(v)
            return out
        if callable(raw):
            try:
                computed = raw()
            except Exception:
                computed = None
            if isinstance(computed, Mapping):
                out: dict[str, str] = {}
                for k, v in computed.items():
                    if k is None:
                        continue
                    out[str(k)] = "" if v is None else str(v)
                return out
        return {}

    @staticmethod
    def _extract_runtime_telegram_user_id(
        *,
        route: str | None,
        page_url: str | None,
        page_query: object | None,
    ) -> int | None:
        def _from_tg_init_data(init_data: str | None) -> int | None:
            if not init_data:
                return None
            try:
                parsed = parse_qs(init_data, keep_blank_values=False)
            except Exception:
                return None
            user_vals = parsed.get("user")
            if not user_vals:
                packed = (
                    parsed.get("tgWebAppData")
                    or parsed.get("tg_web_app_data")
                    or parsed.get("init_data")
                    or parsed.get("webapp_data")
                )
                if packed:
                    return _from_tg_init_data(unquote_plus((packed[-1] or "").strip()))
            if not user_vals:
                return None
            raw_user = (user_vals[-1] or "").strip()
            if not raw_user:
                return None
            try:
                payload = json.loads(unquote_plus(raw_user))
            except Exception:
                return None
            if not isinstance(payload, dict):
                return None
            raw_id = payload.get("id")
            try:
                n = int(raw_id)
            except Exception:
                return None
            return n if n > 0 else None

        if route and "?" in route:
            candidate = MiniAppShell._parse_telegram_user_id_from_query_string(route.split("?", 1)[1])
            if candidate is not None:
                return candidate
            candidate = _from_tg_init_data(route.split("?", 1)[1])
            if candidate is not None:
                return candidate
        split = None
        fragment_raw: str | None = None
        fragment_query: str | None = None
        if page_url:
            try:
                split = urlsplit(page_url)
                page_url_query = split.query
                candidate = MiniAppShell._parse_telegram_user_id_from_query_string(page_url_query)
            except Exception:
                candidate = None
            if candidate is not None:
                return candidate
            candidate = _from_tg_init_data(page_url_query)
            if candidate is not None:
                return candidate
            fragment_query = None
            try:
                fragment_raw = split.fragment
                if "?" in fragment_raw:
                    fragment_query = fragment_raw.split("?", 1)[1]
                elif "=" in fragment_raw:
                    fragment_query = fragment_raw
            except Exception:
                fragment_query = None
            candidate = MiniAppShell._parse_telegram_user_id_from_query_string(fragment_query)
            if candidate is not None:
                return candidate
            candidate = _from_tg_init_data(fragment_query)
            if candidate is not None:
                return candidate
        query_map = MiniAppShell._query_object_to_dict(page_query)
        if query_map:
            raw_init_data: str | None = None
            for key in ("telegram_user_id", "tg_user_id", "tguid", "user_id", "tg_bridge_user_id"):
                raw = query_map.get(key)
                if raw is None:
                    continue
                txt = str(raw).strip()
                if txt.isdigit():
                    n = int(txt)
                    if n > 0:
                        return n
            for key in ("tgWebAppData", "tg_web_app_data", "init_data", "webapp_data"):
                raw = query_map.get(key)
                if raw is None:
                    continue
                raw_init_data = str(raw)
                break
            candidate = _from_tg_init_data(raw_init_data)
            if candidate is not None:
                return candidate
        return None

    @staticmethod
    def resolve_runtime_telegram_user_id(
        *,
        app_env: str,
        route: str | None,
        page_url: str | None,
        page_query: object | None,
        dev_telegram_user_id: int,
        allow_dev_fallback: bool,
    ) -> int | None:
        runtime_id = MiniAppShell._extract_runtime_telegram_user_id(
            route=route,
            page_url=page_url,
            page_query=page_query,
        )
        if runtime_id is not None:
            return runtime_id
        env = (app_env or "").strip().lower()
        if allow_dev_fallback and env in {"local", "test"} and dev_telegram_user_id > 0:
            return dev_telegram_user_id
        return None

    @staticmethod
    def _extract_booking_detail_order_id(route: str | None) -> int | None:
        if not route:
            return None
        m = re.match(r"^/bookings/(\d+)$", route.strip())
        if not m:
            return None
        return int(m.group(1))

    @staticmethod
    def _is_bookings_list_route(route: str | None) -> bool:
        if not route:
            return False
        normalized = route.strip()
        return normalized == "/bookings" or normalized == "/bookings/"

    @staticmethod
    def _is_help_route(route: str | None) -> bool:
        if not route:
            return False
        normalized = route.strip()
        return normalized == "/help" or normalized == "/help/"

    @staticmethod
    def _is_custom_request_route(route: str | None) -> bool:
        if not route:
            return False
        normalized = route.strip()
        return normalized == "/custom-request" or normalized == "/custom-request/"

    @staticmethod
    def _extract_custom_request_bridge_request_id(route: str | None) -> int | None:
        if not route:
            return None
        m = re.match(r"^/custom-requests/(\d+)/bridge/?$", route.strip())
        if not m:
            return None
        return int(m.group(1))

    @staticmethod
    def _is_my_requests_list_route(route: str | None) -> bool:
        if not route:
            return False
        normalized = route.strip()
        return normalized == "/my-requests" or normalized == "/my-requests/"

    @staticmethod
    def _extract_my_request_detail_id(route: str | None) -> int | None:
        if not route:
            return None
        m = re.match(r"^/my-requests/(\d+)/?$", route.strip())
        if not m:
            return None
        return int(m.group(1))

    @staticmethod
    def _is_settings_route(route: str | None) -> bool:
        if not route:
            return False
        normalized = route.strip()
        return normalized == "/settings" or normalized == "/settings/"

    @staticmethod
    def _extract_payment_route(route: str | None) -> tuple[str, int] | None:
        if not route:
            return None
        m = re.match(r"^/tours/([^/]+)/prepare/payment/(\d+)$", route)
        if not m:
            return None
        return m.group(1), int(m.group(2))

    @staticmethod
    def _extract_reserved_route(route: str | None) -> tuple[str, int] | None:
        if not route:
            return None
        m = re.match(r"^/tours/([^/]+)/prepare/reserved/(\d+)$", route)
        if not m:
            return None
        return m.group(1), int(m.group(2))

    def _extract_tour_code(self, route: str | None) -> str | None:
        if route is None or not route.startswith(self.TOUR_ROUTE_PREFIX):
            return None
        if "/prepare/payment/" in route or "/prepare/reserved/" in route:
            return None
        if route.endswith(self.TOUR_PREPARATION_ROUTE_SUFFIX):
            return None
        code = route.removeprefix(self.TOUR_ROUTE_PREFIX).strip("/")
        return code or None

    def _extract_preparation_tour_code(self, route: str | None) -> str | None:
        if route is None or not route.startswith(self.TOUR_ROUTE_PREFIX):
            return None
        if "/prepare/payment/" in route or "/prepare/reserved/" in route:
            return None
        if not route.endswith(self.TOUR_PREPARATION_ROUTE_SUFFIX):
            return None
        code = route.removeprefix(self.TOUR_ROUTE_PREFIX)
        code = code.removesuffix(self.TOUR_PREPARATION_ROUTE_SUFFIX).strip("/")
        return code or None

    @staticmethod
    def _extract_supplier_offer_id(route: str | None) -> int | None:
        if not route:
            return None
        m = re.match(r"^/supplier-offers/(\d+)/?$", route.strip())
        if not m:
            return None
        return int(m.group(1))


def main(page: ft.Page) -> None:
    settings = get_mini_app_settings()
    page.title = settings.mini_app_title
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    # Let each screen own scrolling (e.g. catalog Column with expand+scroll). Page-level
    # scroll competes with inner scroll in Telegram WebView and breaks touch scrolling on mobile.
    page.scroll = None

    shell = MiniAppShell(page)
    page.on_route_change = shell.handle_route_change
    page.on_view_pop = shell.handle_view_pop
    # Web client often syncs route "/" before this runs. A later page.go("/") then matches
    # Page.__last_route and Flet skips on_route_change (before_event returns False), so
    # views stay empty — white screen. Mirror Flet routing docs: invoke the handler once.
    shell.handle_route_change(
        ft.RouteChangeEvent("route_change", page, page.route or "/")
    )
    page.run_task(shell.hydrate_language_from_server)
