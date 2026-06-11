#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech.edge_tts_mp3 import DEFAULT_EDGE_TTS_RATE, DEFAULT_EDGE_TTS_VOICE, EdgeTtsError
from app.speech.edge_tts_open import speak_edge_tts_open
from app.speech.local_tts import DEFAULT_VOICE as DEFAULT_LOCAL_VOICE
from app.speech.local_tts import SpeechError, speak_text


ENGINES = {"local", "edge", "edge-fallback"}


def default_engine() -> str:
    requested = os.environ.get("ADAM_VOICE_TTS_ENGINE", "local").strip()
    return requested if requested in ENGINES else "local"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Přečte krátký výsledek nahlas. Výchozí režim je rychlé lokální macOS TTS.")
    parser.add_argument("text", nargs="*", help="Text k přečtení. Pokud chybí, čte se stdin.")
    parser.add_argument(
        "--engine",
        choices=sorted(ENGINES),
        default=default_engine(),
        help="TTS engine: local = rychlý macOS say, edge = online MP3, edge-fallback = Edge a při selhání local.",
    )
    parser.add_argument("--voice", default=None, help="Hlas pro vybraný engine. Default: Zuzana pro local, AntoninNeural pro Edge.")
    parser.add_argument("--rate", default=DEFAULT_EDGE_TTS_RATE, help=f"Rychlost řeči (default: {DEFAULT_EDGE_TTS_RATE}).")
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp"))
    parser.add_argument("--json", action="store_true", help="Vypsat výsledek jako JSON.")
    return parser.parse_args()


def speak_voice_reply(
    text: str,
    *,
    engine: str,
    voice: str | None,
    rate: str = DEFAULT_EDGE_TTS_RATE,
    output_dir: Path = Path("/private/tmp"),
    local_speaker: Callable[..., dict[str, Any]] = speak_text,
    edge_speaker: Callable[..., dict[str, Any]] = speak_edge_tts_open,
) -> dict[str, Any]:
    if engine == "local":
        result = local_speaker(text, voice=voice or DEFAULT_LOCAL_VOICE)
        return {**result, "transport": "local_tts"}
    if engine == "edge":
        return edge_speaker(text, output_dir=output_dir, voice=voice or DEFAULT_EDGE_TTS_VOICE, rate=rate)
    if engine == "edge-fallback":
        try:
            return edge_speaker(text, output_dir=output_dir, voice=voice or DEFAULT_EDGE_TTS_VOICE, rate=rate)
        except (SpeechError, EdgeTtsError) as exc:
            result = local_speaker(text, voice=DEFAULT_LOCAL_VOICE)
            return {
                **result,
                "transport": "local_tts",
                "fallback_from": "edge_tts_open",
                "fallback_reason": str(exc),
            }
    raise SpeechError(f"Nepodporovaný TTS engine: {engine}")


def main() -> int:
    args = parse_args()
    text = " ".join(args.text).strip() if args.text else sys.stdin.read().strip()
    try:
        result = speak_voice_reply(text, engine=args.engine, voice=args.voice, rate=args.rate, output_dir=args.output_dir)
    except (SpeechError, EdgeTtsError) as exc:
        print(f"Chyba: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
        if result.get("path"):
            print(result["path"])
        if result.get("fallback_from"):
            print(f"Fallback: {result['fallback_from']}: {result.get('fallback_reason', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
