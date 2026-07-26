from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.communication.human_adam_profiles import (
    HumanAdamProfileManager,
    KNIHOVNA_DEVELOPER_INSTRUCTIONS,
    human_adam_deferred_integration_action,
    human_adam_development_semaphore_action,
    human_adam_development_semaphore_status_action,
    human_adam_owned_wip_recovery_action,
    human_adam_profile_switch_action,
    human_adam_project_continuity_action,
    private_archive_root,
    workstream_sandbox_policy,
)
from app.communication.deferred_integration import (
    DEFERRED_INTEGRATION_CONFIRMATION,
    OWNED_WIP_MISSING_METADATA,
    OWNED_WIP_RECOVERY_CONFIRMATION,
    READY_FOR_CONFIRMED_INTEGRATION,
    DeferredIntegrationError,
)
from app.communication.human_adam_turn_completion import TurnCompletionMetadata
from app.communication.human_adam_workstream_catalog import WORKSTREAM_CATALOG
from app.communication.human_adam_operations import (
    FAMILY_CALENDAR_TEST_EMAIL_PREVIEW,
    OPERATION_MARKER_END,
    OPERATION_MARKER_START,
)
from app.communication.human_adam_service import (
    THREAD_ROTATION_CONFIRMATION_TEXT,
    HumanAdamService,
    human_adam_status_action,
)
from app.communication.human_adam_workstream_memory import WorkstreamMemoryRegistry
from app.communication.session_hub import SessionBusyError
from app.codex_appserver import AppServerError
from app.project_continuity import ProjectContinuityService


class FakeRuntime:
    def __init__(self, root: Path) -> None:
        self.socket_path = root / "app-server.sock"
        self.reachable = False
        self.last_start_kwargs: dict[str, object] = {}

    def status(self) -> dict[str, object]:
        return {"reachable": self.reachable, "running": self.reachable}

    def start(self, **kwargs: object) -> dict[str, object]:
        self.last_start_kwargs = dict(kwargs)
        self.reachable = True
        return self.status()

    def close(self) -> None:
        self.reachable = False


