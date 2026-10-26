import flet as ft

from frontend.labstock_ui.config import (
    COLOR_BORDER,
    COLOR_DARK_GREEN,
    COLOR_MINT_TINT,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class Topbar(ft.Container):
    def __init__(self, page: ft.Page, title: str = "Dashboard", subtitle: str = ""):
        super().__init__()
        self.page = page
        self.title_text = title
        self.subtitle_text = subtitle
        self.height = 56
        self.bgcolor = COLOR_SURFACE
        self.border = ft.Border.only(bottom=ft.BorderSide(1, COLOR_BORDER))
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=8)
        self.content = self._build_content()

    def _build_content(self) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            self.title_text,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(self.subtitle_text, size=11, color=COLOR_TEXT_SECONDARY)
                        if self.subtitle_text
                        else ft.Container(),
                    ],
                    spacing=0,
                    tight=True,
                ),
                ft.Row(
                    controls=[
                        # Live connection pill
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        width=7,
                                        height=7,
                                        border_radius=4,
                                        bgcolor=COLOR_DARK_GREEN,
                                    ),
                                    ft.Text(
                                        "FastAPI Engine Connected",
                                        size=11,
                                        weight=ft.FontWeight.W_500,
                                        color=COLOR_DARK_GREEN,
                                    ),
                                ],
                                spacing=6,
                                tight=True,
                            ),
                            bgcolor=COLOR_MINT_TINT,
                            border=ft.Border.all(1, "#A7F3D0"),
                            border_radius=9999,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                            icon_size=20,
                            tooltip="Notifications",
                        ),
                    ],
                    spacing=12,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def update_title(self, title: str, subtitle: str = ""):
        self.title_text = title
        self.subtitle_text = subtitle
        self.content = self._build_content()
        self.update()
