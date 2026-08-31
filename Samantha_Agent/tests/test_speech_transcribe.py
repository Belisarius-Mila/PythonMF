from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from app.speech.transcribe import (
    MAX_AUDIO_BYTES,
    TranscriptionError,
    decode_audio_base64,
    normalize_mime_type,
    openai_api_key_available,
    transcription_context_fields,
    transcribe_audio_base64,
    transcribe_audio_bytes,
    transcribe_audio_file,
    transcribe_audio_file_with_curl,
    main,
)


class FakeTranscriptions:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(text="Najdi dnešní dokumenty.")


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.transcriptions = FakeTranscriptions()
        self.audio = SimpleNamespace(transcriptions=self.transcriptions)


class SpeechTranscribeTests(unittest.TestCase):
    def test_decode_audio_base64_accepts_plain_and_data_url(self) -> None:
        encoded = base64.b64encode(b"audio").decode("ascii")

        self.assertEqual(decode_audio_base64(encoded), b"audio")
        self.assertEqual(decode_audio_base64(f"data:audio/webm;base64,{encoded}"), b"audio")

    def test_decode_audio_base64_rejects_bad_or_large_audio(self) -> None:
        with self.assertRaises(TranscriptionError):
            decode_audio_base64("not valid base64")
        with self.assertRaises(TranscriptionError):
            decode_audio_base64(base64.b64encode(b"x" * (MAX_AUDIO_BYTES + 1)).decode("ascii"))

    def test_normalize_mime_type_allows_expected_audio_formats(self) -> None:
        self.assertEqual(normalize_mime_type("audio/webm;codecs=opus"), "audio/webm")
        self.assertEqual(normalize_mime_type("audio/mp4"), "audio/mp4")
        with self.assertRaises(TranscriptionError):
            normalize_mime_type("text/plain")

    def test_transcription_context_uses_structured_czech_hints(self) -> None:
        context = transcription_context_fields("CS")

        self.assertEqual(context["languages"], ["cs"])
        self.assertEqual(
            context["keywords"],
            ["Samantha", "Adam", "Míla", "Cockpit", "Human–Adam"],
        )
        with self.assertRaises(TranscriptionError):
            transcription_context_fields("czech")

    def test_openai_api_key_available_reloads_empty_env_from_dotenv(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("OPENAI_API_KEY=test-key-from-dotenv\n", encoding="utf-8")
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                self.assertTrue(openai_api_key_available(env_path=env_path))
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key-from-dotenv")

    def test_transcribe_audio_bytes_uses_openai_client_and_deletes_temp_file(self) -> None:
        client = FakeOpenAIClient()
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            result = transcribe_audio_bytes(
                b"fake audio",
                mime_type="audio/webm",
                client=client,
                temp_dir=temp_dir,
            )
            leftovers = list(Path(temp_dir).iterdir())

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Najdi dnešní dokumenty.")
        self.assertEqual(result["audio_bytes"], 10)
        self.assertEqual(leftovers, [])
        self.assertEqual(client.transcriptions.calls[0]["model"], "gpt-transcribe")
        self.assertEqual(client.transcriptions.calls[0]["response_format"], "json")
        self.assertEqual(
            client.transcriptions.calls[0]["extra_body"],
            {
                "languages": ["cs"],
                "keywords": ["Samantha", "Adam", "Míla", "Cockpit", "Human–Adam"],
            },
        )
        self.assertNotIn("language", client.transcriptions.calls[0])

    def test_transcribe_audio_base64_passes_decoded_audio_to_client(self) -> None:
        client = FakeOpenAIClient()
        encoded = base64.b64encode(b"fake audio").decode("ascii")

        result = transcribe_audio_base64(encoded, mime_type="audio/webm", client=client)

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Najdi dnešní dokumenty.")

    def test_transcribe_audio_file_reads_file_and_uses_client(self) -> None:
        client = FakeOpenAIClient()
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            audio_path = Path(temp_dir) / "voice.webm"
            audio_path.write_bytes(b"fake audio")

            result = transcribe_audio_file(audio_path, mime_type="audio/webm", client=client)

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Najdi dnešní dokumenty.")
        self.assertEqual(result["audio_bytes"], 10)

    def test_transcribe_audio_file_with_curl_posts_audio_without_secret_in_args(self) -> None:
        seen = {}

        def fake_runner(args, **kwargs):
            seen["args"] = args
            seen["input"] = kwargs["input"]
            self.assertNotIn("test-secret-key", " ".join(args))
            self.assertIn("Authorization: Bearer test-secret-key", kwargs["input"])
            self.assertIn("form = \"model=gpt-transcribe\"", kwargs["input"])
            self.assertIn("form = \"response_format=json\"", kwargs["input"])
            self.assertIn("form = \"languages[]=cs\"", kwargs["input"])
            self.assertIn("form = \"keywords[]=Samantha\"", kwargs["input"])
            self.assertIn("form = \"keywords[]=Míla\"", kwargs["input"])
            self.assertNotIn("form = \"language=", kwargs["input"])
            self.assertIn(";type=audio/webm", kwargs["input"])
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps({"text": "Najdi dnešní dokumenty."}),
                stderr="",
            )

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            audio_path = Path(temp_dir) / "voice.webm"
            audio_path.write_bytes(b"fake audio")
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-secret-key"}, clear=False):
                result = transcribe_audio_file_with_curl(audio_path, mime_type="audio/webm", runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "Najdi dnešní dokumenty.")
        self.assertEqual(result["audio_bytes"], 10)
        self.assertEqual(seen["args"][0], "/usr/bin/curl")
        self.assertIn("--config", seen["args"])

    def test_transcribe_audio_file_with_curl_reports_openai_error(self) -> None:
        def fake_runner(args, **kwargs):
            return subprocess.CompletedProcess(
                args,
                22,
                stdout=json.dumps({"error": {"message": "bad request"}}),
                stderr="",
            )

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            audio_path = Path(temp_dir) / "voice.webm"
            audio_path.write_bytes(b"fake audio")
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-secret-key"}, clear=False):
                with self.assertRaises(TranscriptionError) as cm:
                    transcribe_audio_file_with_curl(audio_path, mime_type="audio/webm", runner=fake_runner)

        self.assertIn("bad request", str(cm.exception))

    def test_transcribe_cli_main_outputs_json(self) -> None:
        fake_result = {
            "ok": True,
            "text": "Najdi dnešní dokumenty.",
            "model": "test-model",
            "language": "cs",
        }
        with (
            patch("app.speech.transcribe.transcribe_audio_file", return_value=fake_result) as transcribe,
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            code = main([
                "--audio-file",
                "/private/tmp/voice.webm",
                "--mime-type",
                "audio/webm",
                "--language",
                "cs",
                "--model",
                "test-model",
            ])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), fake_result)
        transcribe.assert_called_once()

    def test_transcribe_cli_main_reports_transcription_error(self) -> None:
        with (
            patch(
                "app.speech.transcribe.transcribe_audio_file",
                side_effect=TranscriptionError("Chybí OPENAI_API_KEY"),
            ),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            code = main(["--audio-file", "/private/tmp/voice.webm", "--mime-type", "audio/webm"])

        self.assertEqual(code, 1)
        result = json.loads(stdout.getvalue())
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "transcription_failed")
        self.assertIn("Chybí OPENAI_API_KEY", result["message"])


if __name__ == "__main__":
    unittest.main()
