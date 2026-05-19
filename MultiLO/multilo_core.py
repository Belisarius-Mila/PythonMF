"""Shared non-UI logic for MultiLO screens and standalone modules."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from data_layer import DataBundle, UserItemPreference


LANG_COL_MAP = {"FR": "fr", "IT": "it", "ES": "es", "EN": "en"}

FLASH_OKRUH_TO_FOLDER = {
    "Zelenina a ovoce": "VegFruit",
    "Zvířata": "Animals",
    "Ptáci": "Birds",
    "Rostliny": "Plants",
}

COLORS_OKRUH = "Základní barvy"
WEEKDAYS_OKRUH = "Dny v týdnu"
MONTHS_OKRUH = "Měsíce v roce"
NUMBERS_OKRUH = "Číslovky"

DAY_ORDER = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
MONTH_ORDER = [
    "Leden",
    "Únor",
    "Březen",
    "Duben",
    "Květen",
    "Červen",
    "Červenec",
    "Srpen",
    "Září",
    "Říjen",
    "Listopad",
    "Prosinec",
]
DEFAULT_DAY_COLORS = [
    "#4F46E5",
    "#0EA5E9",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#6B7280",
]

_FALLBACK_COLOR_HEX = {
    "Červená": "#EF4444",
    "Modrá": "#3B82F6",
    "Žlutá": "#FACC15",
    "Zelená": "#22C55E",
    "Oranžová": "#F97316",
    "Fialová": "#8B5CF6",
    "Růžová": "#EC4899",
    "Hnědá": "#92400E",
    "Černá": "#111827",
    "Bílá": "#F9FAFB",
    "Šedá": "#9CA3AF",
}

NUMBER_VALUE_BY_CZ = {
    "Jedna": 1,
    "Jeden": 1,
    "Dva": 2,
    "Dvě": 2,
    "Tři": 3,
    "Čtyři": 4,
    "Pět": 5,
    "Šest": 6,
    "Sedm": 7,
    "Osm": 8,
    "Devět": 9,
    "Deset": 10,
    "Jedenáct": 11,
    "Dvanáct": 12,
    "Třináct": 13,
    "Čtrnáct": 14,
    "Patnáct": 15,
    "Šestnáct": 16,
    "Sedmnáct": 17,
    "Osmnáct": 18,
    "Devatenáct": 19,
    "Dvacet": 20,
    "Třicet": 30,
    "Čtyřicet": 40,
    "Padesát": 50,
    "Šedesát": 60,
    "Sedmdesát": 70,
    "Osmdesát": 80,
    "Devadesát": 90,
    "Sto": 100,
    "Tisíc": 1000,
    "Milion": 1000000,
    "Jeden milion": 1000000,
}


@dataclass(frozen=True)
class FlashcardItem:
    item_id: int
    okruh: str
    cz: str
    target_text: str
    en: str
    image_path: Path | None


@dataclass(frozen=True)
class ColorCardItem:
    item_id: int
    cz: str
    target_text: str
    en: str
    image_path: Path | None


@dataclass(frozen=True)
class WeekdayCardItem:
    item_id: int
    cz: str
    fr: str
    it: str
    es: str
    en: str

    def target_text(self, lang: str) -> str:
        return getattr(self, LANG_COL_MAP[lang])


@dataclass(frozen=True)
class MonthCardItem:
    item_id: int
    cz: str
    fr: str
    it: str
    es: str
    en: str

    def target_text(self, lang: str) -> str:
        return getattr(self, LANG_COL_MAP[lang])


@dataclass(frozen=True)
class NumberCardItem:
    item_id: int
    cz: str
    fr: str
    it: str
    es: str
    en: str
    numeric_value: int | None

    def target_text(self, lang: str) -> str:
        return getattr(self, LANG_COL_MAP[lang])


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def build_asset_index(
    assets_root: Path,
    folder_map: dict[str, str] | None = None,
) -> dict[str, dict[str, Path]]:
    index: dict[str, dict[str, Path]] = {}
    for folder in (folder_map or FLASH_OKRUH_TO_FOLDER).values():
        dir_path = assets_root / folder
        folder_assets: dict[str, Path] = {}
        if dir_path.exists():
            for path in dir_path.glob("*"):
                if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    folder_assets[path.stem.lower()] = path
        index[folder] = folder_assets
    return index


def build_flashcards(
    bundle: DataBundle,
    target_lang: str,
    okruh: str,
    assets_for_folder: dict[str, Path],
) -> list[FlashcardItem]:
    col = LANG_COL_MAP[target_lang]
    cards: list[FlashcardItem] = []
    for item in bundle.vocab:
        if item.okruh != okruh:
            continue
        stem_candidates = {
            item.en.lower(),
            slugify(item.en),
            item.en.lower().replace(" ", "_"),
            item.en.lower().replace(" ", ""),
        }
        image_path = None
        for stem in stem_candidates:
            if stem in assets_for_folder:
                image_path = assets_for_folder[stem]
                break
        cards.append(
            FlashcardItem(
                item_id=item.item_id,
                okruh=item.okruh,
                cz=item.cz,
                target_text=getattr(item, col),
                en=item.en,
                image_path=image_path,
            )
        )
    return cards


def build_assets(assets_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if assets_dir.exists():
        for path in assets_dir.glob("*"):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                out[path.stem.lower()] = path
    return out


def build_color_cards(
    bundle: DataBundle,
    target_lang: str,
    assets: dict[str, Path],
) -> list[ColorCardItem]:
    col = LANG_COL_MAP[target_lang]
    cards: list[ColorCardItem] = []
    for item in bundle.vocab:
        if item.okruh != COLORS_OKRUH:
            continue
        stem_candidates = {
            item.en.lower(),
            slugify(item.en),
            item.en.lower().replace(" ", "_"),
            item.en.lower().replace(" ", ""),
        }
        image_path = None
        for stem in stem_candidates:
            if stem in assets:
                image_path = assets[stem]
                break
        cards.append(
            ColorCardItem(
                item_id=item.item_id,
                cz=item.cz,
                target_text=getattr(item, col),
                en=item.en,
                image_path=image_path,
            )
        )
    return cards


def build_weekdays(bundle: DataBundle) -> list[WeekdayCardItem]:
    by_cz = {item.cz: item for item in bundle.vocab if item.okruh == WEEKDAYS_OKRUH}
    cards: list[WeekdayCardItem] = []
    for day in DAY_ORDER:
        item = by_cz.get(day)
        if item is None:
            continue
        cards.append(
            WeekdayCardItem(
                item_id=item.item_id,
                cz=item.cz,
                fr=item.fr,
                it=item.it,
                es=item.es,
                en=item.en,
            )
        )
    return cards


def build_months(bundle: DataBundle) -> list[MonthCardItem]:
    by_cz = {item.cz: item for item in bundle.vocab if item.okruh == MONTHS_OKRUH}
    cards: list[MonthCardItem] = []
    for month in MONTH_ORDER:
        item = by_cz.get(month)
        if item is None:
            continue
        cards.append(
            MonthCardItem(
                item_id=item.item_id,
                cz=item.cz,
                fr=item.fr,
                it=item.it,
                es=item.es,
                en=item.en,
            )
        )
    return cards


def build_numbers(bundle: DataBundle) -> list[NumberCardItem]:
    cards: list[NumberCardItem] = []
    for item in bundle.vocab:
        if item.okruh != NUMBERS_OKRUH:
            continue
        cards.append(
            NumberCardItem(
                item_id=item.item_id,
                cz=item.cz,
                fr=item.fr,
                it=item.it,
                es=item.es,
                en=item.en,
                numeric_value=NUMBER_VALUE_BY_CZ.get(item.cz),
            )
        )
    return cards


def color_name_map(bundle: DataBundle) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in bundle.vocab:
        if item.okruh == COLORS_OKRUH and item.cz in _FALLBACK_COLOR_HEX:
            out[item.cz] = _FALLBACK_COLOR_HEX[item.cz]
    return out


def normalize_answer(value: str) -> str:
    value = unicodedata.normalize("NFKC", (value or "").strip())
    return " ".join(value.split()).casefold()


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def load_pref_map(
    bundle: DataBundle,
    user_id: str,
    cards: list[WeekdayCardItem],
) -> dict[int, UserItemPreference]:
    valid_item_ids = {card.item_id for card in cards}
    pref_map: dict[int, UserItemPreference] = {}
    for pref in bundle.prefs:
        if pref.user_id == user_id and pref.item_id in valid_item_ids:
            pref_map[pref.item_id] = pref
    return pref_map


def load_pref_map_from_file(
    prefs_path: Path,
    user_id: str,
    cards: list[WeekdayCardItem],
) -> dict[int, UserItemPreference]:
    if not prefs_path.exists():
        return {}
    valid_item_ids = {card.item_id for card in cards}
    pref_map: dict[int, UserItemPreference] = {}
    with prefs_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("user_id") or "").strip() != user_id:
                continue
            try:
                item_id = int((row.get("item_id") or "").strip())
            except ValueError:
                continue
            if item_id not in valid_item_ids:
                continue
            try:
                priority = int((row.get("priority") or "1").strip())
            except ValueError:
                priority = 1
            pref_map[item_id] = UserItemPreference(
                user_id=user_id,
                item_id=item_id,
                enabled=(row.get("enabled") or "").strip() in {"1", "true", "True", "yes", "YES"},
                priority=priority,
                assoc_color_hex=(row.get("assoc_color_hex") or "").strip(),
                assoc_note=(row.get("assoc_note") or "").strip(),
            )
    return pref_map


def write_user_color_prefs(
    prefs_path: Path,
    bundle: DataBundle,
    user_id: str,
    item_colors: dict[int, str],
) -> None:
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows: list[dict[str, str]] = []
    if prefs_path.exists():
        with prefs_path.open("r", encoding="utf-8-sig", newline="") as handle:
            existing_rows = list(csv.DictReader(handle))

    weekday_item_ids = set(item_colors)
    retained: list[dict[str, str]] = []
    for row in existing_rows:
        try:
            row_item_id = int((row.get("item_id") or "").strip())
        except ValueError:
            retained.append(row)
            continue
        if row.get("user_id") == user_id and row_item_id in weekday_item_ids:
            continue
        retained.append(row)

    for item_id, color_hex in item_colors.items():
        retained.append(
            {
                "user_id": user_id,
                "item_id": str(item_id),
                "enabled": "1",
                "priority": "2",
                "assoc_color_hex": color_hex,
                "assoc_note": "Barva dne",
            }
        )

    fieldnames = ["user_id", "item_id", "enabled", "priority", "assoc_color_hex", "assoc_note"]
    tmp_path = prefs_path.with_suffix(f"{prefs_path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(retained)
    tmp_path.replace(prefs_path)
