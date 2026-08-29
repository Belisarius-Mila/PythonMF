#!/usr/bin/env python3
"""Build and verify fixed MP3 assets for the MMTX clearing meeting."""

from __future__ import annotations

import argparse
import json
import os
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
MANIFEST_NAME = "scene01_audio_manifest.js"
CAPABILITY_ID = "generate_project_audio_asset"
CAPABILITY_TOOL = "app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync"
RATE = "-10%"
VERSION = "20260829fixed1"
MIN_AUDIO_BYTES = 1000


@dataclass(frozen=True)
class Voice:
    voice_id: str
    label: str


@dataclass(frozen=True)
class BilingualLine:
    speaker_id: str
    text_en: str
    text_cz: str
    english_paths: tuple[str, ...]


@dataclass(frozen=True)
class SpokenEntry:
    speaker_id: str
    language: str
    text: str
    voice: Voice
    paths: tuple[Path, ...]
    preserve_existing: bool = False
    synthesis_text: str | None = None

    @property
    def key(self) -> str:
        return f"{self.speaker_id}::{self.text}"


@dataclass(frozen=True)
class AudioAsset:
    entry: SpokenEntry
    relative_path: Path


PRESERVED_ENGLISH = Voice("preserved-existing-English", "Existing approved English")
JENNY = Voice("en-US-JennyNeural", "Jenny")
VLASTA = Voice("cs-CZ-VlastaNeural", "Vlasta")

DIALOGUE = (
    BilingualLine(
        "benji",
        "Hello. I am Benji.",
        "Ahoj! Já jsem Benji.",
        (
            "audio/english/benji_bunny_01_benji_hello_en.mp3",
            "audio/english/benji_bunny_03_benji_i_am_benji_en.mp3",
        ),
    ),
    BilingualLine(
        "bunny",
        "Hello. I am Bunny.",
        "Ahoj. Já jsem Bunny.",
        (
            "audio/english/benji_bunny_02_bunny_hello_en.mp3",
            "audio/english/benji_bunny_04_bunny_i_am_bunny_en.mp3",
        ),
    ),
    BilingualLine(
        "benji",
        "We are friends!",
        "Jsme kamarádi!",
        ("audio/english/benji_fable_we_are_friends_01_plain.mp3",),
    ),
    BilingualLine(
        "bruno",
        "Hello. I am Bruno.",
        "Ahoj. Já jsem Bruno.",
        ("audio/english/scene01_03_bruno_hello_i_am_bruno_en.mp3",),
    ),
    BilingualLine(
        "fiona",
        "Hi. I am Fiona.",
        "Ahoj. Já jsem Fiona.",
        ("audio/english/scene01_04_fiona_hi_i_am_fiona_en.mp3",),
    ),
    BilingualLine(
        "sunny",
        "Hello! I am Sunny.",
        "Ahoj! Já jsem Sunny.",
        ("audio/english/scene01_05_sunny_hello_i_am_sunny_en.mp3",),
    ),
    BilingualLine(
        "fiona",
        "We are friends too.",
        "My jsme také kamarádi.",
        ("audio/english/scene01_06_fiona_we_are_friends_too_en.mp3",),
    ),
    BilingualLine(
        "bruno",
        "We are going to the lake.",
        "Jdeme k jezeru.",
        ("audio/english/scene01_07_bruno_we_are_going_to_the_lake_en.mp3",),
    ),
    BilingualLine(
        "benji",
        "We are going to the lake too.",
        "My jdeme k jezeru také.",
        ("audio/english/scene01_08_benji_we_are_going_to_the_lake_too_en.mp3",),
    ),
    BilingualLine(
        "sunny",
        "We can go together.",
        "Můžeme jít společně.",
        ("audio/english/scene01_09_sunny_we_can_go_together_en.mp3",),
    ),
    BilingualLine(
        "fiona",
        "Now we are all friends!",
        "Teď jsme všichni kamarádi!",
        ("audio/english/scene01_10_fiona_now_we_are_all_friends_en.mp3",),
    ),
)

UI_ENGLISH = (
    ("Tap Benji.", "tap_benji"),
    ("Tap Bunny.", "tap_bunny"),
    ("Tap Bruno.", "tap_bruno"),
    ("Tap Fiona.", "tap_fiona"),
    ("Tap Sunny.", "tap_sunny"),
    ("Great. Open the door or run again.", "great_open_the_door_or_run_again"),
)

UI_CZECH = (
    (
        "Poslouchej anglickou nápovědu. Klikni na postavu, na kterou ukazuje šipka. Postava řekne větu anglicky a potom česky. Ikona knihy otevírá slovníček.",
        "intro_help",
    ),
    (
        "Celou scénu můžeš spustit znovu tlačítkem šipky v kruhu. Doporučujeme scénu přehrát několikrát a několikrát si projít slovníček, to je ikona knihy.",
        "help",
    ),
    ("Dveřmi vstoupíš do další scény nebo si přehraj vše znovu.", "complete"),
)

