from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from app.cockpit_readonly_routes import (
    HEALTH_RECOVERY_STATUS_GET_PATHS,
    ReadOnlyJsonRoute,
    ReadOnlyJsonRouteDispatch,
    build_health_recovery_status_dispatch,
)


class CockpitReadOnlyRouteTests(unittest.TestCase):
    def test_health_recovery_status_dispatch_registers_exact_paths(self) -> None:
        loaders = [
            MagicMock(return_value={"ok": True})
            for _path in HEALTH_RECOVERY_STATUS_GET_PATHS
        ]
        dispatch = build_health_recovery_status_dispatch(
            status_loader=loaders[0],
            live_status_loader=loaders[1],
            decision_status_loader=loaders[2],
            server_health_loader=loaders[3],
            recovery_status_loader=loaders[4],
        )

        self.assertEqual(dispatch.paths, HEALTH_RECOVERY_STATUS_GET_PATHS)

    def test_dispatch_calls_only_selected_loader_and_preserves_query_compatibility(self) -> None:
        loaders = [
            MagicMock(return_value={"ok": True, "path": path})
            for path in HEALTH_RECOVERY_STATUS_GET_PATHS
        ]
        dispatch = build_health_recovery_status_dispatch(
            status_loader=loaders[0],
            live_status_loader=loaders[1],
            decision_status_loader=loaders[2],
            server_health_loader=loaders[3],
            recovery_status_loader=loaders[4],
        )
        respond_json = MagicMock()

        handled = dispatch.dispatch(
            request_target="/api/server/health?ignored=kept-compatible",
            respond_json=respond_json,
        )

        self.assertTrue(handled)
        loaders[3].assert_called_once_with()
        for index, loader in enumerate(loaders):
            if index != 3:
                loader.assert_not_called()
        respond_json.assert_called_once_with({"ok": True, "path": "/api/server/health"})

    def test_dispatch_leaves_unknown_path_untouched(self) -> None:
        loader = MagicMock(return_value={"ok": True})
        dispatch = ReadOnlyJsonRouteDispatch(
            (ReadOnlyJsonRoute(path="/api/status", load_payload=loader),)
        )
        respond_json = MagicMock()

        handled = dispatch.dispatch(
            request_target="/api/other-status",
            respond_json=respond_json,
        )

        self.assertFalse(handled)
        loader.assert_not_called()
        respond_json.assert_not_called()

    def test_dispatch_rejects_duplicate_or_non_api_registration(self) -> None:
        loader = MagicMock(return_value={"ok": True})

        with self.assertRaises(ValueError):
            ReadOnlyJsonRouteDispatch(
                (
                    ReadOnlyJsonRoute(path="/api/status", load_payload=loader),
                    ReadOnlyJsonRoute(path="/api/status", load_payload=loader),
                )
            )
        with self.assertRaises(ValueError):
            ReadOnlyJsonRouteDispatch(
                (ReadOnlyJsonRoute(path="/status", load_payload=loader),)
            )


if __name__ == "__main__":
    unittest.main()
