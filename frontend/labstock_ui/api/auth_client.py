import contextlib
from typing import Any

from frontend.labstock_ui.api.client import api_client
from frontend.labstock_ui.state.session import session


def login(username_or_email: str, password: str) -> dict[str, Any]:
    res = api_client.post(
        "/auth/login",
        json_data={"username_or_email": username_or_email.strip(), "password": password},
    )
    token = res.get("access_token")
    user = res.get("user")
    session.login(token, user)
    return res


def logout():
    with contextlib.suppress(Exception):
        api_client.post("/auth/logout")
    session.logout()


def get_me() -> dict[str, Any]:
    return api_client.get("/auth/me")
