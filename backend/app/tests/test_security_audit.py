from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.services.report_service import sanitize_csv_cell


def test_csv_formula_injection_whitespace_bypass():
    """Verify that leading whitespace or tab before formula triggers is neutralized."""
    assert sanitize_csv_cell("=1+1").startswith("'")
    assert sanitize_csv_cell("  =1+1").startswith("'")
    assert sanitize_csv_cell("\t=cmd").startswith("'")
    assert sanitize_csv_cell("   +12345").startswith("'")
    assert sanitize_csv_cell("   -12345").startswith("'")
    assert sanitize_csv_cell("   @SUM").startswith("'")
    assert sanitize_csv_cell("Normal Text") == "Normal Text"
    assert sanitize_csv_cell("12345") == "12345"


def test_infinite_and_nan_stock_quantities_rejected(client: TestClient, manager_headers: dict):
    """Adversarial input test: floating-point Infinity or NaN must be rejected by API validation."""
    # 1. Create a legitimate item
    item_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "SEC-NUM-001",
            "name": "Numerical Bound Component",
            "category": "Testing",
            "storage_location": "BIN-NUM",
            "initial_stock": 10.0,
        },
        headers=manager_headers,
    )
    assert item_resp.status_code == 201
    item_id = item_resp.json()["id"]

    # Infinity quantity in receipt
    inf_payload = {
        "item_id": item_id,
        "quantity": "Infinity",
        "reference_type": "exploit",
    }
    resp = client.post("/api/v1/movements/receipts", json=inf_payload, headers=manager_headers)
    assert resp.status_code == 422, f"Expected 422 on Infinity, got {resp.status_code}: {resp.text}"

    # NaN quantity in receipt
    nan_payload = {
        "item_id": item_id,
        "quantity": "NaN",
        "reference_type": "exploit",
    }
    resp = client.post("/api/v1/movements/receipts", json=nan_payload, headers=manager_headers)
    assert resp.status_code == 422, f"Expected 422 on NaN, got {resp.status_code}: {resp.text}"

    # Negative or Zero quantity in receipt
    zero_payload = {
        "item_id": item_id,
        "quantity": 0.0,
        "reference_type": "exploit",
    }
    resp = client.post("/api/v1/movements/receipts", json=zero_payload, headers=manager_headers)
    assert resp.status_code == 422


def test_auth_logout_token_revocation(client: TestClient, manager_headers: dict):
    """OWASP ASVS V3.3: After logout, the previously active session token must be revoked server-side."""
    # 1. Verify token works before logout
    resp1 = client.get("/api/v1/auth/me", headers=manager_headers)
    assert resp1.status_code == 200

    # 2. Invoke logout
    resp_logout = client.post("/api/v1/auth/logout", headers=manager_headers)
    assert resp_logout.status_code == 200

    # 3. Verify same token is now rejected with 401 Unauthorized
    resp2 = client.get("/api/v1/auth/me", headers=manager_headers)
    assert resp2.status_code == 401
    assert (
        "revoked" in resp2.json()["error"]["message"].lower()
        or "expired" in resp2.json()["error"]["message"].lower()
    )


