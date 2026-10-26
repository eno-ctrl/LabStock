from typing import Any

from frontend.labstock_ui.api.client import api_client


def get_report_data(report_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    p = params or {}
    p["format"] = "json"
    if report_type == "current_stock":
        return api_client.get("/reports/stock", params=p)
    elif report_type == "low_stock":
        return api_client.get("/reports/low-stock", params=p)
    elif report_type == "out_of_stock":
        return api_client.get("/reports/out-of-stock", params=p)
    elif report_type == "movements":
        return api_client.get("/reports/movements", params=p)
    elif report_type == "consumption":
        return api_client.get("/reports/consumption", params=p)
    elif report_type == "damaged_stock":
        return api_client.get("/reports/damaged-stock", params=p)
    return {"data": []}


def download_report_csv(report_type: str, params: dict[str, Any] | None = None) -> str:
    p = params or {}
    p["format"] = "csv"
    if report_type == "current_stock":
        return api_client.get("/reports/stock", params=p)
    elif report_type == "low_stock":
        return api_client.get("/reports/low-stock", params=p)
    elif report_type == "out_of_stock":
        return api_client.get("/reports/out-of-stock", params=p)
    elif report_type == "movements":
        return api_client.get("/reports/movements", params=p)
    elif report_type == "consumption":
        return api_client.get("/reports/consumption", params=p)
    elif report_type == "damaged_stock":
        return api_client.get("/reports/damaged-stock", params=p)
    return ""
