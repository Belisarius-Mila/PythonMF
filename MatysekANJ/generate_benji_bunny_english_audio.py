#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

import certifi


API_URL = "https://api.openai.com/v1/audio/speech"
MODEL = "gpt-4o-mini-tts"
ROOT = Path(__file__).resolve().parent
DIALOGUE_PATH = ROOT / "benji_bunny_dialogue.json"
ENGLISH_DIR = ROOT / "benji_bunny_audio" / "english"
CZECH_DIR = ROOT / "benji_bunny_audio" / "czech"


def load_dialogue() -> list[dict[str, str]]:
    return json.loads(DIALOGUE_PATH.read_text(encoding="utf-8"))


def generate_sample(api_key: str, item: dict[str, str]) -> Path:
    payload = {
        "model": MODEL,
        "voice": item["voice_en"],
        "input": item["text_en"],
        "response_format": "mp3",
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    output_path = ENGLISH_DIR / item["audio_en"]
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=120, context=ssl_context) as response:
        output_path.write_bytes(response.read())
    return output_path


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
      print("OPENAI_API_KEY is not set.", file=sys.stderr)
      return 1

    ENGLISH_DIR.mkdir(parents=True, exist_ok=True)
    CZECH_DIR.mkdir(parents=True, exist_ok=True)
    (CZECH_DIR / "README.txt").write_text(
        "Sem uloz ceske audio soubory podle nazvu v benji_bunny_dialogue.json.\n",
        encoding="utf-8",
    )

    for item in load_dialogue():
        try:
            output_path = generate_sample(api_key, item)
            print(f"OK  {output_path}")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            print(f"HTTP {error.code} for {item['audio_en']}: {body}", file=sys.stderr)
            return 2
        except urllib.error.URLError as error:
            print(f"Network error for {item['audio_en']}: {error}", file=sys.stderr)
            return 3

    print(f"\nGenerated English files in {ENGLISH_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
