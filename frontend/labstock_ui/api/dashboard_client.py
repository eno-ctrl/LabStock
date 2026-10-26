from typing import Any

from frontend.labstock_ui.api.client import api_client


def get_summary() -> dict[str, Any]:
    return api_client.get("/dashboard/summary")


def get_recent_activity() -> dict[str, Any]:
    return api_client.get("/dashboard/recent-activity")


def get_low_stock_replenishment() -> Any:
    return api_client.get("/replenishment/low-stock")


def get_out_of_stock_replenishment() -> Any:
    return api_client.get("/replenishment/out-of-stock")
