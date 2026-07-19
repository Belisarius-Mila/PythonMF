from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.communication.human_adam_profiles import (
    HumanAdamProfileManager,
    human_adam_development_semaphore_action,
    human_adam_profile_switch_action,
    human_adam_project_continuity_action,
)
from app.communication.human_adam_service import (
    THREAD_ROTATION_CONFIRMATION_TEXT,
    HumanAdamService,
)
from app.communication.session_hub import SessionBusyError
from app.codex_appserver import AppServerError
from app.project_continuity import ProjectContinuityService


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
        self.checkpoint_subject = ""
        self.checkpoint_path = "Samantha_Agent/app.py"

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
        review: dict[str, object] = {
            "ok": True,
            "dirty": self.dirty,
            "changes": [],
            "change_count": 0,
            "local_checkpoint_ahead": self.local_ahead,
            "local_commit_count": 1 if self.local_ahead else 0,
            "checkpoint_changes": (
                [{"status": "M", "path": self.checkpoint_path}] if self.local_ahead else []
            ),
            "checkpoint_change_count": 1 if self.local_ahead else 0,
            "checkpoint_head": "b" * 40 if self.local_ahead else "",
            "checkpoint_subject": self.checkpoint_subject if self.local_ahead else "",
        }
        return review

    def checkpoint(self, **kwargs: object) -> dict[str, object]:
        if not self.dirty:
            return {**self.status(), "checkpoint_created": False, "message": "Není co checkpointovat."}
        self.checkpoint_subject = str(kwargs.get("message") or "WIP")
        self.dirty = False
        self.local_ahead = True
        return {**self.status(), "checkpoint_created": True, "message": "Checkpoint vytvořen."}


class FakeHub:
    def __init__(self, thread_id: str) -> None:
        self.thread_id = thread_id
        self.model: str | None = None
        self.connected = False
        self.turn_busy = False
        self.active_turn: dict[str, object] | None = None
        self.messages: list[dict[str, object]] = []
        self.last_send: dict[str, object] = {}
        self.close_count = 0
        self.rotation_count = 0

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

    def send(self, **kwargs: object) -> dict[str, object]:
        self.last_send = dict(kwargs)
        return {"ok": True, "entry": {"answer": "Hotovo"}}

    def rotation_status(self) -> dict[str, object]:
        blockers = []
        if self.turn_busy or self.active_turn:
            blockers.append("Vlákno nelze rotovat během aktivního tahu.")
        return {
            "ok": True,
            "ready": not blockers,
            "thread_id": self.thread_id,
            "thread_message_count": len(self.messages),
            "rotation_count": self.rotation_count,
            "blockers": blockers,
        }

    def rotate_thread(self, *, expected_thread_id: str) -> dict[str, object]:
        if expected_thread_id != self.thread_id:
            raise AppServerError("stale thread")
        previous = self.thread_id
        self.thread_id = f"{previous}-rotated"
        self.rotation_count += 1
        return {
            "ok": True,
            "rotated": True,
            "previous_thread_id": previous,
            "thread_id": self.thread_id,
            "rotation_count": self.rotation_count,
        }

    def close(self) -> None:
        self.connected = False
        self.close_count += 1


def fake_profile(**_kwargs: object) -> dict[str, object]:
    return {"model": "test-codex", "reasoning_effort": "high"}


