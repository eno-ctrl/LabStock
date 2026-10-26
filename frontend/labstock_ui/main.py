import sys
from pathlib import Path

import flet as ft

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from frontend.labstock_ui.app import create_app


def main():
    ft.app(target=create_app)


if __name__ == "__main__":
    main()
