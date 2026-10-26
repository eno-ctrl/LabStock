import flet as ft

from frontend.labstock_ui.api import dashboard_client
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
    COLOR_WARNING,
)
from frontend.labstock_ui.state.navigation import navigation
from frontend.labstock_ui.state.session import session


class ReplenishmentPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.low_stock_items: list = []
        self.out_stock_items: list = []

        self.content = loading_state("Analyzing stock thresholds and replenishment needs...")
        self.load_data()

    def load_data(self):
        try:
            self.low_stock_items = dashboard_client.get_low_stock_replenishment()
            self.out_stock_items = dashboard_client.get_out_of_stock_replenishment()
            self.content = self._build_view()
        except ApiClientException as e:
            self.content = empty_state("Error", e.message, ft.Icons.ERROR_OUTLINE)
        except Exception as e:
            self.content = empty_state("Error", str(e), ft.Icons.ERROR_OUTLINE)
        self.page.update()

    def _create_quick_pr(self):
        """Creates a consolidated replenishment purchase request draft for all low and out of stock items."""
        if not self.low_stock_items and not self.out_stock_items:
            self._show_toast("No replenishment items required.")
            return

        navigation.navigate("purchase_requests")

    def _show_toast(self, msg: str):
        snack = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=COLOR_PRIMARY_NAVY)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _build_view(self) -> ft.Column:
        total_low = len(self.low_stock_items)
        total_out = len(self.out_stock_items)

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "Low Stock & Replenishment",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Track inventory deficits, reorder suggestions, and purchase requirements.",
                            size=12,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Create Purchase Request",
                            icon=ft.Icons.ADD_SHOPPING_CART,
                            bgcolor=COLOR_PRIMARY_NAVY,
                            color="white",
                            on_click=lambda e: navigation.navigate("purchase_requests"),
                            visible=session.is_manager,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Refresh replenishment data",
                            on_click=lambda e: self.load_data(),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Out of Stock Section
        out_table_rows = []
        for it in self.out_stock_items:
            out_table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(sku_chip(it.get("SKU", ""))),
                        ft.DataCell(
                            ft.Text(it.get("Item Name", ""), size=13, weight=ft.FontWeight.W_600)
                        ),
                        ft.DataCell(ft.Text(it.get("Category", ""), size=12)),
                        ft.DataCell(ft.Text(it.get("Storage Location", ""), size=12)),
                        ft.DataCell(
                            ft.Text(
                                f"{it.get('Min Threshold', 0):g}", size=12, font_family="monospace"
                            )
                        ),
                        ft.DataCell(status_badge("OUT_OF_STOCK")),
                        ft.DataCell(
                            ft.Text(it.get("Supplier", "N/A"), size=12, color=COLOR_TEXT_SECONDARY)
                        ),
                    ]
                )
            )

        out_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text("SKU", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text(
                        "ITEM NAME", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "CATEGORY", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "LOCATION", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "MIN REQUIRED",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "STATUS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "PREFERRED SUPPLIER",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
            ],
            rows=out_table_rows,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_color="#FEE2E2",
            heading_row_height=42,
            data_row_min_height=52,
            data_row_max_height=60,
        )

        # Low Stock Section
        low_table_rows = []
        for it in self.low_stock_items:
            low_table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(sku_chip(it.get("SKU", ""))),
                        ft.DataCell(
                            ft.Text(it.get("Item Name", ""), size=13, weight=ft.FontWeight.W_600)
                        ),
                        ft.DataCell(ft.Text(it.get("Category", ""), size=12)),
                        ft.DataCell(ft.Text(it.get("Storage Location", ""), size=12)),
                        ft.DataCell(
                            ft.Text(
                                f"{it.get('Quantity on Hand', 0):g}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{it.get('Min Threshold', 0):g}", size=12, font_family="monospace"
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                f"{it.get('Deficit', 0):g}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_WARNING,
                                font_family="monospace",
                            )
                        ),
                        ft.DataCell(status_badge("LOW_STOCK")),
                        ft.DataCell(
                            ft.Text(it.get("Supplier", "N/A"), size=12, color=COLOR_TEXT_SECONDARY)
                        ),
                    ]
                )
            )

        low_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text("SKU", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
                ),
                ft.DataColumn(
                    ft.Text(
                        "ITEM NAME", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "CATEGORY", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
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
                        "MIN THRESH", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "DEFICIT", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "STATUS", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "PREFERRED SUPPLIER",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
            ],
            rows=low_table_rows,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_color="#FEF3C7",
            heading_row_height=42,
            data_row_min_height=52,
            data_row_max_height=60,
        )

        return ft.Column(
            controls=[
                header,
                ft.Container(height=8),
                # Critical Section
                ft.Row(
                    controls=[
                        ft.Text(
                            "Critical Depletions (Out of Stock)",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_ERROR,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{total_out} items",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_ERROR,
                            ),
                            bgcolor="#FEE2E2",
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(
                    content=out_table
                    if self.out_stock_items
                    else ft.Container(
                        content=ft.Text(
                            "No catalog items are completely out of stock.",
                            size=13,
                            color=COLOR_DARK_GREEN,
                        ),
                        padding=16,
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
                ft.Container(height=12),
                # Low Stock Section
                ft.Row(
                    controls=[
                        ft.Text(
                            "Items Below Safety Threshold (Low Stock)",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_WARNING,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{total_low} items",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_WARNING,
                            ),
                            bgcolor="#FEF3C7",
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(
                    content=low_table
                    if self.low_stock_items
                    else ft.Container(
                        content=ft.Text(
                            "All active items meet minimum stock thresholds.",
                            size=13,
                            color=COLOR_DARK_GREEN,
                        ),
                        padding=16,
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
