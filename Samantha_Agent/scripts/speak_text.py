#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech import SpeechError, speak_text
from app.speech.local_tts import DEFAULT_VOICE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Přečte krátký text nahlas přes lokální macOS hlas.")
    parser.add_argument("text", nargs="*", help="Text k přečtení. Pokud chybí, čte se stdin.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"Hlas pro macOS say (default: {DEFAULT_VOICE})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = " ".join(args.text).strip() if args.text else sys.stdin.read().strip()
    try:
        result = speak_text(text, voice=args.voice)
    except SpeechError as exc:
        print(f"Chyba: {exc}", file=sys.stderr)
        return 1
    print(result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
