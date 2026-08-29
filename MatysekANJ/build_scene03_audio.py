#!/usr/bin/env python3
"""Build and verify the fixed MP3 library for MMTX Scene 3."""

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
DOCS_ROOT = REPO_ROOT / "docs" / "scene03_journey_to_the_lake"
MIRROR_ROOT = REPO_ROOT / "MatysekANJ" / "web_mmtx" / "scene03_journey_to_the_lake"
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
    speaker_id: str
    text_en: str
    text_cz: str


@dataclass(frozen=True)
class SpokenItem:
    speaker_id: str
    language: str
    text: str
    voice: Voice
    relative_path: Path
    preserve_existing: bool = False
    synthesis_text: str | None = None

    @property
    def key(self) -> str:
        return f"{self.speaker_id}::{self.text}"


VLASTA = Voice("cs-CZ-VlastaNeural", "Vlasta")
JENNY = Voice("en-US-JennyNeural", "Jenny")

ENGLISH_VOICES = {
    "all": JENNY,
    "benji": Voice("en-US-AndrewNeural", "Andrew"),
    "bruno": Voice("local-macOS-Daniel", "Daniel"),
    "bunny": Voice("en-US-AnaNeural", "Ana"),
    "crow": Voice("en-US-EricNeural", "Eric"),
    "fiona": Voice("en-US-JennyNeural", "Jenny"),
    "horse": Voice("en-US-ChristopherNeural", "Christopher"),
    "sunny": Voice("en-US-MichelleNeural", "Michelle"),
    "ui": JENNY,
}

DIALOGUE = (
    BilingualLine("benji", "Look! Two paths.", "Podívej! Dvě cesty."),
    BilingualLine("bunny", "This way!", "Tudy!"),
    BilingualLine("bruno", "No! This way!", "Ne! Tudy!"),
    BilingualLine("fiona", "Wait, wait...", "Počkejte, počkejte..."),
    BilingualLine("crow", "Caw! Go left!", "Krá krá! Jděte vlevo!"),
    BilingualLine("crow", "Left is good. Right is bad.", "Vlevo je to dobré. Vpravo je to špatné."),
    BilingualLine("sunny", "Why is it bad?", "Proč je to špatné?"),
    BilingualLine("crow", "It is a deep valley.", "Je tam hluboké údolí."),
    BilingualLine("crow", "Maybe... bears!", "Možná... medvědi!"),
    BilingualLine("bunny", "Bears?! No, thank you!", "Medvědi?! Ne, děkuji!"),
    BilingualLine("fiona", "Okay. Left it is.", "Dobře. Tak vlevo."),
    BilingualLine("benji", "Thank you, crow!", "Děkujeme, havrane!"),
    BilingualLine("crow", "Caw! Bye bye!", "Krá krá! Pá pá!"),
    BilingualLine("all", "Let's go left!", "Pojďme vlevo!"),
    BilingualLine("crow", "Caw! No, no. Go left!", "Krá krá! Ne, ne. Jděte vlevo!"),
    BilingualLine("sunny", "A horse! A big horse!", "Kůň! Velký kůň!"),
    BilingualLine("bunny", "I am scared.", "Bojím se."),
    BilingualLine("fiona", "Me too!", "Já taky!"),
    BilingualLine("benji", "I am not scared. I will go.", "Já se nebojím. Já půjdu."),
    BilingualLine("horse", "Hello! Don't be scared.", "Ahoj! Nebojte se."),
    BilingualLine("horse", "I am friendly.", "Jsem přátelský."),
    BilingualLine("benji", "Hello! I am Benji.", "Ahoj! Já jsem Benji."),
    BilingualLine("horse", "Careful! A dog lives there.", "Opatrně! Bydlí tam pes."),
    BilingualLine("horse", "He is not friendly with strangers.", "Není přátelský k cizím."),
    BilingualLine("benji", "Thank you for the warning.", "Děkuji za varování."),
    BilingualLine("horse", "Come! Drink some water.", "Pojďte! Napijte se vody."),
    BilingualLine("fiona", "Look, a pump! But the bucket is empty.", "Podívej, pumpa! Ale vědro je prázdné."),
    BilingualLine("bunny", "How do we get water?", "Jak dostaneme vodu?"),
    BilingualLine("bunny", "I don't know.", "Nevím."),
    BilingualLine("benji", "I don't know.", "Nevím."),
    BilingualLine("bruno", "Let us drink in the forest.", "Napijme se v lese."),
    BilingualLine("sunny", "I have nuts, not water!", "Mám oříšky, ne vodu!"),
    BilingualLine("fiona", "The pump needs help.", "Pumpa potřebuje pomoc."),
    BilingualLine("fiona", "I know! Sunny, jump on the handle!", "Já vím! Sunny, skoč na páku!"),
    BilingualLine("fiona", "Bruno, push it up!", "Bruno, tlač ji nahoru!"),
    BilingualLine("sunny", "Okay, I am jumping!", "Dobře, skáču!"),
    BilingualLine("bruno", "I am pushing!", "Tlačím!"),
    BilingualLine("bunny", "Water! We have water!", "Voda! Máme vodu!"),
    BilingualLine("all", "Thank you, Fiona!", "Děkujeme, Fiono!"),
)

