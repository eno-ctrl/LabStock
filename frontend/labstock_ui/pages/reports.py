from typing import Any

import flet as ft

from frontend.labstock_ui.api import report_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.empty_state import empty_state
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_DARK_GREEN,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class ReportsPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.selected_report = "current_stock"
        self.report_data: list[dict[str, Any]] = []

        self.content = loading_state("Generating report...")
        self.load_report()

    def load_report(self):
        try:
            res = report_client.get_report_data(self.selected_report)
            self.report_data = res.get("data", [])
            self.content = self._build_view()
        except ApiClientException as e:
            self.content = empty_state("Error Generating Report", e.message, ft.Icons.ERROR_OUTLINE)
        except Exception as e:
            self.content = empty_state("Error Generating Report", str(e), ft.Icons.ERROR_OUTLINE)
        self.page.update()

    def _export_csv(self):
        try:
            csv_text = report_client.download_report_csv(self.selected_report)
            dialog = ft.AlertDialog(
                title=ft.Text(
                    f"CSV Export: {self.selected_report}", size=16, weight=ft.FontWeight.BOLD
                ),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Sanitized CSV stream with spreadsheet injection mitigation:", size=13
                        ),
                        ft.TextField(
                            value=csv_text[:800]
                            + ("\n... [truncated]" if len(csv_text) > 800 else ""),
                            multiline=True,
                            min_lines=6,
                            max_lines=12,
                            read_only=True,
                            text_size=11,
                            text_style=ft.TextStyle(font_family="monospace"),
                        ),
                    ],
                    tight=True,
                    width=520,
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

    def _show_toast(self, msg: str, is_error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor="#DC3545" if is_error else COLOR_PRIMARY_NAVY,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def _build_view(self) -> ft.Column:
        report_dropdown = ft.Dropdown(
            label="Select Report",
            value=self.selected_report,
            height=42,
            text_size=13,
            width=280,
            options=[
                ft.dropdown.Option("current_stock", "Current Stock Balance Report"),
                ft.dropdown.Option("consumption", "Item Consumption & Net Usage"),
                ft.dropdown.Option("movements", "All Stock Movements Audit Ledger"),
                ft.dropdown.Option("damaged_stock", "Damaged & Written-off Stock"),
                ft.dropdown.Option("low_stock", "Low Stock & Threshold Deficits"),
                ft.dropdown.Option("out_of_stock", "Out-of-Stock Depletions"),
            ],
            on_change=lambda e: self._on_report_change(e.control.value),
        )

        controls_row = ft.Row(
            controls=[
                report_dropdown,
                ft.ElevatedButton(
                    text="Refresh Report",
                    icon=ft.Icons.REFRESH,
                    bgcolor=COLOR_PRIMARY_NAVY,
                    color="white",
                    height=40,
                    on_click=lambda e: self.load_report(),
                ),
                ft.OutlinedButton(
                    text="Export Sanitized CSV",
                    icon=ft.Icons.DOWNLOAD,
                    height=40,
                    on_click=lambda e: self._export_csv(),
                ),
            ],
            spacing=10,
        )

        # Build Dynamic Data Table
        if self.report_data:
            columns_keys = list(self.report_data[0].keys())
            dt_cols = [
                ft.DataColumn(
                    ft.Text(
                        col.upper(), size=11, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_SECONDARY
                    )
                )
                for col in columns_keys
            ]

            dt_rows = []
            for row in self.report_data[:100]:
                cells = [
                    ft.DataCell(
                        ft.Text(
                            str(row.get(col, "")),
                            size=12,
                            font_family="monospace"
                            if any(
                                num_key in col.lower()
                                for num_key in (
                                    "qty",
                                    "on hand",
                                    "units",
                                    "quantity",
                                    "consumption",
                                    "balance",
                                    "sku",
                                )
                            )
                            else None,
                        )
                    )
                    for col in columns_keys
                ]
                dt_rows.append(ft.DataRow(cells=cells))

            report_table = ft.DataTable(
                columns=dt_cols,
                rows=dt_rows,
                border=ft.Border.all(1, COLOR_BORDER),
                border_radius=8,
                heading_row_color="#F8FAFC",
                heading_row_height=40,
                data_row_min_height=42,
            )
        else:
            report_table = empty_state(
                "No data returned", "This report contains no records matching criteria."
            )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Reports & Analytics",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Audit-ready inventory summaries, consumption analytics, and safe exports.",
                                    size=12,
                                    color=COLOR_TEXT_SECONDARY,
                                ),
                            ],
                            spacing=2,
                        ),
                        ft.Text(
                            f"Records: {len(self.report_data)}",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=COLOR_DARK_GREEN,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=8),
                controls_row,
                ft.Container(height=12),
                ft.Container(
                    content=report_table,
                    bgcolor=COLOR_SURFACE,
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _on_report_change(self, rep: str):
        self.selected_report = rep
        self.load_report()
