from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

from app.communication.deferred_integration import (
    DELIVERY_UNKNOWN,
    IN_PROGRESS,
    OWNED_WIP_MISSING_METADATA,
    READY_FOR_CONFIRMED_INTEGRATION,
    DeferredIntegrationError,
    DeferredIntegrationStore,
    change_fingerprint,
)
from app.communication.human_adam_turn_completion import TurnCompletionMetadata


class DeferredIntegrationStoreTests(unittest.TestCase):
    @staticmethod
    def completion() -> TurnCompletionMetadata:
        return TurnCompletionMetadata(
            commit_message="Integrate deferred Human-Adam step",
            summary="Odložený krok je připravený k bezpečné integraci",
            decision="Main při posunu vyžaduje servisní rozhodnutí",
            next_step="Potvrdit integraci na nezměněném základu",
            proposed_next_steps=("Později ověřit širší automatizaci",),
        )

    @staticmethod
    def status(
        *,
        source_pending_changes: int,
        relation: str = "aligned",
        changes: list[dict[str, str]] | None = None,
        dirty: bool = True,
    ) -> dict[str, object]:
        return {
            "dirty": dirty,
            "workspace_relation": relation,
            "source_pending_changes": source_pending_changes,
            "head": "a" * 40,
            "source_head": "a" * 40 if relation == "aligned" else "b" * 40,
            "changes": (
                []
                if not dirty
                else (
                    changes
                    or [
                        {"status": " M", "path": "app/communication/example.py"},
                        {"status": "??", "path": "tests/test_example.py"},
                    ]
                )
            ),
        }

    def test_provisional_marker_precedes_turn_and_recovers_missing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            store = DeferredIntegrationStore(marker_path)
            started = store.begin(
                workstream_id="layer-human-adam-development",
                client_message_id="owned-turn-001",
                workspace_status=self.status(
                    source_pending_changes=0,
                    dirty=False,
                ),
                integration_deferred=False,
                now_factory=lambda: "2026-07-26T18:00:00+00:00",
            )
            raw_started = marker_path.read_text(encoding="utf-8")
            owned = store.finalize(
                workstream_id="layer-human-adam-development",
                client_message_id="owned-turn-001",
                workspace_status=self.status(source_pending_changes=0),
                completion=None,
                now_factory=lambda: "2026-07-26T18:01:00+00:00",
            )
            completed = store.attach_completion(
                workstream_id="layer-human-adam-development",
                workspace_status=self.status(source_pending_changes=0),
                completion=self.completion(),
                now_factory=lambda: "2026-07-26T18:02:00+00:00",
            )
            verified = store.verify(
                workstream_id="layer-human-adam-development",
                workspace_status=self.status(source_pending_changes=0),
            )

            self.assertEqual(stat.S_IMODE(marker_path.stat().st_mode), 0o600)

        self.assertEqual(started.state, IN_PROGRESS)
        self.assertNotIn("app/communication/example.py", raw_started)
        self.assertEqual(owned.state, OWNED_WIP_MISSING_METADATA)
        self.assertIsNone(owned.completion)
        self.assertEqual(completed.state, READY_FOR_CONFIRMED_INTEGRATION)
        self.assertEqual(verified, completed)

    def test_delivery_unknown_marker_stays_fail_closed_without_chat_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            store = DeferredIntegrationStore(marker_path)
            store.begin(
                workstream_id="layer-human-adam-development",
                client_message_id="uncertain-turn-001",
                workspace_status=self.status(
                    source_pending_changes=0,
                    dirty=False,
                ),
                integration_deferred=False,
            )
            record = store.mark_delivery_unknown(
                workstream_id="layer-human-adam-development",
                client_message_id="uncertain-turn-001",
                workspace_status=self.status(source_pending_changes=0),
            )
            raw = marker_path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(
                DeferredIntegrationError,
                "servisní rozhodnutí",
            ):
                store.verify_owned(
                    workstream_id="layer-human-adam-development",
                    workspace_status=self.status(source_pending_changes=0),
                )

        self.assertEqual(record.state, DELIVERY_UNKNOWN)
        self.assertNotIn("chat", raw.casefold())
        self.assertNotIn("user_text", raw)

    def test_clean_new_turn_replaces_completed_marker_without_wip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            store = DeferredIntegrationStore(marker_path)
            store.begin(
                workstream_id="layer-human-adam-development",
                client_message_id="completed-turn-001",
                workspace_status=self.status(
                    source_pending_changes=0,
                    dirty=False,
                ),
                integration_deferred=False,
                now_factory=lambda: "2026-07-26T18:00:00+00:00",
            )
            store.finalize(
                workstream_id="layer-human-adam-development",
                client_message_id="completed-turn-001",
                workspace_status=self.status(source_pending_changes=0),
                completion=self.completion(),
                now_factory=lambda: "2026-07-26T18:01:00+00:00",
            )

            replacement = store.begin(
                workstream_id="layer-human-adam-development",
                client_message_id="new-clean-turn-002",
                workspace_status=self.status(
                    source_pending_changes=0,
                    dirty=False,
                ),
                integration_deferred=False,
                now_factory=lambda: "2026-07-27T12:00:00+00:00",
            )

        self.assertEqual(replacement.state, IN_PROGRESS)
        self.assertEqual(replacement.client_message_id, "new-clean-turn-002")
        self.assertEqual(replacement.change_count, 0)

    def test_clean_new_turn_keeps_uncertain_marker_fail_closed(self) -> None:
        for state in (IN_PROGRESS, DELIVERY_UNKNOWN):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp_dir:
                store = DeferredIntegrationStore(Path(temp_dir) / "marker.json")
                store.begin(
                    workstream_id="layer-human-adam-development",
                    client_message_id="uncertain-turn-001",
                    workspace_status=self.status(
                        source_pending_changes=0,
                        dirty=False,
                    ),
                    integration_deferred=False,
                )
                if state == DELIVERY_UNKNOWN:
                    store.mark_delivery_unknown(
                        workstream_id="layer-human-adam-development",
                        client_message_id="uncertain-turn-001",
                        workspace_status=self.status(
                            source_pending_changes=0,
                            dirty=False,
                        ),
                    )

                with self.assertRaisesRegex(
                    DeferredIntegrationError,
                    "není uzavřený",
                ):
                    store.begin(
                        workstream_id="layer-human-adam-development",
                        client_message_id="new-clean-turn-002",
                        workspace_status=self.status(
                            source_pending_changes=0,
                            dirty=False,
                        ),
                        integration_deferred=False,
                    )

    def test_save_load_and_verify_exact_private_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            store = DeferredIntegrationStore(marker_path)
            record = store.save(
                workstream_id="layer-human-adam-development",
                workspace_status=self.status(source_pending_changes=2),
                completion=self.completion(),
                now_factory=lambda: "2026-07-24T12:00:00+00:00",
            )
            raw = marker_path.read_text(encoding="utf-8")
            verified = store.verify(
                workstream_id="layer-human-adam-development",
                workspace_status=self.status(source_pending_changes=0),
            )

            self.assertEqual(record, verified)
            self.assertEqual(stat.S_IMODE(marker_path.stat().st_mode), 0o600)
            self.assertNotIn("app/communication/example.py", raw)
            self.assertNotIn("tests/test_example.py", raw)
            self.assertNotIn("chat", raw.casefold())
            self.assertNotIn("identity", raw.casefold())
            self.assertEqual(
                record.change_fingerprint,
                change_fingerprint(self.status(source_pending_changes=0)["changes"]),
            )

    def test_verify_fails_closed_when_base_or_changes_advance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = DeferredIntegrationStore(Path(temp_dir) / "marker.json")
            store.save(
                workstream_id="layer-human-adam-development",
                workspace_status=self.status(source_pending_changes=1),
                completion=self.completion(),
            )

            with self.assertRaisesRegex(
                DeferredIntegrationError,
                "servisní rozhodnutí",
            ):
                store.verify(
                    workstream_id="layer-human-adam-development",
                    workspace_status=self.status(
                        source_pending_changes=0,
                        relation="source_ahead",
                    ),
                )
            with self.assertRaisesRegex(
                DeferredIntegrationError,
                "servisní rozhodnutí",
            ):
                store.verify(
                    workstream_id="layer-human-adam-development",
                    workspace_status=self.status(
                        source_pending_changes=0,
                        changes=[
                            {"status": " M", "path": "app/communication/changed.py"}
                        ],
                    ),
                )

    def test_missing_or_malformed_marker_never_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            store = DeferredIntegrationStore(marker_path)
            with self.assertRaises(DeferredIntegrationError):
                store.verify(
                    workstream_id="layer-human-adam-development",
                    workspace_status=self.status(source_pending_changes=0),
                )

            marker_path.write_text(
                json.dumps(
                    {
                        "schema_version": 99,
                        "workstream_id": "layer-human-adam-development",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DeferredIntegrationError, "schéma"):
                store.load()

    def test_marker_rejects_unvalidated_completion_and_can_be_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = Path(temp_dir) / "marker.json"
            store = DeferredIntegrationStore(marker_path)
            store.save(
                workstream_id="layer-human-adam-development",
                workspace_status=self.status(source_pending_changes=1),
                completion=self.completion(),
            )
            payload = json.loads(marker_path.read_text(encoding="utf-8"))
            payload["completion"]["summary"] = "password=secret"
            marker_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(DeferredIntegrationError, "účtenku"):
                store.load()

            store.clear()
            self.assertFalse(marker_path.exists())


if __name__ == "__main__":
    unittest.main()
