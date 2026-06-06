#!/usr/bin/env python3
"""Audit Jana's VocabularyFR CSV against Pict mapping and existing images."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CSV = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/VocabularyFR/VocabularyFR.csv"
)
DEFAULT_PICT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/PythonMF/Pict"
)
DEFAULT_SOURCE_MAPPING = Path("/Users/miloslavfalta/Desktop/PythonMF/Pict/mapping.json")
DEFAULT_REPORT = Path(
    "/Users/miloslavfalta/Library/Mobile Documents/com~apple~CloudDocs/"
    "PythonMF/PictNew/jana_vocabularyfr_mapping_audit.md"
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
FEMALE_PRONOUNS = {"ona", "elle"}
MALE_PRONOUNS = {"on", "il", "lui"}
AMBIGUOUS_PRONOUNS = {"ja", "je", "moi", "vy", "vous"}
CONJUNCTION_WORDS = {"a", "ale", "nebo", "et", "ou", "mais"}
PREPOSITION_WORDS = {"na", "v", "ve", "do", "z", "u", "k", "sur", "dans", "de", "en"}
ADJ_ADV_WORDS = {"prislovce", "pridavnejmeno", "adverbe", "adjective", "adjectif"}
CATEGORY_FALLBACKS = {"others", "man", "woman", "conjuction", "preposition", "proverbs", "verb"}


@dataclass(frozen=True)
class ImageChoice:
    stem: str
    source: str
    key: str
    mapping_value: str = ""


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


def keys_for_row(row: dict[str, str]) -> list[str]:
    fr = (row.get("FR") or "").strip()
    cz = (row.get("CZ") or "").strip()
    keys = [normalize_word(fr), normalize_word(cz), *tokenize_words(fr), *tokenize_words(cz)]
    deduped: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if key and key not in seen:
            deduped.append(key)
            seen.add(key)
    return deduped


def image_files(pict_dir: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in pict_dir.iterdir():
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            files.setdefault(normalize_word(path.stem), path.name)
    return files


def load_mapping(mapping_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    raw = json.loads(mapping_path.read_text(encoding="utf-8"))
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        norm_key = normalize_word(str(key))
        norm_value = normalize_word(str(value))
        if norm_key and norm_value:
            normalized[norm_key] = norm_value
    return raw, normalized


def choose_picture(row: dict[str, str], files: dict[str, str], mapping: dict[str, str]) -> ImageChoice:
    fr = (row.get("FR") or "").strip()
    cz = (row.get("CZ") or "").strip()
    keys = keys_for_row(row)

    for key in keys:
        if key in files:
            return ImageChoice(stem=key, source="exact-file", key=key)

    for key in keys:
        mapped = mapping.get(key)
        if mapped and mapped in files:
            return ImageChoice(stem=mapped, source="mapping", key=key, mapping_value=mapped)

    token_set = set(tokenize_words(fr) + tokenize_words(cz))
    if token_set & FEMALE_PRONOUNS:
        return ImageChoice(stem="woman", source="fallback", key="female-pronoun")
    if token_set & MALE_PRONOUNS:
        return ImageChoice(stem="man", source="fallback", key="male-pronoun")
    if token_set & AMBIGUOUS_PRONOUNS:
        return ImageChoice(stem=pick_gender_fallback(fr, cz), source="fallback", key="ambiguous-pronoun")
    if token_set & CONJUNCTION_WORDS:
        return ImageChoice(stem="conjuction", source="fallback", key="conjunction")
    if token_set & PREPOSITION_WORDS:
        return ImageChoice(stem="preposition", source="fallback", key="preposition")
    if token_set & ADJ_ADV_WORDS:
        return ImageChoice(stem="proverbs", source="fallback", key="adj-adv-word")
    if probable_verb(fr):
        return ImageChoice(stem="verb", source="fallback", key="probable-verb")
    if probable_adj_or_adv(fr, cz):
        return ImageChoice(stem="proverbs", source="fallback", key="probable-adj-adv")
    return ImageChoice(stem="others", source="fallback", key="none")


def first_mapping_for_row(row: dict[str, str], mapping: dict[str, str]) -> tuple[str, str]:
    for key in keys_for_row(row):
        mapped = mapping.get(key)
        if mapped:
            return key, mapped
    return "", ""


def markdown_row(cells: list[str]) -> str:
    escaped = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells]
    return "| " + " | ".join(escaped) + " |"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--pict", type=Path, default=DEFAULT_PICT)
    parser.add_argument("--source-mapping", type=Path, default=DEFAULT_SOURCE_MAPPING)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    csv_path = args.csv.expanduser()
    pict_dir = args.pict.expanduser()
    source_mapping_path = args.source_mapping.expanduser()
    report_path = args.report.expanduser()
    mapping_path = pict_dir / "mapping.json"

    files = image_files(pict_dir)
    raw_mapping, mapping = load_mapping(mapping_path)
    raw_source_mapping, source_mapping = load_mapping(source_mapping_path)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    mapped_rows: list[tuple[dict[str, str], ImageChoice]] = []
    exact_rows: list[tuple[dict[str, str], ImageChoice]] = []
    fallback_rows: list[tuple[dict[str, str], ImageChoice]] = []
    mapping_value_without_file: list[tuple[dict[str, str], str, str]] = []
    full_cz_mapping_candidates: list[tuple[dict[str, str], ImageChoice, str]] = []
    source_mapping_can_fix_fallback: list[tuple[dict[str, str], str, str, str]] = []
    source_mapping_missing_entries: list[tuple[str, str]] = []
    source_mapping_different_entries: list[tuple[str, str, str]] = []

    for key, value in raw_source_mapping.items():
        if key not in raw_mapping and normalize_word(value) in files:
            source_mapping_missing_entries.append((key, value))
        elif key in raw_mapping and raw_mapping[key] != value:
            source_mapping_different_entries.append((key, raw_mapping[key], value))

    for row in rows:
        choice = choose_picture(row, files, mapping)
        first_key, first_value = first_mapping_for_row(row, mapping)
        if first_value and first_value not in files:
            mapping_value_without_file.append((row, first_key, first_value))

        if choice.source == "mapping":
            mapped_rows.append((row, choice))
        elif choice.source == "exact-file":
            exact_rows.append((row, choice))
        else:
            fallback_rows.append((row, choice))

        cz_norm = normalize_word(row.get("CZ", ""))
        if (
            cz_norm
            and cz_norm not in mapping
            and choice.stem in files
            and choice.stem not in CATEGORY_FALLBACKS
        ):
            full_cz_mapping_candidates.append((row, choice, files[choice.stem]))

        if choice.source == "fallback":
            source_choice = choose_picture(row, files, source_mapping)
            if (
                source_choice.source == "mapping"
                and source_choice.stem in files
                and source_choice.stem not in CATEGORY_FALLBACKS
            ):
                source_mapping_can_fix_fallback.append(
                    (
                        row,
                        source_choice.key,
                        source_choice.mapping_value,
                        files[source_choice.stem],
                    )
                )

    concrete_rows = mapped_rows + exact_rows
    report: list[str] = []
    report.append("# Jana VocabularyFR mapping audit")
    report.append("")
    report.append(f"CSV: `{csv_path}`")
    report.append(f"Pict: `{pict_dir}`")
    report.append(f"mapping.json: `{mapping_path}`")
    report.append(f"Zdrojovy mapping pro porovnani: `{source_mapping_path}`")
    report.append("")
    report.append("## Souhrn")
    report.append("")
    report.append(f"- Slovicek v CSV: {len(rows)}")
    report.append(f"- Jedinecnych obrazkovych stemu v Pict: {len(files)}")
    report.append(f"- Zaznamu v mapping.json: {len(raw_mapping)}")
    report.append(f"- Zaznamu ve zdrojovem mappingu: {len(raw_source_mapping)}")
    report.append(f"- Zdrojovych mapping zaznamu chybejicich u Jany, cilovy obrazek existuje: {len(source_mapping_missing_entries)}")
    report.append(f"- Zdrojovych mapping zaznamu s odlisnou hodnotou u Jany: {len(source_mapping_different_entries)}")
    report.append(f"- Radku s obrazkem pres mapping: {len(mapped_rows)}")
    report.append(f"- Radku s primou shodou nazvu obrazku bez mappingu: {len(exact_rows)}")
    report.append(f"- Radku jen s fallback/kategorii: {len(fallback_rows)}")
    report.append(f"- Fallback radku opravitelných zdrojovym mappingem na existujici obrazek: {len(source_mapping_can_fix_fallback)}")
    report.append(f"- Kandidatu na doplneni celeho CZ klice do mappingu: {len(full_cz_mapping_candidates)}")
    report.append(f"- Mapping hodnot bez existujiciho obrazku pro radky CSV: {len(mapping_value_without_file)}")
    report.append("")

    report.append("## Fallback radky, ktere opravi nas zdrojovy mapping")
    report.append("")
    report.append(
        "Tyto radky dnes u Jany padaji na obecny fallback, ale v nasem mapping.json "
        "uz existuje mapovani na obrazek, ktery Jana fyzicky ma v Pict."
    )
    report.append("")
    report.append(markdown_row(["Order", "FR", "CZ", "Chybejici mapping klic", "Hodnota", "Soubor"]))
    report.append(markdown_row(["---", "---", "---", "---", "---", "---"]))
    for row, key, value, filename in source_mapping_can_fix_fallback:
        report.append(
            markdown_row(
                [
                    row.get("Order", ""),
                    row.get("FR", ""),
                    row.get("CZ", ""),
                    key,
                    value,
                    filename,
                ]
            )
        )
    report.append("")

    if source_mapping_different_entries:
        report.append("## Pozor: stejne klice maji jinou hodnotu")
        report.append("")
        report.append(markdown_row(["Klic", "Jana", "Nase verze"]))
        report.append(markdown_row(["---", "---", "---"]))
        for key, jana_value, source_value in source_mapping_different_entries:
            report.append(markdown_row([key, jana_value, source_value]))
        report.append("")

    report.append("## Kandidati na doplneni mappingu k existujicim obrazkum")
    report.append("")
    report.append(
        "Tyto radky uz technicky najdou konkretni existujici obrazek pres dilci shodu "
        "nebo existujici mapping, ale cely cesky vyznam z CSV neni samostatny klic "
        "v mapping.json. Je to pomocny seznam k rucni revizi, ne automaticky apply plan."
    )
    report.append("")
    report.append(markdown_row(["Order", "FR", "CZ", "Navrh mappingu", "Soubor"]))
    report.append(markdown_row(["---", "---", "---", "---", "---"]))
    for row, choice, filename in full_cz_mapping_candidates:
        report.append(
            markdown_row(
                [
                    row.get("Order", ""),
                    row.get("FR", ""),
                    row.get("CZ", ""),
                    f"{row.get('CZ', '')} -> {choice.stem}",
                    filename,
                ]
            )
        )
    report.append("")

    report.append("## Radky jen s fallback obrazkem")
    report.append("")
    report.append(
        "Tyto radky nemaji primou shodu ani pouzitelny mapping na konkretni obrazek. "
        "Aplikace jim dava obecny fallback; tady bude potreba rucne rozhodnout, "
        "jestli pouzit existujici obrazek, nebo pozdeji vytvorit novy."
    )
    report.append("")
    report.append(markdown_row(["Order", "FR", "CZ", "Fallback", "Duvod"]))
    report.append(markdown_row(["---", "---", "---", "---", "---"]))
    for row, choice in fallback_rows:
        report.append(
            markdown_row(
                [
                    row.get("Order", ""),
                    row.get("FR", ""),
                    row.get("CZ", ""),
                    choice.stem,
                    choice.key,
                ]
            )
        )
    report.append("")

    if mapping_value_without_file:
        report.append("## Problem: mapping ukazuje na neexistujici obrazek")
        report.append("")
        report.append(markdown_row(["Order", "FR", "CZ", "Mapping klic", "Mapping hodnota"]))
        report.append(markdown_row(["---", "---", "---", "---", "---"]))
        for row, key, value in mapping_value_without_file:
            report.append(
                markdown_row(
                    [row.get("Order", ""), row.get("FR", ""), row.get("CZ", ""), key, value]
                )
            )
        report.append("")

    text = "\n".join(report) + "\n"

    print(f"CSV rows: {len(rows)}")
    print(f"Pict unique image stems: {len(files)}")
    print(f"Mapping entries: {len(raw_mapping)}")
    print(f"Source mapping entries: {len(raw_source_mapping)}")
    print(f"Source entries missing in Jana mapping with existing image: {len(source_mapping_missing_entries)}")
    print(f"Source entries with different value in Jana mapping: {len(source_mapping_different_entries)}")
    print(f"Rows via mapping: {len(mapped_rows)}")
    print(f"Rows via exact image filename: {len(exact_rows)}")
    print(f"Rows via fallback only: {len(fallback_rows)}")
    print(f"Fallback rows fixable by source mapping: {len(source_mapping_can_fix_fallback)}")
    print(f"Full-CZ mapping candidates: {len(full_cz_mapping_candidates)}")
    print(f"Mapping values without image: {len(mapping_value_without_file)}")
    print("")
    print("Fallback rows fixable by source mapping:")
    for row, key, value, filename in source_mapping_can_fix_fallback:
        print(
            f"- {row.get('Order')}: {row.get('FR')} | {row.get('CZ')} "
            f"-> {key}: {value} ({filename})"
        )
    print("")
    print("Fallback rows:")
    for row, choice in fallback_rows:
        print(
            f"- {row.get('Order')}: {row.get('FR')} | {row.get('CZ')} "
            f"-> {choice.stem} ({choice.key})"
        )

    if args.write_report:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
        print("")
        print(f"Report written: {report_path}")
    else:
        print("")
        print("DRY RUN: report jsem nezapsal. Pro zapis pouzij --write-report.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
