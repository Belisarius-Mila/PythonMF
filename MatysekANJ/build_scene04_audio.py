#!/usr/bin/env python3
"""Build and verify fixed MP3 assets for the integrated MMTX Harry scene."""

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
DOCS_ROOT = REPO_ROOT / "docs" / "scene04_harry_guard_prototype"
MIRROR_ROOT = REPO_ROOT / "MatysekANJ" / "web_mmtx" / "scene04_harry_guard_prototype"
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
class DialogueLine:
    line_id: str
    character_id: str
    text_en: str
    text_cz: str


@dataclass(frozen=True)
class VocabularyItem:
    slug: str
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
    "harry": Voice("en-GB-RyanNeural", "Ryan"),
    "benji": Voice("en-US-AndrewNeural", "Andrew"),
    "bunny": Voice("en-US-AnaNeural", "Ana"),
    "sunny": Voice("en-US-MichelleNeural", "Michelle"),
    "fiona": Voice("en-US-JennyNeural", "Jenny"),
    "bruno": Voice("en-US-GuyNeural", "Guy"),
    "dictionary": Voice("en-US-JennyNeural", "Jenny"),
}

CZECH_VOICES = {
    "harry": Voice("cs-CZ-AntoninNeural", "Antonín"),
    "benji": Voice("cs-CZ-AntoninNeural", "Antonín"),
    "bunny": Voice("cs-CZ-VlastaNeural", "Vlasta"),
    "sunny": Voice("cs-CZ-VlastaNeural", "Vlasta"),
    "fiona": Voice("cs-CZ-VlastaNeural", "Vlasta"),
    "bruno": Voice("cs-CZ-AntoninNeural", "Antonín"),
    "dictionary": Voice("cs-CZ-VlastaNeural", "Vlasta"),
}

DIALOGUE_LINES = (
    DialogueLine("introduction", "harry", "My name is Harry, and I guard this gate!", "Jmenuji se Harry a hlídám tuto branku!"),
    DialogueLine("stop", "harry", "Stop! Do not come closer!", "Stůjte! Nepřibližujte se!"),
    DialogueLine("friendly", "benji", "Hello. We are friendly.", "Ahoj. Jsme přátelé."),
    DialogueLine("strangers", "harry", "Friendly? I do not know you.", "Přátelé? Já vás neznám."),
    DialogueLine("map_question", "harry", "Who has the map?", "Kdo má mapu?"),
    DialogueLine("not_me", "bunny", "Not me.", "Já ne."),
    DialogueLine("map_answer", "benji", "I have a map.", "Mám mapu."),
    DialogueLine("sheep_question", "harry", "Do you want to chase my sheep?", "Chceš honit moje ovce?"),
    DialogueLine("listen_again", "harry", "Listen again.", "Poslechni si otázku znovu."),
    DialogueLine("no_chase", "benji", "No. I do not chase sheep.", "Ne. Nehoním ovce."),
    DialogueLine("helper", "benji", "I help little animals.", "Pomáhám malým zvířátkům."),
    DialogueLine("trust", "harry", "Hmm. Maybe I can trust you.", "Hmm. Možná ti můžu věřit."),
    DialogueLine("rabbit_intro", "harry", "Wait! What about the rabbit?", "Počkejte! A co ten králík?"),
    DialogueLine("rabbit_prompt", "harry", "Who is the rabbit?", "Kdo je králík?"),
    DialogueLine("bunny_answer", "bunny", "I am Bunny.", "Já jsem Bunny."),
    DialogueLine("carrot_question", "harry", "Do you want to eat the carrots in my garden?", "Chceš sníst mrkev z mé zahrádky?"),
    DialogueLine("own_carrots", "bunny", "No. I have my own carrots.", "Ne. Mám vlastní mrkev."),
    DialogueLine("lake_only", "bunny", "I only want to go to the lake.", "Chci jen jít k jezeru."),
    DialogueLine("bunny_accepted", "harry", "Good answer, Bunny. But the gate stays closed.", "Dobrá odpověď, Bunny. Ale branka zůstává zavřená."),
    DialogueLine("squirrel_intro", "harry", "Now, what about the squirrel?", "A teď, co ta veverka?"),
    DialogueLine("squirrel_prompt", "harry", "Who is the squirrel?", "Kdo je veverka?"),
    DialogueLine("sunny_answer", "sunny", "Hello! I am Sunny.", "Ahoj! Já jsem Sunny."),
    DialogueLine("nut_question", "harry", "Do you want to eat the nuts from my tree?", "Chceš sníst ořechy z mého stromu?"),
    DialogueLine("own_nuts", "sunny", "No. I have my own nuts.", "Ne. Mám vlastní ořechy."),
    DialogueLine("sunny_lake_with_friends", "sunny", "I want to go to the lake with my friends.", "Chci jít s kamarády k jezeru."),
    DialogueLine("sunny_accepted", "harry", "Good answer, Sunny. But I have more questions.", "Dobrá odpověď, Sunny. Ale mám další otázky."),
    DialogueLine("fox_intro", "harry", "And what about the fox?", "A co ta liška?"),
    DialogueLine("fox_prompt", "harry", "Who is the fox?", "Kdo je liška?"),
    DialogueLine("fiona_answer", "fiona", "Hi. I am Fiona.", "Ahoj. Já jsem Fiona."),
    DialogueLine("chicken_question", "harry", "Do you want to catch a chicken in my yard?", "Chceš chytit slepičku na mém dvorku?"),
    DialogueLine("no_chickens", "fiona", "No. I do not catch chickens.", "Ne. Nechytám slepice."),
    DialogueLine("fiona_lake_with_friends", "fiona", "I want to go to the lake with my friends.", "Chci jít s kamarády k jezeru."),
    DialogueLine("fiona_accepted", "harry", "Good answer, Fiona. But I have one more question.", "Dobrá odpověď, Fiono. Ale mám ještě jednu otázku."),
    DialogueLine("badger_intro", "harry", "One more! What about the badger?", "Ještě jeden! A co ten jezevec?"),
    DialogueLine("badger_prompt", "harry", "Who is the badger?", "Kdo je jezevec?"),
    DialogueLine("bruno_answer", "bruno", "Hello. I am Bruno.", "Ahoj. Já jsem Bruno."),
    DialogueLine("fence_question", "harry", "Do you want to dig under my fence?", "Chceš se podhrabat pod mým plotem?"),
    DialogueLine("no_digging", "bruno", "No. I do not dig under fences.", "Ne. Nepodhrabávám se pod ploty."),
    DialogueLine("bruno_lake_with_friends", "bruno", "I want to go to the lake with my friends.", "Chci jít s kamarády k jezeru."),
    DialogueLine("bruno_accepted", "harry", "Good answer, Bruno. I believe you.", "Dobrá odpověď, Bruno. Věřím ti."),
    DialogueLine("gate_opened", "harry", "OK, now you can continue. The gate is open for you, friends!", "Dobře, teď můžete pokračovat. Branka je pro vás otevřená, kamarádi!"),
)

