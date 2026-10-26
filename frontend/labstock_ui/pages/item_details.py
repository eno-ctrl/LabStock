from typing import Any

import flet as ft

from frontend.labstock_ui.api import inventory_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.components.metric_card import metric_card
from frontend.labstock_ui.components.status_badge import sku_chip, status_badge
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.navigation import navigation
from frontend.labstock_ui.state.session import session


class ItemDetailsPage(ft.Container):
    def __init__(self, page: ft.Page, item_id: int):
        super().__init__()
        self.page = page
        self.item_id = item_id
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.item_data: dict[str, Any] | None = None
        self.movements: list = []

        self.content = loading_state("Loading item details & transaction history...")
        self.load_data()

    def load_data(self):
        try:
            self.item_data = inventory_client.get_item(self.item_id)
            mov_res = inventory_client.get_item_movements(self.item_id, page_size=50)
            self.movements = mov_res.get("items", [])
            self.content = self._build_view()
        except ApiClientException as e:
            self.content = ft.Text(f"Error: {e.message}", color="red")
        except Exception as e:
            self.content = ft.Text(f"Error: {str(e)}", color="red")
        self.page.update()

    def _build_view(self) -> ft.Column:
        data = self.item_data or {}
        balance = data.get("balance") or {}
        supplier = data.get("supplier") or {}

        sku = data.get("sku", "")
        name = data.get("name", "")
        category = data.get("category", "")
        loc = data.get("storage_location", "")
        unit = data.get("unit", "pcs")
        qoh = balance.get("quantity_on_hand", 0.0)
        avail = balance.get("available_to_issue", 0.0)
        min_thresh = data.get("min_stock_threshold", 0.0)
        target = data.get("target_stock") or "N/A"
        st_status = data.get("stock_status", "IN_STOCK")

        # Header Section
        header = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: navigation.navigate("inventory"),
                        ),
                        ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        sku_chip(sku),
                                        ft.Text(
                                            name,
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_TEXT_PRIMARY,
                                        ),
                                        status_badge(st_status),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(
                                    f"Category: {category} • Location: {loc}",
                                    size=12,
                                    color=COLOR_TEXT_SECONDARY,
                                ),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            text="Edit Metadata",
                            icon=ft.Icons.EDIT_OUTLINED,
                            on_click=lambda e: navigation.navigate(
                                "item_form", {"item_id": self.item_id}
                            ),
                            visible=session.is_manager,
                        ),
                        ft.ElevatedButton(
                            text="Transact Stock",
                            icon=ft.Icons.SWAP_VERT,
                            bgcolor=COLOR_PRIMARY_NAVY,
                            color="white",
                            on_click=lambda e: navigation.navigate(
                                "stock_movements", {"item_id": self.item_id}
                            ),
                            visible=session.is_manager,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # 4 Balance Cards
        balance_row = ft.Row(
            controls=[
                metric_card(
                    title="Quantity on Hand",
                    value=f"{qoh:g} {unit}",
                    subtitle="Current physical units",
                    icon=ft.Icons.LAYERS_OUTLINED,
                ),
                metric_card(
                    title="Available to Issue",
                    value=f"{avail:g} {unit}",
                    subtitle="Unreserved usable stock",
                    icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                    icon_color="#059669",
                    icon_bg="#EBFBF5",
                ),
                metric_card(
                    title="Minimum Safety Level",
                    value=f"{min_thresh:g} {unit}",
                    subtitle="Replenishment trigger threshold",
                    icon=ft.Icons.WARNING_AMBER_ROUNDED,
                ),
                metric_card(
                    title="Target / Reorder Level",
                    value=f"{target} {unit}" if target != "N/A" else "Not Configured",
                    subtitle="Optimum inventory target",
                    icon=ft.Icons.FLAG_OUTLINED,
                ),
            ],
            spacing=16,
        )

        # Item Metadata Card
        meta_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Catalog Specifications",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_PRIMARY,
                    ),
                    ft.Divider(height=1, color=COLOR_BORDER),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Manufacturer / Model Code:",
                                        size=11,
                                        color=COLOR_TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        data.get("manufacturer_model") or "Not Specified",
                                        size=13,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Preferred Supplier:", size=11, color=COLOR_TEXT_SECONDARY
                                    ),
                                    ft.Text(
                                        supplier.get("name") if supplier else "None Assigned",
                                        size=13,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Catalog Registration Date:",
                                        size=11,
                                        color=COLOR_TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        data.get("created_at", "")[:19].replace("T", " "), size=13
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Container(height=4),
                    ft.Text("Description & Handling Specs:", size=11, color=COLOR_TEXT_SECONDARY),
                    ft.Text(
                        data.get("description") or "No technical notes entered.",
                        size=13,
                        color=COLOR_TEXT_PRIMARY,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=COLOR_SURFACE,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=10,
            padding=16,
        )

        # Movement History Table
        history_rows = []
        for m in self.movements:
            signed = m.get("signed_quantity", 0.0)
            sign_str = f"+{signed:g}" if signed > 0 else f"{signed:g}"
            sign_color = "#15803D" if signed > 0 else "#DC2626"

            history_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                m.get("timestamp", "")[:19].replace("T", " "),
                                size=11,
                                color=COLOR_TEXT_SECONDARY,
                            )
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

        history_table = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text(
                        "TIMESTAMP", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                ),
                ft.DataColumn(
                    ft.Text(
                        "MOVEMENT", size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
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
                        "RECIPIENT / PROJECT",
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
            rows=history_rows,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=8,
            heading_row_color="#F8FAFC",
            heading_row_height=38,
            data_row_min_height=42,
            data_row_max_height=48,
        )

        return ft.Column(
            controls=[
                header,
                ft.Container(height=4),
                balance_row,
                ft.Container(height=8),
                meta_card,
                ft.Container(height=12),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Chronological Movement History",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            f"Total Transactions: {len(self.movements)}",
                            size=12,
                            color=COLOR_TEXT_SECONDARY,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=history_table
                    if self.movements
                    else ft.Text(
                        "No transactions logged for this item yet.",
                        size=13,
                        color=COLOR_TEXT_SECONDARY,
                    ),
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
