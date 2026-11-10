from __future__ import annotations

import importlib.util
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

    def fixture(self, folder):
        root = Path(folder)
        docs, mirror = root / "docs", root / "mirror"
        docs.mkdir()
        (docs / "dialogue.json").write_bytes((DOCS / "dialogue.json").read_bytes())
        return docs, mirror, root / "private/receipt.json"

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
    def test_player_sequence_errors_repeat_and_late_callbacks(self):
        script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const nodes = new Map();
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {hidden: false, disabled: true, textContent: '',
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
const context = vm.createContext({document:{getElementById:node}, window:{addEventListener(t,f){events[t]=f;}},
  Audio, fetch:async()=>({ok:true,json:async()=>data}), console});
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
 assert.equal(node('nextButton').hidden,true);assert.equal(node('restartButton').hidden,false);
 node('restartButton').disabled=false;node('restartButton').click();
 assert.equal(node('speakerName').textContent,'Benji');
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
