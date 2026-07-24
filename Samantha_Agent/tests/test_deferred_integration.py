from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

from app.communication.deferred_integration import (
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
    ) -> dict[str, object]:
        return {
            "dirty": True,
            "workspace_relation": relation,
            "source_pending_changes": source_pending_changes,
            "head": "a" * 40,
            "source_head": "a" * 40 if relation == "aligned" else "b" * 40,
            "changes": changes
            or [
                {"status": " M", "path": "app/communication/example.py"},
                {"status": "??", "path": "tests/test_example.py"},
            ],
        }

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
