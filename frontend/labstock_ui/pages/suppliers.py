from typing import Any

import flet as ft

from frontend.labstock_ui.api import supplier_client
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
from frontend.labstock_ui.state.session import session


class SuppliersPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.suppliers: list = []
        self.content = loading_state("Loading suppliers directory...")
        self.load_suppliers()

    def load_suppliers(self):
        try:
            res = supplier_client.list_suppliers(page_size=100)
            self.suppliers = res.get("items", [])
            self.content = self._build_view()
        except ApiClientException as e:
            self.content = empty_state("Error", e.message, ft.Icons.ERROR_OUTLINE)
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

    def _open_supplier_modal(self, sup: dict[str, Any] | None = None):
        is_edit = sup is not None
        name_input = ft.TextField(
            label="Supplier / Vendor Name *",
            value=sup.get("name", "") if is_edit else "",
            height=44,
            text_size=13,
        )
        contact_input = ft.TextField(
            label="Contact Person",
            value=sup.get("contact_person", "") if is_edit else "",
            height=44,
            text_size=13,
        )
        email_input = ft.TextField(
            label="Email Address",
            value=sup.get("email", "") if is_edit else "",
            height=44,
            text_size=13,
        )
        phone_input = ft.TextField(
            label="Phone Number",
            value=sup.get("phone", "") if is_edit else "",
            height=44,
            text_size=13,
        )
        address_input = ft.TextField(
            label="Address / Office",
            value=sup.get("address", "") if is_edit else "",
            height=44,
            text_size=13,
        )
        notes_input = ft.TextField(
            label="Notes & Special Terms",
            value=sup.get("notes", "") if is_edit else "",
            multiline=True,
            min_lines=2,
            text_size=13,
        )
        active_switch = ft.Switch(
            label="Active Supplier",
            value=sup.get("is_active", True) if is_edit else True,
        )

        error_text = ft.Text("", color=COLOR_ERROR, size=12, visible=False)

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def submit_supplier(e):
            n = name_input.value.strip()
            if not n:
                error_text.value = "Supplier name is required"
                error_text.visible = True
                self.page.update()
                return

            payload = {
                "name": n,
                "contact_person": contact_input.value.strip() if contact_input.value else None,
                "email": email_input.value.strip() if email_input.value else None,
                "phone": phone_input.value.strip() if phone_input.value else None,
                "address": address_input.value.strip() if address_input.value else None,
                "notes": notes_input.value.strip() if notes_input.value else None,
                "is_active": active_switch.value,
            }

            try:
                if is_edit:
                    supplier_client.update_supplier(sup["id"], payload)
                    self._show_toast("Supplier details updated.")
                else:
                    supplier_client.create_supplier(payload)
                    self._show_toast("New supplier registered.")
                close_dialog(None)
                self.load_suppliers()
            except ApiClientException as ex:
                error_text.value = ex.message
                error_text.visible = True
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Edit Supplier" if is_edit else "Register New Supplier",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        error_text,
                        name_input,
                        ft.Row(controls=[contact_input, phone_input], spacing=10),
                        email_input,
                        address_input,
                        notes_input,
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
                    "Save Supplier",
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    on_click=submit_supplier,
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
                            "Supplier & Vendor Management",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Manage hardware vendors, parts distributors, and procurement contacts.",
                            size=12,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Add Supplier",
                            icon=ft.Icons.ADD_BUSINESS,
                            bgcolor=COLOR_PRIMARY_NAVY,
                            color="white",
                            on_click=lambda e: self._open_supplier_modal(),
                            visible=session.is_manager,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Refresh suppliers",
                            on_click=lambda e: self.load_suppliers(),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        table_rows = []
        for s in self.suppliers:
            name = s.get("name", "")
            contact = s.get("contact_person") or "—"
            email = s.get("email") or "—"
            phone = s.get("phone") or "—"
            addr = s.get("address") or "—"
            active = s.get("is_active", True)

            actions = []
            if session.is_manager:
                actions.append(
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_size=18,
                        tooltip="Edit supplier details",
                        on_click=lambda e, sup_data=s: self._open_supplier_modal(sup_data),
                    )
                )

            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                name, size=13, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY
                            )
                        ),
                        ft.DataCell(ft.Text(contact, size=12)),
                        ft.DataCell(ft.Text(email, size=12)),
                        ft.DataCell(ft.Text(phone, size=12, font_family="monospace")),
                        ft.DataCell(ft.Text(addr, size=12, color=COLOR_TEXT_SECONDARY)),
                        ft.DataCell(status_badge("ACTIVE" if active else "DEACTIVATED")),
                        ft.DataCell(ft.Row(controls=actions, spacing=2, tight=True)),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text(
                        "SUPPLIER NAME",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "CONTACT PERSON",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text("EMAIL", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text("PHONE", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text(
                        "ADDRESS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "STATUS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "ACTIONS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
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
                    if self.suppliers
                    else empty_state(
                        "No suppliers registered",
                        "Register your vendors to link with catalog items and purchase requests.",
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
