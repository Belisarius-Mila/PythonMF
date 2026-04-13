#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


APP_NAME = "VocabularyEN"
CSV_FILENAME = "VocabularyEN.csv"
SUPPORTED_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
FEMALE_PRONOUNS = {"she", "her", "hers", "ona", "ji", "jeji"}
MALE_PRONOUNS = {"he", "him", "his", "on", "ho", "jeho"}
AMBIGUOUS_PRONOUNS = {
    "i", "you", "we", "they", "it", "me", "us", "them",
    "ja", "ty", "my", "vy", "oni", "ono",
}
CONJUNCTION_WORDS = {"and", "or", "but", "nor", "so", "yet", "a", "nebo", "ale"}
PREPOSITION_WORDS = {
    "in", "on", "at", "to", "for", "from", "with", "by", "about", "under", "over", "between",
    "into", "through", "during", "before", "after", "without", "against", "among",
    "na", "v", "ve", "do", "z", "u", "k", "od", "po", "pro", "s", "bez", "mezi",
}
ADJ_ADV_WORDS = {"adjective", "adverb", "pridavnejmeno", "prislovce"}


def normalize_word(text: str) -> str:
    value = (text or "").strip().casefold()
    if not value:
        return ""
    value = "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", value)


def tokenize_words(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+", (text or "").casefold())
    return [normalize_word(token) for token in raw if normalize_word(token)]


def is_probable_verb(word: str) -> bool:
    normalized = normalize_word(word)
    if not normalized or " " in normalized:
        return False
    if normalized.startswith("to") and len(normalized) > 4:
        return True
    return normalized.endswith(("ing", "ed", "en", "fy", "ise", "ize"))


def is_probable_adj_or_adv(en_word: str, cz_word: str) -> bool:
    cz = normalize_word(cz_word)
    en = normalize_word(en_word)
    if cz.endswith(("e", "ne", "ove", "ova", "ovy", "ych", "ich", "y", "a", "i")):
        return True
    if en.endswith(("ly", "ous", "ful", "less", "able", "ible", "ive", "al", "ic", "ish")):
        return True
    return False


def pick_gender_for_ambiguous(en_word: str, cz_word: str) -> str:
    key = f"{normalize_word(en_word)}|{normalize_word(cz_word)}"
    if not key.strip("|"):
        return "man"
    score = sum(ord(ch) for ch in key)
    return "woman" if (score % 2) else "man"


def repair_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    repaired: list[dict[str, str]] = []
    for row in rows:
        en = (row.get("EN") or row.get("FR") or "").strip()
        cz = (row.get("CZ") or "").strip()
        sentence = (row.get("Sentence") or "").strip()
        sentence_t = (row.get("SentenceT") or "").strip()
        learned = (row.get("L") or "ne").strip().lower()
        hard_training = (row.get("HT") or "ne").strip().lower()

        if not en and not cz and not sentence:
            continue

        if learned not in ("ano", "ne"):
            learned = "ne"
        if hard_training not in ("ano", "ne"):
            hard_training = "ne"

        repaired.append(
            {
                "EN": en,
                "CZ": cz,
                "Order": "",
                "Sentence": sentence,
                "SentenceT": sentence_t,
                "L": learned,
                "HT": hard_training,
            }
        )

    for index, row in enumerate(repaired, start=1):
        row["Order"] = str(index)
    return repaired


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return repair_rows(list(csv.DictReader(handle)))


def build_picture_base_dirs(repo_root: Path, csv_path: Path) -> list[Path]:
    csv_dir = csv_path.parent.resolve()
    code_dir = csv_path.parent.resolve()
    dirs: list[Path] = []
    for path in (
        repo_root / "Pict",
        csv_dir / "Pict",
        code_dir / "Pict",
    ):
        resolved = path.resolve()
        if resolved not in dirs:
            dirs.append(resolved)
    return dirs


def mapping_file_candidates(base_dirs: list[Path], csv_path: Path) -> list[Path]:
    candidates = [base / "mapping.json" for base in base_dirs]
    candidates.append(csv_path.parent.resolve() / "mapping.json")
    dedup: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        dedup.append(resolved)
    return dedup


def load_external_mapping(base_dirs: list[Path], csv_path: Path) -> dict[str, str]:
    for path in mapping_file_candidates(base_dirs, csv_path):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        mapping: dict[str, str] = {}
        for key, value in data.items():
            normalized_key = normalize_word(str(key))
            normalized_value = normalize_word(str(value))
            if normalized_key and normalized_value:
                mapping[normalized_key] = normalized_value
        return mapping
    return {}


def discover_picture_stems(base_dirs: list[Path]) -> set[str]:
    stems: set[str] = set()
    for base_dir in base_dirs:
        if not base_dir.is_dir():
            continue
        for path in base_dir.iterdir():
            if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
                continue
            stems.add(normalize_word(path.stem))
    return stems


def choose_picture_stem(
    row: dict[str, str],
    picture_stems: set[str],
    synonym_image_map: dict[str, str],
) -> tuple[str, str]:
    en = (row.get("EN") or "").strip()
    cz = (row.get("CZ") or "").strip()
    en_norm = normalize_word(en)
    cz_norm = normalize_word(cz)
    tokens = tokenize_words(en) + tokenize_words(cz)

    for key in [en_norm, cz_norm] + tokens:
        if key and key in picture_stems:
            return key, "direct"

    for key in [en_norm, cz_norm] + tokens:
        mapped = synonym_image_map.get(key)
        if mapped:
            return mapped, "mapping"

    token_set = set(tokens)
    if token_set & FEMALE_PRONOUNS:
        return "woman", "fallback"
    if token_set & MALE_PRONOUNS:
        return "man", "fallback"
    if token_set & AMBIGUOUS_PRONOUNS:
        return pick_gender_for_ambiguous(en, cz), "fallback"
    if token_set & CONJUNCTION_WORDS:
        return "conjuction", "fallback"
    if token_set & PREPOSITION_WORDS:
        return "preposition", "fallback"
    if token_set & ADJ_ADV_WORDS:
        return "proverbs", "fallback"
    if is_probable_verb(en):
        return "verb", "fallback"
    if is_probable_adj_or_adv(en, cz):
        return "proverbs", "fallback"
    return "others", "fallback"


def find_picture_path(stem: str, base_dirs: list[Path]) -> Path | None:
    normalized_stem = normalize_word(stem)
    if not normalized_stem:
        return None
    candidate_names = [f"{normalized_stem}{suffix}" for suffix in SUPPORTED_IMAGE_SUFFIXES]
    for base_dir in base_dirs:
        for name in candidate_names:
            path = base_dir / name
            if path.exists():
                return path
    return None


def relative_posix_path(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def ensure_clean_assets_dir(target_dir: Path, expected_names: set[str]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for child in target_dir.iterdir():
        if child.is_file() and child.name not in expected_names:
            child.unlink()


def build_export_payload(
    rows: list[dict[str, str]],
    base_dirs: list[Path],
    synonym_image_map: dict[str, str],
    picture_stems: set[str],
    output_root: Path,
    asset_dir_name: str,
    source_csv_label: str,
) -> tuple[dict[str, object], dict[Path, str]]:
    asset_dir = output_root / "assets" / asset_dir_name
    asset_map: dict[Path, str] = {}
    items: list[dict[str, object]] = []
    image_source_counter: Counter[str] = Counter()

    for index, row in enumerate(rows, start=1):
        requested_stem, image_source = choose_picture_stem(row, picture_stems, synonym_image_map)
        source_path = find_picture_path(requested_stem, base_dirs)
        resolved_stem = requested_stem
        image_missing = False

        if source_path is None and requested_stem != "others":
            source_path = find_picture_path("others", base_dirs)
            resolved_stem = "others"
            image_source = f"{image_source}_to_others"

        if source_path is None:
            image_relative = None
            image_missing = True
        else:
            dest_name = f"{normalize_word(resolved_stem) or 'image'}{source_path.suffix.lower()}"
            asset_map[source_path] = dest_name
            image_relative = relative_posix_path(asset_dir / dest_name, output_root)

        image_source_counter[image_source] += 1
        item = {
            "id": index,
            "order": index,
            "en": row.get("EN", ""),
            "cz": row.get("CZ", ""),
            "sentenceEn": row.get("Sentence", ""),
            "sentenceCz": row.get("SentenceT", ""),
            "selected": row.get("L", "ne") == "ano",
            "hardTraining": row.get("HT", "ne") == "ano",
            "image": image_relative,
            "imageStem": resolved_stem,
            "imageRequestedStem": requested_stem,
            "imageSource": image_source,
            "imageMissing": image_missing,
        }
        items.append(item)

    payload = {
        "app": APP_NAME,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceCsv": source_csv_label,
        "itemCount": len(items),
        "stats": {
            "selected": sum(1 for row in rows if row.get("L", "ne") == "ano"),
            "hardTraining": sum(1 for row in rows if row.get("HT", "ne") == "ano"),
            "withSentence": sum(1 for row in rows if row.get("Sentence", "").strip()),
            "withSentenceTranslation": sum(1 for row in rows if row.get("SentenceT", "").strip()),
            "imageSources": dict(sorted(image_source_counter.items())),
            "uniqueImageFiles": len(set(asset_map.values())),
        },
        "items": items,
    }
    return payload, asset_map


def write_output(
    output_root: Path,
    payload: dict[str, object],
    asset_map: dict[Path, str],
    json_name: str,
    asset_dir_name: str,
) -> None:
    data_dir = output_root / "data"
    asset_dir = output_root / "assets" / asset_dir_name
    data_dir.mkdir(parents=True, exist_ok=True)
    ensure_clean_assets_dir(asset_dir, set(asset_map.values()))

    for source_path, dest_name in sorted(asset_map.items(), key=lambda item: item[1]):
        shutil.copy2(source_path, asset_dir / dest_name)

    output_json_path = data_dir / json_name
    output_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Synchronize VocabularyEN CSV and images into web-friendly docs assets."
    )
    parser.add_argument(
        "--csv-path",
        default=str(repo_root / "VocabularyEN" / CSV_FILENAME),
        help="Source CSV file.",
    )
    parser.add_argument(
        "--output-root",
        default=str(repo_root / "docs"),
        help="Primary web output root. The script writes data/vocabulary-en.json and assets/vocabulary-en/ here.",
    )
    parser.add_argument(
        "--json-name",
        default="vocabulary-en.json",
        help="Output JSON filename inside data/.",
    )
    parser.add_argument(
        "--asset-dir-name",
        default="vocabulary-en",
        help="Asset subdirectory name inside assets/.",
    )
    parser.add_argument(
        "--extra-output-root",
        action="append",
        default=[],
        help="Optional extra web output root. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise SystemExit(f"CSV file not found: {csv_path}")

    repo_root = Path(__file__).resolve().parents[1]
    output_roots = [Path(args.output_root).expanduser().resolve()]
    output_roots.extend(Path(path).expanduser().resolve() for path in args.extra_output_root)

    rows = load_rows(csv_path)
    base_dirs = build_picture_base_dirs(repo_root, csv_path)
    synonym_image_map = load_external_mapping(base_dirs, csv_path)
    picture_stems = discover_picture_stems(base_dirs)
    try:
        source_csv_label = csv_path.relative_to(repo_root).as_posix()
    except ValueError:
        source_csv_label = csv_path.as_posix()

    payload, asset_map = build_export_payload(
        rows=rows,
        base_dirs=base_dirs,
        synonym_image_map=synonym_image_map,
        picture_stems=picture_stems,
        output_root=output_roots[0],
        asset_dir_name=args.asset_dir_name,
        source_csv_label=source_csv_label,
    )

    for output_root in output_roots:
        local_payload = json.loads(json.dumps(payload))
        for item in local_payload["items"]:
            image_path = item.get("image")
            if image_path:
                item["image"] = f"assets/{args.asset_dir_name}/{Path(image_path).name}"
        write_output(output_root, local_payload, asset_map, args.json_name, args.asset_dir_name)
        print(f"OK  {output_root / 'data' / args.json_name}")
        print(f"OK  {output_root / 'assets' / args.asset_dir_name}")

    stats = payload["stats"]
    print("")
    print(f"Rows: {payload['itemCount']}")
    print(f"Unique copied images: {stats['uniqueImageFiles']}")
    print(f"Image source stats: {stats['imageSources']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
