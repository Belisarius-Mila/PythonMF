from __future__ import annotations

from inspect import signature
import json
import tempfile
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.communication import human_adam_service as human_adam_service_module
from app.communication.human_adam_service import (
    CANONICAL_PRIVATE_DEVELOPER_INSTRUCTIONS,
    CANONICAL_TVBCP_RELATIVE_PATH,
    DELIVERY_RECOVERY_CONFIRMATION_TEXT,
    HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
    THREAD_ROTATION_CONFIRMATION_TEXT,
    HumanAdamService,
    human_adam_checkpoint_action,
    human_adam_connect_action,
    human_adam_delivery_recovery_action,
    human_adam_delivery_recovery_status_action,
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
        self.source_repo = root.parent
        self.project_dir_name = root.name
        self.sync_available = False
        self.dirty = False
        self.local_checkpoint_ahead = False
        self.local_checkpoint_preserved = False
        self.diverged = False
        self.last_checkpoint_message = ""
        self.source_head = "a" * 40
        self.workspace_head = "a" * 40

    @property
    def canonical_project_root(self) -> Path:
        return (self.source_repo / self.project_dir_name).resolve()

    @property
    def canonical_private_root(self) -> Path:
        return (self.canonical_project_root / "data" / "private").resolve()

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
        self.messages: list[dict[str, object]] = []

    def snapshot(self) -> dict[str, object]:
        return {
            "thread_id": self.thread_id,
            "connected": self.connected,
            "connection_state": "connected" if self.connected else "disconnected",
            "turn_busy": self.turn_busy,
            "active_turn": self.active_turn,
            "messages": list(self.messages),
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

    def reconcile_completed_delivery(self, **kwargs: object) -> dict[str, object]:
        entry = self.messages[-1]
        entry.update(
            {
                "status": "completed",
                "answer": str(kwargs.get("answer") or ""),
                "turn_id": str(kwargs.get("turn_id") or ""),
                "delivery_confirmed": True,
                "recovery_required": False,
            }
        )
        return dict(entry)

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
    def make_service(
        self,
        root: Path,
        *,
        sandbox_policy: dict[str, object] | None = None,
    ) -> tuple[HumanAdamService, FakeRuntime, FakeWorkspace, FakeHub]:
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
            sandbox_policy=sandbox_policy,
        )
        return service, runtime, workspace, hub

    def test_status_omits_legacy_deployment_readers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            status = service.status()

        self.assertNotIn("deployment_confirmation", status)
        self.assertNotIn("deployment_diagnostic", status)

    def test_detached_hub_has_local_delivery_recovery_reader(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, _workspace, _hub = self.make_service(root)
            detached = service.detached_session_hub(
                state_path=root / "detached.json",
                developer_instructions="Test",
            )

        self.assertIsNotNone(detached.delivery_recovery_reader)

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

    def test_status_exposes_only_safe_short_source_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, workspace, _hub = self.make_service(Path(temp_dir))

            status = service.status()
            workspace.source_head = "not-a-git-head"
            invalid_status = service.status()

        self.assertEqual(status["workspace"]["source_head_short"], "a" * 12)
        self.assertNotIn("source_head", status["workspace"])
        self.assertEqual(invalid_status["workspace"]["source_head_short"], "")

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
        self.assertIn(
            "uvedena v aktualnim bloku DEVELOPMENT_CONTROL",
            HUMAN_ADAM_DEVELOPER_INSTRUCTIONS,
        )
        self.assertIn(
            "jednu nedestruktivni upravu",
            CANONICAL_PRIVATE_DEVELOPER_INSTRUCTIONS,
        )
        self.assertIn(
            "nevytvarej novou branu pro kazdou operaci",
            CANONICAL_PRIVATE_DEVELOPER_INSTRUCTIONS,
        )

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

    def test_detached_hub_uses_private_copy_of_service_sandbox_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            live_archive = root / "private-archive"
            requested_policy: dict[str, object] = {
                "type": "workspaceWrite",
                "networkAccess": False,
                "writableRoots": [str(live_archive)],
            }
            service, _runtime, _workspace, _hub = self.make_service(
                root,
                sandbox_policy=requested_policy,
            )
            detached = service.detached_session_hub(
                state_path=root / "detached.json",
                developer_instructions="Knihovna",
            )
            requested_policy["writableRoots"] = []

        self.assertEqual(detached.sandbox_policy["writableRoots"], [str(live_archive)])
        self.assertFalse(detached.sandbox_policy["networkAccess"])

    def test_detached_hub_accepts_a_capability_derived_sandbox_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            live_archive = root / "private-archive"
            service, _runtime, workspace, _hub = self.make_service(root)
            requested_policy: dict[str, object] = {
                "type": "workspaceWrite",
                "networkAccess": False,
                "writableRoots": [str(live_archive)],
            }
            detached = service.detached_session_hub(
                state_path=root / "detached.json",
                developer_instructions="Capability instructions",
                sandbox_policy=requested_policy,
            )
            requested_policy["writableRoots"] = []

        self.assertEqual(detached.sandbox_policy["writableRoots"], [str(live_archive)])
        self.assertEqual(
            service.sandbox_policy["writableRoots"],
            [str(workspace.canonical_private_root)],
        )
        self.assertFalse(detached.sandbox_policy["networkAccess"])

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

    def test_connect_reports_the_effective_custom_sandbox_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            live_archive = root / "private-archive"
            service, _runtime, _workspace, _hub = self.make_service(
                root,
                sandbox_policy={
                    "type": "workspaceWrite",
                    "networkAccess": False,
                    "writableRoots": [str(live_archive)],
                },
            )
            result = service.connect()

        self.assertEqual(
            result["profile"]["sandbox_policy"]["writableRoots"],
            [str(live_archive)],
        )
        self.assertFalse(result["profile"]["network_access"])

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

    def test_send_action_forwards_observed_server_stamp(self) -> None:
        calls: list[str] = []

        class SendService:
            def send(
                self,
                *,
                text: str,
                client_message_id: str,
                client_sent_at: str,
                write_intent: bool,
                observed_code_stamp: str,
            ) -> dict[str, object]:
                del text, client_message_id, client_sent_at, write_intent
                calls.append(observed_code_stamp)
                return {"ok": True}

        result = human_adam_send_action(
            {
                "message": "Test",
                "client_message_id": "human-adam-message-stamp",
            },
            service=SendService(),  # type: ignore[arg-type]
            observed_code_stamp="0123456789abcdef",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(calls, ["0123456789abcdef"])

    def test_raw_service_rejects_unvalidated_write_intent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, hub = self.make_service(Path(temp_dir))
            service.connect()
            result = human_adam_send_action(
                {
                    "message": "Proveď změnu",
                    "client_message_id": "human-adam-write-0001",
                    "client_sent_at": "2026-07-21T08:01:00Z",
                    "write_intent": True,
                },
                service=service,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "human_adam_send_failed")
        self.assertIn("musí ověřit správce pracovních proudů", result["message"])
        self.assertEqual(hub.sent, [])

    def test_context_anchor_feature_is_fully_removed_and_legacy_file_is_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            legacy_path = root / "context_anchor.json"
            legacy_content = '{"schema_version": 1, "legacy": "preserved"}\n'
            legacy_path.write_text(legacy_content, encoding="utf-8")
            service, _runtime, _workspace, hub = self.make_service(root)
            service.connect()
            result = human_adam_send_action(
                {
                    "message": "Původní text Míly",
                    "client_message_id": "human-adam-no-anchor-0001",
                    "client_sent_at": "2026-07-17T08:00:00Z",
                },
                service=service,
            )
            restarted, _runtime2, _workspace2, restarted_hub = self.make_service(root)
            status_payload = restarted.status()
            restarted.connect()
            human_adam_send_action(
                {
                    "message": "Tah po restartu",
                    "client_message_id": "human-adam-no-anchor-0002",
                    "client_sent_at": "2026-07-17T08:02:00Z",
                },
                service=restarted,
            )
            preserved = legacy_path.read_text(encoding="utf-8")

        removed_module_api = (
            "DEFAULT_CONTEXT_ANCHOR_PATH",
            "MAX_CONTEXT_ANCHOR_CHARS",
            "CONTEXT_ANCHOR_SCHEMA_VERSION",
            "ContextAnchorError",
            "ContextAnchorConflictError",
            "empty_context_anchor",
            "load_context_anchor",
            "write_context_anchor",
            "_validated_anchor_content",
            "_validated_anchor_timestamp",
            "_validated_expected_revision",
            "human_adam_context_anchor_action",
            "human_adam_context_anchor_update_action",
            "context_anchor_model_block",
        )
        for name in removed_module_api:
            with self.subTest(name=name):
                self.assertFalse(hasattr(human_adam_service_module, name))
        self.assertNotIn("context_anchor_path", signature(HumanAdamService).parameters)
        self.assertFalse(hasattr(HumanAdamService, "context_anchor"))
        self.assertFalse(hasattr(HumanAdamService, "set_context_anchor"))
        self.assertEqual(preserved, legacy_content)
        self.assertNotIn("context_anchor", status_payload)
        self.assertNotIn("[HUMAN_ADAM_CONTEXT_ANCHOR]", hub.sent[0]["model_input_text"])
        self.assertTrue(hub.sent[0]["model_input_text"].endswith("\n\nPůvodní text Míly"))
        self.assertEqual(hub.sent[0]["text"], "Původní text Míly")
        self.assertTrue(restarted_hub.sent[0]["model_input_text"].endswith("\n\nTah po restartu"))
        self.assertNotIn("context_anchor_warning", result)

    def test_thread_rotation_requires_connected_profile_but_not_pinned_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, _hub = self.make_service(Path(temp_dir))
            initial = human_adam_thread_rotation_status_action(service=service)
            service.connect()
            ready = human_adam_thread_rotation_status_action(service=service)

        self.assertFalse(initial["ready"])
        self.assertIn("připojený", " ".join(initial["blockers"]))
        self.assertNotIn("připni", " ".join(initial["blockers"]))
        self.assertTrue(ready["ready"])
        self.assertNotIn("context_anchor_revision", ready)
        self.assertEqual(ready["thread_message_count"], 3)
        self.assertTrue(ready["preserves_previous_thread"])
        self.assertFalse(ready["archives_previous_thread"])

    def test_thread_rotation_requires_exact_phrase_and_preserves_previous_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service, _runtime, _workspace, hub = self.make_service(Path(temp_dir))
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
        self.assertNotIn("context_anchor_revision", rotated)

    def test_delivery_recovery_requires_local_completion_evidence_and_never_resends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service, _runtime, _workspace, hub = self.make_service(root)
            service.codex_sessions_root = root / "sessions"
            hub.thread_id = "thread-0001"
            hub.messages.append(
                {
                    "client_message_id": "message-0001",
                    "thread_id": "thread-0001",
                    "status": "delivery_unknown",
                    "recovery_required": True,
                }
            )
            rollout = service.codex_sessions_root / "rollout-test-thread-0001.jsonl"
            rollout.parent.mkdir(parents=True)
            events = [
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "user_message",
                        "client_id": "message-0001",
                        "message": "private",
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "agent_message",
                        "phase": "final_answer",
                        "message": "Hotovo",
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "task_complete",
                        "turn_id": "turn-0001",
                        "completed_at": "done",
                        "last_agent_message": "Hotovo",
                    },
                },
            ]
            rollout.write_text(
                "".join(json.dumps(item) + "\n" for item in events),
                encoding="utf-8",
            )
            audit = human_adam_delivery_recovery_status_action(service=service)
            rejected = human_adam_delivery_recovery_action(
                {
                    "confirmation": "ano",
                    "expected_client_message_id": "message-0001",
                    "expected_thread_id": "thread-0001",
                },
                service=service,
            )
            recovered = human_adam_delivery_recovery_action(
                {
                    "confirmation": DELIVERY_RECOVERY_CONFIRMATION_TEXT,
                    "expected_client_message_id": "message-0001",
                    "expected_thread_id": "thread-0001",
                },
                service=service,
            )

        self.assertTrue(audit["ready"])
        self.assertFalse(audit["resends_original_message"])
        self.assertFalse(rejected["ok"])
        self.assertTrue(recovered["recovered"])
        self.assertTrue(recovered["delivery_confirmed"])
        self.assertFalse(recovered["recovery_required"])
        self.assertEqual(hub.sent, [])

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
            result = human_adam_work_review_action(
                service=service,
                observed_code_stamp="0123456789abcdef",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["change_count"], 1)
        self.assertEqual(result["changes"][0]["path"], "Samantha_Agent/test.py")
        self.assertNotIn("content", result["changes"][0])

    def test_work_review_action_forwards_observed_server_stamp(self) -> None:
        calls: list[str] = []

        class ReviewService:
            def work_review(
                self,
                *,
                observed_code_stamp: str = "",
            ) -> dict[str, object]:
                calls.append(observed_code_stamp)
                return {"ok": True, "workstream_live_status": {}}

        result = human_adam_work_review_action(
            service=ReviewService(),  # type: ignore[arg-type]
            observed_code_stamp="0123456789abcdef",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(calls, ["0123456789abcdef"])

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
