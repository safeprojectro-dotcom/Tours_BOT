from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

import httpx
import flet as ft

from app.schemas.mini_app import MiniAppCatalogRead
from app.schemas.prepared import CatalogTourCardRead
from mini_app.api_client import MiniAppApiClient
from mini_app.config import get_mini_app_settings


class CatalogScreen:
    def __init__(
        self,
        page: ft.Page,
        *,
        api_client: MiniAppApiClient,
        default_language_code: str,
    ) -> None:
        self.page = page
        self.api_client = api_client
        self.language_code = default_language_code

        self.destination_field = ft.TextField(
            label="Destination",
            hint_text="Belgrade",
            dense=True,
        )
        self.departure_from_field = ft.TextField(
            label="Departure from",
            hint_text="YYYY-MM-DD",
            dense=True,
        )
        self.departure_to_field = ft.TextField(
            label="Departure to",
            hint_text="YYYY-MM-DD",
            dense=True,
        )
        self.max_price_field = ft.TextField(
            label="Max price",
            hint_text="150",
            dense=True,
        )
        self.apply_button = ft.ElevatedButton("Apply filters", on_click=self._on_apply_filters)
        self.clear_button = ft.TextButton("Clear", on_click=self._on_clear_filters)
        self.loading_row = ft.Row(
            [
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text("Loading tours..."),
            ],
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
            detail = "Unable to load tours right now."
            if exc.response is not None:
                try:
                    detail = exc.response.json().get("detail", detail)
                except Exception:
                    detail = detail
            self._show_error(detail)
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
        description = card.short_description or "Tour summary will expand in the next Mini App slice."
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


class MiniAppShell:
    def __init__(self, page: ft.Page) -> None:
        settings = get_mini_app_settings()
        self.page = page
        self.catalog_screen = CatalogScreen(
            page,
            api_client=MiniAppApiClient(settings.normalized_api_base_url),
            default_language_code=settings.mini_app_default_language,
        )

    def handle_route_change(self, _: ft.RouteChangeEvent) -> None:
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                route="/",
                controls=[self.catalog_screen.build()],
                padding=0,
                spacing=0,
            )
        )
        self.page.update()


def main(page: ft.Page) -> None:
    settings = get_mini_app_settings()
    page.title = settings.mini_app_title
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    shell = MiniAppShell(page)
    page.on_route_change = shell.handle_route_change
    page.go(page.route or "/")
    page.run_task(shell.catalog_screen.load_catalog)
