"""
Flet Mini App entrypoint.

- Local: starts a small web server (opens browser when not in container mode).
- Railway/container: set PORT (and optionally FLET_HOST); binds 0.0.0.0 so Telegram can open the public URL.

Start examples:
  python -m mini_app.main
  python -m mini_app.main   # with PORT=8080 FLET_HOST=0.0.0.0 in env
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import flet as ft

from mini_app.app import main as app_main


def run_mini_app() -> None:
    """Run the Flet web UI. Uses PORT/FLET_HOST when set (Railway, Docker)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    port = 0
    host: str | None = None
    project_root = Path(__file__).resolve().parent.parent
    root_assets_dir = project_root / "assets"
    package_assets_dir = Path(__file__).resolve().parent / "assets"
    if root_assets_dir.exists():
        assets_dir = str(root_assets_dir)
    elif package_assets_dir.exists():
        assets_dir = str(package_assets_dir)
    else:
        assets_dir = "assets"
    port_raw = os.environ.get("PORT") or os.environ.get("FLET_SERVER_PORT")
    if port_raw:
        port = int(port_raw)
        host = os.environ.get("FLET_HOST", "0.0.0.0")

    # ft.app is deprecated. no_cdn=True avoids blank web UI when CDN assets are blocked.
    ft.run(
        app_main,
        view=ft.AppView.WEB_BROWSER,
        no_cdn=True,
        assets_dir=assets_dir,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    run_mini_app()
