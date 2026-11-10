from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs/scene06_lake_arrival"
MIRROR = REPO / "MatysekANJ/web_mmtx/scene06_lake_arrival"
spec = importlib.util.spec_from_file_location("mmtx_opening_builder", REPO / "MatysekANJ/build_scene06_opening_audio.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
cs_spec = importlib.util.spec_from_file_location("mmtx_czech_builder", REPO / "MatysekANJ/build_scene06_czech_audio.py")
czech = importlib.util.module_from_spec(cs_spec)
cs_spec.loader.exec_module(czech)
dict_spec = importlib.util.spec_from_file_location("mmtx_dictionary_builder", REPO / "MatysekANJ/build_scene06_dictionary_audio.py")
dictionary = importlib.util.module_from_spec(dict_spec)
dict_spec.loader.exec_module(dictionary)


class Scene06OpeningTests(unittest.TestCase):
    def test_exact_approved_dialogue_and_voice_cast(self):
        lines = builder.dialogue()["lines"]
        self.assertEqual([(x["speaker"], x["text"]) for x in lines], [
            ("Benji", "Look! The lake!"),
            ("Fiona", "It’s beautiful. Look at the blue water."),
            ("Sunny", "And look at those clouds!"),
            ("Bunny", "They look like my ears!"),
            ("Bruno", "Two ears here. Two in the sky."),
            ("Sunny", "Four ears! Can you hear us better?"),
            ("Bunny", "Yes. So please don’t shout!"),
        ])
        self.assertEqual([x["voice"] for x in lines], [
            "en-US-AndrewNeural", "en-US-JennyNeural", "en-US-MichelleNeural",
            "en-US-AnaNeural", "en-US-GuyNeural", "en-US-MichelleNeural", "en-US-AnaNeural",
        ])

    def test_all_published_files_have_identical_mirrors(self):
        files = [x.relative_to(DOCS) for x in DOCS.rglob("*") if x.is_file()]
        self.assertGreaterEqual(len(files), 13)
        for path in files:
            self.assertEqual((DOCS / path).read_bytes(), (MIRROR / path).read_bytes(), str(path))

    def test_audio_integrity_and_decode(self):
        self.assertEqual(builder.check()["english_mp3"], 7)

    def test_picture_two_exact_dialogue_and_audio_integrity(self):
        rows = builder.dialogue(picture=2)["lines"]
        self.assertEqual([(x["speaker"], x["text"]) for x in rows], [
            ("Ollie", "Look! A big fish in my net!"), ("Bruno", "That’s a big dinner!"),
            ("Ollie", "Will you eat with me?"), ("Benji", "Thank you, but we have our own food."),
            ("Fiona", "We’re here for the meeting. Where is it?"),
            ("Ollie", "On the other side of the lake, next morning."),
            ("Sunny", "How will we find the place?"),
            ("Ollie", "Look for an old boat beside an old fishing hut."),
            ("Ollie", "Follow the path by the water."), ("Bunny", "Thank you, Ollie. Enjoy your fish!"),
        ])
        self.assertEqual({x["voice"] for x in rows if x["speaker"] == "Ollie"}, {"en-US-AndrewNeural"})
        self.assertEqual(builder.check(picture=2)["english_mp3"], 10)

    def test_picture_two_build_preserves_first_picture_and_its_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            (docs / "dialogue_02.json").write_bytes((DOCS / "dialogue_02.json").read_bytes())
            calls = []
            def synth(text, **kwargs):
                calls.append(text)
                kwargs["budget"].reserve(builder.ssml_parts(text, kwargs["voice"])[1])
                return b"ID3" + text.encode() * 100
            builder.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            before = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
            original_receipt = receipt.read_bytes()
            second_receipt = receipt.with_name("second.json")
            result = builder.build(docs=docs, mirror=mirror, receipt=second_receipt, picture=2,
                                   synthesizer=synth, validator=lambda x: None)
            self.assertEqual((result["new_requests"], len(calls)), (10, 17))
            self.assertEqual(receipt.read_bytes(), original_receipt)
            for path, content in before.items():
                self.assertEqual((docs / path).read_bytes(), content, str(path))
            again = builder.build(docs=docs, mirror=mirror, receipt=second_receipt, picture=2,
                                  synthesizer=synth, validator=lambda x: None)
            self.assertEqual((again["new_requests"], len(calls)), (0, 17))

    def test_picture_three_exact_dialogue_voices_and_decode(self):
        rows = builder.dialogue(picture=3)["lines"]
        self.assertEqual([(x["speaker"], x["text"]) for x in rows], [
            ("Dotty", "A beautiful jump, Freddie!"), ("Freddie", "And a big splash!"),
            ("Dotty", "Too big! Try a smaller splash next time."),
            ("Bunny", "Why are you practising?"), ("Freddie", "For the frog-jumping race!"),
            ("Fiona", "We’re here for the meeting."), ("Dotty", "We’re coming too. See you there!"),
            ("Freddie", "Just one more jump!"),
        ])
        self.assertEqual({x["voice"] for x in rows if x["speaker"] == "Freddie"}, {"en-US-GuyNeural"})
        self.assertEqual({x["voice"] for x in rows if x["speaker"] == "Dotty"}, {"en-US-JennyNeural"})
        self.assertEqual(builder.check(picture=3)["english_mp3"], 8)

    def test_picture_three_build_preserves_both_earlier_pictures_and_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, first_receipt = self.fixture(folder)
            for name in ("dialogue_02.json", "dialogue_03.json"):
                (docs / name).write_bytes((DOCS / name).read_bytes())
            calls = []
            def synth(text, **kwargs):
                calls.append(text)
                kwargs["budget"].reserve(builder.ssml_parts(text, kwargs["voice"])[1])
                return b"ID3" + text.encode() * 100
            receipts = [first_receipt, first_receipt.with_name("second.json")]
            for picture, receipt in enumerate(receipts, 1):
                builder.build(docs=docs, mirror=mirror, receipt=receipt, picture=picture,
                              synthesizer=synth, validator=lambda x: None)
            before = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
            old_receipts = [p.read_bytes() for p in receipts]
            third_receipt = first_receipt.with_name("third.json")
            result = builder.build(docs=docs, mirror=mirror, receipt=third_receipt, picture=3,
                                   synthesizer=synth, validator=lambda x: None)
            self.assertEqual((result["new_requests"], len(calls)), (8, 25))
            for path, content in before.items():
                self.assertEqual((docs / path).read_bytes(), content, str(path))
            self.assertEqual([p.read_bytes() for p in receipts], old_receipts)
            again = builder.build(docs=docs, mirror=mirror, receipt=third_receipt, picture=3,
                                  synthesizer=synth, validator=lambda x: None)
            self.assertEqual((again["new_requests"], len(calls)), (0, 25))

    def test_remaining_approved_transcript_voices_images_and_audio(self):
        # Frozen from the approved scenario, independently of the player data.
        transcripts = {
            4: "37be37a35779be865cd53a5b64b781447b059c489c6b4fdcf1cb9e5602daf212",
            5: "21268b60e92cdc16dcad53582d6c42d8a0d0a5decbfa8da9056d5f4ece9b4129",
            6: "aded26ea3b3fe87c12dd5e4e52a0a63cf99dc509173fdacc1f6a2672617300f9",
            7: "f46a687d32f693aef7b4790c1d0f73c1e19e52e5df9dc92a8974532173d15484",
            8: "d9200e6ac653a638cf124efc85086aa34432f7ccd125fd57e64bda36c8779af0",
            9: "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            10: "dd957f20ccdb8269a45af54d6d1449f5aecd5ce48f057a066dc75a33f00ddab7",
        }
        voices = {"Benji": "Andrew", "Bunny": "Ana", "Bruno": "Guy", "Fiona": "Jenny",
                  "Sunny": "Michelle", "Logan": "Christopher", "Old Stag": "Guy",
                  "Animals": "Andrew", "Woodpecker": "Andrew", "Freddie": "Guy",
                  "Dotty": "Jenny", "Ollie": "Andrew"}
        total = 0
        for picture, expected in transcripts.items():
            rows = builder.dialogue(picture=picture)["lines"]
            text = json.dumps([(x["speaker"], x["text"]) for x in rows], ensure_ascii=False, separators=(",", ":"))
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), expected)
            for row in rows:
                self.assertEqual(row["voice"], f'en-US-{voices[row["speaker"]]}Neural')
            total += builder.check(picture=picture)["english_mp3"]
        self.assertEqual(total, 42)
        pictures = json.loads((DOCS / "pictures.json").read_text())["pictures"]
        self.assertEqual([p["line_count"] for p in pictures], [7, 10, 8, 7, 7, 8, 8, 6, 0, 6])
        for picture in pictures[3:]:
            self.assertEqual(picture["layout"], "below")
            self.assertTrue((DOCS / picture["image"]).is_file())

    def test_silence_requires_no_transport_receipt_or_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            mirror.mkdir()
            for root in (docs, mirror):
                (root / "dialogue_09.json").write_bytes((DOCS / "dialogue_09.json").read_bytes())
            calls = []
            result = builder.build(docs=docs, mirror=mirror, receipt=receipt, picture=9,
                                   synthesizer=lambda *a, **k: calls.append(a))
            self.assertEqual((result["assets"], result["new_requests"], result["reserved_characters"]), (0, 0, 0))
            self.assertEqual(calls, [])
            self.assertFalse(receipt.exists())
            self.assertFalse((docs / "audio").exists())
            self.assertFalse((docs / "audio_manifest_09.json").exists())

    def test_silence_cannot_accidentally_become_a_spoken_line(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            data = builder.dialogue(picture=9)
            data["lines"] = [{"speaker": "Animals", "voice": "en-US-AndrewNeural",
                              "text": "Everyone looks down.", "audio": "audio/en/p09_01_animals.mp3"}]
            (docs / "dialogue_09.json").write_text(json.dumps(data))
            calls = []
            with self.assertRaisesRegex(RuntimeError, "Neplatný dialog"):
                builder.build(docs=docs, mirror=mirror, receipt=receipt, picture=9,
                              synthesizer=lambda *a, **k: calls.append(a))
            self.assertEqual(calls, [])
            self.assertFalse(receipt.exists())

    def test_final_audio_build_preserves_all_three_previous_pictures(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, first_receipt = self.fixture(folder)
            for picture in range(2, 11):
                name = builder.names(picture)[0]
                (docs / name).write_bytes((DOCS / name).read_bytes())
            calls = []
            def synth(text, **kwargs):
                calls.append(text)
                kwargs["budget"].reserve(builder.ssml_parts(text, kwargs["voice"])[1])
                return b"ID3" + text.encode() * 100
            receipts = [first_receipt.with_name(f"receipt_{n}.json") for n in range(1, 11)]
            for picture in range(1, 4):
                builder.build(docs=docs, mirror=mirror, receipt=receipts[picture-1], picture=picture,
                              synthesizer=synth, validator=lambda x: None)
            before = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
            old_receipts = [p.read_bytes() for p in receipts[:3]]
            for picture in (4, 5, 6, 7, 8, 10):
                result = builder.build(docs=docs, mirror=mirror, receipt=receipts[picture-1], picture=picture,
                                       synthesizer=synth, validator=lambda x: None)
                self.assertEqual(result["new_requests"], builder.LINE_COUNTS[picture])
                again = builder.build(docs=docs, mirror=mirror, receipt=receipts[picture-1], picture=picture,
                                      synthesizer=synth, validator=lambda x: None)
                self.assertEqual(again["new_requests"], 0)
            self.assertEqual(len(calls), 67)
            self.assertEqual([p.read_bytes() for p in receipts[:3]], old_receipts)
            for path, content in before.items():
                self.assertEqual((docs / path).read_bytes(), content, str(path))

    def fixture(self, folder):
        root = Path(folder)
        docs, mirror = root / "docs", root / "mirror"
        docs.mkdir()
        (docs / "dialogue.json").write_bytes((DOCS / "dialogue.json").read_bytes())
        return docs, mirror, root / "private/receipt.json"

    def czech_fixture(self, folder):
        docs, mirror, receipt = self.fixture(folder)
        mirror.mkdir()
        for name in [builder.names(n)[0] for n in range(1, 11)] + [czech.INPUT]:
            for root in (docs, mirror):
                (root / name).write_bytes((DOCS / name).read_bytes())
        (docs / "old_english.mp3").write_bytes(b"preserve approved English")
        return docs, mirror, receipt

    def dictionary_fixture(self, folder):
        root = Path(folder)
        docs, mirror = root / "docs/scene06_lake_arrival", root / "mirror"
        docs.mkdir(parents=True); mirror.mkdir()
        for name in dictionary.PRIOR + dictionary.SCRIPTS:
            dest = docs.parent / name; dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((DOCS.parent / name).read_bytes())
        for n in range(1, 11):
            name = builder.names(n)[0]; (docs / name).write_bytes((DOCS / name).read_bytes())
        data = dictionary.vocabulary()
        for item in data["entries"]:
            item["origins"] = {"en": {"type": "azure"}, "cs": {"type": "azure"}}
        for dest in (docs, mirror): (dest / dictionary.INPUT).write_text(json.dumps(data))
        return docs, mirror, root / "private/dictionary_receipt.json"

    def test_dictionary_novelty_and_audio_integrity(self):
        data = dictionary.vocabulary()
        self.assertEqual(len(data["entries"]), 77)
        self.assertFalse({"tree", "come", "good", "benji", "freddie"} & {x["lemma"] for x in data["entries"]})
        self.assertTrue({"cut down", "find out", "woodpecker", "meeting"} <= {x["en"] for x in data["entries"]})
        self.assertEqual(dictionary.check()["audio_assets"], 154)

    def test_dictionary_rejects_prior_word_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.dictionary_fixture(folder)
            data = json.loads((docs / dictionary.INPUT).read_text())
            data["entries"][0].update(en="trees", lemma="tree", forms=["trees"])
            (docs / dictionary.INPUT).write_text(json.dumps(data))
            calls = []
            with self.assertRaisesRegex(RuntimeError, "již bylo"):
                dictionary.build(docs=docs, mirror=mirror, receipt=receipt,
                                 synthesizer=lambda *a, **k: calls.append(a), validator=lambda x: None)
            self.assertEqual(calls, []); self.assertFalse(receipt.exists())

    def test_dictionary_build_budget_reuse_and_prior_data_preservation(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.dictionary_fixture(folder)
            before = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
            calls = []
            def synth(text, **kwargs):
                calls.append(text); kwargs["budget"].reserve(builder.ssml_parts(text, kwargs["voice"])[1])
                return b"ID3" + text.encode() * 100
            with self.assertRaisesRegex(RuntimeError, "rozpočet"):
                dictionary.build(docs=docs, mirror=mirror, receipt=receipt, limit=1, synthesizer=synth, validator=lambda x: None)
            self.assertEqual(calls, [])
            result = dictionary.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            self.assertEqual(result["new_requests"], 154)
            result = dictionary.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            self.assertEqual((result["new_requests"], len(calls)), (0, 154))
            for name, content in before.items(): self.assertEqual((docs / name).read_bytes(), content)

    def test_dictionary_reused_audio_is_bound_to_exact_voice_text_and_hash(self):
        import copy
        row = next(x for x in dictionary.assets(dictionary.vocabulary()) if x["origin"]["type"] == "reused")
        raw = dictionary.reused_bytes(row, DOCS)
        self.assertEqual(builder.digest(raw), row["origin"]["sha256"])
        wrong = copy.deepcopy(row); wrong["text"] += " changed"
        with self.assertRaisesRegex(RuntimeError, "hlas, tempo nebo text"):
            dictionary.reused_bytes(wrong, DOCS)
        wrong = copy.deepcopy(row); wrong["origin"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "otisk"):
            dictionary.reused_bytes(wrong, DOCS)

    def test_czech_transcript_binding_and_audio(self):
        data = czech.translations()
        self.assertEqual(len(data["lines"]), 67)
        self.assertNotIn(9, {row["picture"] for row in data["lines"]})
        payload = json.dumps([(x["english"], x["text"]) for x in data["lines"]], ensure_ascii=False, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), "e85c3255a59d7cdff930dc76eea6b56405dfe393c041523e4d95fb288f05a219")
        self.assertEqual(czech.check()["czech_mp3"], 67)

    def test_czech_build_is_bounded_reusable_and_preserves_english(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.czech_fixture(folder)
            before = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
            calls = []
            def synth(text, **kwargs):
                calls.append(text)
                kwargs["budget"].reserve(czech.english.ssml_parts(text, kwargs["voice"])[1])
                return b"ID3" + text.encode() * 100
            with self.assertRaisesRegex(RuntimeError, "rozpočet"):
                czech.build(docs=docs, mirror=mirror, receipt=receipt, limit=1, synthesizer=synth, validator=lambda x: None)
            self.assertEqual(calls, [])
            result = czech.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            self.assertEqual((result["new_requests"], result["reserved_characters"]), (67, 3977))
            again = czech.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            self.assertEqual((again["new_requests"], len(calls)), (0, 67))
            for name, content in before.items():
                self.assertEqual((docs / name).read_bytes(), content)

    def test_czech_lost_response_is_reserved_and_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.czech_fixture(folder)
            calls = []
            def lost(*args, **kwargs):
                calls.append(args)
                self.assertEqual(json.loads(receipt.read_text())["assets"]["audio/cs/p01_01_benji.mp3"]["state"], "attempted")
                raise RuntimeError("lost")
            with self.assertRaisesRegex(RuntimeError, "lost"):
                czech.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=lost, validator=lambda x: None)
            with self.assertRaisesRegex(RuntimeError, "Nejistý"):
                czech.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=lost, validator=lambda x: None)
            self.assertEqual(len(calls), 1)

    def test_changed_english_binding_blocks_czech_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.czech_fixture(folder)
            data = json.loads((docs / czech.INPUT).read_text())
            data["lines"][0]["english"] = "different text"
            (docs / czech.INPUT).write_text(json.dumps(data))
            calls = []
            with self.assertRaisesRegex(RuntimeError, "neodpovídá"):
                czech.build(docs=docs, mirror=mirror, receipt=receipt,
                            synthesizer=lambda *a, **k: calls.append(a), validator=lambda x: None)
            self.assertEqual(calls, [])
            self.assertFalse(receipt.exists())

    def test_budget_is_checked_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            calls = []
            with self.assertRaisesRegex(RuntimeError, "rozpočet"):
                builder.build(docs=docs, mirror=mirror, receipt=receipt, limit=1,
                              synthesizer=lambda *a, **k: calls.append(a), validator=lambda x: None)
            self.assertEqual(calls, [])

    def test_lost_response_has_durable_claim_and_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            calls = []
            def lost(*args, **kwargs):
                calls.append(args)
                self.assertEqual(json.loads(receipt.read_text())["assets"]["audio/en/01_benji.mp3"]["state"], "attempted")
                raise RuntimeError("lost")
            with self.assertRaisesRegex(RuntimeError, "lost"):
                builder.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=lost, validator=lambda x: None)
            with self.assertRaisesRegex(RuntimeError, "Nejistý"):
                builder.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=lost, validator=lambda x: None)
            self.assertEqual(len(calls), 1)

    def test_complete_outputs_are_reused_without_new_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            calls = []
            def synth(text, **kwargs):
                calls.append(text)
                kwargs["budget"].reserve(builder.ssml_parts(text, kwargs["voice"])[1])
                return b"ID3" + text.encode() * 100
            first = builder.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            second = builder.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            self.assertEqual((first["new_requests"], second["new_requests"], len(calls)), (7, 0, 7))
            (docs / "audio/en/01_benji.mp3").write_bytes(b"changed")
            with self.assertRaisesRegex(RuntimeError, "Změněný"):
                builder.build(docs=docs, mirror=mirror, receipt=receipt, synthesizer=synth, validator=lambda x: None)
            self.assertEqual(len(calls), 7)

    def test_unreceipted_audio_blocks_the_entire_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            docs, mirror, receipt = self.fixture(folder)
            path = docs / "audio/en/07_bunny.mp3"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"preserve")
            calls = []
            with self.assertRaisesRegex(RuntimeError, "bez odpovídající"):
                builder.build(docs=docs, mirror=mirror, receipt=receipt,
                              synthesizer=lambda *a, **k: calls.append(a), validator=lambda x: None)
            self.assertEqual(calls, [])
            self.assertEqual(path.read_bytes(), b"preserve")

    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_czech_player_all_lines_modes_errors_and_live_switching(self):
        result = subprocess.run([shutil.which("node"), str(Path(__file__).with_name("mmtx_scene06_czech_player.js")), str(DOCS)],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_direct_picture_entry_keeps_audio_gate_and_falls_back_safely(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const folder=process.argv[1],source=fs.readFileSync(path.join(folder,'script.js'),'utf8');
const catalog=JSON.parse(fs.readFileSync(path.join(folder,'pictures.json'),'utf8')).pictures;
async function check(hash,expected){
 const nodes=new Map(),audios=[];
 function node(id){
  if(!nodes.has(id)) nodes.set(id,{hidden:false,disabled:true,textContent:'',dataset:{},listeners:{},append(){},replaceChildren(){},
   setAttribute(k,v){this[k]=v;},classList:{remove(){},add(){},toggle(){}},
   addEventListener(k,f){this.listeners[k]=f;},click(){if(!this.disabled)this.listeners.click?.();}});
  return nodes.get(id);
 }
 class Audio{constructor(src){this.src=src;audios.push(this);}play(){return Promise.resolve();}pause(){}}
 const context=vm.createContext({document:{getElementById:node,createElement:()=>node(Symbol())},window:{location:{hash},addEventListener(){}},Audio,
  fetch:async(url)=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(folder,url.split('?')[0]),'utf8'))})});
 vm.runInContext(source,context);await new Promise(resolve=>setImmediate(resolve));
 assert.equal(audios.length,0);assert.equal(node('startButton').disabled,false);
 assert.equal(node('sceneImage').src,catalog[expected-1].image);
 assert.equal(node('nextButton').hidden,true);
 node('startButton').click();assert.equal(node('scene').dataset.picture,String(expected));
 if(expected===9){assert.equal(audios.length,0);assert.equal(node('speechBubble').hidden,true);assert.equal(node('repeatButton').disabled,true);}
 else{
  const data=JSON.parse(fs.readFileSync(path.join(folder,catalog[expected-1].dialogue),'utf8'));
  assert.equal(audios.length,1);assert.equal(audios[0].src,data.lines[0].audio);
  assert.equal(node('nextButton').disabled,true);audios[0].onended();
  node('nextButton').click();assert.equal(audios[1].src,data.lines[1].audio);
 }
}
(async()=>{for(const [hash,target] of [['#picture=4',4],['#picture=10',10],['#picture=9',9],['#picture=999',1],['#picture=foo',1],['',1]])await check(hash,target);})()
.catch(e=>{console.error(e);process.exitCode=1;});
'''
        result = subprocess.run([shutil.which("node"), "-e", script, str(DOCS)],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_player_sequence_errors_repeat_and_late_callbacks(self):
        script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert'), path = require('path');
const nodes = new Map();
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {hidden: false, disabled: true, textContent: '', dataset:{}, append(){},replaceChildren(){},
    setAttribute(name,value){this[name]=value;},
    classList: {remove(){}, add(){}, toggle(){}}, listeners: {},
    addEventListener(type, fn) {this.listeners[type] = fn;},
    click(){if(!this.disabled && this.listeners.click) this.listeners.click();}});
  return nodes.get(id);
}
const audios = [], events = {};
class Audio {
  constructor(src) {this.src = src; audios.push(this);}
  play() {return Promise.resolve();}
  pause() {this.paused = true;}
}
const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const second = JSON.parse(fs.readFileSync(path.join(path.dirname(process.argv[2]),'dialogue_02.json'),'utf8'));
const third = JSON.parse(fs.readFileSync(path.join(path.dirname(process.argv[2]),'dialogue_03.json'),'utf8'));
const catalog = JSON.parse(fs.readFileSync(path.join(path.dirname(process.argv[2]),'pictures.json'),'utf8'));
const context = vm.createContext({document:{getElementById:node,createElement:()=>node(Symbol())}, window:{addEventListener(t,f){events[t]=f;}},
  Audio, fetch:async(url)=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(path.dirname(process.argv[2]),url.split('?')[0]),'utf8'))}), console});
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'),context);
events.pageshow();assert.equal(node('restartButton').hidden,true);
const flush = ()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await flush();
 assert.equal(audios.length,0); assert.equal(node('startButton').disabled,false);
 node('startButton').click(); node('startButton').click();
 assert.equal(audios.length,1); assert.equal(node('speakerName').textContent,'Benji');
 assert.equal(node('nextButton').disabled,true);
 const stale=audios[0].onended; audios[0].onended();
 node('nextButton').click(); assert.equal(node('speakerName').textContent,'Fiona');
 stale(); assert.equal(node('nextButton').disabled,true);
 audios[1].onerror(); assert.equal(node('nextButton').disabled,true);
 assert.equal(node('repeatButton').disabled,false);
 node('repeatButton').click(); assert.equal(audios[2].src,data.lines[1].audio);
 audios[2].onended();
 for(let n=2;n<7;n++) {node('nextButton').click();assert.equal(node('speechText').textContent,data.lines[n].text);audios.at(-1).onended();}
 assert.equal(node('nextButton').hidden,false);assert.equal(node('restartButton').hidden,true);
 assert.equal(node('nextButton').textContent,'Next picture ▶');
 assert.equal(node('scene').dataset.picture,'1');
 node('nextButton').click();
 assert.equal(node('speakerName').textContent,'Ollie');assert.equal(node('lineNumber').textContent,'1 / 10');
 assert.equal(node('sceneImage').src,'ollie_dinner_benji_v2.webp');assert.equal(node('scene').dataset.picture,'2');
 assert.equal(node('nextButton').disabled,true);
 audios.at(-1).onerror();assert.equal(node('nextButton').disabled,true);
 node('repeatButton').click();assert.equal(audios.at(-1).src,second.lines[0].audio);audios.at(-1).onended();
 for(let n=1;n<10;n++){node('nextButton').click();assert.equal(node('speechText').textContent,second.lines[n].text);audios.at(-1).onended();}
 assert.equal(node('nextButton').textContent,'Next picture ▶');
 assert.equal(node('restartButton').hidden,true);
 node('nextButton').click();assert.equal(node('speakerName').textContent,'Dotty');
 assert.equal(node('lineNumber').textContent,'1 / 8');assert.equal(node('sceneImage').src,'freddie_jump_benji_v2.webp');
 audios.at(-1).onended();
 node('nextButton').click();assert.equal(node('speechText').textContent,third.lines[1].text);audios.at(-1).onended();
 node('nextButton').click();assert.equal(node('speechText').textContent,third.lines[2].text);
 assert.equal(node('sceneImage').src,'freddie_jump_benji_v2.webp');
 const jumpEnded=audios.at(-1).onended;jumpEnded();
 assert.equal(node('nextButton').textContent,'Next picture ▶');
 node('nextButton').click();
 assert.equal(node('speechText').textContent,'Why are you practising?');assert.equal(node('lineNumber').textContent,'4 / 8');
 assert.equal(node('sceneImage').src,'freddie_conversation_benji_v2.webp');assert.equal(node('scene').dataset.picture,'3');
 jumpEnded();assert.equal(node('nextButton').disabled,true);
 audios.at(-1).onerror();assert.equal(node('nextButton').disabled,true);
 node('repeatButton').click();assert.equal(node('sceneImage').src,'freddie_conversation_benji_v2.webp');
 assert.equal(audios.at(-1).src,third.lines[3].audio);audios.at(-1).onended();
 for(let n=4;n<8;n++){node('nextButton').click();assert.equal(node('speechText').textContent,third.lines[n].text);assert.equal(node('sceneImage').src,'freddie_conversation_benji_v2.webp');audios.at(-1).onended();}
 let lastEnded;
 for(let p=4;p<=8;p++){
  const picture=catalog.pictures[p-1];
  const rows=JSON.parse(fs.readFileSync(path.join(path.dirname(process.argv[2]),picture.dialogue),'utf8')).lines;
  assert.equal(node('nextButton').textContent,'Next picture ▶');assert.equal(node('restartButton').hidden,true);
  for(let n=0;n<rows.length;n++){
   node('nextButton').click();assert.equal(node('scene').dataset.picture,String(p));
   assert.equal(node('scene').dataset.layout,'below');assert.equal(node('sceneImage').src,picture.image);
   assert.equal(node('speechBubble').hidden,false);assert.equal(node('speakerName').textContent,rows[n].speaker);
   assert.equal(node('speechText').textContent,rows[n].text);assert.equal(audios.at(-1).src,rows[n].audio);
   assert.equal(node('lineNumber').textContent,`${n+1} / ${rows.length}`);
   if(p===6 && n===0){audios.at(-1).onerror();assert.equal(node('nextButton').disabled,true);node('repeatButton').click();assert.equal(audios.at(-1).src,rows[n].audio);}
   lastEnded=audios.at(-1).onended;lastEnded();
  }
 }
 const beforeSilence=audios.length;
 node('nextButton').click();assert.equal(node('sceneImage').src,'silence.webp');
 assert.equal(node('scene').dataset.picture,'9');assert.equal(node('speechBubble').hidden,true);
 assert.equal(node('speechText').textContent,'');assert.equal(node('speakerName').textContent,'');
 assert.equal(node('lineNumber').textContent,'');assert.equal(node('status').textContent,'Silence');
 assert.equal(node('repeatButton').disabled,true);assert.equal(node('nextButton').disabled,false);
 assert.equal(node('nextButton').textContent,'Next picture ▶');assert.equal(node('restartButton').hidden,true);
 lastEnded();events.pagehide();events.pageshow();node('repeatButton').click();
 assert.equal(audios.length,beforeSilence);assert.equal(node('repeatButton').disabled,true);
 assert.equal(node('speechBubble').hidden,true);assert.equal(node('nextButton').disabled,false);
 const finalRows=JSON.parse(fs.readFileSync(path.join(path.dirname(process.argv[2]),'dialogue_10.json'),'utf8')).lines;
 for(let n=0;n<finalRows.length;n++){
  node('nextButton').click();assert.equal(node('scene').dataset.picture,'10');
  assert.equal(node('sceneImage').src,'benji_plan.webp');assert.equal(node('speechBubble').hidden,false);
  assert.equal(node('speechText').textContent,finalRows[n].text);assert.equal(audios.at(-1).src,finalRows[n].audio);
  assert.equal(node('lineNumber').textContent,`${n+1} / 6`);audios.at(-1).onended();
 }
 assert.equal(new Set(audios.map(a=>a.src)).size,67);
 assert.equal(node('nextButton').hidden,true);assert.equal(node('restartButton').hidden,false);
 node('restartButton').disabled=false;node('restartButton').click();
 assert.equal(node('speakerName').textContent,'Benji');
 assert.equal(node('sceneImage').src,'arrival_side_view_benji_v2.webp');
 events.pagehide();assert.equal(audios.at(-1).paused,true);
 events.pageshow();assert.equal(node('repeatButton').disabled,false);
 node('repeatButton').click();assert.equal(audios.at(-1).src,data.lines[0].audio);
 console.log('sequence, error/repeat, stale callback, completion, restart, back/forward restore: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
        result = subprocess.run([shutil.which("node"), "-e", script,
                                 str(DOCS / "script.js"), str(DOCS / "dialogue.json")],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
