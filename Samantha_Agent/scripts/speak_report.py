#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.speech.local_tts import DEFAULT_VOICE
from app.speech.report import DEFAULT_COCKPIT_SPEAK_URL, speak_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Přečte krátký Adamův report nahlas.")
    parser.add_argument("text", nargs="*", help="Text reportu. Pokud chybí, čte se stdin.")
    parser.add_argument("--endpoint", default=DEFAULT_COCKPIT_SPEAK_URL, help="Cockpit /api/speech/speak endpoint.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"Hlas pro lokální fallback (default: {DEFAULT_VOICE}).")
    parser.add_argument("--no-fallback", action="store_true", help="Nepoužívat lokální TTS fallback.")
    parser.add_argument("--json", action="store_true", help="Vytisknout strojově čitelný výsledek.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = " ".join(args.text).strip() if args.text else sys.stdin.read().strip()
    result = speak_report(
        text,
        endpoint=args.endpoint,
        voice=args.voice,
        allow_local_fallback=not args.no_fallback,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