VOCABULARY = (
    VocabularyItem("come_closer", "come closer", "přijít blíž"),
    VocabularyItem("chase", "chase", "honit"),
    VocabularyItem("sheep", "sheep", "ovce"),
    VocabularyItem("little_animals", "little animals", "malá zvířátka"),
    VocabularyItem("trust", "trust", "důvěřovat"),
    VocabularyItem("rabbit", "rabbit", "králík"),
    VocabularyItem("eat", "eat", "jíst"),
    VocabularyItem("own", "own", "vlastní"),
    VocabularyItem("gate", "gate", "branka"),
    VocabularyItem("closed", "closed", "zavřený"),
    VocabularyItem("squirrel", "squirrel", "veverka"),
    VocabularyItem("question", "question", "otázka"),
    VocabularyItem("answer", "answer", "odpověď"),
    VocabularyItem("fox", "fox", "liška"),
    VocabularyItem("catch", "catch", "chytit"),
    VocabularyItem("chicken", "chicken", "slepice"),
    VocabularyItem("yard", "yard", "dvorek"),
    VocabularyItem("badger", "badger", "jezevec"),
    VocabularyItem("dig", "dig", "hrabat"),
    VocabularyItem("under", "under", "pod"),
    VocabularyItem("fence", "fence", "plot"),
    VocabularyItem("believe", "believe", "věřit"),
)

EXISTING_ENGLISH_PATHS = {
    "benji::Hello. We are friendly.": "audio/english/scene04_benji_hello_we_are_friendly_en.mp3",
    "benji::I have a map.": "audio/english/scene04_benji_i_have_a_map_en.mp3",
    "benji::No. I do not chase sheep.": "audio/english/scene04_benji_no_i_do_not_chase_sheep_en.mp3",
    "benji::I help little animals.": "audio/english/scene04_benji_i_help_little_animals_en.mp3",
    "bunny::Not me.": "audio/english/scene04_bunny_not_me_en.mp3",
    "bunny::I am Bunny.": "audio/english/scene04_bunny_i_am_bunny_en.mp3",
    "bunny::No. I have my own carrots.": "audio/english/scene04_bunny_no_i_have_my_own_carrots_en.mp3",
    "bunny::I only want to go to the lake.": "audio/english/scene04_bunny_i_only_want_to_go_to_the_lake_en.mp3",
    "sunny::Hello! I am Sunny.": "audio/english/scene04_sunny_hello_i_am_sunny_en.mp3",
    "sunny::No. I have my own nuts.": "audio/english/scene04_sunny_no_i_have_my_own_nuts_en.mp3",
    "sunny::I want to go to the lake with my friends.": "audio/english/scene04_sunny_i_want_to_go_to_the_lake_with_my_friends_en.mp3",
    "fiona::Hi. I am Fiona.": "audio/english/scene04_fiona_hi_i_am_fiona_en.mp3",
    "fiona::No. I do not catch chickens.": "audio/english/scene04_fiona_no_i_do_not_catch_chickens_en.mp3",
    "fiona::I want to go to the lake with my friends.": "audio/english/scene04_fiona_i_want_to_go_to_the_lake_with_my_friends_en.mp3",
    "bruno::Hello. I am Bruno.": "audio/english/scene04_bruno_hello_i_am_bruno_en.mp3",
    "bruno::No. I do not dig under fences.": "audio/english/scene04_bruno_no_i_do_not_dig_under_fences_en.mp3",
    "bruno::I want to go to the lake with my friends.": "audio/english/scene04_bruno_i_want_to_go_to_the_lake_with_my_friends_en.mp3",
}


