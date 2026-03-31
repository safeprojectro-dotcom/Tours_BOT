import flet as ft

from mini_app.app import main


if __name__ == "__main__":
    # Use ft.run (ft.app is deprecated). no_cdn=True avoids blank web UI when CDN assets are blocked.
    ft.run(main, view=ft.AppView.WEB_BROWSER, no_cdn=True)
