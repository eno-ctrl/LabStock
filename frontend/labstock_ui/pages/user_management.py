from typing import Any

import flet as ft

from frontend.labstock_ui.api import user_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.empty_state import empty_state
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.components.status_badge import status_badge
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_ERROR,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class UserManagementPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.users: list = []
        self.content = loading_state("Loading user accounts...")
        self.load_users()

    def load_users(self):
        try:
            res = user_client.list_users(page_size=100)
            self.users = res.get("items", [])
            self.content = self._build_view()
        except ApiClientException as e:
            self.content = empty_state("Access Restricted", e.message, ft.Icons.LOCK_OUTLINED)
        except Exception as e:
            self.content = empty_state("Error", str(e), ft.Icons.ERROR_OUTLINE)
        self.page.update()

    def _show_toast(self, msg: str, is_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor="#DC3545" if is_error else COLOR_PRIMARY_NAVY,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _open_user_modal(self, user_data: dict[str, Any] | None = None):
        is_edit = user_data is not None

        email_input = ft.TextField(
            label="Institutional Email *",
            value=user_data.get("email", "") if is_edit else "",
            disabled=is_edit,
            height=44,
            text_size=13,
        )

        name_input = ft.TextField(
            label="Full Name *",
            value=user_data.get("full_name", "") if is_edit else "",
            height=44,
            text_size=13,
        )

        role_dropdown = ft.Dropdown(
            label="Role & Access Tier *",
            value=user_data.get("role", "viewer") if is_edit else "viewer",
            height=44,
            text_size=13,
            options=[
                ft.dropdown.Option("administrator", "Administrator (Full Control)"),
                ft.dropdown.Option("inventory_manager", "Inventory Manager (Stock & Procurement)"),
                ft.dropdown.Option("viewer", "Viewer (Read Only Access)"),
            ],
        )

        password_input = ft.TextField(
            label="Password " + ("(leave blank to keep unchanged)" if is_edit else "*"),
            password=True,
            can_reveal_password=True,
            height=44,
            text_size=13,
        )

        active_switch = ft.Switch(
            label="Active User Account",
            value=user_data.get("is_active", True) if is_edit else True,
        )

        error_text = ft.Text("", color=COLOR_ERROR, size=12, visible=False)

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def submit_user(e):
            n = name_input.value.strip()
            if not n:
                error_text.value = "Full name is required"
                error_text.visible = True
                self.page.update()
                return

            if not is_edit:
                em = email_input.value.strip()
                pwd = password_input.value
                if not em or not pwd:
                    error_text.value = "Email and password are required"
                    error_text.visible = True
                    self.page.update()
                    return
                if len(pwd) < 8:
                    error_text.value = "Password must be at least 8 characters"
                    error_text.visible = True
                    self.page.update()
                    return

                try:
                    user_client.create_user(
                        {
                            "email": em,
                            "full_name": n,
                            "password": pwd,
                            "role": role_dropdown.value,
                            "is_active": active_switch.value,
                        }
                    )
                    self._show_toast("User account created.")
                    close_dialog(None)
                    self.load_users()
                except ApiClientException as ex:
                    error_text.value = ex.message
                    error_text.visible = True
                    self.page.update()
            else:
                payload = {
                    "full_name": n,
                    "role": role_dropdown.value,
                    "is_active": active_switch.value,
                }
                if password_input.value and len(password_input.value) >= 8:
                    payload["password"] = password_input.value

                try:
                    user_client.update_user(user_data["id"], payload)
                    self._show_toast("User account updated.")
                    close_dialog(None)
                    self.load_users()
                except ApiClientException as ex:
                    error_text.value = ex.message
                    error_text.visible = True
                    self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Edit User" if is_edit else "Create Institutional User",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        error_text,
                        email_input,
                        name_input,
                        role_dropdown,
                        password_input,
                        active_switch,
                    ],
                    spacing=12,
                    tight=True,
                ),
                width=460,
            ),
            actions=[
                ft.OutlinedButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Save Account", bgcolor=COLOR_PRIMARY_NAVY, color="white", on_click=submit_user
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _build_view(self) -> ft.Column:
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "User & Role Management",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Administrator-only access tier: manage accounts, role assignments, and active states.",
                            size=12,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Add User",
                            icon=ft.Icons.PERSON_ADD,
                            bgcolor=COLOR_PRIMARY_NAVY,
                            color="white",
                            on_click=lambda e: self._open_user_modal(),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Refresh users",
                            on_click=lambda e: self.load_users(),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        table_rows = []
        for u in self.users:
            email = u.get("email", "")
            name = u.get("full_name", "")
            active = u.get("is_active", True)
            last_login = u.get("last_login_at")
            last_login_str = last_login[:19].replace("T", " ") if last_login else "Never logged in"

            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                name, size=13, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY
                            )
                        ),
                        ft.DataCell(ft.Text(email, size=12)),
                        ft.DataCell(status_badge(u.get("role", "viewer"))),
                        ft.DataCell(status_badge("ACTIVE" if active else "DEACTIVATED")),
                        ft.DataCell(ft.Text(last_login_str, size=11, color=COLOR_TEXT_SECONDARY)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_size=18,
                                tooltip="Edit account or change role",
                                on_click=lambda e, user_row=u: self._open_user_modal(user_row),
                            )
                        ),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text(
                        "FULL NAME", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "EMAIL / USERNAME",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "ROLE TIER", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "STATUS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "LAST LOGIN", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "ACTION", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
            ],
            rows=table_rows,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_height=42,
            data_row_min_height=48,
            data_row_max_height=56,
        )

        return ft.Column(
            controls=[
                header,
                ft.Container(height=12),
                ft.Container(
                    content=data_table
                    if self.users
                    else empty_state(
                        "No users found", "Create institutional accounts for lab staff."
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
