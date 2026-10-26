import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


def metric_card(
    title: str,
    value: str,
    subtitle: str | None = None,
    icon: ft.Icon = ft.Icons.INVENTORY_2_OUTLINED,
    icon_bg: str = "#E5EEFF",
    icon_color: str = "#15263B",
    value_color: str = COLOR_TEXT_PRIMARY,
    on_click=None,
) -> ft.Container:
    """Enterprise metric display card with crisp borders and clean typography."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            title, size=12, weight=ft.FontWeight.W_600, color=COLOR_TEXT_SECONDARY
                        ),
                        ft.Container(
                            content=ft.Icon(icon, size=18, color=icon_color),
                            width=32,
                            height=32,
                            border_radius=8,
                            bgcolor=icon_bg,
                            alignment=ft.Alignment(0, 0),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=4),
                ft.Text(
                    value,
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=value_color,
                    font_family="monospace",
                ),
                ft.Text(subtitle or "", size=11, color=COLOR_TEXT_SECONDARY)
                if subtitle
                else ft.Container(),
            ],
            spacing=2,
            tight=True,
        ),
        bgcolor=COLOR_SURFACE,
        border=ft.Border.all(1, COLOR_BORDER),
        border_radius=10,
        padding=16,
        expand=True,
        on_click=on_click,
    )
