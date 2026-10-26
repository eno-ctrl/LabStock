from collections.abc import Callable
from typing import Any, Optional


class SessionState:
    _instance: Optional["SessionState"] = None

    def __init__(self):
        self.access_token: str | None = None
        self.current_user: dict[str, Any] | None = None
        self._on_auth_change_listeners: list[Callable[[], None]] = []

    @classmethod
    def get_instance(cls) -> "SessionState":
        if cls._instance is None:
            cls._instance = SessionState()
        return cls._instance

    @property
    def is_authenticated(self) -> bool:
        return self.access_token is not None and self.current_user is not None

    @property
    def role(self) -> str:
        if self.current_user:
            return self.current_user.get("role", "viewer")
        return "viewer"

    @property
    def is_admin(self) -> bool:
        return self.role == "administrator"

    @property
    def is_manager(self) -> bool:
        return self.role in ("administrator", "inventory_manager")

    def login(self, token: str, user_dict: dict[str, Any]):
        self.access_token = token
        self.current_user = user_dict
        self._notify_listeners()

    def logout(self):
        self.access_token = None
        self.current_user = None
        self._notify_listeners()

    def add_listener(self, listener: Callable[[], None]):
        self._on_auth_change_listeners = [listener]

    def _notify_listeners(self):
        for listener in list(self._on_auth_change_listeners):
            try:
                listener()
            except Exception:
                if listener in self._on_auth_change_listeners:
                    self._on_auth_change_listeners.remove(listener)


session = SessionState.get_instance()
