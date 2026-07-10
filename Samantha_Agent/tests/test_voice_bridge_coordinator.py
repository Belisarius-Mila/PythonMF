from __future__ import annotations

import unittest
from pathlib import Path

from app.speech import TranscriptionError
from app.voice_bridge_coordinator import (
    VoiceBridgeCommandDependencies,
    coordinate_text_voice_command,
    coordinate_transcribed_voice_command,
)


class VoiceBridgeCoordinatorTests(unittest.TestCase):
    def test_running_watcher_is_the_only_owner_for_text_and_recording(self) -> None:
        saved_commands: list[dict[str, object]] = []
        inline_calls: list[dict[str, object]] = []
        voice_mode = {"ok": True, "running": True, "pid": 12345}

        def save_command(command: dict[str, object], **kwargs: object) -> dict[str, object]:
            saved_commands.append(command)
            return {"saved": True, "latest_voice_command_path": "latest_voice_command.md"}

        def deliver_inline(**kwargs: object) -> dict[str, object]:
            inline_calls.append(kwargs)
            return {"voice_delivery_status": "unexpected_inline_delivery"}

        dependencies = VoiceBridgeCommandDependencies(
            save_command=save_command,
            load_voice_mode=lambda: voice_mode,
            deliver_inline=deliver_inline,
            record_transcription_failure=lambda **kwargs: None,
            sanitize_text=lambda text: text,
        )
        paths = {
            "inbox_dir": Path("/tmp/voice-inbox"),
            "pending_path": Path("/tmp/pending.json"),
            "history_path": Path("/tmp/history.jsonl"),
        }

        text_result = coordinate_text_voice_command(
            {"text": "Ověř textovou cestu."},
            dependencies=dependencies,
            **paths,
        )
        recording_result = coordinate_transcribed_voice_command(
            {"audio_base64": "abc", "mime_type": "audio/webm", "language": "cs"},
            dependencies=dependencies,
            transcriber=lambda *args, **kwargs: {"ok": True, "text": "Ověř nahranou cestu."},
            **paths,
        )

        self.assertEqual(text_result["voice_delivery_status"], "watcher_will_deliver")
        self.assertEqual(recording_result["voice_delivery_status"], "watcher_will_deliver")
        self.assertEqual(inline_calls, [])
        self.assertEqual(
            [command["text"] for command in saved_commands],
            ["Ověř textovou cestu.", "Ověř nahranou cestu."],
        )

    def test_explicit_inline_adapter_bypasses_running_watcher(self) -> None:
        explicit_bridge = lambda command: {"ok": True, "verified": True}
        inline_calls: list[dict[str, object]] = []

        def deliver_inline(**kwargs: object) -> dict[str, object]:
            inline_calls.append(kwargs)
            return {
                "voice_delivery_status": "voice_command_delivered",
                "voice_delivery_message": "Doručeno.",
            }

        dependencies = VoiceBridgeCommandDependencies(
            save_command=lambda command, **kwargs: {"saved": True},
            load_voice_mode=lambda: {"ok": True, "running": True},
            deliver_inline=deliver_inline,
            record_transcription_failure=lambda **kwargs: None,
            sanitize_text=lambda text: text,
        )

        result = coordinate_text_voice_command(
            {"text": "Použij testovací bridge."},
            dependencies=dependencies,
            inbox_dir=Path("/tmp/voice-inbox"),
            pending_path=Path("/tmp/pending.json"),
            history_path=Path("/tmp/history.jsonl"),
            terminal_bridge=explicit_bridge,
        )

        self.assertEqual(result["voice_delivery_status"], "voice_command_delivered")
        self.assertEqual(len(inline_calls), 1)
        self.assertIs(inline_calls[0]["terminal_bridge"], explicit_bridge)

    def test_transcription_failure_is_recorded_without_delivery(self) -> None:
        failures: list[str] = []
        inline_calls: list[dict[str, object]] = []

        def fail_transcription(*args: object, **kwargs: object) -> dict[str, object]:
            raise TranscriptionError("testovací chyba přepisu")

        dependencies = VoiceBridgeCommandDependencies(
            save_command=lambda command, **kwargs: {"saved": True},
            load_voice_mode=lambda: {"ok": True, "running": False},
            deliver_inline=lambda **kwargs: inline_calls.append(kwargs) or {},
            record_transcription_failure=lambda **kwargs: failures.append(str(kwargs["message"])),
            sanitize_text=lambda text: text,
        )

        result = coordinate_transcribed_voice_command(
            {"audio_base64": "abc", "mime_type": "audio/webm"},
            dependencies=dependencies,
            inbox_dir=Path("/tmp/voice-inbox"),
            pending_path=Path("/tmp/pending.json"),
            history_path=Path("/tmp/history.jsonl"),
            transcriber=fail_transcription,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "transcription_failed")
        self.assertEqual(failures, ["testovací chyba přepisu"])
        self.assertEqual(inline_calls, [])

    def test_empty_text_stops_before_persistence_or_delivery(self) -> None:
        calls: list[str] = []
        dependencies = VoiceBridgeCommandDependencies(
            save_command=lambda command, **kwargs: calls.append("save") or {},
            load_voice_mode=lambda: calls.append("status") or {},
            deliver_inline=lambda **kwargs: calls.append("inline") or {},
            record_transcription_failure=lambda **kwargs: calls.append("failure"),
            sanitize_text=lambda text: text,
        )

        result = coordinate_text_voice_command(
            {"text": "   "},
            dependencies=dependencies,
            inbox_dir=Path("/tmp/voice-inbox"),
            pending_path=Path("/tmp/pending.json"),
            history_path=Path("/tmp/history.jsonl"),
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "empty_voice_text")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
