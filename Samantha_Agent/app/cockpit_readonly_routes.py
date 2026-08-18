from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


JsonPayload = dict[str, Any]
PayloadLoader = Callable[[], JsonPayload]
JsonResponder = Callable[[JsonPayload], None]


HEALTH_RECOVERY_STATUS_GET_PATHS = (
    "/api/status",
    "/api/live-status",
    "/api/decision-status",
    "/api/server/health",
    "/api/recovery/status",
)


@dataclass(frozen=True)
class ReadOnlyJsonRoute:
    path: str
    load_payload: PayloadLoader


class ReadOnlyJsonRouteDispatch:
    """Exact-path dispatcher for a small read-only JSON route domain."""

    def __init__(self, routes: tuple[ReadOnlyJsonRoute, ...]) -> None:
        route_map = {route.path: route for route in routes}
        if len(route_map) != len(routes):
            raise ValueError("Read-only JSON route paths must be unique.")
        if any(not path.startswith("/api/") for path in route_map):
            raise ValueError("Read-only JSON routes must use an /api/ path.")
        self._routes: Mapping[str, ReadOnlyJsonRoute] = route_map

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(self._routes)

    def dispatch(self, *, request_target: str, respond_json: JsonResponder) -> bool:
        parsed = urlparse(request_target)
        route = self._routes.get(parsed.path)
        if route is None:
            return False
        respond_json(route.load_payload())
        return True


def build_health_recovery_status_dispatch(
    *,
    status_loader: PayloadLoader,
    live_status_loader: PayloadLoader,
    decision_status_loader: PayloadLoader,
    server_health_loader: PayloadLoader,
    recovery_status_loader: PayloadLoader,
) -> ReadOnlyJsonRouteDispatch:
    loaders = (
        status_loader,
        live_status_loader,
        decision_status_loader,
        server_health_loader,
        recovery_status_loader,
    )
    routes = tuple(
        ReadOnlyJsonRoute(path=path, load_payload=loader)
        for path, loader in zip(HEALTH_RECOVERY_STATUS_GET_PATHS, loaders, strict=True)
    )
    return ReadOnlyJsonRouteDispatch(routes)