def _dialogue_variants() -> tuple[DialogueLine, ...]:
    expanded: list[DialogueLine] = []
    for line in DIALOGUE_LINES:
        if line.line_id != "not_me":
            expanded.append(line)
            continue
        for character_id in ("harry", "benji", "bunny", "sunny", "fiona", "bruno"):
            expanded.append(DialogueLine(f"not_me_{character_id}", character_id, line.text_en, line.text_cz))
    return tuple(expanded)


def _dialogue_path(line: DialogueLine, language: str) -> Path:
    key = f"{line.character_id}::{line.text_en}"
    if language == "en" and key in EXISTING_ENGLISH_PATHS:
        return Path(EXISTING_ENGLISH_PATHS[key])
    suffix = "en" if language == "en" else "cz"
    folder = "english" if language == "en" else "czech"
    slug = "not_me" if line.line_id.startswith("not_me_") else line.line_id
    return Path("audio") / folder / f"scene04_{line.character_id}_{slug}_{suffix}.mp3"


def audio_assets() -> tuple[AudioAsset, ...]:
    assets: list[AudioAsset] = []
    for line in _dialogue_variants():
        key = f"{line.character_id}::{line.text_en}"
        assets.append(AudioAsset(key, "en", line.text_en, ENGLISH_VOICES[line.character_id], _dialogue_path(line, "en")))
        assets.append(AudioAsset(f"{line.character_id}::{line.text_cz}", "cs", line.text_cz, CZECH_VOICES[line.character_id], _dialogue_path(line, "cs")))
    for item in VOCABULARY:
        assets.append(AudioAsset(f"dictionary::{item.text_en}", "en", item.text_en, ENGLISH_VOICES["dictionary"], Path("audio/english") / f"scene04_vocab_{item.slug}_en.mp3"))
        assets.append(AudioAsset(f"dictionary::{item.text_cz}", "cs", item.text_cz, CZECH_VOICES["dictionary"], Path("audio/czech") / f"scene04_vocab_{item.slug}_cz.mp3"))
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
        "stats": {"dialogueCombinations": len(_dialogue_variants()), "vocabularyItems": len(VOCABULARY), "audioReferences": len(audio_assets())},
        "dialogue": dialogue,
    }


def manifest_bytes() -> bytes:
    payload = json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    return f"window.SCENE04_AUDIO_MANIFEST = {payload};\n".encode("utf-8")


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
    lines_block = source.split("const lines = {", 1)[1].split("const state =", 1)[0]
    if lines_block.count(": dialogue(") + lines_block.count(": prompt(") != len(DIALOGUE_LINES):
        raise RuntimeError("Počet dialogů v script.js se liší od audio manifestu.")
    for line in DIALOGUE_LINES:
        if f'"{line.text_en}"' not in lines_block or f'"{line.text_cz}"' not in lines_block:
            raise RuntimeError(f"Audio manifest neodpovídá dialogu {line.line_id}.")
    for item in VOCABULARY:
        if f'en: "{item.text_en}"' not in source or f'cz: "{item.text_cz}"' not in source:
            raise RuntimeError(f"Audio manifest neodpovídá slovníčku {item.slug}.")


def build(*, apply: bool) -> dict[str, int]:
    _source_is_complete()
    synthesizer = registered_synthesizer() if apply else None
    generated = 0
    existing = 0
    missing = 0
    for index, asset in enumerate(audio_assets(), start=1):
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
            print(f"[{index}/{len(audio_assets())}] vytvořeno {asset.relative_path}", flush=True)
        else:
            existing += 1
        if apply and (not mirror_path.is_file() or mirror_path.read_bytes() != data):
            _atomic_write(mirror_path, data)

    if apply:
        data = manifest_bytes()
        _atomic_write(DOCS_ROOT / MANIFEST_NAME, data)
        _atomic_write(MIRROR_ROOT / MANIFEST_NAME, data)
    return {"generated": generated, "existing": existing, "missing": missing, "total": len(audio_assets())}


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
        print(f"Scene 4 audio kontrola OK: {len(audio_assets())} pevných stop.")
        return 0
    result = build(apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))
    if not args.apply and result["missing"]:
        print("Pro vytvoření chybějících stop použij --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
