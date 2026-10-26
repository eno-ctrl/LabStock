from typing import Any

from frontend.labstock_ui.api.client import api_client


def list_purchase_requests(
    status: str | None = None, page: int = 1, page_size: int = 20
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if status and status != "All":
        params["status"] = status.lower()
    return api_client.get("/purchase-requests", params=params)


def get_purchase_request(request_id: int) -> dict[str, Any]:
    return api_client.get(f"/purchase-requests/{request_id}")


def create_purchase_request(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/purchase-requests", json_data=payload)


def submit_purchase_request(request_id: int) -> dict[str, Any]:
    return api_client.post(f"/purchase-requests/{request_id}/submit")


def approve_purchase_request(request_id: int) -> dict[str, Any]:
    return api_client.post(f"/purchase-requests/{request_id}/approve")


def order_purchase_request(request_id: int) -> dict[str, Any]:
    return api_client.post(f"/purchase-requests/{request_id}/order")


def receive_purchase_request_stock(request_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post(f"/purchase-requests/{request_id}/receive", json_data=payload)


def cancel_purchase_request(request_id: int, reason: str | None = None) -> dict[str, Any]:
    path = f"/purchase-requests/{request_id}/cancel"
    if reason:
        path = f"{path}?reason={reason}"
    return api_client.post(path)
