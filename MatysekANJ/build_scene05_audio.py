#!/usr/bin/env python3
"""Build and verify fixed MP3 assets for the opening of MMTX Scene 5."""

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
DOCS_ROOT = REPO_ROOT / "docs" / "scene05_log_bridge"
MIRROR_ROOT = REPO_ROOT / "MatysekANJ" / "web_mmtx" / "scene05_log_bridge"
SCRIPT_PATH = DOCS_ROOT / "script.js"
MANIFEST_NAME = "audio_manifest.js"
CAPABILITY_ID = "generate_project_audio_asset"
CAPABILITY_TOOL = "app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync"
RATE = "-10%"
VERSION = "20260901crossing1"
MIN_AUDIO_BYTES = 1000

@dataclass(frozen=True)
class Voice:
    voice_id: str
    label: str

@dataclass(frozen=True)
class DialogueLine:
    line_id: str
    character_id: str
    text_en: str
    text_cz: str

@dataclass(frozen=True)
class AudioAsset:
    key: str
    language: str
    text: str
    voice: Voice
    relative_path: Path

ENGLISH_VOICES = {
    "benji": Voice("en-US-AndrewNeural", "Andrew"),
    "bunny": Voice("en-US-AnaNeural", "Ana"),
    "fiona": Voice("en-US-JennyNeural", "Jenny"),
    "logan": Voice("en-US-ChristopherNeural", "Christopher"),
    "sunny": Voice("en-US-MichelleNeural", "Michelle"),
}
CZECH_VOICE = Voice("cs-CZ-VlastaNeural", "Vlasta")

DIALOGUE_LINES = (
    DialogueLine("bridge_gone", "benji", "Oh no! The old bridge is gone.", "Ach ne! Starý most je pryč."),
    DialogueLine("stream_wide", "bunny", "The stream is too wide.", "Potok je příliš široký."),
    DialogueLine("get_across", "fiona", "How can we get across?", "Jak se dostaneme na druhou stranu?"),
    DialogueLine("hello", "logan", "Hello, friends! My name is Logan.", "Ahoj, kamarádi! Jmenuji se Logan."),
    DialogueLine("can_help", "logan", "I can help you.", "Mohu vám pomoci."),
    DialogueLine("strong_logs", "logan", "I have three strong logs.", "Mám tři pevné klády."),
    DialogueLine("tap_logs", "logan", "Help Logan. Tap the three logs.", "Pomoz Loganovi. Klepni na tři klády."),
    DialogueLine("one_log", "logan", "One log.", "Jedna kláda."),
    DialogueLine("two_logs", "logan", "Two logs.", "Dvě klády."),
    DialogueLine("three_logs", "logan", "Three logs!", "Tři klády!"),
    DialogueLine("bridge_ready", "logan", "Great! The bridge is ready.", "Skvěle! Most je hotový."),
    DialogueLine("who_first", "logan", "Who wants to go first?", "Kdo chce jít první?"),
    DialogueLine("go_first", "benji", "I will go first.", "Já půjdu první."),
    DialogueLine("tap_benji", "benji", "Tap Benji and help him cross.", "Klepni na Benjiho a pomoz mu přejít."),
    DialogueLine("bridge_safe", "benji", "I did it! The bridge is safe.", "Zvládl jsem to! Most je bezpečný."),
    DialogueLine("my_turn", "sunny", "My turn! I can jump.", "Teď já! Umím skákat."),
    DialogueLine("tap_sunny", "sunny", "Tap Sunny. Help her jump across.", "Klepni na Sunny. Pomoz jí přeskákat."),
    DialogueLine("three_jumps", "sunny", "One, two, three!", "Raz, dva, tři!"),
    DialogueLine("bunny_scared", "bunny", "Oh no... I am scared.", "Ach ne... Já se bojím."),
)

def _asset_path(line: DialogueLine, language: str) -> Path:
    suffix = "en" if language == "en" else "cz"
    folder = "english" if language == "en" else "czech"
    return Path("audio") / folder / f"scene05_{line.character_id}_{line.line_id}_{suffix}.mp3"

def audio_assets() -> tuple[AudioAsset, ...]:
    assets: list[AudioAsset] = []
    for line in DIALOGUE_LINES:
        assets.append(AudioAsset(f"{line.character_id}::{line.text_en}", "en", line.text_en, ENGLISH_VOICES[line.character_id], _asset_path(line, "en")))
        assets.append(AudioAsset(f"{line.character_id}::{line.text_cz}", "cs", line.text_cz, CZECH_VOICE, _asset_path(line, "cs")))
    return tuple(assets)

def build_manifest() -> dict[str, object]:
    dialogue = {"en": {}, "cs": {}}
    voices: dict[str, dict[str, str]] = {}
    for asset in audio_assets():
        dialogue[asset.language][asset.key] = asset.relative_path.as_posix()
        voices[asset.voice.voice_id] = {"id": asset.voice.voice_id, "label": asset.voice.label}
    return {
        "schemaVersion": 1,
        "version": VERSION,
        "rate": RATE,
        "voices": voices,
        "stats": {"dialogueLines": len(DIALOGUE_LINES), "audioReferences": len(audio_assets())},
        "dialogue": dialogue,
    }

def manifest_bytes() -> bytes:
    payload = json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"window.SCENE05_AUDIO_MANIFEST = {payload};\n".encode("utf-8")

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
    if not all(trusted_external_generation_text_allowed(asset.text) for asset in audio_assets()):
        raise RuntimeError("Manifest obsahuje text nepovolený pro externí generování.")
    return synthesize_edge_tts_mp3_sync

def _valid_audio(data: bytes) -> bool:
    return len(data) >= MIN_AUDIO_BYTES and data[:2] in {b"\xff\xf3", b"\xff\xfb", b"ID"}

def _source_is_complete() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    lines_block = source.split("const lines = {", 1)[1].split("const introLines =", 1)[0]
    if lines_block.count(": dialogue(") + lines_block.count(": prompt(") != len(DIALOGUE_LINES):
        raise RuntimeError("Počet dialogů v script.js se liší od audio manifestu.")
    for line in DIALOGUE_LINES:
        if f'"{line.text_en}"' not in lines_block or f'"{line.text_cz}"' not in lines_block:
            raise RuntimeError(f"Audio manifest neodpovídá dialogu {line.line_id}.")

def build(*, apply: bool) -> dict[str, int]:
    _source_is_complete()
    synthesizer = registered_synthesizer() if apply else None
    generated = existing = missing = 0
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
    return {"generated": generated, "existing": existing, "missing": missing, "total": len(assets)}

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
        if (DOCS_ROOT / asset.relative_path).read_bytes() != (MIRROR_ROOT / asset.relative_path).read_bytes():
            raise RuntimeError(f"Mirror se liší: {asset.relative_path}.")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="vygeneruje jen chybějící MP3 a oba manifesty")
    parser.add_argument("--check", action="store_true", help="ověří úplnost bez externího volání")
    args = parser.parse_args()
    if args.check:
        verify()
        print(f"Scene 5 audio kontrola OK: {len(audio_assets())} pevných stop.")
        return 0
    result = build(apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))
    if not args.apply and result["missing"]:
        print("Pro vytvoření chybějících stop použij --apply.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
