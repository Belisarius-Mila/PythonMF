from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from app.codex_appserver import AppServerError
from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
)
from app.communication.human_adam_workstream_threads import WorkstreamThreadRegistry
from app.communication.session_hub import CanonicalSessionHub, SessionBusyError


class FakeClient:
    def __init__(
        self,
        events: list[tuple[str, str]],
        next_thread_id: str,
        *,
        fail_connect: bool = False,
    ):
        self.events = events
        self.next_thread_id = next_thread_id
        self.fail_connect = fail_connect
        self.running = True

    def start_thread(self, **_kwargs: Any) -> str:
        if self.fail_connect:
            raise AppServerError("Simulované selhání připojení.")
        self.events.append(("start", self.next_thread_id))
        return self.next_thread_id

    def resume_thread(self, thread_id: str, **_kwargs: Any) -> None:
        if self.fail_connect:
            raise AppServerError("Simulované selhání připojení.")
        self.events.append(("resume", thread_id))

    def close(self) -> None:
        self.running = False


def clean_workspace_status() -> dict[str, Any]:
    return {
        "prepared": True,
        "ok": True,
        "project_ready": True,
        "remotes": [],
        "dirty": False,
        "local_checkpoint_ahead": False,
        "source_pending_changes": 0,
        "workspace_relation": "aligned",
        "source_update_available": False,
    }


class WorkstreamThreadRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.private_root = self.root / "private-workstreams"
        self.events: list[tuple[str, str]] = []
        self.factory_calls: list[str] = []
        self.hubs: dict[str, CanonicalSessionHub] = {}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def registry(
        self,
        *,
        workspace_status=clean_workspace_status,
        catalog=WORKSTREAM_CATALOG,
        reserved_workstream_ids=(),
        fail_connect_ids=(),
    ) -> WorkstreamThreadRegistry:
        failing = frozenset(fail_connect_ids)

        def factory(record: CanonicalWorkstream, state_path: Path) -> CanonicalSessionHub:
            self.factory_calls.append(record.workstream_id)
            ordinal = len(self.factory_calls)
            hub = CanonicalSessionHub(
                state_path=state_path,
                workspace=self.root,
                client_factory=lambda: FakeClient(
                    self.events,
                    f"thread-{ordinal}",
                    fail_connect=record.workstream_id in failing,
                ),
                developer_instructions=f"Workstream {record.workstream_id}",
                sandbox="workspace-write",
                sandbox_policy={},
                approval_policy="never",
                reasoning_effort="medium",
            )
            self.hubs[record.workstream_id] = hub
            return hub

        return WorkstreamThreadRegistry(
            state_root=self.private_root,
            hub_factory=factory,
            workspace_status=workspace_status,
            catalog=catalog,
            reserved_workstream_ids=reserved_workstream_ids,
        )

    def test_catalog_status_is_inert_and_redacted(self) -> None:
        registry = self.registry()

        status = registry.status()

        self.assertFalse(self.private_root.exists())
        self.assertEqual(self.factory_calls, [])
        self.assertEqual(len(status["workstreams"]), 32)
        self.assertEqual(status["initialized_count"], 0)
        self.assertEqual(status["connected_count"], 0)
        self.assertNotIn("backend", status["workstreams"][0])
        self.assertNotIn("thread_id", repr(status))
        self.assertNotIn(str(self.private_root), repr(status))

    def test_first_open_materializes_only_requested_thread(self) -> None:
        registry = self.registry()

        result = registry.open(workstream_id="project-mmtx", confirmed=True)
        status = registry.status()

        self.assertTrue(result["thread"]["initialized"])
        self.assertTrue(result["thread"]["connected"])
        self.assertEqual(self.factory_calls, ["project-mmtx"])
        self.assertEqual(self.events, [("start", "thread-1")])
        self.assertTrue((self.private_root / "project-mmtx" / "session.json").is_file())
        self.assertEqual(status["initialized_count"], 1)
        self.assertEqual(status["connected_count"], 1)
        self.assertEqual(status["active_workstream_id"], "project-mmtx")
        self.assertIs(
            registry.active_hub(expected_workstream_id="project-mmtx"),
            self.hubs["project-mmtx"],
        )
        with self.assertRaisesRegex(AppServerError, "mezitím změnil"):
            registry.active_hub(expected_workstream_id="project-lekarna")
        self.assertNotIn("thread_id", repr(result))

    def test_new_registry_resumes_persisted_thread_without_materializing_others(self) -> None:
        first = self.registry()
        first.open(workstream_id="project-mmtx", confirmed=True)
        first.close()
        self.factory_calls.clear()
        self.hubs.clear()

        second = self.registry()
        second.open(workstream_id="project-mmtx", confirmed=True)

        self.assertEqual(self.factory_calls, ["project-mmtx"])
        self.assertEqual(self.events[-1], ("resume", "thread-1"))
        self.assertEqual(second.status()["initialized_count"], 1)

    def test_restore_active_is_inert_and_requires_existing_session(self) -> None:
        first = self.registry()
        first.open(workstream_id="project-mmtx", confirmed=True)
        first.close()
        self.factory_calls.clear()
        self.events.clear()
        self.hubs.clear()
        second = self.registry()

        result = second.restore_active(workstream_id="project-mmtx")

        self.assertTrue(result["restored"])
        self.assertEqual(second.active_workstream_id, "project-mmtx")
        self.assertEqual(self.factory_calls, ["project-mmtx"])
        self.assertEqual(self.events, [])
        self.assertFalse(self.hubs["project-mmtx"].snapshot()["connected"])
        with self.assertRaisesRegex(AppServerError, "nemá existující"):
            self.registry().restore_active(workstream_id="project-lekarna")

    def test_switch_disconnects_previous_and_keeps_one_connected_thread(self) -> None:
        registry = self.registry()
        registry.open(workstream_id="project-mmtx", confirmed=True)

        registry.open(workstream_id="project-lekarna", confirmed=True)
        status = registry.status()

        self.assertEqual(self.factory_calls, ["project-mmtx", "project-lekarna"])
        self.assertFalse(self.hubs["project-mmtx"].snapshot()["connected"])
        self.assertTrue(self.hubs["project-lekarna"].snapshot()["connected"])
        self.assertEqual(status["connected_count"], 1)
        self.assertEqual(status["active_workstream_id"], "project-lekarna")

    def test_failed_target_connect_restores_previous_lazy_thread(self) -> None:
        registry = self.registry(fail_connect_ids={"project-lekarna"})
        registry.open(workstream_id="project-mmtx", confirmed=True)

        with self.assertRaisesRegex(AppServerError, "Simulované selhání"):
            registry.open(workstream_id="project-lekarna", confirmed=True)
        status = registry.status()

        self.assertEqual(status["active_workstream_id"], "project-mmtx")
        self.assertEqual(status["connected_count"], 1)
        self.assertTrue(self.hubs["project-mmtx"].snapshot()["connected"])
        self.assertFalse(self.hubs["project-lekarna"].snapshot()["connected"])
        self.assertEqual(self.events[-1], ("resume", "thread-1"))

    def test_active_turn_blocks_switch_before_target_is_materialized(self) -> None:
        registry = self.registry()
        registry.open(workstream_id="project-mmtx", confirmed=True)
        current = self.hubs["project-mmtx"]
        current._turn_lock.acquire()
        try:
            with self.assertRaisesRegex(SessionBusyError, "aktivního tahu"):
                registry.open(workstream_id="project-lekarna", confirmed=True)
        finally:
            current._turn_lock.release()

        self.assertEqual(self.factory_calls, ["project-mmtx"])
        self.assertFalse((self.private_root / "project-lekarna").exists())

    def test_uncertain_delivery_blocks_switch(self) -> None:
        registry = self.registry()
        registry.open(workstream_id="project-mmtx", confirmed=True)
        current = self.hubs["project-mmtx"]
        current._state["messages"].append(
            {"status": "delivery_unknown", "recovery_required": True}
        )

        with self.assertRaisesRegex(SessionBusyError, "nejisté doručení"):
            registry.open(workstream_id="project-lekarna", confirmed=True)

        self.assertEqual(self.factory_calls, ["project-mmtx"])

    def test_checkpoint_context_requires_connected_idle_certain_thread(self) -> None:
        registry = self.registry()
        with self.assertRaisesRegex(AppServerError, "Není připojený"):
            registry.checkpoint_workstream_id()

        registry.open(workstream_id="project-mmtx", confirmed=True)
        self.assertEqual(registry.checkpoint_workstream_id(), "project-mmtx")

        current = self.hubs["project-mmtx"]
        current._state["messages"].append(
            {"status": "delivery_unknown", "recovery_required": True}
        )
        with self.assertRaisesRegex(SessionBusyError, "nejisté doručení"):
            registry.checkpoint_workstream_id()

    def test_close_active_requires_idle_certain_clean_stream(self) -> None:
        workspace = clean_workspace_status()
        registry = self.registry(workspace_status=lambda: workspace)
        registry.open(workstream_id="project-mmtx", confirmed=True)
        current = self.hubs["project-mmtx"]
        with self.assertRaisesRegex(AppServerError, "výslovné potvrzení"):
            registry.close_active(confirmed=False)
        current._state["messages"].append(
            {"status": "delivery_unknown", "recovery_required": True}
        )
        with self.assertRaisesRegex(SessionBusyError, "nejisté doručení"):
            registry.close_active(confirmed=True)
        current._state["messages"].append({"status": "completed"})
        workspace["dirty"] = True
        with self.assertRaisesRegex(AppServerError, "není čistý"):
            registry.close_active(confirmed=True)
        workspace["dirty"] = False

        result = registry.close_active(confirmed=True)

        self.assertTrue(result["closed"])
        self.assertEqual(result["workstream_id"], "project-mmtx")
        self.assertEqual(registry.active_workstream_id, "")
        self.assertFalse(current.snapshot()["connected"])

    def test_dirty_or_unsynchronized_workspace_blocks_before_private_write(self) -> None:
        dirty = clean_workspace_status()
        dirty["dirty"] = True
        registry = self.registry(workspace_status=lambda: dirty)

        with self.assertRaisesRegex(AppServerError, "není čistý"):
            registry.open(workstream_id="project-mmtx", confirmed=True)

        self.assertEqual(self.factory_calls, [])
        self.assertFalse(self.private_root.exists())

    def test_confirmation_reserved_and_archived_guards_are_fail_closed(self) -> None:
        registry = self.registry(reserved_workstream_ids={"project-mmtx"})

        with self.assertRaisesRegex(AppServerError, "výslovné potvrzení"):
            registry.open(workstream_id="project-lekarna", confirmed=False)
        with self.assertRaisesRegex(AppServerError, "původní pracovní profil"):
            registry.open(workstream_id="project-mmtx", confirmed=True)

        archived = CanonicalWorkstream(
            "project-archived",
            "Project",
            "Archiv",
            "archived",
            "3",
            ("Archivní zdroj",),
        )
        archived_registry = self.registry(catalog=(archived,))
        with self.assertRaisesRegex(AppServerError, "Archivovaný"):
            archived_registry.open(workstream_id="project-archived", confirmed=True)

        self.assertEqual(self.factory_calls, [])


if __name__ == "__main__":
    unittest.main()
