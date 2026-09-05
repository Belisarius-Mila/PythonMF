#!/usr/bin/env python3
"""Build a local, non-published voice casting for VocabularyEN."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMANTHA_ROOT = REPO_ROOT / "Samantha_Agent"
CSV_PATH = Path(__file__).with_name("VocabularyEN.csv")
DEFAULT_OUTPUT_DIR = Path(__file__).with_name("audio_casting")
RATE = "-10%"
CAPABILITY_ID = "generate_project_audio_asset"
CAPABILITY_TOOL = "app.speech.edge_tts_mp3.synthesize_edge_tts_mp3_sync"


@dataclass(frozen=True)
class Voice:
    voice_id: str
    slug: str
    language: str
    label: str
    description: str


@dataclass(frozen=True)
class CastingItem:
    item_id: str
    order: int
    display_en: str
    display_cz: str
    speak_en: str
    speak_cz: str


VOICES = (
    Voice(
        "en-US-AnaNeural",
        "en-us-ana-neural",
        "en",
        "Ana",
        "mladší americký ženský hlas",
    ),
    Voice(
        "en-US-AriaNeural",
        "en-us-aria-neural",
        "en",
        "Aria",
        "dospělý americký ženský hlas",
    ),
    Voice(
        "cs-CZ-VlastaNeural",
        "cs-cz-vlasta-neural",
        "cz",
        "Vlasta",
        "český ženský hlas",
    ),
    Voice(
        "cs-CZ-AntoninNeural",
        "cs-cz-antonin-neural",
        "cz",
        "Antonín",
        "český mužský hlas",
    ),
)


CASTING_SOURCE = (
    ("glass-water", 1, "a glass (of water)", "sklenice (vody)", "a glass of water", "sklenice vody"),
    ("drink", 30, "drink", "nápoj, pít", "drink", "nápoj. Pít."),
    ("free", 44, "free", "volný; zdarma", "free", "volný. Zdarma."),
    ("live", 69, "live", "žít; bydlet", "live", "žít. Bydlet."),
    ("welcome", 141, "you're welcome", "není zač", "you're welcome", "není zač"),
    ("right", 144, "right", "pravý, správný, doprava", "right", "pravý. Správný. Doprava."),
    ("three", 189, "three", "tři", "three", "tři"),
    ("do-you-have", 259, "Do you have?", "máš?", "Do you have?", "Máš?"),
    ("dont-know", 284, "I don't know", "nevím", "I don't know", "Nevím"),
    ("squirrel", 296, "squirrel", "veverka", "squirrel", "veverka"),
)


def load_casting_items(csv_path: Path = CSV_PATH) -> tuple[CastingItem, ...]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = {int(row["Order"]): row for row in csv.DictReader(handle)}

    items: list[CastingItem] = []
    for item_id, order, display_en, display_cz, speak_en, speak_cz in CASTING_SOURCE:
        row = rows.get(order)
        if row is None:
            raise ValueError(f"Ve VocabularyEN.csv chybí řádek Order={order}.")
        actual = ((row.get("EN") or "").strip(), (row.get("CZ") or "").strip())
        expected = (display_en, display_cz)
        if actual != expected:
            raise ValueError(
                f"Řádek Order={order} se změnil: očekáváno {expected!r}, nalezeno {actual!r}."
            )
        items.append(
            CastingItem(item_id, order, display_en, display_cz, speak_en, speak_cz)
        )
    return tuple(items)


def registered_synthesizer() -> Callable[..., bytes]:
    if str(SAMANTHA_ROOT) not in sys.path:
        sys.path.insert(0, str(SAMANTHA_ROOT))

    from app.capabilities import RiskLevel, get_capability
    from app.speech.edge_tts_mp3 import synthesize_edge_tts_mp3_sync

    capability = get_capability(CAPABILITY_ID)
    if capability.risk != RiskLevel.EXTERNAL_GENERATION:
        raise RuntimeError("Audio capability nemá očekávanou úroveň external_generation.")
    if capability.tool != CAPABILITY_TOOL:
        raise RuntimeError("Audio capability neukazuje na schválený syntetizér.")
    if capability.metadata.get("durable_consent") != "trusted_external_generation_v1":
        raise RuntimeError("Audio capability nemá očekávaný trvalý souhlas.")
    return synthesize_edge_tts_mp3_sync


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


def _manifest(items: tuple[CastingItem, ...]) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "purpose": "local VocabularyEN voice casting; not production audio",
        "rate": RATE,
        "voices": [
            {
                "id": voice.voice_id,
                "slug": voice.slug,
                "language": voice.language,
                "label": voice.label,
                "description": voice.description,
            }
            for voice in VOICES
        ],
        "items": [
            {
                "id": item.item_id,
                "order": item.order,
                "displayEn": item.display_en,
                "displayCz": item.display_cz,
                "speakEn": item.speak_en,
                "speakCz": item.speak_cz,
            }
            for item in items
        ],
        "audio": {
            voice.voice_id: {
                item.item_id: f"audio/{voice.slug}/{item.item_id}.mp3"
                for item in items
            }
            for voice in VOICES
        },
    }


def build_casting(
    output_dir: Path,
    *,
    synthesize: Callable[..., bytes],
    force: bool = False,
    csv_path: Path = CSV_PATH,
) -> dict[str, int]:
    items = load_casting_items(csv_path)
    generated = 0
    skipped = 0

    for voice in VOICES:
        for item in items:
            target = output_dir / "audio" / voice.slug / f"{item.item_id}.mp3"
            if target.exists() and not force:
                skipped += 1
                continue
            text = item.speak_en if voice.language == "en" else item.speak_cz
            audio = synthesize(text, voice=voice.voice_id, rate=RATE)
            if not isinstance(audio, bytes) or len(audio) < 512:
                raise RuntimeError(
                    f"Neplatné audio pro {voice.voice_id}/{item.item_id}: "
                    f"{len(audio) if isinstance(audio, bytes) else 'není bytes'} bajtů."
                )
            _atomic_write(target, audio)
            generated += 1

    manifest = json.dumps(_manifest(items), ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    _atomic_write(output_dir / "casting.json", manifest)
    return {"generated": generated, "skipped": skipped, "total": len(VOICES) * len(items)}


def planned_files(output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    items = load_casting_items()
    return [
        output_dir / "audio" / voice.slug / f"{item.item_id}.mp3"
        for voice in VOICES
        for item in items
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="vygeneruje lokální castingová MP3")
    parser.add_argument("--force", action="store_true", help="znovu vygeneruje i existující MP3")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    files = planned_files(args.output_dir)
    if not args.apply:
        print(f"Casting je připraven pro {len(files)} MP3. Bez --apply se nic nezměnilo.")
        for path in files:
            print(path.relative_to(REPO_ROOT))
        return 0

    result = build_casting(
        args.output_dir,
        synthesize=registered_synthesizer(),
        force=args.force,
    )
    print(
        f"Casting hotov: {result['generated']} vygenerováno, "
        f"{result['skipped']} ponecháno, {result['total']} celkem."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
