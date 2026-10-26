from typing import Any

from frontend.labstock_ui.api.client import api_client


def list_items(
    query: str | None = None,
    category: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if query:
        params["query"] = query
    if category and category != "All":
        params["category"] = category
    if status and status != "All":
        params["status"] = status
    if is_active is not None:
        params["is_active"] = is_active
    return api_client.get("/items", params=params)


def get_item(item_id: int) -> dict[str, Any]:
    return api_client.get(f"/items/{item_id}")


def create_item(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/items", json_data=payload)


def update_item_metadata(item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.patch(f"/items/{item_id}", json_data=payload)


def deactivate_item(item_id: int) -> dict[str, Any]:
    return api_client.post(f"/items/{item_id}/deactivate")


def activate_item(item_id: int) -> dict[str, Any]:
    return api_client.post(f"/items/{item_id}/activate")


def get_item_movements(item_id: int, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    return api_client.get(
        f"/items/{item_id}/movements", params={"page": page, "page_size": page_size}
    )


def reconcile_item(item_id: int) -> dict[str, Any]:
    return api_client.get(f"/items/{item_id}/reconcile")
