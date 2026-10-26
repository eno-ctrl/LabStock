from typing import Any

import flet as ft

from frontend.labstock_ui.api import inventory_client, supplier_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.components.loading_state import loading_state
from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_ERROR,
    COLOR_PRIMARY_MINT,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.navigation import navigation


class ItemFormPage(ft.Container):
    def __init__(self, page: ft.Page, item_id: int | None = None):
        super().__init__()
        self.page = page
        self.item_id = item_id
        self.is_edit = item_id is not None
        self.expand = True
        self.padding = ft.Padding.all(24)

        self.suppliers_list: list = []
        self.item_data: dict[str, Any] | None = None

        self.content = loading_state("Initializing form...")
        self._init_data()

    def _init_data(self):
        try:
            sup_res = supplier_client.list_suppliers(page_size=100)
            self.suppliers_list = sup_res.get("items", [])
            if self.is_edit:
                self.item_data = inventory_client.get_item(self.item_id)
            self.content = self._build_form()
        except Exception as e:
            self.content = ft.Text(f"Error loading data: {e}", color=COLOR_ERROR)
        self.page.update()

    def _build_form(self) -> ft.Column:
        title = "Edit Inventory Item" if self.is_edit else "Add New Inventory Item"
        subtitle = (
            f"Update catalog metadata for SKU: {self.item_data.get('sku')}"
            if self.is_edit
            else "Register a laboratory component, supply, or spare part into the central catalog."
        )

        data = self.item_data or {}

        self.sku_field = ft.TextField(
            label="SKU / Part Identifier *",
            hint_text="e.g. EL-MTR-042",
            value=data.get("sku", ""),
            disabled=self.is_edit,  # SKU is immutable once created
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
            text_style=ft.TextStyle(font_family="monospace"),
        )

        self.name_field = ft.TextField(
            label="Item Name *",
            hint_text="e.g. DC Motor Driver L298N",
            value=data.get("name", ""),
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
        )

        self.category_dropdown = ft.Dropdown(
            label="Category *",
            value=data.get("category", "Electronics"),
            height=44,
            text_size=13,
            options=[
                ft.dropdown.Option("Electronics"),
                ft.dropdown.Option("Sensors"),
                ft.dropdown.Option("Microcontrollers"),
                ft.dropdown.Option("Single Board Computers"),
                ft.dropdown.Option("Semiconductors"),
                ft.dropdown.Option("Passive Components"),
                ft.dropdown.Option("Motors"),
                ft.dropdown.Option("Tools"),
                ft.dropdown.Option("Fasteners & Hardware"),
            ],
        )

        self.unit_field = ft.TextField(
            label="Unit of Measure *",
            hint_text="e.g. pcs, meters, rolls, grams",
            value=data.get("unit", "pcs"),
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
        )

        self.location_field = ft.TextField(
            label="Storage Location (Bin / Shelf / Cabinet) *",
            hint_text="e.g. Shelf B-04, Cabinet C-02",
            value=data.get("storage_location", ""),
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
        )

        self.min_thresh_field = ft.TextField(
            label="Minimum Stock Threshold",
            hint_text="Trigger replenishment alert when below",
            value=str(data.get("min_stock_threshold", 0.0)),
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.target_stock_field = ft.TextField(
            label="Target Stock / Reorder Goal",
            hint_text="Suggested reorder calculation target",
            value=str(data.get("target_stock") or ""),
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        supplier_opts = [ft.dropdown.Option("None", "No Preferred Supplier")]
        for s in self.suppliers_list:
            supplier_opts.append(ft.dropdown.Option(str(s["id"]), s["name"]))

        pref_sup_val = (
            str(data.get("preferred_supplier_id")) if data.get("preferred_supplier_id") else "None"
        )
        self.supplier_dropdown = ft.Dropdown(
            label="Preferred Supplier",
            value=pref_sup_val,
            height=44,
            text_size=13,
            options=supplier_opts,
        )

        self.mfr_model_field = ft.TextField(
            label="Manufacturer / Model Code",
            hint_text="e.g. L298N-STMicroelectronics",
            value=data.get("manufacturer_model") or "",
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
        )

        self.desc_field = ft.TextField(
            label="Description & Technical Specs",
            hint_text="Enter operating voltages, pinouts, tolerances, or handling notes...",
            value=data.get("description") or "",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            text_size=13,
        )

        self.initial_stock_field = ft.TextField(
            label="Initial Physical Count (Opening Receipt)",
            hint_text="Enter current verified units on shelf (creates opening receipt)",
            value="0",
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            height=44,
            text_size=13,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=not self.is_edit,  # Strictly hidden during edit!
        )

        self.active_switch = ft.Switch(
            label="Active catalog item (available for issue/receipt)",
            value=data.get("is_active", True),
        )

        self.error_banner = ft.Container(
            content=ft.Text("", color=COLOR_ERROR, size=13),
            visible=False,
            padding=ft.Padding.all(8),
            bgcolor="#FEF2F2",
            border=ft.Border.all(1, "#FCA5A5"),
            border_radius=6,
        )

        save_btn = ft.ElevatedButton(
            text="Save Item" if not self.is_edit else "Update Metadata",
            icon=ft.Icons.CHECK,
            bgcolor=COLOR_PRIMARY_NAVY,
            color="white",
            height=42,
            on_click=lambda e: self._submit_form(),
        )

        cancel_btn = ft.OutlinedButton(
            text="Cancel",
            height=42,
            on_click=lambda e: navigation.navigate("inventory"),
        )

        # Layout Card
        form_card = ft.Container(
            content=ft.Column(
                controls=[
                    self.error_banner,
                    ft.Row(controls=[self.sku_field, self.name_field], spacing=16),
                    ft.Row(controls=[self.category_dropdown, self.unit_field], spacing=16),
                    ft.Row(controls=[self.location_field, self.mfr_model_field], spacing=16),
                    ft.Row(controls=[self.min_thresh_field, self.target_stock_field], spacing=16),
                    self.supplier_dropdown,
                    self.desc_field,
                    self.initial_stock_field if not self.is_edit else ft.Container(),
                    self.active_switch,
                    ft.Divider(height=1, color=COLOR_BORDER),
                    ft.Row(
                        controls=[cancel_btn, save_btn],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=10,
                    ),
                ],
                spacing=16,
            ),
            bgcolor=COLOR_SURFACE,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=10,
            padding=24,
            expand=True,
        )

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: navigation.navigate("inventory"),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    title,
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(subtitle, size=12, color=COLOR_TEXT_SECONDARY),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(height=8),
                form_card,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _submit_form(self):
        sku = self.sku_field.value.strip().upper()
        name = self.name_field.value.strip()
        loc = self.location_field.value.strip()
        unit = self.unit_field.value.strip()

        if not sku or not name or not loc or not unit:
            self.error_banner.content.value = "Please complete all mandatory fields marked with *"
            self.error_banner.visible = True
            self.page.update()
            return

        try:
            min_thresh = float(self.min_thresh_field.value or 0.0)
            target_stock = (
                float(self.target_stock_field.value) if self.target_stock_field.value else None
            )
        except ValueError:
            self.error_banner.content.value = "Threshold and target stock must be valid numbers"
            self.error_banner.visible = True
            self.page.update()
            return

        sup_id = (
            int(self.supplier_dropdown.value)
            if self.supplier_dropdown.value and self.supplier_dropdown.value != "None"
            else None
        )

        if self.is_edit:
            payload = {
                "name": name,
                "category": self.category_dropdown.value,
                "unit": unit,
                "storage_location": loc,
                "min_stock_threshold": min_thresh,
                "target_stock": target_stock,
                "preferred_supplier_id": sup_id,
                "manufacturer_model": self.mfr_model_field.value.strip()
                if self.mfr_model_field.value
                else None,
                "description": self.desc_field.value.strip() if self.desc_field.value else None,
                "is_active": self.active_switch.value,
            }
            try:
                inventory_client.update_item_metadata(self.item_id, payload)
                navigation.navigate("inventory")
            except ApiClientException as e:
                self.error_banner.content.value = e.message
                self.error_banner.visible = True
                self.page.update()
        else:
            try:
                init_stock = float(self.initial_stock_field.value or 0.0)
            except ValueError:
                init_stock = 0.0

            payload = {
                "sku": sku,
                "name": name,
                "category": self.category_dropdown.value,
                "unit": unit,
                "storage_location": loc,
                "min_stock_threshold": min_thresh,
                "target_stock": target_stock,
                "preferred_supplier_id": sup_id,
                "manufacturer_model": self.mfr_model_field.value.strip()
                if self.mfr_model_field.value
                else None,
                "description": self.desc_field.value.strip() if self.desc_field.value else None,
                "initial_stock": init_stock,
                "is_active": self.active_switch.value,
            }
            try:
                inventory_client.create_item(payload)
                navigation.navigate("inventory")
            except ApiClientException as e:
                self.error_banner.content.value = e.message
                self.error_banner.visible = True
                self.page.update()
