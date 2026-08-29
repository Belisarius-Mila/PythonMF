#!/usr/bin/env python3
"""Build and verify fixed MP3 assets for MMTX Scene 2."""

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
DOCS_ROOT = REPO_ROOT / "docs" / "scene02_sunnys_lost_nuts"
MIRROR_ROOT = REPO_ROOT / "MatysekANJ" / "web_mmtx" / "scene02_sunnys_lost_nuts"
SCRIPT_PATH = DOCS_ROOT / "script.js"
MANIFEST_NAME = "audio_manifest.js"
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
    character_id: str
    text_en: str
    text_cz: str
    path_en: str
    path_cz: str


@dataclass(frozen=True)
class SpokenItem:
    speaker_id: str
    language: str
    text: str
    voice: Voice
    relative_path: Path

    @property
    def key(self) -> str:
        return f"{self.speaker_id}::{self.text}"


VLASTA = Voice("cs-CZ-VlastaNeural", "Vlasta")
JENNY = Voice("en-US-JennyNeural", "Jenny")

ENGLISH_VOICES = {
    "sunny": Voice("en-US-MichelleNeural", "Michelle"),
    "fiona": Voice("en-US-JennyNeural", "Jenny"),
    "benji": Voice("en-US-AndrewNeural", "Andrew"),
    "bunny": Voice("en-US-AnaNeural", "Ana"),
    "bruno": Voice("en-US-GuyNeural", "Guy"),
}

DIALOGUE = (
    BilingualLine(
        "sunny",
        "Oh no! I don't have my nuts!",
        "Ach ne! Nemám svoje oříšky!",
        "audio/english/scene02_01_sunny_no_nuts_en.mp3",
        "audio/czech/scene02_01_sunny_no_nuts_cz.mp3",
    ),
    BilingualLine(
        "fiona",
        "Benji, do you have nuts?",
        "Benji, máš oříšky?",
        "audio/english/scene02_02_fiona_benji_nuts_en.mp3",
        "audio/czech/scene02_02_fiona_benji_nuts_cz.mp3",
    ),
    BilingualLine(
        "benji",
        "No. I have a map.",
        "Ne. Mám mapu.",
        "audio/english/scene02_03_benji_map_en.mp3",
        "audio/czech/scene02_03_benji_map_cz.mp3",
    ),
    BilingualLine(
        "fiona",
        "Bunny, do you have nuts?",
        "Bunny, máš oříšky?",
        "audio/english/scene02_04_fiona_bunny_nuts_en.mp3",
        "audio/czech/scene02_04_fiona_bunny_nuts_cz.mp3",
    ),
    BilingualLine(
        "bunny",
        "No. I have a carrot.",
        "Ne. Mám mrkev.",
        "audio/english/scene02_05_bunny_carrot_en.mp3",
        "audio/czech/scene02_05_bunny_carrot_cz.mp3",
    ),
    BilingualLine(
        "bruno",
        "Wait a second. I have a bag.",
        "Počkejte chvilku. Mám brašnu.",
        "audio/english/scene02_06_bruno_bag_wait_second_en_fix1.mp3",
        "audio/czech/scene02_06_bruno_bag_wait_second_cz.mp3",
    ),
    BilingualLine(
        "bruno",
        "It is big. Look inside, friends!",
        "Je velká. Podívejte se dovnitř, kamarádi!",
        "audio/english/scene02_07_bruno_look_inside_friends_en_fix3_balanced.mp3",
        "audio/czech/scene02_07_bruno_look_inside_friends_cz.mp3",
    ),
    BilingualLine(
        "sunny",
        "My nuts! I am so happy!",
        "Moje oříšky! Mám takovou radost!",
        "audio/english/scene02_08_sunny_my_nuts_en_fix1_balanced.mp3",
        "audio/czech/scene02_08_sunny_my_nuts_cz.mp3",
    ),
    BilingualLine(
        "fiona",
        "Good. Now we are ready.",
        "Dobře. Teď jsme připraveni.",
        "audio/english/scene02_09_fiona_ready_en.mp3",
        "audio/czech/scene02_09_fiona_ready_cz.mp3",
    ),
)

UI_ENGLISH = (
    ("Tap Benji. Does he have nuts?", "audio/english/scene02_prompt_tap_benji_en.mp3"),
    ("Tap Bunny. Does he have nuts?", "audio/english/scene02_prompt_tap_bunny_en.mp3"),
    ("Tap the bag.", "audio/english/scene02_prompt_tap_bag_en.mp3"),
    ("Not yet. Tap Benji.", "audio/english/scene02_not_yet_tap_benji_en.mp3"),
    ("Not yet. Tap Bunny.", "audio/english/scene02_not_yet_tap_bunny_en.mp3"),
    ("Look at the bag.", "audio/english/scene02_look_at_bag_en.mp3"),
    ("Try again.", "audio/english/scene02_try_again_en.mp3"),
)

