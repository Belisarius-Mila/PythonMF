"""Fast projection regressions without FastAPI, media codecs or paid services."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from camino.domain.codec import wire
from camino.domain.model import JourneyDay, LocationFix, Privacy
from tests.camino_viewer_fixture import ViewerFixture, uid


class ViewerProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f = ViewerFixture(Path(self.tmp.name))

    def snapshot(self):
        return self.f.store.viewer_snapshot(self.f.trip.id)

    def test_only_allowed_rows_and_no_private_counts_or_provenance(self):
        self.f.upload(31, "audio", b"secret", private=True)
        data = self.snapshot()
        self.assertEqual(len(data["moments"]), 1)
        value = json.dumps(data)
        for forbidden in ("TAJNA", self.f.private.id, uid(31), "location", "related_moment", "excluded"):
            self.assertNotIn(forbidden, value)

    def test_latest_privacy_and_hidden_revision_win(self):
        self.f.lock()
        self.assertEqual(self.snapshot()["moments"], [])
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "privacy", "new_privacy": "diary", "user_action": "unlock"}}, expected=2)
        self.assertEqual(len(self.snapshot()["moments"]), 1)
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "hidden", "hidden": True}}, expected=3)
        self.assertEqual(self.snapshot()["moments"], [])

    def test_map_point_only_from_allowed_moment_without_measurement_timestamp(self):
        point = LocationFix(0, 0, self.f.capture.utc_ms, 8)
        allowed = self.f.moment(70, Privacy.DIARY, location=point)
        self.f.moment(71, Privacy.OWNER_ONLY,
                      location=LocationFix(66.123456, 77.654321, self.f.capture.utc_ms, 5))
        data = self.snapshot()
        projected = {m["id"]: m for m in data["moments"]}
        self.assertEqual(projected[allowed.id]["map_point"],
                         {"latitude": 0, "longitude": 0, "accuracy_m": 8})
        self.assertIsNone(projected[self.f.public.id]["map_point"])
        for secret in ("66.123456", "77.654321", uid(71), "measured_at_utc_ms"):
            self.assertNotIn(secret, json.dumps(data))
        self.assertIsNotNone(self.f.store.moment(uid(71))["location"])

    def test_map_point_disappears_after_lock_hide_or_unknown_privacy(self):
        point = LocationFix(12.25, 34.5, self.f.capture.utc_ms, 150)
        moment = self.f.moment(70, Privacy.DIARY, location=point)
        for privacy, hidden in (("owner_only", False), ("diary", True), ("unknown", False)):
            with self.subTest(privacy=privacy, hidden=hidden):
                with self.f.store._connection() as c:
                    body = wire(replace(moment, privacy=privacy, hidden=hidden))
                    c.execute("UPDATE moments SET body=? WHERE id=?", (json.dumps(body), moment.id))
                self.assertNotIn("12.25", json.dumps(self.snapshot()))
                self.assertNotIn(moment.id, json.dumps(self.snapshot()))

    def test_map_point_cannot_bypass_trip_grant_conflict_or_recovery(self):
        self.f.moment(70, Privacy.DIARY,
                      location=LocationFix(12.25, 34.5, self.f.capture.utc_ms, 8))
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=False)
        self.assertEqual(self.snapshot()["moments"], [])
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=True)
        with self.f.store._connection() as c:
            c.execute("UPDATE meta SET exports_blocked=1")
        self.assertEqual(self.snapshot()["moments"], [])
        with self.f.store._connection() as c:
            c.execute("UPDATE meta SET exports_blocked=0, reconciliation_required=1")
        self.assertEqual(self.snapshot()["moments"], [])

    def test_conflict_restore_and_disabled_trip_close_projection(self):
        with self.f.store._connection() as c:
            c.execute("UPDATE meta SET exports_blocked=1")
        self.assertEqual(self.snapshot()["moments"], [])
        with self.f.store._connection() as c:
            c.execute("UPDATE meta SET exports_blocked=0")
            c.execute("UPDATE trips SET body=? WHERE id=?", (json.dumps(wire(replace(self.f.trip, viewer_enabled=False))), self.f.trip.id))
        self.assertEqual(self.snapshot()["moments"], [])
        self.f.store.rotate_epoch_for_restore()
        self.assertEqual(self.snapshot()["moments"], [])

    def test_unknown_privacy_and_other_trip_do_not_leak(self):
        with self.f.store._connection() as c:
            body = wire(replace(self.f.public, privacy="unknown"))
            c.execute("UPDATE moments SET body=? WHERE id=?", (json.dumps(body), self.f.public.id))
        self.assertEqual(self.snapshot()["moments"], [])
        self.assertEqual(self.f.store.viewer_snapshot(uid(999))["moments"], [])

    def test_text_provenance_cannot_reference_private_or_unknown_source(self):
        self.f.text(self.f.public, 22, "TAJNA-PARAFRAZE", sources=(self.f.private.id,), role="human_revision")
        self.assertEqual(self.snapshot()["moments"][0]["text"], "")

    def test_human_text_precedence_and_late_chapter(self):
        self.f.text(self.f.public, 22, "Lidská oprava", role="human_revision")
        self.f.text(self.f.public, 23, "Pozdní automatický text", role="transcript_clean")
        other = JourneyDay(uid(7), self.f.trip.id, "2026-09-24")
        self.f.send("create_day", wire(other))
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "chapter", "day_id": other.id}}, expected=1)
        m = self.snapshot()["moments"][0]
        self.assertEqual(m["day"], "2026-09-24")
        self.assertEqual(m["text"], "Lidská oprava")


if __name__ == "__main__":
    unittest.main()