class HumanAdamProfileManagerTests(unittest.TestCase):
    def make_manager(
        self,
        root: Path,
        *,
        target_prepared: bool = True,
        project_continuity: ProjectContinuityService | None = None,
    ):
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
            work_profile_id="human_adam",
            hub=human_hub,  # type: ignore[arg-type]
            profile_getter=fake_profile,
        )
        library = HumanAdamService(
            runtime=runtime,  # type: ignore[arg-type]
            workspace=library_workspace,  # type: ignore[arg-type]
            state_path=root / "library.json",
            context_anchor_path=root / "library-anchor.json",
            deployment_receipt_path=root / "library-receipt.json",
            work_profile_id="knihovna",
            hub=library_hub,  # type: ignore[arg-type]
            profile_getter=fake_profile,
            tvbcp_relative_path=Path("memory/tvbcp/knihovna_cockpit.txt"),
            tvbcp_title="Knihovna v Cockpitu",
        )
        manager = HumanAdamProfileManager(
            profiles={
                "human_adam": {
                    "label": "Human–Adam",
                    "description": "Původní",
                    "default_project_name": "Testovací projekt",
                    "service": human,
                },
                "knihovna": {
                    "label": "Knihovna",
                    "description": "Nový profil",
                    "service": library,
                },
            },
            default_profile_id="human_adam",
            state_path=root / "active-profile.json",
            runtime=runtime,  # type: ignore[arg-type]
            project_continuity=project_continuity,
        )
        return manager, human_workspace, library_workspace, human_hub, library_hub

    @staticmethod
    def make_project_continuity(root: Path) -> tuple[ProjectContinuityService, str, str]:
        handoff_path = "memory/handoffs/test_project.md"
        (root / "memory/handoffs").mkdir(parents=True)
        (root / "memory/tvbcp").mkdir(parents=True)
        (root / "memory/ACTIVE_PROJECTS.md").write_text(
            """| Oblast | Priorita | Rezim | Stav | Memory soubor | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- |
| Testovací projekt | 1 | active | Rozpracováno | `memory/tvbcp/test_project.txt` | `memory/handoffs/test_project.md` | Pokračovat. |
""",
            encoding="utf-8",
        )
        (root / handoff_path).write_text("Aktuální handoff\n", encoding="utf-8")
        (root / "memory/tvbcp/test_project.txt").write_text("TVBCP\n", encoding="utf-8")
        workspace_handoff = root / "human" / handoff_path
        workspace_handoff.parent.mkdir(parents=True)
        workspace_handoff.write_text("Aktuální handoff\n", encoding="utf-8")
        workspace_tvbcp = root / "human/memory/tvbcp/test_project.txt"
        workspace_tvbcp.parent.mkdir(parents=True)
        workspace_tvbcp.write_text("TVBCP\n", encoding="utf-8")
        workspace_handoff.write_text("Aktuální handoff\n", encoding="utf-8")
        service = ProjectContinuityService(project_root=root)
        return service, service.catalog()[0].project_id, handoff_path

    def test_status_advertises_two_profiles_without_changing_original_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, _human_hub, _library_hub = self.make_manager(Path(temp_dir))
            status = manager.status()

        self.assertEqual(status["work_profile"]["id"], "human_adam")
        self.assertEqual([item["id"] for item in status["work_profiles"]], ["human_adam", "knihovna"])
        self.assertEqual(status["work_profiles"][1]["tvbcp_title"], "Knihovna v Cockpitu")
        self.assertEqual(manager.work_profile_id, "human_adam")
        self.assertTrue(status["development_semaphore"]["ok"])
        self.assertFalse(status["development_semaphore"]["active"])
        self.assertTrue(status["development_semaphore"]["can_acquire_profile"])

    def test_project_binding_is_required_when_catalog_exists_and_audit_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, *_rest = self.make_manager(root, project_continuity=continuity)
            with self.assertRaisesRegex(AppServerError, "Vyber projekt"):
                manager.change_development_semaphore(
                    operation="acquire_profile",
                    expected_revision=0,
                    topic="Projektová kontinuita",
                    confirmed=True,
                )
            acquired = manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Projektová kontinuita",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            status = human_adam_project_continuity_action(service=manager)

        self.assertEqual(acquired["project_id"], project_id)
        self.assertEqual(acquired["handoff_path"], handoff_path)
        self.assertTrue(status["read_only"])
        self.assertFalse(status["blocking"])
        self.assertEqual(status["audit"]["state"], "current")

    def test_terminal_binding_is_conservatively_unverifiable_without_registered_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, *_rest = self.make_manager(root, project_continuity=continuity)
            manager.change_development_semaphore(
                operation="acquire_terminal",
                expected_revision=0,
                topic="Terminálový WIP",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            status = manager.project_continuity_status()

        self.assertEqual(status["audit"]["state"], "unverifiable")
        self.assertIn("nezná přesný pracovní strom", status["audit"]["message"])
        self.assertFalse(status["audit"]["blocking"])

    def test_successful_checkpoint_returns_read_only_handoff_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, human_workspace, *_rest = self.make_manager(root, project_continuity=continuity)
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Návrh handoffu po checkpointu",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            human_workspace.dirty = True
            before = (root / handoff_path).read_text(encoding="utf-8")
            checkpoint = manager.checkpoint(confirmed=True, message="WIP s návrhem")
            after = (root / handoff_path).read_text(encoding="utf-8")

        proposal = checkpoint["work"]["handoff_proposal"]
        self.assertTrue(checkpoint["checkpoint_created"])
        self.assertTrue(proposal["available"])
        self.assertEqual(proposal["state"], "ready")
        self.assertFalse(proposal["writes_performed"])
        self.assertEqual(before, after)
        self.assertIn("WIP s návrhem", proposal["draft"])

    def test_handoff_proposal_failure_does_not_undo_successful_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, human_workspace, *_rest = self.make_manager(root, project_continuity=continuity)
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Fail-closed návrh",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            human_workspace.dirty = True
            human_workspace.checkpoint_path = "Samantha_Agent/data/private/secret.txt"
            checkpoint = manager.checkpoint(confirmed=True, message="WIP zůstává platný")

        proposal = checkpoint["work"]["handoff_proposal"]
        self.assertTrue(checkpoint["checkpoint_created"])
        self.assertEqual(proposal["state"], "unverifiable")
        self.assertFalse(proposal["available"])

    def test_takeover_handoff_check_uses_owned_project_binding_and_is_warning_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, *_rest = self.make_manager(root, project_continuity=continuity)
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Kontrola převzetí",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            verified = manager.takeover_handoff_check(
                deployment_audit={
                    "ok": True,
                    "ready": True,
                    "changes": [{"status": "M", "path": f"human/{handoff_path}"}],
                }
            )
            warning = manager.takeover_handoff_check(
                deployment_audit={
                    "ok": True,
                    "ready": True,
                    "changes": [{"status": "M", "path": "human/app/example.py"}],
                }
            )

        self.assertEqual(verified["state"], "verified")
        self.assertTrue(verified["handoff_in_checkpoint"])
        self.assertEqual(warning["state"], "warning")
        self.assertFalse(warning["blocking"])
        self.assertFalse(warning["writes_performed"])

    def test_checkpoint_requires_active_owned_lease_and_pause_blocks_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            human_workspace.dirty = True
            with self.assertRaisesRegex(AppServerError, "převezmi globální"):
                manager.checkpoint(confirmed=True, message="WIP")
            acquired = manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Semafor",
                confirmed=True,
            )
            checkpoint = manager.checkpoint(confirmed=True, message="WIP")
            paused = manager.change_development_semaphore(
                operation="pause",
                expected_revision=int(acquired["revision"]),
                topic="",
                confirmed=True,
            )
            with self.assertRaisesRegex(AppServerError, "pozastavený"):
                manager.checkpoint(confirmed=True, message="WIP")

        self.assertIn("checkpoint_created", checkpoint)
        self.assertEqual(paused["mode"], "paused")
        self.assertFalse(paused["can_checkpoint"])

    def test_terminal_owner_blocks_profile_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            acquired = manager.change_development_semaphore(
                operation="acquire_terminal",
                expected_revision=0,
                topic="Terminálová změna",
                confirmed=True,
            )
            human_workspace.dirty = True
            with self.assertRaisesRegex(AppServerError, "Terminálový Adam"):
                manager.checkpoint(confirmed=True, message="Cizí WIP")

        self.assertEqual(acquired["owner_id"], "terminal")
        self.assertFalse(acquired["can_checkpoint"])

    def test_foreign_profile_wip_blocks_deployment_and_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, *_rest = self.make_manager(Path(temp_dir))
            acquired = manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Human změna",
                confirmed=True,
            )
            library_workspace.dirty = True
            status = manager.development_status()
            with self.assertRaisesRegex(AppServerError, "cizí WIP"):
                manager.assert_deployment_allowed("human_adam")
            release = human_adam_development_semaphore_action(
                {
                    "operation": "release",
                    "expected_revision": acquired["revision"],
                    "topic": "",
                    "confirmed": True,
                },
                service=manager,
            )

        self.assertFalse(status["can_deploy"])
        self.assertFalse(status["can_release"])
        self.assertFalse(release["ok"])
        self.assertIn("neuzavřený WIP", release["message"])

    def test_send_injects_fail_closed_read_only_or_writable_control(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = self.make_manager(Path(temp_dir))
            manager.connect()
            manager.send(text="Jen analyzuj", client_message_id="read-only")
            read_only_input = str(human_hub.last_send["model_input_text"])
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Povolený vývoj",
                confirmed=True,
            )
            manager.send(text="Proveď změnu", client_message_id="writable")
            writable_input = str(human_hub.last_send["model_input_text"])

        self.assertIn("[DEVELOPMENT_CONTROL]", read_only_input)
        self.assertIn("lease_state=free", read_only_input)
        self.assertIn("writable=false", read_only_input)
        self.assertIn("lease_owner_id=human_adam", writable_input)
        self.assertIn("writable=true", writable_input)

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
        self.assertEqual(manager.work_profile_id, "knihovna")
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
                expected_revision=0,
                content="Cíl: Human–Adam kontinuita",
                confirmed=True,
            )
            pinned = manager.set_context_anchor(
                operation="pin",
                expected_revision=saved["revision"],
                confirmed=True,
            )
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

    def test_thread_rotation_is_locked_to_active_profile_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            saved = manager.set_context_anchor(
                operation="save",
                expected_revision=0,
                content="Cíl: bezpečně pokračovat v novém vlákně",
                confirmed=True,
            )
            manager.set_context_anchor(
                operation="pin",
                expected_revision=saved["revision"],
                confirmed=True,
            )
            manager.connect()
            audit = manager.thread_rotation_status()
            result = manager.rotate_thread(
                confirmation=THREAD_ROTATION_CONFIRMATION_TEXT,
                expected_thread_id="human-thread",
            )

        self.assertTrue(audit["ready"])
        self.assertEqual(result["previous_thread_id"], "human-thread")
        self.assertEqual(human_hub.thread_id, "human-thread-rotated")
        self.assertEqual(library_hub.thread_id, "library-thread")

    def test_thread_rotation_audit_respects_profile_operation_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            with manager.profile_operation():
                with self.assertRaises(SessionBusyError):
                    manager.thread_rotation_status()

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

    def test_confirmed_turn_after_historical_uncertainty_allows_profile_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = self.make_manager(Path(temp_dir))
            human_hub.messages = [
                {"status": "delivery_unknown", "recovery_required": True},
                {"status": "completed", "recovery_required": False},
            ]

            result = manager.switch(profile_id="knihovna", confirmed=True)

        self.assertTrue(result["ok"])
        self.assertTrue(result["switched"])
        self.assertEqual(manager.active_profile_id, "knihovna")

    def test_new_uncertainty_after_last_confirmed_turn_still_blocks_profile_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = self.make_manager(Path(temp_dir))
            human_hub.messages = [
                {"status": "completed", "recovery_required": False},
                {"status": "delivery_unknown", "recovery_required": True},
            ]

            result = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": True},
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertIn("nejisté doručení", result["message"])
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_switch_safely_fast_forwards_clean_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, _human_hub, _library_hub = self.make_manager(Path(temp_dir))
            library_workspace.source_ahead = True
            result = manager.switch(profile_id="knihovna", confirmed=True)

        self.assertTrue(result["ok"])
        self.assertEqual(library_workspace.sync_count, 1)
        self.assertFalse(library_workspace.source_ahead)

    def test_connect_safely_fast_forwards_clean_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            human_workspace.source_ahead = True

            result = manager.connect()

        self.assertTrue(result["ok"])
        self.assertTrue(result["workspace_synced"])
        self.assertEqual(result["work_profile"]["id"], "human_adam")
        self.assertEqual(result["session"]["thread_id"], "human-thread")
        self.assertEqual(human_workspace.sync_count, 1)
        self.assertFalse(human_workspace.source_ahead)
        self.assertTrue(human_hub.connected)

    def test_connect_does_not_sync_unsafe_active_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            human_workspace.source_ahead = True
            human_workspace.dirty = True

            with self.assertRaises(AppServerError):
                manager.connect()

        self.assertEqual(human_workspace.sync_count, 0)
        self.assertFalse(human_hub.connected)

    def test_connect_does_not_sync_active_workspace_during_uncertain_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            human_workspace.source_ahead = True
            human_hub.messages = [{"status": "delivery_unknown", "recovery_required": True}]

            with self.assertRaises(SessionBusyError):
                manager.connect()

        self.assertEqual(human_workspace.sync_count, 0)
        self.assertFalse(human_hub.connected)
