import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


def empty_state(
    title: str = "No records found",
    message: str = "No data is currently available matching your request.",
    icon: ft.Icon = ft.Icons.INVENTORY_2_OUTLINED,
    action_label: str | None = None,
    on_action=None,
) -> ft.Container:
    controls = [
        ft.Container(
            content=ft.Icon(icon, size=36, color=COLOR_TEXT_SECONDARY),
            width=64,
            height=64,
            border_radius=32,
            bgcolor="#F1F5F9",
            alignment=ft.Alignment(0, 0),
        ),
        ft.Text(title, size=15, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
        ft.Text(message, size=13, color=COLOR_TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
    ]

    if action_label and on_action:
        controls.append(ft.Container(height=8))
        controls.append(
            ft.ElevatedButton(
                text=action_label,
                icon=ft.Icons.ADD,
                bgcolor=COLOR_PRIMARY_NAVY,
                color="white",
                on_click=on_action,
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=controls,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        alignment=ft.Alignment(0, 0),
        bgcolor=COLOR_SURFACE,
        border=ft.Border.all(1, COLOR_BORDER),
        border_radius=10,
        padding=48,
        expand=True,
    )
