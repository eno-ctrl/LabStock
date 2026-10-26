import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_SURFACE,
)


def table_container(table_control: ft.Control) -> ft.Container:
    """Wraps data tables in a standardized Clinical Precision card container."""
    return ft.Container(
        content=ft.Column(
            controls=[table_control],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
        ),
        bgcolor=COLOR_SURFACE,
        border=ft.Border.all(1, COLOR_BORDER),
        border_radius=10,
        expand=True,
    )
