#!/usr/bin/env python3
"""Build sentence MP3s without changing the existing word library.

No arguments performs a local audit. --apply needs a private receipt path;
an interrupted request without a saved asset is never repeated automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from pathlib import Path
from typing import Callable

from build_audio_casting import RATE, _atomic_write, registered_synthesizer
from build_vocabulary_en_audio import DEFAULT_OUTPUT_ROOT, CSV_PATH, VOICES, MIN_AUDIO_BYTES
from build_vocabulary_en_audio import load_and_validate_web_items

MANIFEST_RELATIVE_PATH = Path("data/vocabulary-en-sentence-audio.json")
AUDIO_RELATIVE_ROOT = Path("assets/vocabulary-en-sentences")


def sentence_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 1500:
        raise ValueError("Věta chybí nebo překračuje limit; nebude zkrácena.")
    # Preserve punctuation and wording; only whitespace is normalized by TTS.
    return " ".join(value.split())


def asset_relative_path(language: str, text: str) -> Path:
    voice = VOICES[language]
    digest = hashlib.sha256(f"{voice['id']}\n{RATE}\n{text}".encode()).hexdigest()[:20]
    return AUDIO_RELATIVE_ROOT / str(voice["slug"]) / (digest + ".mp3")


def build_manifest(items: list[dict]) -> dict:
    records = {}
    for item in items:
        uid = item.get("uid")
        if not uid or uid in records:
            raise ValueError("Větné audio vyžaduje jedinečná trvalá UID.")
        en, cz = sentence_text(item.get("sentenceEn")), sentence_text(item.get("sentenceCz"))
        records[uid] = {"uid": uid, "sourceEn": item["en"], "sourceCz": item["cz"],
                        "sourceSentenceEn": item["sentenceEn"], "sourceSentenceCz": item["sentenceCz"],
                        "spokenEn": en, "spokenCz": cz,
                        "en": asset_relative_path("en", en).as_posix(),
                        "cz": asset_relative_path("cz", cz).as_posix()}
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    paths = {r[lang] for r in records.values() for lang in ("en", "cz")}
    return {"schemaVersion": 1, "kind": "sentences", "source": "VocabularyEN/VocabularyEN.csv",
            "sourceDigest": hashlib.sha256(canonical.encode()).hexdigest(),
            "rate": RATE, "voices": VOICES, "items": records,
            "stats": {"itemCount": len(items), "audioReferences": len(items)*2, "uniqueAssets": len(paths)}}


def load_manifest(output_root: Path, csv_path: Path) -> dict:
    import csv
    items = load_and_validate_web_items(output_root, csv_path)
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = {(r["EN"].strip(), r["CZ"].strip()): r for r in csv.DictReader(handle)}
    for item in items:
        row = rows[(item["en"], item["cz"])]
        if (item.get("sentenceEn"), item.get("sentenceCz")) != (row.get("Sentence", "").strip(), row.get("SentenceT", "").strip()):
            raise ValueError("Webové věty neodpovídají CSV; generování nebylo spuštěno.")
    return build_manifest(items)


def jobs(manifest: dict) -> dict:
    return {r[lang]: (r["spokenEn" if lang == "en" else "spokenCz"], str(VOICES[lang]["id"]))
            for r in manifest["items"].values() for lang in ("en", "cz")}


def audit(output_root: Path = DEFAULT_OUTPUT_ROOT, csv_path: Path = CSV_PATH) -> dict:
    expected = load_manifest(output_root, csv_path)
    missing = [p for p in jobs(expected) if not (output_root/p).is_file() or (output_root/p).stat().st_size < MIN_AUDIO_BYTES]
    path = output_root/MANIFEST_RELATIVE_PATH
    manifest_matches = path.is_file() and json.loads(path.read_text()) == expected
    return {**expected["stats"], "missing": len(missing), "manifest_matches": manifest_matches,
            "complete": not missing and manifest_matches}


def build_library(output_root: Path, *, csv_path: Path = CSV_PATH, synthesize: Callable,
                  receipt_path: Path, limit: int | None = None, uids: list[str] | None = None,
                  workers: int = 1) -> dict:
    manifest = load_manifest(output_root, csv_path)
    if limit is not None and limit < 1:
        raise ValueError("Limit musí být kladný.")
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError("Počet souběžných požadavků musí být 1 až 4.")
    selected = set(uids or manifest["items"])
    if selected - manifest["items"].keys():
        raise ValueError("Neznámé UID ukázky.")
    receipt = {"sourceDigest": manifest["sourceDigest"], "jobs": {}}
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("sourceDigest") != manifest["sourceDigest"]:
            raise ValueError("Zdroj se změnil; původní účtenka musí zůstat zachovaná.")
    def save():
        _atomic_write(receipt_path, (json.dumps(receipt, ensure_ascii=False, indent=2)+"\n").encode())
    generated = skipped = 0
    pending = []
    selected_paths = {r[lang] for uid, r in manifest["items"].items() if uid in selected for lang in ("en", "cz")}
    for relative, (text, voice) in jobs(manifest).items():
        if relative not in selected_paths:
            continue
        target = output_root/relative
        previous = receipt["jobs"].get(relative)
        if target.is_file() and target.stat().st_size >= MIN_AUDIO_BYTES:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if previous and previous.get("sha256") and previous["sha256"] != digest:
                raise ValueError("Uložená nahrávka se změnila; nebude přepsána.")
            receipt["jobs"][relative] = {"state": "completed", "sha256": digest}
            save(); skipped += 1
            continue
        if previous:
            raise RuntimeError("Nejistý nebo neúspěšný požadavek zůstává zachovaný; bez automatického opakování.")
        pending.append((relative, text, voice))
    # Validate every uncertain request before sending any new one.
    if limit is not None:
        pending = pending[:limit]
    lock, stopped = Lock(), Event()
    def generate(job):
        nonlocal generated
        relative, text, voice = job
        with lock:
            if stopped.is_set():
                return
            receipt["jobs"][relative] = {"state": "requested"}; save()
        try:
            audio = synthesize(text, voice=voice, rate=RATE)
            if not isinstance(audio, bytes) or len(audio) < MIN_AUDIO_BYTES:
                raise RuntimeError("Syntéza nevrátila platné audio.")
            _atomic_write(output_root/relative, audio)
        except Exception:
            stopped.set()
            with lock:
                receipt["jobs"][relative] = {"state": "uncertain"}; save()
            raise
        with lock:
            receipt["jobs"][relative] = {"state": "completed", "sha256": hashlib.sha256(audio).hexdigest()}; save()
            generated += 1
            if generated % 25 == 0 or len(pending) <= 10:
                print(f"Větné audio: {generated}/{len(pending)} nových, {skipped} zachovaných", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(generate, pending))
    missing = [p for p in jobs(manifest) if not (output_root/p).is_file() or (output_root/p).stat().st_size < MIN_AUDIO_BYTES]
    # Never advertise a partially generated library as complete.
    if not missing:
        _atomic_write(output_root/MANIFEST_RELATIVE_PATH, (json.dumps(manifest, ensure_ascii=False, indent=2)+"\n").encode())
    return {"generated": generated, "skipped": skipped, "missing": len(missing), "complete": not missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--csv-path", type=Path, default=CSV_PATH)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--uids", nargs="+")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.apply:
        if args.receipt is None:
            parser.error("--apply vyžaduje privátní --receipt")
        result = build_library(args.output_root, csv_path=args.csv_path, receipt_path=args.receipt,
                               synthesize=registered_synthesizer(), limit=args.limit, uids=args.uids, workers=args.workers)
    else:
        result = audit(args.output_root, args.csv_path)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
