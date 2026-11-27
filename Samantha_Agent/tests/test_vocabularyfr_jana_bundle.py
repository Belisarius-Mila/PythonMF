from __future__ import annotations

import importlib.util
import hashlib
import json
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "VocabularyFR"))
from jana_launcher import portable_arguments  # noqa: E402
from local_audio import LocalAudio, LocalPictures  # noqa: E402
from vocab_trainer_fr import VocabularyTrainerApp  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "jana_bundle_builder", ROOT / "Samantha_Agent/scripts/build_jana_vocabularyfr_bundle.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class JanaBundleTests(unittest.TestCase):
    def test_portable_app_selects_only_its_adjacent_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "Janin slovník"
            folder.mkdir()
            for name in builder.DATA:
                (folder / name).write_text("data")
            exe = folder / "VocabularyFR.app/Contents/MacOS/VocabularyFR"
            self.assertEqual(portable_arguments(exe, []), ["--data-dir", str(folder)])

    def test_missing_data_does_not_create_or_migrate_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Chybí"):
                portable_arguments(folder / "VocabularyFR.app/Contents/MacOS/VocabularyFR", [])
            self.assertEqual(list(folder.iterdir()), [])

    def test_explicit_data_dir_remains_explicit(self):
        for args in (["--data-dir", "/tmp/test data"], ["--data-dir=/tmp/test data"]):
            self.assertEqual(portable_arguments("/unused", args), args)

    def test_symlink_data_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in builder.DATA:
                (folder / name).symlink_to(sys.executable)
            with self.assertRaisesRegex(ValueError, "Chybí"):
                portable_arguments(folder / "VocabularyFR.app/Contents/MacOS/VocabularyFR", [])

    def test_build_refuses_existing_output_without_changing_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            marker = folder / "keep.txt"
            marker.write_text("original")
            with self.assertRaisesRegex(ValueError, "existuje"):
                builder.validate_request({"input_dir": tmp, "output_dir": tmp, "python": sys.executable})
            self.assertEqual(marker.read_text(), "original")

    def test_build_refuses_incomplete_sentences_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in builder.DATA:
                (folder / name).write_text("FR,CZ,Sentence,SentenceT\nbonjour,ahoj,,\n")
            with self.assertRaisesRegex(ValueError, "věty"):
                builder.validate_request({"input_dir": tmp, "output_dir": str(folder / "new"),
                                          "python": sys.executable})
            self.assertFalse((folder / "new").exists())


class LocalAudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = b"synthetic-mp3-for-hash-test"
        (self.root / "voice.mp3").write_bytes(self.raw)
        self.body = {"schemaVersion": 1, "kind": "vocabulary-fr-local-audio", "items": [
            {"channel": "fr", "text": "Le thé est chaud.", "asset": "voice.mp3",
             "sha256": hashlib.sha256(self.raw).hexdigest()}]}
        self.save()
        self.audio = LocalAudio(self.root)

    def save(self):
        (self.root / "manifest.json").write_text(json.dumps(self.body))

    def test_exact_channel_and_text_no_inference(self):
        self.assertEqual(self.audio.resolve("fr", "Le thé est chaud."), self.root / "voice.mp3")
        self.assertIsNone(self.audio.resolve("cz", "Le thé est chaud."))
        self.assertIsNone(self.audio.resolve("fr", "Le thé est froid."))

    def test_cached_file_and_manifest_changes_invalidate_media(self):
        self.assertIsNotNone(self.audio.resolve("fr", "Le thé est chaud."))
        (self.root / "voice.mp3").write_bytes(b"changed")
        self.assertIsNone(self.audio.resolve("fr", "Le thé est chaud."))
        (self.root / "voice.mp3").write_bytes(self.raw)
        (self.root / "manifest.json").write_text("invalid JSON")
        self.assertIsNone(self.audio.resolve("fr", "Le thé est chaud."))

    def test_traversal_symlinks_and_conflicting_records_refused(self):
        for relative in ("../voice.mp3", "/voice.mp3", "nested/../voice.mp3", "nested\\voice.mp3"):
            self.body["items"][0]["asset"] = relative
            self.save()
            self.assertIsNone(self.audio.resolve("fr", "Le thé est chaud."))
        self.body["items"][0]["asset"] = "link.mp3"
        (self.root / "link.mp3").symlink_to(self.root / "voice.mp3")
        self.save()
        self.assertIsNone(self.audio.resolve("fr", "Le thé est chaud."))
        self.body["items"][0]["asset"] = "voice.mp3"
        self.body["items"].append({**self.body["items"][0], "asset": "other.mp3"})
        self.save()
        self.assertIsNone(self.audio.resolve("fr", "Le thé est chaud."))

    def test_picture_lookup_disambiguates_full_meaning_without_touching_audio(self):
        self.body["kind"] = "vocabulary-fr-local-pictures"
        self.body["items"] = [
            {"channel": "fr", "text": json.dumps(["carte", "platební karta"], ensure_ascii=False),
             "asset": "card.webp", "sha256": hashlib.sha256(self.raw).hexdigest()}]
        (self.root / "card.webp").write_bytes(self.raw)
        self.save()
        pictures = LocalPictures(self.root)
        self.assertEqual(pictures.resolve("carte", "platební karta"), self.root / "card.webp")
        self.assertIsNone(pictures.resolve("carte", "hrací karta"))
        self.assertIsNone(pictures.resolve("carte", "platební karty"))
        self.assertIsNone(self.audio.resolve("fr", self.body["items"][0]["text"]))

    def test_playback_failure_reports_fallback_without_retry(self):
        with patch("local_audio.subprocess.run", side_effect=OSError) as run:
            self.assertFalse(self.audio.play("fr", "Le thé est chaud."))
            self.assertEqual(run.call_count, 1)

    def test_trainer_uses_mp3_and_falls_back_to_original_say(self):
        class App:
            local_audio = self.audio
        with patch("local_audio.subprocess.run") as run:
            run.return_value.returncode = 0
            VocabularyTrainerApp._say_blocking(App(), "Thomas", "Le thé est chaud.", channel="fr")
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][0], "/usr/bin/afplay")
        with patch("vocab_trainer_fr.subprocess.run") as run:
            VocabularyTrainerApp._say_blocking(App(), "Thomas", "Missing clip", channel="fr")
            self.assertEqual(run.call_args.args[0], ["say", "-v", "Thomas", "Missing clip"])


if __name__ == "__main__":
    unittest.main()
