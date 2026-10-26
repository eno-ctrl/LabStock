import uuid

import flet as ft

from frontend.labstock_ui.api import inventory_client, movement_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.empty_state import empty_state
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.components.status_badge import sku_chip, status_badge
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_ERROR,
    COLOR_PRIMARY_NAVY,
    COLOR_SECONDARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.session import session


class StockMovementsPage(ft.Container):
    def __init__(self, page: ft.Page, default_item_id: int | None = None):
        super().__init__()
        self.page = page
        self.default_item_id = default_item_id
        self.expand = True
        self.padding = ft.Padding.all(24)

        # Filters
        self.selected_type = "All"
        self.search_query = ""
        self.current_page = 1
        self.page_size = 20

        self.items_catalog: list = []
        self.content = loading_state("Loading stock movements ledger...")
        self.load_catalog_and_movements()

    def load_catalog_and_movements(self):
        try:
            it_res = inventory_client.list_items(page_size=100, is_active=True)
            self.items_catalog = it_res.get("items", [])
            self.load_movements()
        except Exception as e:
            self.content = ft.Text(f"Failed to load catalog: {e}", color=COLOR_ERROR)
            self.page.update()

    def load_movements(self):
        try:
            mov_res = movement_client.list_movements(
                movement_type=self.selected_type if self.selected_type != "All" else None,
                query=self.search_query if self.search_query else None,
                item_id=self.default_item_id,
                page=self.current_page,
                page_size=self.page_size,
            )
            movements = mov_res.get("items", [])
            meta = mov_res.get("meta", {})
            self.content = self._build_view(movements, meta)
        except ApiClientException as e:
            self.content = empty_state("Error", e.message, ft.Icons.ERROR_OUTLINE)
        except Exception as e:
            self.content = empty_state("Error", str(e), ft.Icons.ERROR_OUTLINE)
        self.page.update()

    def _show_toast(self, message: str, is_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor="#DC3545" if is_error else COLOR_PRIMARY_NAVY,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _open_action_modal(self, action_type: str):
        """Dedicated transactional modal dialog for Receipt, Issue, Return, Damage, or Adjustment."""
        item_options = [
            ft.dropdown.Option(
                str(it["id"]),
                f"{it['sku']} — {it['name']} (On hand: {it.get('balance', {}).get('quantity_on_hand', 0):g})",
            )
            for it in self.items_catalog
        ]

        def_val = (
            str(self.default_item_id)
            if self.default_item_id
            else (item_options[0].key if item_options else None)
        )

        item_dropdown = ft.Dropdown(
            label="Catalog Item *",
            options=item_options,
            value=def_val,
            height=44,
            text_size=12,
        )

        qty_input = ft.TextField(
            label="Quantity *",
            hint_text="Positive number greater than zero",
            height=44,
            text_size=13,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        recipient_input = ft.TextField(
            label="Recipient / Student / Project Name *",
            hint_text="e.g. Maya Lin (Student ID #4829) / Autonomous Rover Project",
            height=44,
            text_size=13,
            visible=(action_type == "issue"),
        )

        reason_input = ft.TextField(
            label="Reason / Audit Explanation *"
            if action_type in ("damage", "adjust")
            else "Reference / Notes",
            hint_text="Mandatory explanation for audit trail",
            multiline=True,
            min_lines=2,
            text_size=13,
        )

        direction_radio = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="INCREASE", label="Physical count is higher (Increase Stock)"),
                    ft.Radio(value="DECREASE", label="Physical count is lower (Decrease Stock)"),
                ],
                spacing=16,
            ),
            value="INCREASE",
            visible=(action_type == "adjust"),
        )

        error_text = ft.Text("", color=COLOR_ERROR, size=12, visible=False)

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def submit_transaction(e):
            if not item_dropdown.value:
                error_text.value = "Please select an item"
                error_text.visible = True
                self.page.update()
                return

            try:
                qty = float(qty_input.value)
                if qty <= 0:
                    raise ValueError()
            except Exception:
                error_text.value = "Please enter a valid positive quantity greater than 0"
                error_text.visible = True
                self.page.update()
                return

            item_id = int(item_dropdown.value)
            reason = reason_input.value.strip() if reason_input.value else None
            idemp_key = f"ui_{uuid.uuid4().hex}"

            try:
                if action_type == "receipt":
                    movement_client.receive_stock(
                        {
                            "item_id": item_id,
                            "quantity": qty,
                            "reason": reason,
                            "idempotency_key": idemp_key,
                        }
                    )
                    self._show_toast("Stock received and balance updated.")
                elif action_type == "issue":
                    recip = recipient_input.value.strip()
                    if not recip:
                        error_text.value = "Recipient / Project is required for stock issue"
                        error_text.visible = True
                        self.page.update()
                        return
                    movement_client.issue_stock(
                        {
                            "item_id": item_id,
                            "quantity": qty,
                            "recipient_project": recip,
                            "reason": reason,
                            "idempotency_key": idemp_key,
                        }
                    )
                    self._show_toast("Stock issued successfully.")
                elif action_type == "return":
                    movement_client.return_stock(
                        {
                            "item_id": item_id,
                            "quantity": qty,
                            "reason": reason or "Returned component",
                            "idempotency_key": idemp_key,
                        }
                    )
                    self._show_toast("Stock return recorded.")
                elif action_type == "damage":
                    if not reason or len(reason) < 3:
                        error_text.value = "Mandatory explanation required for damage write-off"
                        error_text.visible = True
                        self.page.update()
                        return
                    movement_client.record_damage(
                        {
                            "item_id": item_id,
                            "quantity": qty,
                            "reason": reason,
                            "idempotency_key": idemp_key,
                        }
                    )
                    self._show_toast("Damage write-off completed.")
                elif action_type == "adjust":
                    if not reason or len(reason) < 5:
                        error_text.value = "Detailed explanation required for stock adjustment"
                        error_text.visible = True
                        self.page.update()
                        return
                    movement_client.adjust_stock(
                        {
                            "item_id": item_id,
                            "quantity": qty,
                            "direction": direction_radio.value,
                            "reason": reason,
                            "idempotency_key": idemp_key,
                        }
                    )
                    self._show_toast("Stock adjustment recorded in audit ledger.")

                close_dialog(None)
                self.load_catalog_and_movements()
            except ApiClientException as ex:
                error_text.value = ex.message
                error_text.visible = True
                self.page.update()

        action_titles = {
            "receipt": "Receive Stock (Stock In)",
            "issue": "Issue Stock (Stock Out)",
            "return": "Return Stock (Return to Shelf)",
            "damage": "Record Damage / Write-off (Stock Out)",
            "adjust": "Authorized Stock Adjustment (Reconciliation)",
        }

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                action_titles.get(action_type, "Stock Transaction"),
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        error_text,
                        item_dropdown,
                        direction_radio if action_type == "adjust" else ft.Container(),
                        qty_input,
                        recipient_input if action_type == "issue" else ft.Container(),
                        reason_input,
                    ],
                    spacing=12,
                    tight=True,
                ),
                width=480,
            ),
            actions=[
                ft.OutlinedButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Submit Transaction",
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    on_click=submit_transaction,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _build_view(self, movements: list, meta: dict) -> ft.Column:
        # Top Transaction Trigger Buttons
        action_strip = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="Receive Stock",
                    icon=ft.Icons.MOVE_TO_INBOX_OUTLINED,
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    height=40,
                    on_click=lambda e: self._open_action_modal("receipt"),
                    visible=session.is_manager,
                ),
                ft.ElevatedButton(
                    text="Issue Stock",
                    icon=ft.Icons.OUTBOX_OUTLINED,
                    bgcolor=COLOR_SECONDARY_NAVY,
                    color="white",
                    height=40,
                    on_click=lambda e: self._open_action_modal("issue"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text="Return Stock",
                    icon=ft.Icons.KEYBOARD_RETURN_ROUNDED,
                    height=40,
                    on_click=lambda e: self._open_action_modal("return"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text="Record Damage",
                    icon=ft.Icons.REPORT_PROBLEM_OUTLINED,
                    height=40,
                    on_click=lambda e: self._open_action_modal("damage"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text="Stock Adjustment",
                    icon=ft.Icons.TUNE_ROUNDED,
                    height=40,
                    on_click=lambda e: self._open_action_modal("adjust"),
                    visible=session.is_manager,
                ),
            ],
            spacing=10,
            wrap=True,
        )

        # Filters Bar
        search_field = ft.TextField(
            hint_text="Search SKU, recipient, or reference...",
            value=self.search_query,
            prefix_icon=ft.Icons.SEARCH,
            height=40,
            text_size=13,
            expand=True,
            border_color=COLOR_BORDER,
            on_submit=lambda e: self._handle_search(e.control.value),
        )

        type_dropdown = ft.Dropdown(
            label="Movement Type",
            value=self.selected_type,
            height=40,
            text_size=12,
            width=160,
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("receipt", "Receipt"),
                ft.dropdown.Option("issue", "Issue"),
                ft.dropdown.Option("return", "Return"),
                ft.dropdown.Option("damage", "Damage"),
                ft.dropdown.Option("adjustment", "Adjustment"),
                ft.dropdown.Option("reversal", "Reversal"),
            ],
            on_change=lambda e: self._handle_type_change(e.control.value),
        )

        filter_row = ft.Row(
            controls=[
                search_field,
                type_dropdown,
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh ledger",
                    on_click=lambda e: self.load_catalog_and_movements(),
                ),
            ],
            spacing=10,
        )

        # Table
        table_rows = []
        for m in movements:
            signed = m.get("signed_quantity", 0.0)
            sign_str = f"+{signed:g}" if signed > 0 else f"{signed:g}"
            sign_color = "#15803D" if signed > 0 else "#DC2626"

            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                m.get("timestamp", "")[:19].replace("T", " "),
                                size=11,
                                color=COLOR_TEXT_SECONDARY,
                            )
                        ),
                        ft.DataCell(sku_chip(m.get("item_sku", ""))),
                        ft.DataCell(
                            ft.Text(m.get("item_name", ""), size=12, weight=ft.FontWeight.W_500)
                        ),
                        ft.DataCell(status_badge(m.get("movement_type", ""))),
                        ft.DataCell(
                            ft.Text(
                                sign_str,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=sign_color,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{m.get('balance_after', 0):g}", size=12, font_family="monospace"
                            )
                        ),
                        ft.DataCell(ft.Text(m.get("recipient_project") or "—", size=12)),
                        ft.DataCell(
                            ft.Text(
                                m.get("reason") or m.get("reference_id") or "—",
                                size=11,
                                color=COLOR_TEXT_SECONDARY,
                            )
                        ),
                        ft.DataCell(ft.Text(m.get("actor_name") or "System", size=11)),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text(
                        "TIMESTAMP", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text("SKU", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text(
                        "ITEM NAME", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text("TYPE", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text(
                        "CHANGE", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "BALANCE AFTER",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "RECIPIENT / WORK REF",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "REASON / REFERENCE",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text("ACTOR", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
            ],
            rows=table_rows,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_color="#F8FAFC",
            heading_row_height=40,
            data_row_min_height=42,
            data_row_max_height=50,
        )

        total_items = meta.get("total", 0)
        total_pages = meta.get("total_pages", 1)
        current_page = meta.get("page", 1)

        pagination_row = ft.Row(
            controls=[
                ft.Text(
                    f"Showing {len(movements)} of {total_items} transactions (Page {current_page} of {total_pages})",
                    size=12,
                    color=COLOR_TEXT_SECONDARY,
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            text="Previous",
                            disabled=not meta.get("has_prev", False),
                            on_click=lambda e: self._change_page(current_page - 1),
                            height=32,
                        ),
                        ft.OutlinedButton(
                            text="Next",
                            disabled=not meta.get("has_next", False),
                            on_click=lambda e: self._change_page(current_page + 1),
                            height=32,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        return ft.Column(
            controls=[
                action_strip,
                ft.Container(height=4),
                filter_row,
                ft.Container(height=4),
                ft.Container(
                    content=data_table
                    if movements
                    else empty_state(
                        "No transactions found",
                        "Try clearing your filters or recording a movement.",
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
                ft.Container(height=4),
                pagination_row,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _handle_search(self, q: str):
        self.search_query = q.strip()
        self.current_page = 1
        self.load_movements()

    def _handle_type_change(self, t: str):
        self.selected_type = t
        self.current_page = 1
        self.load_movements()

    def _change_page(self, page: int):
        self.current_page = page
        self.load_movements()
