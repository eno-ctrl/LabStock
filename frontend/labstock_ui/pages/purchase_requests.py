from typing import Any

import flet as ft

from frontend.labstock_ui.api import inventory_client, procurement_client, supplier_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.empty_state import empty_state
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.components.status_badge import sku_chip, status_badge
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_DARK_GREEN,
    COLOR_ERROR,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.session import session


class PurchaseRequestsPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.requests: list = []
        self.catalog_items: list = []
        self.suppliers_list: list = []
        self.status_filter = "All"
        self.current_page = 1
        self.page_size = 20

        self.content = loading_state("Loading purchase requests...")
        self.load_data()

    def load_data(self):
        try:
            sup_res = supplier_client.list_suppliers(page_size=100)
            self.suppliers_list = sup_res.get("items", [])
            it_res = inventory_client.list_items(page_size=100, is_active=True)
            self.catalog_items = it_res.get("items", [])

            pr_res = procurement_client.list_purchase_requests(
                status=self.status_filter if self.status_filter != "All" else None,
                page=self.current_page,
                page_size=self.page_size,
            )
            self.requests = pr_res.get("items", [])
            meta = pr_res.get("meta", {})
            self.content = self._build_view(meta)
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

    def _open_create_modal(self):
        sup_options = [ft.dropdown.Option("None", "No Specific Supplier")]
        for s in self.suppliers_list:
            sup_options.append(ft.dropdown.Option(str(s["id"]), s["name"]))

        item_options = [
            ft.dropdown.Option(str(it["id"]), f"{it['sku']} — {it['name']}")
            for it in self.catalog_items
        ]

        sup_dropdown = ft.Dropdown(
            label="Supplier / Vendor",
            options=sup_options,
            value=sup_options[0].key,
            height=44,
            text_size=12,
        )

        item_dropdown = ft.Dropdown(
            label="Item to Replenish *",
            options=item_options,
            value=item_options[0].key if item_options else None,
            height=44,
            text_size=12,
        )

        qty_input = ft.TextField(
            label="Requested Quantity *",
            hint_text="e.g. 50",
            height=44,
            text_size=13,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        cost_input = ft.TextField(
            label="Estimated Unit Cost ($ / ₹)",
            hint_text="Optional unit price",
            height=44,
            text_size=13,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        notes_input = ft.TextField(
            label="Justification & Purpose",
            hint_text="e.g. Replenishment for Spring Mechatronics Laboratory Course",
            multiline=True,
            min_lines=2,
            text_size=13,
        )

        error_text = ft.Text("", color=COLOR_ERROR, size=12, visible=False)

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def submit_pr(e):
            if not item_dropdown.value:
                error_text.value = "Please select an item"
                error_text.visible = True
                self.page.update()
                return

            try:
                q = float(qty_input.value)
                if q <= 0:
                    raise ValueError()
            except Exception:
                error_text.value = "Quantity must be a positive number greater than 0"
                error_text.visible = True
                self.page.update()
                return

            cost = float(cost_input.value) if cost_input.value else None
            sup_id = (
                int(sup_dropdown.value)
                if sup_dropdown.value and sup_dropdown.value != "None"
                else None
            )

            payload = {
                "supplier_id": sup_id,
                "notes": notes_input.value.strip() if notes_input.value else None,
                "lines": [
                    {
                        "item_id": int(item_dropdown.value),
                        "requested_quantity": q,
                        "unit_cost": cost,
                    }
                ],
            }

            try:
                procurement_client.create_purchase_request(payload)
                self._show_toast("Purchase Request draft created.")
                close_dialog(None)
                self.load_data()
            except ApiClientException as ex:
                error_text.value = ex.message
                error_text.visible = True
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("New Purchase Request", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        error_text,
                        sup_dropdown,
                        item_dropdown,
                        ft.Row(controls=[qty_input, cost_input], spacing=10),
                        notes_input,
                    ],
                    spacing=12,
                    tight=True,
                ),
                width=460,
            ),
            actions=[
                ft.OutlinedButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Create Draft PR", bgcolor=COLOR_PRIMARY_NAVY, color="white", on_click=submit_pr
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _open_inspect_modal(self, pr: dict[str, Any]):
        pr_id = pr.get("id")
        req_num = pr.get("request_number", "")
        pr_status = pr.get("status", "draft")
        lines = pr.get("lines", [])

        line_cells = []
        for line in lines:
            rem = max(0.0, line.get("ordered_quantity", 0) - line.get("received_quantity", 0))
            line_cells.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(sku_chip(line.get("item_sku", ""))),
                        ft.DataCell(ft.Text(line.get("item_name", ""), size=12)),
                        ft.DataCell(
                            ft.Text(
                                f"{line.get('requested_quantity', 0):g}",
                                size=12,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{line.get('ordered_quantity', 0):g}",
                                size=12,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{line.get('received_quantity', 0):g}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(ft.Text(f"{rem:g}", size=12, font_family="monospace")),
                    ]
                )
            )

        lines_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("SKU", size=11, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ITEM", size=11, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("REQUESTED", size=11, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("ORDERED", size=11, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("RECEIVED", size=11, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("OUTSTANDING", size=11, weight=ft.FontWeight.BOLD)),
            ],
            rows=line_cells,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_height=36,
        )

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        def do_action(action_fn, success_msg: str):
            try:
                action_fn(pr_id)
                self._show_toast(success_msg)
                close_dialog(None)
                self.load_data()
            except Exception as ex:
                self._show_toast(str(ex), is_error=True)

        action_buttons = [ft.OutlinedButton("Close", on_click=close_dialog)]

        if pr_status == "draft" and session.is_manager:
            action_buttons.append(
                ft.ElevatedButton(
                    "Submit for Approval",
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    on_click=lambda e: do_action(
                        procurement_client.submit_request, "Request submitted."
                    ),
                )
            )
        elif pr_status == "submitted" and session.is_admin:
            action_buttons.append(
                ft.ElevatedButton(
                    "Approve Purchase Request",
                    bgcolor=COLOR_DARK_GREEN,
                    color="white",
                    on_click=lambda e: do_action(
                        procurement_client.approve_request, "Request approved."
                    ),
                )
            )
        elif pr_status == "approved" and session.is_manager:
            action_buttons.append(
                ft.ElevatedButton(
                    "Mark PO Placed (Ordered)",
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    on_click=lambda e: do_action(
                        procurement_client.order_request, "Request marked ordered."
                    ),
                )
            )
        elif pr_status in ("ordered", "partially_received") and session.is_manager:
            action_buttons.append(
                ft.ElevatedButton(
                    "Receive Physical Stock...",
                    bgcolor=COLOR_DARK_GREEN,
                    color="white",
                    icon=ft.Icons.MOVE_TO_INBOX,
                    on_click=lambda e: self._open_receive_modal(pr, close_dialog),
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Text(f"Request #{req_num}", size=16, weight=ft.FontWeight.BOLD),
                    status_badge(pr_status),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Notes: {pr.get('notes') or 'None'}",
                            size=13,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                        ft.Container(height=4),
                        lines_table,
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=580,
            ),
            actions=action_buttons,
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _open_receive_modal(self, pr: dict[str, Any], parent_close_fn):
        pr_id = pr.get("id")
        lines = pr.get("lines", [])
        if not lines:
            return

        parent_close_fn(None)

        receive_inputs = []
        for line in lines:
            rem = max(0.0, line.get("ordered_quantity", 0) - line.get("received_quantity", 0))
            tf = ft.TextField(
                label=f"Receive qty for {line.get('item_sku')} (Ordered: {line.get('ordered_quantity'):g}, Outstanding: {rem:g})",
                value=str(rem),
                height=44,
                text_size=13,
                keyboard_type=ft.KeyboardType.NUMBER,
            )
            receive_inputs.append((line["id"], tf, rem))

        ref_input = ft.TextField(
            label="Delivery / Invoice Reference",
            hint_text="e.g. Delivery Challan #DC-9921",
            height=44,
            text_size=13,
        )

        err_text = ft.Text("", color=COLOR_ERROR, size=12, visible=False)

        def close_recv_dialog(e):
            recv_dialog.open = False
            self.page.update()

        def submit_physical_receipt(e):
            payload_items = []
            for line_id, tf, rem in receive_inputs:
                try:
                    qty = float(tf.value or 0.0)
                except ValueError:
                    qty = 0.0
                if qty > 0:
                    if qty > rem:
                        err_text.value = (
                            f"Cannot receive {qty:g} units; only {rem:g} outstanding on order."
                        )
                        err_text.visible = True
                        self.page.update()
                        return
                    payload_items.append({"line_id": line_id, "quantity_to_receive": qty})

            if not payload_items:
                err_text.value = "Please enter quantity to receive for at least one line"
                err_text.visible = True
                self.page.update()
                return

            try:
                procurement_client.receive_purchase_request_stock(
                    pr_id,
                    {
                        "items": payload_items,
                        "reference": ref_input.value.strip() if ref_input.value else None,
                    },
                )
                self._show_toast("Stock received and catalog balance updated atomically.")
                close_recv_dialog(None)
                self.load_data()
            except ApiClientException as ex:
                err_text.value = ex.message
                err_text.visible = True
                self.page.update()

        recv_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Receive Stock for {pr.get('request_number')}", size=16, weight=ft.FontWeight.BOLD
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        err_text,
                        ft.Text(
                            "Enter verified physical units delivered. Stock will be credited immediately to inventory:",
                            size=12,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                        *[tf for _, tf, _ in receive_inputs],
                        ref_input,
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=500,
            ),
            actions=[
                ft.OutlinedButton("Cancel", on_click=close_recv_dialog),
                ft.ElevatedButton(
                    "Record Receipt",
                    bgcolor=COLOR_DARK_GREEN,
                    color="white",
                    on_click=submit_physical_receipt,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(recv_dialog)
        recv_dialog.open = True
        self.page.update()

    def _build_view(self, meta: dict) -> ft.Column:
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "Purchase Requests & Orders",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Control the procurement lifecycle: Draft → Submitted → Approved → Ordered → Received.",
                            size=12,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="New Request",
                            icon=ft.Icons.ADD_SHOPPING_CART,
                            bgcolor=COLOR_PRIMARY_NAVY,
                            color="white",
                            height=40,
                            on_click=lambda e: self._open_create_modal(),
                            visible=session.is_manager,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Refresh requests",
                            on_click=lambda e: self.load_data(),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        status_dropdown = ft.Dropdown(
            label="Filter by Status",
            value=self.status_filter,
            height=40,
            text_size=12,
            width=200,
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("draft", "Draft"),
                ft.dropdown.Option("submitted", "Submitted"),
                ft.dropdown.Option("approved", "Approved"),
                ft.dropdown.Option("ordered", "Ordered"),
                ft.dropdown.Option("partially_received", "Partially Received"),
                ft.dropdown.Option("received", "Received"),
                ft.dropdown.Option("cancelled", "Cancelled"),
            ],
            on_change=lambda e: self._on_filter_change(e.control.value),
        )

        table_rows = []
        for pr in self.requests:
            pr_num = pr.get("request_number", "")
            pr_status = pr.get("status", "draft")
            sup = pr.get("supplier") or {}
            sup_name = sup.get("name", "Unassigned")
            req_by = pr.get("requester") or {}
            req_name = req_by.get("full_name", "Staff")
            lines_count = len(pr.get("lines", []))
            date_str = pr.get("created_at", "")[:10]

            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                pr_num, size=12, weight=ft.FontWeight.BOLD, font_family="monospace"
                            )
                        ),
                        ft.DataCell(status_badge(pr_status)),
                        ft.DataCell(ft.Text(sup_name, size=12)),
                        ft.DataCell(
                            ft.Text(f"{lines_count} item(s)", size=12, font_family="monospace")
                        ),
                        ft.DataCell(ft.Text(req_name, size=12, color=COLOR_TEXT_SECONDARY)),
                        ft.DataCell(ft.Text(date_str, size=12, color=COLOR_TEXT_SECONDARY)),
                        ft.DataCell(
                            ft.ElevatedButton(
                                text="Inspect",
                                height=28,
                                on_click=lambda e, r=pr: self._open_inspect_modal(r),
                            )
                        ),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text(
                        "REQUEST #", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "STATUS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "SUPPLIER", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "LINE ITEMS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "REQUESTED BY",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text("DATE", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
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
                ft.Container(height=4),
                ft.Row(controls=[status_dropdown]),
                ft.Container(height=4),
                ft.Container(
                    content=data_table
                    if self.requests
                    else empty_state(
                        "No purchase requests found",
                        "Create a purchase request to replenish laboratory stock.",
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _on_filter_change(self, val: str):
        self.status_filter = val
        self.current_page = 1
        self.load_data()
