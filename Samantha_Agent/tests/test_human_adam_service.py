from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.communication.human_adam_service import (
    CANONICAL_TVBCP_RELATIVE_PATH,
    HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
    HumanAdamService,
    human_adam_checkpoint_action,
    human_adam_connect_action,
    human_adam_send_action,
    human_adam_tvbcp_action,
    human_adam_work_review_action,
)


class FakeRuntime:
    def __init__(self, root: Path) -> None:
        self.socket_path = root / "app-server.sock"
        self.started = 0
        self.closed = 0
        self.reachable = False

    def status(self) -> dict[str, object]:
        return {
            "running": self.reachable,
            "reachable": self.reachable,
            "owned_by_cockpit": self.reachable,
            "socket_exists": self.reachable,
            "transport": "private_local_unix_socket",
        }

    def start(self) -> dict[str, object]:
        self.started += 1
        self.reachable = True
        return {**self.status(), "started": True}

    def close(self) -> None:
        self.closed += 1
        self.reachable = False


class FakeWorkspace:
    def __init__(self, root: Path) -> None:
        self.project_root = root
        self.sync_available = False
        self.dirty = False
        self.local_checkpoint_ahead = False
        self.last_checkpoint_message = ""

    def status(self) -> dict[str, object]:
        return {
            "ok": True,
            "prepared": True,
            "project_ready": True,
            "dirty": self.dirty,
            "change_count": 1 if self.dirty else 0,
            "changes": ([{"status": " M", "path": "Samantha_Agent/test.py"}] if self.dirty else []),
            "sync_available": self.sync_available,
            "source_update_available": self.sync_available,
            "workspace_relation": "local_ahead" if self.local_checkpoint_ahead else ("source_ahead" if self.sync_available else "aligned"),
            "local_checkpoint_ahead": self.local_checkpoint_ahead,
            "local_commit_count": 1 if self.local_checkpoint_ahead else 0,
            "remotes": [],
            "head": "abc123",
        }

    def review(self) -> dict[str, object]:
        status = self.status()
        return {
            "ok": True,
            "dirty": self.dirty,
            "changes": status["changes"],
            "change_count": status["change_count"],
            "checkpoint_changes": ([{"status": "M", "path": "Samantha_Agent/test.py"}] if self.local_checkpoint_ahead else []),
            "checkpoint_change_count": 1 if self.local_checkpoint_ahead else 0,
            "local_checkpoint_ahead": self.local_checkpoint_ahead,
            "local_commit_count": 1 if self.local_checkpoint_ahead else 0,
            "workspace_relation": status["workspace_relation"],
            "source_update_available": self.sync_available,
            "has_git_remote": False,
        }

    def checkpoint(self, *, confirmed: bool, message: str = "") -> dict[str, object]:
        if not confirmed:
            raise AppServerError("confirmation")
        self.last_checkpoint_message = message
        self.dirty = False
        self.local_checkpoint_ahead = True
        return {**self.status(), "checkpoint_created": True, "message": message or "WIP"}


class FakeHub:
    def __init__(self) -> None:
        self.model: str | None = None
        self.connected = False
        self.sent: list[dict[str, str]] = []
        self.closed = 0

    def snapshot(self) -> dict[str, object]:
        return {
            "thread_id": "canonical-thread",
            "connected": self.connected,
            "connection_state": "connected" if self.connected else "disconnected",
            "messages": [],
        }

    def connect(self) -> dict[str, object]:
        self.connected = True
        return self.snapshot()

    def send(self, *, text: str, client_message_id: str, client_sent_at: str) -> dict[str, object]:
        self.sent.append(
            {"text": text, "client_message_id": client_message_id, "client_sent_at": client_sent_at}
        )
        return {"ok": True, "entry": {"answer": "Hotovo", "delivery_confirmed": True}}

    def close(self) -> None:
        self.connected = False
        self.closed += 1


def fake_profile(**_kwargs: object) -> dict[str, object]:
    return {
        "model": "test-codex",
        "reasoning_effort": "high",
        "network_access": False,
        "approval_policy": "never",
    }


