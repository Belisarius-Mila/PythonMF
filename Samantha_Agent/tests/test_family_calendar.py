from __future__ import annotations

import json
import stat
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from app.family_calendar import (
    DEFAULT_FAMILY_CALENDAR_PREFILL,
    ensure_family_calendar_prefill,
    family_calendar_status,
    load_family_people,
    notification_candidates,
    save_family_person,
    set_family_person_active,
    upcoming_family_events,
)


class FamilyCalendarTests(unittest.TestCase):
    def test_authorized_default_prefill_is_complete_and_valid(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"

            result = ensure_family_calendar_prefill(
                path=path,
                today=date(2026, 7, 19),
                now=datetime(2026, 7, 19, 8, 0, tzinfo=timezone.utc),
            )
            people = load_family_people(path, today=date(2026, 7, 19))

        self.assertTrue(result["applied"])
        self.assertEqual(result["count"], len(DEFAULT_FAMILY_CALENDAR_PREFILL))
        self.assertEqual(len(people), len(DEFAULT_FAMILY_CALENDAR_PREFILL))
        self.assertTrue(all(person.name_day is not None for person in people))
        self.assertTrue(all(person.birth_date is None for person in people))

    def test_prefill_is_idempotent_and_preserves_existing_registry(self) -> None:
        first_records = (
            {
                "id": "person-seedaaaa0001",
                "display_name": "Alena",
                "relation": "teta",
                "name_day": "08-13",
            },
        )
        second_records = (
            {
                "id": "person-seedbbbb0002",
                "display_name": "Běla",
                "relation": "sestřenice",
                "name_day": "01-21",
            },
        )
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"

            first = ensure_family_calendar_prefill(
                path=path,
                records=first_records,
                today=date(2026, 7, 19),
            )
            saved = save_family_person(
                person_id="person-seedaaaa0001",
                display_name="Alena",
                relation="teta",
                birth_date="1980-04-03",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 19),
            )
            second = ensure_family_calendar_prefill(
                path=path,
                records=second_records,
                today=date(2026, 7, 19),
            )
            people = load_family_people(path, today=date(2026, 7, 19))

        self.assertTrue(first["applied"])
        self.assertFalse(second["applied"])
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0].person_id, saved.person_id)
        self.assertEqual(people[0].birth_date, date(1980, 4, 3))

    def test_missing_private_registry_is_an_empty_calendar(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"

            people = load_family_people(path)
            status = family_calendar_status(path=path, today=date(2026, 7, 18))

        self.assertEqual(people, [])
        self.assertEqual(status["counts"]["people"], 0)
        self.assertEqual(status["events"], [])

    def test_create_update_and_deactivate_person_without_deletion(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "family" / "people.json"
            now = datetime(2026, 7, 18, 8, 0, tzinfo=timezone.utc)
            created = save_family_person(
                display_name="Alena",
                relation="teta",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 18),
                now=now,
                person_id_factory=lambda: "person-aaaaaaaaaaaa",
            )
            updated = save_family_person(
                person_id=created.person_id,
                display_name="Alena",
                relation="teta",
                birth_date="1975-04-03",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 18),
                now=datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
            )
            deactivated = set_family_person_active(
                created.person_id,
                active=False,
                path=path,
                now=datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc),
            )
            stored = json.loads(path.read_text(encoding="utf-8"))
            file_mode = stat.S_IMODE(path.stat().st_mode)
            directory_mode = stat.S_IMODE(path.parent.stat().st_mode)

        self.assertEqual(updated.birth_date, date(1975, 4, 3))
        self.assertEqual(updated.created_at, created.created_at)
        self.assertFalse(deactivated.active)
        self.assertEqual(stored["schema_version"], 1)
        self.assertEqual(len(stored["people"]), 1)
        self.assertFalse(stored["people"][0]["active"])
        self.assertEqual(file_mode, 0o600)
        self.assertEqual(directory_mode, 0o700)

    def test_validation_rejects_missing_invalid_or_duplicate_dates(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            with self.assertRaisesRegex(ValueError, "datum narození nebo datum svátku"):
                save_family_person(display_name="Bez data", path=path, today=date(2026, 7, 18))
            with self.assertRaisesRegex(ValueError, "RRRR-MM-DD"):
                save_family_person(
                    display_name="Chybné narození",
                    birth_date="18. 7. 1980",
                    path=path,
                    today=date(2026, 7, 18),
                )
            with self.assertRaisesRegex(ValueError, "budoucnosti"):
                save_family_person(
                    display_name="Budoucí datum",
                    birth_date="2027-01-01",
                    path=path,
                    today=date(2026, 7, 18),
                )
            with self.assertRaisesRegex(ValueError, "Datum svátku není platné"):
                save_family_person(
                    display_name="Chybný svátek",
                    name_day="02-31",
                    path=path,
                    today=date(2026, 7, 18),
                )
            save_family_person(
                display_name="Alena",
                relation="teta",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 18),
                person_id_factory=lambda: "person-bbbbbbbbbbbb",
            )
            with self.assertRaisesRegex(ValueError, "Stejná osoba"):
                save_family_person(
                    display_name="Alena",
                    relation="teta",
                    birth_date="1975-04-03",
                    path=path,
                    today=date(2026, 7, 18),
                )

    def test_same_display_name_with_different_relation_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            save_family_person(
                display_name="Alena",
                relation="teta",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 18),
                person_id_factory=lambda: "person-111111111111",
            )
            save_family_person(
                display_name="Alena",
                relation="prababička",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 18),
                person_id_factory=lambda: "person-222222222222",
            )

            people = load_family_people(path)

        self.assertEqual(len(people), 2)
        self.assertEqual({person.relation for person in people}, {"teta", "prababička"})

    def test_update_cannot_collide_with_another_active_person(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            first = save_family_person(
                display_name="Alena",
                relation="teta",
                name_day="08-13",
                path=path,
                today=date(2026, 7, 18),
                person_id_factory=lambda: "person-111111111111",
            )
            second = save_family_person(
                display_name="Běla",
                relation="sestřenice",
                name_day="01-21",
                path=path,
                today=date(2026, 7, 18),
                person_id_factory=lambda: "person-222222222222",
            )

            with self.assertRaisesRegex(ValueError, "Stejná osoba"):
                save_family_person(
                    person_id=second.person_id,
                    display_name=first.display_name,
                    relation=first.relation,
                    name_day="01-21",
                    path=path,
                    today=date(2026, 7, 18),
                )

    def test_loading_registry_rejects_future_birth_date(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "people": [
                            {
                                "id": "person-ffffffffffff",
                                "display_name": "Alena",
                                "relation": "teta",
                                "birth_date": "2027-01-01",
                                "name_day": "",
                                "reminders_enabled": True,
                                "active": True,
                                "created_at": "2026-07-18T08:00:00+00:00",
                                "updated_at": "2026-07-18T08:00:00+00:00",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "budoucnosti"):
                load_family_people(path, today=date(2026, 7, 18))

    def test_upcoming_events_include_age_and_cross_year_name_day(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            person = save_family_person(
                display_name="Alena",
                relation="teta",
                birth_date="1980-12-19",
                name_day="12-18",
                path=path,
                today=date(2026, 12, 17),
                person_id_factory=lambda: "person-cccccccccccc",
            )

            events = upcoming_family_events([person], today=date(2026, 12, 17), lookahead_days=3)

        self.assertEqual([event.event_type for event in events], ["name_day", "birthday"])
        self.assertEqual([event.days_until for event in events], [1, 2])
        self.assertIsNone(events[0].age)
        self.assertEqual(events[1].age, 46)
        self.assertTrue(events[0].catch_up)
        self.assertFalse(events[1].catch_up)

    def test_notification_candidates_skip_sent_event_and_allow_day_before_catch_up(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            person = save_family_person(
                display_name="Alena",
                relation="teta",
                birth_date="1980-12-19",
                name_day="12-18",
                path=path,
                today=date(2026, 12, 17),
                person_id_factory=lambda: "person-dddddddddddd",
            )
            events = upcoming_family_events([person], today=date(2026, 12, 17), lookahead_days=3)
            birthday_key = next(event.event_key for event in events if event.event_type == "birthday")

            candidates = notification_candidates(events, sent_event_keys={birthday_key})

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["event_type"], "name_day")
        self.assertEqual(candidates[0]["delivery_kind"], "catch_up")

    def test_february_29_birthday_uses_february_28_in_non_leap_year(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = Path(temp_dir) / "people.json"
            person = save_family_person(
                display_name="Robin",
                relation="bratranec",
                birth_date="2000-02-29",
                path=path,
                today=date(2027, 2, 26),
                person_id_factory=lambda: "person-eeeeeeeeeeee",
            )

            event = upcoming_family_events([person], today=date(2027, 2, 26), lookahead_days=2)[0]

        self.assertEqual(event.event_date, date(2027, 2, 28))
        self.assertEqual(event.days_until, 2)
        self.assertEqual(event.age, 27)


if __name__ == "__main__":
    unittest.main()
