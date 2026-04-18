"""Hotfix: My request detail must not build Flet controls with empty required content."""

from __future__ import annotations

import flet as ft


def test_filled_button_with_content_instantiates_when_hidden() -> None:
    b = ft.FilledButton("Continue", visible=False, on_click=lambda _: None)
    assert b.content == "Continue"
