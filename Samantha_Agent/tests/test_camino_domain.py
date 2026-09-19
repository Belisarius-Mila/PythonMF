"""Synthetic C03a contract checks; no private Camino material or runtime claims."""

import unittest
from dataclasses import replace
from datetime import datetime, timezone

from camino.domain import (
    Asset, CaptureTime, ChapterChange, ContractError, HiddenChange, JourneyDay,
    LocationFix, MomentHistory, MomentKind, OperationConflict, Privacy,
    PrivacyChange, RevisionConflict, ServerMoment, TextDraft, TextHistory,
    TextRevision, Trip, create_moment, create_private_addendum,
    select_viewer_candidates, server_revision_pending,
)
from camino.domain.model import TimeSource


def uid(number: int) -> str:
    return f"00000000-0000-0000-0000-{number:012x}"


def utc_ms(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp() * 1000)


class CaminoDomainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trip = Trip(uid(1), "Synthetic trip", "cs", True, True)
        self.day = JourneyDay(uid(2), self.trip.id, "2026-09-20")
        self.capture = CaptureTime(
            utc_ms("2026-09-20T08:00:00"), "2026-09-20T10:00:00", 120,
            "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )

    def moment(self, number: int = 3, kind: MomentKind = MomentKind.PHOTO,
               privacy: Privacy = Privacy.DIARY):
        return create_moment(
            id=uid(number), trip=self.trip, day=self.day, kind=kind,
            captured=self.capture, new_moment_privacy=privacy,
        )

    def server(self, moment, revision=1, privacy=None, hidden=False):
        return ServerMoment(
            moment.id, moment.trip_id, revision, privacy or moment.privacy,
            hidden, utc_ms("2026-09-22T08:00:00"),
        )

    def test_reflection_private_even_when_normal_default_is_diary(self):
        photo = self.moment()
        reflection = self.moment(4, MomentKind.REFLECTION)
        self.assertEqual(reflection.privacy, Privacy.OWNER_ONLY.value)
        self.assertEqual(select_viewer_candidates(self.trip, [self.server(photo), self.server(reflection)]),
                         (photo.id,))
        addendum = create_private_addendum(
            id=uid(5), trip=self.trip, parent=photo, day=self.day, captured=self.capture,
        )
        self.assertEqual(addendum.related_moment_id, photo.id)
        self.assertNotEqual(addendum.id, photo.id)
        self.assertEqual(photo.privacy, Privacy.DIARY.value)
        self.assertEqual(addendum.privacy, Privacy.OWNER_ONLY.value)
        with self.assertRaises(ContractError):
            replace(reflection, privacy=Privacy.DIARY.value)

    def test_reflection_release_requires_explicit_action_and_new_revision(self):
        reflection = self.moment(4, MomentKind.REFLECTION)
        history = MomentHistory((reflection,))
        wrong = PrivacyChange(uid(20), reflection.id, 1, 1, Privacy.DIARY, "unlock")
        with self.assertRaises(ContractError):
            history.apply(wrong)
        release = replace(wrong, user_action="insert_reflection_into_diary")
        self.assertEqual(release.queue_priority, 0)
        published = history.apply(release)
        self.assertEqual(published.current.revision, 2)
        self.assertEqual(history.current.privacy, Privacy.OWNER_ONLY.value)
        self.assertEqual(published.apply(release), published)
        self.assertEqual(select_viewer_candidates(self.trip, [self.server(reflection)]), ())
        self.assertEqual(select_viewer_candidates(self.trip, [self.server(published.current, 2)]),
                         (reflection.id,))

    def test_latest_accepted_server_revision_controls_viewer(self):
        diary = self.moment()
        other = self.moment(4)
        locked = self.server(diary, 2, Privacy.OWNER_ONLY.value)
        old = self.server(diary)
        hidden = self.server(other, 2, hidden=True)
        self.assertEqual(select_viewer_candidates(self.trip, [old, locked, self.server(other), hidden]), ())
        self.assertEqual(select_viewer_candidates(self.trip, [locked, old]), ())
        unknown = self.server(diary, 3, "future_privacy_value")
        self.assertEqual(select_viewer_candidates(self.trip, [old, unknown]), ())
        conflicting = self.server(diary, 1, Privacy.OWNER_ONLY.value)
        self.assertEqual(select_viewer_candidates(self.trip, [old, conflicting]), ())
        self.assertEqual(select_viewer_candidates(replace(self.trip, viewer_enabled=False), [old]), ())
        self.assertEqual(select_viewer_candidates(self.trip, [old, old]), (diary.id,))

    def test_operation_retry_conflict_and_immutable_history(self):
        photo = self.moment()
        history = MomentHistory((photo,))
        lock = PrivacyChange(uid(20), photo.id, 1, 1, Privacy.OWNER_ONLY, "lock")
        locked = history.apply(lock)
        self.assertTrue(server_revision_pending(locked.current, self.server(photo)))
        self.assertTrue(server_revision_pending(locked.current, None))
        self.assertFalse(server_revision_pending(
            locked.current, self.server(locked.current, 2)))
        self.assertEqual(locked.apply(lock), locked)
        self.assertEqual(history.current.privacy, Privacy.DIARY.value)
        with self.assertRaises(OperationConflict):
            locked.apply(replace(lock, user_action="unlock"))
        with self.assertRaises(RevisionConflict):
            locked.apply(PrivacyChange(uid(21), photo.id, 2, 1, Privacy.DIARY, "unlock"))
        with self.assertRaises(ContractError):
            PrivacyChange(uid(21), photo.id, True, 1, Privacy.DIARY, "unlock")
        unlocked = locked.apply(PrivacyChange(uid(21), photo.id, 2, 2, Privacy.DIARY, "unlock"))
        self.assertEqual([item.privacy for item in unlocked.versions],
                         [Privacy.DIARY.value, Privacy.OWNER_ONLY.value, Privacy.DIARY.value])

    def test_hide_and_chapter_move_keep_original_and_privacy(self):
        photo = self.moment()
        moved_day = JourneyDay(uid(8), self.trip.id, "2026-09-21")
        history = MomentHistory((photo,))
        moved = history.apply(ChapterChange(uid(22), photo.id, 1, 1, moved_day))
        self.assertEqual(moved.current.chapter_date, "2026-09-21")
        self.assertEqual(moved.current.captured, photo.captured)
        hidden = moved.apply(HiddenChange(uid(23), photo.id, 2, 2, True))
        self.assertEqual(hidden.current.privacy, photo.privacy)
        self.assertEqual(hidden.current.hidden, True)
        self.assertEqual(hidden.versions[0], photo)
        self.assertEqual(select_viewer_candidates(self.trip, [self.server(hidden.current, 3, hidden=True)]), ())

    def test_dst_repeated_hour_and_delayed_receipt_do_not_move_chapter(self):
        first = CaptureTime(
            utc_ms("2026-10-25T00:30:00"), "2026-10-25T02:30:00", 120,
            "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        second = CaptureTime(
            utc_ms("2026-10-25T01:30:00"), "2026-10-25T02:30:00", 60,
            "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        day = JourneyDay(uid(6), self.trip.id, "2026-10-25")
        a = create_moment(id=uid(7), trip=self.trip, day=day, kind=MomentKind.COMMENT,
                          captured=first, new_moment_privacy=Privacy.DIARY)
        b = create_moment(id=uid(8), trip=self.trip, day=day, kind=MomentKind.COMMENT,
                          captured=second, new_moment_privacy=Privacy.DIARY)
        self.assertEqual(a.chapter_date, b.chapter_date)
        self.assertNotEqual(a.captured.utc_ms, b.captured.utc_ms)
        self.assertEqual(a.captured.utc_offset_minutes, 120)
        self.assertEqual(b.captured.utc_offset_minutes, 60)
        self.assertEqual(self.server(a).received_at_utc_ms,
                         utc_ms("2026-09-22T08:00:00"))
        with self.assertRaises(ContractError):
            replace(first, utc_offset_minutes=60)

    def test_midnight_duration_and_uncertain_import(self):
        late = CaptureTime(
            utc_ms("2026-09-20T21:55:00"), "2026-09-20T23:55:00", 120,
            "Europe/Prague", TimeSource.DEVICE_CAPTURE,
        )
        moment = create_moment(id=uid(7), trip=self.trip, day=self.day,
                               kind=MomentKind.COMMENT, captured=late,
                               new_moment_privacy=Privacy.DIARY)
        audio = Asset(uid(9), moment.id, "audio", "recording", 1000, "a" * 64, 600_000)
        self.assertEqual(moment.chapter_date, "2026-09-20")
        self.assertEqual(audio.duration_ms, 600_000)
        assigned = CaptureTime(None, None, None, None, TimeSource.IMPORT_ASSIGNMENT, True)
        imported = create_moment(id=uid(10), trip=self.trip, day=self.day,
                                 kind=MomentKind.PHOTO, captured=assigned,
                                 new_moment_privacy=Privacy.OWNER_ONLY)
        self.assertIsNone(imported.captured.utc_offset_minutes)
        with self.assertRaises(ContractError):
            replace(assigned, uncertain=False)

    def test_location_is_optional_and_stale_fix_is_not_attached(self):
        self.assertIsNone(self.moment().location)
        point = LocationFix(50.0, 14.0, self.capture.utc_ms - 120_000, 101.0)
        current = create_moment(id=uid(7), trip=self.trip, day=self.day,
                                kind=MomentKind.PHOTO, captured=self.capture,
                                new_moment_privacy=Privacy.DIARY, location=point)
        self.assertEqual(current.location, point)
        self.assertTrue(point.approximate)
        stale = replace(point, measured_at_utc_ms=self.capture.utc_ms - 120_001)
        older = create_moment(id=uid(8), trip=self.trip, day=self.day,
                              kind=MomentKind.PHOTO, captured=self.capture,
                              new_moment_privacy=Privacy.DIARY, location=stale)
        self.assertIsNone(older.location)

    def test_text_draft_is_not_published_and_human_revision_wins_late_ai(self):
        original = TextRevision(uid(30), uid(3), "transcript_raw", "synthetic raw", (), None,
                                utc_ms("2026-09-20T10:00:00"))
        human = TextRevision(uid(31), uid(3), "human_revision", "synthetic correction",
                             (original.id,), original.id, utc_ms("2026-09-20T10:01:00"))
        late_ai = TextRevision(uid(32), uid(3), "transcript_clean", "synthetic late result",
                               (original.id,), original.id, utc_ms("2026-09-20T10:02:00"))
        history = TextHistory().add(original)
        draft = TextDraft(uid(3), original.id, "synthetic unsaved text",
                          utc_ms("2026-09-20T10:00:30"))
        history = history.save_draft(draft)
        self.assertEqual(history.reader_revision, original)
        history = history.add(human).add(late_ai)
        self.assertEqual(history.reader_revision, human)
        self.assertEqual(len(history.revisions), 3)
        self.assertEqual(history.draft, draft)


if __name__ == "__main__":
    unittest.main()
