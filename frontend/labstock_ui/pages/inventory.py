import flet as ft

from frontend.labstock_ui.api import inventory_client, report_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.confirmation_dialog import show_confirmation_dialog
from frontend.labstock_ui.components.empty_state import empty_state
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.components.status_badge import sku_chip, status_badge
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_DARK_GREEN,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.navigation import navigation
from frontend.labstock_ui.state.session import session


class InventoryPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)

        # State
        self.current_page = 1
        self.page_size = 15
        self.search_query = ""
        self.selected_category = "All"
        self.selected_status = "All"
        self.is_active_filter = True

        self.content = loading_state("Loading inventory catalog...")
        self.load_inventory()

    def load_inventory(self):
        try:
            res = inventory_client.list_items(
                query=self.search_query if self.search_query else None,
                category=self.selected_category if self.selected_category != "All" else None,
                status=self.selected_status if self.selected_status != "All" else None,
                page=self.current_page,
                page_size=self.page_size,
                is_active=self.is_active_filter,
            )
            items = res.get("items", [])
            meta = res.get("meta", {})
            self.content = self._build_view(items, meta)
        except ApiClientException as e:
            self.content = empty_state(
                title="Error loading inventory",
                message=e.message,
                icon=ft.Icons.ERROR_OUTLINE,
                action_label="Retry",
                on_action=lambda e: self.load_inventory(),
            )
        except Exception as e:
            self.content = empty_state(
                title="Connection Error",
                message=str(e),
                icon=ft.Icons.WIFI_OFF,
                action_label="Retry",
                on_action=lambda e: self.load_inventory(),
            )
        self.page.update()

    def _export_csv(self):
        try:
            csv_text = report_client.download_report_csv("current_stock")
            # Show dialog with CSV download confirmation / preview
            dialog = ft.AlertDialog(
                title=ft.Text("CSV Export Ready", size=16, weight=ft.FontWeight.BOLD),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Sanitized CSV stream generated with formula-injection prevention:",
                            size=13,
                        ),
                        ft.TextField(
                            value=csv_text[:600]
                            + ("\n... [truncated for display]" if len(csv_text) > 600 else ""),
                            multiline=True,
                            min_lines=6,
                            max_lines=10,
                            read_only=True,
                            text_size=11,
                            text_style=ft.TextStyle(font_family="monospace"),
                        ),
                    ],
                    tight=True,
                    width=500,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog)),
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
        except Exception as e:
            self._show_toast(f"Export error: {e}", is_error=True)

    def _close_dialog(self, dlg):
        dlg.open = False
        self.page.update()

    def _show_toast(self, message: str, is_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor="#DC3545" if is_error else COLOR_PRIMARY_NAVY,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _confirm_deactivate(self, item_id: int, item_name: str):
        show_confirmation_dialog(
            page=self.page,
            title="Deactivate Inventory Item?",
            message=f"Are you sure you want to deactivate '{item_name}'? The item will be hidden from daily operations, but all historical movements remain preserved.",
            confirm_label="Deactivate",
            is_destructive=True,
            on_confirm=lambda: self._do_deactivate(item_id),
        )

    def _do_deactivate(self, item_id: int):
        try:
            inventory_client.deactivate_item(item_id)
            self._show_toast("Item successfully deactivated.")
            self.load_inventory()
        except Exception as e:
            self._show_toast(f"Failed to deactivate: {e}", is_error=True)

    def _confirm_activate(self, item_id: int):
        try:
            inventory_client.activate_item(item_id)
            self._show_toast("Item successfully reactivated.")
            self.load_inventory()
        except Exception as e:
            self._show_toast(f"Failed to reactivate: {e}", is_error=True)

    def _build_view(self, items: list, meta: dict) -> ft.Column:
        # Search & Action Bar
        search_field = ft.TextField(
            hint_text="Search SKU, item name, category, or bin location...",
            value=self.search_query,
            prefix_icon=ft.Icons.SEARCH,
            height=42,
            text_size=13,
            expand=True,
            border_color=COLOR_BORDER,
            on_submit=lambda e: self._handle_search(e.control.value),
        )

        category_dropdown = ft.Dropdown(
            label="Category",
            value=self.selected_category,
            height=42,
            text_size=12,
            width=180,
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Electronics"),
                ft.dropdown.Option("Sensors"),
                ft.dropdown.Option("Microcontrollers"),
                ft.dropdown.Option("Single Board Computers"),
                ft.dropdown.Option("Semiconductors"),
                ft.dropdown.Option("Passive Components"),
                ft.dropdown.Option("Motors"),
                ft.dropdown.Option("Tools"),
            ],
            on_change=lambda e: self._handle_category_change(e.control.value),
        )

        status_dropdown = ft.Dropdown(
            label="Stock Status",
            value=self.selected_status,
            height=42,
            text_size=12,
            width=160,
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("in_stock", "In Stock"),
                ft.dropdown.Option("low_stock", "Low Stock"),
                ft.dropdown.Option("out_of_stock", "Out of Stock"),
            ],
            on_change=lambda e: self._handle_status_change(e.control.value),
        )

        action_buttons = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="Add Item",
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    height=40,
                    on_click=lambda e: navigation.navigate("item_form"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text="Export CSV",
                    icon=ft.Icons.DOWNLOAD_OUTLINED,
                    height=40,
                    on_click=lambda e: self._export_csv(),
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh inventory",
                    on_click=lambda e: self.load_inventory(),
                ),
            ],
            spacing=8,
        )

        controls_row = ft.Row(
            controls=[
                search_field,
                category_dropdown,
                status_dropdown,
                action_buttons,
            ],
            spacing=10,
        )

        # Table rows
        table_rows = []
        for it in items:
            item_id = it.get("id")
            sku = it.get("sku", "")
            name = it.get("name", "")
            category = it.get("category", "")
            loc = it.get("storage_location", "")
            unit = it.get("unit", "pcs")
            balance = it.get("balance") or {}
            qoh = balance.get("quantity_on_hand", 0.0)
            avail = balance.get("available_to_issue", 0.0)
            min_thresh = it.get("min_stock_threshold", 0.0)
            st_status = it.get("stock_status", "IN_STOCK")
            is_active = it.get("is_active", True)

            # Row actions
            actions = [
                ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_size=17,
                    tooltip="Details & Movement History",
                    on_click=lambda e, i=item_id: navigation.navigate(
                        "item_details", {"item_id": i}
                    ),
                ),
            ]
            if session.is_manager:
                actions.append(
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_size=17,
                        tooltip="Edit metadata",
                        on_click=lambda e, i=item_id: navigation.navigate(
                            "item_form", {"item_id": i}
                        ),
                    )
                )
                if is_active:
                    actions.append(
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=17,
                            tooltip="Deactivate item",
                            icon_color="#DC3545",
                            on_click=lambda e, i=item_id, n=name: self._confirm_deactivate(i, n),
                        )
                    )
                else:
                    actions.append(
                        ft.IconButton(
                            icon=ft.Icons.RESTORE_ROUNDED,
                            icon_size=17,
                            tooltip="Reactivate item",
                            icon_color=COLOR_DARK_GREEN,
                            on_click=lambda e, i=item_id: self._confirm_activate(i),
                        )
                    )

            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(sku_chip(sku)),
                        ft.DataCell(
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        name,
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=COLOR_TEXT_PRIMARY,
                                    ),
                                    ft.Text(category, size=11, color=COLOR_TEXT_SECONDARY),
                                ],
                                spacing=1,
                                tight=True,
                            )
                        ),
                        ft.DataCell(ft.Text(loc, size=12)),
                        ft.DataCell(
                            ft.Text(
                                f"{qoh:g} {unit}",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(ft.Text(f"{avail:g}", size=12, font_family="monospace")),
                        ft.DataCell(
                            ft.Text(
                                f"{min_thresh:g}",
                                size=12,
                                color=COLOR_TEXT_SECONDARY,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(status_badge(st_status if is_active else "DEACTIVATED")),
                        ft.DataCell(ft.Row(controls=actions, spacing=2, tight=True)),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text("SKU", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text(
                        "ITEM / CATEGORY",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "LOCATION", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "ON HAND", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "AVAILABLE", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "MIN THRESH", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
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
            heading_row_color="#F8FAFC",
            heading_row_height=40,
            data_row_min_height=44,
            data_row_max_height=52,
        )

        # Pagination controls
        total_items = meta.get("total", 0)
        total_pages = meta.get("total_pages", 1)
        current_page = meta.get("page", 1)

        pagination_row = ft.Row(
            controls=[
                ft.Text(
                    f"Showing {len(items)} of {total_items} items (Page {current_page} of {total_pages})",
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
                controls_row,
                ft.Container(height=4),
                ft.Container(
                    content=data_table
                    if items
                    else empty_state(
                        "No items match query", "Try adjusting your search or category filter."
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

    def _handle_search(self, query: str):
        self.search_query = query.strip()
        self.current_page = 1
        self.load_inventory()

    def _handle_category_change(self, cat: str):
        self.selected_category = cat
        self.current_page = 1
        self.load_inventory()

    def _handle_status_change(self, st: str):
        self.selected_status = st
        self.current_page = 1
        self.load_inventory()

    def _change_page(self, page: int):
        self.current_page = page
        self.load_inventory()
