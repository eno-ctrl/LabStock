from typing import Any

from frontend.labstock_ui.api.client import api_client


def list_users(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    return api_client.get("/users", params={"page": page, "page_size": page_size})


def get_user(user_id: int) -> dict[str, Any]:
    return api_client.get(f"/users/{user_id}")


def create_user(payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.post("/users", json_data=payload)


def update_user(user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    return api_client.patch(f"/users/{user_id}", json_data=payload)
