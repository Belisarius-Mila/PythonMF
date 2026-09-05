#!/usr/bin/env python3
"""Build and verify production MP3 pronunciation assets for VocabularyEN."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from build_audio_casting import RATE, _atomic_write, registered_synthesizer


REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = Path(__file__).with_name("VocabularyEN.csv")
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "docs"
DATA_RELATIVE_PATH = Path("data/vocabulary-en.json")
MANIFEST_RELATIVE_PATH = Path("data/vocabulary-en-audio.json")
AUDIO_RELATIVE_ROOT = Path("assets/vocabulary-en-audio")
MIN_AUDIO_BYTES = 1000

VOICES = {
    "en": {
        "id": "en-US-AriaNeural",
        "slug": "en-us-aria-neural",
        "label": "Aria",
    },
    "cz": {
        "id": "cs-CZ-VlastaNeural",
        "slug": "cs-cz-vlasta-neural",
        "label": "Vlasta",
    },
}

# Aria pronounces the isolated word "cat" as "Kate". Keep the displayed and
# spoken text intact; use the verified voice for this pronunciation only.
VOICE_OVERRIDES = {("en", "cat"): "en-US-JennyNeural"}


def asset_voice(language: str, spoken_text: str) -> str:
    return VOICE_OVERRIDES.get((language, spoken_text), str(VOICES[language]["id"]))


def normalize_spoken_text(text: str) -> str:
    """Turn compact vocabulary notation into clear TTS text."""

    value = " ".join(str(text or "").split())
    value = value.replace("(", "").replace(")", "")
    value = re.sub(r"\s*[,;/]\s*", ". ", value)
    value = re.sub(r"\s+([?.!])", r"\1", value)
    value = re.sub(r"\.{2,}", ".", value)
    return value.strip()


def load_csv_rows(csv_path: Path = CSV_PATH) -> list[dict[str, object]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))

    rows: list[dict[str, object]] = []
    for row in source_rows:
        en = (row.get("EN") or "").strip()
        cz = (row.get("CZ") or "").strip()
        if not en and not cz:
            continue
        rows.append({"id": int(row["Order"]), "en": en, "cz": cz})
    return rows


def load_and_validate_web_items(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    csv_path: Path = CSV_PATH,
) -> list[dict[str, object]]:
    data_path = output_root / DATA_RELATIVE_PATH
    if not data_path.is_file():
        raise ValueError(f"Chybí {data_path}. Nejprve spusť synchronizaci VocabularyEN.")
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("Webový vocabulary-en.json nemá platné pole items.")

    csv_rows = load_csv_rows(csv_path)
    expected = [(row["id"], row["en"], row["cz"]) for row in csv_rows]
    actual = [(item.get("id"), item.get("en"), item.get("cz")) for item in items]
    if actual != expected:
        raise ValueError(
            "Webová data neodpovídají VocabularyEN.csv. "
            "Nejprve spusť: python3 VocabularyEN/sync_vocabulary_en_to_docs.py"
        )
    return items


def asset_relative_path(language: str, spoken_text: str) -> Path:
    voice_id = asset_voice(language, spoken_text)
    identity = f"{voice_id}\n{RATE}\n{spoken_text}".encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:20]
    voice_slug = re.sub(r"([a-z])([A-Z])", r"\1-\2", voice_id).lower()
    return AUDIO_RELATIVE_ROOT / voice_slug / f"{digest}.mp3"


def _source_digest(items: list[dict[str, object]]) -> str:
    canonical = json.dumps(
        [[item["id"], item["en"], item["cz"]] for item in items],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def build_manifest(items: list[dict[str, object]]) -> dict[str, object]:
    records: dict[str, dict[str, object]] = {}
    for item in items:
        spoken_en = normalize_spoken_text(str(item["en"]))
        spoken_cz = normalize_spoken_text(str(item["cz"]))
        records[str(item["id"])] = {
            "sourceEn": item["en"],
            "sourceCz": item["cz"],
            "spokenEn": spoken_en,
            "spokenCz": spoken_cz,
            "en": asset_relative_path("en", spoken_en).as_posix(),
            "cz": asset_relative_path("cz", spoken_cz).as_posix(),
        }
        for language, spoken in (("en", spoken_en), ("cz", spoken_cz)):
            if (language, spoken) in VOICE_OVERRIDES:
                records[str(item["id"])][f"{language}Voice"] = asset_voice(language, spoken)

    all_paths = {
        record[language]
        for record in records.values()
        for language in ("en", "cz")
    }
    return {
        "schemaVersion": 1,
        "source": "VocabularyEN/VocabularyEN.csv",
        "sourceDigest": _source_digest(items),
        "rate": RATE,
        "voices": VOICES,
        "stats": {
            "itemCount": len(items),
            "audioReferences": len(items) * 2,
            "uniqueAssets": len(all_paths),
        },
        "items": records,
    }


def _asset_jobs(manifest: dict[str, object]) -> dict[str, tuple[str, str]]:
    jobs: dict[str, tuple[str, str]] = {}
    records = manifest["items"]
    assert isinstance(records, dict)
    for record in records.values():
        assert isinstance(record, dict)
        jobs[str(record["en"])] = (str(record["spokenEn"]), "en")
        jobs[str(record["cz"])] = (str(record["spokenCz"]), "cz")
    return jobs


def verify_library(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    csv_path: Path = CSV_PATH,
) -> dict[str, int]:
    items = load_and_validate_web_items(output_root, csv_path)
    expected = build_manifest(items)
    manifest_path = output_root / MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise ValueError("Chybí vocabulary-en-audio.json. Spusť generátor s --apply.")
    actual = json.loads(manifest_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError("Audio manifest neodpovídá současnému CSV. Spusť generátor s --apply.")

    jobs = _asset_jobs(expected)
    missing = []
    invalid = []
    for relative in jobs:
        path = output_root / relative
        if not path.is_file():
            missing.append(relative)
        elif path.stat().st_size < MIN_AUDIO_BYTES:
            invalid.append(relative)
    if missing or invalid:
        raise ValueError(
            f"Audio knihovna není úplná: chybí {len(missing)}, neplatné {len(invalid)}. "
            "Spusť generátor s --apply."
        )
    return {
        "items": len(items),
        "references": len(items) * 2,
        "assets": len(jobs),
    }


def build_library(
    output_root: Path,
    *,
    synthesize: Callable[..., bytes],
    force: bool = False,
    csv_path: Path = CSV_PATH,
) -> dict[str, int]:
    items = load_and_validate_web_items(output_root, csv_path)
    manifest = build_manifest(items)
    jobs = _asset_jobs(manifest)
    generated = 0
    skipped = 0

    for relative, (text, language) in sorted(jobs.items()):
        target = output_root / relative
        if target.is_file() and target.stat().st_size >= MIN_AUDIO_BYTES and not force:
            skipped += 1
            continue
        audio = synthesize(text, voice=asset_voice(language, text), rate=RATE)
        if not isinstance(audio, bytes) or len(audio) < MIN_AUDIO_BYTES:
            size = len(audio) if isinstance(audio, bytes) else "není bytes"
            raise RuntimeError(f"Neplatné audio pro {relative}: {size} bajtů.")
        _atomic_write(target, audio)
        generated += 1

    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    _atomic_write(output_root / MANIFEST_RELATIVE_PATH, manifest_bytes)
    verified = verify_library(output_root, csv_path)
    return {
        "generated": generated,
        "skipped": skipped,
        "assets": verified["assets"],
        "items": verified["items"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="vygeneruje chybějící MP3 a manifest")
    parser.add_argument("--force", action="store_true", help="znovu vytvoří i existující MP3")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--csv-path", type=Path, default=CSV_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = args.output_root.expanduser().resolve()
    csv_path = args.csv_path.expanduser().resolve()
    if args.apply:
        result = build_library(
            output_root,
            synthesize=registered_synthesizer(),
            force=args.force,
            csv_path=csv_path,
        )
        print(
            f"Audio hotovo: {result['generated']} vygenerováno, "
            f"{result['skipped']} ponecháno, {result['assets']} unikátních MP3 "
            f"pro {result['items']} slovíček."
        )
        return 0

    result = verify_library(output_root, csv_path)
    print(
        f"Audio kontrola OK: {result['assets']} unikátních MP3, "
        f"{result['references']} odkazů pro {result['items']} slovíček."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
