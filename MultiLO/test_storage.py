from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from storage import (
    rank_item_ids_by_weakness,
    record_progress_event,
    record_progress_seen,
    reset_progress_for_okruh,
    summarize_progress_by_okruh,
)


class StorageTests(unittest.TestCase):
    def test_record_progress_event_creates_and_updates_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "progress.json"

            record_progress_event(
                user_id="me",
                item_id=10,
                mode="flashcards",
                okruh="Zvířata",
                lang="IT",
                correct=True,
                path=path,
            )
            record_progress_event(
                user_id="me",
                item_id=10,
                mode="flashcards",
                okruh="Zvířata",
                lang="IT",
                correct=False,
                path=path,
            )

            data = json.loads(path.read_text(encoding="utf-8"))
            item = data["users"]["me"]["items"]["10"]["flashcards"]
            self.assertEqual(item["okruh"], "Zvířata")
            self.assertEqual(item["last_lang"], "IT")
            self.assertEqual(item["seen_count"], 2)
            self.assertEqual(item["correct_count"], 1)
            self.assertEqual(item["wrong_count"], 1)
            self.assertEqual(item["last_result"], "wrong")
            self.assertIn("last_seen_at", item)

    def test_record_progress_seen_updates_seen_without_wrong(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "progress.json"

            record_progress_seen(
                user_id="wife",
                item_id=22,
                mode="numbers_reading",
                okruh="Číslovky",
                lang="FR",
                path=path,
            )

            data = json.loads(path.read_text(encoding="utf-8"))
            item = data["users"]["wife"]["items"]["22"]["numbers_reading"]
            self.assertEqual(item["okruh"], "Číslovky")
            self.assertEqual(item["last_lang"], "FR")
            self.assertEqual(item["seen_count"], 1)
            self.assertEqual(item["correct_count"], 0)
            self.assertEqual(item["wrong_count"], 0)
            self.assertEqual(item["last_result"], "seen")

    def test_summarize_progress_by_okruh_aggregates_seen_and_accuracy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "progress.json"

            record_progress_event(
                user_id="me",
                item_id=1,
                mode="quiz_1_of_3",
                okruh="Zvířata",
                lang="FR",
                correct=True,
                path=path,
            )
            record_progress_event(
                user_id="me",
                item_id=1,
                mode="quiz_1_of_3",
                okruh="Zvířata",
                lang="FR",
                correct=False,
                path=path,
            )
            record_progress_seen(
                user_id="me",
                item_id=2,
                mode="flashcards",
                okruh="Zvířata",
                lang="FR",
                path=path,
            )

            summary = summarize_progress_by_okruh(
                user_id="me",
                item_okruh_map={1: "Zvířata", 2: "Zvířata", 3: "Rostliny"},
                path=path,
            )

            self.assertEqual(summary["Zvířata"]["total_items"], 2)
            self.assertEqual(summary["Zvířata"]["seen_items"], 2)
            self.assertEqual(summary["Zvířata"]["correct_count"], 1)
            self.assertEqual(summary["Zvířata"]["wrong_count"], 1)
            self.assertEqual(summary["Rostliny"]["total_items"], 1)
            self.assertEqual(summary["Rostliny"]["seen_items"], 0)

    def test_rank_item_ids_by_weakness_puts_wrong_answers_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "progress.json"

            record_progress_event(
                user_id="me",
                item_id=1,
                mode="quiz_1_of_3",
                okruh="Zvířata",
                lang="FR",
                correct=False,
                path=path,
            )
            record_progress_event(
                user_id="me",
                item_id=2,
                mode="quiz_1_of_3",
                okruh="Zvířata",
                lang="FR",
                correct=True,
                path=path,
            )

            ranked = rank_item_ids_by_weakness(
                user_id="me",
                item_ids=[1, 2, 3],
                path=path,
            )

            self.assertEqual(ranked[0], 1)
            self.assertEqual(ranked[-1], 2)

    def test_reset_progress_for_okruh_removes_only_target_okruh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "progress.json"

            record_progress_event(
                user_id="me",
                item_id=11,
                mode="weekdays_writing",
                okruh="Dny v týdnu",
                lang="FR",
                correct=False,
                path=path,
            )
            record_progress_seen(
                user_id="me",
                item_id=12,
                mode="weekdays_sequence",
                okruh="Dny v týdnu",
                lang="FR",
                path=path,
            )
            record_progress_event(
                user_id="me",
                item_id=21,
                mode="months_writing",
                okruh="Měsíce v roce",
                lang="FR",
                correct=True,
                path=path,
            )

            reset_progress_for_okruh(
                user_id="me",
                okruh="Dny v týdnu",
                path=path,
            )

            data = json.loads(path.read_text(encoding="utf-8"))
            items = data["users"]["me"]["items"]
            self.assertNotIn("11", items)
            self.assertNotIn("12", items)
            self.assertIn("21", items)
            self.assertIn("months_writing", items["21"])


if __name__ == "__main__":
    unittest.main()
