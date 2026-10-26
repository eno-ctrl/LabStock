from fastapi.testclient import TestClient


def test_create_item_and_duplicate_sku_rejection(client: TestClient, manager_headers: dict):
    payload = {
        "sku": "TEST-SKU-001",
        "name": "Precision Test Resistor 10k",
        "category": "Passives",
        "unit": "pcs",
        "storage_location": "Bin 01-A",
        "min_stock_threshold": 50.0,
        "initial_stock": 100.0,
    }
    resp = client.post("/api/v1/items", json=payload, headers=manager_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "TEST-SKU-001"
    assert data["balance"]["quantity_on_hand"] == 100.0
    assert "id" in data

    # Duplicate SKU creation must fail with 409
    dup_resp = client.post("/api/v1/items", json=payload, headers=manager_headers)
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "DUPLICATE_SKU"


def test_metadata_edit_never_mutates_stock(client: TestClient, manager_headers: dict):
    # 1. Create item with 50 units
    create_payload = {
        "sku": "TEST-SKU-002",
        "name": "Micro Servo Motor SG90",
        "category": "Motors",
        "unit": "pcs",
        "storage_location": "Shelf M-02",
        "min_stock_threshold": 10.0,
        "initial_stock": 50.0,
    }
    resp = client.post("/api/v1/items", json=create_payload, headers=manager_headers)
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # 2. Patch metadata: change name and description, attempt to inject quantity
    patch_payload = {
        "name": "Micro Servo SG90 Rev B",
        "storage_location": "Shelf M-03",
        "quantity_on_hand": 9999.0,  # Should be ignored by schema / repo!
    }
    patch_resp = client.patch(
        f"/api/v1/items/{item_id}", json=patch_payload, headers=manager_headers
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["name"] == "Micro Servo SG90 Rev B"
    assert patched_data["storage_location"] == "Shelf M-03"
    # Balance must remain exactly 50.0
    assert patched_data["balance"]["quantity_on_hand"] == 50.0


def test_item_deactivation_and_filtering(
    client: TestClient, manager_headers: dict, viewer_headers: dict
):
    # Create item
    payload = {
        "sku": "TEST-DEACT-01",
        "name": "Deactivatable Component",
        "category": "Testing",
        "unit": "pcs",
        "storage_location": "Bin Test",
    }
    resp = client.post("/api/v1/items", json=payload, headers=manager_headers)
    item_id = resp.json()["id"]

    # Deactivate
    deact_resp = client.post(f"/api/v1/items/{item_id}/deactivate", headers=manager_headers)
    assert deact_resp.status_code == 200
    assert deact_resp.json()["is_active"] is False

    # Active filter should omit it
    list_active = client.get("/api/v1/items?is_active=true", headers=viewer_headers)
    skus_active = [it["sku"] for it in list_active.json()["items"]]
    assert "TEST-DEACT-01" not in skus_active

    # Inactive filter includes it
    list_inactive = client.get("/api/v1/items?is_active=false", headers=viewer_headers)
    skus_inactive = [it["sku"] for it in list_inactive.json()["items"]]
    assert "TEST-DEACT-01" in skus_inactive
