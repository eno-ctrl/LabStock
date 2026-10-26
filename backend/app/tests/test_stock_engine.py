import uuid

from fastapi.testclient import TestClient


def test_atomic_receipt_issue_and_insufficient_stock(client: TestClient, manager_headers: dict):
    # 1. Create item with 0 initial stock
    create_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "STK-ENG-001",
            "name": "Linear Stepper Motor",
            "category": "Motors",
            "unit": "pcs",
            "storage_location": "Shelf S-01",
            "min_stock_threshold": 5.0,
        },
        headers=manager_headers,
    )
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    # 2. Receipt 10 units
    rcpt_resp = client.post(
        "/api/v1/movements/receipts",
        json={"item_id": item_id, "quantity": 10.0, "reason": "PO-1001"},
        headers=manager_headers,
    )
    assert rcpt_resp.status_code == 201
    assert rcpt_resp.json()["balance_after"] == 10.0

    # 3. Issue 4 units
    issue_resp = client.post(
        "/api/v1/movements/issues",
        json={
            "item_id": item_id,
            "quantity": 4.0,
            "recipient_project": "Robotics Senior Capstone",
        },
        headers=manager_headers,
    )
    assert issue_resp.status_code == 201
    assert issue_resp.json()["balance_after"] == 6.0

    # 4. Attempt to issue 10 units (only 6 available) -> must fail with 409
    fail_issue = client.post(
        "/api/v1/movements/issues",
        json={
            "item_id": item_id,
            "quantity": 10.0,
            "recipient_project": "Invalid Excessive Request",
        },
        headers=manager_headers,
    )
    assert fail_issue.status_code == 409
    assert fail_issue.json()["error"]["code"] == "INSUFFICIENT_STOCK"

    # Verify balance was NOT mutated
    item_resp = client.get(f"/api/v1/items/{item_id}", headers=manager_headers)
    assert item_resp.json()["balance"]["quantity_on_hand"] == 6.0


def test_idempotency_key_replay_and_conflict(client: TestClient, manager_headers: dict):
    create_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "IDEMP-SKU-01",
            "name": "Optocoupler 4N35",
            "category": "ICs",
            "unit": "pcs",
            "storage_location": "Bin 9",
        },
        headers=manager_headers,
    )
    item_id = create_resp.json()["id"]
    idemp_key = f"idemp_{uuid.uuid4().hex}"

    # First receipt with key
    payload = {
        "item_id": item_id,
        "quantity": 25.0,
        "idempotency_key": idemp_key,
    }
    resp1 = client.post("/api/v1/movements/receipts", json=payload, headers=manager_headers)
    assert resp1.status_code == 201
    movement_id_1 = resp1.json()["id"]
    assert resp1.json()["balance_after"] == 25.0

    # Repeating same request with same key must return same movement without double adding
    resp2 = client.post("/api/v1/movements/receipts", json=payload, headers=manager_headers)
    assert resp2.status_code == 201
    assert resp2.json()["id"] == movement_id_1

    # Check balance is STILL 25.0, NOT 50.0!
    item_resp = client.get(f"/api/v1/items/{item_id}", headers=manager_headers)
    assert item_resp.json()["balance"]["quantity_on_hand"] == 25.0

    # Reusing key with DIFFERENT quantity must fail with 409
    diff_payload = {
        "item_id": item_id,
        "quantity": 99.0,
        "idempotency_key": idemp_key,
    }
    resp3 = client.post("/api/v1/movements/receipts", json=diff_payload, headers=manager_headers)
    assert resp3.status_code == 409
    assert resp3.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"


def test_reversal_and_ledger_reconciliation(
    client: TestClient, admin_headers: dict, manager_headers: dict
):
    create_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "RECON-01",
            "name": "Reconciliation Test Item",
            "category": "Testing",
            "unit": "pcs",
            "storage_location": "Bin R",
        },
        headers=manager_headers,
    )
    item_id = create_resp.json()["id"]

    # Receipts & returns
    client.post(
        "/api/v1/movements/receipts",
        json={"item_id": item_id, "quantity": 100.0},
        headers=manager_headers,
    )
    client.post(
        "/api/v1/movements/issues",
        json={"item_id": item_id, "quantity": 30.0, "recipient_project": "Team Alpha"},
        headers=manager_headers,
    )
    client.post(
        "/api/v1/movements/returns",
        json={"item_id": item_id, "quantity": 5.0},
        headers=manager_headers,
    )
    damage_resp = client.post(
        "/api/v1/movements/damages",
        json={"item_id": item_id, "quantity": 10.0, "reason": "Pin bent during transport"},
        headers=manager_headers,
    )
    damage_id = damage_resp.json()["id"]

    # Current balance should be 100 - 30 + 5 - 10 = 65
    item_data = client.get(f"/api/v1/items/{item_id}", headers=manager_headers).json()
    assert item_data["balance"]["quantity_on_hand"] == 65.0

    # Admin reverses the damage movement
    rev_resp = client.post(
        f"/api/v1/movements/{damage_id}/reverse",
        json={"reason": "Damage recorded against wrong SKU, reversing entry"},
        headers=admin_headers,
    )
    assert rev_resp.status_code == 201
    assert rev_resp.json()["signed_quantity"] == 10.0
    assert rev_resp.json()["balance_after"] == 75.0

    # Verify reconciliation check
    recon_resp = client.get(f"/api/v1/items/{item_id}/reconcile", headers=manager_headers)
    assert recon_resp.status_code == 200
    recon = recon_resp.json()
    assert recon["is_reconciled"] is True
    assert recon["balance_qoh"] == 75.0
    assert recon["ledger_sum"] == 75.0
    assert recon["difference"] == 0.0
