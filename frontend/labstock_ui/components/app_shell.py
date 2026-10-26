import flet as ft

from frontend.labstock_ui.components.sidebar import Sidebar
from frontend.labstock_ui.components.topbar import Topbar
from frontend.labstock_ui.config import COLOR_BACKGROUND
from frontend.labstock_ui.pages.dashboard import DashboardPage
from frontend.labstock_ui.pages.inventory import InventoryPage
from frontend.labstock_ui.pages.item_details import ItemDetailsPage
from frontend.labstock_ui.pages.item_form import ItemFormPage
from frontend.labstock_ui.pages.login import LoginPage
from frontend.labstock_ui.pages.purchase_requests import PurchaseRequestsPage
from frontend.labstock_ui.pages.replenishment import ReplenishmentPage
from frontend.labstock_ui.pages.reports import ReportsPage
from frontend.labstock_ui.pages.settings import SettingsPage
from frontend.labstock_ui.pages.stock_movements import StockMovementsPage
from frontend.labstock_ui.pages.suppliers import SuppliersPage
from frontend.labstock_ui.pages.user_management import UserManagementPage
from frontend.labstock_ui.state.navigation import navigation
from frontend.labstock_ui.state.session import session


class AppShell(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.bgcolor = COLOR_BACKGROUND

        self.sidebar = Sidebar(page)
        self.topbar = Topbar(page)
        self.content_area = ft.Container(expand=True, bgcolor=COLOR_BACKGROUND)

        # Wire up listeners
        navigation.add_listener(self._on_route_changed)
        session.add_listener(self._on_auth_changed)

        self._render_current_route()

    def _on_route_changed(self, route: str, params: dict):
        self._render_current_route()

    def _on_auth_changed(self):
        if not session.is_authenticated:
            navigation.navigate("login")
        else:
            self.sidebar.refresh()
            navigation.navigate("dashboard")

    def _render_current_route(self):
        route = navigation.current_route
        params = navigation.route_params

        # Route to title/subtitle mapping
        titles = {
            "dashboard": ("Dashboard", "Monitor laboratory inventory & stock availability"),
            "inventory": (
                "Inventory Management",
                "Manage catalog items, storage bins, and stock status",
            ),
            "item_form": ("Item Catalog Form", "Register or edit component specifications"),
            "item_details": (
                "Item Details & History",
                "Inspect current balance and complete movement ledger",
            ),
            "stock_movements": (
                "Stock Movements",
                "Record physical receipts, issues, returns, damages, and adjustments",
            ),
            "replenishment": (
                "Low Stock & Replenishment",
                "Identify threshold deficits and procurement requirements",
            ),
            "purchase_requests": (
                "Purchase Requests",
                "Control order lifecycles and physical receiving",
            ),
            "suppliers": (
                "Supplier Management",
                "Vendor directory and preferred catalog associations",
            ),
            "reports": (
                "Reports & Analytics",
                "Audit-ready summaries and formula-safe CSV exports",
            ),
            "user_management": (
                "User Management",
                "Administrator account controls and role assignment",
            ),
            "settings": (
                "Settings & Diagnostics",
                "System configuration and database reconciliation",
            ),
        }

        # If not authenticated, force login screen
        if not session.is_authenticated and route != "login":
            route = "login"

        if route == "login":
            self.content = LoginPage(self.page)
        else:
            # Instantiate corresponding page view
            if route == "dashboard":
                page_view = DashboardPage(self.page)
            elif route == "inventory":
                page_view = InventoryPage(self.page)
            elif route == "item_form":
                item_id = params.get("item_id")
                page_view = ItemFormPage(self.page, item_id=item_id)
            elif route == "item_details":
                item_id = params.get("item_id", 1)
                page_view = ItemDetailsPage(self.page, item_id=item_id)
            elif route == "stock_movements":
                item_id = params.get("item_id")
                page_view = StockMovementsPage(self.page, default_item_id=item_id)
            elif route == "replenishment":
                page_view = ReplenishmentPage(self.page)
            elif route == "purchase_requests":
                page_view = PurchaseRequestsPage(self.page)
            elif route == "suppliers":
                page_view = SuppliersPage(self.page)
            elif route == "reports":
                page_view = ReportsPage(self.page)
            elif route == "user_management":
                page_view = UserManagementPage(self.page)
            elif route == "settings":
                page_view = SettingsPage(self.page)
            else:
                page_view = DashboardPage(self.page)

            # Update topbar and sidebar active tab
            t_title, t_sub = titles.get(route, ("LabStock", ""))
            self.topbar.update_title(t_title, t_sub)
            self.sidebar.refresh()
            self.content_area.content = page_view

            self.content = ft.Row(
                controls=[
                    self.sidebar,
                    ft.Column(
                        controls=[
                            self.topbar,
                            self.content_area,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            )

        self.page.update()
