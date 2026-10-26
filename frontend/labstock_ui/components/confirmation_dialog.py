from collections.abc import Callable

import flet as ft

from frontend.labstock_ui.config import COLOR_ERROR, COLOR_PRIMARY_NAVY


def show_confirmation_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm: Callable[[], None],
    confirm_label: str = "Confirm",
    is_destructive: bool = False,
):
    def close_dialog(e):
        dialog.open = False
        page.update()

    def handle_confirm(e):
        close_dialog(e)
        on_confirm()

    confirm_btn = ft.ElevatedButton(
        text=confirm_label,
        bgcolor=COLOR_ERROR if is_destructive else COLOR_PRIMARY_NAVY,
        color="white",
        on_click=handle_confirm,
    )

    cancel_btn = ft.OutlinedButton(
        text="Cancel",
        on_click=close_dialog,
    )

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight=ft.FontWeight.W_600, size=16),
        content=ft.Text(message, size=14),
        actions=[cancel_btn, confirm_btn],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
