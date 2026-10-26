import contextlib
from collections.abc import Callable
from typing import Any, Optional


class NavigationState:
    _instance: Optional["NavigationState"] = None

    def __init__(self):
        self.current_route: str = "dashboard"
        self.route_params: dict[str, Any] = {}
        self._listeners: list[Callable[[str, dict[str, Any]], None]] = []

    @classmethod
    def get_instance(cls) -> "NavigationState":
        if cls._instance is None:
            cls._instance = NavigationState()
        return cls._instance

    def navigate(self, route: str, params: dict[str, Any] | None = None):
        self.current_route = route
        self.route_params = params or {}
        for listener in self._listeners:
            with contextlib.suppress(Exception):
                listener(self.current_route, self.route_params)

    def add_listener(self, listener: Callable[[str, dict[str, Any]], None]):
        if listener not in self._listeners:
            self._listeners.append(listener)


navigation = NavigationState.get_instance()
