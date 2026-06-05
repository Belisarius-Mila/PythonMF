#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech.edge_tts_mp3 import DEFAULT_EDGE_TTS_RATE, DEFAULT_EDGE_TTS_VOICE, EdgeTtsError
from app.speech.edge_tts_open import speak_edge_tts_open
from app.speech.local_tts import SpeechError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vygeneruje české Edge TTS MP3 a otevře ho v macOS přehrávači.")
    parser.add_argument("text", nargs="*", help="Text k přečtení. Pokud chybí, čte se stdin.")
    parser.add_argument("--voice", default=DEFAULT_EDGE_TTS_VOICE, help=f"Edge TTS hlas (default: {DEFAULT_EDGE_TTS_VOICE}).")
    parser.add_argument("--rate", default=DEFAULT_EDGE_TTS_RATE, help=f"Rychlost řeči (default: {DEFAULT_EDGE_TTS_RATE}).")
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp"))
    parser.add_argument("--json", action="store_true", help="Vypsat výsledek jako JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = " ".join(args.text).strip() if args.text else sys.stdin.read().strip()
    try:
        result = speak_edge_tts_open(text, output_dir=args.output_dir, voice=args.voice, rate=args.rate)
    except (SpeechError, EdgeTtsError) as exc:
        print(f"Chyba: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
        print(result["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
