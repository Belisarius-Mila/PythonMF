from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_DIR = REPO_ROOT / "VocabularyEN"
if str(VOCABULARY_DIR) not in sys.path:
    sys.path.insert(0, str(VOCABULARY_DIR))
BUILDER_PATH = VOCABULARY_DIR / "build_vocabulary_en_audio.py"
SPEC = importlib.util.spec_from_file_location("vocabularyen_audio_library", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)
import build_vocabulary_en_sentence_audio as sentence_builder


class VocabularyEnAudioLibraryTests(unittest.TestCase):
    def test_selected_voices_and_spoken_text_normalization_are_canonical(self) -> None:
        self.assertEqual(builder.VOICES["en"]["id"], "en-US-AriaNeural")
        self.assertEqual(builder.VOICES["cz"]["id"], "cs-CZ-VlastaNeural")
        self.assertEqual(builder.RATE, "-10%")
        self.assertEqual(builder.normalize_spoken_text("a glass (of water)"), "a glass of water")
        self.assertEqual(
            builder.normalize_spoken_text("pravý, správný, doprava"),
            "pravý. správný. doprava",
        )

    def test_builder_generates_only_unique_missing_assets_and_verifies_coverage(self) -> None:
        items = [
            {"id": 1, "en": "hello", "cz": "ahoj"},
            {"id": 2, "en": "hello", "cz": "dobrý den, ahoj"},
        ]
        calls: list[tuple[str, str, str]] = []

        def fake_synthesize(text: str, *, voice: str, rate: str) -> bytes:
            calls.append((text, voice, rate))
            return b"ID3" + (f"{voice}|{rate}|{text}".encode("utf-8") * 80)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "vocabulary-en.json").write_text(
                json.dumps({"items": items}), encoding="utf-8"
            )
            csv_path = root / "VocabularyEN.csv"
            csv_path.write_text(
                "EN,CZ,Order\nhello,ahoj,1\nhello,\"dobrý den, ahoj\",2\n",
                encoding="utf-8",
            )

            first = builder.build_library(root, synthesize=fake_synthesize, csv_path=csv_path)
            second = builder.build_library(root, synthesize=fake_synthesize, csv_path=csv_path)
            verified = builder.verify_library(root, csv_path)

            self.assertEqual(first["generated"], 3)
            self.assertEqual(first["assets"], 3)
            self.assertEqual(second["generated"], 0)
            self.assertEqual(second["skipped"], 3)
            self.assertEqual(len(calls), 3)
            self.assertEqual(verified, {"items": 2, "references": 4, "assets": 3})

    def test_builder_refuses_stale_web_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data" / "vocabulary-en.json").write_text(
                json.dumps({"items": [{"id": 1, "en": "wrong", "cz": "ahoj"}]}),
                encoding="utf-8",
            )
            csv_path = root / "VocabularyEN.csv"
            csv_path.write_text("EN,CZ,Order\nhello,ahoj,1\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Nejprve spusť"):
                builder.build_library(root, synthesize=lambda *_args, **_kwargs: b"", csv_path=csv_path)

    def test_cat_voice_correction_is_scoped_and_survives_rebuild(self) -> None:
        items = [{"id": 20, "en": "cat", "cz": "kočka"},
                 {"id": 21, "en": "catch", "cz": "chytit"}]
        calls = []

        def synthesize(text, *, voice, rate):
            calls.append((text, voice))
            return b"ID3" + b"x" * 1500

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "data/vocabulary-en.json").write_text(json.dumps({"items": items}))
            csv_path = root / "VocabularyEN.csv"
            csv_path.write_text("EN,CZ,Order\ncat,kočka,20\ncatch,chytit,21\n", encoding="utf-8")
            builder.build_library(root, synthesize=synthesize, csv_path=csv_path)
            result = builder.build_library(root, synthesize=synthesize, csv_path=csv_path)
            manifest = json.loads((root / builder.MANIFEST_RELATIVE_PATH).read_text())
            cat = manifest["items"]["20"]
            self.assertIn(("cat", "en-US-JennyNeural"), calls)
            self.assertIn(("catch", "en-US-AriaNeural"), calls)
            self.assertIn(("kočka", "cs-CZ-VlastaNeural"), calls)
            self.assertEqual(cat["sourceEn"], "cat")
            self.assertEqual(cat["spokenEn"], "cat")
            self.assertEqual(cat["enVoice"], "en-US-JennyNeural")
            self.assertIn("en-us-jenny-neural/", cat["en"])
            self.assertEqual(result["generated"], 0)
            self.assertEqual(len(calls), 4)

    def test_production_web_uses_mp3_manifest_without_system_speech_fallback(self) -> None:
        html = (REPO_ROOT / "docs" / "vocabulary-en" / "index.html").read_text(encoding="utf-8")
        javascript = (REPO_ROOT / "docs" / "vocabulary-en" / "gallery.js").read_text(encoding="utf-8")

        self.assertIn("data-audio-url", html)
        self.assertIn("vocabulary-en-audio.json", javascript)
        self.assertIn("new Audio", javascript)
        self.assertNotIn("speechSynthesis", javascript)
        self.assertNotIn("SpeechSynthesisUtterance", javascript)

    def test_committed_production_library_covers_current_vocabulary(self) -> None:
        verified = builder.verify_library()
        manifest = json.loads(
            (REPO_ROOT / "docs" / "data" / "vocabulary-en-audio.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(verified, {"items": 425, "references": 850, "assets": 845})
        self.assertEqual(manifest["voices"]["en"]["label"], "Aria")
        self.assertEqual(manifest["voices"]["cz"]["label"], "Vlasta")


class VocabularyEnSentenceAudioTests(unittest.TestCase):
    def test_production_sentence_library_covers_all_current_sentence_pairs(self):
        result = sentence_builder.audit()
        self.assertEqual(result, dict(itemCount=425, audioReferences=850, uniqueAssets=850,
                                      missing=0, manifest_matches=True, complete=True))

    def fixture(self, root):
        items = [{"id": 20, "uid": "ven-0020", "en": "cat", "cz": "kočka",
                  "sentenceEn": "The cat sleeps, then wakes up.", "sentenceCz": "Kočka spí, pak se probudí."},
                 {"id": 21, "uid": "ven-0021", "en": "catch", "cz": "chytit",
                  "sentenceEn": "Catch it!", "sentenceCz": "Chyť to!"}]
        (root/"data").mkdir()
        (root/"data/vocabulary-en.json").write_text(json.dumps({"items": items}))
        csv_path = root/"VocabularyEN.csv"
        with csv_path.open("w", newline="") as handle:
            w = csv.DictWriter(handle, fieldnames=["EN", "CZ", "Order", "Sentence", "SentenceT"])
            w.writeheader()
            for i in items:
                w.writerow(dict(EN=i["en"], CZ=i["cz"], Order=i["id"], Sentence=i["sentenceEn"], SentenceT=i["sentenceCz"]))
        return items, csv_path

    def test_sentence_text_and_voice_preserve_punctuation_and_do_not_inherit_word_exceptions(self):
        self.assertEqual(sentence_builder.sentence_text("Hello, world; how are you?"), "Hello, world; how are you?")
        with tempfile.TemporaryDirectory() as t:
            root = Path(t);items, csv_path = self.fixture(root);calls = []
            def synth(text, **kwargs):
                calls.append((text, kwargs)); return b"ID3"+b"x"*1500
            result = sentence_builder.build_library(root, csv_path=csv_path, synthesize=synth, receipt_path=root/"private/receipt.json", workers=2)
            self.assertTrue(result["complete"])
            self.assertIn((items[0]["sentenceEn"], dict(voice="en-US-AriaNeural", rate="-10%")), calls)
            self.assertIn((items[0]["sentenceCz"], dict(voice="cs-CZ-VlastaNeural", rate="-10%")), calls)
            self.assertTrue(sentence_builder.audit(root, csv_path)["complete"])

    def test_partial_generation_has_no_complete_manifest_and_resume_never_regenerates_saved_audio(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t);_, csv_path = self.fixture(root);calls = []
            def synth(text, **kwargs):
                calls.append(text);return b"ID3"+b"x"*1500
            kwargs = dict(csv_path=csv_path, synthesize=synth, receipt_path=root/"private/r.json")
            first = sentence_builder.build_library(root, limit=2, **kwargs)
            self.assertEqual(first["missing"], 2);self.assertFalse((root/sentence_builder.MANIFEST_RELATIVE_PATH).exists())
            second = sentence_builder.build_library(root, **kwargs)
            self.assertEqual(second["skipped"], 2);self.assertTrue(second["complete"]);self.assertEqual(len(calls),4)
            sentence_builder.build_library(root, **kwargs);self.assertEqual(len(calls),4)

    def test_failed_or_interrupted_request_is_never_sent_again_automatically(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t);_, csv_path = self.fixture(root);calls = []
            def fail(text, **kwargs):
                calls.append(text);raise RuntimeError("lost response")
            kwargs = dict(csv_path=csv_path, synthesize=fail, receipt_path=root/"private/r.json")
            with self.assertRaisesRegex(RuntimeError,"lost response"): sentence_builder.build_library(root, **kwargs)
            with self.assertRaisesRegex(RuntimeError,"opakování"): sentence_builder.build_library(root, **kwargs)
            self.assertEqual(len(calls),1)

    def test_modified_sentence_in_web_is_rejected_before_any_generation(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t);items, csv_path = self.fixture(root);items[0]["sentenceCz"]="jiná věta"
            (root/"data/vocabulary-en.json").write_text(json.dumps({"items":items}))
            with self.assertRaisesRegex(ValueError,"neodpovídají CSV"):
                sentence_builder.build_library(root,csv_path=csv_path,synthesize=lambda *a,**k:self.fail("No request allowed"),receipt_path=root/"r.json")

    def test_changed_saved_bytes_and_changed_receipt_source_are_not_silently_reused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);_,csv_path=self.fixture(root);kwargs=dict(csv_path=csv_path,synthesize=lambda *a,**k:b"ID3"+b"x"*1500,receipt_path=root/"r.json")
            sentence_builder.build_library(root,**kwargs)
            manifest=sentence_builder.load_manifest(root,csv_path);p=root/next(iter(sentence_builder.jobs(manifest)))
            p.write_bytes(b"ID3"+b"y"*1500)
            with self.assertRaisesRegex(ValueError,"změnila"):sentence_builder.build_library(root,**kwargs)
            receipt=json.loads((root/"r.json").read_text());receipt["sourceDigest"]="other";(root/"r.json").write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError,"Zdroj se změnil"):sentence_builder.build_library(root,**kwargs)

    def test_empty_or_too_long_sentences_are_refused_without_truncation(self):
        for value in ("", " ", None, "x"*1501):
            with self.subTest(value_type=type(value).__name__),self.assertRaises(ValueError):sentence_builder.sentence_text(value)

    def test_duplicate_sentences_share_one_asset_but_keep_both_uids(self):
        items=[dict(id=i,uid=f"ven-{i}",en=str(i),cz=str(i),sentenceEn="Hello!",sentenceCz="Ahoj!") for i in (1,2)]
        manifest=sentence_builder.build_manifest(items)
        self.assertEqual(manifest["stats"],dict(itemCount=2,audioReferences=4,uniqueAssets=2))
        self.assertEqual(set(manifest["items"]),{"ven-1","ven-2"})


if __name__ == "__main__":
    unittest.main()
