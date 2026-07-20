from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.communication.human_adam_profiles import (
    DEPLOYMENT_COMPLETION_CONFIRMATION,
    HumanAdamProfileManager,
    human_adam_development_semaphore_action,
    human_adam_profile_switch_action,
    human_adam_project_continuity_action,
)
from app.communication.human_adam_service import (
    THREAD_ROTATION_CONFIRMATION_TEXT,
    HumanAdamService,
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
        self.next_answer = "Hotovo"
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
        self.hubs = {
            "project-mmtx": FakeHub("mmtx-thread"),
            "project-lekarna": FakeHub("lekarna-thread"),
        }

    def status(self) -> dict[str, object]:
        ids = ("project-mmtx", "project-lekarna")
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

    def test_status_advertises_grouped_catalog_without_changing_legacy_default(self) -> None:
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
        self.assertTrue(status["workstream_selection"]["ok"])
        self.assertEqual(status["workstream_selection"]["workstream_count"], 29)
        self.assertEqual(
            [group["label"] for group in status["workstream_selection"]["groups"]],
            ["Projekty", "Tooly", "Vrstvy", "Ostatní"],
        )

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
            with patch(
                "app.communication.human_adam_profiles.load_recent_simple_main_deployment",
                return_value=recovery,
            ):
                status = manager.status()
                manager.switch(profile_id="knihovna", confirmed=True)
                other_status = manager.status()

        self.assertEqual(status["recent_simple_main_deployment"], recovery)
        self.assertIsNone(other_status["recent_simple_main_deployment"])

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

    def test_simple_checkpoint_context_comes_from_active_profile_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            context = manager.simple_checkpoint_context()

        self.assertTrue(context["available"])
        self.assertEqual(context["profile_id"], "human_adam")
        self.assertEqual(context["workstream_id"], "layer-human-adam-development")
        self.assertEqual(context["workstream_type"], "Layer")
        self.assertEqual(
            context["handoff_relative_path"],
            "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
        )
        self.assertEqual(
            context["tvbcp_relative_path"],
            "memory/tvbcp/architektura_komunikace_samantha.txt",
        )

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
        self.assertEqual(result["work_profile"]["id"], "human_adam")
        self.assertEqual(result["workstream"]["type"], "Layer")

    def test_simple_checkpoint_uses_registered_library_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            manager.switch(profile_id="knihovna", confirmed=True)
            context = manager.simple_checkpoint_context()
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
        self.assertTrue(context["available"])
        self.assertEqual(context["workstream_id"], "project-knowledge-library")
        self.assertEqual(context["workstream_type"], "Project")
        self.assertEqual(request.workstream_id, "project-knowledge-library")
        self.assertEqual(
            request.handoff_relative_path,
            "memory/handoffs/knowledge_library_article_editing_2026_07_16.md",
        )
        self.assertEqual(request.tvbcp_relative_path, "memory/tvbcp/knihovna_cockpit.txt")
        self.assertEqual(result["work_profile"]["id"], "knihovna")

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
            self.assertEqual(status["workstream_count"], 29)
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
        self.assertEqual(result["work_profile"]["id"], "human_adam")
        self.assertEqual(result["workstream"]["type"], "Layer")
        self.assertTrue(result["restart"]["scheduled"])
        self.assertEqual(restart_calls, [True])

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
                    "confirmation_text": "POTVRZUJI NASAZENI CISTEHO MAIN",
                },
            ) as audit:
                result = manager.audit_simple_main_deployment()

        call = audit.call_args.kwargs
        self.assertIs(call["workspace"], human_workspace)
        self.assertEqual(call["peer_workspaces"], (library_workspace,))
        self.assertEqual(call["workstream_id"], "layer-human-adam-development")
        self.assertEqual(result["work_profile"]["id"], "human_adam")
        self.assertEqual(result["workstream"]["type"], "Layer")
        self.assertEqual(result["handoff_takeover_check"]["state"], "verified")

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
        self.assertEqual(result["work_profile"]["id"], "knihovna")
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
        self.assertEqual(result["work_profile"]["id"], "human_adam")
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

    def test_private_workstream_catalog_contains_human_adam_and_library(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            status = manager.workstream_status()
            catalog = manager.workstream_coordinator.catalog()

        self.assertTrue(status["ok"])
        self.assertTrue(status["private_backend"])
        self.assertEqual(status["workstream_count"], 2)
        self.assertEqual(len(catalog), 29)
        self.assertEqual(
            [(row["id"], row["type"], row["active"]) for row in status["workstreams"]],
            [
                ("layer-human-adam-development", "Layer", True),
                ("project-knowledge-library", "Project", False),
            ],
        )
        self.assertNotIn("thread", str(status).casefold())

    def test_private_workstream_selection_roundtrip_synchronizes_each_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, library_workspace, *_rest = self.make_manager(
                Path(temp_dir)
            )
            library_workspace.source_ahead = True
            library = manager.select_workstream(
                workstream_id="project-knowledge-library",
                confirmed=True,
            )
            human_workspace.source_ahead = True
            human = manager.select_workstream(
                workstream_id="layer-human-adam-development",
                confirmed=True,
            )

        self.assertTrue(library["switched"])
        self.assertEqual(library_workspace.sync_count, 1)
        self.assertEqual(
            library["workstream_selection"]["active"]["workstream_id"],
            "project-knowledge-library",
        )
        self.assertTrue(human["switched"])
        self.assertEqual(human_workspace.sync_count, 1)
        self.assertEqual(
            human["workstream_selection"]["active"]["workstream_id"],
            "layer-human-adam-development",
        )

    def test_private_workstream_selection_rejects_unknown_id_without_switch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            with self.assertRaisesRegex(AppServerError, "není zaregistrovaný"):
                manager.select_workstream(
                    workstream_id="project-unknown",
                    confirmed=True,
                )

        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_private_workstream_selection_preserves_dirty_current_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, human_workspace, *_rest = self.make_manager(Path(temp_dir))
            human_workspace.dirty = True
            with self.assertRaisesRegex(AppServerError, "necheckpointované změny"):
                manager.select_workstream(
                    workstream_id="project-knowledge-library",
                    confirmed=True,
                )

        self.assertEqual(manager.active_profile_id, "human_adam")
        self.assertTrue(human_workspace.dirty)

    def test_grouped_router_switches_legacy_to_lazy_through_public_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, human_hub, _library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            human_hub.connected = True

            result = human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
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
        self.assertEqual(result["work_profile"]["id"], "project-mmtx")
        self.assertTrue(result["workstream_capabilities"]["lazy_backend"])
        self.assertTrue(result["workstream_capabilities"]["development"])
        self.assertTrue(result["workstream_capabilities"]["checkpoint"])
        self.assertTrue(result["workstream_capabilities"]["writable_pilot"])
        self.assertFalse(result["workstream_capabilities"]["deployment"])
        self.assertEqual(lazy.open_calls, ["project-mmtx"])

    def test_lazy_active_service_routes_send_and_keeps_context_anchor_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_workspaces, human_hub, _library_hub = self.make_manager(
                Path(temp_dir)
            )
            lazy = FakeLazyThreads(Path(temp_dir) / "lazy")
            manager.workstream_threads = lazy  # type: ignore[assignment]
            manager.set_context_anchor(
                operation="save",
                expected_revision=0,
                content="Cíl: legacy Human–Adam",
                confirmed=True,
            )
            human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
            )

            empty_lazy_anchor = manager.context_anchor()
            manager.set_context_anchor(
                operation="save",
                expected_revision=0,
                content="Cíl: samostatný MMTX",
                confirmed=True,
            )
            sent = manager.send(
                text="Kontrola MMTX pilotu",
                client_message_id="lazy-route-001",
            )
            human_adam_profile_switch_action(
                {"workstream_id": "layer-human-adam-development", "confirmed": True},
                service=manager,
            )
            legacy_anchor = manager.context_anchor()
            human_adam_profile_switch_action(
                {"workstream_id": "project-mmtx", "confirmed": True},
                service=manager,
            )
            restored_lazy_anchor = manager.context_anchor()

        lazy_send = lazy.hubs["project-mmtx"].last_send
        self.assertFalse(empty_lazy_anchor["has_content"])
        self.assertEqual(legacy_anchor["content"], "Cíl: legacy Human–Adam")
        self.assertEqual(restored_lazy_anchor["content"], "Cíl: samostatný MMTX")
        self.assertEqual(lazy_send["text"], "Kontrola MMTX pilotu")
        self.assertIn("profile_id=project-mmtx", str(lazy_send["model_input_text"]))
        self.assertIn("source=mmtx_writable_pilot", str(lazy_send["model_input_text"]))
        self.assertIn("writable=true", str(lazy_send["model_input_text"]))
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
            with self.assertRaisesRegex(AppServerError, "Audit nasazení"):
                manager.audit_simple_main_deployment()

        self.assertEqual(tvbcp["content"], "# TVBCP: MMTX\n")
        self.assertEqual(tvbcp["relative_path"], binding.tvbcp_relative_path)
        self.assertFalse(development["can_acquire_profile"])
        self.assertFalse(development["can_checkpoint"])
        self.assertFalse(development["can_deploy"])

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
            human_workspace.dirty = True
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
                )

        request = checkpoint.call_args.kwargs["request"]
        model_input = str(lazy.hubs["project-mmtx"].last_send["model_input_text"])
        self.assertIn("source=mmtx_writable_pilot", model_input)
        self.assertIn("lease_state=pilot", model_input)
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

        model_input = str(lazy.hubs["project-lekarna"].last_send["model_input_text"])
        self.assertFalse(capabilities["development"])
        self.assertFalse(capabilities["checkpoint"])
        self.assertFalse(capabilities["writable_pilot"])
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

    def test_confirmed_post_restart_completion_commits_pushes_and_releases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            continuity, project_id, handoff_path = self.make_project_continuity(root)
            manager, *_rest = self.make_manager(root, project_continuity=continuity)
            (root / ".gitignore").write_text(
                "human/\nlibrary/\nactive-profile.json\ndevelopment_semaphore.json\n"
                "deployment_completion.json\n*.json.lock\nremote.git/\n",
                encoding="utf-8",
            )

            def git(*args: str, cwd: Path = root) -> str:
                completed = subprocess.run(
                    ["/usr/bin/git", "-C", str(cwd), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init")
            git("config", "user.name", "Test Adam")
            git("config", "user.email", "adam@example.invalid")
            git("add", ".gitignore", "memory")
            git("commit", "-m", "Create project")
            git("branch", "-M", "main")
            git("init", "--bare", str(root / "remote.git"))
            git("remote", "add", "origin", str(root / "remote.git"))
            git("push", "-u", "origin", "main")
            checkpoint_head = git("rev-parse", "HEAD")
            manager.change_development_semaphore(
                operation="acquire_profile",
                expected_revision=0,
                topic="Potvrzené dokončení",
                project_id=project_id,
                handoff_path=handoff_path,
                confirmed=True,
            )
            prepared = manager.prepare_deployment_completion(
                profile_id="human_adam",
                deployment_result={
                    "checkpoint_token": checkpoint_head,
                    "gate": {"test_count": 849},
                    "deployment_confirmation": {
                        "completed_at": "2026-07-19T12:55:31+00:00"
                    },
                },
                previous_pid=os.getpid() + 1000,
            )
            smoke = [SimpleNamespace(ok=True) for _index in range(5)]
            with patch(
                "app.communication.human_adam_profiles.run_smoke_check",
                return_value=smoke,
            ):
                audit = manager.deployment_completion_status()
                completed = manager.finalize_deployment_completion(
                    confirmation=DEPLOYMENT_COMPLETION_CONFIRMATION,
                    next_step="Ručně ověřit novou kartu v Cockpitu.",
                )
            handoff_text = (root / handoff_path).read_text(encoding="utf-8")
            local_head = git("rev-parse", "main")
            remote_head = git("rev-parse", "origin/main")
            semaphore = manager.development_semaphore.status()

        self.assertEqual(prepared["state"], "pending_restart")
        self.assertTrue(audit["ready"])
        self.assertEqual(audit["checkpoint_head"], checkpoint_head)
        self.assertTrue(completed["writes_performed"])
        self.assertEqual(completed["state"], "complete")
        self.assertEqual(local_head, remote_head)
        self.assertIn("Stav: nasazeno", handoff_text)
        self.assertIn("849 testů, OK", handoff_text)
        self.assertFalse(semaphore["active"])

    def test_post_restart_completion_rejects_non_exact_confirmation_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            with self.assertRaisesRegex(AppServerError, "Chybí přesná potvrzovací věta"):
                manager.finalize_deployment_completion(
                    confirmation="ano",
                    next_step="Ověřit výsledek.",
                )

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
        self.assertNotIn("[AUTOMATIC_STEP_COMPLETION]", read_only_input)
        self.assertIn("[AUTOMATIC_STEP_COMPLETION]", writable_input)

    def test_writable_turn_with_receipt_completes_direct_main_checkpoint(self) -> None:
        receipt = (
            "Změna i test jsou hotové.\n\n"
            "[HUMAN_ADAM_STEP_COMPLETION]\n"
            '{"commit_message":"Complete phase 1.5","summary":"Automatické dokončení tahu",'
            '"next_step":"Provést checkpoint fáze 1.5"}\n'
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
            human_workspace.dirty = True
            human_hub.next_answer = receipt
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
                    text="Dokonči fázi 1.5",
                    client_message_id="completion-001",
                )

        request = checkpoint.call_args.kwargs["request"]
        self.assertIs(checkpoint.call_args.kwargs["workspace"], human_workspace)
        self.assertEqual(checkpoint.call_args.kwargs["peer_workspaces"], (library_workspace,))
        self.assertEqual(request.commit_message, "Complete phase 1.5")
        self.assertEqual(request.summary, "Automatické dokončení tahu")
        self.assertEqual(result["automatic_completion"]["state"], "completed")
        self.assertNotIn("HUMAN_ADAM_STEP_COMPLETION", result["entry"]["answer"])
        self.assertIn("testy prošly", result["entry"]["answer"])
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
            human_workspace.dirty = True
            human_hub.next_answer = "Test ještě neprošel."
            with patch(
                "app.communication.human_adam_profiles.complete_simple_main_checkpoint"
            ) as checkpoint:
                result = manager.send(
                    text="Pokus se o změnu",
                    client_message_id="completion-002",
                )

        checkpoint.assert_not_called()
        self.assertTrue(human_workspace.dirty)
        self.assertEqual(result["automatic_completion"]["state"], "metadata_missing")
        self.assertIn("Změny zůstaly viditelné", result["entry"]["answer"])

    def test_switch_requires_confirmation_and_preserves_active_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manager, *_rest = self.make_manager(Path(temp_dir))
            result = human_adam_profile_switch_action(
                {"profile_id": "knihovna", "confirmed": False},
                service=manager,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(manager.active_profile_id, "human_adam")

    def test_switch_action_routes_registered_workstream_through_coordinator(self) -> None:
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

        self.assertTrue(result["ok"])
        self.assertTrue(result["switched"])
        self.assertEqual(manager.active_profile_id, "knihovna")
        self.assertEqual(
            result["workstream_selection"]["active"]["workstream_id"],
            "project-knowledge-library",
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
