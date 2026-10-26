import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_DARK_GREEN,
    COLOR_MINT_TINT,
    COLOR_PRIMARY_MINT,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.navigation import navigation
from frontend.labstock_ui.state.session import session


class Sidebar(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.width = 250
        self.bgcolor = COLOR_SURFACE
        self.border = ft.Border.only(right=ft.BorderSide(1, COLOR_BORDER))
        self.padding = ft.Padding.all(16)
        self.content = self._build_content()

    def _nav_item(
        self,
        label: str,
        icon: ft.Icon,
        route: str,
        is_active: bool,
    ) -> ft.Container:
        bg = COLOR_MINT_TINT if is_active else "transparent"
        text_color = COLOR_DARK_GREEN if is_active else COLOR_TEXT_PRIMARY
        icon_color = COLOR_PRIMARY_MINT if is_active else COLOR_TEXT_SECONDARY
        weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_400

        def on_click(e):
            navigation.navigate(route)

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=18, color=icon_color),
                    ft.Text(label, size=13, weight=weight, color=text_color),
                ],
                spacing=10,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=9),
            border_radius=8,
            bgcolor=bg,
            on_click=on_click,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

    def _build_content(self) -> ft.Column:
        cur_route = navigation.current_route

        nav_links = [
            ("Dashboard", ft.Icons.DASHBOARD_OUTLINED, "dashboard"),
            ("Inventory", ft.Icons.INVENTORY_2_OUTLINED, "inventory"),
            ("Stock Movements", ft.Icons.SWAP_VERT_ROUNDED, "stock_movements"),
            ("Replenishment", ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED, "replenishment"),
            ("Purchase Requests", ft.Icons.SHOPPING_CART_OUTLINED, "purchase_requests"),
            ("Suppliers", ft.Icons.STOREFRONT_OUTLINED, "suppliers"),
            ("Reports & Analytics", ft.Icons.BAR_CHART_OUTLINED, "reports"),
        ]

        # Admin only link
        if session.is_admin:
            nav_links.append(("User Management", ft.Icons.PEOPLE_ALT_OUTLINED, "user_management"))

        nav_links.append(("Settings", ft.Icons.SETTINGS_OUTLINED, "settings"))

        link_controls = []
        for label, icon, route in nav_links:
            link_controls.append(
                self._nav_item(
                    label=label,
                    icon=icon,
                    route=route,
                    is_active=(
                        cur_route == route
                        or (route == "inventory" and cur_route in ("item_form", "item_details"))
                    ),
                )
            )

        # Brand header
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.PRECISION_MANUFACTURING, size=20, color="white"),
                        width=36,
                        height=36,
                        border_radius=8,
                        bgcolor=COLOR_PRIMARY_NAVY,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "LabStock",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLOR_PRIMARY_NAVY,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            "CORE",
                                            size=9,
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_DARK_GREEN,
                                        ),
                                        bgcolor=COLOR_MINT_TINT,
                                        border_radius=4,
                                        padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                                    ),
                                ],
                                spacing=6,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.Text("Laboratory Precision", size=10, color=COLOR_TEXT_SECONDARY),
                        ],
                        spacing=0,
                        tight=True,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding.only(bottom=16),
        )

        # Footer with current user and logout
        user_name = (
            session.current_user.get("full_name", "User") if session.current_user else "User"
        )
        user_role = session.role.replace("_", " ").title()

        footer = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON, size=18, color=COLOR_PRIMARY_NAVY),
                        width=32,
                        height=32,
                        border_radius=16,
                        bgcolor="#E2E8F0",
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                user_name,
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_TEXT_PRIMARY,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(user_role, size=10, color=COLOR_TEXT_SECONDARY),
                        ],
                        spacing=0,
                        expand=True,
                        tight=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_size=16,
                        tooltip="Log out",
                        on_click=lambda e: session.logout(),
                    ),
                ],
                spacing=8,
            ),
            padding=ft.Padding.only(top=16),
            border=ft.Border.only(top=ft.BorderSide(1, COLOR_BORDER)),
        )

        return ft.Column(
            controls=[
                header,
                ft.Divider(height=1, color=COLOR_BORDER),
                ft.Column(
                    controls=link_controls, spacing=4, expand=True, scroll=ft.ScrollMode.AUTO
                ),
                footer,
            ],
            spacing=8,
            expand=True,
        )

    def refresh(self):
        self.content = self._build_content()
        self.update()
