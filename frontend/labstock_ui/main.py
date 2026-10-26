import os
import sys
from pathlib import Path

import flet as ft

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from frontend.labstock_ui.app import create_app


def main():
    port = int(os.environ.get("FLET_PORT", 8502))
    view_mode = os.environ.get("FLET_VIEW", "web_browser")
    app_view = ft.AppView.WEB_BROWSER if view_mode == "web_browser" else ft.AppView.FLET_APP

    if hasattr(ft, "run"):
        ft.run(main=create_app, view=app_view, port=port)
    elif hasattr(ft, "app"):
        ft.app(target=create_app)


if __name__ == "__main__":
    main()
