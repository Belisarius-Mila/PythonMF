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
OUTPUT_DIR = Path(__file__).resolve().parent / "voice_test_english"

SAMPLES = [
    {
        "filename": "benji_intro_fable.mp3",
        "voice": "fable",
        "text": "Hello, I am Benji. Let us explore the forest together.",
    },
    {
        "filename": "benji_colors_fable.mp3",
        "voice": "fable",
        "text": "Click the mushrooms and listen to the colours.",
    },
    {
        "filename": "bunny_intro_shimmer.mp3",
        "voice": "shimmer",
        "text": "Hello, I am Bunny. Come and play with me.",
    },
    {
        "filename": "bunny_intro_ash.mp3",
        "voice": "ash",
        "text": "Hello, I am Bunny. Come and play with me.",
    },
    {
        "filename": "bunny_intro_echo.mp3",
        "voice": "echo",
        "text": "Hello, I am Bunny. Come and play with me.",
    },
    {
        "filename": "bunny_intro_onyx.mp3",
        "voice": "onyx",
        "text": "Hello, I am Bunny. Come and play with me.",
    },
    {
        "filename": "bunny_count_shimmer.mp3",
        "voice": "shimmer",
        "text": "Let us count the mushrooms. One, two, three.",
    },
]


def generate_sample(api_key: str, sample: dict[str, str]) -> None:
    payload = {
        "model": MODEL,
        "voice": sample["voice"],
        "input": sample["text"],
        "response_format": "mp3",
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    output_path = OUTPUT_DIR / sample["filename"]
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=120, context=ssl_context) as response:
        output_path.write_bytes(response.read())
    print(f"OK  {output_path}")


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "README.txt").write_text(
        "Test English audio generated via OpenAI TTS.\n"
        "Benji uses voice 'fable'. Bunny uses voice 'shimmer'.\n",
        encoding="utf-8",
    )

    for sample in SAMPLES:
        try:
            generate_sample(api_key, sample)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            print(f"HTTP {error.code} for {sample['filename']}: {body}", file=sys.stderr)
            return 2
        except urllib.error.URLError as error:
            print(f"Network error for {sample['filename']}: {error}", file=sys.stderr)
            return 3

    print(f"\nGenerated {len(SAMPLES)} files in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
