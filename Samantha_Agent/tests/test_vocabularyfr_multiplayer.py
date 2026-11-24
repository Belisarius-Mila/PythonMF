"""Private rooms tested against real public FR metadata and isolated databases."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import random
import sqlite3
import subprocess
from tempfile import TemporaryDirectory
import threading
import unittest

from app.vocabulary_fr_multiplayer import Catalog, GameError, GameServer, Rooms, API, OFFLINE_SECONDS
from scripts.cockpit_quality_gate import node_binary


class Clock:
    def __init__(self):
        self.now = 1800000000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class RoomFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = Catalog()
        cls.uids = []
        for uid in cls.catalog.items:
            if all(cls.catalog.compatible(uid, prior) for prior in cls.uids):
                cls.uids.append(uid)
            if len(cls.uids) == 12:
                break
        assert len(cls.uids) == 12

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clock = Clock()
        self.path = Path(self.tmp.name) / "rooms.sqlite3"
        self.rooms = Rooms(self.path, self.catalog, clock=self.clock, shuffle=random.Random(8).shuffle)
        self.host, self.guest, self.invite = "a" * 64, "b" * 64, "c" * 64
        self.count = 0
        self.payload = {"name": "Jana", "uids": self.uids, "playerToken": self.host, "invite": self.invite, "requestId": "d" * 64}
        self.initial = self.rooms.create(self.payload)
        self.room = self.initial["room"]

    def action(self, action, token=None, **values):
        self.count += 1
        room = self.raw()
        return self.rooms.act(self.room, token or self.host, action, {"requestId": f"{self.count:064x}", "expectedRound": room["round"], "expectedStage": room["stage"], **values})

    def start(self):
        self.rooms.join(self.room, {"name": "Míla", "invite": self.invite, "playerToken": self.guest})
        return self.action("start")

    def raw(self):
        with sqlite3.connect(self.path) as conn:
            return json.loads(conn.execute("SELECT body FROM rooms WHERE id=?", (self.room,)).fetchone()[0])

    def heard(self):
        stage = self.action("sync")["stage"]
        self.clock.advance(2)
        self.action("heard", stage=stage)
        return self.action("heard", self.guest, stage=stage)

    def pair(self, a, b, token=None):
        self.action("flip", token, index=a)
        self.heard()
        self.action("flip", token, index=b)
        state = self.heard()
        self.assertEqual(state["phase"], "compare")
        self.clock.advance(1)
        state = self.action("sync")
        if state["phase"] == "reward":
            self.heard()
            state = self.action("sync")
        return state


class RoomsTests(RoomFixture):
    def test_hidden_deck_and_credentials_are_not_exposed_and_tokens_are_hashed_on_disk(self):
        serialized = json.dumps(self.initial)
        for secret in [self.host, self.invite, *self.uids]:
            self.assertNotIn(secret, serialized)
        raw = self.path.read_bytes()
        self.assertNotIn(self.host.encode(), raw)
        self.assertNotIn(self.invite.encode(), raw)
        self.assertEqual(len(self.initial["cards"]), 24)
        self.assertTrue(all(set(card) == {"index", "state"} for card in self.initial["cards"]))

    def test_create_and_join_are_idempotent_but_cannot_change_payload_or_take_other_seat(self):
        self.assertEqual(self.rooms.create(self.payload)["room"], self.room)
        with self.assertRaises(GameError):
            self.rooms.create({**self.payload, "name": "Eva"})
        joined = self.rooms.join(self.room, {"name": "Míla", "invite": self.invite, "playerToken": self.guest})
        self.assertEqual(joined["you"], 1)
        self.assertEqual(self.rooms.join(self.room, {"name": "Míla", "invite": self.invite, "playerToken": self.guest})["you"], 1)
        for invite, token in [("e" * 64, "f" * 64), (self.invite, "f" * 64), (self.invite, self.host)]:
            with self.assertRaises(GameError):
                self.rooms.join(self.room, {"name": "Cizí", "invite": invite, "playerToken": token})

    def test_only_host_can_start_when_both_players_are_present(self):
        with self.assertRaises(GameError):
            self.action("start")
        self.rooms.join(self.room, {"name": "Míla", "invite": self.invite, "playerToken": self.guest})
        with self.assertRaises(GameError):
            self.action("start", self.guest)
        self.assertEqual(self.action("start")["phase"], "choose")

    def test_flip_waits_for_both_audio_completions_and_at_least_two_seconds(self):
        self.start()
        first = self.action("flip", index=21)
        self.assertEqual(first["focus"], 21)
        self.assertEqual(sum(c["state"] == "open" for c in first["cards"]), 1)
        self.action("heard", stage=first["stage"])
        self.assertEqual(self.action("heard", self.guest, stage=first["stage"])["phase"], "reveal")
        self.clock.advance(2)
        self.assertEqual(self.action("sync")["phase"], "choose")
        second = self.action("flip", index=2)
        self.assertEqual(second["focus"], 2)
        self.clock.advance(20)
        self.action("sync", self.guest)
        self.assertEqual(self.action("heard", stage=second["stage"])["phase"], "reveal")

    def test_other_player_rapid_click_duplicate_card_and_wrong_types_are_rejected(self):
        self.start()
        for index, token in [(0, self.guest), (True, self.host), (-1, self.host), (24, self.host)]:
            with self.assertRaises(GameError):
                self.action("flip", token, index=index)
        self.action("flip", index=0)
        with self.assertRaises(GameError):
            self.action("flip", index=1)
        self.heard()
        with self.assertRaises(GameError):
            self.action("flip", index=0)

    def test_success_awards_once_repeats_same_player_and_reward_precedes_next_turn(self):
        self.start()
        deck = self.raw()["deck"]
        a, b = [i for i, uid in enumerate(deck) if uid == deck[0]]
        self.action("flip", index=a)
        self.heard()
        self.action("flip", index=b)
        self.heard()
        self.clock.advance(1)
        state = self.action("sync")
        self.assertEqual((state["phase"], state["active"], state["turns"]), ("reward", 0, 1))
        self.assertEqual(state["owners"], {deck[0]: 0})
        self.assertEqual(sum(c["state"] == "matched" for c in state["cards"]), 2)
        self.clock.advance(10)
        self.assertEqual(self.action("sync")["phase"], "reward")
        state = self.heard()
        self.assertEqual((state["phase"], state["active"]), ("choose", 0))
        with self.assertRaises(GameError):
            self.action("flip", index=a)

    def test_mismatch_changes_player_and_hides_both_identities(self):
        self.start()
        deck = self.raw()["deck"]
        state = self.pair(0, next(i for i, uid in enumerate(deck) if uid != deck[0]))
        self.assertEqual((state["active"], state["turns"], state["phase"]), (1, 1, "choose"))
        self.assertTrue(all(c["state"] == "hidden" and "uid" not in c for c in state["cards"]))

    def test_exact_retry_cannot_repeat_flip_or_reuse_id_for_different_action(self):
        self.start()
        payload = {"requestId": "e" * 64, "index": 4, "expectedRound": 1, "expectedStage": 0}
        first = self.rooms.act(self.room, self.host, "flip", payload)
        self.assertEqual(self.rooms.act(self.room, self.host, "flip", payload)["stage"], first["stage"])
        with self.assertRaises(GameError):
            self.rooms.act(self.room, self.host, "flip", {**payload, "index": 5})

    def test_concurrent_duplicate_flip_and_duplicate_ack_remain_single_actions(self):
        self.start()
        payload = {"requestId": "e" * 64, "index": 4, "expectedRound": 1, "expectedStage": 0}
        with ThreadPoolExecutor(max_workers=2) as pool:
            states = list(pool.map(lambda _: self.rooms.act(self.room, self.host, "flip", payload), range(2)))
        self.assertEqual(states[0]["stage"], states[1]["stage"])
        self.assertEqual(self.raw()["open"], [4])
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: self.rooms.act(self.room, self.host, "heard", {"requestId": "f" * 64, "stage": states[0]["stage"], "expectedRound": 1, "expectedStage": states[0]["stage"]}), range(2)))
        self.assertEqual(self.raw()["acks"], [0])

    def test_disconnect_freezes_timers_and_resumption_requires_both_hear_again(self):
        self.start()
        self.action("flip", index=0)
        self.action("leave", self.guest)
        self.assertTrue(self.action("sync")["paused"])
        self.clock.advance(120)
        self.action("sync")
        with self.assertRaises(GameError):
            self.action("flip", index=1)
        state = self.action("ready", self.guest)
        self.assertFalse(state["paused"])
        self.assertEqual(state["phase"], "reveal")
        self.assertEqual(self.heard()["phase"], "choose")

    def test_hard_disconnect_pauses_and_changed_presence_updates_waiting_room(self):
        self.start()
        self.clock.advance(OFFLINE_SECONDS + 1)
        self.assertTrue(self.action("sync")["paused"])
        self.assertFalse(self.action("sync")["players"][1]["connected"])
        self.assertFalse(self.action("sync", self.guest)["paused"])

    def test_restart_preserves_private_access_cards_scores_and_in_progress_reward(self):
        self.start()
        deck = self.raw()["deck"]
        a, b = [i for i, uid in enumerate(deck) if uid == deck[0]]
        self.action("flip", index=a)
        self.heard()
        self.action("flip", index=b)
        self.heard()
        self.clock.advance(1)
        old = self.action("sync")
        self.rooms = Rooms(self.path, self.catalog, clock=self.clock)
        state = self.action("sync")
        self.assertEqual(state, old)
        self.assertEqual(state["phase"], "reward")
        self.heard()
        self.assertEqual(len(self.action("sync")["owners"]), 1)

    def test_all_twelve_pairs_final_reward_then_result_and_host_only_rematch(self):
        self.start()
        deck = self.raw()["deck"]
        for uid in self.uids:
            a, b = [i for i, candidate in enumerate(deck) if candidate == uid]
            self.pair(a, b)
        state = self.action("sync")
        self.assertEqual((state["phase"], len(state["owners"]), state["turns"]), ("finished", 12, 12))
        with self.assertRaises(GameError):
            self.action("rematch", self.guest)
        state = self.action("rematch")
        self.assertEqual((state["round"], state["owners"], state["turns"], state["phase"]), (2, {}, 0, "choose"))
        self.assertTrue(all(c["state"] == "hidden" for c in state["cards"]))
        self.assertEqual(set(self.raw()["deck"]), set(deck))

    def test_new_words_rematch_keeps_room_access_and_survives_restart_without_repeating(self):
        self.start()
        deck = self.raw()["deck"]
        for uid in self.uids:
            self.pair(*[i for i, candidate in enumerate(deck) if candidate == uid])
        before = self.raw()
        chosen = []
        for uid in self.catalog.items:
            if uid not in self.uids and all(self.catalog.compatible(uid, other) for other in chosen):
                chosen.append(uid)
            if len(chosen) == 12:
                break
        payload = {"requestId": "e" * 64, "expectedRound": before["round"], "expectedStage": before["stage"], "uids": chosen}
        for token, values in [(self.guest, payload), (self.host, {**payload, "uids": chosen[:11]}),
                              (self.host, {**payload, "uids": [chosen[0]] * 12}),
                              (self.host, {**payload, "uids": chosen[:-1] + ["unknown"]})]:
            with self.assertRaises(GameError):
                self.rooms.act(self.room, token, "rematch", values)
            self.assertEqual(self.raw(), before)
        state = self.rooms.act(self.room, self.host, "rematch", payload)
        self.assertEqual((state["room"], state["round"], state["phase"], state["owners"], state["turns"], state["active"]),
                         (self.room, 2, "choose", {}, 0, 0))
        after = self.raw()
        self.assertEqual(set(after["deck"]), set(chosen))
        self.assertTrue(set(after["deck"]).isdisjoint(deck))
        self.assertEqual(after["players"], before["players"])
        self.assertEqual(after["inviteHash"], before["inviteHash"])
        self.assertTrue(all(card["state"] == "hidden" and "uid" not in card for card in state["cards"]))
        self.rooms = Rooms(self.path, self.catalog, clock=self.clock)
        self.assertEqual(self.rooms.act(self.room, self.host, "rematch", payload), state)
        self.assertEqual(self.raw()["deck"], after["deck"])
        self.assertEqual(self.action("sync", self.guest)["round"], 2)
        with self.assertRaises(GameError):
            self.rooms.act(self.room, self.host, "rematch", {**payload, "requestId": "f" * 64})
        with self.assertRaises(GameError):
            self.action("rematch", uids=self.uids)
        self.assertEqual(self.raw()["deck"], after["deck"])

    def test_expiry_catalog_drift_authentication_capacity_and_bad_selection(self):
        for bad in ["x", "e" * 64]:
            with self.assertRaises(GameError):
                self.rooms.act(self.room, bad, "sync")
        for uids in [self.uids[:11], self.uids + [self.uids[0]], [self.uids[0]] * 12, self.uids[:-1] + ["ven-0001"]]:
            with self.assertRaises(GameError):
                self.rooms.create({**self.payload, "uids": uids})
        limited = Rooms(self.path, self.catalog, clock=self.clock, capacity=1)
        with self.assertRaises(GameError):
            limited.create({**self.payload, "requestId": "f" * 64})
        self.clock.advance(7201)
        with self.assertRaises(GameError) as caught:
            self.action("sync")
        self.assertEqual(caught.exception.status, 410)

    def test_stale_flip_and_wrong_audio_stage_cannot_mutate_a_new_phase(self):
        self.start()
        self.action("flip", index=0)
        self.heard()
        before = self.raw()
        with self.assertRaises(GameError):
            self.rooms.act(self.room, self.host, "flip", {"index": 1, "requestId": "f" * 64, "expectedRound": 1, "expectedStage": 0})
        self.assertEqual(self.raw(), before)
        self.action("flip", index=1)
        with self.assertRaises(GameError):
            self.action("heard", stage=1)
        with self.assertRaises(GameError):
            self.action("heard", stage=True)

    def test_different_concurrent_flips_accept_only_one_and_catalog_changes_stop_resume(self):
        self.start()
        def flip(index):
            try:
                return self.rooms.act(self.room, self.host, "flip", {"index": index, "requestId": str(index + 5) * 64, "expectedRound": 1, "expectedStage": 0})
            except GameError as error:
                return error.status
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(flip, [0, 1]))
        self.assertEqual(sum(isinstance(value, dict) for value in outcomes), 1)
        self.assertEqual(len(self.raw()["open"]), 1)
        from unittest.mock import patch
        with patch.object(self.catalog, "revision", "different"):
            with self.assertRaises(GameError) as caught:
                self.action("sync")
            self.assertEqual(caught.exception.status, 409)

    def test_only_public_media_and_client_compatible_selections_are_accepted(self):
        code = "const fs=require('node:fs'),m=require('../docs/vocabulary-fr/memory.js');const d=JSON.parse(fs.readFileSync('../docs/data/vocabulary-fr-v2.json')),a=JSON.parse(fs.readFileSync('../docs/data/vocabulary-fr-audio.json')),q=JSON.parse(fs.readFileSync('../docs/data/vocabulary-fr-quiz.json'));console.log(JSON.stringify(m.choose(d.items,a,q,()=>.5).map(i=>i.uid)));"
        selected = json.loads(subprocess.check_output([node_binary(), "-e", code], cwd=Path(__file__).resolve().parents[1], text=True))
        self.assertEqual(self.catalog.selection(selected), selected)
        self.assertFalse(self.catalog._asset("assets/vocabulary-fr-v2/../../.env"))
        self.assertFalse(self.catalog._asset("assets/vocabulary-fr-v2//image.webp"))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)


class HTTPTests(RoomFixture):
    def test_http_two_clients_and_isolation(self):
        server = GameServer(("127.0.0.1", 0), self.rooms)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        def request(path, body=None, token=None, origin=None, headers=None, method=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            values = {"Origin": origin or server.origin, "Content-Type": "application/json", **(headers or {})}
            if token:
                values["Authorization"] = "Bearer " + token
            conn.request(method or ("POST" if body is not None else "GET"), path, None if body is None else json.dumps(body), values)
            response = conn.getresponse()
            data = response.read()
            status, returned = response.status, dict(response.getheaders())
            conn.close()
            return status, data, returned

        status, raw, _ = request(API + "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["catalog"], self.catalog.revision)
        status, raw, _ = request(API + "/" + self.room + "/join", {"name": "Míla", "invite": self.invite, "playerToken": self.guest})
        self.assertEqual((status, json.loads(raw)["you"]), (200, 1))
        status, raw, _ = request(API + "/" + self.room + "/start", {"requestId": "e" * 64, "expectedRound": 1, "expectedStage": 0}, self.host)
        self.assertEqual((status, json.loads(raw)["phase"]), (200, "choose"))
        status, raw, _ = request(API + "/" + self.room + "/flip", {"requestId": "f" * 64, "index": 3, "expectedRound": 1, "expectedStage": 0}, self.host)
        self.assertEqual(status, 200)
        state = json.loads(raw)
        self.assertEqual(state["focus"], 3)
        status, raw, headers = request(API + "/" + self.room + "/sync", {}, self.guest)
        self.assertEqual(json.loads(raw)["cards"], state["cards"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(request(API + "/" + self.room + "/sync", {}, "0" * 64)[0], 403)
        self.assertEqual(request(API, self.payload, origin="https://untrusted.example")[0], 403)
        self.assertEqual(request(API, self.payload, headers={"Host": "untrusted.example"})[0], 403)
        self.assertEqual(request(API, self.payload, headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(request(API, {"padding": "x" * 33000})[0], 413)
        for path in ["/api/server/health", "/.env", "/data/private/test", "/vocabulary-it/", "/vocabulary-fr/%2e%2e/%2e%2e/AGENTS.md"]:
            self.assertEqual(request(path)[0], 404, path)
        for path in ["/vocabulary-fr/", "/vocabulary-fr/online.html", "/vocabulary-fr/online.js", "/data/vocabulary-fr-v2.json"]:
            self.assertEqual(request(path)[0], 200, path)
        for path in (self.catalog.items[self.uids[0]][key] for key in ("image", "thumbnail", "audio")):
            status, body, _ = request("/" + path)
            self.assertEqual(status, 200, path)
            self.assertEqual(body, (self.catalog.docs / path).read_bytes())
        sound = self.catalog.items[self.uids[0]]["audio"]
        full = (self.catalog.docs / sound).read_bytes()
        for header, expected, bounds in [("bytes=0-1", full[:2], (0, 1)),
                                         ("bytes=-5", full[-5:], (len(full)-5, len(full)-1)),
                                         ("bytes=2-", full[2:], (2, len(full)-1))]:
            status, body, headers = request("/"+sound, headers={"Range": header})
            self.assertEqual((status, body), (206, expected))
            self.assertEqual(headers["Content-Range"], f"bytes {bounds[0]}-{bounds[1]}/{len(full)}")
            self.assertEqual(int(headers["Content-Length"]), len(expected))
        for header in [f"bytes={len(full)}-", "bytes=-0", "bytes=4-1", "bytes=0-1,4-5", "bytes=--", "bytes="+"9"*500+"-"]:
            status, body, headers = request("/"+sound, headers={"Range": header})
            self.assertEqual((status, body), (416, b""))
            self.assertEqual(headers["Content-Range"], f"bytes */{len(full)}")
        status, body, headers = request("/"+sound, method="HEAD", headers={"Range":"bytes=0-1"})
        self.assertEqual((status, body, headers["Content-Length"]), (206, b"", "2"))
        with self.assertRaises(ValueError):
            GameServer(("127.0.0.1", 0), self.rooms, "http://public.example")


class ClientTests(unittest.TestCase):
    def test_real_online_client_with_two_independent_browser_fixtures(self):
        result = subprocess.run([node_binary(), "--test", "tests/test_vocabularyfr_online.js"], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("fail 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