UI_ENGLISH = (
    "Tap the crow.",
    "Tap the left path.",
    "Tap Benji.",
    "Tap the farm door.",
    "Who knows how to get water?",
    "Try the crow.",
    "Try left.",
    "Benji is brave.",
    "Try the door.",
    "Try someone else.",
    "Try Fiona!",
    "Try again.",
)

UI_CZECH = (
    (
        "Poslouchej anglické věty. Když se objeví žlutá nápověda, klepni na havrana, cestu nebo postavu.",
        "main_help",
    ),
    ("Klepni na havrana.", "tap_the_crow"),
    ("Klepni na levou cestu.", "tap_the_left_path"),
    ("Klepni na Benjiho.", "tap_benji"),
    ("Klepni na dveře statku.", "tap_the_farm_door"),
    (
        "Klikni na některého kamaráda, aby řekl, zda ví, jak dostat vodu.",
        "who_knows_how_to_get_water",
    ),
    ("Slovníček. Klepni na slovo a uslyšíš ho anglicky.", "dictionary_help"),
)

VOCABULARY = (
    ("look", "podívej, dívat se"),
    ("left", "vlevo"),
    ("right", "vpravo"),
    ("way", "cesta"),
    ("path", "cesta"),
    ("crow", "havran"),
    ("bad", "špatný"),
    ("deep", "hluboký"),
    ("valley", "údolí"),
    ("maybe", "možná"),
    ("bears", "medvědi"),
    ("but", "ale"),
    ("horse", "kůň"),
    ("scared", "vystrašený"),
    ("me too", "já také"),
    ("friendly", "přátelský"),
    ("careful", "opatrný, opatrně"),
    ("dog", "pes"),
    ("live", "žít, bydlet"),
    ("warning", "varování"),
    ("farm", "farma"),
    ("door", "dveře"),
    ("stranger", "cizinec"),
    ("come", "jít, přijít"),
    ("drink", "pít"),
    ("water", "voda"),
    ("pump", "pumpa"),
    ("get", "dostat"),
    ("bucket", "vědro, kbelík"),
    ("empty", "prázdný"),
    ("I don't know", "nevím"),
    ("forest", "les"),
    ("handle", "páka"),
    ("jump", "skočit"),
    ("push", "tlačit"),
)

LEGACY_PRESERVED = (
    Path("audio/english/scene03_bruno_lets_drink_in_the_forest_en.mp3"),
)


def audio_slug(text: str) -> str:
    normalized = text.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")[:64]


def dialogue_path(speaker_id: str, text_en: str, language: str) -> Path:
    suffix = "en" if language == "en" else "cz"
    folder = "english" if language == "en" else "czech"
    return Path(f"audio/{folder}/scene03_{speaker_id}_{audio_slug(text_en)}_{suffix}.mp3")


def ui_path(text_en: str, language: str) -> Path:
    suffix = "en" if language == "en" else "cz"
    folder = "english" if language == "en" else "czech"
    return Path(f"audio/{folder}/scene03_ui_{audio_slug(text_en)}_{suffix}.mp3")


def czech_synthesis_text(text: str) -> str:
    return (
        text.replace("Benjiho", "Benžiho")
        .replace("Benji", "Benži")
        .replace("Bunnyho", "Bannyho")
        .replace("Bunny", "Banny")
        .replace("Fiono", "Fijono")
        .replace("Fiona", "Fijona")
    )


