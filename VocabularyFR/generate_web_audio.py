#!/usr/bin/env python3
"""Generate local browser-playable audio for VocabularyFR web.

This is a build/maintenance helper for Mila's Mac. Jana does not need Python
when the generated web/audio directory is deployed with the web app.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "VocabularyFR.csv"
WEB_AUDIO_DIR = ROOT / "web" / "audio"
VOICE = "Thomas"


def audio_slug(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.strip().lower())
    ascii_text = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    out: list[str] = []
    previous_dash = False
    for ch in ascii_text:
        if ch.isascii() and ch.isalnum():
            out.append(ch)
            previous_dash = False
        elif not previous_dash:
            out.append("-")
            previous_dash = True
    slug = "".join(out).strip("-")[:90]
    return slug or "audio"


def load_texts() -> tuple[set[str], set[str]]:
    words: set[str] = set()
    sentences: set[str] = set()
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            fr = (row.get("FR") or "").strip()
            sentence = (row.get("Sentence") or "").strip()
            if fr:
                words.add(fr)
            if sentence:
                sentences.add(sentence)
    return words, sentences


def generate_one(text: str, target: Path) -> bool:
    if target.exists() and target.stat().st_size > 0:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        aiff = Path(tmp) / "speech.aiff"
        subprocess.run(["say", "-v", VOICE, "-o", str(aiff), text], check=True)
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", str(aiff), str(target)], check=True)
    return True


def generate_many(kind: str, texts: set[str]) -> int:
    created = 0
    used_slugs: dict[str, str] = {}
    for text in sorted(texts, key=lambda value: value.casefold()):
        slug = audio_slug(text)
        if slug in used_slugs and used_slugs[slug] != text:
            # Rare collision fallback; browser lookup intentionally uses the base slug,
            # so skip colliding variants rather than silently mismatching audio.
            continue
        used_slugs[slug] = text
        if generate_one(text, WEB_AUDIO_DIR / kind / f"{slug}.m4a"):
            created += 1
    return created


def main() -> int:
    words, sentences = load_texts()
    created_words = generate_many("fr_words", words)
    created_sentences = generate_many("fr_sentences", sentences)
    print(f"words={len(words)} created={created_words}")
    print(f"sentences={len(sentences)} created={created_sentences}")
    print(f"audio_dir={WEB_AUDIO_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
