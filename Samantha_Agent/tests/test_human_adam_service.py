from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.communication.human_adam_deploy import (
    DEPLOYMENT_COMPLETE,
    DEPLOYMENT_PENDING,
    write_deployment_diagnostic,
    write_deployment_receipt,
)
from app.communication.human_adam_service import (
    CANONICAL_TVBCP_RELATIVE_PATH,
    HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
    THREAD_ROTATION_CONFIRMATION_TEXT,
    HumanAdamService,
    human_adam_checkpoint_action,
    human_adam_connect_action,
    human_adam_context_anchor_action,
    human_adam_context_anchor_update_action,
    human_adam_send_action,
    human_adam_thread_rotation_action,
    human_adam_thread_rotation_status_action,
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

    def start(self, **_kwargs: object) -> dict[str, object]:
        self.started += 1
        self.reachable = True
        return {**self.status(), "started": True}

    def close(self) -> None:
        self.closed += 1
        self.reachable = False


class FakeWorkspace:
    def __init__(self, root: Path) -> None:
        self.workspace_root = root.parent
        self.project_root = root
        self.sync_available = False
        self.dirty = False
        self.local_checkpoint_ahead = False
        self.local_checkpoint_preserved = False
        self.diverged = False
        self.last_checkpoint_message = ""
        self.source_head = "a" * 40
        self.workspace_head = "a" * 40

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
            "workspace_relation": "diverged" if self.diverged else ("local_ahead" if self.local_checkpoint_ahead else ("source_ahead" if self.sync_available else "aligned")),
            "local_checkpoint_ahead": self.local_checkpoint_ahead,
            "local_checkpoint_preserved": self.local_checkpoint_preserved,
            "local_commit_count": 1 if self.local_checkpoint_ahead or self.local_checkpoint_preserved else 0,
            "remotes": [],
            "source_head": self.source_head,
            "head": ("b" * 40) if self.local_checkpoint_ahead or self.local_checkpoint_preserved else self.workspace_head,
        }

    def review(self) -> dict[str, object]:
        status = self.status()
        return {
            "ok": True,
            "dirty": self.dirty,
            "changes": status["changes"],
            "change_count": status["change_count"],
            "checkpoint_changes": ([{"status": "M", "path": "Samantha_Agent/test.py"}] if self.local_checkpoint_ahead or self.local_checkpoint_preserved else []),
            "checkpoint_change_count": 1 if self.local_checkpoint_ahead or self.local_checkpoint_preserved else 0,
            "local_checkpoint_ahead": self.local_checkpoint_ahead,
            "local_checkpoint_preserved": self.local_checkpoint_preserved,
            "local_commit_count": 1 if self.local_checkpoint_ahead or self.local_checkpoint_preserved else 0,
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
        self.turn_busy = False
        self.active_turn: dict[str, object] | None = None
        self.thread_id = "canonical-thread"
        self.rotation_count = 0

    def snapshot(self) -> dict[str, object]:
        return {
            "thread_id": self.thread_id,
            "connected": self.connected,
            "connection_state": "connected" if self.connected else "disconnected",
            "turn_busy": self.turn_busy,
            "active_turn": self.active_turn,
            "messages": [],
        }

    def rotation_status(self) -> dict[str, object]:
        blockers = []
        if self.turn_busy or self.active_turn:
            blockers.append("Vlákno nelze rotovat během aktivního tahu.")
        return {
            "ok": True,
            "ready": not blockers,
            "thread_id": self.thread_id,
            "thread_message_count": 3,
            "rotation_count": self.rotation_count,
            "blockers": blockers,
        }

    def rotate_thread(self, *, expected_thread_id: str) -> dict[str, object]:
        if expected_thread_id != self.thread_id:
            raise AppServerError("stale thread")
        previous = self.thread_id
        self.thread_id = "rotated-thread"
        self.rotation_count += 1
        return {
            "ok": True,
            "rotated": True,
            "previous_thread_id": previous,
            "thread_id": self.thread_id,
            "rotation_count": self.rotation_count,
        }

    def connect(self) -> dict[str, object]:
        self.connected = True
        return self.snapshot()

    def send(
        self,
        *,
        text: str,
        client_message_id: str,
        client_sent_at: str,
        model_input_text: str | None = None,
    ) -> dict[str, object]:
        self.sent.append(
            {
                "text": text,
                "client_message_id": client_message_id,
                "client_sent_at": client_sent_at,
                "model_input_text": model_input_text or "",
            }
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
            context_anchor_path=root / "context_anchor.json",
            deployment_receipt_path=root / "deployment_receipt.json",
            profile_getter=fake_profile,
            hub=hub,  # type: ignore[arg-type]
        )
        return service, runtime, workspace, hub

    def test_status_exposes_persistent_confirmation_only_for_same_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, workspace, _hub = self.make_service(root)
            write_deployment_receipt(
                service.deployment_receipt_path,
                checkpoint_head=workspace.source_head,
                thread_id="canonical-thread",
                state=DEPLOYMENT_COMPLETE,
                recorded_at="2026-07-14T20:30:00+00:00",
                deployed_at="2026-07-14T20:31:00+00:00",
            )

            restarted_service, _runtime, _workspace, _hub = self.make_service(root)
            confirmation = restarted_service.status()["deployment_confirmation"]

        self.assertEqual(
            confirmation,
            {
                "checkpoint_short": "aaaaaaa",
                "gate_passed": True,
                "completed_at": "2026-07-14T20:31:00+00:00",
            },
        )
        self.assertNotIn("canonical-thread", str(confirmation))
        self.assertNotIn("private", str(confirmation))

    def test_status_rejects_pending_receipt_even_when_source_head_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, workspace, _hub = self.make_service(root)
            write_deployment_receipt(
                service.deployment_receipt_path,
                checkpoint_head=workspace.source_head,
                thread_id="canonical-thread",
                state=DEPLOYMENT_PENDING,
                recorded_at="2026-07-14T20:31:00+00:00",
            )

            restarted_service, _runtime, _workspace, _hub = self.make_service(root)
            confirmation = restarted_service.status()["deployment_confirmation"]

        self.assertIsNone(confirmation)

    def test_status_restores_safe_deployment_diagnostic_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, workspace, _hub = self.make_service(root)
            write_deployment_diagnostic(
                service.deployment_diagnostic_path,
                checkpoint_head=workspace.source_head,
                thread_id="canonical-thread",
                stage="push",
                outcome="failed",
                updated_at="2026-07-15T10:31:00+00:00",
            )

            restarted_service, _runtime, _workspace, _hub = self.make_service(root)
            diagnostic = restarted_service.status()["deployment_diagnostic"]

        self.assertEqual(diagnostic["checkpoint_short"], "aaaaaaa")
        self.assertEqual(diagnostic["stage"], "push")
        self.assertEqual(diagnostic["outcome"], "failed")
        self.assertEqual(
            diagnostic["message"],
            "Push větve main selhal; vzdálená větev není potvrzená.",
        )
        self.assertNotIn("canonical-thread", str(diagnostic))
        self.assertNotIn("private", str(diagnostic))

    def test_status_exposes_preserved_checkpoint_without_claiming_it_is_auditable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, workspace, _hub = self.make_service(Path(temp_dir))
            workspace.diverged = True
            workspace.local_checkpoint_preserved = True

            status = service.status()

        self.assertFalse(status["ok"])
        self.assertEqual(status["workspace"]["workspace_relation"], "diverged")
        self.assertTrue(status["workspace"]["local_checkpoint_preserved"])
        self.assertFalse(status["workspace"]["local_checkpoint_ahead"])
        self.assertEqual(status["workspace"]["local_commit_count"], 1)

    def test_developer_instructions_require_timestamped_tvbcp_append(self) -> None:
        self.assertIn("na konec souboru", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("YYYY-MM-DD HH:MM TZ", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)

    def test_developer_instructions_reserve_git_actions_and_tvbcp_for_mila(self) -> None:
        self.assertIn("Sam nikdy nespoustej git add", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("git commit, checkpoint, prevzeti do main, push ani nasazeni", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("vyhradne na Miluv vyslovny pokyn", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("nikdy do nej nezapisuj samostatne ani pri milniku", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertNotIn("na Miluv pokyn nebo pri skutecnem milniku", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)

    def test_developer_instructions_prefer_short_file_names_in_user_answers(self) -> None:
        self.assertIn("jen samotny nazev bez cele cesty", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("pouze pri shodnych nazvech", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)
        self.assertIn("absolutni cestu do textoveho okna nevypisuj", HUMAN_ADAM_DEVELOPER_INSTRUCTIONS)

    def test_detached_lazy_hub_can_use_isolated_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, workspace, _hub = self.make_service(root)
            legacy = service.detached_session_hub(
                state_path=root / "legacy.json",
                developer_instructions="Legacy",
            )
            lazy = service.detached_session_hub(
                state_path=root / "lazy.json",
                developer_instructions="Lazy",
                workspace=workspace.workspace_root,
            )

        self.assertEqual(legacy.workspace, workspace.project_root.resolve())
        self.assertEqual(lazy.workspace, workspace.workspace_root.resolve())

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
        self.assertTrue(hub.sent[0]["model_input_text"].endswith("\n\nProveď kontrolu"))
        self.assertEqual(result["session"]["thread_id"], "canonical-thread")

    def test_explicit_context_anchor_survives_restart_and_is_sent_only_to_model(self) -> None:
        anchor_text = "Cíl: Zachovat kontinuitu\nPlán:\n1. Ověřit kompresi\nDalší krok: Ruční test"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, _workspace, hub = self.make_service(root)
            saved = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": anchor_text, "confirmed": True},
                service=service,
            )
            pinned = human_adam_context_anchor_update_action(
                {"operation": "pin", "expected_revision": saved["revision"], "confirmed": True},
                service=service,
            )
            service.connect()
            result = human_adam_send_action(
                {
                    "message": "Původní text Míly",
                    "client_message_id": "human-adam-anchor-0001",
                    "client_sent_at": "2026-07-17T08:00:00Z",
                },
                service=service,
            )
            restarted, _runtime2, _workspace2, restarted_hub = self.make_service(root)
            restored = human_adam_context_anchor_action(service=restarted)
            status_anchor = restarted.status()["context_anchor"]
            restarted.connect()
            human_adam_send_action(
                {
                    "message": "Tah po restartu",
                    "client_message_id": "human-adam-anchor-0003",
                    "client_sent_at": "2026-07-17T08:02:00Z",
                },
                service=restarted,
            )

        self.assertTrue(saved["ok"])
        self.assertFalse(saved["active"])
        self.assertTrue(saved["has_content"])
        self.assertTrue(pinned["active"])
        self.assertEqual(restored["content"], anchor_text)
        self.assertTrue(restored["active"])
        self.assertNotIn("content", status_anchor)
        self.assertIn("[HUMAN_ADAM_CONTEXT_ANCHOR]", hub.sent[0]["model_input_text"])
        self.assertIn(anchor_text, hub.sent[0]["model_input_text"])
        self.assertIn("current explicit user message below overrides this anchor", hub.sent[0]["model_input_text"])
        self.assertTrue(hub.sent[0]["model_input_text"].endswith("\n\nPůvodní text Míly"))
        self.assertEqual(hub.sent[0]["text"], "Původní text Míly")
        self.assertIn(anchor_text, restarted_hub.sent[0]["model_input_text"])
        self.assertTrue(restarted_hub.sent[0]["model_input_text"].endswith("\n\nTah po restartu"))
        self.assertEqual(result["context_anchor_warning"], "")

    def test_thread_rotation_requires_connected_profile_and_pinned_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            initial = human_adam_thread_rotation_status_action(service=service)
            saved = human_adam_context_anchor_update_action(
                {
                    "operation": "save",
                    "expected_revision": 0,
                    "content": "Cíl: pokračovat po rotaci\nDalší krok: ověřit nové vlákno",
                    "confirmed": True,
                },
                service=service,
            )
            pinned = human_adam_context_anchor_update_action(
                {
                    "operation": "pin",
                    "expected_revision": saved["revision"],
                    "confirmed": True,
                },
                service=service,
            )
            service.connect()
            ready = human_adam_thread_rotation_status_action(service=service)

        self.assertFalse(initial["ready"])
        self.assertIn("připojený", " ".join(initial["blockers"]))
        self.assertIn("připni", " ".join(initial["blockers"]))
        self.assertTrue(pinned["active"])
        self.assertTrue(ready["ready"])
        self.assertEqual(ready["thread_message_count"], 3)
        self.assertTrue(ready["preserves_previous_thread"])
        self.assertFalse(ready["archives_previous_thread"])

    def test_thread_rotation_requires_exact_phrase_and_preserves_previous_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, hub = self.make_service(Path(temp_dir))
            saved = human_adam_context_anchor_update_action(
                {
                    "operation": "save",
                    "expected_revision": 0,
                    "content": "Cíl: bezpečná rotace",
                    "confirmed": True,
                },
                service=service,
            )
            human_adam_context_anchor_update_action(
                {
                    "operation": "pin",
                    "expected_revision": saved["revision"],
                    "confirmed": True,
                },
                service=service,
            )
            service.connect()
            rejected = human_adam_thread_rotation_action(
                {"confirmation": "ano", "expected_thread_id": "canonical-thread"},
                service=service,
            )
            rotated = human_adam_thread_rotation_action(
                {
                    "confirmation": THREAD_ROTATION_CONFIRMATION_TEXT,
                    "expected_thread_id": "canonical-thread",
                },
                service=service,
            )

        self.assertFalse(rejected["ok"])
        self.assertEqual(hub.thread_id, "rotated-thread")
        self.assertTrue(rotated["rotated"])
        self.assertEqual(rotated["previous_thread_id"], "canonical-thread")
        self.assertTrue(rotated["previous_thread_preserved"])
        self.assertEqual(rotated["context_anchor_revision"], 2)

    def test_corrupt_context_anchor_is_ignored_without_blocking_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, _workspace, hub = self.make_service(root)
            service.context_anchor_path.write_text("{broken", encoding="utf-8")
            service.connect()
            result = human_adam_send_action(
                {
                    "message": "Pokračuj bezpečně",
                    "client_message_id": "human-adam-anchor-0002",
                    "client_sent_at": "2026-07-17T08:01:00Z",
                },
                service=service,
            )

        self.assertTrue(result["ok"])
        self.assertNotIn("HUMAN_ADAM_CONTEXT_ANCHOR", hub.sent[0]["model_input_text"])
        self.assertIn("bude ignorován", result["context_anchor_warning"])

    def test_corrupt_context_anchor_is_not_overwritten_by_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            service.context_anchor_path.write_text("{broken", encoding="utf-8")
            result = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: Bezpečný návrh", "confirmed": True},
                service=service,
            )
            persisted = service.context_anchor_path.read_text(encoding="utf-8")

        self.assertFalse(result["ok"])
        self.assertEqual(persisted, "{broken")

    def test_context_anchor_requires_explicit_action_and_rejects_private_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            unconfirmed = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: Test", "confirmed": False},
                service=service,
            )
            missing_revision = human_adam_context_anchor_update_action(
                {"operation": "save", "content": "Cíl: Test", "confirmed": True},
                service=service,
            )
            private_path = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: přečíst /Users/example/private.txt", "confirmed": True},
                service=service,
            )
            secret = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "token=secret-value", "confirmed": True},
                service=service,
            )
            unknown = human_adam_context_anchor_update_action(
                {"operation": "replace", "expected_revision": 0, "content": "Cíl: Test", "confirmed": True},
                service=service,
            )

        self.assertFalse(unconfirmed["ok"])
        self.assertFalse(missing_revision["ok"])
        self.assertIn("očekávanou revizi", missing_revision["message"])
        self.assertFalse(private_path["ok"])
        self.assertIn("absolutní cestu", private_path["message"])
        self.assertFalse(secret["ok"])
        self.assertIn("token", secret["message"])
        self.assertFalse(unknown["ok"])
        self.assertIn("neznámou operaci", unknown["message"])

    def test_context_anchor_pause_retains_content_and_repin_restores_exact_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, _workspace, hub = self.make_service(root)
            saved = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: Test", "confirmed": True},
                service=service,
            )
            pinned = human_adam_context_anchor_update_action(
                {"operation": "pin", "expected_revision": saved["revision"], "confirmed": True},
                service=service,
            )
            paused = human_adam_context_anchor_update_action(
                {"operation": "pause", "expected_revision": pinned["revision"], "confirmed": True},
                service=service,
            )
            service.connect()
            human_adam_send_action(
                {"message": "Tah bez kotvy", "client_message_id": "anchor-paused", "client_sent_at": ""},
                service=service,
            )
            repinned = human_adam_context_anchor_update_action(
                {"operation": "pin", "expected_revision": paused["revision"], "confirmed": True},
                service=service,
            )
            persisted = (root / "context_anchor.json").read_text(encoding="utf-8")

        self.assertTrue(paused["ok"])
        self.assertFalse(paused["active"])
        self.assertTrue(paused["has_content"])
        self.assertEqual(paused["content"], "Cíl: Test")
        self.assertNotIn("HUMAN_ADAM_CONTEXT_ANCHOR", hub.sent[0]["model_input_text"])
        self.assertTrue(repinned["active"])
        self.assertEqual(repinned["content"], "Cíl: Test")
        self.assertIn('"active": true', persisted)
        self.assertIn('"content": "Cíl: Test"', persisted)
        self.assertGreaterEqual(repinned["revision"], 4)

    def test_context_anchor_updates_in_both_states_and_delete_is_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            first = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: První", "confirmed": True}, service=service
            )
            pinned = human_adam_context_anchor_update_action(
                {"operation": "pin", "expected_revision": first["revision"], "confirmed": True}, service=service
            )
            active_update = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": pinned["revision"], "content": "Cíl: Druhý", "confirmed": True}, service=service
            )
            paused = human_adam_context_anchor_update_action(
                {"operation": "pause", "expected_revision": active_update["revision"], "confirmed": True}, service=service
            )
            paused_update = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": paused["revision"], "content": "Cíl: Třetí", "confirmed": True}, service=service
            )
            deleted = human_adam_context_anchor_update_action(
                {"operation": "delete", "expected_revision": paused_update["revision"], "confirmed": True}, service=service
            )
            restored = human_adam_context_anchor_action(service=service)

        self.assertFalse(first["active"])
        self.assertTrue(active_update["active"])
        self.assertEqual(active_update["content"], "Cíl: Druhý")
        self.assertFalse(paused_update["active"])
        self.assertEqual(paused_update["content"], "Cíl: Třetí")
        self.assertFalse(deleted["has_content"])
        self.assertEqual(restored["content"], "")
        self.assertFalse(restored["active"])

    def test_context_anchor_rejects_stale_device_revision_without_overwriting_newer_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            original = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: Původní", "confirmed": True},
                service=service,
            )
            mac_update = human_adam_context_anchor_update_action(
                {
                    "operation": "save",
                    "expected_revision": original["revision"],
                    "content": "Cíl: Novější změna z Macu",
                    "confirmed": True,
                },
                service=service,
            )
            stale_iphone_update = human_adam_context_anchor_update_action(
                {
                    "operation": "save",
                    "expected_revision": original["revision"],
                    "content": "Cíl: Starší editor na iPhonu",
                    "confirmed": True,
                },
                service=service,
            )
            restored = human_adam_context_anchor_action(service=service)

        self.assertTrue(mac_update["ok"])
        self.assertFalse(stale_iphone_update["ok"])
        self.assertEqual(stale_iphone_update["status"], "human_adam_context_anchor_conflict")
        self.assertEqual(stale_iphone_update["expected_revision"], original["revision"])
        self.assertEqual(stale_iphone_update["current_revision"], mac_update["revision"])
        self.assertEqual(restored["revision"], mac_update["revision"])
        self.assertEqual(restored["content"], "Cíl: Novější změna z Macu")

    def test_context_anchor_cannot_change_during_active_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, hub = self.make_service(Path(temp_dir))
            hub.turn_busy = True
            hub.active_turn = {"started_at": "2026-07-17T08:00:00Z"}
            result = human_adam_context_anchor_update_action(
                {"operation": "save", "expected_revision": 0, "content": "Cíl: Neměnit během tahu", "confirmed": True},
                service=service,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "human_adam_busy")

    def test_send_adds_only_allowlisted_workspace_snapshot_to_model_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, workspace, hub = self.make_service(Path(temp_dir))
            workspace.dirty = True
            workspace.local_checkpoint_ahead = True
            service.connect()
            human_adam_send_action(
                {
                    "message": "Původní text Míly",
                    "client_message_id": "human-adam-message-0003",
                    "client_sent_at": "2026-07-14T08:02:00Z",
                },
                service=service,
            )

        model_input = hub.sent[0]["model_input_text"]
        self.assertIn(f"source_head={'a' * 40}", model_input)
        self.assertIn(f"workspace_head={'b' * 40}", model_input)
        self.assertIn("workspace_relation=local_ahead", model_input)
        self.assertIn("uncommitted_change_count=1", model_input)
        self.assertIn("local_commit_count=1", model_input)
        self.assertNotIn("Samantha_Agent/test.py", model_input)
        self.assertEqual(hub.sent[0]["text"], "Původní text Míly")

    def test_workspace_snapshot_redacts_unsafe_head_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, workspace, hub = self.make_service(Path(temp_dir))
            workspace.source_head = "/private/source-head"
            workspace.workspace_head = "../../data/private/workspace-head"
            service.connect()
            human_adam_send_action(
                {
                    "message": "Bezpečný text",
                    "client_message_id": "human-adam-message-0004",
                    "client_sent_at": "2026-07-14T08:03:00Z",
                },
                service=service,
            )

        model_input = hub.sent[0]["model_input_text"]
        self.assertEqual(model_input.count("=unknown"), 2)
        self.assertNotIn("/private/", model_input)
        self.assertNotIn("../", model_input)

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
        self.assertTrue(result["initialized"])
        self.assertTrue(result["read_only"])
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
