from fastapi.testclient import TestClient

from backend.app.core.security import get_password_hash, verify_password
from backend.app.models.user import User


def test_argon2id_password_hashing():
    raw_pwd = "SuperSecurePassword2026!"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_login_successful(client: TestClient, admin_user: User):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": admin_user.email, "password": "AdminPassword123#"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == admin_user.email
    assert data["user"]["role"] == "administrator"


def test_login_invalid_password(client: TestClient, admin_user: User):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": admin_user.email, "password": "IncorrectPassword!"},
    )
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"
    assert "Invalid email/username or password" in data["error"]["message"]


def test_read_me_endpoint(client: TestClient, admin_headers: dict, admin_user: User):
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == admin_user.id
    assert data["email"] == admin_user.email


def test_deactivated_user_cannot_login(client: TestClient, db, manager_user: User):
    manager_user.is_active = False
    db.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": manager_user.email, "password": "ManagerPassword123#"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTHENTICATION_FAILED"
