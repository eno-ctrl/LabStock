import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
)


def filter_dropdown(
    label: str,
    options: list[tuple[str, str]],
    value: str | None = None,
    on_change=None,
    width: int = 180,
) -> ft.Dropdown:
    """Standardized Clinical Precision filter dropdown."""
    return ft.Dropdown(
        label=label,
        value=value,
        options=[ft.dropdown.Option(k, text=v) for k, v in options],
        dense=True,
        text_size=13,
        height=40,
        width=width,
        bgcolor=COLOR_SURFACE,
        border_color=COLOR_BORDER,
        border_radius=8,
        color=COLOR_TEXT_PRIMARY,
        on_change=on_change,
    )
