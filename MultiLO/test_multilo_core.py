from __future__ import annotations

import unittest
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_layer import load_data
from multilo_core import (
    FLASH_OKRUH_TO_FOLDER,
    MONTH_ORDER,
    NumberCardItem,
    WeekdayCardItem,
    build_asset_index,
    build_flashcards,
    build_months,
    build_numbers,
    build_weekdays,
)


class MultiLOCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_data(BASE_DIR)
        cls.asset_index = build_asset_index(BASE_DIR / "Foto_normalized")

    def test_build_weekdays_no_numeric_value(self) -> None:
        cards = build_weekdays(self.bundle)
        self.assertEqual(len(cards), 7)
        self.assertTrue(all(isinstance(card, WeekdayCardItem) for card in cards))
        self.assertFalse(any(hasattr(card, "numeric_value") for card in cards))

    def test_build_numbers_has_numeric_value(self) -> None:
        cards = build_numbers(self.bundle)
        self.assertTrue(cards)
        self.assertTrue(all(isinstance(card, NumberCardItem) for card in cards))
        by_cz = {card.cz: card for card in cards}
        self.assertEqual(by_cz["Jedna"].numeric_value, 1)
        self.assertEqual(by_cz["Dva"].numeric_value, 2)
        self.assertEqual(by_cz["Deset"].numeric_value, 10)
        self.assertEqual(by_cz["Sto"].numeric_value, 100)

    def test_build_months_correct_count(self) -> None:
        cards = build_months(self.bundle)
        self.assertEqual(len(cards), len(MONTH_ORDER))
        self.assertEqual([card.cz for card in cards], MONTH_ORDER)

    def test_build_flashcards_returns_flashcard_items(self) -> None:
        okruh = "Zvířata"
        cards = build_flashcards(
            self.bundle,
            target_lang="IT",
            okruh=okruh,
            assets_for_folder=self.asset_index[FLASH_OKRUH_TO_FOLDER[okruh]],
        )
        self.assertTrue(cards)
        first = cards[0]
        self.assertEqual(first.okruh, okruh)
        self.assertTrue(hasattr(first, "target_text"))
        self.assertTrue(hasattr(first, "image_path"))


if __name__ == "__main__":
    unittest.main()
