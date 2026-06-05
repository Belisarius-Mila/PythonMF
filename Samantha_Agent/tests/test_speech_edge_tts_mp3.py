from __future__ import annotations

import asyncio
import unittest

from app.speech.edge_tts_mp3 import EdgeTtsError, synthesize_edge_tts_mp3


class FakeCommunicate:
    def __init__(self, *, text: str, voice: str, rate: str) -> None:
        self.text = text
        self.voice = voice
        self.rate = rate

    async def stream(self):
        yield {"type": "metadata", "data": b""}
        yield {"type": "audio", "data": b"MP3"}


class EmptyCommunicate:
    async def stream(self):
        yield {"type": "metadata", "data": b""}


class EdgeTtsMp3Tests(unittest.TestCase):
    def test_synthesize_edge_tts_mp3_collects_audio_chunks(self) -> None:
        audio = asyncio.run(
            synthesize_edge_tts_mp3(
                "Ahoj",
                communicate_factory=lambda **kwargs: FakeCommunicate(**kwargs),
            )
        )

        self.assertEqual(audio, b"MP3")

    def test_synthesize_edge_tts_mp3_requires_audio(self) -> None:
        with self.assertRaises(EdgeTtsError):
            asyncio.run(
                synthesize_edge_tts_mp3(
                    "Ahoj",
                    communicate_factory=lambda **kwargs: EmptyCommunicate(),
                )
            )


if __name__ == "__main__":
    unittest.main()
