import flet as ft

from frontend.labstock_ui.config import COLOR_PRIMARY_NAVY, COLOR_TEXT_SECONDARY


def loading_state(message: str = "Loading data...") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.ProgressRing(color=COLOR_PRIMARY_NAVY, width=32, height=32),
                ft.Text(message, size=13, color=COLOR_TEXT_SECONDARY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.Alignment(0, 0),
        padding=40,
        expand=True,
    )
