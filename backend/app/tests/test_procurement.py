from fastapi.testclient import TestClient


def test_purchase_request_lifecycle_and_physical_receipt(
    client: TestClient, admin_headers: dict, manager_headers: dict
):
    # 1. Create item
    item_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "PR-TEST-001",
            "name": "Arduino Uno R3",
            "category": "Microcontrollers",
            "unit": "pcs",
            "storage_location": "Cabinet B",
            "min_stock_threshold": 10.0,
            "initial_stock": 0.0,
        },
        headers=manager_headers,
    )
    item_id = item_resp.json()["id"]

    # 2. Create Purchase Request
    pr_payload = {
        "notes": "Annual student replenishment",
        "lines": [{"item_id": item_id, "requested_quantity": 20.0, "unit_cost": 15.50}],
    }
    pr_resp = client.post("/api/v1/purchase-requests", json=pr_payload, headers=manager_headers)
    assert pr_resp.status_code == 201
    pr_data = pr_resp.json()
    pr_id = pr_data["id"]
    line_id = pr_data["lines"][0]["id"]
    assert pr_data["status"] == "draft"

    # 3. Submit PR
    submit_resp = client.post(f"/api/v1/purchase-requests/{pr_id}/submit", headers=manager_headers)
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "submitted"

    # 4. Approve PR (Admin only)
    approve_resp = client.post(f"/api/v1/purchase-requests/{pr_id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # Verify inventory is STILL 0.0! (Approving does NOT add inventory)
    check_item = client.get(f"/api/v1/items/{item_id}", headers=manager_headers)
    assert check_item.json()["balance"]["quantity_on_hand"] == 0.0

    # 5. Mark as ordered
    order_resp = client.post(f"/api/v1/purchase-requests/{pr_id}/order", headers=manager_headers)
    assert order_resp.status_code == 200
    assert order_resp.json()["status"] == "ordered"
    assert check_item.json()["balance"]["quantity_on_hand"] == 0.0

    # 6. Partial physical receipt: receive 8 of 20
    receive_payload = {
        "items": [{"line_id": line_id, "quantity_to_receive": 8.0}],
        "reference": "Delivery Note DN-881",
    }
    recv_resp = client.post(
        f"/api/v1/purchase-requests/{pr_id}/receive",
        json=receive_payload,
        headers=manager_headers,
    )
    assert recv_resp.status_code == 200
    assert recv_resp.json()["status"] == "partially_received"
    assert recv_resp.json()["lines"][0]["received_quantity"] == 8.0

    # Verify stock increased by exactly 8.0
    item_after_partial = client.get(f"/api/v1/items/{item_id}", headers=manager_headers).json()
    assert item_after_partial["balance"]["quantity_on_hand"] == 8.0

    # 7. Disallow over-receipt: attempt to receive 15 more when only 12 remaining
    over_recv = client.post(
        f"/api/v1/purchase-requests/{pr_id}/receive",
        json={"items": [{"line_id": line_id, "quantity_to_receive": 15.0}]},
        headers=manager_headers,
    )
    assert over_recv.status_code == 409
    assert over_recv.json()["error"]["code"] == "OVER_RECEIPT_DISALLOWED"

    # 8. Complete final physical receipt: 12 units
    final_recv = client.post(
        f"/api/v1/purchase-requests/{pr_id}/receive",
        json={"items": [{"line_id": line_id, "quantity_to_receive": 12.0}]},
        headers=manager_headers,
    )
    assert final_recv.status_code == 200
    assert final_recv.json()["status"] == "received"
    assert final_recv.json()["lines"][0]["received_quantity"] == 20.0

    # Stock is now 20.0
    item_final = client.get(f"/api/v1/items/{item_id}", headers=manager_headers).json()
    assert item_final["balance"]["quantity_on_hand"] == 20.0
