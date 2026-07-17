from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.communication.human_adam_profiles import (
    HumanAdamProfileManager,
    human_adam_profile_switch_action,
)
from app.communication.human_adam_service import HumanAdamService


class FakeRuntime:
    def __init__(self, root: Path) -> None:
        self.socket_path = root / "app-server.sock"
        self.reachable = False

    def status(self) -> dict[str, object]:
        return {"reachable": self.reachable, "running": self.reachable}

    def start(self) -> dict[str, object]:
        self.reachable = True
        return self.status()

    def close(self) -> None:
        self.reachable = False


class FakeWorkspace:
    def __init__(self, root: Path, *, prepared: bool = True) -> None:
        self.project_root = root
        self.prepared = prepared
        self.dirty = False
        self.local_ahead = False
        self.source_ahead = False
        self.diverged = False
        self.prepare_count = 0
        self.sync_count = 0

    def status(self) -> dict[str, object]:
        relation = "diverged" if self.diverged else ("local_ahead" if self.local_ahead else ("source_ahead" if self.source_ahead else "aligned"))
        return {
            "ok": True,
            "prepared": self.prepared,
            "project_ready": self.prepared,
            "dirty": self.dirty,
            "change_count": 1 if self.dirty else 0,
            "changes": [{"status": " M", "path": "Samantha_Agent/app.py"}] if self.dirty else [],
            "source_update_available": self.source_ahead,
            "sync_available": self.source_ahead,
            "workspace_relation": relation,
            "local_checkpoint_ahead": self.local_ahead,
            "local_commit_count": 1 if self.local_ahead else 0,
            "remotes": [],
            "source_pending_changes": 0,
            "source_head": "a" * 40,
            "head": "b" * 40 if self.local_ahead else "a" * 40,
        }

    def prepare(self) -> dict[str, object]:
        self.prepared = True
        self.prepare_count += 1
        return self.status()

    def sync_from_main(self, *, confirmed: bool) -> dict[str, object]:
        if not confirmed:
            raise AssertionError("sync must be confirmed")
        self.source_ahead = False
        self.sync_count += 1
        return self.status()

    def review(self) -> dict[str, object]:
        return {"ok": True, "dirty": self.dirty, "changes": [], "change_count": 0}

    def checkpoint(self, **_kwargs: object) -> dict[str, object]:
        return {**self.status(), "checkpoint_created": False, "message": "Není co checkpointovat."}


class FakeHub:
    def __init__(self, thread_id: str) -> None:
        self.thread_id = thread_id
        self.model: str | None = None
        self.connected = False
        self.turn_busy = False
        self.active_turn: dict[str, object] | None = None
        self.messages: list[dict[str, object]] = []
        self.close_count = 0

    def snapshot(self) -> dict[str, object]:
        return {
            "thread_id": self.thread_id,
            "connected": self.connected,
            "turn_busy": self.turn_busy,
            "active_turn": self.active_turn,
            "messages": list(self.messages),
        }

    def connect(self) -> dict[str, object]:
        self.connected = True
        return self.snapshot()

    def send(self, **_kwargs: object) -> dict[str, object]:
        return {"ok": True, "entry": {"answer": "Hotovo"}}

    def close(self) -> None:
        self.connected = False
        self.close_count += 1


def fake_profile(**_kwargs: object) -> dict[str, object]:
    return {"model": "test-codex", "reasoning_effort": "high"}


