import flet as ft

from mini_app.app import main


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
