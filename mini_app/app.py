from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import flet as ft
import httpx

from app.models.enums import PaymentStatus
from app.schemas.mini_app import (
    MiniAppBookingDetailRead,
    MiniAppBookingFacadeState,
    MiniAppBookingPrimaryCta,
    MiniAppBookingsListRead,
    MiniAppCatalogRead,
    MiniAppReservationPreparationRead,
    MiniAppTourDetailRead,
)
from app.schemas.prepared import (
    CatalogTourCardRead,
    OrderSummaryRead,
    PaymentEntryRead,
    ReservationPreparationSummaryRead,
)
from app.schemas.tour import BoardingPointRead
from mini_app.api_client import MiniAppApiClient
from mini_app.config import get_mini_app_settings


def _payment_status_user_label(status: PaymentStatus) -> str:
    labels: dict[PaymentStatus, str] = {
        PaymentStatus.AWAITING_PAYMENT: "Waiting for payment",
        PaymentStatus.UNPAID: "Not paid yet",
        PaymentStatus.PAID: "Paid",
    }
    return labels.get(status, status.value.replace("_", " ").title())


def _hold_timer_hint(expires_at: datetime | None) -> str:
    if expires_at is None:
        return "No payment deadline is set for this hold."
    now = datetime.now(UTC)
    end = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
    if end <= now:
        return "This hold has expired. Return to the catalog to check availability."
    total_minutes = max(0, int((end - now).total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    return (
        f"Time left to pay: about {hours}h {minutes}m "
        f"(deadline {CatalogScreen._format_datetime(expires_at)})."
    )


class CatalogScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        on_open_detail: Callable[[str], None],
        on_my_bookings: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_help: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.on_open_detail = on_open_detail
        self.on_my_bookings = on_my_bookings
        self.on_open_settings = on_open_settings
        self.on_help = on_help

        self.destination_field = ft.TextField(label="Destination", hint_text="Belgrade", dense=True)
        self.departure_from_field = ft.TextField(label="Departure from", hint_text="YYYY-MM-DD", dense=True)
        self.departure_to_field = ft.TextField(label="Departure to", hint_text="YYYY-MM-DD", dense=True)
        self.max_price_field = ft.TextField(label="Max price", hint_text="150", dense=True)
        self.apply_button = ft.ElevatedButton("Apply filters", on_click=self._on_apply_filters)
        self.clear_button = ft.TextButton("Clear", on_click=self._on_clear_filters)
        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Loading tours...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.summary_text = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT)
        self.empty_state = ft.Text(
            "No tours match the current filters. Try clearing one or more filters.",
            visible=False,
        )
        self.cards_column = ft.Column(spacing=12)

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Text("Tours catalog", size=26, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Main booking flow: browse here, then use My bookings for reservation and payment status. "
                            "Optional filters below mirror the quick shortcuts in the bot chat.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(
                            [
                                ft.OutlinedButton("My bookings", on_click=lambda _: self.on_my_bookings()),
                                ft.OutlinedButton(
                                    "Language & settings",
                                    on_click=lambda _: self.on_open_settings(),
                                ),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
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
                                    ft.Text("Filters", size=18, weight=ft.FontWeight.W_600),
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
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_catalog(self) -> None:
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
        badges = ft.Row(
            [
                self._build_badge(self._status_label(card.status.value), ft.Colors.BLUE_50, ft.Colors.BLUE_900),
                self._build_badge(
                    "Seats available" if card.is_available else "Sold out",
                    ft.Colors.GREEN_50 if card.is_available else ft.Colors.RED_50,
                    ft.Colors.GREEN_900 if card.is_available else ft.Colors.RED_900,
                ),
            ],
            spacing=8,
        )
        description = card.short_description or "Open the detail screen to see the full tour description."
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
            padding=16,
            content=ft.Column(
                [
                    badges,
                    ft.Text(card.title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"{self._format_datetime(card.departure_datetime)} | {card.duration_days} day(s)",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        f"{self._format_price(card.base_price)} {card.currency} | {card.seats_available} / {card.seats_total} seats left",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(description, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row(
                        [ft.TextButton("View details", on_click=lambda _, code=card.code: self.on_open_detail(code))],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
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
            return exc.response.json().get("detail", default)
        except Exception:
            return default


class TourDetailScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        on_back: Callable[[], None],
        on_prepare: Callable[[str], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.on_back = on_back
        self.on_prepare = on_prepare
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.current_tour_code: str | None = None

        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Loading tour details...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.content_column = ft.Column(spacing=14)

    def set_tour_code(self, tour_code: str) -> None:
        self.current_tour_code = tour_code

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Back to catalog",
                                    icon=ft.Icons.ARROW_BACK,
                                    on_click=lambda _: self.on_back(),
                                ),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
                                ft.TextButton("Settings", on_click=lambda _: self.on_open_settings()),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            wrap=True,
                        ),
                        self.loading_row,
                        self.error_text,
                        self.content_column,
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_tour_detail(self) -> None:
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
            self._render_detail(detail)
        finally:
            self._set_loading(False)
            self.page.update()

    def _render_detail(self, detail: MiniAppTourDetailRead | None) -> None:
        self.content_column.controls.clear()
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
                    "Seats available" if detail.is_available else "Sold out",
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
                    f"{CatalogScreen._format_datetime(detail.tour.departure_datetime)} | {detail.tour.duration_days} day(s)",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Text(
                    f"{CatalogScreen._format_price(detail.tour.base_price)} {detail.tour.currency} | {detail.tour.seats_available} / {detail.tour.seats_total} seats left",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ]
        )

        self.content_column.controls.append(
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Prepare reservation",
                        on_click=lambda _, code=detail.tour.code: self.on_prepare(code),
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )

        if localized.used_fallback:
            self.content_column.controls.append(
                ft.Text(
                    "No translation is available for your selected language for this tour; "
                    "showing the next available language (see Language & settings).",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        overview = localized.full_description or localized.short_description
        if overview:
            self.content_column.controls.append(self._build_text_section("Overview", overview))
        if localized.program_text:
            self.content_column.controls.append(self._build_text_section("Program", localized.program_text))
        if localized.included_text:
            self.content_column.controls.append(self._build_text_section("Included", localized.included_text))
        if localized.excluded_text:
            self.content_column.controls.append(self._build_text_section("Not included", localized.excluded_text))

        self.content_column.controls.append(ft.Text("Boarding points", size=18, weight=ft.FontWeight.W_600))
        if detail.boarding_points:
            for boarding_point in detail.boarding_points:
                self.content_column.controls.append(self._build_boarding_point_card(boarding_point))
        else:
            self.content_column.controls.append(
                ft.Text("Boarding point details are not available for this tour yet.")
            )

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
        notes = boarding_point.notes or "No extra notes for this boarding point."
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=16,
            padding=16,
            content=ft.Column(
                [
                    ft.Text(boarding_point.city, size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(boarding_point.address),
                    ft.Text(f"Departure time: {boarding_point.time.strftime('%H:%M')}"),
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
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_reserved = on_reserved
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.current_tour_code: str | None = None

        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Loading reservation options...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.selection_container = ft.Column(spacing=12)
        self.summary_container = ft.Column(spacing=12)
        self.seats_dropdown = ft.Dropdown(label="Seats", dense=True, options=[])
        self.boarding_dropdown = ft.Dropdown(label="Boarding point", dense=True, options=[])
        self.preview_button = ft.OutlinedButton("Preview summary", on_click=self._on_preview_summary)
        self.confirm_reserve_button = ft.ElevatedButton(
            "Confirm Reservation",
            disabled=True,
            on_click=lambda _: self.page.run_task(self._confirm_reservation),
        )
        self.preparation_note = ft.Text(
            "Pick seats and boarding, preview the summary, then confirm to create a temporary reservation "
            f"(dev user id {dev_telegram_user_id}). Payment entry follows on the next screen.",
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

    def set_tour_code(self, tour_code: str) -> None:
        self.current_tour_code = tour_code

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Back to tour details",
                                    icon=ft.Icons.ARROW_BACK,
                                    on_click=lambda _: self.on_back(self.current_tour_code or ""),
                                ),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
                                ft.TextButton("Settings", on_click=lambda _: self.on_open_settings()),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            wrap=True,
                        ),
                        self.loading_row,
                        self.error_text,
                        self.preparation_note,
                        self.selection_container,
                        self.summary_container,
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_preparation(self) -> None:
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
        if preparation is None:
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

        localized = preparation.tour.localized_content
        self.selection_container.controls.extend(
            [
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
        self.summary_container.controls.extend(
            [
                ft.Text("Preparation summary", size=20, weight=ft.FontWeight.W_600),
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    border_radius=16,
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(summary.tour.localized_content.title, size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Seats: {summary.seats_count}"),
                            ft.Text(
                                f"Boarding point: {summary.boarding_point.city}, {summary.boarding_point.address}"
                            ),
                            ft.Text(
                                f"Boarding time: {summary.boarding_point.time.strftime('%H:%M')}"
                            ),
                            ft.Text(
                                f"Estimated total: {CatalogScreen._format_price(summary.estimated_total_amount)} {summary.tour.currency}"
                            ),
                            ft.Text(
                                "Your seats are not held until you confirm. This creates a temporary hold; "
                                "complete payment before the deadline on the next screens.",
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
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_continue_to_payment = on_continue_to_payment
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.tour_code: str | None = None
        self.order_id: int | None = None

        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Loading reservation...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=10)
        self.continue_button = ft.ElevatedButton(
            "Continue to payment",
            disabled=True,
            on_click=lambda _: self._on_continue(),
        )

    def set_context(self, *, tour_code: str, order_id: int) -> None:
        self.tour_code = tour_code
        self.order_id = order_id

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Back to preparation",
                                    icon=ft.Icons.ARROW_BACK,
                                    on_click=lambda _: self.on_back(self.tour_code or ""),
                                ),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
                                ft.TextButton("Settings", on_click=lambda _: self.on_open_settings()),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            wrap=True,
                        ),
                        self.loading_row,
                        self.error_text,
                        ft.Text("Reservation confirmed", size=26, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Temporary hold is active. Pay before the deadline or the seats may be released.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        self.body_column,
                        ft.Row([self.continue_button], alignment=ft.MainAxisAlignment.START),
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_overview(self) -> None:
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
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(overview.tour.localized_content.title, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Reservation reference: #{order.id}"),
                        ft.Text(
                            f"Amount to pay: {CatalogScreen._format_price(order.total_amount)} {order.currency}"
                        ),
                        ft.Text(
                            f"Payment status: {_payment_status_user_label(order.payment_status)}",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(_hold_timer_hint(expires)),
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


class PaymentEntryScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        dev_telegram_user_id: int,
        on_back: Callable[[str], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back = on_back
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.tour_code: str | None = None
        self.order_id: int | None = None
        self._last_entry: PaymentEntryRead | None = None

        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Starting payment entry...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=10)
        self.pay_now_button = ft.ElevatedButton("Pay Now", on_click=self._on_pay_now)

    def set_context(self, *, tour_code: str, order_id: int) -> None:
        self.tour_code = tour_code
        self.order_id = order_id

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Back to preparation",
                                    icon=ft.Icons.ARROW_BACK,
                                    on_click=lambda _: self.on_back(self.tour_code or ""),
                                ),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
                                ft.TextButton("Settings", on_click=lambda _: self.on_open_settings()),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            wrap=True,
                        ),
                        self.loading_row,
                        self.error_text,
                        ft.Text("Payment", size=26, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Reservation is temporary. Complete payment before the hold expires. "
                            "Details below come from the server; payment is not marked successful until the backend confirms it.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        self.body_column,
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_payment_entry(self) -> None:
        if self.order_id is None:
            self._show_error("Missing order reference.")
            return

        self._set_loading(True)
        self.error_text.visible = False
        self.body_column.controls.clear()
        self.page.update()

        try:
            entry = await self.api_client.start_payment_entry(
                order_id=self.order_id,
                telegram_user_id=self.dev_telegram_user_id,
            )
        except httpx.HTTPStatusError as exc:
            message = CatalogScreen._http_error_message(
                exc,
                default="Unable to start payment entry for this reservation.",
            )
            self._show_error(message)
        except Exception:
            self._show_error("Unable to start payment entry for this reservation.")
        else:
            self._render_entry(entry)
        finally:
            self._set_loading(False)
            self.page.update()

    def _render_entry(self, entry: PaymentEntryRead) -> None:
        self._last_entry = entry
        order = entry.order
        expires = order.reservation_expires_at
        expiry_line = (
            f"Pay before: {CatalogScreen._format_datetime(expires)}"
            if expires
            else "Reservation expiry time is not available."
        )
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(f"Reservation reference: #{order.id}", weight=ft.FontWeight.W_600),
                        ft.Text(expiry_line),
                        ft.Text(_hold_timer_hint(expires)),
                        ft.Text(
                            f"Amount due: {CatalogScreen._format_price(order.total_amount)} {order.currency}"
                        ),
                        ft.Text(f"Payment session reference: {entry.payment_session_reference}"),
                        ft.Text(
                            f"Status: {_payment_status_user_label(entry.payment.status)}",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            "Provider checkout inside this app is not connected yet. "
                            "Pay Now explains the next step; nothing is shown as paid until reconciliation confirms it.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=8,
                ),
            ),
            ft.Row([self.pay_now_button], alignment=ft.MainAxisAlignment.START),
        ]

    def _on_pay_now(self, _: ft.ControlEvent) -> None:
        entry = self._last_entry
        if entry is None:
            return
        if entry.payment_url:
            self.page.launch_url(entry.payment_url)
            return
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(
                "Checkout is not available inside this Mini App yet. Keep your payment session reference; "
                "when a provider URL is configured, Pay Now will open it. "
                "Your booking is not paid until the server confirms payment."
            ),
            action="OK",
        )
        self.page.snack_bar.open = True
        self.page.update()

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
        dev_telegram_user_id: int,
        on_back_catalog: Callable[[], None],
        on_open_booking: Callable[[int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back_catalog = on_back_catalog
        self.on_open_booking = on_open_booking
        self.on_help = on_help
        self.on_open_settings = on_open_settings

        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Loading bookings...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.items_column = ft.Column(spacing=12)

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton("Back to catalog", on_click=lambda _: self.on_back_catalog()),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
                                ft.TextButton("Settings", on_click=lambda _: self.on_open_settings()),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            wrap=True,
                        ),
                        ft.Text("My bookings", size=26, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Temporary holds, confirmed trips, and released holds (not paid) are listed below.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        self.loading_row,
                        self.error_text,
                        self.items_column,
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_bookings(self) -> None:
        self.loading_row.visible = True
        self.error_text.visible = False
        self.page.update()
        try:
            data = await self.api_client.list_my_bookings(
                telegram_user_id=self.dev_telegram_user_id,
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
        if data is None:
            return
        if not data.items:
            self.items_column.controls.append(
                ft.Text("No bookings yet. Browse the catalog to reserve a tour.", color=ft.Colors.ON_SURFACE_VARIANT)
            )
            return
        for item in data.items:
            s = item.summary
            tour = s.tour
            title = tour.localized_content.title
            dep = CatalogScreen._format_datetime(tour.departure_datetime)
            amount = f"{CatalogScreen._format_price(s.order.total_amount)} {s.order.currency}"
            self.items_column.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    border_radius=16,
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(dep, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(f"{amount} · {s.order.seats_count} seat(s)", color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(item.user_visible_booking_label, weight=ft.FontWeight.W_500),
                            ft.Text(item.user_visible_payment_label, color=ft.Colors.ON_SURFACE_VARIANT, size=13),
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        "Open",
                                        on_click=lambda _, oid=s.order.id: self.on_open_booking(oid),
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=6,
                    ),
                )
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
        dev_telegram_user_id: int,
        on_back_to_bookings: Callable[[], None],
        on_browse_tours: Callable[[], None],
        on_pay_now: Callable[[str, int], None],
        on_help: Callable[[], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = language_code
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_back_to_bookings = on_back_to_bookings
        self.on_browse_tours = on_browse_tours
        self.on_pay_now = on_pay_now
        self.on_help = on_help
        self.on_open_settings = on_open_settings
        self.order_id: int | None = None
        self._last_detail: MiniAppBookingDetailRead | None = None

        self.loading_row = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2), ft.Text("Loading booking...")],
            visible=False,
            spacing=10,
        )
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.body_column = ft.Column(spacing=12)

    def set_order_id(self, order_id: int) -> None:
        self.order_id = order_id

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.TextButton("Back to bookings", on_click=lambda _: self.on_back_to_bookings()),
                                ft.TextButton("Help", on_click=lambda _: self.on_help()),
                                ft.TextButton("Settings", on_click=lambda _: self.on_open_settings()),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            wrap=True,
                        ),
                        ft.Text("Booking details", size=22, weight=ft.FontWeight.BOLD),
                        self.loading_row,
                        self.error_text,
                        self.body_column,
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_detail(self) -> None:
        if self.order_id is None:
            return
        self.loading_row.visible = True
        self.error_text.visible = False
        self.page.update()
        try:
            detail = await self.api_client.get_booking_status(
                order_id=self.order_id,
                telegram_user_id=self.dev_telegram_user_id,
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
            [ft.Text(_hold_timer_hint(order.reservation_expires_at), color=ft.Colors.ON_SURFACE_VARIANT)]
            if detail.facade_state == MiniAppBookingFacadeState.ACTIVE_TEMPORARY_RESERVATION
            else []
        )
        pay_hint = (
            [ft.Text(detail.payment_session_hint, size=12, color=ft.Colors.ON_SURFACE_VARIANT)]
            if detail.payment_session_hint
            else []
        )
        self.body_column.controls = [
            ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border_radius=16,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(f"Booking reference: #{order.id}", weight=ft.FontWeight.W_600),
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
                        ft.Text(detail.user_visible_booking_label, weight=ft.FontWeight.W_600),
                        ft.Text(detail.user_visible_payment_label, color=ft.Colors.ON_SURFACE_VARIANT),
                        *timer_line,
                        *pay_hint,
                    ],
                    spacing=8,
                ),
            ),
        ]
        cta_row: list[ft.Control] = []
        if detail.primary_cta == MiniAppBookingPrimaryCta.PAY_NOW:
            cta_row.append(
                ft.FilledButton(
                    "Pay now",
                    on_click=lambda _: self.on_pay_now(tour.code, order.id),
                )
            )
        elif detail.primary_cta == MiniAppBookingPrimaryCta.BROWSE_TOURS:
            cta_row.append(
                ft.FilledButton(
                    "Browse tours",
                    on_click=lambda _: self.on_browse_tours(),
                )
            )
        else:
            cta_row.append(
                ft.OutlinedButton(
                    "Back to bookings",
                    on_click=lambda _: self.on_back_to_bookings(),
                )
            )
        self.body_column.controls.append(ft.Row(cta_row, alignment=ft.MainAxisAlignment.START))

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True


class HelpScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        on_close: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.on_close = on_close
        self.body_column = ft.Column(spacing=12)

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.TextButton("Back", icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.on_close())],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Text("Help", size=26, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Close the Mini App or switch back to the bot chat in Telegram anytime — "
                            "the bot is your guide; this app is where you book and pay.",
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        self.body_column,
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_content(self) -> None:
        self.body_column.controls = [
            ft.Row(
                [ft.ProgressRing(width=20, height=20, stroke_width=2), ft.Text("Loading help...")],
                spacing=10,
            )
        ]
        self.page.update()
        try:
            h = await self.api_client.get_help()
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
            self.body_column.controls = blocks
        self.page.update()


class SettingsScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        dev_telegram_user_id: int,
        on_language_applied: Callable[[str], None],
        on_close: Callable[[], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.dev_telegram_user_id = dev_telegram_user_id
        self.on_language_applied = on_language_applied
        self.on_close = on_close
        self.language_dropdown = ft.Dropdown(label="Display language", dense=True, width=320, options=[])
        self.hint_text = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.error_text = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.save_button = ft.FilledButton("Save", on_click=lambda _: self.page.run_task(self._save_language))

    def build(self) -> ft.Control:
        return ft.SafeArea(
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row(
                            [ft.TextButton("Back", icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.on_close())],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Text("Language & settings", size=26, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Choose the language for tour content and booking summaries. "
                            "If a translation is missing, the app falls back and tells you.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        self.language_dropdown,
                        self.hint_text,
                        self.error_text,
                        ft.Row([self.save_button], alignment=ft.MainAxisAlignment.START),
                    ],
                    spacing=14,
                    scroll=ft.ScrollMode.AUTO,
                ),
            )
        )

    async def load_options(self) -> None:
        self.error_text.visible = False
        self.page.update()
        try:
            snap = await self.api_client.get_mini_app_settings(telegram_user_id=self.dev_telegram_user_id)
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
        try:
            applied = await self.api_client.post_language_preference(
                telegram_user_id=self.dev_telegram_user_id,
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

    def __init__(self, page: ft.Page) -> None:
        settings = get_mini_app_settings()
        self.page = page
        self.api_client = MiniAppApiClient(settings.normalized_api_base_url)
        self._dev_telegram_user_id = settings.mini_app_dev_telegram_user_id
        self._modal_return_route: str = "/"
        self.catalog_screen = CatalogScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            on_open_detail=self.open_tour_detail,
            on_my_bookings=self.open_bookings,
            on_open_settings=self.open_settings,
            on_help=self.open_help,
        )
        self.my_bookings_screen = MyBookingsScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back_catalog=self.open_catalog,
            on_open_booking=self.open_booking_detail,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
        )
        self.booking_detail_screen = BookingDetailScreen(
            page,
            api_client=self.api_client,
            language_code=settings.mini_app_default_language,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back_to_bookings=self.open_bookings,
            on_browse_tours=self.open_catalog,
            on_pay_now=self.open_payment_entry,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
        )
        self.tour_detail_screen = TourDetailScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            on_back=self.open_catalog,
            on_prepare=self.open_tour_preparation,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
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
        )
        self.payment_entry_screen = PaymentEntryScreen(
            page,
            api_client=self.api_client,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_back=self.open_reservation_success_from_payment,
            on_help=self.open_help,
            on_open_settings=self.open_settings,
        )
        self.help_screen = HelpScreen(page, api_client=self.api_client, on_close=self.close_modal)
        self.settings_screen = SettingsScreen(
            page,
            api_client=self.api_client,
            dev_telegram_user_id=self._dev_telegram_user_id,
            on_language_applied=self.apply_language,
            on_close=self.close_modal,
        )

    def apply_language(self, code: str) -> None:
        self.catalog_screen.language_code = code
        self.tour_detail_screen.language_code = code
        self.reservation_preparation_screen.language_code = code
        self.reservation_success_screen.language_code = code
        self.my_bookings_screen.language_code = code
        self.booking_detail_screen.language_code = code

    async def hydrate_language_from_server(self) -> None:
        try:
            snap = await self.api_client.get_mini_app_settings(telegram_user_id=self._dev_telegram_user_id)
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

    def close_modal(self) -> None:
        target = self._modal_return_route or "/"
        self.page.go(target)

    def handle_route_change(self, _: ft.RouteChangeEvent) -> None:
        self.page.views.clear()
        self.page.views.append(ft.View(route="/", controls=[self.catalog_screen.build()], padding=0, spacing=0))

        if self._is_help_route(self.page.route):
            self.page.views.append(ft.View(route="/help", controls=[self.help_screen.build()], padding=0, spacing=0))
            self.page.update()
            self.page.run_task(self.help_screen.load_content)
            return

        if self._is_settings_route(self.page.route):
            self.page.views.append(
                ft.View(route="/settings", controls=[self.settings_screen.build()], padding=0, spacing=0)
            )
            self.page.update()
            self.page.run_task(self.settings_screen.load_options)
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


def main(page: ft.Page) -> None:
    settings = get_mini_app_settings()
    page.title = settings.mini_app_title
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

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