VOCABULARY = (
    ("Hello", "ahoj", "hello"),
    ("I am", "já jsem", "i_am"),
    ("friends", "kamarádi", "friends"),
    ("we are", "my jsme", "we_are"),
    ("too", "také", "too"),
    ("going", "jdeme", "going"),
    ("lake", "jezero", "lake"),
    ("together", "společně", "together"),
)


def czech_synthesis_text(text: str) -> str:
    return (
        text.replace("Benjiho", "Benžiho")
        .replace("Benji", "Benži")
        .replace("Bunnyho", "Bannyho")
        .replace("Bunny", "Banny")
        .replace("Fiono", "Fijono")
        .replace("Fiona", "Fijona")
        .replace("Sunny", "Sany")
    )


def spoken_entries() -> tuple[SpokenEntry, ...]:
    entries: list[SpokenEntry] = []
    for index, line in enumerate(DIALOGUE, start=1):
        entries.append(
            SpokenEntry(
                line.speaker_id,
                "en",
                line.text_en,
                PRESERVED_ENGLISH,
                tuple(Path(path) for path in line.english_paths),
                preserve_existing=True,
            )
        )
        entries.append(
            SpokenEntry(
                line.speaker_id,
                "cs",
                line.text_cz,
                VLASTA,
                (
                    Path(
                        "audio/czech"
                    ) / f"scene01_{index:02d}_{line.speaker_id}_dialogue_cz.mp3",
                ),
                synthesis_text=czech_synthesis_text(line.text_cz),
            )
        )
    for text, slug in UI_ENGLISH:
        entries.append(
            SpokenEntry(
                "ui",
                "en",
                text,
                JENNY,
                (Path(f"audio/english/scene01_ui_{slug}_en.mp3"),),
            )
        )
    for text, slug in UI_CZECH:
        entries.append(
            SpokenEntry(
                "ui",
                "cs",
                text,
                VLASTA,
                (Path(f"audio/czech/scene01_ui_{slug}_cz.mp3"),),
                synthesis_text=czech_synthesis_text(text),
            )
        )
    for text_en, text_cz, slug in VOCABULARY:
        speaker_id = f"dictionary-{text_en}"
        entries.append(
            SpokenEntry(
                speaker_id,
                "en",
                text_en,
                JENNY,
                (Path(f"audio/english/scene01_vocab_{slug}_en.mp3"),),
            )
        )
        entries.append(
            SpokenEntry(
                speaker_id,
                "cs",
                text_cz,
                VLASTA,
                (Path(f"audio/czech/scene01_vocab_{slug}_cz.mp3"),),
                synthesis_text=czech_synthesis_text(text_cz),
            )
        )
    return tuple(entries)


def audio_assets() -> tuple[AudioAsset, ...]:
    return tuple(
        AudioAsset(entry, path)
        for entry in spoken_entries()
        for path in entry.paths
    )


def build_manifest() -> dict[str, object]:
    dialogue: dict[str, dict[str, str | list[str]]] = {"en": {}, "cs": {}}
    voices: dict[str, dict[str, str]] = {}
    for entry in spoken_entries():
        if entry.key in dialogue[entry.language]:
            raise RuntimeError(f"Duplicitní audio klíč: {entry.language} {entry.key}")
        paths = [path.as_posix() for path in entry.paths]
        dialogue[entry.language][entry.key] = paths[0] if len(paths) == 1 else paths
        voices[entry.voice.voice_id] = {
            "id": entry.voice.voice_id,
            "label": entry.voice.label,
        }
    return {
        "schemaVersion": 1,
        "version": VERSION,
        "rate": RATE,
        "voices": voices,
        "stats": {
            "dialogueLines": len(DIALOGUE),
            "uiEnglish": len(UI_ENGLISH),
            "uiCzech": len(UI_CZECH),
            "vocabularyItems": len(VOCABULARY),
            "audioReferences": len(spoken_entries()),
            "audioFiles": len(audio_assets()),
            "preservedEnglishFiles": sum(
                len(entry.paths) for entry in spoken_entries() if entry.preserve_existing
            ),
        },
        "dialogue": dialogue,
    }


