from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation

import flet as ft
import httpx

from app.schemas.mini_app import MiniAppCatalogRead, MiniAppReservationPreparationRead, MiniAppTourDetailRead
from app.schemas.prepared import CatalogTourCardRead, ReservationPreparationSummaryRead
from app.schemas.tour import BoardingPointRead
from mini_app.api_client import MiniAppApiClient
from mini_app.config import get_mini_app_settings


class CatalogScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
        on_open_detail: Callable[[str], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.on_open_detail = on_open_detail

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
                            "Browse open tours and narrow the list with a small set of safe filters.",
                            color=ft.Colors.ON_SURFACE_VARIANT,
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
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.on_back = on_back
        self.on_prepare = on_prepare
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
                                )
                            ]
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
                    "Showing fallback language content for this tour.",
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
        on_back: Callable[[str], None],
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code
        self.on_back = on_back
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
        self.preview_button = ft.ElevatedButton("Preview reservation", on_click=self._on_preview_summary)
        self.preparation_note = ft.Text(
            "Preparation only. No reservation is created at this step.",
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
                                )
                            ]
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
            return

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
                                "This is a preparation-only preview. Reservation creation remains the next step.",
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=8,
                    ),
                ),
            ]
        )

    def _on_preview_summary(self, _: ft.ControlEvent) -> None:
        self.page.run_task(self.load_summary)

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_text.visible = True
        self.page.update()

    def _set_loading(self, is_loading: bool) -> None:
        self.loading_row.visible = is_loading
        self.preview_button.disabled = is_loading


class MiniAppShell:
    TOUR_ROUTE_PREFIX = "/tours/"
    TOUR_PREPARATION_ROUTE_SUFFIX = "/prepare"

    def __init__(self, page: ft.Page) -> None:
        settings = get_mini_app_settings()
        self.page = page
        self.api_client = MiniAppApiClient(settings.normalized_api_base_url)
        self.catalog_screen = CatalogScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            on_open_detail=self.open_tour_detail,
        )
        self.tour_detail_screen = TourDetailScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            on_back=self.open_catalog,
            on_prepare=self.open_tour_preparation,
        )
        self.reservation_preparation_screen = ReservationPreparationScreen(
            page,
            api_client=self.api_client,
            default_language_code=settings.mini_app_default_language,
            on_back=self.open_tour_detail,
        )

    def handle_route_change(self, _: ft.RouteChangeEvent) -> None:
        self.page.views.clear()
        self.page.views.append(ft.View(route="/", controls=[self.catalog_screen.build()], padding=0, spacing=0))

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

    def open_tour_detail(self, tour_code: str) -> None:
        self.page.go(f"{self.TOUR_ROUTE_PREFIX}{tour_code}")

    def open_tour_preparation(self, tour_code: str) -> None:
        self.page.go(f"{self.TOUR_ROUTE_PREFIX}{tour_code}{self.TOUR_PREPARATION_ROUTE_SUFFIX}")

    def _extract_tour_code(self, route: str | None) -> str | None:
        if route is None or not route.startswith(self.TOUR_ROUTE_PREFIX):
            return None
        if route.endswith(self.TOUR_PREPARATION_ROUTE_SUFFIX):
            return None
        code = route.removeprefix(self.TOUR_ROUTE_PREFIX).strip("/")
        return code or None

    def _extract_preparation_tour_code(self, route: str | None) -> str | None:
        if route is None or not route.startswith(self.TOUR_ROUTE_PREFIX):
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
    page.go(page.route or "/")
