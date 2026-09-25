"""Fast projection regressions without FastAPI, media codecs or paid services."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from camino.domain.codec import wire
from camino.domain.model import JourneyDay, Privacy
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
