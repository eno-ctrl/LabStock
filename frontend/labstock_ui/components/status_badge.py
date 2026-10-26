import flet as ft

from frontend.labstock_ui.config import (
    COLOR_CODE_BG,
    COLOR_DARK_GREEN,
    COLOR_ERROR,
    COLOR_ERROR_BG,
    COLOR_ERROR_BORDER,
    COLOR_INFO,
    COLOR_INFO_BG,
    COLOR_INFO_BORDER,
    COLOR_MINT_TINT,
    COLOR_PRIMARY_MINT,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    COLOR_WARNING_BG,
    COLOR_WARNING_BORDER,
)


def status_badge(status_text: str) -> ft.Container:
    """Builds a pill badge conforming to Clinical Precision status tokens."""
    st = status_text.upper().replace(" ", "_")

    bg = COLOR_MINT_TINT
    border = COLOR_PRIMARY_MINT
    text_color = COLOR_DARK_GREEN
    icon = ft.Icons.CHECK_CIRCLE_OUTLINE
    label = status_text.replace("_", " ").title()

    if "LOW" in st:
        bg = COLOR_WARNING_BG
        border = COLOR_WARNING_BORDER
        text_color = COLOR_WARNING
        icon = ft.Icons.WARNING_AMBER_ROUNDED
        label = "Low Stock"
    elif "OUT" in st or "CRITICAL" in st or "CANCEL" in st or "DAMAGE" in st:
        bg = COLOR_ERROR_BG
        border = COLOR_ERROR_BORDER
        text_color = COLOR_ERROR
        icon = ft.Icons.ERROR_OUTLINE_ROUNDED
        label = "Out of Stock" if "OUT" in st else label
    elif "SUBMITTED" in st or "PENDING" in st:
        bg = COLOR_WARNING_BG
        border = COLOR_WARNING_BORDER
        text_color = COLOR_WARNING
        icon = ft.Icons.SCHEDULE
    elif "ORDERED" in st or "PARTIAL" in st:
        bg = COLOR_INFO_BG
        border = COLOR_INFO_BORDER
        text_color = COLOR_INFO
        icon = ft.Icons.LOCAL_SHIPPING_OUTLINED
    elif "DRAFT" in st:
        bg = "#F1F5F9"
        border = "#CBD5E1"
        text_color = "#64748B"
        icon = ft.Icons.EDIT_NOTE

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(icon, size=13, color=text_color),
                ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=text_color),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        ),
        bgcolor=bg,
        border=ft.Border.all(1, border),
        border_radius=9999,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
    )


def sku_chip(sku: str) -> ft.Container:
    """Monospace SKU tag container with soft outline."""
    return ft.Container(
        content=ft.Text(
            sku,
            size=11,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT_PRIMARY,
            font_family="monospace",
        ),
        bgcolor=COLOR_CODE_BG,
        border=ft.Border.all(1, "#E2E8F0"),
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
    )
