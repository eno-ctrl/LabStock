import flet as ft

from frontend.labstock_ui.api import dashboard_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.empty_state import empty_state
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.components.metric_card import metric_card
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


class DashboardPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)
        self.content = loading_state("Loading dashboard metrics...")
        self.load_data()

    def load_data(self):
        try:
            summary = dashboard_client.get_summary()
            recent_res = dashboard_client.get_recent_activity()
            recent_movements = recent_res.get("recent_movements", [])
            self.content = self._build_dashboard(summary, recent_movements)
        except ApiClientException as e:
            self.content = empty_state(
                title="Unable to load dashboard",
                message=e.message,
                icon=ft.Icons.CLOUD_OFF,
                action_label="Retry",
                on_action=lambda e: self.load_data(),
            )
        except Exception as e:
            self.content = empty_state(
                title="Connection Error",
                message=f"Error connecting to backend: {str(e)}",
                icon=ft.Icons.ERROR_OUTLINE,
                action_label="Retry",
                on_action=lambda e: self.load_data(),
            )
        self.page.update()

    def _build_dashboard(self, summary: dict, recent_movements: list) -> ft.Column:
        # Quick Action Strip
        action_strip = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="Add Item",
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    on_click=lambda e: navigation.navigate("item_form"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text="Receive Stock",
                    icon=ft.Icons.MOVE_TO_INBOX_OUTLINED,
                    on_click=lambda e: navigation.navigate("stock_movements"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text="Issue Stock",
                    icon=ft.Icons.OUTBOX_OUTLINED,
                    on_click=lambda e: navigation.navigate("stock_movements"),
                    visible=session.is_manager,
                ),
                ft.OutlinedButton(
                    text=f"View Low Stock ({summary.get('low_stock_count', 0)})",
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                    on_click=lambda e: navigation.navigate("replenishment"),
                ),
                ft.OutlinedButton(
                    text="Purchase Requests",
                    icon=ft.Icons.SHOPPING_CART_OUTLINED,
                    on_click=lambda e: navigation.navigate("purchase_requests"),
                ),
            ],
            spacing=10,
            wrap=True,
        )

        # 4 Metric Cards
        metrics_row = ft.Row(
            controls=[
                metric_card(
                    title="Active Catalog Items",
                    value=f"{summary.get('active_items_count', 0):,}",
                    subtitle="Tracked components",
                    icon=ft.Icons.INVENTORY_2_OUTLINED,
                    icon_bg="#E5EEFF",
                    icon_color=COLOR_PRIMARY_NAVY,
                ),
                metric_card(
                    title="Total Units on Hand",
                    value=f"{summary.get('total_quantity_on_hand', 0):,.0f}",
                    subtitle="Verified physical units",
                    icon=ft.Icons.LAYERS_OUTLINED,
                    icon_bg="#E0F2FE",
                    icon_color="#0284C7",
                ),
                metric_card(
                    title="Low Stock Items",
                    value=str(summary.get("low_stock_count", 0)),
                    subtitle="Below minimum threshold",
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                    icon_bg="#FEF3C7",
                    icon_color=COLOR_WARNING,
                    value_color=COLOR_WARNING
                    if summary.get("low_stock_count", 0) > 0
                    else COLOR_TEXT_PRIMARY,
                    on_click=lambda e: navigation.navigate("replenishment"),
                ),
                metric_card(
                    title="Out of Stock",
                    value=str(summary.get("out_of_stock_count", 0)),
                    subtitle="Depleted inventory",
                    icon=ft.Icons.ERROR_OUTLINE,
                    icon_bg="#FEE2E2",
                    icon_color=COLOR_ERROR,
                    value_color=COLOR_ERROR
                    if summary.get("out_of_stock_count", 0) > 0
                    else COLOR_TEXT_PRIMARY,
                    on_click=lambda e: navigation.navigate("replenishment"),
                ),
            ],
            spacing=16,
        )

        # Attention Items List
        attention_controls = []
        attention_items = summary.get("attention_items", [])
        if attention_items:
            for item in attention_items:
                attention_controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                sku_chip(item.get("sku", "")),
                                                ft.Text(
                                                    item.get("name", ""),
                                                    size=14,
                                                    weight=ft.FontWeight.W_600,
                                                    color=COLOR_TEXT_PRIMARY,
                                                ),
                                                status_badge(item.get("status", "LOW_STOCK")),
                                            ],
                                            spacing=8,
                                        ),
                                        ft.Text(
                                            f"Location: {item.get('storage_location', 'N/A')} • Min: {item.get('min_stock_threshold')} units",
                                            size=12,
                                            color=COLOR_TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"{item.get('quantity_on_hand', 0)} on hand",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_TEXT_PRIMARY,
                                        ),
                                        ft.Text(
                                            f"Suggest reorder: {item.get('suggested_reorder', 'N/A')}",
                                            size=11,
                                            color=COLOR_TEXT_SECONDARY,
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=2,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                        bgcolor=COLOR_SURFACE,
                        border=ft.Border.all(1, COLOR_BORDER),
                        border_radius=8,
                    )
                )
        else:
            attention_controls.append(
                ft.Container(
                    content=ft.Text(
                        "All inventory items currently satisfy safety thresholds.",
                        size=13,
                        color=COLOR_DARK_GREEN,
                    ),
                    padding=ft.Padding.all(16),
                    bgcolor="#EBFBF5",
                    border=ft.Border.all(1, "#A7F3D0"),
                    border_radius=8,
                )
            )

        # Recent Movements Ledger Preview
        movement_rows = []
        if recent_movements:
            for m in recent_movements[:8]:
                movement_rows.append(
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
                                    f"{m.get('quantity', 0)}",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="monospace",
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    f"{m.get('balance_after', 0)}", size=12, font_family="monospace"
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    m.get("recipient_project") or m.get("reason") or "—",
                                    size=11,
                                    color=COLOR_TEXT_SECONDARY,
                                )
                            ),
                        ]
                    )
                )

        recent_table = ft.DataTable(
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
                    ft.Text("QTY", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY)
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
                        "REFERENCE / RECIPIENT",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_SECONDARY,
                    )
                ),
            ],
            rows=movement_rows,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_color="#F8FAFC",
            heading_row_height=38,
            data_row_min_height=42,
            data_row_max_height=48,
        )

        return ft.Column(
            controls=[
                action_strip,
                ft.Container(height=8),
                metrics_row,
                ft.Container(height=16),
                ft.Text(
                    "Items Requiring Attention",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXT_PRIMARY,
                ),
                ft.Column(controls=attention_controls, spacing=8),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Recent Stock Transactions",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.TextButton(
                            "View All Movements",
                            on_click=lambda e: navigation.navigate("stock_movements"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(content=recent_table, bgcolor=COLOR_SURFACE, border_radius=8),
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
