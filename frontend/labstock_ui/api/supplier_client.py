from typing import Any

from frontend.labstock_ui.api.client import api_client


def list_suppliers(query: str | None = None, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if query:
        params["query"] = query
    return api_client.get("/suppliers", params=params)


def get_supplier(supplier_id: int) -> dict[str, Any]:
    return api_client.get(f"/suppliers/{supplier_id}")


def create_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/suppliers", json_data=payload)


def update_supplier(supplier_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.patch(f"/suppliers/{supplier_id}", json_data=payload)