def manifest_bytes() -> bytes:
    payload = json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"window.SCENE01_AUDIO_MANIFEST = {payload};\n".encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def registered_synthesizer() -> Callable[..., bytes]:
    if str(SAMANTHA_ROOT) not in sys.path:
        sys.path.insert(0, str(SAMANTHA_ROOT))
    from app.capabilities import RiskLevel, get_capability
    from app.communication.trusted_external_generation import (
        trusted_external_generation_text_allowed,
    )
    from app.speech.edge_tts_mp3 import synthesize_edge_tts_mp3_sync

    capability = get_capability(CAPABILITY_ID)
    if capability.risk != RiskLevel.EXTERNAL_GENERATION or capability.tool != CAPABILITY_TOOL:
        raise RuntimeError("Projektová audio capability neodpovídá schválenému registru.")
    if capability.metadata.get("durable_consent") != "trusted_external_generation_v1":
        raise RuntimeError("Projektová audio capability nemá očekávaný trvalý souhlas.")
    if not all(
        trusted_external_generation_text_allowed(entry.synthesis_text or entry.text)
        for entry in spoken_entries()
        if not entry.preserve_existing
    ):
        raise RuntimeError("Manifest obsahuje text nepovolený pro externí generování.")
    return synthesize_edge_tts_mp3_sync


def _valid_audio(data: bytes) -> bool:
    return len(data) >= MIN_AUDIO_BYTES and data[:2] in {b"\xff\xf3", b"\xff\xfb", b"ID"}


def _source_is_complete() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    for line in DIALOGUE:
        if line.text_en not in source or line.text_cz not in source:
            raise RuntimeError(f"Audio manifest neodpovídá dialogu {line.speaker_id}.")
    for text, _ in (*UI_ENGLISH, *UI_CZECH):
        if text not in source:
            raise RuntimeError(f"Audio manifest neodpovídá UI větě: {text}")
    for text_en, text_cz, slug in VOCABULARY:
        if text_en not in source or text_cz not in source:
            raise RuntimeError(f"Audio manifest neodpovídá slovníčku {slug}.")


def build(*, apply: bool) -> dict[str, int]:
    _source_is_complete()
    synthesizer = registered_synthesizer() if apply else None
    generated = 0
    existing = 0
    missing = 0
    assets = audio_assets()
    for index, asset in enumerate(assets, start=1):
        docs_path = DOCS_ROOT / asset.relative_path
        mirror_path = MIRROR_ROOT / asset.relative_path
        data = docs_path.read_bytes() if docs_path.is_file() else b""
        if not _valid_audio(data):
            if asset.entry.preserve_existing:
                raise RuntimeError(f"Chybí zachovávané anglické MP3 {asset.relative_path}.")
            if not apply:
                missing += 1
                continue
            assert synthesizer is not None
            synthesis_text = asset.entry.synthesis_text or asset.entry.text
            data = synthesizer(
                synthesis_text,
                voice=asset.entry.voice.voice_id,
                rate=RATE,
            )
            if not _valid_audio(data):
                raise RuntimeError(f"Neplatné MP3 pro {asset.relative_path}.")
            _atomic_write(docs_path, data)
            generated += 1
            print(f"[{index}/{len(assets)}] vytvořeno {asset.relative_path}", flush=True)
        else:
            existing += 1
        if apply and (not mirror_path.is_file() or mirror_path.read_bytes() != data):
            _atomic_write(mirror_path, data)

    if apply:
        data = manifest_bytes()
        _atomic_write(DOCS_ROOT / MANIFEST_NAME, data)
        _atomic_write(MIRROR_ROOT / MANIFEST_NAME, data)
    return {
        "generated": generated,
        "existing": existing,
        "missing": missing,
        "references": len(spoken_entries()),
        "files": len(assets),
    }


def verify() -> None:
    _source_is_complete()
    expected_manifest = manifest_bytes()
    for root in (DOCS_ROOT, MIRROR_ROOT):
        manifest = root / MANIFEST_NAME
        if not manifest.is_file() or manifest.read_bytes() != expected_manifest:
            raise RuntimeError(f"Neaktuální {manifest}.")
        for asset in audio_assets():
            path = root / asset.relative_path
            if not path.is_file() or not _valid_audio(path.read_bytes()):
                raise RuntimeError(f"Chybí platné MP3 {path}.")
    for asset in audio_assets():
        docs_path = DOCS_ROOT / asset.relative_path
        mirror_path = MIRROR_ROOT / asset.relative_path
        if docs_path.read_bytes() != mirror_path.read_bytes():
            raise RuntimeError(f"Mirror se liší: {asset.relative_path}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="vygeneruje jen chybějící MP3 a oba manifesty",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="ověří úplnost bez externího volání",
    )
    args = parser.parse_args()
    if args.check:
        verify()
        print(f"Scene 1 audio kontrola OK: {len(audio_assets())} pevných stop.")
        return 0
    result = build(apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))
    if not args.apply and result["missing"]:
        print("Pro vytvoření chybějících stop použij --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
