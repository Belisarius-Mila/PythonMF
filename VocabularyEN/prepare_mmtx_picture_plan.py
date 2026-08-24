#!/usr/bin/env python3
"""Prepare a fail-closed image reuse/generation plan for imported MMTX words."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "VocabularyEN" / "VocabularyEN.csv"
PICT_DIR = REPO_ROOT / "Pict"
FOREST_ASSET_DIR = REPO_ROOT / "MatysekANJ" / "web_mmtx" / "assets"
MAPPING_PATH = PICT_DIR / "mapping.json"
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def load_import_module():
    path = REPO_ROOT / "VocabularyEN" / "import_mmtx_vocabulary.py"
    spec = importlib.util.spec_from_file_location("import_mmtx_vocabulary", path)
    if not spec or not spec.loader:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REUSE = {
    "apples": "apple",
    "bears": "bear",
    "friends": "friend",
    "pigs": "pig",
    "wecan": "can",
    "weare": "people",
    "ok": "good",
    "going": "go",
    "doyouhave": "have",
    "doeshehave": "have",
    "ihave": "ihave",
    "look": "see",
    "way": "travel",
    "path": "travel",
    "metoo": "also",
    "too": "also",
    "friendly": "friend",
    "stranger": "foreigner",
    "littleanimals": "animal",
    "eat": "meal",
    "yard": "courtyard",
    "eight": "otto",
}

GENERATE_GROUP = {
    "one": "one",
    "two": "two",
    "three": "three",
    "four": "four",
    "six": "six",
    "seven": "seven",
    "sunflowers": "sunflowers",
    "count": "count",
    "nuts": "nuts",
    "idonthave": "idonthave",
    "lookinside": "lookinside",
    "crow": "crow",
    "bad": "bad",
    "deep": "valley",
    "valley": "valley",
    "scared": "scared",
    "careful": "warning",
    "warning": "warning",
    "farm": "farm",
    "come": "comecloser",
    "pump": "pump",
    "get": "get",
    "bucket": "bucket",
    "empty": "empty",
    "forest": "forest",
    "handle": "handle",
    "push": "push",
    "comecloser": "comecloser",
    "chase": "chase",
    "trust": "trust",
    "own": "own",
    "gate": "gate",
    "squirrel": "squirrel",
    "question": "question",
    "catch": "catch",
    "badger": "badger",
    "dig": "dig",
    "fence": "fence",
    "believe": "trust",
}

SCENES = {
    "one": "exactly one bright red apple on a small plate; no other countable objects",
    "two": "exactly two blue toy balls side by side; no other countable objects",
    "three": "exactly three friendly rabbits sitting in a row; no other animals",
    "four": "exactly four colorful kites flying in the sky; no other kites",
    "six": "exactly six oranges arranged clearly in one basket; no other fruit",
    "seven": "exactly seven sheep standing clearly separated in a green field; no other sheep",
    "sunflowers": "a small group of tall yellow sunflowers turning toward the warm sun",
    "count": "a child pointing carefully at five apples in a row and counting them; no written numerals",
    "bad": "a muddy damaged path after heavy rain, clearly unsafe and unpleasant, with a child stopping before it",
    "badger": "a friendly European badger standing outside its woodland burrow at dusk",
    "bucket": "a simple metal bucket filled with clean water beside a garden pump",
    "catch": "a child successfully catching a bright red ball with both hands",
    "chase": "a playful dog chasing a rolling red ball across grass",
    "comecloser": "one child warmly beckoning a friend to come closer with an open hand gesture",
    "crow": "a black crow perched clearly on a wooden fence in daylight",
    "dig": "a badger actively digging soft earth beside a wooden fence",
    "empty": "one clearly empty drinking glass on a simple table, viewed close enough to see that it contains nothing",
    "farm": "a cheerful small farm with a red barn, field, cow and chickens",
    "fence": "a clear wooden fence running across a green meadow",
    "forest": "a welcoming green forest path with tall trees and soft daylight",
    "get": "a child receiving a wrapped present from a smiling adult, with the handover clearly visible",
    "handle": "a close view of a hand pressing down the long handle of an old water pump",
    "idonthave": "a child opening an empty backpack and shrugging with empty hands",
    "lookinside": "a curious child leaning over and looking inside an open cardboard box",
    "nuts": "a small wooden bowl filled with clearly visible hazelnuts and walnuts",
    "own": "two children each holding their own different backpack close to themselves, clear personal possession",
    "pump": "an old hand water pump pouring fresh water into a bucket",
    "push": "a child pushing a heavy wooden door open with both hands",
    "question": "a student raising one hand with a curious questioning expression in a classroom",
    "scared": "a horse looking startled by a sudden harmless noise, with a caring child nearby",
    "squirrel": "a red squirrel holding a nut on a tree branch",
    "trust": "one child safely helping another child cross a shallow stream by holding hands",
    "valley": "a clearly deep green valley between high hills with a river at the bottom",
    "warning": "a careful child stopping safely before a pedestrian crossing while a red traffic light is visible",
    "gate": "a closed wooden farm gate between two fence posts, clearly distinct from the fence",
}

MAPPING_OVERRIDES = {
    "čepice": "hat",
}

STYLE_PROMPT = (
    "Warm square vocabulary-card illustration for a child learner, but not babyish. "
    "Use a clear everyday scene with a simple uncluttered background, natural details, "
    "soft shadows and the main concept instantly readable. No text, letters, labels, "
    "watermark, signature or decorative border."
)


def picture_files_by_normalized_stem(normalize_word) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in sorted(PICT_DIR.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.setdefault(normalize_word(path.stem), path)
    return files


def forest_keys(import_module) -> set[str]:
    entries = import_module.extract_source_entries()
    forest_label = "MMTX intro, Owl Garden and Forest School"
    result = set()
    for key, entry in entries.items():
        source_path = FOREST_ASSET_DIR / f"forest_school_{key}.png"
        if forest_label in entry["sources"] and source_path.exists():
            result.add(key)
    return result


def build_plan() -> dict[str, object]:
    import_module = load_import_module()
    normalize_word = import_module.normalize_word
    files = picture_files_by_normalized_stem(normalize_word)
    forest = forest_keys(import_module)
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if int(row["Order"]) >= 187]
    if len(rows) != 120:
        raise SystemExit(f"Expected 120 imported MMTX rows, found {len(rows)}")

    assignments = []
    generation_words: dict[str, list[dict[str, str]]] = defaultdict(list)
    unresolved = []
    for row in rows:
        key = normalize_word(row["EN"])
        if key in files:
            action = "reuse_pict_exact"
            image_stem = normalize_word(files[key].stem)
            source = files[key].relative_to(REPO_ROOT).as_posix()
        elif key in forest:
            action = "reuse_mmtx_forest_asset"
            image_stem = key
            source = (FOREST_ASSET_DIR / f"forest_school_{key}.png").relative_to(REPO_ROOT).as_posix()
        elif key in REUSE and REUSE[key] in files:
            action = "reuse_pict_mapped"
            image_stem = REUSE[key]
            source = files[image_stem].relative_to(REPO_ROOT).as_posix()
        elif key in GENERATE_GROUP:
            action = "generate"
            image_stem = GENERATE_GROUP[key]
            source = ""
            generation_words[image_stem].append({"en": row["EN"], "cz": row["CZ"]})
        else:
            unresolved.append(row["EN"])
            continue
        assignments.append(
            {
                "order": int(row["Order"]),
                "en": row["EN"],
                "cz": row["CZ"],
                "normalized_en": key,
                "action": action,
                "image_stem": image_stem,
                "source": source,
            }
        )
    if unresolved:
        raise SystemExit("Unresolved image assignments: " + ", ".join(unresolved))

    requests = []
    for image_stem, words in sorted(generation_words.items()):
        if image_stem not in SCENES:
            raise SystemExit(f"Missing generation scene for {image_stem}")
        requests.append(
            {
                "image_name": image_stem,
                "words": [item["en"] for item in words],
                "czech_meanings": [item["cz"] for item in words],
                "prompt": (
                    "Use case: illustration-story\n"
                    "Asset type: square English vocabulary card\n"
                    f"Primary request: {SCENES[image_stem]}.\n"
                    "Style/medium: polished warm educational illustration, realistic enough to be unambiguous\n"
                    "Composition/framing: centered main idea, square composition, generous padding\n"
                    f"Constraints: {STYLE_PROMPT}"
                ),
            }
        )

    existing_mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    proposed: dict[str, str] = {}
    conflicts = []
    for item in assignments:
        key = str(item["cz"])
        target = MAPPING_OVERRIDES.get(key, str(item["image_stem"]))
        current = existing_mapping.get(key)
        if current is not None:
            if current != target:
                conflicts.append({"cz": key, "current": current, "proposed": target, "decision": "preserve_current"})
            continue
        previous = proposed.get(key)
        if previous is not None and previous != target:
            raise SystemExit(f"Conflicting new mapping for {key}: {previous} vs {target}")
        proposed[key] = target

    return {
        "schema_version": 1,
        "created_at": "2026-08-24",
        "language": "en_mmtx",
        "source_csv": "VocabularyEN/VocabularyEN.csv",
        "imported_row_count": len(rows),
        "assignment_counts": {
            action: sum(item["action"] == action for item in assignments)
            for action in ("reuse_pict_exact", "reuse_mmtx_forest_asset", "reuse_pict_mapped", "generate")
        },
        "total_unique_target_images": len(requests),
        "batch_size": 5,
        "assignments": assignments,
        "requests": requests,
        "mapping_preview": dict(sorted(proposed.items(), key=lambda item: item[0].casefold())),
        "preserved_mapping_conflicts": conflicts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_plan()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported rows: {payload['imported_row_count']}")
    print(f"Assignments: {payload['assignment_counts']}")
    print(f"Images to generate: {payload['total_unique_target_images']}")
    print(f"Mapping additions preview: {len(payload['mapping_preview'])}")
    print(f"Preserved existing mapping conflicts: {len(payload['preserved_mapping_conflicts'])}")
    print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