def test_password_change_invalidates_prior_tokens(
    client: TestClient, admin_headers: dict, manager_user
):
    """When a user's password is changed, tokens issued prior to the change must be invalidated."""
    # 1. Issue token for manager
    old_token = create_access_token(
        subject=manager_user.email,
        role=manager_user.role,
        user_id=manager_user.id,
    )
    headers = {"Authorization": f"Bearer {old_token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    # 2. Admin updates manager password
    update_resp = client.patch(
        f"/api/v1/users/{manager_user.id}",
        json={"password": "NewSecretPassword123!"},
        headers=admin_headers,
    )
    assert update_resp.status_code == 200

    # 3. Old token must now be rejected
    after_resp = client.get("/api/v1/auth/me", headers=headers)
    assert after_resp.status_code == 401


def test_security_headers_present(client: TestClient):
    """Verify presence of standard OWASP recommended security headers on all responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") in ("DENY", "SAMEORIGIN")
    assert "strict-origin" in headers.get("Referrer-Policy", "").lower()
    assert headers.get("Permissions-Policy") is not None


def test_reversal_idempotency_replay(
    client: TestClient, admin_headers: dict, manager_headers: dict
):
    """Replaying an identical reversal request with the same idempotency key must succeed idempotently."""
    # 1. Create item
    item_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "SEC-REV-001",
            "name": "Reversal Test Component",
            "category": "Testing",
            "storage_location": "BIN-REV",
            "initial_stock": 20.0,
        },
        headers=manager_headers,
    )
    item_id = item_resp.json()["id"]

    # 2. Issue 5 units
    issue_resp = client.post(
        "/api/v1/movements/issues",
        json={
            "item_id": item_id,
            "quantity": 5.0,
            "recipient_project": "Lab Test",
            "reason": "Test Issue",
        },
        headers=manager_headers,
    )
    movement_id = issue_resp.json()["id"]

    # 3. First reversal with idempotency key
    key = "idem-rev-sec-key-001"
    rev1 = client.post(
        f"/api/v1/movements/{movement_id}/reverse",
        json={"reason": "Clerical mistake correction", "idempotency_key": key},
        headers=admin_headers,
    )
    assert rev1.status_code == 201
    rev1_id = rev1.json()["id"]

    # 4. Replay reversal with exact same key -> MUST succeed idempotently, returning same movement ID
    rev2 = client.post(
        f"/api/v1/movements/{movement_id}/reverse",
        json={"reason": "Clerical mistake correction", "idempotency_key": key},
        headers=admin_headers,
    )
    assert rev2.status_code in (200, 201)
    assert rev2.json()["id"] == rev1_id


def test_purchase_request_self_approval_prevented(
    client: TestClient, admin_headers: dict, admin_user, manager_headers: dict
):
    """Segregation of Duties: A requester cannot approve their own purchase request."""
    # 1. Create item
    item_resp = client.post(
        "/api/v1/items",
        json={
            "sku": "SEC-PR-001",
            "name": "Procurement Item",
            "category": "Testing",
            "storage_location": "BIN-PR",
        },
        headers=manager_headers,
    )
    assert item_resp.status_code == 201
    item_id = item_resp.json()["id"]

    # 2. Admin creates a PR where they are the requester
    pr_resp = client.post(
        "/api/v1/purchase-requests",
        json={
            "notes": "Admin self-requested purchase order",
            "lines": [
                {
                    "item_id": item_id,
                    "requested_quantity": 10.0,
                    "unit_cost": 5.0,
                }
            ],
        },
        headers=admin_headers,
    )
    assert pr_resp.status_code == 201
    pr_id = pr_resp.json()["id"]

    # 3. Submit the PR
    sub_resp = client.post(f"/api/v1/purchase-requests/{pr_id}/submit", headers=admin_headers)
    assert sub_resp.status_code == 200

    # 4. Admin attempts to self-approve
    approve_resp = client.post(f"/api/v1/purchase-requests/{pr_id}/approve", headers=admin_headers)
    assert approve_resp.status_code in (400, 403, 409), (
        f"Expected self-approval rejection, got {approve_resp.status_code}"
    )


def test_vertical_privilege_escalation_matrix(
    client: TestClient, viewer_headers: dict, manager_headers: dict
):
    """Viewer attempting manager/admin actions, and Manager attempting admin actions."""
    # Viewer cannot create items
    resp = client.post(
        "/api/v1/items",
        json={
            "sku": "VIEWER-ESC",
            "name": "Illegal Item",
            "category": "Test",
            "storage_location": "B1",
        },
        headers=viewer_headers,
    )
    assert resp.status_code == 403

    # Viewer cannot list users
    resp = client.get("/api/v1/users", headers=viewer_headers)
    assert resp.status_code == 403

    # Manager cannot list users
    resp = client.get("/api/v1/users", headers=manager_headers)
    assert resp.status_code == 403

    # Manager cannot reverse movements
    resp = client.post(
        "/api/v1/movements/1/reverse",
        json={"reason": "Manager unauthorized reversal"},
        headers=manager_headers,
    )
    assert resp.status_code == 403


def test_error_envelope_sanitization_no_stack_traces(client: TestClient):
    """Server errors must never leak stack traces or internal file paths to unauthenticated clients."""
    resp = client.post(
        "/api/v1/auth/login",
        content=b"invalid-json-body{{{",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert "Traceback" not in resp.text
    assert "C:\\" not in resp.text
    assert "/Users/" not in resp.text