def audio_assets() -> tuple[SpokenItem, ...]:
    assets: list[SpokenItem] = []
    for line in DIALOGUE:
        assets.append(
            SpokenItem(
                line.speaker_id,
                "en",
                line.text_en,
                ENGLISH_VOICES[line.speaker_id],
                dialogue_path(line.speaker_id, line.text_en, "en"),
                preserve_existing=True,
            )
        )
        assets.append(
            SpokenItem(
                line.speaker_id,
                "cs",
                line.text_cz,
                VLASTA,
                dialogue_path(line.speaker_id, line.text_en, "cs"),
                synthesis_text=czech_synthesis_text(line.text_cz),
            )
        )
    for text in UI_ENGLISH:
        assets.append(
            SpokenItem(
                "ui",
                "en",
                text,
                JENNY,
                ui_path(text, "en"),
                preserve_existing=True,
            )
        )
    for text, slug in UI_CZECH:
        assets.append(
            SpokenItem(
                "ui",
                "cs",
                text,
                VLASTA,
                Path(f"audio/czech/scene03_ui_{slug}_cz.mp3"),
                synthesis_text=czech_synthesis_text(text),
            )
        )
    for text_en, text_cz in VOCABULARY:
        speaker_id = f"dictionary-{text_en}"
        assets.append(
            SpokenItem(
                speaker_id,
                "en",
                text_en,
                JENNY,
                ui_path(text_en, "en"),
                preserve_existing=True,
                synthesis_text="liv" if text_en == "live" else None,
            )
        )
        assets.append(
            SpokenItem(
                speaker_id,
                "cs",
                text_cz,
                VLASTA,
                ui_path(text_en, "cs"),
                synthesis_text=czech_synthesis_text(text_cz),
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
            "uiEnglish": len(UI_ENGLISH),
            "uiCzech": len(UI_CZECH),
            "vocabularyItems": len(VOCABULARY),
            "activeAudioReferences": len(audio_assets()),
            "preservedLegacyAssets": len(LEGACY_PRESERVED),
            "totalAudioFiles": len(audio_assets()) + len(LEGACY_PRESERVED),
        },
        "dialogue": dialogue,
        "preservedLegacy": [path.as_posix() for path in LEGACY_PRESERVED],
    }


def manifest_bytes() -> bytes:
    payload = json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"window.SCENE03_AUDIO_MANIFEST = {payload};\n".encode("utf-8")


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
        trusted_external_generation_text_allowed(asset.synthesis_text or asset.text)
        for asset in audio_assets()
        if not asset.preserve_existing
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
    for text_en, text_cz in VOCABULARY:
        if text_en not in source or text_cz not in source:
            raise RuntimeError(f"Audio manifest neodpovídá slovníčku {text_en}.")
    for text in UI_ENGLISH:
        if text != "Try again." and text not in source:
            raise RuntimeError(f"Audio manifest neodpovídá anglické UI větě: {text}")
    for text, _ in UI_CZECH:
        if text not in source:
            raise RuntimeError(f"Audio manifest neodpovídá české UI větě: {text}")


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
            if asset.preserve_existing:
                raise RuntimeError(f"Chybí zachovávané anglické MP3 {asset.relative_path}.")
            if not apply:
                missing += 1
                continue
            assert synthesizer is not None
            synthesis_text = asset.synthesis_text or asset.text
            data = synthesizer(synthesis_text, voice=asset.voice.voice_id, rate=RATE)
            if not _valid_audio(data):
                raise RuntimeError(f"Neplatné MP3 pro {asset.relative_path}.")
            _atomic_write(docs_path, data)
            generated += 1
            print(f"[{index}/{len(assets)}] vytvořeno {asset.relative_path}", flush=True)
        else:
            existing += 1
        if apply and (not mirror_path.is_file() or mirror_path.read_bytes() != data):
            _atomic_write(mirror_path, data)

    for relative_path in LEGACY_PRESERVED:
        docs_path = DOCS_ROOT / relative_path
        mirror_path = MIRROR_ROOT / relative_path
        data = docs_path.read_bytes() if docs_path.is_file() else b""
        if not _valid_audio(data):
            raise RuntimeError(f"Chybí zachovávané starší MP3 {relative_path}.")
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
        "active": len(assets),
        "preservedLegacy": len(LEGACY_PRESERVED),
        "totalFiles": len(assets) + len(LEGACY_PRESERVED),
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
        for relative_path in LEGACY_PRESERVED:
            path = root / relative_path
            if not path.is_file() or not _valid_audio(path.read_bytes()):
                raise RuntimeError(f"Chybí zachovávané MP3 {path}.")
    for relative_path in {
        *(asset.relative_path for asset in audio_assets()),
        *LEGACY_PRESERVED,
    }:
        docs_path = DOCS_ROOT / relative_path
        mirror_path = MIRROR_ROOT / relative_path
        if docs_path.read_bytes() != mirror_path.read_bytes():
            raise RuntimeError(f"Mirror se liší: {relative_path}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="vygeneruje jen chybějící české MP3 a oba manifesty",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="ověří úplnost bez externího volání",
    )
    args = parser.parse_args()
    if args.check:
        verify()
        print(f"Scene 3 audio kontrola OK: {len(audio_assets()) + len(LEGACY_PRESERVED)} pevných stop.")
        return 0
    result = build(apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))
    if not args.apply and result["missing"]:
        print("Pro vytvoření chybějících českých stop použij --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
