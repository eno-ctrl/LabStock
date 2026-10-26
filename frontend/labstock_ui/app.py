import flet as ft

import frontend.labstock_ui  # noqa: F401
from frontend.labstock_ui.components.app_shell import AppShell
from frontend.labstock_ui.config import COLOR_BACKGROUND, COLOR_PRIMARY_NAVY


def create_app(page: ft.Page):
    page.title = "LabStock — Laboratory Inventory & Spare Parts Management"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COLOR_BACKGROUND
    page.padding = 0
    page.spacing = 0

    # Window geometry
    page.window.width = 1320
    page.window.height = 840
    page.window.min_width = 960
    page.window.min_height = 640

    # Fonts
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "monospace": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap",
    }
    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme_seed=COLOR_PRIMARY_NAVY,
    )

    shell = AppShell(page)
    page.add(shell)
    page.update()
