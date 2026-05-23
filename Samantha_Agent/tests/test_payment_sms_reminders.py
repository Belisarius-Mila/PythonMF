from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.reminders.payment_sms_tools import save_payment_sms_reminder_text
from app.reminders.store import load_reminders_store


RIXO_SMS = (
    "Dobry den, dekujeme za sjednani pojistky cislo 3275111280. "
    "Pripominame, ze pojisteni je potreba zaplatit pred datem jeho pocatku, "
    "jinak muze dojit k odlozeni pocatku pojisteni. Veskere instrukce k uhrade "
    "castky 4956.00 Kc naleznete na https://app.rixo.cz/platba/secret-token. "
    "Vase RIXO.cz"
)


class PaymentSmsReminderTests(unittest.TestCase):
    def test_without_confirmation_does_not_write_and_returns_generated_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"

            result = save_payment_sms_reminder_text(
                sms_text=RIXO_SMS,
                source_sender="RIXO.cz",
                source_date="2026-05-21",
                user_confirmed=False,
                confirmation_text="",
                path=path,
                today="2026-05-21",
            )

            self.assertIn("sms-overit-splatnost-3275111280-2026-05-21", result)
            self.assertIn("nic nezapisuji", result)
            self.assertFalse(path.exists())

    def test_unverified_due_date_saves_review_reminder_not_payment_fact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            reminder_id = "sms-overit-splatnost-3275111280-2026-05-22"

            result = save_payment_sms_reminder_text(
                sms_text=RIXO_SMS,
                source_sender="RIXO.cz",
                source_date="2026-05-21",
                review_due_date="2026-05-22",
                user_confirmed=True,
                confirmation_text=f"Potvrzuji, uloz pripominku {reminder_id}.",
                path=path,
                today="2026-05-21",
            )
            store = load_reminders_store(path)
            reminder = store["reminders"][0]
            raw = path.read_text(encoding="utf-8")

            self.assertIn(f"Ulozeno: {reminder_id}", result)
            self.assertEqual(reminder["id"], reminder_id)
            self.assertEqual(reminder["title"], "Overit splatnost platby 3275111280")
            self.assertEqual(reminder["due_date"], "2026-05-22")
            self.assertIn("skutecna splatnost nebyla overena", reminder["notes"])
            self.assertEqual(reminder["links"], [{"domain": "app.rixo.cz", "count": 1}])
            self.assertNotIn("https://", raw)
            self.assertNotIn("secret-token", raw)

    def test_verified_due_date_saves_payment_reminder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"
            reminder_id = "sms-platba-3275111280-2026-07-31"

            result = save_payment_sms_reminder_text(
                sms_text=RIXO_SMS,
                source_sender="RIXO.cz",
                source_date="2026-05-21",
                verified_due_date="2026-07-31",
                verified_start_date="2026-08-01",
                user_confirmed=True,
                confirmation_text=f"Potvrzuji, uloz pripominku {reminder_id}.",
                path=path,
                today="2026-05-21",
            )
            store = load_reminders_store(path)
            reminder = store["reminders"][0]
            raw = path.read_text(encoding="utf-8")

            self.assertIn(f"Ulozeno: {reminder_id}", result)
            self.assertEqual(reminder["title"], "Zaplatit pojistku/fakturu 3275111280")
            self.assertEqual(reminder["due_date"], "2026-07-31")
            self.assertIn("Overena splatnost: 2026-07-31", reminder["notes"])
            self.assertIn("Overeny pocatek noveho pojisteni/sluzby: 2026-08-01", reminder["notes"])
            self.assertIn("4956.00 Kc", reminder["notes"])
            self.assertNotIn("https://", raw)
            self.assertNotIn("secret-token", raw)

    def test_rejects_invalid_dates_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reminders.json"

            with self.assertRaisesRegex(ValueError, "verified_due_date"):
                save_payment_sms_reminder_text(
                    sms_text=RIXO_SMS,
                    verified_due_date="31.7.2026",
                    user_confirmed=True,
                    confirmation_text="Potvrzuji, uloz pripominku whatever.",
                    path=path,
                    today="2026-05-21",
                )

            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