UI_CZECH = (
    (
        "Poslouchej anglické věty. Když se objeví žlutá nápověda, klepni na správnou postavu nebo na brašnu.",
        "audio/czech/scene02_main_help_cz.mp3",
    ),
    ("Klepni na Benjiho. Má oříšky?", "audio/czech/scene02_help_tap_benji_cz.mp3"),
    ("Klepni na Bunnyho. Má oříšky?", "audio/czech/scene02_prompt_tap_bunny_cz.mp3"),
    ("Klepni na Bunny. Má oříšky?", "audio/czech/scene02_help_tap_bunny_cz.mp3"),
    ("Klepni na brašnu.", "audio/czech/scene02_help_tap_bag_cz.mp3"),
    (
        "Slovníček. Klepni na slovo a uslyšíš ho anglicky.",
        "audio/czech/scene02_dictionary_help_cz.mp3",
    ),
)

VOCABULARY = (
    ("nuts", "oříšky", "nuts"),
    ("map", "mapa", "map"),
    ("carrot", "mrkev", "carrot"),
    ("bag", "brašna", "bag"),
    ("I have", "mám", "i_have"),
    ("I don't have", "nemám", "i_dont_have"),
    ("Do you have?", "máš?", "do_you_have"),
    ("Does he have?", "má on?", "does_he_have"),
    ("Look inside", "podívej se dovnitř", "look_inside"),
    ("ready", "připravený", "ready"),
    ("wait", "počkat", "wait"),
    ("happy", "šťastný", "happy"),
)


def audio_assets() -> tuple[SpokenItem, ...]:
    assets: list[SpokenItem] = []
    for line in DIALOGUE:
        assets.append(
            SpokenItem(
                line.character_id,
                "en",
                line.text_en,
                ENGLISH_VOICES[line.character_id],
                Path(line.path_en),
            )
        )
        assets.append(
            SpokenItem(line.character_id, "cs", line.text_cz, VLASTA, Path(line.path_cz))
        )
    assets.extend(
        SpokenItem("ui", "en", text, JENNY, Path(path)) for text, path in UI_ENGLISH
    )
    assets.extend(
        SpokenItem("ui", "cs", text, VLASTA, Path(path)) for text, path in UI_CZECH
    )
    for text_en, text_cz, slug in VOCABULARY:
        assets.append(
            SpokenItem(
                "dictionary",
                "en",
                text_en,
                JENNY,
                Path("audio/english") / f"scene02_vocab_{slug}_en.mp3",
            )
        )
        assets.append(
            SpokenItem(
                "dictionary",
                "cs",
                text_cz,
                VLASTA,
                Path("audio/czech") / f"scene02_vocab_{slug}_cz.mp3",
            )
        )
    return tuple(assets)


def build_manifest() -> dict[str, object]:
    dialogue: dict[str, dict[str, str]] = {"en": {}, "cs": {}}
    voices: dict[str, dict[str, str]] = {}
    for asset in audio_assets():
        if asset.key in dialogue[asset.language]:
            raise RuntimeError(f"Duplicitní audio klíč: {asset.language} {asset.key}")
        dialogue[asset.language][asset.key] = asset.relative_path.as_posix()
        voices[asset.voice.voice_id] = {
            "id": asset.voice.voice_id,
            "label": asset.voice.label,
        }
    return {
        "schemaVersion": 1,
        "version": VERSION,
        "rate": RATE,
        "voices": voices,
        "stats": {
            "dialogueLines": len(DIALOGUE),
            "vocabularyItems": len(VOCABULARY),
            "audioReferences": len(audio_assets()),
        },
        "dialogue": dialogue,
    }


def manifest_bytes() -> bytes:
    payload = json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"window.SCENE02_AUDIO_MANIFEST = {payload};\n".encode("utf-8")


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
    if not all(trusted_external_generation_text_allowed(asset.text) for asset in audio_assets()):
        raise RuntimeError("Manifest obsahuje text nepovolený pro externí generování.")
    return synthesize_edge_tts_mp3_sync


def _valid_audio(data: bytes) -> bool:
    return len(data) >= MIN_AUDIO_BYTES and data[:2] in {b"\xff\xf3", b"\xff\xfb", b"ID"}


def _source_is_complete() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    for line in DIALOGUE:
        if f'"{line.text_en}"' not in source or f'"{line.text_cz}"' not in source:
            raise RuntimeError(f"Audio manifest neodpovídá dialogu {line.character_id}.")
    for text_en, text_cz, slug in VOCABULARY:
        if f'en: "{text_en}"' not in source or f'cz: "{text_cz}"' not in source:
            raise RuntimeError(f"Audio manifest neodpovídá slovníčku {slug}.")
    for text, _ in (*UI_ENGLISH, *UI_CZECH):
        if f'"{text}"' not in source:
            raise RuntimeError(f"Audio manifest neodpovídá UI větě: {text}")


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
            if not apply:
                missing += 1
                continue
            assert synthesizer is not None
            data = synthesizer(asset.text, voice=asset.voice.voice_id, rate=RATE)
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
        "total": len(assets),
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
        print(f"Scene 2 audio kontrola OK: {len(audio_assets())} pevných stop.")
        return 0
    result = build(apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))
    if not args.apply and result["missing"]:
        print("Pro vytvoření chybějících stop použij --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
