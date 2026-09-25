"""M2b: immutable audio ordering, append-only upgrade, privacy and player behavior."""

import copy
import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path

from camino.api import CaminoV1Contract
from camino.domain.audio_layout import decode_audio_layout, ordered_audio_groups
from camino.domain.model import ContractError
from camino.domain.revision_store import RevisionStore, StoreConflict
from scripts.cockpit_quality_gate import node_binary
from tests.camino_viewer_fixture import ViewerFixture, uid


def layout(clip, assets, *, moment=3, session=None, previous=None, gap=None, missing=False):
    return {"clip_id": uid(clip), "moment_id": uid(moment), "session_id": uid(session or clip),
            "previous_clip_id": uid(previous) if previous else None, "gap_before_ms": gap,
            "missing_tail": missing, "parts": [
                {"asset_id": uid(asset), "index": index, "discontinuity_before": False}
                for index, asset in enumerate(assets)]}


class AudioLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = ViewerFixture(Path(self.temp.name))
        # Deliberately opposite UUID/upload order to recorded playback order.
        self.assets = [self.f.upload(n, "audio", b"synthetic-audio") for n in (30, 32, 31)]

    def test_strict_fields_gaps_and_segment_discontinuities(self):
        good = layout(50, [32, 30])
        self.assertEqual(decode_audio_layout(good), good)
        bad_values = []
        for changes in ({"unexpected": True}, {"gap_before_ms": 0}, {"missing_tail": 1},
                        {"clip_id": "bad"}, {"parts": []}, {"previous_clip_id": uid(50)}):
            bad_values.append({**good, **changes})
        for gap in (-1, True, 0.5, 9_007_199_254_740_992):
            bad_values.append(layout(51, [31], session=50, previous=50, gap=gap))
        duplicate = copy.deepcopy(good)
        duplicate["parts"][1]["asset_id"] = uid(32)
        bad_values.append(duplicate)
        skipped = copy.deepcopy(good)
        skipped["parts"][1]["index"] = 3
        bad_values.append(skipped)
        for value in bad_values:
            with self.subTest(value=value), self.assertRaises(ContractError):
                decode_audio_layout(value)
        skipped["parts"][1]["discontinuity_before"] = True
        self.assertEqual(decode_audio_layout(skipped), skipped)

    def test_recorded_predecessors_and_indices_override_arrival_order(self):
        first = layout(50, [32, 30])
        second = layout(51, [31], session=50, previous=50, gap=12_345)
        self.f.send("create_audio_layout", second)
        self.f.send("create_audio_layout", first)
        snapshot = self.f.store.viewer_snapshot(self.f.trip.id)["moments"][0]
        groups, used = ordered_audio_groups(snapshot["assets"], snapshot["audio_layouts"])
        clips = groups[0]["clips"]
        self.assertEqual([item["clip_id"] for item in clips], [uid(50), uid(51)])
        self.assertTrue(all(item["order_known"] for item in clips))
        self.assertEqual([part["asset_id"] for part in clips[0]["parts"]], [uid(32), uid(30)])
        self.assertEqual(clips[1]["gap_before_ms"], 12_345)
        self.assertEqual(used, {uid(30), uid(31), uid(32)})
        partial, _ = ordered_audio_groups(self.assets, [second])
        self.assertFalse(partial[0]["clips"][0]["order_known"])
        third = layout(52, [30], session=50, previous=51, gap=0)
        partial, _ = ordered_audio_groups(self.assets, [third, second])
        self.assertEqual([clip["clip_id"] for clip in partial[0]["clips"]], [uid(51), uid(52)])
        self.assertFalse(partial[0]["clips"][0]["order_known"])

    def test_schema_one_upgrade_and_retry_preserve_old_rows_and_media(self):
        with self.f.store._connection() as c:
            c.execute("DROP TABLE audio_layouts")  # synthetic schema-1 fixture only
            c.execute("PRAGMA user_version=1")
            before = list(c.execute("SELECT * FROM assets"))
            before = [tuple(row) for row in before]
        reopened = RevisionStore(self.f.store.path)
        self.f.store = reopened
        before_sources = [self.f.media.verified_source(a["id"]).read_bytes() for a in self.assets]
        first = layout(50, [32, 30, 31])
        self.f.send("create_audio_layout", first)
        self.f.send("create_audio_layout", first)
        again = RevisionStore(reopened.path)
        with again._connection() as c:
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual([tuple(row) for row in c.execute("SELECT * FROM assets")], before)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM audio_layouts").fetchone()[0], 1)
            self.assertEqual(c.execute("SELECT revision FROM moments WHERE id=?", (uid(3),)).fetchone()[0], 1)
        self.assertEqual(before_sources, [self.f.media.verified_source(a["id"]).read_bytes() for a in self.assets])
        self.assertIn("audio_layout_v1", again.state()["features"])

    def test_transaction_rolls_back_and_conflicting_identity_blocks_exports(self):
        with self.f.store._connection() as c:
            c.execute("CREATE TRIGGER fail_layout BEFORE INSERT ON accepted_operations WHEN NEW.kind='create_audio_layout' BEGIN SELECT RAISE(ABORT,'synthetic'); END")
        with self.assertRaises(sqlite3.DatabaseError):
            self.f.send("create_audio_layout", layout(50, [30]))
        with self.f.store._connection() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM audio_layouts").fetchone()[0], 0)
            c.execute("DROP TRIGGER fail_layout")
        self.f.sequence -= 1
        self.f.send("create_audio_layout", layout(50, [30]))
        with self.assertRaises(StoreConflict):
            self.f.send("create_audio_layout", layout(50, [31]))
        self.assertTrue(self.f.store.state()["exports_blocked"])
        self.assertEqual(self.f.store.viewer_snapshot(self.f.trip.id)["moments"], [])

    def test_cross_moment_sources_branching_and_cycles_are_rejected(self):
        self.f.upload(40, "audio", b"private", private=True)
        bad = layout(50, [40])
        with self.assertRaises(ContractError):
            self.f.send("create_audio_layout", bad)
        self.f.sequence -= 1
        self.f.send("create_audio_layout", layout(51, [30], session=50, previous=52))
        for value in (layout(52, [31], session=50, previous=51),
                      layout(53, [31], session=50, previous=52),
                      layout(52, [31], session=60, previous=61)):
            with self.assertRaises(ContractError):
                self.f.send("create_audio_layout", value)
            self.f.sequence -= 1

    def test_private_layouts_never_enter_projection_and_lock_removes_public(self):
        self.f.upload(40, "audio", b"private", private=True)
        self.f.send("create_audio_layout", layout(60, [40], moment=4))
        self.f.send("create_audio_layout", layout(50, [30, 32, 31]))
        snapshot = self.f.store.viewer_snapshot(self.f.trip.id)
        self.assertNotIn(uid(60), json.dumps(snapshot))
        self.assertNotIn(uid(40), json.dumps(snapshot))
        self.f.lock()
        self.assertEqual(self.f.store.viewer_snapshot(self.f.trip.id)["moments"], [])

    def test_owner_api_accepts_declared_extension_and_denies_unauthorized(self):
        api = CaminoV1Contract(self.f.store, authenticate=lambda value: value == "Bearer synthetic")
        state = api.handle("GET", "/api/v1/state", authorization="Bearer synthetic")
        self.assertIn("audio_layout_v1", state.body["features"])
        body = {"contract_version": 1, "epoch": state.body["epoch"], "operation_id": uid(900),
                "device_id": uid(90), "device_sequence": self.f.sequence + 1,
                "kind": "create_audio_layout", "expected_revision": None, "payload": layout(50, [32, 30, 31])}
        raw = json.dumps(body).encode()
        self.assertEqual(api.handle("POST", "/api/v1/operations", authorization="", body=raw, content_type="application/json").status, 401)
        accepted = api.handle("POST", "/api/v1/operations", authorization="Bearer synthetic", body=raw, content_type="application/json")
        self.assertEqual(accepted.status, 200, accepted.body)

    def test_player_advances_only_explicit_neighbor_and_handles_blocked_autoplay(self):
        javascript = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function player(id, next) {return {id, dataset: {next}, events: {}, played: 0, paused: 0,
  addEventListener(event, fn) {this.events[event] = fn;},
  pause() {this.paused++;}, focus() {this.focused = true;},
  async play() {this.played++; if(this.blocked) throw Error('synthetic'); this.events.play();}};}
const a=player('a','b'), b=player('b'), c=player('c'), d=player('d','not-a-player');
const status={}; const players=[a,b,c,d];
const document={querySelectorAll(){return players;},getElementById(id){return id==='audioPlaybackStatus'?status:players.find(p=>p.id===id);}};
vm.runInNewContext(fs.readFileSync('camino/server/viewer_player.js','utf8'), {document});
(async()=>{
 b.currentTime=42; await a.events.ended(); assert.equal(b.played,1); assert.equal(b.currentTime,0); assert.equal(c.played,0);
 await b.events.ended(); assert.equal(c.played,0); // real pause/discontinuity, no next link
 await d.events.ended(); assert.equal(c.played,0);
 b.blocked=true; await a.events.ended(); assert.equal(b.focused,true); assert.ok(status.textContent);
 await c.play(); assert.ok(a.paused>0); assert.ok(b.paused>0);
})().catch(error=>{console.error(error);process.exitCode=1;});
'''
        run = subprocess.run([node_binary(), "-"], input=javascript, text=True, capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
