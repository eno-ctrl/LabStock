from typing import Any

from frontend.labstock_ui.api.client import api_client


def list_movements(
    item_id: int | None = None,
    movement_type: str | None = None,
    query: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if item_id:
        params["item_id"] = item_id
    if movement_type and movement_type != "All":
        params["movement_type"] = movement_type.lower()
    if query:
        params["query"] = query
    return api_client.get("/movements", params=params)


def receive_stock(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/movements/receipts", json_data=payload)


def issue_stock(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/movements/issues", json_data=payload)


def return_stock(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/movements/returns", json_data=payload)


def record_damage(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/movements/damages", json_data=payload)


def adjust_stock(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/movements/adjustments", json_data=payload)


def reverse_movement(
    movement_id: int, reason: str, idempotency_key: str | None = None
) -> dict[str, Any]:
    return api_client.post(
        f"/movements/{movement_id}/reverse",
        json_data={"reason": reason, "idempotency_key": idempotency_key},
    )
