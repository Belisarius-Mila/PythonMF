"""Synthetic C03b wire, revision durability, and fail-closed contract checks."""

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from camino.api import CaminoV1Contract
from camino.domain.codec import decode_text, wire
from camino.domain.model import (
    Asset, CaptureTime, ContractError, JourneyDay, MomentKind, Privacy, TextHistory,
    TextRevision, TimeSource, Trip, create_moment,
)
from camino.domain.revision_store import RevisionStore


def uid(number: int) -> str:
    return f"00000000-0000-0000-0000-{number:012x}"


def utc_ms(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp() * 1000)


class CaminoC03bContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "synthetic-camino.sqlite"
        self.store = RevisionStore(self.database)
        self.api = CaminoV1Contract(
            self.store, authenticate=lambda value: value == "Bearer synthetic-only",
        )
        self.trip = Trip(uid(1), "Synthetic trip", "cs", True, True)
        self.day = JourneyDay(uid(2), self.trip.id, "2026-09-20")
        self.capture = CaptureTime(
            utc_ms("2026-09-20T08:00:00"), "2026-09-20T10:00:00", 120,
            "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        self.moment = create_moment(
            id=uid(3), trip=self.trip, day=self.day, kind=MomentKind.VIDEO,
            captured=self.capture, new_moment_privacy=Privacy.DIARY,
        )
        self.asset = Asset(uid(4), self.moment.id, "video", "camera", 1000,
                           "a" * 64, 9000)
        self.epoch = self.store.state()["epoch"]

    def envelope(self, sequence, kind, payload, *, operation_id=None,
                 expected_revision=None, epoch=None):
        return {
            "contract_version": 1, "epoch": epoch or self.epoch,
            "operation_id": operation_id or uid(100 + sequence),
            "device_sequence": sequence, "device_id": uid(90), "kind": kind,
            "expected_revision": expected_revision, "payload": payload,
        }

    def send(self, data, *, raw=None, authorization="Bearer synthetic-only"):
        if raw is None:
            raw = json.dumps(data, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return self.api.handle(
            "POST", "/api/v1/operations", authorization=authorization,
            body=raw, content_type="application/json",
        )

    def register(self):
        for sequence, kind, value in (
            (1, "create_trip", self.trip),
            (2, "create_day", self.day),
            (3, "create_moment", self.moment),
            (4, "create_asset", self.asset),
        ):
            response = self.send(self.envelope(sequence, kind, wire(value)))
            self.assertEqual(response.status, 200, response.body)

    def test_revisions_survive_restart_without_media_reupload(self):
        self.register()
        lock = self.envelope(5, "update_metadata", {
            "moment_id": self.moment.id,
            "change": {"type": "privacy", "new_privacy": "owner_only", "user_action": "lock"},
        }, expected_revision=1)
        locked = self.send(lock)
        self.assertEqual(locked.status, 200, locked.body)
        self.assertEqual(locked.body["revision"], 2)
        next_day = JourneyDay(uid(5), self.trip.id, "2026-09-21")
        self.assertEqual(self.send(self.envelope(6, "create_day", wire(next_day))).status, 200)
        moved = self.send(self.envelope(7, "update_metadata", {
            "moment_id": self.moment.id,
            "change": {"type": "chapter", "day_id": next_day.id},
        }, expected_revision=2))
        self.assertEqual(moved.status, 200, moved.body)
        text = TextRevision(uid(20), self.moment.id, "human_revision", "synthetic note",
                            (), None, utc_ms("2026-09-20T10:01:00"))
        self.assertEqual(self.send(self.envelope(
            8, "append_text", wire(text), expected_revision=3,
        )).status, 200)
        original_retry = self.send(self.envelope(9, "create_moment", wire(self.moment)))
        self.assertEqual(original_retry.status, 200, original_retry.body)
        self.assertTrue(original_retry.body["reused"])
        reopened = RevisionStore(self.database)
        self.assertEqual(reopened.state()["cursor"], 9)
        self.assertEqual([row["privacy"] for row in reopened.moment_history(self.moment.id)],
                         ["diary", "owner_only", "owner_only"])
        self.assertEqual(reopened.moment(self.moment.id)["chapter_date"], "2026-09-21")
        self.assertEqual(reopened.moment(self.moment.id)["captured"], wire(self.capture))
        self.assertEqual(reopened.asset(self.asset.id), wire(self.asset))
        self.assertEqual(reopened.text_history(self.moment.id), (wire(text),))
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM assets").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM moment_revisions").fetchone()[0], 3)
        changes = self.api.handle(
            "GET", f"/api/v1/changes?epoch={self.epoch}&cursor=4",
            authorization="Bearer synthetic-only",
        )
        self.assertEqual(changes.status, 200)
        self.assertEqual([item["device_sequence"] for item in changes.body["events"]],
                         [5, 6, 7, 8, 9])
        self.assertEqual(changes.body["cursor"], 9)

    def test_exact_bytes_retry_and_different_bytes_conflict(self):
        request = self.envelope(1, "create_trip", wire(self.trip))
        raw = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        first = self.send(request, raw=raw)
        self.assertEqual(first.status, 200)
        self.api = CaminoV1Contract(RevisionStore(self.database),
                                    authenticate=lambda value: value == "Bearer synthetic-only")
        self.assertEqual(self.send(request, raw=raw), first)
        different_bytes = json.dumps(request, sort_keys=True).encode()
        conflict = self.send(request, raw=different_bytes)
        self.assertEqual(conflict.status, 409)
        self.assertEqual(conflict.body["error"]["code"], "operation_id_conflict")
        self.assertEqual(self.store.state()["cursor"], 1)
        self.assertTrue(self.store.state()["exports_blocked"])
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM conflict_candidates").fetchone()[0], 1)

    def test_revision_conflict_is_preserved_and_blocks_exports(self):
        self.register()
        self.assertEqual(self.store.viewer_safe_ids(self.trip.id), (self.moment.id,))
        stale = self.envelope(5, "update_metadata", {
            "moment_id": self.moment.id,
            "change": {"type": "privacy", "new_privacy": "owner_only", "user_action": "lock"},
        }, expected_revision=999)
        result = self.send(stale)
        self.assertEqual(result.status, 409)
        self.assertEqual(result.body["error"]["code"], "revision_conflict")
        self.assertEqual(result.body["error"]["current_revision"], 1)
        self.assertEqual(self.send(stale), result)
        changed = replace_dict(stale, payload={
            "moment_id": self.moment.id,
            "change": {"type": "hidden", "hidden": True},
        })
        self.assertEqual(self.send(changed).body["error"]["code"], "operation_id_conflict")
        self.assertEqual(self.store.moment(self.moment.id)["privacy"], "diary")
        self.assertEqual(self.store.state()["cursor"], 4)
        self.assertTrue(self.store.state()["exports_blocked"])
        self.assertEqual(self.store.viewer_safe_ids(self.trip.id), ())
        with sqlite3.connect(self.database) as connection:
            row = connection.execute(
                "SELECT request_body FROM conflict_candidates WHERE error_code='revision_conflict'"
            ).fetchone()
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM conflict_candidates"
            ).fetchone()[0], 2)
        self.assertEqual(json.loads(row[0])["payload"]["change"]["new_privacy"], "owner_only")

    def test_gap_does_not_advance_cursor_or_skip_operation(self):
        request = self.envelope(2, "create_trip", wire(self.trip))
        result = self.send(request)
        self.assertEqual(result.status, 409)
        self.assertEqual(result.body["error"]["code"], "sequence_gap")
        self.assertEqual(self.store.state()["cursor"], 0)
        self.assertEqual(self.send(self.envelope(1, "create_trip", wire(self.trip))).status, 200)
        self.assertEqual(self.send(request).status, 200)
        self.assertEqual(self.store.state()["cursor"], 2)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM trips").fetchone()[0], 1)

    def test_one_writer_is_bound_by_first_accepted_operation(self):
        first = self.envelope(1, "create_trip", wire(self.trip))
        self.assertEqual(self.send(first).status, 200)
        self.assertEqual(self.store.state()["writer_device_id"], uid(90))
        second_phone = replace_dict(self.envelope(2, "create_day", wire(self.day)),
                                    device_id=uid(91))
        response = self.send(second_phone)
        self.assertEqual(response.status, 409)
        self.assertEqual(response.body["error"]["code"], "writer_mismatch")
        self.assertEqual(self.store.state()["cursor"], 1)
        self.assertEqual(self.send(self.envelope(2, "create_day", wire(self.day))).status, 200)

    def test_same_object_id_with_changed_content_is_durable_conflict(self):
        self.assertEqual(self.send(self.envelope(1, "create_trip", wire(self.trip))).status, 200)
        changed = wire(self.trip)
        changed["name"] = "Different synthetic trip"
        response = self.send(self.envelope(2, "create_trip", changed))
        self.assertEqual(response.status, 409)
        self.assertEqual(response.body["error"]["code"], "identity_conflict")
        self.assertEqual(self.store.state()["cursor"], 1)
        self.assertTrue(self.store.state()["exports_blocked"])

    def test_restore_epoch_requires_inventory_comparison_and_keeps_block(self):
        self.register()
        old_epoch = self.epoch
        changed = self.store.rotate_epoch_for_restore()
        self.assertNotEqual(changed["epoch"], old_epoch)
        self.assertTrue(changed["reconciliation_required"])
        self.assertTrue(changed["exports_blocked"])
        self.assertEqual(self.store.viewer_safe_ids(self.trip.id), ())
        stale = self.send(self.envelope(5, "update_metadata", {
            "moment_id": self.moment.id,
            "change": {"type": "privacy", "new_privacy": "owner_only", "user_action": "lock"},
        }, expected_revision=1))
        self.assertEqual(stale.body["error"]["code"], "epoch_mismatch")
        inventory = {
            "contract_version": 1, "last_known_epoch": old_epoch,
            "moments": [{"id": self.moment.id, "revision": 2, "privacy": "owner_only"}],
        }
        response = self.api.handle(
            "POST", "/api/v1/reconcile", authorization="Bearer synthetic-only",
            body=json.dumps(inventory).encode(), content_type="application/json",
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["differences"],
                         [{"id": self.moment.id, "reason": "server_older"}])
        self.assertTrue(response.body["exports_blocked"])
        self.assertTrue(RevisionStore(self.database).state()["reconciliation_required"])
        old_cursor = self.api.handle(
            "GET", f"/api/v1/changes?epoch={old_epoch}&cursor=4",
            authorization="Bearer synthetic-only",
        )
        self.assertEqual(old_cursor.body["error"]["code"], "epoch_mismatch")

    def test_transaction_rolls_back_projection_if_receipt_write_fails(self):
        self.register()
        with sqlite3.connect(self.database) as connection:
            connection.execute(
                "CREATE TRIGGER synthetic_abort BEFORE INSERT ON accepted_operations "
                "WHEN NEW.kind='update_metadata' BEGIN SELECT RAISE(ABORT,'synthetic'); END"
            )
        lock = self.envelope(5, "update_metadata", {
            "moment_id": self.moment.id,
            "change": {"type": "privacy", "new_privacy": "owner_only", "user_action": "lock"},
        }, expected_revision=1)
        response = self.send(lock)
        self.assertEqual(response.status, 503)
        reopened = RevisionStore(self.database)
        self.assertEqual(reopened.state()["cursor"], 4)
        self.assertEqual(reopened.moment(self.moment.id)["privacy"], "diary")
        self.assertEqual(len(reopened.moment_history(self.moment.id)), 1)

    def test_errors_authorization_version_shape_and_private_reflection(self):
        state = self.api.handle("GET", "/api/v1/state", authorization="Bearer wrong")
        self.assertEqual(state.status, 401)
        self.assertEqual(state.body["error"]["code"], "unauthorized")
        unsupported = self.api.handle("GET", "/api/v2/state",
                                      authorization="Bearer synthetic-only")
        self.assertEqual(unsupported.status, 426)
        bad_version = self.send(replace_dict(self.envelope(1, "create_trip", wire(self.trip)),
                                             contract_version=2))
        self.assertEqual(bad_version.status, 426)
        float_version = self.send(replace_dict(self.envelope(1, "create_trip", wire(self.trip)),
                                               contract_version=1.0))
        self.assertEqual(float_version.status, 426)
        unknown_field = self.send(replace_dict(self.envelope(1, "create_trip", wire(self.trip)),
                                                extra="synthetic"))
        self.assertEqual(unknown_field.status, 422)
        duplicate = self.send({}, raw=b'{"contract_version":1,"contract_version":1}')
        self.assertEqual(duplicate.status, 422)
        malformed_role = self.send(self.envelope(
            1, "append_text", {
                "id": uid(20), "moment_id": self.moment.id, "role": [],
                "content": "synthetic", "source_ids": [], "parent_revision_id": None,
                "created_at_utc_ms": utc_ms("2026-09-20T10:00:00"),
            }, expected_revision=1,
        ))
        self.assertEqual(malformed_role.status, 422)
        malformed_id = self.send(self.envelope(
            1, "update_metadata", {
                "moment_id": [], "change": {"type": "hidden", "hidden": True},
            }, expected_revision=1,
        ))
        self.assertEqual(malformed_id.status, 422)
        self.assertEqual(malformed_id.body["error"]["code"], "invalid_request")
        self.assertEqual(self.store.state()["cursor"], 0)
        self.assertEqual(self.send(self.envelope(1, "create_trip", wire(self.trip))).status, 200)
        self.assertEqual(self.send(self.envelope(2, "create_day", wire(self.day))).status, 200)
        reflection = create_moment(
            id=uid(8), trip=self.trip, day=self.day, kind=MomentKind.REFLECTION,
            captured=self.capture, new_moment_privacy=Privacy.DIARY,
        )
        forged = wire(reflection)
        forged["privacy"] = "diary"
        rejected = self.send(self.envelope(3, "create_moment", forged))
        self.assertEqual(rejected.status, 422)
        self.assertEqual(self.store.state()["cursor"], 2)
        private_read = self.api.handle(
            "GET", f"/api/v1/moments/{reflection.id}", authorization="Bearer wrong",
        )
        self.assertEqual(private_read.status, 401)
        self.assertNotIn("moment", private_read.body)

    def test_openapi_documents_exact_versioned_routes(self):
        document = Path(__file__).resolve().parents[1] / "camino/docs/C03b_OPENAPI_V1.json"
        spec = json.loads(document.read_text(encoding="utf-8"))
        self.assertEqual(spec["openapi"], "3.1.0")
        self.assertEqual(spec["info"]["version"], "1.0.0")
        self.assertEqual(set(spec["paths"]), {
            "/api/v1/state", "/api/v1/operations", "/api/v1/changes",
            "/api/v1/moments/{moment_id}", "/api/v1/moments/{moment_id}/text",
            "/api/v1/reconcile",
        })
        self.assertEqual(set(spec["components"]["schemas"]["OperationEnvelope"]
                             ["properties"]["kind"]["enum"]), {
            "create_trip", "create_day", "create_moment", "create_asset",
            "update_metadata", "append_text", "create_audio_layout",
        })
        self.assertEqual(spec["security"], [{"ownerBearer": []}])

    def test_private_database_permissions_are_required(self):
        self.assertEqual(self.database.stat().st_mode & 0o777, 0o600)
        self.database.chmod(0o644)
        with self.assertRaises(ContractError):
            RevisionStore(self.database)

    def test_human_text_remains_selected_after_later_ai_revision(self):
        self.register()
        original = TextRevision(uid(21), self.moment.id, "transcript_raw", "synthetic raw",
                                (), None, utc_ms("2026-09-20T10:00:00"))
        human = TextRevision(uid(22), self.moment.id, "human_revision", "synthetic edit",
                             (original.id,), original.id, utc_ms("2026-09-20T10:01:00"))
        ai = TextRevision(uid(23), self.moment.id, "transcript_clean", "synthetic AI",
                          (original.id,), original.id, utc_ms("2026-09-20T10:02:00"))
        for seq, item in ((5, original), (6, human), (7, ai)):
            self.assertEqual(self.send(self.envelope(
                seq, "append_text", wire(item), expected_revision=1,
            )).status, 200)
        persisted = RevisionStore(self.database).text_history(self.moment.id)
        history = TextHistory(tuple(decode_text(item) for item in persisted))
        self.assertEqual(history.reader_revision.id, human.id)
        self.assertEqual(len(persisted), 3)


def replace_dict(value, **changes):
    return {**value, **changes}


if __name__ == "__main__":
    unittest.main()
