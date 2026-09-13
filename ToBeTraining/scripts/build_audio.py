#!/usr/bin/env python3
"""Generate fixed MP3s through Samantha's registered project-audio capability.

No CSV mutations or publication. Existing nonempty tracks are reused, so an
interrupted run can resume. Only public teaching sentences leave this machine.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "Samantha_Agent"))
from app.speech.edge_tts_mp3 import synthesize_edge_tts_mp3


async def main():
    data = json.loads((ROOT / "web/data.json").read_text())
    semaphore = asyncio.Semaphore(3)
    completed = 0

    async def generate(key, clip):
        nonlocal completed
        path = ROOT / "web" / clip["src"]
        if path.exists() and path.stat().st_size > 1000:
            completed += 1
            return
        async with semaphore:
            for attempt in range(3):
                try:
                    audio = await asyncio.wait_for(synthesize_edge_tts_mp3(
                        clip["text"], voice=data["voice"], rate=data["rate"]), timeout=60)
                    if len(audio) <= 1000:
                        raise ValueError("Audio too short")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(audio)
                    completed += 1
                    if completed % 20 == 0:
                        print(f"MP3: {completed}/{len(data['audio'])}", flush=True)
                    return
                except Exception as error:
                    if attempt == 2:
                        raise RuntimeError(f"Audio generation failed for {key}: {type(error).__name__}") from None
                    await asyncio.sleep(2 * (attempt + 1))

    await asyncio.gather(*(generate(key, clip) for key, clip in data["audio"].items()))
    print(f"MP3 ready: {completed}/{len(data['audio'])}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
