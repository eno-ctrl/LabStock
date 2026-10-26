import flet as ft

from frontend.labstock_ui.api import auth_client
from frontend.labstock_ui.api.client import ApiClientException
from frontend.labstock_ui.config import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_DARK_GREEN,
    COLOR_ERROR,
    COLOR_MINT_TINT,
    COLOR_PRIMARY_MINT,
    COLOR_PRIMARY_NAVY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from frontend.labstock_ui.state.navigation import navigation


class LoginPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.bgcolor = COLOR_BACKGROUND
        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self.content = self._build_content()

    def _build_content(self) -> ft.Container:
        self.username_input = ft.TextField(
            label="Username or Institutional Email",
            hint_text="e.g. admin@labstock.edu",
            value="admin@labstock.edu",
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            text_size=14,
            height=48,
        )

        self.password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            value="AdminPassword123#",
            border_color=COLOR_BORDER,
            focused_border_color=COLOR_PRIMARY_MINT,
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            text_size=14,
            height=48,
            on_submit=lambda e: self._handle_login(),
        )

        self.error_banner = ft.Container(
            content=ft.Text("", color=COLOR_ERROR, size=13),
            visible=False,
            padding=ft.Padding.all(8),
            bgcolor="#FEF2F2",
            border=ft.Border.all(1, "#FCA5A5"),
            border_radius=6,
        )

        self.login_btn = ft.ElevatedButton(
            text="Sign In to LabStock",
            icon=ft.Icons.LOGIN,
            bgcolor=COLOR_PRIMARY_NAVY,
            color="white",
            height=44,
            on_click=lambda e: self._handle_login(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        # Quick demo login preset buttons for development
        def set_preset(u: str, p: str):
            self.username_input.value = u
            self.password_input.value = p
            self.error_banner.visible = False
            self.page.update()

        demo_presets = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Quick Demo Credentials:",
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=COLOR_TEXT_SECONDARY,
                    ),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                text="Admin",
                                on_click=lambda e: set_preset(
                                    "admin@labstock.edu", "AdminPassword123#"
                                ),
                                height=28,
                            ),
                            ft.OutlinedButton(
                                text="Manager",
                                on_click=lambda e: set_preset(
                                    "manager@labstock.edu", "ManagerPassword123#"
                                ),
                                height=28,
                            ),
                            ft.OutlinedButton(
                                text="Viewer",
                                on_click=lambda e: set_preset(
                                    "viewer@labstock.edu", "ViewerPassword123#"
                                ),
                                height=28,
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=6,
            ),
            padding=ft.Padding.only(top=8),
        )

        # Brand Emblem & Showcase
        brand_emblem = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.PRECISION_MANUFACTURING, size=38, color="white"),
                        width=72,
                        height=72,
                        border_radius=16,
                        bgcolor=COLOR_PRIMARY_NAVY,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(blur_radius=12, color="#2015263B"),
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "LabStock",
                                size=26,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_PRIMARY_NAVY,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "CORE",
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_DARK_GREEN,
                                ),
                                bgcolor=COLOR_MINT_TINT,
                                border=ft.Border.all(1, "#A7F3D0"),
                                border_radius=4,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "Laboratory Inventory & Spare Parts Management",
                        size=13,
                        color=COLOR_TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.VERIFIED_ROUNDED, size=14, color=COLOR_DARK_GREEN),
                                ft.Text(
                                    "Clinical Precision • Real-Time Stock • Traceable",
                                    size=11,
                                    weight=ft.FontWeight.W_500,
                                    color=COLOR_DARK_GREEN,
                                ),
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER,
                            tight=True,
                        ),
                        bgcolor=COLOR_MINT_TINT,
                        border_radius=9999,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            margin=ft.Margin.only(bottom=24),
        )

        # Main login card
        card_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Welcome back", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY
                    ),
                    ft.Text(
                        "Sign in to your institutional laboratory account",
                        size=13,
                        color=COLOR_TEXT_SECONDARY,
                    ),
                    ft.Container(height=12),
                    self.error_banner,
                    self.username_input,
                    self.password_input,
                    ft.Container(height=6),
                    ft.Row(
                        controls=[self.login_btn],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Divider(height=1, color=COLOR_BORDER),
                    demo_presets,
                ],
                spacing=12,
                tight=True,
            ),
            width=420,
            bgcolor=COLOR_SURFACE,
            border=ft.Border.all(1, COLOR_BORDER),
            border_radius=12,
            padding=28,
            shadow=ft.BoxShadow(blur_radius=16, color="#0A15263B"),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    brand_emblem,
                    card_content,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            ),
            alignment=ft.Alignment(0, 0),
            padding=24,
        )

    def _handle_login(self):
        u = self.username_input.value.strip()
        p = self.password_input.value
        if not u or not p:
            self.error_banner.content.value = "Please enter both username and password"
            self.error_banner.visible = True
            self.page.update()
            return

        self.login_btn.disabled = True
        self.login_btn.text = "Authenticating..."
        self.error_banner.visible = False
        self.page.update()

        try:
            auth_client.login(u, p)
            navigation.navigate("dashboard")
        except ApiClientException as e:
            self.error_banner.content.value = e.message
            self.error_banner.visible = True
        except Exception as e:
            self.error_banner.content.value = f"Connection error: {str(e)}"
            self.error_banner.visible = True
        finally:
            self.login_btn.disabled = False
            self.login_btn.text = "Sign In to LabStock"
            self.page.update()