class FakeWorkspace:
    def __init__(self, root: Path, *, prepared: bool = True) -> None:
        self.project_root = root
        self.workspace_root = root
        self.source_repo = root.parent
        self.prepared = prepared
        self.dirty = False
        self.local_ahead = False
        self.source_ahead = False
        self.diverged = False
        self.prepare_count = 0
        self.sync_count = 0
        self.source_pending_changes = 0
        self.checkpoint_subject = ""
        self.checkpoint_path = "Samantha_Agent/app.py"

    def status(self) -> dict[str, object]:
        relation = "diverged" if self.diverged else ("local_ahead" if self.local_ahead else ("source_ahead" if self.source_ahead else "aligned"))
        return {
            "ok": True,
            "prepared": self.prepared,
            "project_ready": self.prepared,
            "branch": "main",
            "source_branch": "main",
            "dirty": self.dirty,
            "change_count": 1 if self.dirty else 0,
            "changes": [{"status": " M", "path": "Samantha_Agent/app.py"}] if self.dirty else [],
            "source_update_available": self.source_ahead,
            "sync_available": self.source_ahead,
            "workspace_relation": relation,
            "local_checkpoint_ahead": self.local_ahead,
            "local_checkpoint_preserved": False,
            "local_commit_count": 1 if self.local_ahead else 0,
            "remotes": [],
            "source_pending_changes": self.source_pending_changes,
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
        relation = (
            "diverged"
            if self.diverged
            else (
                "local_ahead"
                if self.local_ahead
                else ("source_ahead" if self.source_ahead else "aligned")
            )
        )
        if not self.dirty:
            audit_state = "not_pending"
            service_decision = False
        elif self.diverged or self.local_ahead:
            audit_state = "blocked_workspace_history"
            service_decision = True
        elif self.source_pending_changes:
            audit_state = "waiting_source_clean"
            service_decision = False
        elif self.source_ahead:
            audit_state = "source_advanced_service_decision"
            service_decision = True
        else:
            audit_state = "ready_for_confirmed_integration"
            service_decision = False
        review: dict[str, object] = {
            "ok": True,
            "dirty": self.dirty,
            "changes": (
                [{"status": " M", "path": "Samantha_Agent/app.py"}]
                if self.dirty
                else []
            ),
            "change_count": 1 if self.dirty else 0,
            "source_pending_changes": self.source_pending_changes,
            "local_checkpoint_ahead": self.local_ahead,
            "local_checkpoint_preserved": False,
            "local_commit_count": 1 if self.local_ahead else 0,
            "checkpoint_changes": (
                [{"status": "M", "path": self.checkpoint_path}] if self.local_ahead else []
            ),
            "checkpoint_change_count": 1 if self.local_ahead else 0,
            "checkpoint_head": "b" * 40 if self.local_ahead else "",
            "checkpoint_subject": self.checkpoint_subject if self.local_ahead else "",
            "workspace_relation": relation,
            "pending_integration_audit": {
                "ok": True,
                "read_only": True,
                "writes_performed": False,
                "pending": self.dirty,
                "state": audit_state,
                "label": audit_state,
                "message": "Testovací audit.",
                "next_step": "Testovací další krok.",
                "requires_service_decision": service_decision,
                "overlap_count": 0,
                "overlap_paths": [],
            },
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
        self.next_answer = "Hotovo"
        self.on_send = None
        self.replaced_answers: list[tuple[str, str]] = []
        self.fail_connect = False

    def snapshot(self) -> dict[str, object]:
        return {
            "thread_id": self.thread_id,
            "connected": self.connected,
            "turn_busy": self.turn_busy,
            "active_turn": self.active_turn,
            "messages": list(self.messages),
        }

    def connect(self) -> dict[str, object]:
        if self.fail_connect:
            raise AppServerError("Simulované selhání legacy připojení.")
        self.connected = True
        return self.snapshot()

    def send(self, **kwargs: object) -> dict[str, object]:
        self.last_send = dict(kwargs)
        if callable(self.on_send):
            self.on_send()
        return {
            "ok": True,
            "entry": {
                "client_message_id": str(kwargs.get("client_message_id") or ""),
                "status": "completed",
                "delivery_confirmed": True,
                "answer": self.next_answer,
            },
        }

    def replace_completed_answer(
        self,
        *,
        client_message_id: str,
        answer: str,
    ) -> dict[str, object]:
        self.replaced_answers.append((client_message_id, answer))
        return {
            "client_message_id": client_message_id,
            "status": "completed",
            "answer": answer,
        }

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


class FakeLazyThreads:
    def __init__(self, state_root: Path) -> None:
        self.state_root = Path(state_root)
        self.active_workstream_id = ""
        self.fail_open_ids: set[str] = set()
        self.busy = False
        self.uncertain = False
        self.open_calls: list[str] = []
        self.close_calls: list[str] = []
        self.restore_calls: list[str] = []
        self.hubs = {
            "project-mmtx": FakeHub("mmtx-thread"),
            "project-family-calendar": FakeHub("family-calendar-thread"),
            "project-lekarna": FakeHub("lekarna-thread"),
        }

    def status(self) -> dict[str, object]:
        ids = ("project-mmtx", "project-family-calendar", "project-lekarna")
        return {
            "ok": True,
            "active_workstream_id": self.active_workstream_id,
            "workstreams": [
                {
                    "id": workstream_id,
                    "available": True,
                    "initialized": workstream_id in self.open_calls,
                    "connected": workstream_id == self.active_workstream_id,
                }
                for workstream_id in ids
            ],
        }

    def checkpoint_workstream_id(self) -> str:
        if not self.active_workstream_id:
            raise AppServerError("Není připojený žádný lazy pracovní proud.")
        if self.busy:
            raise SessionBusyError("Checkpoint nelze spustit během aktivního tahu Adama.")
        if self.uncertain:
            raise SessionBusyError("Checkpoint blokuje nejisté doručení.")
        return self.active_workstream_id

    def active_hub(self, *, expected_workstream_id: str = "") -> FakeHub:
        if not self.active_workstream_id:
            raise AppServerError("Není připojený žádný lazy pracovní proud.")
        if expected_workstream_id and expected_workstream_id != self.active_workstream_id:
            raise AppServerError("Aktivní lazy pracovní proud se mezitím změnil.")
        return self.hubs[self.active_workstream_id]

    def restore_active(self, *, workstream_id: str) -> dict[str, object]:
        self.restore_calls.append(workstream_id)
        self.active_workstream_id = workstream_id
        return {"ok": True, "restored": True}

    def open(self, *, workstream_id: str, confirmed: bool) -> dict[str, object]:
        if not confirmed:
            raise AssertionError("lazy open must be confirmed")
        self.open_calls.append(workstream_id)
        if workstream_id in self.fail_open_ids:
            raise AppServerError("Simulované selhání lazy připojení.")
        if self.active_workstream_id:
            self.hubs[self.active_workstream_id].close()
        self.active_workstream_id = workstream_id
        self.hubs[workstream_id].connect()
        return {"ok": True, "opened": True}

    def close_active(self, *, confirmed: bool) -> dict[str, object]:
        if not confirmed:
            raise AssertionError("lazy close must be confirmed")
        workstream_id = self.checkpoint_workstream_id()
        self.close_calls.append(workstream_id)
        self.hubs[workstream_id].close()
        self.active_workstream_id = ""
        return {"ok": True, "closed": True, "workstream_id": workstream_id}


def fake_profile(**_kwargs: object) -> dict[str, object]:
    return {"model": "test-codex", "reasoning_effort": "high"}


def workstream_capabilities(workstream_id: str):
    return next(
        record.capabilities
        for record in WORKSTREAM_CATALOG
        if record.workstream_id == workstream_id
    )


class HumanAdamProfileManagerTests(unittest.TestCase):
    def make_manager(
        self,
        root: Path,
        *,
        target_prepared: bool = True,
        project_continuity: ProjectContinuityService | None = None,
        workstream_threads=None,
    ):
        runtime = FakeRuntime(root)
        human_workspace = FakeWorkspace(root / "human")
        library_workspace = FakeWorkspace(root / "library", prepared=target_prepared)
        human_hub = FakeHub("human-thread")
        library_hub = FakeHub("library-thread")
        library_capabilities = workstream_capabilities("project-knowledge-library")
        human = HumanAdamService(
            runtime=runtime,  # type: ignore[arg-type]
            workspace=human_workspace,  # type: ignore[arg-type]
            state_path=root / "human.json",
            work_profile_id="human_adam",
            hub=human_hub,  # type: ignore[arg-type]
            profile_getter=fake_profile,
        )
        library = HumanAdamService(
            runtime=runtime,  # type: ignore[arg-type]
            workspace=library_workspace,  # type: ignore[arg-type]
            state_path=root / "library.json",
            work_profile_id="knihovna",
            hub=library_hub,  # type: ignore[arg-type]
            profile_getter=fake_profile,
            developer_instructions=KNIHOVNA_DEVELOPER_INSTRUCTIONS,
            sandbox_policy=workstream_sandbox_policy(library_capabilities),
            tvbcp_relative_path=Path("memory/tvbcp/knihovna_cockpit.txt"),
            tvbcp_title="Knihovna v Cockpitu",
        )
        manager = HumanAdamProfileManager(
            profiles={
                "human_adam": {
                    "label": "Human–Adam",
                    "description": "Původní",
                    "default_project_name": "Testovací projekt",
                    "workstream": {
                        "id": "layer-human-adam-development",
                        "type": "Layer",
                        "name": "Human–Adam / vývojové prostředí",
                        "handoff": "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
                        "tvbcp": "memory/tvbcp/architektura_komunikace_samantha.txt",
                    },
                    "service": human,
                },
                "knihovna": {
                    "label": "Knihovna",
                    "description": "Nový profil",
                    "workstream": {
                        "id": "project-knowledge-library",
                        "type": "Project",
                        "name": "Knihovna",
                        "handoff": "memory/handoffs/knowledge_library_article_editing_2026_07_16.md",
                        "tvbcp": "memory/tvbcp/knihovna_cockpit.txt",
                    },
                    "service": library,
                },
            },
            default_profile_id="human_adam",
            state_path=root / "active-profile.json",
            runtime=runtime,  # type: ignore[arg-type]
            project_continuity=project_continuity,
            workstream_threads=workstream_threads,
            workstream_memory=WorkstreamMemoryRegistry(),
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

    def test_status_advertises_only_grouped_catalog_without_public_profile_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, _human_hub, _library_hub = self.make_manager(Path(temp_dir))
            status = human_adam_status_action(service=manager)  # type: ignore[arg-type]
            semaphore = human_adam_development_semaphore_status_action(service=manager)

        self.assertNotIn("work_profile", status)
        self.assertNotIn("work_profiles", status)
        self.assertTrue(
            all(
                "profile_id" not in row
                for row in status["workstream_selection"]["workstreams"]
            )
        )
        self.assertEqual(manager.work_profile_id, "human_adam")
        self.assertTrue(status["development_semaphore"]["ok"])
        self.assertFalse(status["development_semaphore"]["active"])
        self.assertTrue(status["development_semaphore"]["can_acquire_profile"])
        for payload in (semaphore, status["development_semaphore"]):
            self.assertNotIn("active_profile_id", payload)
            self.assertNotIn("active_profile_label", payload)
        self.assertTrue(status["workstream_selection"]["ok"])
        self.assertEqual(status["workstream_selection"]["workstream_count"], 30)
        self.assertEqual(
            [group["label"] for group in status["workstream_selection"]["groups"]],
            ["Projekty", "Tooly", "Vrstvy", "Ostatní"],
        )

    def test_development_status_error_payload_omits_public_profile_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            with patch.object(
                manager,
                "_development_workspace_rows",
                side_effect=AppServerError("Simulované selhání workspace auditu."),
            ):
                semaphore = human_adam_development_semaphore_status_action(service=manager)

        self.assertFalse(semaphore["ok"])
        self.assertNotIn("active_profile_id", semaphore)
        self.assertNotIn("active_profile_label", semaphore)

    def test_pending_integration_audit_classifies_source_and_foreign_wip_read_only(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )

            clean = manager.work_review()["pending_integration_audit"]
            human_workspace.dirty = True
            human_workspace.source_pending_changes = 1
            waiting = manager.work_review()["pending_integration_audit"]
            human_workspace.source_pending_changes = 0
            ready = manager.work_review()["pending_integration_audit"]
            human_workspace.source_ahead = True
            advanced = manager.work_review()["pending_integration_audit"]
            library_workspace.dirty = True
            blocked = manager.work_review()["pending_integration_audit"]

        self.assertEqual(clean["state"], "not_pending")
        self.assertEqual(waiting["state"], "waiting_source_clean")
        self.assertEqual(ready["state"], "blocked_ownership_unverified")
        self.assertFalse(ready["can_integrate"])
        self.assertEqual(advanced["state"], "source_advanced_service_decision")
        self.assertTrue(advanced["requires_service_decision"])
        self.assertEqual(blocked["state"], "blocked_foreign_wip")
        self.assertEqual(blocked["foreign_blocker_count"], 1)
        self.assertTrue(blocked["read_only"])
        self.assertFalse(blocked["writes_performed"])
        self.assertTrue(human_workspace.dirty)
        self.assertTrue(library_workspace.dirty)
        self.assertEqual(human_workspace.sync_count, 0)
        self.assertEqual(library_workspace.sync_count, 0)

    def test_pending_integration_requires_exact_marker_before_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            human_workspace.dirty = True
            human_workspace.source_pending_changes = 1
            manager.deferred_integration_store.save(
                workstream_id="layer-human-adam-development",
                workspace_status=human_workspace.status(),
                completion=TurnCompletionMetadata(
                    commit_message="Integrate deferred step",
                    summary="Odložený krok je hotový",
                    next_step="Potvrdit integraci",
                ),
            )
            human_workspace.source_pending_changes = 0

            ready = manager.work_review()["pending_integration_audit"]

        self.assertEqual(ready["state"], "ready_for_confirmed_integration")
        self.assertTrue(ready["ownership_marker_verified"])
        self.assertTrue(ready["can_integrate"])
        self.assertEqual(
            ready["confirmation_text"],
            DEFERRED_INTEGRATION_CONFIRMATION,
        )

    def test_compatibility_backends_preserve_both_existing_service_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, human_workspace, library_workspace, human_hub, library_hub = (
                self.make_manager(root)
            )
            human_service = manager.profiles["human_adam"]["service"]
            library_service = manager.profiles["knihovna"]["service"]

            self.assertIs(
                manager.workstream_backends.service(
                    "layer-human-adam-development",
                    lazy_service_factory=manager._lazy_service,
                ),
                human_service,
            )
            self.assertIs(manager.active_service, human_service)
            self.assertIs(manager.active_service.workspace, human_workspace)
            self.assertIs(manager.active_service.hub, human_hub)
            self.assertEqual(manager.active_service.state_path, root / "human.json")

            manager.switch(profile_id="knihovna", confirmed=True)

            self.assertIs(manager.active_service, library_service)
            self.assertIs(manager.active_service.workspace, library_workspace)
            self.assertIs(manager.active_service.hub, library_hub)
            self.assertEqual(manager.active_service.state_path, root / "library.json")
            self.assertEqual(
                manager.grouped_workstream_status()["active"]["backend"],
                "compatibility_adapter",
            )

    def test_legacy_profile_state_is_read_without_rewrite_then_migrated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state_path = root / "active-profile.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "active_profile_id": "knihovna",
                        "updated_at": "2026-07-20T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )

            manager, *_rest = self.make_manager(root)
            before = json.loads(state_path.read_text(encoding="utf-8"))
            result = manager.activate_grouped_workstream(
                workstream_id="project-knowledge-library",
                confirmed=True,
            )
            after = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(manager.active_profile_id, "knihovna")
        self.assertEqual(manager.active_workstream_id, "project-knowledge-library")
        self.assertEqual(before["schema_version"], 1)
        self.assertFalse(result["switched"])
        self.assertEqual(after["schema_version"], 2)
        self.assertEqual(
            after["active_workstream_id"],
            "project-knowledge-library",
        )
        self.assertNotIn("active_profile_id", after)

    def test_schema_two_ignores_stale_profile_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "active-profile.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "active_workstream_id": "project-knowledge-library",
                        "active_profile_id": "human_adam",
                        "updated_at": "2026-07-21T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )

            manager, *_rest = self.make_manager(root)

        self.assertEqual(manager.active_workstream_id, "project-knowledge-library")
        self.assertEqual(manager.active_profile_id, "knihovna")

    def test_persisted_lazy_workstream_restores_selection_without_connect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "active-profile.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "active_workstream_id": "project-mmtx",
                        "updated_at": "2026-07-21T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            lazy = FakeLazyThreads(root / "lazy")

            manager, *_rest = self.make_manager(
                root,
                workstream_threads=lazy,
            )

        self.assertEqual(manager.active_workstream_id, "project-mmtx")
        self.assertEqual(manager.active_profile_id, "human_adam")
        self.assertEqual(lazy.restore_calls, ["project-mmtx"])
        self.assertFalse(lazy.hubs["project-mmtx"].connected)
        self.assertIs(manager.active_service.hub, lazy.hubs["project-mmtx"])

    def test_restored_lazy_selection_connects_same_service_only_on_demand(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "active-profile.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "active_workstream_id": "project-mmtx",
                        "updated_at": "2026-07-21T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
            lazy = FakeLazyThreads(root / "lazy")
            manager, *_rest = self.make_manager(
                root,
                workstream_threads=lazy,
            )

            result = manager.connect()

        self.assertTrue(result["ok"])
        self.assertEqual(manager.active_workstream_id, "project-mmtx")
        self.assertEqual(lazy.restore_calls, ["project-mmtx"])
        self.assertEqual(lazy.open_calls, [])
        self.assertTrue(lazy.hubs["project-mmtx"].connected)

    def test_status_exposes_only_recent_deployment_for_active_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            recovery = {
                "state": "deployed",
                "workstream_id": "layer-human-adam-development",
                "main_short": "abcdef012345",
                "deployed_at": "2026-07-20T13:47:16+00:00",
                "gate": {"passed": True, "test_count": 904, "duration_seconds": 272.5},
                "smoke": {"passed": True, "check_count": 5},
            }
            def for_workstream(_path, *, expected_workstream_id, **_kwargs):
                return (
                    recovery
                    if expected_workstream_id == "layer-human-adam-development"
                    else None
                )

            with patch(
                "app.communication.human_adam_profiles.load_completed_simple_main_deployment",
                side_effect=for_workstream,
            ), patch(
                "app.communication.human_adam_profiles.load_recent_simple_main_deployment",
                side_effect=for_workstream,
            ):
                status = manager.status()
                manager.switch(profile_id="knihovna", confirmed=True)
                other_status = manager.status()

        self.assertEqual(status["last_simple_main_deployment"], recovery)
        self.assertEqual(status["recent_simple_main_deployment"], recovery)
        self.assertIsNone(other_status["last_simple_main_deployment"])
        self.assertIsNone(other_status["recent_simple_main_deployment"])
        self.assertNotIn("deployment_confirmation", status)
        self.assertNotIn("deployment_diagnostic", status)

    def test_connect_allows_runtime_recovery_only_for_safe_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            safe_recovery = manager.runtime.last_start_kwargs
            manager.runtime.reachable = False
            human_hub.messages = [
                {"status": "delivery_unknown", "recovery_required": True}
            ]
            manager.connect()
            uncertain_recovery = manager.runtime.last_start_kwargs

        self.assertTrue(safe_recovery["recover_unreachable_owned"])
        self.assertFalse(uncertain_recovery["recover_unreachable_owned"])

    def test_simple_checkpoint_builds_request_from_profile_and_includes_peers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={"ok": True, "checkpoint_head": "c" * 40},
            ) as checkpoint:
                result = manager.simple_main_checkpoint(
                    commit_message="Checkpoint fáze 1.2",
                    summary="Napojení profilového kontextu",
                    next_step="Doplnit neveřejnou integrační vrstvu.",
                    confirmed=True,
                )

        call = checkpoint.call_args.kwargs
        request = call["request"]
        self.assertIs(call["workspace"], human_workspace)
        self.assertEqual(call["peer_workspaces"], (library_workspace,))
        self.assertTrue(call["confirmed"])
        self.assertEqual(request.workstream_id, "layer-human-adam-development")
        self.assertEqual(
            request.handoff_relative_path,
            "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
        )
        self.assertEqual(
            request.tvbcp_relative_path,
            "memory/tvbcp/architektura_komunikace_samantha.txt",
        )
        self.assertNotIn("work_profile", result)
        self.assertEqual(result["workstream"]["type"], "Layer")

    def test_checkpoint_request_contains_only_redacted_operational_context(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.runtime.reachable = True
            human_hub.connected = True
            human_hub.messages = [
                {
                    "status": "completed",
                    "recovery_required": False,
                    "user_text": "never return this private text",
                    "answer": "never return this private answer",
                }
            ]
            completed = {
                "state": "deployed",
                "workstream_id": "layer-human-adam-development",
                "main_short": "a" * 12,
                "deployed_at": "2026-07-25T21:56:59+00:00",
                "gate": {
                    "passed": True,
                    "test_count": 1216,
                    "duration_seconds": 314.9,
                },
                "smoke": {"passed": True, "check_count": 5},
            }
            receipt = {
                "state": "deployed",
                "workstream_id": "layer-human-adam-development",
                "main_head": "a" * 40,
                "expected_code_stamp": "0123456789abcdef",
                "test_count": 1216,
                "smoke_count": 5,
                "deployed_at": "2026-07-25T21:56:59+00:00",
                "prepared_at": "2026-07-25T21:50:00+00:00",
            }
            with patch(
                "app.communication.human_adam_profiles.load_completed_simple_main_deployment",
                return_value=completed,
            ), patch(
                "app.communication.human_adam_profiles.load_simple_main_deployment_receipt",
                return_value=receipt,
            ), patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={"ok": True, "checkpoint_head": "c" * 40},
            ) as checkpoint:
                manager.simple_main_checkpoint(
                    commit_message="Checkpoint fáze 8.2",
                    summary="Checkpointová projekce",
                    next_step="Ověřit projekci.",
                    confirmed=True,
                )

        request = checkpoint.call_args.kwargs["request"]
        encoded = json.dumps(request.operational_context, ensure_ascii=False)
        self.assertNotIn("never return", encoded.casefold())
        self.assertNotIn("user_text", encoded)
        self.assertNotIn("answer", encoded)
        self.assertEqual(
            request.operational_context["deployment"]["main_head"],
            "a" * 40,
        )
        self.assertTrue(
            request.operational_context["deployment_expected"]
        )
        self.assertEqual(
            request.operational_context["server"]["code_stamp"],
            "0123456789abcdef",
        )
        self.assertTrue(request.operational_context["runtime"]["reachable"])
        self.assertEqual(
            request.operational_context["session"]["messages"],
            [{"status": "completed", "recovery_required": False}],
        )

    def test_work_review_exposes_one_redacted_read_only_live_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.runtime.reachable = True
            human_hub.connected = True
            human_hub.messages = [
                {
                    "status": "completed",
                    "recovery_required": False,
                    "user_text": "never return this private text",
                    "answer": "never return this private answer",
                }
            ]
            receipt = {
                "state": "deployed",
                "workstream_id": "layer-human-adam-development",
                "main_head": "a" * 40,
                "expected_code_stamp": "0123456789abcdef",
                "test_count": 1228,
                "smoke_count": 5,
                "deployed_at": "2026-07-26T06:33:07+00:00",
                "prepared_at": "2026-07-26T06:20:00+00:00",
            }
            remote = {
                "ok": True,
                "read_only": True,
                "writes_performed": False,
                "state": "aligned",
                "local_head": "a" * 40,
                "origin_head": "a" * 40,
            }
            with patch(
                "app.communication.human_adam_profiles.load_simple_main_deployment_receipt",
                return_value=receipt,
            ), patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync",
                return_value=remote,
            ):
                result = manager.work_review(
                    observed_code_stamp="0123456789abcdef"
                )

        live = result["workstream_live_status"]
        encoded = json.dumps(live, ensure_ascii=False)
        self.assertTrue(result["ok"])
        self.assertEqual(live["state"], "current")
        self.assertTrue(live["read_only"])
        self.assertFalse(live["writes_performed"])
        self.assertEqual(
            live["workstream_id"],
            "layer-human-adam-development",
        )
        self.assertEqual(live["main"]["state"], "aligned")
        self.assertEqual(live["deployment"]["state"], "verified_current")
        self.assertEqual(live["workspaces"]["state"], "aligned_clean")
        self.assertEqual(live["workspaces"]["count"], 2)
        self.assertEqual(live["runtime"]["state"], "connected")
        self.assertNotIn("never return", encoded.casefold())
        self.assertNotIn("user_text", encoded)
        self.assertNotIn("answer", encoded)
        self.assertNotIn("pid", encoded.casefold())
        self.assertNotIn("path", encoded.casefold())
        self.assertEqual(human_workspace.prepare_count, 0)
        self.assertEqual(human_workspace.sync_count, 0)
        self.assertEqual(library_workspace.prepare_count, 0)
        self.assertEqual(library_workspace.sync_count, 0)
        self.assertEqual(manager.runtime.last_start_kwargs, {})

    def test_work_review_keeps_live_status_fail_closed_when_remote_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            with patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync",
                side_effect=AppServerError("GitHub není dostupný."),
            ):
                result = manager.work_review(
                    observed_code_stamp="0123456789abcdef"
                )

        live = result["workstream_live_status"]
        self.assertTrue(result["ok"])
        self.assertEqual(live["state"], "unverified")
        self.assertEqual(live["main"]["state"], "origin_unverified")
        self.assertTrue(live["read_only"])
        self.assertFalse(live["writes_performed"])

    def test_simple_checkpoint_uses_registered_library_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            manager.switch(profile_id="knihovna", confirmed=True)
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={"ok": True, "checkpoint_head": "d" * 40},
            ) as checkpoint:
                result = manager.simple_main_checkpoint(
                    commit_message="Checkpoint Knihovny",
                    summary="Knihovna je registrovaný Project",
                    next_step="Pokračovat v Knihovně.",
                    confirmed=True,
                )

        request = checkpoint.call_args.kwargs["request"]
        self.assertEqual(request.workstream_id, "project-knowledge-library")
        self.assertEqual(
            request.handoff_relative_path,
            "memory/handoffs/knowledge_library_article_editing_2026_07_16.md",
        )
        self.assertEqual(request.tvbcp_relative_path, "memory/tvbcp/knihovna_cockpit.txt")
        self.assertNotIn("work_profile", result)
        self.assertEqual(result["workstream"]["id"], "project-knowledge-library")

    def test_lazy_checkpoint_uses_active_workstream_canonical_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            manager.workstream_memory = WorkstreamMemoryRegistry()
            manager.workstream_threads = SimpleNamespace(
                checkpoint_workstream_id=lambda: "project-mmtx"
            )
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={"ok": True, "checkpoint_head": "e" * 40},
            ) as checkpoint:
                result = manager.simple_lazy_workstream_checkpoint(
                    commit_message="Checkpoint MMTX",
                    summary="MMTX dokončil jeden krok",
                    next_step="Pokračovat dalším krokem.",
                    confirmed=True,
                )

        call = checkpoint.call_args.kwargs
        request = call["request"]
        self.assertIs(call["workspace"], human_workspace)
        self.assertEqual(call["peer_workspaces"], (library_workspace,))
        self.assertEqual(request.workstream_id, "project-mmtx")
        self.assertEqual(
            request.handoff_relative_path,
            "memory/handoffs/workstreams/project-mmtx.md",
        )
        self.assertEqual(
            request.tvbcp_relative_path,
            "memory/tvbcp/workstreams/project-mmtx.md",
        )
        self.assertIn("Pracovni proud: project-mmtx", request.handoff_initial_content)
        self.assertIn("# TVBCP: MMTX", request.tvbcp_initial_content)
        self.assertFalse(
            request.operational_context["deployment_expected"]
        )
        self.assertEqual(result["workstream"]["name"], "MMTX")

    def test_lazy_checkpoint_requires_connected_active_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            manager.workstream_memory = WorkstreamMemoryRegistry()
            def no_active_workstream() -> str:
                raise AppServerError("Není připojený žádný lazy pracovní proud.")

            manager.workstream_threads = SimpleNamespace(
                checkpoint_workstream_id=no_active_workstream
            )

            with self.assertRaisesRegex(AppServerError, "Není připojený"):
                manager.simple_lazy_workstream_checkpoint(
                    commit_message="Checkpoint MMTX",
                    summary="MMTX dokončil jeden krok",
                    next_step="Pokračovat.",
                    confirmed=True,
                )

    def test_memory_status_is_inert_and_covers_all_catalog_streams(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            manager.workstream_memory = WorkstreamMemoryRegistry()

            status = manager.lazy_workstream_memory_status()

            self.assertTrue(status["available"])
            self.assertEqual(status["workstream_count"], 30)
            self.assertEqual(status["ready_count"], 0)
            self.assertFalse(Path(human_workspace.project_root).exists())

    def test_simple_deployment_derives_main_and_workstream_and_can_schedule_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            restart_calls: list[bool] = []

            def schedule_restart() -> dict[str, object]:
                restart_calls.append(True)
                return {"ok": True, "status": "restart_started", "pid": 321}

            with patch(
                "app.communication.human_adam_profiles.prepare_clean_main_deployment",
                return_value={
                    "ok": True,
                    "state": "pending_restart",
                    "main_head": "a" * 40,
                    "restart_required": True,
                    "semaphore_used": False,
                },
            ) as deploy:
                result = manager.prepare_simple_main_deployment(
                    previous_pid=321,
                    confirmed=True,
                    restart_scheduler=schedule_restart,
                )

        call = deploy.call_args.kwargs
        request = call["request"]
        self.assertIs(call["workspace"], human_workspace)
        self.assertEqual(call["peer_workspaces"], (library_workspace,))
        self.assertEqual(call["receipt_path"], manager.simple_main_deployment_receipt_path)
        self.assertTrue(call["confirmed"])
        self.assertEqual(request.workstream_id, "layer-human-adam-development")
        self.assertEqual(request.expected_head, "a" * 40)
        self.assertEqual(request.previous_pid, 321)
        self.assertNotIn("work_profile", result)
        self.assertEqual(result["workstream"]["type"], "Layer")
        self.assertTrue(result["restart"]["scheduled"])
        self.assertEqual(restart_calls, [True])

    def test_simple_deployment_operation_lock_blocks_workstream_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            deployment_entered = threading.Event()
            release_deployment = threading.Event()
            worker_errors: list[BaseException] = []

            def blocking_deployment(**_kwargs: object) -> dict[str, object]:
                deployment_entered.set()
                if not release_deployment.wait(timeout=2):
                    raise AssertionError("Test neuvolnil simple-main nasazení.")
                return {"ok": True, "state": "pending_restart"}

            def prepare() -> None:
                try:
                    manager.prepare_simple_main_deployment(
                        previous_pid=321,
                        confirmed=True,
                    )
                except BaseException as exc:  # pragma: no cover - asserted below
                    worker_errors.append(exc)

            with patch(
                "app.communication.human_adam_profiles.prepare_clean_main_deployment",
                side_effect=blocking_deployment,
            ):
                worker = threading.Thread(target=prepare)
                worker.start()
                self.assertTrue(deployment_entered.wait(timeout=2))
                try:
                    with self.assertRaisesRegex(SessionBusyError, "aktivní operace"):
                        manager.activate_grouped_workstream(
                            workstream_id="project-knowledge-library",
                            confirmed=True,
                        )
                finally:
                    release_deployment.set()
                    worker.join(timeout=2)

        self.assertFalse(worker.is_alive())
        self.assertEqual(worker_errors, [])
        self.assertEqual(manager.active_workstream_id, "layer-human-adam-development")

    def test_simple_deployment_audit_derives_workstream_and_both_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            with patch(
                "app.communication.human_adam_profiles.audit_clean_main_deployment",
                return_value={
                    "ok": True,
                    "ready": True,
                    "main_head": "a" * 40,
                    "main_short": "a" * 12,
                    "confirmation_text": (
                        "POTVRZUJI NASAZENI AKTUALNIHO MAIN DO COCKPITU"
                    ),
                },
            ) as audit:
                result = manager.audit_simple_main_deployment()

        call = audit.call_args.kwargs
        self.assertIs(call["workspace"], human_workspace)
        self.assertEqual(call["peer_workspaces"], (library_workspace,))
        self.assertEqual(call["workstream_id"], "layer-human-adam-development")
        self.assertNotIn("work_profile", result)
        self.assertEqual(result["workstream"]["type"], "Layer")
        self.assertEqual(result["handoff_takeover_check"]["state"], "verified")

    def test_main_remote_sync_audit_requires_idle_clean_aligned_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            with patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync",
                return_value={
                    "ok": True,
                    "state": "fast_forward_available",
                    "can_fast_forward": True,
                    "local_head": "a" * 40,
                    "origin_head": "b" * 40,
                },
            ) as audit:
                result = manager.audit_main_remote_sync()

            self.assertTrue(result["profiles_ready"])
            self.assertEqual(result["profile_workspace_count"], 2)
            self.assertEqual(
                audit.call_args.kwargs["source_repo"],
                human_workspace.source_repo,
            )

            library_workspace.dirty = True
            with patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync"
            ) as blocked_audit:
                with self.assertRaisesRegex(AppServerError, "profilový WIP"):
                    manager.audit_main_remote_sync()
                blocked_audit.assert_not_called()
            library_workspace.dirty = False
            library_hub.turn_busy = True
            with patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync"
            ) as busy_audit:
                with self.assertRaisesRegex(SessionBusyError, "aktivní tah"):
                    manager.audit_main_remote_sync()
                busy_audit.assert_not_called()
            self.assertFalse(human_hub.turn_busy)

    def test_confirmed_main_remote_sync_aligns_both_clean_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            with patch(
                "app.communication.human_adam_profiles.apply_clean_main_remote_sync",
                return_value={
                    "ok": True,
                    "state": "main_fast_forwarded",
                    "main_fast_forwarded": True,
                    "main_head": "a" * 40,
                    "main_short": "a" * 12,
                },
            ) as apply_sync:
                result = manager.apply_main_remote_sync(
                    expected_local_head="a" * 40,
                    expected_origin_head="b" * 40,
                    confirmed=True,
                )

        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "aligned")
        self.assertEqual(human_workspace.sync_count, 1)
        self.assertEqual(library_workspace.sync_count, 1)
        self.assertEqual(len(result["workspaces"]), 2)
        self.assertTrue(all(row["aligned"] for row in result["workspaces"]))
        self.assertTrue(apply_sync.call_args.kwargs["confirmed"])

    def test_simple_deployment_uses_registered_library_without_restart_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            manager.switch(profile_id="knihovna", confirmed=True)
            with patch(
                "app.communication.human_adam_profiles.prepare_clean_main_deployment",
                return_value={"ok": True, "state": "pending_restart"},
            ) as deploy:
                result = manager.prepare_simple_main_deployment(
                    previous_pid=654,
                    confirmed=True,
                )

        call = deploy.call_args.kwargs
        self.assertIs(call["workspace"], library_workspace)
        self.assertEqual(call["peer_workspaces"], (human_workspace,))
        self.assertEqual(call["request"].workstream_id, "project-knowledge-library")
        self.assertNotIn("work_profile", result)
        self.assertFalse(result["restart"]["scheduled"])
        self.assertTrue(result["restart"]["ready"])

    def test_simple_deployment_blocks_active_or_uncertain_turn_in_any_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            library_hub.turn_busy = True
            with patch(
                "app.communication.human_adam_profiles.prepare_clean_main_deployment"
            ) as deploy:
                with self.assertRaisesRegex(SessionBusyError, "Knihovna má aktivní tah"):
                    manager.prepare_simple_main_deployment(
                        previous_pid=321,
                        confirmed=True,
                    )
                deploy.assert_not_called()
            library_hub.turn_busy = False
            human_hub.messages = [
                {"status": "delivery_unknown", "recovery_required": True}
            ]
            with patch(
                "app.communication.human_adam_profiles.prepare_clean_main_deployment"
            ) as deploy:
                with self.assertRaisesRegex(SessionBusyError, "nevyřešené doručení"):
                    manager.prepare_simple_main_deployment(
                        previous_pid=321,
                        confirmed=True,
                    )
                deploy.assert_not_called()

    def test_simple_deployment_rejects_failed_restart_scheduler_but_keeps_backend_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            with patch(
                "app.communication.human_adam_profiles.prepare_clean_main_deployment",
                return_value={"ok": True, "state": "pending_restart"},
            ) as deploy:
                with self.assertRaisesRegex(AppServerError, "nepodařilo naplánovat"):
                    manager.prepare_simple_main_deployment(
                        previous_pid=321,
                        confirmed=True,
                        restart_scheduler=lambda: {"ok": False},
                    )

        deploy.assert_called_once()

    def test_simple_deployment_verification_uses_receipt_workstream_and_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            with patch(
                "app.communication.human_adam_profiles.load_simple_main_deployment_receipt",
                return_value={
                    "state": "pending_restart",
                    "workstream_id": "layer-human-adam-development",
                },
            ), patch(
                "app.communication.human_adam_profiles.verify_clean_main_deployment",
                return_value={"ok": True, "state": "deployed", "smoke": {"check_count": 5}},
            ) as verify:
                result = manager.verify_simple_main_deployment(
                    observed_pid=654,
                    observed_code_stamp="0123456789abcdef",
                )

        call = verify.call_args.kwargs
        self.assertIs(call["workspace"], human_workspace)
        self.assertEqual(call["peer_workspaces"], (library_workspace,))
        self.assertEqual(call["receipt_path"], manager.simple_main_deployment_receipt_path)
        self.assertEqual(call["observed_pid"], 654)
        self.assertEqual(call["observed_code_stamp"], "0123456789abcdef")
        self.assertNotIn("work_profile", result)
        self.assertEqual(result["workstream"]["id"], "layer-human-adam-development")

    def test_simple_deployment_verification_rejects_different_active_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            manager.switch(profile_id="knihovna", confirmed=True)
            with patch(
                "app.communication.human_adam_profiles.load_simple_main_deployment_receipt",
                return_value={
                    "state": "pending_restart",
                    "workstream_id": "layer-human-adam-development",
                },
            ), patch(
                "app.communication.human_adam_profiles.verify_clean_main_deployment"
            ) as verify:
                with self.assertRaisesRegex(AppServerError, "jinému pracovnímu proudu"):
                    manager.verify_simple_main_deployment(
                        observed_pid=654,
                        observed_code_stamp="0123456789abcdef",
                    )
                verify.assert_not_called()

    def test_grouped_router_switches_legacy_to_lazy_through_public_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, *_workspaces, human_hub, _library_hub = self.make_manager(
                root
            )
            lazy = FakeLazyThreads(root / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            human_hub.connected = True

            result = human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
            )
            persisted = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )

        self.assertTrue(result["switched"])
        self.assertEqual(lazy.active_workstream_id, "project-mmtx")
        self.assertFalse(human_hub.connected)
        self.assertEqual(manager.active_profile_id, "human_adam")
        self.assertEqual(
            result["workstream_selection"]["active"]["workstream_id"],
            "project-mmtx",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["session"]["thread_id"], "mmtx-thread")
        self.assertNotIn("work_profile", result)
        self.assertTrue(result["workstream_capabilities"]["lazy_backend"])
        self.assertTrue(result["workstream_capabilities"]["development"])
        self.assertTrue(result["workstream_capabilities"]["checkpoint"])
        self.assertTrue(result["workstream_capabilities"]["writable_pilot"])
        self.assertTrue(result["workstream_capabilities"]["one_turn_write"])
        self.assertNotIn("context_anchor", result["workstream_capabilities"])
        self.assertEqual(
            result["workstream_capabilities"]["write_authorization"],
            "one_turn",
        )
        self.assertFalse(result["workstream_capabilities"]["deployment"])
        self.assertEqual(lazy.open_calls, ["project-mmtx"])
        self.assertEqual(persisted["schema_version"], 2)
        self.assertEqual(persisted["active_workstream_id"], "project-mmtx")

    def test_lazy_active_service_routes_send_without_obsolete_anchor_injection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, human_hub, _library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
            )

            sent = manager.send(
                text="Kontrola MMTX pilotu",
                client_message_id="lazy-route-001",
            )

        lazy_send = lazy.hubs["project-mmtx"].last_send
        self.assertEqual(lazy_send["text"], "Kontrola MMTX pilotu")
        self.assertNotIn(
            "HUMAN_ADAM_CONTEXT_ANCHOR",
            str(lazy_send["model_input_text"]),
        )
        self.assertIn("profile_id=project-mmtx", str(lazy_send["model_input_text"]))
        self.assertIn(
            "source=one_turn_direct_main_authorization",
            str(lazy_send["model_input_text"]),
        )
        self.assertIn("lease_state=not_requested", str(lazy_send["model_input_text"]))
        self.assertIn("writable=false", str(lazy_send["model_input_text"]))
        self.assertEqual(human_hub.last_send, {})
        self.assertEqual(sent["automatic_completion"]["state"], "not_needed")

    def test_mmtx_service_reads_canonical_tvbcp_but_blocks_manual_checkpoint_and_deploy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            binding = manager.workstream_memory.binding("project-mmtx")  # type: ignore[union-attr]
            tvbcp_path = human_workspace.project_root / binding.tvbcp_relative_path
            tvbcp_path.parent.mkdir(parents=True)
            tvbcp_path.write_text("# TVBCP: MMTX\n", encoding="utf-8")
            human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
            )

            tvbcp = manager.tvbcp()
            development = manager.development_status()
            with self.assertRaisesRegex(AppServerError, "Ruční WIP checkpoint"):
                manager.checkpoint(confirmed=True, message="Zakázaný checkpoint")
            with self.assertRaisesRegex(
                AppServerError,
                "Audit nasazení lazy pracovního proudu zatím není povolené",
            ):
                manager.audit_simple_main_deployment()

        self.assertEqual(tvbcp["content"], "# TVBCP: MMTX\n")
        self.assertEqual(tvbcp["relative_path"], binding.tvbcp_relative_path)
        self.assertTrue(tvbcp["initialized"])
        self.assertTrue(tvbcp["read_only"])
        self.assertEqual(tvbcp["source"], "isolated_workspace")
        self.assertFalse(development["can_acquire_profile"])
        self.assertFalse(development["can_checkpoint"])
        self.assertFalse(development["can_deploy"])

    def test_family_calendar_has_one_turn_write_without_mmtx_pilot_label(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-family-calendar",
                confirmed=True,
            )

            capabilities = manager.status()["workstream_capabilities"]
            with self.assertRaisesRegex(
                AppServerError,
                "Audit nasazení lazy pracovního proudu zatím není povolené",
            ):
                manager.audit_simple_main_deployment()
            read_only = manager.send(
                text="Jen analyzuj kalendář",
                client_message_id="calendar-read-only-001",
            )
            read_only_input = str(
                lazy.hubs["project-family-calendar"].last_send["model_input_text"]
            )
            library_workspace.source_ahead = True
            writable = manager.send(
                text="Bezpečný zapisovací test kalendáře",
                client_message_id="calendar-write-001",
                write_intent=True,
            )
            writable_input = str(
                lazy.hubs["project-family-calendar"].last_send["model_input_text"]
            )
            expired = manager.send(
                text="Znovu jen analyzuj kalendář",
                client_message_id="calendar-expired-001",
            )
            expired_input = str(
                lazy.hubs["project-family-calendar"].last_send["model_input_text"]
            )
            binding = manager.workstream_memory.binding(  # type: ignore[union-attr]
                "project-family-calendar"
            )
            handoff_created = (
                human_workspace.project_root / binding.handoff_relative_path
            ).exists()
            tvbcp_created = (
                human_workspace.project_root / binding.tvbcp_relative_path
            ).exists()

        self.assertTrue(capabilities["development"])
        self.assertTrue(capabilities["checkpoint"])
        self.assertTrue(capabilities["one_turn_write"])
        self.assertEqual(capabilities["write_authorization"], "one_turn")
        self.assertFalse(capabilities["writable_pilot"])
        self.assertIn("writable=false", read_only_input)
        self.assertIn("[AUTOMATIC_OPERATION_REQUEST]", read_only_input)
        self.assertIn("lease_state=authorized_once", writable_input)
        self.assertIn("lease_owner_id=project-family-calendar", writable_input)
        self.assertIn("writable=true", writable_input)
        self.assertEqual(library_workspace.sync_count, 1)
        self.assertFalse(library_workspace.source_ahead)
        self.assertIn("lease_state=not_requested", expired_input)
        self.assertIn("writable=false", expired_input)
        self.assertEqual(read_only["automatic_completion"]["state"], "not_needed")
        self.assertEqual(writable["automatic_completion"]["state"], "not_needed")
        self.assertEqual(expired["automatic_completion"]["state"], "not_needed")
        self.assertEqual(
            binding.handoff_relative_path,
            "memory/handoffs/workstreams/project-family-calendar.md",
        )
        self.assertEqual(
            binding.tvbcp_relative_path,
            "memory/tvbcp/workstreams/project-family-calendar.md",
        )
        self.assertFalse(handoff_created)
        self.assertFalse(tvbcp_created)

    def test_family_calendar_read_only_turn_executes_server_owned_operation(self) -> None:
        receipt = (
            "Spustím bezpečný preview bez odeslání.\n\n"
            f"{OPERATION_MARKER_START}\n"
            f'{{"operation_id":"{FAMILY_CALENDAR_TEST_EMAIL_PREVIEW}"}}\n'
            f"{OPERATION_MARKER_END}"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, _human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-family-calendar",
                confirmed=True,
            )
            lazy.hubs["project-family-calendar"].next_answer = receipt
            with patch(
                "app.communication.human_adam_profiles.execute_human_adam_operation",
                return_value={
                    "status": "preview",
                    "mode": "dry_run",
                    "recipient_count": 4,
                    "confirmation_required": True,
                    "transport_called": False,
                },
            ) as operation:
                result = manager.send(
                    text="Spusť preview testovacího e-mailu",
                    client_message_id="calendar-operation-001",
                )

        operation.assert_called_once()
        self.assertEqual(
            operation.call_args.kwargs["workstream_id"],
            "project-family-calendar",
        )
        self.assertFalse(human_workspace.dirty)
        self.assertEqual(result["automatic_operation"]["state"], "completed")
        self.assertEqual(result["automatic_completion"]["state"], "not_needed")
        self.assertNotIn(OPERATION_MARKER_START, result["entry"]["answer"])
        self.assertIn('"status":"preview"', result["entry"]["answer"])
        self.assertIn(
            "[AUTOMATIC_OPERATION_REQUEST]",
            str(lazy.hubs["project-family-calendar"].last_send["model_input_text"]),
        )

    def test_family_calendar_operation_is_blocked_when_turn_leaves_changes(self) -> None:
        receipt = (
            "Požaduji bezpečný preview.\n\n"
            f"{OPERATION_MARKER_START}\n"
            f'{{"operation_id":"{FAMILY_CALENDAR_TEST_EMAIL_PREVIEW}"}}\n'
            f"{OPERATION_MARKER_END}"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, _human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-family-calendar",
                confirmed=True,
            )
            lazy.hubs["project-family-calendar"].on_send = lambda: setattr(
                human_workspace,
                "dirty",
                True,
            )
            lazy.hubs["project-family-calendar"].next_answer = receipt
            with patch(
                "app.communication.human_adam_profiles.execute_human_adam_operation"
            ) as operation:
                result = manager.send(
                    text="Tento vadný tah nesmí vykonat operaci",
                    client_message_id="calendar-operation-dirty-001",
                )

        operation.assert_not_called()
        self.assertTrue(human_workspace.dirty)
        self.assertEqual(result["automatic_operation"]["state"], "blocked_dirty")
        self.assertNotIn(OPERATION_MARKER_START, result["entry"]["answer"])
        self.assertIn("workspace obsahuje pracovní změny", result["entry"]["answer"])

    def test_lazy_tvbcp_previews_canonical_template_without_creating_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            binding = manager.workstream_memory.binding("project-mmtx")  # type: ignore[union-attr]
            tvbcp_path = human_workspace.project_root / binding.tvbcp_relative_path
            human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
            )

            tvbcp = manager.tvbcp()
            tvbcp_created = tvbcp_path.exists()

        self.assertFalse(tvbcp_created)
        self.assertFalse(tvbcp["initialized"])
        self.assertTrue(tvbcp["read_only"])
        self.assertEqual(tvbcp["source"], "canonical_template")
        self.assertEqual(tvbcp["modified_at"], "")
        self.assertEqual(tvbcp["relative_path"], binding.tvbcp_relative_path)
        self.assertIn("# TVBCP: MMTX", tvbcp["content"])
        self.assertIn("Prvni zaznam prida potvrzeny checkpoint", tvbcp["content"])

    def test_mmtx_pilot_completes_canonical_lazy_checkpoint(self) -> None:
        receipt = (
            "MMTX změna je hotová.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Complete MMTX pilot","summary":"Malá MMTX změna",'
            '"next_step":"Ověřit živý MMTX proud"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, _human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )
            lazy.hubs["project-mmtx"].on_send = lambda: setattr(
                human_workspace, "dirty", True
            )
            lazy.hubs["project-mmtx"].next_answer = receipt
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={
                    "ok": True,
                    "checkpoint_head": "c" * 40,
                    "checkpoint_short": "c" * 12,
                    "all_workspaces_aligned": True,
                },
            ) as checkpoint:
                result = manager.send(
                    text="Proveď malou MMTX změnu",
                    client_message_id="mmtx-pilot-001",
                    write_intent=True,
                )

        request = checkpoint.call_args.kwargs["request"]
        model_input = str(lazy.hubs["project-mmtx"].last_send["model_input_text"])
        self.assertIn("source=one_turn_direct_main_authorization", model_input)
        self.assertIn("lease_state=authorized_once", model_input)
        self.assertIn("lease_owner_id=project-mmtx", model_input)
        self.assertIn("profile_id=project-mmtx", model_input)
        self.assertIn("writable=true", model_input)
        self.assertIs(checkpoint.call_args.kwargs["workspace"], human_workspace)
        self.assertEqual(checkpoint.call_args.kwargs["peer_workspaces"], (library_workspace,))
        self.assertEqual(request.workstream_id, "project-mmtx")
        self.assertEqual(
            request.handoff_relative_path,
            "memory/handoffs/workstreams/project-mmtx.md",
        )
        self.assertEqual(
            request.tvbcp_relative_path,
            "memory/tvbcp/workstreams/project-mmtx.md",
        )
        self.assertEqual(result["automatic_completion"]["state"], "completed")

    def test_nonpilot_lazy_stream_remains_read_only_even_with_matching_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, *_rest = self.make_manager(Path(temp_dir))
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-lekarna",
                confirmed=True,
            )
            capabilities = manager.status()["workstream_capabilities"]
            development = manager.development_status()
            with self.assertRaisesRegex(AppServerError, "vývojového semaforu"):
                manager.change_development_semaphore(
                    operation="acquire_profile",
                    expected_revision=0,
                    topic="Zakázaný lazy vývoj",
                    confirmed=True,
                )
            manager.development_semaphore.acquire(
                owner_id="project-lekarna",
                owner_label="Lékárna",
                workspace_label="Testovací lazy workspace",
                base_head="a" * 40,
                topic="Simulovaný cizí lease",
                expected_revision=0,
                confirmed=True,
            )
            sent = manager.send(
                text="Tento tah musí zůstat read-only",
                client_message_id="nonpilot-readonly-001",
            )
            with self.assertRaisesRegex(AppServerError, "read-only"):
                manager.send(
                    text="Tento zápis musí být odmítnut",
                    client_message_id="nonpilot-write-001",
                    write_intent=True,
                )

        model_input = str(lazy.hubs["project-lekarna"].last_send["model_input_text"])
        self.assertFalse(capabilities["development"])
        self.assertFalse(capabilities["checkpoint"])
        self.assertFalse(capabilities["writable_pilot"])
        self.assertFalse(capabilities["one_turn_write"])
        self.assertEqual(capabilities["write_authorization"], "read_only")
        self.assertFalse(development["can_acquire_profile"])
        self.assertIn("source=lazy_read_only_policy", model_input)
        self.assertIn("lease_state=read_only", model_input)
        self.assertIn("lease_owner_id=none", model_input)
        self.assertIn("writable=false", model_input)
        self.assertEqual(sent["automatic_completion"]["state"], "not_needed")

    def test_nonpilot_lazy_checkpoint_backend_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            manager.workstream_threads = SimpleNamespace(
                checkpoint_workstream_id=lambda: "project-lekarna"
            )

            with self.assertRaisesRegex(AppServerError, "read-only"):
                manager.simple_lazy_workstream_checkpoint(
                    commit_message="Zakázaný checkpoint",
                    summary="Nemá vzniknout",
                    next_step="Zůstat read-only.",
                    confirmed=True,
                )

    def test_grouped_router_restores_original_legacy_after_lazy_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, human_hub, library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            lazy.fail_open_ids.add("project-mmtx")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.switch(profile_id="knihovna", confirmed=True)

            with self.assertRaisesRegex(AppServerError, "lazy připojení"):
                manager.activate_grouped_workstream(
                    workstream_id="project-mmtx",
                    confirmed=True,
                )

        self.assertEqual(manager.active_profile_id, "knihovna")
        self.assertEqual(lazy.active_workstream_id, "")
        self.assertTrue(library_hub.connected)
        self.assertFalse(human_hub.connected)

    def test_lazy_persistence_failure_restores_compatibility_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, *_workspaces, human_hub, library_hub = self.make_manager(root)
            lazy = FakeLazyThreads(root / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.switch(profile_id="knihovna", confirmed=True)
            persisted_before = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )

            with patch.object(
                manager,
                "_write_active_workstream_id",
                side_effect=OSError("Simulované selhání perzistence."),
            ):
                with self.assertRaisesRegex(OSError, "perzistence"):
                    manager.activate_grouped_workstream(
                        workstream_id="project-mmtx",
                        confirmed=True,
                    )
            persisted_after = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )

        self.assertEqual(persisted_after, persisted_before)
        self.assertEqual(manager.active_workstream_id, "project-knowledge-library")
        self.assertEqual(manager.active_profile_id, "knihovna")
        self.assertEqual(lazy.active_workstream_id, "")
        self.assertTrue(library_hub.connected)
        self.assertFalse(human_hub.connected)

    def test_lazy_preparation_failure_restores_original_compatibility_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, *_workspaces, human_hub, library_hub = self.make_manager(root)
            lazy = FakeLazyThreads(root / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.switch(profile_id="knihovna", confirmed=True)
            persisted_before = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )
            original_prepare = manager._prepare_profile_workspace_unlocked
            prepare_count = 0

            def fail_second_prepare(service):
                nonlocal prepare_count
                prepare_count += 1
                if prepare_count == 2:
                    raise AppServerError("Simulované selhání druhé přípravy.")
                return original_prepare(service)

            with patch.object(
                manager,
                "_prepare_profile_workspace_unlocked",
                side_effect=fail_second_prepare,
            ):
                with self.assertRaisesRegex(AppServerError, "druhé přípravy"):
                    manager.activate_grouped_workstream(
                        workstream_id="project-mmtx",
                        confirmed=True,
                    )
            persisted_after = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )

        self.assertEqual(prepare_count, 3)
        self.assertEqual(persisted_after, persisted_before)
        self.assertEqual(manager.active_workstream_id, "project-knowledge-library")
        self.assertEqual(manager.active_profile_id, "knihovna")
        self.assertEqual(lazy.active_workstream_id, "")
        self.assertTrue(library_hub.connected)
        self.assertFalse(human_hub.connected)

    def test_grouped_router_synchronizes_shared_workspace_for_lazy_to_lazy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )
            human_workspace.source_ahead = True

            result = manager.activate_grouped_workstream(
                workstream_id="project-lekarna",
                confirmed=True,
            )

        self.assertTrue(result["switched"])
        self.assertEqual(lazy.active_workstream_id, "project-lekarna")
        self.assertEqual(human_workspace.sync_count, 1)
        self.assertEqual(lazy.open_calls, ["project-mmtx", "project-lekarna"])

    def test_lazy_to_lazy_persistence_failure_restores_previous_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, *_rest = self.make_manager(root)
            lazy = FakeLazyThreads(root / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )
            persisted_before = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )
            original_write = manager._write_active_workstream_id

            def fail_target(workstream_id: str):
                if workstream_id == "project-lekarna":
                    raise OSError("Simulované selhání lazy perzistence.")
                return original_write(workstream_id)

            with patch.object(
                manager,
                "_write_active_workstream_id",
                side_effect=fail_target,
            ):
                with self.assertRaisesRegex(OSError, "lazy perzistence"):
                    manager.activate_grouped_workstream(
                        workstream_id="project-lekarna",
                        confirmed=True,
                    )
            persisted_after = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )

        self.assertEqual(persisted_after, persisted_before)
        self.assertEqual(manager.active_workstream_id, "project-mmtx")
        self.assertEqual(lazy.active_workstream_id, "project-mmtx")
        self.assertEqual(
            lazy.open_calls,
            ["project-mmtx", "project-lekarna", "project-mmtx"],
        )

    def test_grouped_router_switches_lazy_to_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, human_hub, library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )

            result = manager.activate_grouped_workstream(
                workstream_id="project-knowledge-library",
                confirmed=True,
            )

        self.assertTrue(result["switched"])
        self.assertEqual(lazy.active_workstream_id, "")
        self.assertEqual(lazy.close_calls, ["project-mmtx"])
        self.assertEqual(manager.active_profile_id, "knihovna")
        self.assertTrue(library_hub.connected)
        self.assertFalse(human_hub.connected)

    def test_grouped_router_restores_lazy_after_legacy_connect_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, human_hub, library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )
            library_hub.fail_connect = True

            with self.assertRaisesRegex(AppServerError, "legacy připojení"):
                manager.activate_grouped_workstream(
                    workstream_id="project-knowledge-library",
                    confirmed=True,
                )

        self.assertEqual(manager.active_profile_id, "human_adam")
        self.assertEqual(lazy.active_workstream_id, "project-mmtx")
        self.assertFalse(human_hub.connected)
        self.assertFalse(library_hub.connected)

    def test_grouped_router_keeps_lazy_active_when_turn_is_busy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )
            lazy.busy = True

            with self.assertRaisesRegex(SessionBusyError, "aktivního tahu"):
                manager.activate_grouped_workstream(
                    workstream_id="project-knowledge-library",
                    confirmed=True,
                )

        self.assertEqual(lazy.active_workstream_id, "project-mmtx")
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_grouped_router_rejects_unconfirmed_unknown_and_unavailable_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]

            with self.assertRaisesRegex(AppServerError, "výslovné potvrzení"):
                manager.activate_grouped_workstream(
                    workstream_id="project-mmtx",
                    confirmed=False,
                )
            with self.assertRaisesRegex(AppServerError, "katalogu neexistuje"):
                manager.activate_grouped_workstream(
                    workstream_id="project-unknown",
                    confirmed=True,
                )
            with self.assertRaisesRegex(AppServerError, "nelze bezpečně otevřít"):
                manager.activate_grouped_workstream(
                    workstream_id="project-vocabulary-fr",
                    confirmed=True,
                )

        self.assertEqual(lazy.open_calls, [])
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_grouped_router_preserves_dirty_legacy_before_lazy_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_workspaces, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            human_hub.connected = True
            human_workspace.dirty = True

            with self.assertRaisesRegex(AppServerError, "necheckpointované změny"):
                manager.activate_grouped_workstream(
                    workstream_id="project-mmtx",
                    confirmed=True,
                )

        self.assertEqual(lazy.open_calls, [])
        self.assertTrue(human_hub.connected)
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_grouped_router_preserves_lazy_on_uncertain_target_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, _human_hub, library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )
            library_hub.messages = [
                {"status": "delivery_unknown", "recovery_required": True}
            ]

            with self.assertRaisesRegex(SessionBusyError, "nejisté doručení"):
                manager.activate_grouped_workstream(
                    workstream_id="project-knowledge-library",
                    confirmed=True,
                )

        self.assertEqual(lazy.active_workstream_id, "project-mmtx")
        self.assertEqual(lazy.close_calls, [])
        self.assertEqual(manager.active_profile_id, "human_adam")

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

    def test_project_continuity_uses_persistent_deployment_for_active_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, *_rest = self.make_manager(root, project_continuity=continuity)
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Projektová kontinuita",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            deployment = {
                "state": "deployed",
                "workstream_id": "layer-human-adam-development",
                "main_short": "a" * 12,
                "deployed_at": "2099-01-01T12:00:00+00:00",
                "gate": {"passed": True, "test_count": 979},
                "smoke": {"passed": True, "check_count": 5},
            }
            with patch(
                "app.communication.human_adam_profiles.load_completed_simple_main_deployment",
                return_value=deployment,
            ) as load_completed:
                status = manager.project_continuity_status()

        self.assertEqual(status["audit"]["state"], "needs_update")
        self.assertIn("poslední nasazení", " ".join(status["audit"]["reasons"]))
        self.assertEqual(
            load_completed.call_args.kwargs["expected_workstream_id"],
            "layer-human-adam-development",
        )

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
            manager.send(text="Stále jen analyzuj", client_message_id="leased-read-only")
            leased_read_only_input = str(human_hub.last_send["model_input_text"])
            manager.send(
                text="Proveď změnu",
                client_message_id="writable",
                write_intent=True,
            )
            writable_input = str(human_hub.last_send["model_input_text"])
            manager.send(text="Znovu jen analyzuj", client_message_id="expired")
            expired_input = str(human_hub.last_send["model_input_text"])

        self.assertIn("[DEVELOPMENT_CONTROL]", read_only_input)
        self.assertIn("lease_state=not_requested", read_only_input)
        self.assertIn("writable=false", read_only_input)
        self.assertIn("lease_state=not_requested", leased_read_only_input)
        self.assertIn("lease_owner_id=none", leased_read_only_input)
        self.assertIn("writable=false", leased_read_only_input)
        self.assertIn("lease_owner_id=human_adam", writable_input)
        self.assertIn("lease_state=authorized_once", writable_input)
        self.assertIn("writable=true", writable_input)
        self.assertIn("lease_state=not_requested", expired_input)
        self.assertIn("lease_owner_id=none", expired_input)
        self.assertIn("writable=false", expired_input)
        self.assertNotIn("[AUTOMATIC_STEP_COMPLETION]", read_only_input)
        self.assertIn("[AUTOMATIC_STEP_COMPLETION]", writable_input)
        self.assertNotIn("[AUTOMATIC_STEP_COMPLETION]", expired_input)
        self.assertEqual(read_only_input.count("[WORKSTREAM_LIVE_STATUS]"), 1)
        self.assertEqual(writable_input.count("[WORKSTREAM_LIVE_STATUS]"), 1)
        self.assertLess(
            read_only_input.index("[WORKSTREAM_LIVE_STATUS]"),
            read_only_input.index("[DEVELOPMENT_CONTROL]"),
        )

    def test_send_injects_same_redacted_live_snapshot_into_model_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.runtime.reachable = True
            human_hub.connected = True
            human_hub.messages = [
                {
                    "status": "completed",
                    "recovery_required": False,
                    "user_text": "never return this private text",
                    "answer": "never return this private answer",
                    "path": "/private/never-return-this",
                    "pid": 98765,
                }
            ]
            receipt = {
                "state": "deployed",
                "workstream_id": "layer-human-adam-development",
                "main_head": "a" * 40,
                "expected_code_stamp": "0123456789abcdef",
                "test_count": 1232,
                "smoke_count": 5,
                "deployed_at": "2026-07-26T07:15:00+00:00",
                "prepared_at": "2026-07-26T07:10:00+00:00",
            }
            remote = {
                "ok": True,
                "read_only": True,
                "writes_performed": False,
                "state": "aligned",
                "local_head": "a" * 40,
                "origin_head": "a" * 40,
            }
            with patch(
                "app.communication.human_adam_profiles.load_simple_main_deployment_receipt",
                return_value=receipt,
            ), patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync",
                return_value=remote,
            ):
                result = manager.send(
                    text="Zkontroluj připravenost.",
                    client_message_id="live-status-model-input-001",
                    observed_code_stamp="0123456789abcdef",
                )

        model_input = str(human_hub.last_send["model_input_text"])
        self.assertTrue(result["ok"])
        self.assertEqual(model_input.count("[WORKSTREAM_LIVE_STATUS]"), 1)
        self.assertIn("state=current", model_input)
        self.assertIn("workstream_id=layer-human-adam-development", model_input)
        self.assertIn("main_state=aligned", model_input)
        self.assertIn(f"main_head={'a' * 12}", model_input)
        self.assertIn(f"origin_head={'a' * 12}", model_input)
        self.assertIn("deployment_state=verified_current", model_input)
        self.assertIn("deployment_test_count=1232", model_input)
        self.assertIn("deployment_smoke_count=5", model_input)
        self.assertIn("workspaces_state=aligned_clean", model_input)
        self.assertIn("workspace_count=2", model_input)
        self.assertIn("runtime_state=connected", model_input)
        self.assertIn("runtime_connected=true", model_input)
        self.assertLess(
            model_input.index("[WORKSTREAM_LIVE_STATUS]"),
            model_input.index("[DEVELOPMENT_CONTROL]"),
        )
        self.assertTrue(model_input.endswith("\n\nZkontroluj připravenost."))
        self.assertNotIn("never return", model_input.casefold())
        self.assertNotIn("/private/", model_input)
        self.assertNotIn("98765", model_input)
        self.assertEqual(human_workspace.prepare_count, 0)
        self.assertEqual(human_workspace.sync_count, 0)
        self.assertEqual(library_workspace.prepare_count, 0)
        self.assertEqual(library_workspace.sync_count, 0)
        self.assertEqual(manager.runtime.last_start_kwargs, {})

    def test_send_continues_with_fail_closed_live_status_when_remote_audit_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.runtime.reachable = True
            human_hub.connected = True
            with patch(
                "app.communication.human_adam_profiles.audit_clean_main_remote_sync",
                side_effect=AppServerError(
                    "private diagnostic detail must stay out"
                ),
            ):
                result = manager.send(
                    text="Pokračuj v read-only kontrole.",
                    client_message_id="live-status-model-input-002",
                    observed_code_stamp="0123456789abcdef",
                )

        model_input = str(human_hub.last_send["model_input_text"])
        self.assertTrue(result["ok"])
        self.assertIn("state=unverified", model_input)
        self.assertIn("main_state=origin_unverified", model_input)
        self.assertIn("[DEVELOPMENT_CONTROL]", model_input)
        self.assertIn("writable=false", model_input)
        self.assertTrue(model_input.endswith("\n\nPokračuj v read-only kontrole."))
        self.assertNotIn("private diagnostic detail", model_input)

    def test_knihovna_plain_turn_allows_only_direct_single_card_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, _human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.switch(profile_id="knihovna", confirmed=True)
            result = manager.send(
                text="Uprav název této jedné karty podle mého pokynu.",
                client_message_id="knihovna-single-edit-001",
            )
            model_input = str(library_hub.last_send["model_input_text"])
            capabilities = manager.status()["workstream_capabilities"]
            expected_capabilities = workstream_capabilities(
                "project-knowledge-library"
            )
            expected_root = private_archive_root(expected_capabilities)

        self.assertIn("writable=false", model_input)
        self.assertIn("workspace_writable=false", model_input)
        self.assertIn(
            "private_archive_access=read_diagnose_and_explicit_single_edit",
            model_input,
        )
        self.assertIn(
            f"private_archive_root={expected_root}",
            model_input,
        )
        self.assertIn(
            "private_archive_confirmation_required="
            + ",".join(
                expected_capabilities.private_archive_confirmation_required
            ),
            model_input,
        )
        self.assertNotIn("[AUTOMATIC_STEP_COMPLETION]", model_input)
        self.assertEqual(result["automatic_completion"]["state"], "not_needed")
        self.assertTrue(capabilities["private_archive_direct"])
        self.assertTrue(capabilities["private_archive_read"])
        self.assertTrue(capabilities["private_archive_single_edit"])
        self.assertEqual(
            capabilities["private_archive_confirmation_required"],
            list(expected_capabilities.private_archive_confirmation_required),
        )

    def test_private_archive_direct_access_is_not_advertised_outside_knihovna(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            capabilities = manager.status()["workstream_capabilities"]
            manager.connect()
            manager.send(text="Jen analyzuj.", client_message_id="human-read-only")
            model_input = str(human_hub.last_send["model_input_text"])
            sandbox_policy = manager.active_service.sandbox_policy

        self.assertFalse(capabilities["private_archive_direct"])
        self.assertFalse(capabilities["private_archive_read"])
        self.assertFalse(capabilities["private_archive_single_edit"])
        self.assertEqual(capabilities["private_archive_confirmation_required"], [])
        self.assertNotIn("private_archive_access=", model_input)
        self.assertNotIn("private_archive_root=", model_input)
        self.assertEqual(sandbox_policy["writableRoots"], [])
        self.assertFalse(sandbox_policy["networkAccess"])

    def test_knihovna_policy_keeps_network_closed_and_one_writable_root(self) -> None:
        capabilities = workstream_capabilities("project-knowledge-library")
        sandbox_policy = workstream_sandbox_policy(capabilities)
        archive_root = private_archive_root(capabilities)

        self.assertFalse(sandbox_policy["networkAccess"])
        self.assertEqual(
            sandbox_policy["writableRoots"],
            [str(archive_root)],
        )
        self.assertIn("pres API app.article_archive", KNIHOVNA_DEVELOPER_INSTRUCTIONS)
        self.assertIn("Mazani nebo odebirani", KNIHOVNA_DEVELOPER_INSTRUCTIONS)
        self.assertIn("hromadna zmena", KNIHOVNA_DEVELOPER_INSTRUCTIONS)
        self.assertIn("odeslani ven", KNIHOVNA_DEVELOPER_INSTRUCTIONS)
        self.assertIn("systemovy zasah", KNIHOVNA_DEVELOPER_INSTRUCTIONS)
        self.assertIn("Git, checkpoint, commit, push i nasazeni", KNIHOVNA_DEVELOPER_INSTRUCTIONS)

    def test_one_turn_write_preflight_rejects_dirty_active_workspace_before_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_workspace.dirty = True

            with self.assertRaisesRegex(AppServerError, "rozpracovanou práci"):
                manager.send(
                    text="Tento tah se nesmí odeslat",
                    client_message_id="dirty-preflight-001",
                    write_intent=True,
                )

        self.assertEqual(human_hub.last_send, {})

    def test_one_turn_write_preflight_synchronizes_clean_unsynced_peer_before_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            library_workspace.source_ahead = True

            manager.send(
                text="Tento tah se smí odeslat po bezpečné synchronizaci",
                client_message_id="peer-preflight-001",
                write_intent=True,
            )

        self.assertEqual(library_workspace.sync_count, 1)
        self.assertFalse(library_workspace.source_ahead)
        self.assertIn("writable=true", str(human_hub.last_send["model_input_text"]))

    def test_one_turn_write_preflight_rejects_dirty_unsynced_peer_without_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            library_workspace.source_ahead = True
            library_workspace.dirty = True

            with self.assertRaisesRegex(AppServerError, "Knihovna má 1 necheckpointovaných změn"):
                manager.send(
                    text="Tento tah se nesmí odeslat",
                    client_message_id="dirty-peer-preflight-001",
                    write_intent=True,
                )

        self.assertEqual(library_workspace.sync_count, 0)
        self.assertEqual(human_hub.last_send, {})

    def test_one_turn_write_preflight_rejects_busy_unsynced_peer_without_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            library_workspace.source_ahead = True
            library_hub.active_turn = {"turn_id": "busy-peer-turn"}

            with self.assertRaisesRegex(SessionBusyError, "Knihovna.*aktivního tahu"):
                manager.send(
                    text="Tento tah se nesmí odeslat",
                    client_message_id="busy-peer-preflight-001",
                    write_intent=True,
                )

        self.assertEqual(library_workspace.sync_count, 0)
        self.assertEqual(human_hub.last_send, {})

    def test_one_turn_write_preflight_rejects_uncertain_unsynced_peer_without_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, library_workspace, human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            library_workspace.source_ahead = True
            library_hub.messages = [
                {"status": "delivery_unknown", "recovery_required": True}
            ]

            with self.assertRaisesRegex(SessionBusyError, "Knihovna.*nejisté doručení"):
                manager.send(
                    text="Tento tah se nesmí odeslat",
                    client_message_id="uncertain-peer-preflight-001",
                    write_intent=True,
                )

        self.assertEqual(library_workspace.sync_count, 0)
        self.assertEqual(human_hub.last_send, {})

    def test_writable_turn_creates_provisional_marker_before_model_send(self) -> None:
        receipt = (
            "Změna je hotová.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Complete owned step","summary":"Owned step is complete",'
            '"next_step":"Deploy separately"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            observed_states: list[str] = []

            def observe_marker() -> None:
                observed_states.append(
                    manager.deferred_integration_store.load().state
                )
                human_workspace.dirty = True

            human_hub.on_send = observe_marker
            human_hub.next_answer = receipt
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={
                    "ok": True,
                    "checkpoint_short": "c" * 12,
                    "all_workspaces_aligned": True,
                },
            ):
                result = manager.send(
                    text="Proveď jeden vlastněný krok",
                    client_message_id="owned-turn-start-001",
                    write_intent=True,
                )

            self.assertFalse(manager.deferred_integration_store.path.exists())

        self.assertEqual(observed_states, ["in_progress"])
        self.assertEqual(result["automatic_completion"]["state"], "completed")
        self.assertTrue(
            result["automatic_completion"]["ownership_marker_cleared"]
        )

    def test_human_adam_write_during_source_wip_stays_isolated_and_uncommitted(self) -> None:
        receipt = (
            "Změna i test jsou hotové.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Must not commit","summary":"Must stay isolated",'
            '"next_step":"Wait for clean main"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_workspace.source_pending_changes = 2
            library_workspace.source_pending_changes = 2
            human_hub.on_send = lambda: setattr(human_workspace, "dirty", True)
            human_hub.next_answer = receipt
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint"
            ) as checkpoint:
                result = manager.send(
                    text="Implementuj změnu jen v izolovaném workspace",
                    client_message_id="isolated-source-wip-001",
                    write_intent=True,
                )

        model_input = str(human_hub.last_send["model_input_text"])
        checkpoint.assert_not_called()
        self.assertTrue(human_workspace.dirty)
        self.assertIn("writable=true", model_input)
        self.assertIn("lease_state=authorized_isolated_source_wip", model_input)
        self.assertIn("integration_deferred=true", model_input)
        self.assertIn("Leave successful changes uncommitted", model_input)
        self.assertIn("[AUTOMATIC_STEP_COMPLETION]", model_input)
        self.assertIn("Integration is deferred", model_input)
        self.assertEqual(
            result["automatic_completion"]["state"],
            "deferred_source_wip",
        )
        self.assertTrue(result["automatic_completion"]["ownership_marker"])
        self.assertNotIn(
            "HUMAN_ADAM_STEP_COMPLETION",
            result["entry"]["answer"],
        )
        self.assertIn("bez commitu", result["entry"]["answer"])

    def test_confirmed_deferred_integration_reuses_canonical_checkpoint_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            human_workspace.dirty = True
            human_workspace.source_pending_changes = 1
            manager.deferred_integration_store.save(
                workstream_id="layer-human-adam-development",
                workspace_status=human_workspace.status(),
                completion=TurnCompletionMetadata(
                    commit_message="Integrate deferred step",
                    summary="Odložený krok je hotový",
                    decision="Posun main zůstává servisní rozhodnutí",
                    next_step="Nasadit čistý main samostatně",
                    proposed_next_steps=("Provést živý souběžný test",),
                ),
            )
            human_workspace.source_pending_changes = 0
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={
                    "ok": True,
                    "checkpoint_short": "c" * 12,
                    "push_completed": True,
                },
            ) as checkpoint:
                result = manager.integrate_deferred_changes(
                    confirmation=DEFERRED_INTEGRATION_CONFIRMATION
                )

            self.assertFalse(manager.deferred_integration_store.path.exists())

        checkpoint.assert_called_once()
        request = checkpoint.call_args.kwargs["request"]
        self.assertEqual(request.commit_message, "Integrate deferred step")
        self.assertEqual(
            request.decision,
            "Posun main zůstává servisní rozhodnutí",
        )
        self.assertEqual(
            request.proposed_next_steps,
            ("Provést živý souběžný test",),
        )
        self.assertEqual(result["operation"], "confirmed_deferred_integration")
        self.assertFalse(result["source_advanced_automation"])

    def test_deferred_turn_without_completion_receipt_keeps_owned_recoverable_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_workspace.source_pending_changes = 1
            library_workspace.source_pending_changes = 1
            human_hub.on_send = lambda: setattr(human_workspace, "dirty", True)
            human_hub.next_answer = "Změna zůstala rozpracovaná."

            result = manager.send(
                text="Proveď odložený vývoj bez dokončovací účtenky",
                client_message_id="deferred-no-receipt-001",
                write_intent=True,
            )

            marker = manager.deferred_integration_store.load()
            human_workspace.source_pending_changes = 0
            audit = manager.pending_integration_status()

        self.assertTrue(human_workspace.dirty)
        self.assertEqual(marker.state, OWNED_WIP_MISSING_METADATA)
        self.assertEqual(
            result["automatic_completion"]["state"],
            "deferred_metadata_missing",
        )
        self.assertTrue(result["automatic_completion"]["ownership_marker"])
        self.assertEqual(audit["state"], OWNED_WIP_MISSING_METADATA)
        self.assertTrue(audit["ownership_marker_verified"])
        self.assertTrue(audit["can_recover"])
        self.assertFalse(audit["can_integrate"])

    def test_confirmed_owned_wip_recovery_attaches_metadata_and_checkpoints_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_hub.on_send = lambda: setattr(human_workspace, "dirty", True)
            human_hub.next_answer = "Hotovo bez strukturované účtenky."
            manager.send(
                text="Proveď krok bez účtenky",
                client_message_id="owned-recovery-turn-001",
                write_intent=True,
            )

            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={
                    "ok": True,
                    "checkpoint_short": "d" * 12,
                    "all_workspaces_aligned": True,
                },
            ) as checkpoint:
                result = manager.recover_owned_changes(
                    confirmation=OWNED_WIP_RECOVERY_CONFIRMATION,
                    commit_message="Recover owned step",
                    summary="Vlastněný krok je bezpečně dokončený",
                    next_step="Nasadit samostatně",
                )

            self.assertFalse(manager.deferred_integration_store.path.exists())

        checkpoint.assert_called_once()
        request = checkpoint.call_args.kwargs["request"]
        self.assertEqual(request.commit_message, "Recover owned step")
        self.assertEqual(
            request.summary,
            "Vlastněný krok je bezpečně dokončený",
        )
        self.assertEqual(result["operation"], "confirmed_owned_wip_recovery")
        self.assertTrue(result["ownership_marker_cleared"])

    def test_deferred_turn_marker_write_failure_stays_service_blocked(self) -> None:
        receipt = (
            "Změna i test jsou hotové.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Keep deferred","summary":"Deferred work stays safe",'
            '"next_step":"Resolve marker service failure"}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_workspace.source_pending_changes = 1
            library_workspace.source_pending_changes = 1
            human_hub.on_send = lambda: setattr(human_workspace, "dirty", True)
            human_hub.next_answer = receipt
            with patch.object(
                manager.deferred_integration_store,
                "finalize",
                side_effect=DeferredIntegrationError(
                    "Private ownership marker nelze bezpečně uložit."
                ),
            ):
                result = manager.send(
                    text="Proveď odložený vývoj při selhání markeru",
                    client_message_id="deferred-marker-failure-001",
                    write_intent=True,
                )

        self.assertTrue(human_workspace.dirty)
        self.assertEqual(
            result["automatic_completion"]["state"],
            "ownership_finalize_failed",
        )
        self.assertFalse(result["automatic_completion"]["ownership_marker"])
        self.assertIn("servisně blokované", result["entry"]["answer"])

    def test_deferred_integration_refuses_wrong_confirmation_and_source_advance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            human_workspace.dirty = True
            human_workspace.source_pending_changes = 1
            manager.deferred_integration_store.save(
                workstream_id="layer-human-adam-development",
                workspace_status=human_workspace.status(),
                completion=TurnCompletionMetadata(
                    commit_message="Integrate deferred step",
                    summary="Odložený krok je hotový",
                    next_step="Potvrdit integraci",
                ),
            )
            human_workspace.source_pending_changes = 0

            with self.assertRaisesRegex(AppServerError, "přesnou potvrzovací"):
                manager.integrate_deferred_changes(confirmation="ano")

            human_workspace.source_ahead = True
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint"
            ) as checkpoint:
                with self.assertRaisesRegex(AppServerError, "servisní"):
                    manager.integrate_deferred_changes(
                        confirmation=DEFERRED_INTEGRATION_CONFIRMATION
                    )

        checkpoint.assert_not_called()

    def test_deferred_integration_action_returns_safe_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            result = human_adam_deferred_integration_action(
                {"confirmation": "nesouhlasí"},
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["status"],
            "human_adam_deferred_integration_failed",
        )

    def test_owned_wip_recovery_action_returns_safe_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            result = human_adam_owned_wip_recovery_action(
                {
                    "confirmation": "nesouhlasí",
                    "commit_message": "Recover step",
                    "summary": "Recovered",
                    "next_step": "Deploy",
                },
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["status"],
            "human_adam_owned_wip_recovery_failed",
        )

    def test_source_wip_isolated_write_rejects_unsynced_peer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_workspace.source_pending_changes = 1
            library_workspace.source_pending_changes = 1
            library_workspace.source_ahead = True

            with self.assertRaisesRegex(
                AppServerError,
                "Knihovna není zarovnaný",
            ):
                manager.send(
                    text="Tento izolovaný tah se nesmí odeslat",
                    client_message_id="isolated-source-wip-unsynced-001",
                    write_intent=True,
                )

        self.assertEqual(human_hub.last_send, {})

    def test_source_wip_does_not_unlock_knihovna_code_development(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, _human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.switch(profile_id="knihovna", confirmed=True)
            human_workspace.source_pending_changes = 1
            library_workspace.source_pending_changes = 1

            with self.assertRaisesRegex(
                AppServerError,
                "jednorázový vývoj zůstává uzamčený",
            ):
                manager.send(
                    text="Tento vývoj se nesmí odemknout",
                    client_message_id="knihovna-source-wip-001",
                    write_intent=True,
                )

        self.assertEqual(library_hub.last_send, {})

    def test_writable_turn_with_receipt_completes_direct_main_checkpoint(self) -> None:
        receipt = (
            "Změna i test jsou hotové.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Complete phase 1.5","summary":"Automatické dokončení tahu",'
            '"decision":"TVBCP bude upřednostňovat lidský stav",'
            '"next_step":"Provést checkpoint fáze 1.5",'
            '"proposed_next_steps":["Ověřit nový záznam","Pokračovat druhou fází"]}\n'
            "[/HUMAN_ADAM_STEP_COMPLETION]"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, human_hub, _library_hub = self.make_manager(
                Path(temp_dir)
            )
            manager.connect()
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Automatické dokončení",
                confirmed=True,
            )
            human_hub.on_send = lambda: setattr(human_workspace, "dirty", True)
            human_hub.next_answer = receipt
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint",
                return_value={
                    "ok": True,
                    "checkpoint_head": "c" * 40,
                    "checkpoint_short": "c" * 12,
                    "all_workspaces_aligned": True,
                },
            ) as checkpoint, patch(
                "app.communication.human_adam_profiles.load_completed_simple_main_deployment",
                return_value={
                    "state": "deployed",
                    "workstream_id": "layer-human-adam-development",
                    "main_short": "d" * 12,
                },
            ):
                result = manager.send(
                    text="Dokonči fázi 1.5",
                    client_message_id="completion-001",
                    write_intent=True,
                )

        request = checkpoint.call_args.kwargs["request"]
        self.assertIs(checkpoint.call_args.kwargs["workspace"], human_workspace)
        self.assertEqual(checkpoint.call_args.kwargs["peer_workspaces"], (library_workspace,))
        self.assertEqual(request.commit_message, "Complete phase 1.5")
        self.assertEqual(request.summary, "Automatické dokončení tahu")
        self.assertEqual(
            request.decision,
            "TVBCP bude upřednostňovat lidský stav",
        )
        self.assertEqual(
            request.proposed_next_steps,
            ("Ověřit nový záznam", "Pokračovat druhou fází"),
        )
        self.assertEqual(result["automatic_completion"]["state"], "completed")
        self.assertNotIn("HUMAN_ADAM_STEP_COMPLETION", result["entry"]["answer"])
        self.assertIn("testy prošly", result["entry"]["answer"])
        self.assertIn("Git dokončen", result["entry"]["answer"])
        self.assertIn("začleněný do main a pushnutý na GitHub", result["entry"]["answer"])
        self.assertIn(
            f"Běžící Cockpit používá commit `{'d' * 12}`",
            result["entry"]["answer"],
        )
        self.assertIn(
            f"nový commit `{'c' * 12}` v něm zatím neběží",
            result["entry"]["answer"],
        )
        self.assertIn("jednou audit nasazení do Cockpitu", result["entry"]["answer"])
        self.assertEqual(human_hub.replaced_answers[-1][0], "completion-001")

    def test_dirty_writable_turn_without_receipt_stays_visible_and_uncommitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = self.make_manager(
                Path(temp_dir)
            )
            manager.connect()
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Nedokončený tah",
                confirmed=True,
            )
            human_hub.on_send = lambda: setattr(human_workspace, "dirty", True)
            human_hub.next_answer = "Test ještě neprošel."
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint"
            ) as checkpoint:
                result = manager.send(
                    text="Pokus se o změnu",
                    client_message_id="completion-002",
                    write_intent=True,
                )

        checkpoint.assert_not_called()
        self.assertTrue(human_workspace.dirty)
        self.assertEqual(result["automatic_completion"]["state"], "metadata_missing")
        self.assertIn("Změny zůstaly viditelné", result["entry"]["answer"])

    def test_workstream_switch_requires_confirmation_and_preserves_active_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            result = human_adam_profile_switch_action(
                {"workstream_id": "project-knowledge-library", "confirmed": False},
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_switch_action_rejects_legacy_profile_field_even_with_workstream_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            result = human_adam_profile_switch_action(
                {
                    "workstream_id": "project-knowledge-library",
                    "profile_id": "human_adam",
                    "confirmed": True,
                },
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertIn("profile_id", result["message"])
        self.assertEqual(manager.active_workstream_id, "layer-human-adam-development")
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_profile_only_payload_is_rejected_without_leaving_lazy_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, *_rest = self.make_manager(root)
            lazy = FakeLazyThreads(root / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.activate_grouped_workstream(
                workstream_id="project-mmtx",
                confirmed=True,
            )

            result = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": True},
                service=manager,
            )
            persisted = json.loads(
                (root / "active-profile.json").read_text(encoding="utf-8")
            )

        self.assertFalse(result["ok"])
        self.assertIn("profile_id", result["message"])
        self.assertEqual(manager.active_workstream_id, "project-mmtx")
        self.assertEqual(manager.active_profile_id, "human_adam")
        self.assertEqual(lazy.close_calls, [])
        self.assertEqual(
            persisted["active_workstream_id"],
            "project-mmtx",
        )

    def test_switch_prepares_target_and_persists_profile_without_thread_mix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager, _human_workspace, library_workspace, human_hub, library_hub = self.make_manager(root, target_prepared=False)
            human_hub.connected = True
            result = manager.switch(profile_id="knihovna", confirmed=True)
            persisted = json.loads((root / "active-profile.json").read_text(encoding="utf-8"))

        self.assertTrue(result["ok"])
        self.assertTrue(result["switched"])
        self.assertNotIn("work_profile", result)
        self.assertEqual(
            result["workstream_selection"]["active"]["workstream_id"],
            "project-knowledge-library",
        )
        self.assertEqual(manager.work_profile_id, "knihovna")
        self.assertEqual(result["session"]["thread_id"], "library-thread")
        self.assertEqual(library_workspace.prepare_count, 1)
        self.assertEqual(human_hub.close_count, 1)
        self.assertTrue(library_hub.connected)
        self.assertEqual(persisted["schema_version"], 2)
        self.assertEqual(
            persisted["active_workstream_id"],
            "project-knowledge-library",
        )
        self.assertNotIn("active_profile_id", persisted)
        self.assertNotIn("thread", str(persisted))

    def test_context_anchor_api_and_service_paths_are_fully_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            human_service = manager.active_service
            manager.switch(profile_id="knihovna", confirmed=True)
            library_service = manager.active_service

        self.assertFalse(hasattr(manager, "context_anchor"))
        self.assertFalse(hasattr(manager, "set_context_anchor"))
        for service in (human_service, library_service):
            self.assertFalse(hasattr(service, "context_anchor"))
            self.assertFalse(hasattr(service, "set_context_anchor"))
            self.assertFalse(hasattr(service, "context_anchor_path"))

    def test_thread_rotation_is_locked_to_active_profile_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, _human_workspace, _library_workspace, human_hub, library_hub = (
                self.make_manager(Path(temp_dir))
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
                {"workstream_id": "project-knowledge-library", "confirmed": True},
                service=manager,
            )
            human_workspace.dirty = False
            human_workspace.local_ahead = True
            checkpoint = human_adam_profile_switch_action(
                {"workstream_id": "project-knowledge-library", "confirmed": True},
                service=manager,
            )
            human_workspace.local_ahead = False
            human_hub.messages = [{"status": "delivery_unknown", "recovery_required": True}]
            uncertain = human_adam_profile_switch_action(
                {"workstream_id": "project-knowledge-library", "confirmed": True},
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
                {"workstream_id": "project-knowledge-library", "confirmed": True},
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
        self.assertNotIn("work_profile", result)
        self.assertEqual(
            result["workstream_selection"]["active"]["workstream_id"],
            "layer-human-adam-development",
        )
        self.assertEqual(result["session"]["thread_id"], "human-thread")
        self.assertEqual(human_workspace.sync_count, 1)
        self.assertFalse(human_workspace.source_ahead)
        self.assertTrue(human_hub.connected)

    def test_send_safely_fast_forwards_clean_idle_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()
            human_workspace.source_ahead = True

            result = manager.send(
                text="Navrhni další bezpečný krok",
                client_message_id="auto-sync-send-001",
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["workspace_synced"])
        self.assertEqual(human_workspace.sync_count, 1)
        self.assertFalse(human_workspace.source_ahead)
        self.assertEqual(
            human_hub.last_send["client_message_id"],
            "auto-sync-send-001",
        )

    def test_send_reports_no_sync_when_active_workspace_is_aligned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, _library_workspace, _human_hub, _library_hub = (
                self.make_manager(Path(temp_dir))
            )
            manager.connect()

            result = manager.send(
                text="Jen pokračuj",
                client_message_id="aligned-send-001",
            )

        self.assertFalse(result["workspace_synced"])
        self.assertEqual(human_workspace.sync_count, 0)

    def test_send_does_not_sync_dirty_or_busy_active_workspace(self) -> None:
        cases = ("dirty", "busy")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as temp_dir:
                    manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                        self.make_manager(Path(temp_dir))
                    )
                    manager.connect()
                    human_workspace.source_ahead = True
                    if case == "dirty":
                        human_workspace.dirty = True
                        expected_error = AppServerError
                    else:
                        human_hub.active_turn = {"turn_id": "busy-turn"}
                        expected_error = SessionBusyError

                    with self.assertRaises(expected_error):
                        manager.send(
                            text="Tento pokyn se nesmí odeslat",
                            client_message_id=f"blocked-auto-sync-{case}",
                        )

                self.assertEqual(human_workspace.sync_count, 0)
                self.assertEqual(human_hub.last_send, {})

    def test_send_does_not_sync_uncertain_or_dirty_source_main(self) -> None:
        cases = ("uncertain", "source_dirty")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as temp_dir:
                    manager, human_workspace, _library_workspace, human_hub, _library_hub = (
                        self.make_manager(Path(temp_dir))
                    )
                    manager.connect()
                    human_workspace.source_ahead = True
                    if case == "uncertain":
                        human_hub.messages = [
                            {
                                "status": "delivery_unknown",
                                "recovery_required": True,
                            }
                        ]
                        expected_error = SessionBusyError
                    else:
                        human_workspace.source_pending_changes = 1
                        expected_error = AppServerError

                    with self.assertRaises(expected_error):
                        manager.send(
                            text="Tento pokyn se nesmí odeslat",
                            client_message_id=f"blocked-auto-sync-{case}",
                        )

                self.assertEqual(human_workspace.sync_count, 0)
                self.assertEqual(human_hub.last_send, {})

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