class HumanAdamProfileManagerTests(unittest.TestCase):
    def make_manager(self, root: Path, *, target_prepared: bool = True):
        runtime = FakeRuntime(root)
        human_workspace = FakeWorkspace(root / "human")
        library_workspace = FakeWorkspace(root / "library", prepared=target_prepared)
        human_hub = FakeHub("human-thread")
        library_hub = FakeHub("library-thread")
        human = HumanAdamService(
            runtime=runtime,  # type: ignore[arg-type]
            workspace=human_workspace,  # type: ignore[arg-type]
            state_path=root / "human.json",
            context_anchor_path=root / "human-anchor.json",
            deployment_receipt_path=root / "human-receipt.json",
            hub=human_hub,  # type: ignore[arg-type]
            profile_getter=fake_profile,
        )
        library = HumanAdamService(
            runtime=runtime,  # type: ignore[arg-type]
            workspace=library_workspace,  # type: ignore[arg-type]
            state_path=root / "library.json",
            context_anchor_path=root / "library-anchor.json",
            deployment_receipt_path=root / "library-receipt.json",
            hub=library_hub,  # type: ignore[arg-type]
            profile_getter=fake_profile,
            tvbcp_relative_path=Path("memory/tvbcp/knihovna_cockpit.txt"),
            tvbcp_title="Knihovna v Cockpitu",
        )
        manager = HumanAdamProfileManager(
            profiles={
                "human_adam": {"label": "Human–Adam", "description": "Původní", "service": human},
                "knihovna": {"label": "Knihovna", "description": "Nový profil", "service": library},
            },
            default_profile_id="human_adam",
            state_path=root / "active-profile.json",
            runtime=runtime,  # type: ignore[arg-type]
        )
        return manager, human_workspace, library_workspace, human_hub, library_hub

    def test_status_advertises_two_profiles_without_changing_original_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, _human_hub, _library_hub = self.make_manager(Path(temp_dir))
            status = manager.status()

        self.assertEqual(status["work_profile"]["id"], "human_adam")
        self.assertEqual([item["id"] for item in status["work_profiles"]], ["human_adam", "knihovna"])
        self.assertEqual(status["work_profiles"][1]["tvbcp_title"], "Knihovna v Cockpitu")

    def test_switch_requires_confirmation_and_preserves_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            result = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": False},
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_switch_prepares_target_and_persists_profile_without_thread_mix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, _human_workspace, library_workspace, human_hub, library_hub = self.make_manager(root, target_prepared=False)
            human_hub.connected = True
            result = manager.switch(profile_id="knihovna", confirmed=True)
            persisted = json.loads((root / "active-profile.json").read_text(encoding="utf-8"))

        self.assertTrue(result["ok"])
        self.assertTrue(result["switched"])
        self.assertEqual(result["work_profile"]["id"], "knihovna")
        self.assertEqual(result["session"]["thread_id"], "library-thread")
        self.assertEqual(library_workspace.prepare_count, 1)
        self.assertEqual(human_hub.close_count, 1)
        self.assertTrue(library_hub.connected)
        self.assertEqual(persisted["active_profile_id"], "knihovna")
        self.assertNotIn("thread", str(persisted))

    def test_context_anchor_is_isolated_per_work_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = self.make_manager(Path(temp_dir))
            human_hub.connected = True
            saved = manager.set_context_anchor(
                operation="save",
                content="Cíl: Human–Adam kontinuita",
                confirmed=True,
            )
            pinned = manager.set_context_anchor(operation="pin", confirmed=True)
            manager.switch(profile_id="knihovna", confirmed=True)
            library_anchor = manager.context_anchor()
            manager.switch(profile_id="human_adam", confirmed=True)
            human_anchor = manager.context_anchor()

        self.assertFalse(saved["active"])
        self.assertTrue(saved["has_content"])
        self.assertTrue(pinned["active"])
        self.assertFalse(library_anchor["active"])
        self.assertFalse(library_anchor["has_content"])
        self.assertEqual(human_anchor["content"], "Cíl: Human–Adam kontinuita")

    def test_switch_rejects_dirty_checkpoint_and_uncertain_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = self.make_manager(Path(temp_dir))
            human_workspace.dirty = True
            dirty = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": True},
                service=manager,
            )
            human_workspace.dirty = False
            human_workspace.local_ahead = True
            checkpoint = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": True},
                service=manager,
            )
            human_workspace.local_ahead = False
            human_hub.messages = [{"status": "delivery_unknown", "recovery_required": True}]
            uncertain = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": True},
                service=manager,
            )

        self.assertFalse(dirty["ok"])
        self.assertIn("necheckpointované", dirty["message"])
        self.assertFalse(checkpoint["ok"])
        self.assertIn("WIP checkpoint", checkpoint["message"])
        self.assertFalse(uncertain["ok"])
        self.assertIn("nejisté doručení", uncertain["message"])
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_switch_safely_fast_forwards_clean_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, _human_hub, _library_hub = self.make_manager(Path(temp_dir))
            library_workspace.source_ahead = True
            result = manager.switch(profile_id="knihovna", confirmed=True)

        self.assertTrue(result["ok"])
        self.assertEqual(library_workspace.sync_count, 1)
        self.assertFalse(library_workspace.source_ahead)
