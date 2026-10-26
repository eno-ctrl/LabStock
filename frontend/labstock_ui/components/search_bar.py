import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


def search_bar(
    placeholder: str = "Search...",
    on_change=None,
    on_submit=None,
    width: int | None = 320,
) -> ft.TextField:
    """Standardized Clinical Precision search bar component."""
    return ft.TextField(
        hint_text=placeholder,
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        text_size=13,
        height=40,
        width=width,
        bgcolor=COLOR_SURFACE,
        border_color=COLOR_BORDER,
        border_radius=8,
        color=COLOR_TEXT_PRIMARY,
        hint_style=ft.TextStyle(color=COLOR_TEXT_SECONDARY, size=13),
        on_change=on_change,
        on_submit=on_submit,
    )
