#!/usr/bin/env python3
"""Build and verify the fixed MP3 library for MMTX Forest School."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMANTHA_ROOT = REPO_ROOT / "Samantha_Agent"
DOCS_ROOT = REPO_ROOT / "docs"
MIRROR_ROOT = REPO_ROOT / "MatysekANJ" / "web_mmtx"
SCRIPT_PATH = DOCS_ROOT / "script_intro_v2.js"
MANIFEST_NAME = "forest_school_audio_manifest.js"
CAPABILITY_ID = "generate_project_audio_asset"
CAPABILITY_TOOL = "app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync"
RATE = "-10%"
VERSION = "20260830fixed1"
MIN_AUDIO_BYTES = 1000


@dataclass(frozen=True)
class Voice:
    voice_id: str
    label: str


@dataclass(frozen=True)
class ForestObject:
    object_id: str
    word: str
    translation: str


@dataclass(frozen=True)
class Lesson:
    title: str
    objects: tuple[ForestObject, ...]


@dataclass(frozen=True)
class SpokenItem:
    speaker_id: str
    language: str
    text: str
    voice: Voice
    relative_path: Path
    preserve_existing: bool = False

    @property
    def key(self) -> str:
        return f"{self.speaker_id}::{self.text}"


JENNY = Voice("en-US-JennyNeural", "Jenny")
VLASTA = Voice("cs-CZ-VlastaNeural", "Vlasta")
PRESERVED_ENGLISH = Voice("preserved-existing-English", "Existing approved English")
PRESERVED_CZECH = Voice("preserved-existing-Czech", "Existing approved Czech")

WELCOME = "Welcome to forest school."
WILL_YOU_TRY = "Will you try?"
TRY_AGAIN = "Try again."
EXCELLENT = "Excellent."
FINISHED = "Great job. Forest school is finished."
BUNNY_YES = "Yes, it is."
BENJI_NO = "No, it isn't."
HELP_CZECH = "Je to správně? Pokud ano, klikňi na jes. Pokud ne, klikňi na nou."
PREVIEW_CZECH = (
    "Nejprve si ukážeme slovíčka z této lekce. Poslechněte si anglické "
    "slovíčko a opakujte si výslovnost."
)
CHOICE_CZECH = (
    "Chceš pokračovat další lekcí? Stiskňi ano. Pokud chceš opakovat, "
    "stiskňi ne."
)

PRESERVED_ENGLISH_WORDS = {
    "bag": Path("scene02_sunnys_lost_nuts/audio/english/scene02_vocab_bag_en.mp3"),
    "carrot": Path("scene02_sunnys_lost_nuts/audio/english/scene02_vocab_carrot_en.mp3"),
    "door": Path("scene03_journey_to_the_lake/audio/english/scene03_ui_door_en.mp3"),
    "map": Path("scene02_sunnys_lost_nuts/audio/english/scene02_vocab_map_en.mp3"),
    "water": Path("scene03_journey_to_the_lake/audio/english/scene03_ui_water_en.mp3"),
}

PRESERVED_CZECH_WORDS = {
    "mrkev": Path("scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_carrot_cz.mp3"),
    "dveře": Path("scene03_journey_to_the_lake/audio/czech/scene03_ui_door_cz.mp3"),
    "mapa": Path("scene02_sunnys_lost_nuts/audio/czech/scene02_vocab_map_cz.mp3"),
    "voda": Path("scene03_journey_to_the_lake/audio/czech/scene03_ui_water_cz.mp3"),
}


def parse_lessons(source: str | None = None) -> tuple[Lesson, ...]:
    source = source if source is not None else SCRIPT_PATH.read_text(encoding="utf-8")
    start = source.index("const forestSchoolLessons = [")
    end = source.index("const forestSchoolWinCount", start)
    block = source[start:end]
    lessons: list[Lesson] = []
    for title, objects_block in re.findall(
        r'title: "([^"]+)",\s*objects: \[(.*?)\]\s*,?\n\s*}',
        block,
        flags=re.DOTALL,
    ):
        objects = tuple(
            ForestObject(object_id, word, translation)
            for object_id, word, translation in re.findall(
                r'\{ id: "([^"]+)", word: "([^"]+)", translation: "([^"]+)" }',
                objects_block,
            )
        )
        lessons.append(Lesson(title, objects))
    if len(lessons) != 12 or any(len(lesson.objects) != 5 for lesson in lessons):
        raise RuntimeError("Forest School musí obsahovat 12 lekcí po pěti slovech.")
    return tuple(lessons)


def _word_path(item: ForestObject, language: str, first_ids: dict[str, str]) -> Path:
    if language == "en" and item.word in PRESERVED_ENGLISH_WORDS:
        return PRESERVED_ENGLISH_WORDS[item.word]
    if language == "cs" and item.translation in PRESERVED_CZECH_WORDS:
        return PRESERVED_CZECH_WORDS[item.translation]
    folder = "english" if language == "en" else "czech"
    suffix = "en" if language == "en" else "cz"
    identity = item.word if language == "en" else item.translation
    first_id = first_ids.setdefault(identity, item.object_id)
    return Path(f"audio/{folder}/forest_school_word_{first_id}_{suffix}.mp3")


def spoken_items() -> tuple[SpokenItem, ...]:
    lessons = parse_lessons()
    items: list[SpokenItem] = [
        SpokenItem("owl", "en", WELCOME, JENNY, Path("audio/english/forest_school_welcome_en.mp3")),
        SpokenItem("owl", "en", WILL_YOU_TRY, JENNY, Path("audio/english/forest_school_will_you_try_en.mp3")),
        SpokenItem(
            "owl",
            "en",
            TRY_AGAIN,
            PRESERVED_ENGLISH,
            Path("scene02_sunnys_lost_nuts/audio/english/scene02_try_again_en.mp3"),
            preserve_existing=True,
        ),
        SpokenItem("owl", "en", EXCELLENT, JENNY, Path("audio/english/forest_school_excellent_en.mp3")),
        SpokenItem("owl", "en", FINISHED, JENNY, Path("audio/english/forest_school_finished_en.mp3")),
        SpokenItem("answer", "en", "yes", JENNY, Path("audio/english/forest_school_answer_yes_en.mp3")),
        SpokenItem("answer", "en", "no", JENNY, Path("audio/english/forest_school_answer_no_en.mp3")),
        SpokenItem(
            "bunny",
            "en",
            BUNNY_YES,
            PRESERVED_ENGLISH,
            Path("audio/english/forest_school_bunny_yes_it_is.mp3"),
            preserve_existing=True,
        ),
        SpokenItem(
            "benji",
            "en",
            BENJI_NO,
            PRESERVED_ENGLISH,
            Path("audio/english/forest_school_benji_no_it_isnt.mp3"),
            preserve_existing=True,
        ),
        SpokenItem(
            "ui",
            "cs",
            HELP_CZECH,
            PRESERVED_CZECH,
            Path("audio/czech/forest_school_help_cz.mp3"),
            preserve_existing=True,
        ),
        SpokenItem("ui", "cs", PREVIEW_CZECH, VLASTA, Path("audio/czech/forest_school_lesson_preview_cz.mp3")),
        SpokenItem("ui", "cs", CHOICE_CZECH, VLASTA, Path("audio/czech/forest_school_lesson_choice_cz.mp3")),
    ]

    first_ids: dict[str, str] = {}
    for index, lesson in enumerate(lessons, start=1):
        items.append(
            SpokenItem(
                "owl",
                "en",
                lesson.title,
                JENNY,
                Path(f"audio/english/forest_school_lesson_{index:02d}_title_en.mp3"),
            )
        )
        for item in lesson.objects:
            english_path = _word_path(item, "en", first_ids)
            items.append(
                SpokenItem(
                    f"word-{item.word}",
                    "en",
                    item.word,
                    PRESERVED_ENGLISH if item.word in PRESERVED_ENGLISH_WORDS else JENNY,
                    english_path,
                    preserve_existing=item.word in PRESERVED_ENGLISH_WORDS,
                )
            )
            items.append(
                SpokenItem(
                    "owl",
                    "en",
                    f"Is this a {item.word}?",
                    JENNY,
                    Path(f"audio/english/forest_school_question_{item.object_id}_en.mp3"),
                )
            )
            czech_path = _word_path(item, "cs", first_ids)
            items.append(
                SpokenItem(
                    f"word-{item.word}",
                    "cs",
                    item.translation,
                    PRESERVED_CZECH if item.translation in PRESERVED_CZECH_WORDS else VLASTA,
                    czech_path,
                    preserve_existing=item.translation in PRESERVED_CZECH_WORDS,
                )
            )
    return tuple(items)


def unique_audio_items() -> tuple[SpokenItem, ...]:
    by_path: dict[Path, SpokenItem] = {}
    for item in spoken_items():
        previous = by_path.get(item.relative_path)
        if previous and (previous.language, previous.text) != (item.language, item.text):
            raise RuntimeError(f"Jedna audio cesta má různé texty: {item.relative_path}")
        by_path.setdefault(item.relative_path, item)
    return tuple(by_path.values())


def build_manifest() -> dict[str, object]:
    dialogue: dict[str, dict[str, str]] = {"en": {}, "cs": {}}
    voices: dict[str, dict[str, str]] = {}
    for item in spoken_items():
        if item.key in dialogue[item.language]:
            raise RuntimeError(f"Duplicitní audio klíč: {item.language} {item.key}")
        dialogue[item.language][item.key] = item.relative_path.as_posix()
        voices[item.voice.voice_id] = {"id": item.voice.voice_id, "label": item.voice.label}
    unique = unique_audio_items()
    return {
        "schemaVersion": 1,
        "version": VERSION,
        "rate": RATE,
        "voices": voices,
        "stats": {
            "lessons": len(parse_lessons()),
            "objects": sum(len(lesson.objects) for lesson in parse_lessons()),
            "audioReferences": len(spoken_items()),
            "audioFiles": len(unique),
            "englishFiles": sum(item.language == "en" for item in unique),
            "czechFiles": sum(item.language == "cs" for item in unique),
            "preservedExistingFiles": sum(item.preserve_existing for item in unique),
        },
        "dialogue": dialogue,
    }


def manifest_bytes() -> bytes:
    payload = json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"window.FOREST_SCHOOL_AUDIO_MANIFEST = {payload};\n".encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def registered_synthesizer() -> Callable[..., bytes]:
    if str(SAMANTHA_ROOT) not in sys.path:
        sys.path.insert(0, str(SAMANTHA_ROOT))
    from app.capabilities import RiskLevel, get_capability
    from app.communication.trusted_external_generation import trusted_external_generation_text_allowed
    from app.speech.edge_tts_mp3 import synthesize_edge_tts_mp3_sync

    capability = get_capability(CAPABILITY_ID)
    if capability.risk != RiskLevel.EXTERNAL_GENERATION or capability.tool != CAPABILITY_TOOL:
        raise RuntimeError("Projektová audio capability neodpovídá schválenému registru.")
    if capability.metadata.get("durable_consent") != "trusted_external_generation_v1":
        raise RuntimeError("Projektová audio capability nemá očekávaný trvalý souhlas.")
    if not all(
        trusted_external_generation_text_allowed(item.text)
        for item in unique_audio_items()
        if not item.preserve_existing
    ):
        raise RuntimeError("Manifest obsahuje text nepovolený pro externí generování.")
    return synthesize_edge_tts_mp3_sync


def _valid_audio(data: bytes) -> bool:
    return len(data) >= MIN_AUDIO_BYTES and data[:2] in {b"\xff\xf3", b"\xff\xfb", b"ID"}


def _source_is_complete() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    for item in spoken_items():
        if item.text not in source and not item.text.startswith("Is this a "):
            raise RuntimeError(f"Audio manifest neodpovídá Forest School textu: {item.text}")
    if 'speakForestSchoolBenjiLine("No, it isn\'t.")' not in source:
        raise RuntimeError("Benjiho ukázka nepoužívá zamýšlenou odpověď No, it isn't.")


def build(*, apply: bool) -> dict[str, int]:
    _source_is_complete()
    synthesizer = registered_synthesizer() if apply else None
    generated = existing = missing = 0
    assets = unique_audio_items()
    for index, item in enumerate(assets, start=1):
        docs_path = DOCS_ROOT / item.relative_path
        mirror_path = MIRROR_ROOT / item.relative_path
        data = docs_path.read_bytes() if docs_path.is_file() else b""
        if not _valid_audio(data):
            if item.preserve_existing:
                raise RuntimeError(f"Chybí zachovávané MP3 {item.relative_path}.")
            if not apply:
                missing += 1
                continue
            assert synthesizer is not None
            data = synthesizer(item.text, voice=item.voice.voice_id, rate=RATE)
            if not _valid_audio(data):
                raise RuntimeError(f"Neplatné MP3 pro {item.relative_path}.")
            _atomic_write(docs_path, data)
            generated += 1
            print(f"[{index}/{len(assets)}] vytvořeno {item.relative_path}", flush=True)
        else:
            existing += 1
        if apply and (not mirror_path.is_file() or mirror_path.read_bytes() != data):
            _atomic_write(mirror_path, data)
    if apply:
        data = manifest_bytes()
        _atomic_write(DOCS_ROOT / MANIFEST_NAME, data)
        _atomic_write(MIRROR_ROOT / MANIFEST_NAME, data)
    return {"generated": generated, "existing": existing, "missing": missing, "references": len(spoken_items()), "files": len(assets)}


def verify() -> None:
    _source_is_complete()
    expected_manifest = manifest_bytes()
    for root in (DOCS_ROOT, MIRROR_ROOT):
        manifest = root / MANIFEST_NAME
        if not manifest.is_file() or manifest.read_bytes() != expected_manifest:
            raise RuntimeError(f"Neaktuální {manifest}.")
        for item in unique_audio_items():
            path = root / item.relative_path
            if not path.is_file() or not _valid_audio(path.read_bytes()):
                raise RuntimeError(f"Chybí platné MP3 {path}.")
    for item in unique_audio_items():
        if (DOCS_ROOT / item.relative_path).read_bytes() != (MIRROR_ROOT / item.relative_path).read_bytes():
            raise RuntimeError(f"Mirror se liší: {item.relative_path}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="vygeneruje chybějící MP3 a oba manifesty")
    parser.add_argument("--check", action="store_true", help="ověří úplnost bez externího volání")
    args = parser.parse_args()
    if args.check:
        verify()
        print(f"Forest School audio kontrola OK: {len(unique_audio_items())} pevných stop.")
        return 0
    result = build(apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))
    if not args.apply and result["missing"]:
        print("Pro vytvoření chybějících stop použij --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
