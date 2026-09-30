"""Fast projection regressions without FastAPI, media codecs or paid services."""

import json
import importlib
import sys
import tempfile
import types
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from camino.domain.codec import wire
from camino.domain.model import JourneyDay, LocationFix, Privacy, ContractError
from tests.camino_viewer_fixture import ViewerFixture, uid
from camino.server.viewer_map import route_snapshot, map_page


def _viewer_class_without_fastapi():
    """Load the pure HTML projection without requiring the HTTP test stack."""
    loaded = sys.modules.get("camino.server.viewer")
    if loaded is not None:
        return loaded.CaminoViewer
    fastapi = types.ModuleType("fastapi")
    fastapi.APIRouter = type("APIRouter", (), {})
    fastapi.Request = type("Request", (), {})
    responses = types.ModuleType("fastapi.responses")
    for name in ("FileResponse", "HTMLResponse", "JSONResponse", "Response"):
        setattr(responses, name, type(name, (), {}))
    with patch.dict(sys.modules, {"fastapi": fastapi, "fastapi.responses": responses}):
        return importlib.import_module("camino.server.viewer").CaminoViewer


class ViewerProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.f = ViewerFixture(Path(self.tmp.name))

    def snapshot(self):
        return self.f.store.viewer_snapshot(self.f.trip.id)

    def test_route_capture_order_late_upload_and_chapter_do_not_move_points(self):
        for n, seconds in ((72, 50), (71, 20), (70, 20)):
            m = replace(self.f.public, id=uid(n),
                        captured=replace(self.f.capture, utc_ms=self.f.capture.utc_ms + seconds * 1000,
                                         local_wall=f"2026-09-25T10:00:{seconds:02d}"),
                        location=LocationFix(0, n / 10000, self.f.capture.utc_ms + seconds * 1000, 8))
            self.f.send("create_moment", wire(m))
        other = JourneyDay(uid(7), self.f.trip.id, "2026-09-24")
        self.f.send("create_day", wire(other))
        self.f.send("update_metadata", {"moment_id": uid(72), "change": {
            "type": "chapter", "day_id": other.id}}, expected=1)
        points = route_snapshot(self.snapshot(), root_path="/camino-api")["points"]
        self.assertEqual([p["id"] for p in points], [uid(70), uid(71), uid(72)])
        self.assertEqual([p["connect_previous"] for p in points], [False, True, True])
        self.assertEqual(points[-1]["day"], "2026-09-25")
        self.assertEqual(points[-1]["href"], f"/camino-api/viewer/days/2026-09-24#moment-{uid(72)}")

    def test_route_privacy_revoke_hide_unknown_recovery_and_missing_gps(self):
        m = self.f.moment(70, Privacy.DIARY, location=LocationFix(0, 0, self.f.capture.utc_ms, 8))
        self.f.moment(71, Privacy.OWNER_ONLY, location=LocationFix(66, 77, self.f.capture.utc_ms, 8))
        result = route_snapshot(self.snapshot())
        self.assertEqual(len(result["points"]), 1)
        for forbidden in (uid(71), self.f.private.id, "TAJNA", "assets", "measured_at", "excluded"):
            self.assertNotIn(forbidden, json.dumps(result))
        for privacy, hidden in (("owner_only", False), ("diary", True), ("unknown", False)):
            with self.f.store._connection() as c:
                c.execute("UPDATE moments SET body=? WHERE id=?", (json.dumps(wire(replace(m, privacy=privacy, hidden=hidden))), m.id))
            self.assertEqual(route_snapshot(self.snapshot()), {"points": []})
        with self.f.store._connection() as c:
            c.execute("UPDATE moments SET body=? WHERE id=?", (json.dumps(wire(m)), m.id))
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=False)
        self.assertEqual(route_snapshot(self.snapshot()), {"points": []})
        self.f.store.set_viewer_permission(self.f.trip.id, enabled=True)
        for flags in ("exports_blocked=1", "exports_blocked=0, reconciliation_required=1"):
            with self.f.store._connection() as c:
                c.execute("UPDATE meta SET " + flags)
            self.assertEqual(route_snapshot(self.snapshot()), {"points": []})

    def test_route_connects_every_new_gps_even_when_fix_is_poor_or_far(self):
        self.f.moment(70, Privacy.DIARY, location=LocationFix(0, 0, self.f.capture.utc_ms, 8))
        base = self.snapshot()["moments"][-1]
        # Isolated projection inputs: edge cases need no private/runtime archive.
        base = next(m for m in self.snapshot()["moments"] if m["map_point"])
        second = {**base, "id": uid(71), "captured_utc_ms": base["captured_utc_ms"] + 1000,
                  "map_point": {"latitude": 0, "longitude": .001, "accuracy_m": 8}}
        def linked(changes):
            return route_snapshot({"moments": [base, {**second, **changes}]})["points"][1]["connect_previous"]
        self.assertTrue(linked({}))
        for changes in ({"captured_local": "2026-09-26T00:00:00"},
                        {"captured_utc_ms": base["captured_utc_ms"] + 21600001},
                        {"capture_uncertain": True}, {"captured_utc_ms": None},
                        {"map_point": {"latitude": 0, "longitude": .001, "accuracy_m": 101}},
                        {"map_point": {"latitude": 0, "longitude": 10, "accuracy_m": 8}}):
            with self.subTest(changes=changes):
                self.assertTrue(linked(changes))
        self.assertEqual(route_snapshot({"moments": [m for m in self.snapshot()["moments"] if not m["map_point"]]}), {"points": []})

    def test_map_shell_contains_no_diary_and_only_local_scripts(self):
        html = map_page("/camino-api")
        self.assertIn('/camino-api/viewer/map-assets/map.js', html)
        self.assertIn('id="open-map"', html)
        self.assertNotIn('src="https:', html)
        self.assertNotIn('tile.openstreetmap.org', html)
        self.assertNotIn(self.f.public.id, html)
        with self.assertRaises(ContractError):
            map_page('//untrusted.test')

    def test_attachment_titles_reopen_clear_keep_originals_and_follow_privacy(self):
        from camino.domain.revision_store import RevisionStore
        from tests.test_camino_audio_layout import layout
        photo = self.f.upload(30, "photo", b"photo")
        video = self.f.upload(31, "video", b"video")
        self.f.upload(32, "audio", b"audio-one")
        self.f.upload(33, "audio", b"audio-two")
        self.f.send("create_audio_layout", layout(50, [32, 33]))
        self.f.upload(40, "photo", b"private", private=True)
        original = self.f.store.moment(self.f.public.id)
        self.assertNotIn("attachment_titles", original)
        for revision, (kind, target, title) in enumerate([
            ("asset", 30, "Foto 🥾"), ("asset", 31, "Video"), ("audio_session", 50, "Celý komentář")
        ], 1):
            self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
                "type": "attachment_title", "attachment": {"kind": kind, "target_id": uid(target), "title": title}
            }}, expected=revision)
        self.f.send("update_metadata", {"moment_id": self.f.private.id, "change": {
            "type": "attachment_title", "attachment": {"kind": "asset", "target_id": uid(40), "title": "SECRET-TITLE"}
        }}, expected=1)
        reopened = RevisionStore(self.f.root / "metadata.sqlite")
        self.assertEqual(len(reopened.moment(self.f.public.id)["attachment_titles"]), 3)
        self.assertEqual(self.f.store.asset(uid(30)), photo)
        self.assertEqual(self.f.store.asset(uid(31)), video)
        self.assertNotIn("SECRET-TITLE", json.dumps(self.snapshot()))
        self.f.send("create_moment", original)  # Historical identity still matches.
        self.f.send("create_asset", photo)
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "attachment_title", "attachment": {"kind": "asset", "target_id": uid(30), "title": ""}
        }}, expected=4)
        self.assertEqual(len(self.snapshot()["moments"][0]["attachment_titles"]), 2)
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "privacy", "new_privacy": "owner_only", "user_action": "lock"}}, expected=5)
        self.assertEqual(self.snapshot()["moments"], [])

    def test_photo_video_media_use_two_column_grid_and_wrapped_titles(self):
        viewer_class = _viewer_class_without_fastapi()
        photo = self.f.upload(30, "photo", b"photo")
        video_one = self.f.upload(31, "video", b"video-one")
        video_two = self.f.upload(32, "video", b"video-two")
        photo_two = self.f.upload(33, "photo", b"photo-two")
        long_title = "Dlouhý název fotografie, který se musí v mřížce zalomit na další řádek"
        revision = self.f.store.moment(self.f.public.id)["revision"]
        self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
            "type": "attachment_title", "attachment": {
                "kind": "asset", "target_id": photo["id"], "title": long_title
            }}}, expected=revision)

        class ReadyCopies:
            @staticmethod
            def ready(_asset, verify=False):
                return {"ready": object()}

        viewer = viewer_class(self.f.store, None, ReadyCopies(), None, self.f.trip.id)
        page = viewer.page("2026-09-25")
        self.assertIn('class="media-grid" aria-label="Fotografie a videa"', page)
        self.assertEqual(page.count('class="media-tile"'), 4)
        self.assertEqual(page.count('class="media-title"'), 4)
        self.assertIn('class="media-open"', page)
        self.assertIn('id="mediaLightbox"', page)
        self.assertIn('aria-label="Zvětšená fotografie"', page)
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", page)
        self.assertIn("min-height:2.6em", page)
        self.assertEqual(page.count('class="media-video-preview"'), 2)
        self.assertEqual(page.count('class="media-video-badge"'), 2)
        self.assertIn("▶ Video", page)
        self.assertIn("overflow-wrap:anywhere", page)
        self.assertIn("Dlouhý název fotografie, který se musí v mřížce zalomit", page)
        positions = [page.index(asset["id"]) for asset in (photo, video_one, video_two, photo_two)]
        self.assertEqual(positions, sorted(positions))

    def test_attachment_title_rejects_foreign_missing_audio_segments_and_invalid_values(self):
        from tests.test_camino_audio_layout import layout
        self.f.upload(30, "photo", b"photo")
        self.f.upload(31, "audio", b"audio")
        self.f.upload(40, "photo", b"private", private=True)
        self.f.upload(41, "audio", b"private audio", private=True)
        self.f.send("create_audio_layout", layout(60, [41], moment=4))
        for kind, target, title in [("asset", 40, "Foreign"), ("asset", 31, "Segment"),
                                   ("asset", 99, "Missing"), ("audio_session", 60, "Foreign audio"),
                                   ("audio_session", 61, "Missing audio"), ("asset", 30, "bad\nline"),
                                   ("asset", 30, "x" * 161), ("unknown", 30, "Bad kind")]:
            with self.subTest(kind=kind, target=target), self.assertRaises(ContractError):
                self.f.send("update_metadata", {"moment_id": self.f.public.id, "change": {
                    "type": "attachment_title", "attachment": {"kind": kind, "target_id": uid(target), "title": title}
                }}, expected=1)
            self.f.sequence -= 1
            self.assertEqual(self.f.store.moment(self.f.public.id)["revision"], 1)

    def test_title_revisions_reopen_clear_and_privacy(self):
        from camino.domain.revision_store import RevisionStore
        old = self.f.store.moment(self.f.public.id)
        self.assertNotIn("title", old)
        self.f.send("update_metadata", {"moment_id": self.f.public.id,
                    "change": {"type": "title", "title": "Večer u řeky"}}, expected=1)
        self.f.send("update_metadata", {"moment_id": self.f.private.id,
                    "change": {"type": "title", "title": "TAJNY-NAZEV"}}, expected=1)
        reopened = RevisionStore(self.f.root / "metadata.sqlite")
        self.assertEqual(reopened.moment(self.f.public.id)["title"], "Večer u řeky")
        self.assertEqual(self.snapshot()["moments"][0]["title"], "Večer u řeky")
        self.assertNotIn("TAJNY-NAZEV", json.dumps(self.snapshot()))
        # Legacy unnamed identity can still be retried under a new envelope.
        self.f.send("create_moment", old)
        self.f.send("update_metadata", {"moment_id": self.f.public.id,
                    "change": {"type": "title", "title": ""}}, expected=2)
        self.assertEqual(self.snapshot()["moments"][0]["title"], "")
        self.f.send("update_metadata", {"moment_id": self.f.public.id,
                    "change": {"type": "privacy", "new_privacy": "owner_only",
                               "user_action": "lock"}}, expected=3)
        self.assertEqual(self.snapshot()["moments"], [])

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
