#!/usr/bin/env python3
"""Copy picture assets needed by the VocabularyFR static web prototype."""

from __future__ import annotations

import csv
import json
import re
import shutil
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CSV_PATH = ROOT / "VocabularyFR.csv"
PICT_DIR = PROJECT_ROOT / "Pict"
WEB_PICT_DIR = ROOT / "web" / "pict"
IMAGE_DIR = WEB_PICT_DIR / "images"
MAPPING_PATH = PICT_DIR / "mapping.json"

FEMALE_PRONOUNS = {"ona", "elle"}
MALE_PRONOUNS = {"on", "il", "lui"}
AMBIGUOUS_PRONOUNS = {"ja", "je", "moi", "vy", "vous"}
CONJUNCTION_WORDS = {"a", "ale", "nebo", "et", "ou", "mais"}
PREPOSITION_WORDS = {"na", "v", "ve", "do", "z", "u", "k", "sur", "dans", "de", "en"}
ADJ_ADV_WORDS = {"prislovce", "pridavnejmeno", "adverbe", "adjective", "adjectif"}
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def normalize_word(text: str) -> str:
    value = (text or "").strip().casefold()
    value = "".join(
        ch
        for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", value)


def tokenize_words(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+", (text or "").casefold())
    return [normalize_word(token) for token in raw if normalize_word(token)]


def probable_verb(fr_word: str) -> bool:
    word = normalize_word(fr_word)
    return bool(word) and word.endswith(("er", "ir", "re", "oir", "at", "it", "et", "yt"))


def probable_adj_or_adv(fr_word: str, cz_word: str) -> bool:
    cz = normalize_word(cz_word)
    fr = normalize_word(fr_word)
    if cz.endswith(("e", "ne", "ove", "ova", "ovy", "ych", "ich", "y", "a", "i")):
        return True
    return fr.endswith(("ment", "if", "ive", "eux", "euse", "al", "ale", "el", "elle", "ant", "ente"))


def pick_gender_fallback(fr_word: str, cz_word: str) -> str:
    key = f"{normalize_word(fr_word)}|{normalize_word(cz_word)}"
    score = sum(ord(ch) for ch in key)
    return "woman" if score % 2 else "man"


def picture_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for directory in (PICT_DIR, ROOT):
        for path in directory.iterdir():
            if path.suffix.casefold() not in EXTENSIONS:
                continue
            files.setdefault(normalize_word(path.stem), path)
    return files


def load_mapping() -> tuple[dict[str, str], dict[str, str]]:
    raw_mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    normalized: dict[str, str] = {}
    for key, value in raw_mapping.items():
        normalized_key = normalize_word(str(key))
        normalized_value = normalize_word(str(value))
        if normalized_key and normalized_value:
            normalized[normalized_key] = normalized_value
    return raw_mapping, normalized


def choose_picture_stem(row: dict[str, str], files: dict[str, Path], mapping: dict[str, str]) -> str:
    fr = (row.get("FR") or "").strip()
    cz = (row.get("CZ") or "").strip()
    keys = [normalize_word(fr), normalize_word(cz), *tokenize_words(fr), *tokenize_words(cz)]

    for key in keys:
        if key and key in files:
            return key
    for key in keys:
        mapped = mapping.get(key)
        if mapped and mapped in files:
            return mapped

    token_set = set(tokenize_words(fr) + tokenize_words(cz))
    if token_set & FEMALE_PRONOUNS:
        return "woman"
    if token_set & MALE_PRONOUNS:
        return "man"
    if token_set & AMBIGUOUS_PRONOUNS:
        return pick_gender_fallback(fr, cz)
    if token_set & CONJUNCTION_WORDS:
        return "conjuction"
    if token_set & PREPOSITION_WORDS:
        return "preposition"
    if token_set & ADJ_ADV_WORDS:
        return "proverbs"
    if probable_verb(fr):
        return "verb"
    if probable_adj_or_adv(fr, cz):
        return "proverbs"
    return "others"


def main() -> int:
    files = picture_files()
    raw_mapping, mapping = load_mapping()
    needed = {
        "others",
        "man",
        "woman",
        "conjuction",
        "preposition",
        "proverbs",
        "verb",
        "malefox",
        "femalefox",
    }

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            needed.add(choose_picture_stem(row, files, mapping))

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    missing: list[str] = []
    for stem in sorted(needed):
        source = files.get(stem)
        if not source:
            missing.append(stem)
            continue
        target = IMAGE_DIR / source.name
        shutil.copy2(source, target)
        copied.append(source.name)

    WEB_PICT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "mapping": raw_mapping,
        "images": sorted(copied),
        "missing_stems": sorted(missing),
    }
    (WEB_PICT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"copied={len(copied)}")
    print(f"missing={len(missing)}")
    print(f"target={WEB_PICT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
