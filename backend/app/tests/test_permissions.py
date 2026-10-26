from fastapi.testclient import TestClient

from backend.app.models.user import User


def test_viewer_cannot_modify_inventory_or_users(client: TestClient, viewer_headers: dict):
    # Viewer tries to create item -> 403 Forbidden
    item_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "FAIL-VIEWER-01",
            "name": "Fail",
            "category": "Test",
            "storage_location": "Bin",
        },
        headers=viewer_headers,
    )
    assert item_resp.status_code == 403
    assert item_resp.json()["error"]["code"] == "PERMISSION_DENIED"

    # Viewer tries to post receipt -> 403
    move_resp = client.post(
        "/api/v1/movements/receipts",
        json={"item_id": 1, "quantity": 10.0},
        headers=viewer_headers,
    )
    assert move_resp.status_code == 403

    # Viewer tries to list users -> 403
    user_resp = client.get("/api/v1/users", headers=viewer_headers)
    assert user_resp.status_code == 403


def test_manager_cannot_manage_users_or_reverse_movements(
    client: TestClient, manager_headers: dict
):
    # Manager tries to create a user -> 403
    resp = client.post(
        "/api/v1/users",
        json={"email": "hack@labstock.edu", "full_name": "Hacker", "password": "Password123#"},
        headers=manager_headers,
    )
    assert resp.status_code == 403

    # Manager tries to reverse movement -> 403
    rev_resp = client.post(
        "/api/v1/movements/1/reverse",
        json={"reason": "Attempt reversal"},
        headers=manager_headers,
    )
    assert rev_resp.status_code == 403


def test_last_active_admin_cannot_be_deactivated(
    client: TestClient, admin_headers: dict, admin_user: User
):
    # Attempting to deactivate self when sole admin -> 409
    resp = client.patch(
        f"/api/v1/users/{admin_user.id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "LAST_ADMIN_PROTECTED"