class HumanAdamServiceTests(unittest.TestCase):
    def make_service(self, root: Path) -> tuple[HumanAdamService, FakeRuntime, FakeWorkspace, FakeHub]:
        tvbcp_path = root / CANONICAL_TVBCP_RELATIVE_PATH
        tvbcp_path.parent.mkdir(parents=True, exist_ok=True)
        tvbcp_path.write_text("Kanonická smlouva\nBez citlivých textů.\n", encoding="utf-8")
        runtime = FakeRuntime(root)
        workspace = FakeWorkspace(root)
        hub = FakeHub()
        service = HumanAdamService(
            runtime=runtime,  # type: ignore[arg-type]
            workspace=workspace,  # type: ignore[arg-type]
            state_path=root / "state.json",
            profile_getter=fake_profile,
            hub=hub,  # type: ignore[arg-type]
        )
        return service, runtime, workspace, hub

    def test_developer_instructions_require_timestamped_tvbcp_append(self) -> None:
        self.assertIn("na konec souboru", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("YYYY-MM-DD HH:MM TZ", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)

    def test_status_has_no_process_start_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            status = service.status()

        self.assertTrue(status["ok"])
        self.assertEqual(runtime.started, 0)
        self.assertFalse(status["runtime"]["reachable"])

    def test_explicit_connect_starts_runtime_and_applies_high_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, runtime, _workspace, hub = self.make_service(Path(temp_dir))
            result = human_adam_connect_action(service=service)

        self.assertTrue(result["ok"])
        self.assertEqual(runtime.started, 1)
        self.assertTrue(hub.connected)
        self.assertEqual(hub.model, "test-codex")
        self.assertEqual(result["profile"]["reasoning_effort"], "high")

    def test_send_requires_explicit_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, hub = self.make_service(Path(temp_dir))
            result = human_adam_send_action(
                {
                    "message": "Test",
                    "client_message_id": "human-adam-message-0001",
                    "client_sent_at": "2026-07-14T08:00:00Z",
                },
                service=service,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "human_adam_send_failed")
        self.assertEqual(hub.sent, [])

    def test_connected_send_returns_confirmed_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, hub = self.make_service(Path(temp_dir))
            service.connect()
            result = human_adam_send_action(
                {
                    "message": "Proveď kontrolu",
                    "client_message_id": "human-adam-message-0002",
                    "client_sent_at": "2026-07-14T08:01:00Z",
                },
                service=service,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(hub.sent[0]["text"], "Proveď kontrolu")
        self.assertEqual(result["session"]["thread_id"], "canonical-thread")

    def test_outdated_isolated_workspace_blocks_connect_before_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, runtime, workspace, _hub = self.make_service(Path(temp_dir))
            workspace.sync_available = True
            with self.assertRaises(AppServerError):
                service.connect()

        self.assertEqual(runtime.started, 0)

    def test_tvbcp_reads_only_the_fixed_file_from_isolated_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            result = human_adam_tvbcp_action(service=service)

        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "isolated_workspace")
        self.assertEqual(result["relative_path"], CANONICAL_TVBCP_RELATIVE_PATH.as_posix())
        self.assertIn("Kanonická smlouva", result["content"])
        self.assertFalse(result["workspace_dirty"])

    def test_work_review_lists_paths_without_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, workspace, _hub = self.make_service(Path(temp_dir))
            workspace.dirty = True
            result = human_adam_work_review_action(service=service)

        self.assertTrue(result["ok"])
        self.assertEqual(result["change_count"], 1)
        self.assertEqual(result["changes"][0]["path"], "Samantha_Agent/test.py")
        self.assertNotIn("content", result["changes"][0])

    def test_checkpoint_requires_confirmation_and_keeps_local_wip_usable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, workspace, _hub = self.make_service(Path(temp_dir))
            workspace.dirty = True
            rejected = human_adam_checkpoint_action({"confirmed": False}, service=service)
            missing_name = human_adam_checkpoint_action(
                {"confirmed": True, "message": "   "},
                service=service,
            )
            created = human_adam_checkpoint_action(
                {"confirmed": True, "message": "  Remote   UI WIP  "},
                service=service,
            )

        self.assertEqual(rejected["status"], "confirmation_required")
        self.assertEqual(missing_name["status"], "human_adam_checkpoint_failed")
        self.assertTrue(created["ok"])
        self.assertTrue(created["checkpoint_created"])
        self.assertEqual(workspace.last_checkpoint_message, "Remote UI WIP")
        self.assertTrue(created["work"]["local_checkpoint_ahead"])
        self.assertTrue(created["status"]["ok"])


if __name__ == "__main__":
    unittest.main()
