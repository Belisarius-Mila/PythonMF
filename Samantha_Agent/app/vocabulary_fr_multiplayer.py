"""Isolated, same-origin French pairs service. No Cockpit routes or accounts.

Run locally: python -m app.vocabulary_fr_multiplayer --port 8791
Public operation requires a separately approved HTTPS reverse proxy and origin.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
import unicodedata
from urllib.parse import unquote, urlsplit

PROTOCOL = 1
PAIR_COUNT = 12
OFFLINE_SECONDS = 15
ROOM_SECONDS = 24 * 3600
IDLE_SECONDS = 2 * 3600
MAX_BODY = 32768
TOKEN = re.compile(r"[a-f0-9]{64}\Z")
REQUEST = re.compile(r"[a-f0-9-]{16,64}\Z")
ROOM = re.compile(r"[a-f0-9]{24}\Z")
DOCS = Path(__file__).resolve().parents[2] / "docs"
API = "/api/vocabulary-fr/rooms"


class GameError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _token(value: object) -> str:
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise GameError("Neplatný přístup do partie.", 401)
    return value


def _request(value: object) -> str:
    if not isinstance(value, str) or not REQUEST.fullmatch(value):
        raise GameError("Chybí identita požadavku.")
    return value


def _name(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 12 or any(ord(c) < 32 for c in value):
        raise GameError("Jméno musí mít 1–12 znaků.")
    return value.strip()


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode().lower())


def _meanings(value: str) -> set[str]:
    return {_norm(re.sub(r"\([^)]*\)", "", part)) for part in re.split(r"[,;/]", value)} - {""}


class Catalog:
    """Validate public FR identities/media and the existing pairs exclusions."""

    def __init__(self, docs: Path = DOCS):
        self.docs = docs.resolve()
        blobs = [(self.docs / "data" / name).read_bytes() for name in (
            "vocabulary-fr-v2.json", "vocabulary-fr-audio.json", "vocabulary-fr-quiz.json")]
        data, audio, quiz = map(json.loads, blobs)
        if (data.get("schemaVersion") != 2 or data.get("language") != "fr" or audio.get("schemaVersion") != 1
                or audio.get("language") != "fr" or audio.get("kind") != "words" or quiz.get("schemaVersion") != 1
                or quiz.get("language") != "fr" or quiz.get("kind") != "spelling-pictures"):
            raise ValueError("Invalid FR catalog")
        self.revision = hashlib.sha256(b"\0".join(blobs)).hexdigest()
        self.items = {}
        self.metadata = quiz["entries"]
        for item in data["items"]:
            uid = item["uid"]
            entry = self.metadata.get(uid, {})
            sound = audio["items"].get(uid, {})
            if item.get("active") is False or item.get("imageMissing"):
                continue
            if any(entry.get(k) != item.get(k) for k in ("uid", "fr", "cz", "image", "thumbnail")):
                continue
            pieces = entry.get("pieces")
            if not isinstance(pieces, list) or not 1 <= len(pieces) <= 120 or any(not isinstance(v, str) or not v for v in pieces) or "".join(pieces) != item["fr"]:
                continue
            if entry.get("format") not in ("colors", "objects") or not isinstance(entry.get("conflicts"), list):
                continue
            if not ((entry.get("reviewed") is True and entry.get("displayMode") == "syllables") or
                    (entry.get("reviewed") is False and entry.get("displayMode") == "whole-word" and len(pieces) == 1)):
                continue
            if sound.get("uid") != uid or sound.get("sourceFr") != item["fr"] or sound.get("sourceCz") != item["cz"] or not sound.get("fr"):
                continue
            media = [item.get("image"), item.get("thumbnail"), sound["fr"]]
            if any(not self._asset(path) for path in media):
                continue
            self.items[uid] = {**item, "audio": sound["fr"]}

    def _asset(self, path: object) -> bool:
        if not isinstance(path, str) or not path.startswith(("assets/vocabulary-fr-v2/", "assets/vocabulary-fr-audio/")) or ".." in Path(path).parts or "//" in path:
            return False
        target = (self.docs / path).resolve()
        return target.is_relative_to(self.docs) and target.is_file()

    def compatible(self, a: str, b: str) -> bool:
        x, y = self.items[a], self.items[b]
        return (a != b and _norm(x["fr"]) != _norm(y["fr"]) and x["image"].lower() != y["image"].lower()
                and Path(x["thumbnail"]).name != Path(y["thumbnail"]).name and x["audio"] != y["audio"]
                and not (_meanings(x["cz"]) & _meanings(y["cz"]))
                and not (set(self.metadata[a]["conflicts"]) & set(self.metadata[b]["conflicts"]))
                and not any(isinstance(v, dict) and v.get("uid") == b for v in x.get("related", []))
                and not any(isinstance(v, dict) and v.get("uid") == a for v in y.get("related", [])))

    def selection(self, uids: object) -> list[str]:
        if not isinstance(uids, list) or len(uids) != PAIR_COUNT or any(not isinstance(v, str) for v in uids) or len(set(uids)) != PAIR_COUNT:
            raise GameError("Vyber 12 různých slovíček.")
        if any(uid not in self.items for uid in uids) or any(not self.compatible(a, b) for n, a in enumerate(uids) for b in uids[n + 1:]):
            raise GameError("Výběr nemá 12 dostatečně odlišných obrázků s francouzským zvukem.")
        return list(uids)


class Rooms:
    def __init__(self, database: Path, catalog: Catalog, *, clock=time.time, shuffle=None, capacity=64):
        self.database, self.catalog, self.clock = Path(database), catalog, clock
        self.shuffle = shuffle or secrets.SystemRandom().shuffle
        self.capacity = capacity
        self.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            descriptor = os.open(self.database, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(descriptor)
        with self._db() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, request TEXT UNIQUE, body TEXT NOT NULL)")

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.database, timeout=10)
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _save(self, conn, room):
        conn.execute("UPDATE rooms SET body=? WHERE id=?", (json.dumps(room, ensure_ascii=False), room["id"]))

    def _load(self, conn, room_id):
        if not isinstance(room_id, str) or not ROOM.fullmatch(room_id):
            raise GameError("Partie nebyla nalezena.", 404)
        row = conn.execute("SELECT body FROM rooms WHERE id=?", (room_id,)).fetchone()
        if not row:
            raise GameError("Partie nebyla nalezena.", 404)
        room = json.loads(row[0])
        now = self.clock()
        if now > room["expires"] or now - room["touched"] > IDLE_SECONDS:
            raise GameError("Platnost partie skončila. Založ novou.", 410)
        if room["catalog"] != self.catalog.revision:
            raise GameError("Slovník se změnil. Založ novou partii.", 409)
        return room

    def create(self, payload: dict) -> dict:
        request_id = _request(payload.get("requestId"))
        token, invite = _token(payload.get("playerToken")), _token(payload.get("invite"))
        name, uids = _name(payload.get("name")), self.catalog.selection(payload.get("uids"))
        fingerprint = _hash(json.dumps([name, uids, _hash(token), _hash(invite)]))
        now = self.clock()
        with self._db() as conn:
            prior = conn.execute("SELECT id,body FROM rooms WHERE request=?", (request_id,)).fetchone()
            if prior:
                room = self._load(conn, prior[0])
                if room["createHash"] != fingerprint:
                    raise GameError("Identita požadavku už patří jinému zadání.", 409)
                return self._snapshot(room, 0)
            rows = conn.execute("SELECT body FROM rooms").fetchall()
            if sum(json.loads(row[0])["expires"] > now and now - json.loads(row[0])["touched"] < IDLE_SECONDS for row in rows) >= self.capacity:
                raise GameError("Herní místnosti jsou právě obsazené. Zkus to později.", 429)
            deck = uids * 2
            self.shuffle(deck)
            room = {"id": secrets.token_hex(12), "createHash": fingerprint, "catalog": self.catalog.revision,
                    "inviteHash": _hash(invite), "created": now, "expires": now + ROOM_SECONDS, "touched": now,
                    "players": [{"name": name, "tokenHash": _hash(token), "seen": now, "ready": True}, None],
                    "deck": deck, "owners": {}, "active": 0, "turns": 0, "round": 1, "revision": 1,
                    "phase": "waiting", "since": now, "stage": 0, "acks": [], "open": [], "reward": None,
                    "started": False, "pausedSince": None, "requests": {}}
            conn.execute("INSERT INTO rooms VALUES(?,?,?)", (room["id"], request_id, json.dumps(room, ensure_ascii=False)))
            return self._snapshot(room, 0)

    def join(self, room_id: str, payload: dict) -> dict:
        invite, token = _token(payload.get("invite")), _token(payload.get("playerToken"))
        name = _name(payload.get("name"))
        with self._db() as conn:
            room = self._load(conn, room_id)
            if not secrets.compare_digest(_hash(invite), room["inviteHash"]):
                raise GameError("Pozvánka není platná.", 403)
            guest = room["players"][1]
            before = self._version(room)
            if guest:
                if not secrets.compare_digest(guest["tokenHash"], _hash(token)):
                    raise GameError("Obě místa jsou už obsazená.", 409)
                if guest["name"] != name:
                    raise GameError("Opakované připojení má jiné jméno.", 409)
            else:
                if secrets.compare_digest(room["players"][0]["tokenHash"], _hash(token)):
                    raise GameError("Druhý hráč musí mít vlastní přístup.", 409)
                room["players"][1] = {"name": name, "tokenHash": _hash(token), "seen": self.clock(), "ready": True}
            room["players"][1].update(seen=self.clock(), ready=True)
            room["touched"] = self.clock()
            self._presence(room)
            self._advance(room)
            if self._version(room) != before:
                room["revision"] += 1
            self._save(conn, room)
            return self._snapshot(room, 1)

    def _connected(self, player):
        return bool(player and player["ready"] and self.clock() - player["seen"] <= OFFLINE_SECONDS)

    def _presence(self, room):
        paused = room["started"] and room["phase"] != "finished" and not all(self._connected(p) for p in room["players"])
        now = self.clock()
        if paused and room["pausedSince"] is None:
            room["pausedSince"], room["acks"] = now, []
        elif not paused and room["pausedSince"] is not None:
            room["since"] += now - room["pausedSince"]
            room["pausedSince"] = None

    def _phase(self, room, phase):
        room["phase"], room["since"] = phase, self.clock()
        if phase in ("reveal", "reward"):
            room["stage"] += 1
            room["acks"] = []

    def _advance(self, room):
        if room["pausedSince"] is not None:
            return
        elapsed = self.clock() - room["since"]
        if room["phase"] == "reveal" and elapsed >= 2 and set(room["acks"]) == {0, 1}:
            self._phase(room, "choose" if len(room["open"]) == 1 else "compare")
        elif room["phase"] == "compare" and elapsed >= 1:
            a, b = (room["deck"][i] for i in room["open"])
            room["turns"] += 1
            room["open"] = []
            if a == b:
                room["owners"][a] = room["active"]
                room["reward"] = a
                self._phase(room, "reward")
            else:
                room["active"] = 1 - room["active"]
                self._phase(room, "choose")
        elif room["phase"] == "reward" and elapsed >= 2 and set(room["acks"]) == {0, 1}:
            room["reward"] = None
            self._phase(room, "finished" if len(room["owners"]) == PAIR_COUNT else "choose")

    @staticmethod
    def _version(room):
        values = {k: v for k, v in room.items() if k not in ("revision", "touched", "requests", "players")}
        values["players"] = [({k: v for k, v in p.items() if k != "seen"} if p else None) for p in room["players"]]
        return json.dumps(values, sort_keys=True)

    def act(self, room_id: str, token: str, action: str, payload: dict | None = None) -> dict:
        token, payload = _token(token), payload or {}
        if action not in ("sync", "ready", "leave", "start", "flip", "heard", "rematch"):
            raise GameError("Neznámá herní akce.")
        with self._db() as conn:
            room = self._load(conn, room_id)
            player = next((n for n, p in enumerate(room["players"]) if p and secrets.compare_digest(p["tokenHash"], _hash(token))), None)
            if player is None:
                raise GameError("Neplatný přístup do partie.", 403)
            before = self._version(room)
            room["players"][player]["seen"] = self.clock()
            room["touched"] = self.clock()
            if action == "ready":
                room["players"][player]["ready"] = True
            elif action == "leave":
                room["players"][player]["ready"] = False
            self._presence(room)
            self._advance(room)
            if action in ("start", "flip", "heard", "rematch"):
                request_id = _request(payload.get("requestId"))
                fingerprint = _hash(json.dumps([player, action, payload], sort_keys=True))
                prior = room["requests"].get(request_id)
                if prior and prior != fingerprint:
                    raise GameError("Identita požadavku už patří jiné akci.", 409)
                if not prior:
                    self._action(room, player, action, payload)
                    room["requests"][request_id] = fingerprint
                    room["requests"] = dict(list(room["requests"].items())[-256:])
            self._advance(room)
            if self._version(room) != before:
                room["revision"] += 1
            self._save(conn, room)
            return self._snapshot(room, player)

    def _action(self, room, player, action, payload):
        if (type(payload.get("expectedRound")) is not int or type(payload.get("expectedStage")) is not int
                or payload["expectedRound"] != room["round"] or payload["expectedStage"] != room["stage"]):
            raise GameError("Partie mezitím pokročila. Ověř její aktuální stav.", 409)
        if not all(self._connected(p) for p in room["players"]) or room["pausedSince"] is not None:
            raise GameError("Čekáme na připojení obou hráčů.", 409)
        if action == "start":
            if player != 0 or room["started"]:
                raise GameError("Partii může zahájit její zakladatel.", 409)
            room["started"] = True
            self._phase(room, "choose")
        elif action == "flip":
            index = payload.get("index")
            if room["phase"] != "choose" or room["active"] != player or type(index) is not int or not 0 <= index < 24 or index in room["open"] or room["deck"][index] in room["owners"]:
                raise GameError("Teď tuto kartičku otočit nelze.", 409)
            room["open"].append(index)
            self._phase(room, "reveal")
        elif action == "heard":
            if room["phase"] not in ("reveal", "reward") or type(payload.get("stage")) is not int or payload.get("stage") != room["stage"]:
                raise GameError("Tento poslech už není aktuální.", 409)
            if player not in room["acks"]:
                room["acks"].append(player)
        elif action == "rematch":
            if player != 0 or room["phase"] != "finished":
                raise GameError("Novou partii zahájí zakladatel po dokončení hry.", 409)
            if "uids" in payload:
                room["deck"] = self.catalog.selection(payload["uids"]) * 2
            self.shuffle(room["deck"])
            room.update(owners={}, active=0, turns=0, open=[], reward=None, acks=[], round=room["round"] + 1)
            self._phase(room, "choose")

    def _snapshot(self, room, player):
        cards = []
        for index, uid in enumerate(room["deck"]):
            state = "matched" if uid in room["owners"] else "open" if index in room["open"] else "hidden"
            card = {"index": index, "state": state}
            if state != "hidden":
                card["uid"] = uid
            cards.append(card)
        return {"protocol": PROTOCOL, "room": room["id"], "revision": room["revision"], "catalog": room["catalog"],
                "you": player, "players": [{"name": p["name"], "connected": self._connected(p)} if p else None for p in room["players"]],
                "cards": cards, "owners": room["owners"], "active": room["active"], "turns": room["turns"], "round": room["round"],
                "phase": room["phase"], "stage": room["stage"], "focus": room["open"][-1] if room["open"] else None,
                "reward": room["reward"], "acks": room["acks"],
                "paused": room["pausedSince"] is not None, "expires": room["expires"]}


class GameServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, rooms: Rooms, public_origin: str | None = None):
        self.rooms = rooms
        self.rate_lock, self.rate = threading.Lock(), {}
        super().__init__(address, Handler)
        self.origin = public_origin or f"http://127.0.0.1:{self.server_port}"
        url = urlsplit(self.origin)
        if url.path or url.query or url.fragment or url.username or url.scheme not in ("http", "https") or not url.netloc:
            self.server_close()
            raise ValueError("Use an origin without path, credentials, query or fragment")
        if url.scheme != "https" and url.hostname not in ("127.0.0.1", "localhost", "::1"):
            self.server_close()
            raise ValueError("Public origin requires HTTPS")


class Handler(BaseHTTPRequestHandler):
    server: GameServer

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *_):
        pass  # No room IDs, invitation tokens or player names in access logs.

    def _headers(self, status, kind, length, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; media-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()

    def _json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode()
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def _host(self):
        if self.headers.get("Host") != urlsplit(self.server.origin).netloc:
            raise GameError("Neplatná adresa služby.", 403)

    def do_GET(self):
        self._get()

    def do_HEAD(self):
        self._get(head=True)

    def _get(self, head=False):
        try:
            self._host()
            path = unquote(urlsplit(self.path).path)
            if path == API + "/health":
                body = json.dumps({"protocol": PROTOCOL, "available": True, "catalog": self.server.rooms.catalog.revision}).encode()
                self._headers(200, "application/json", len(body))
            else:
                if path in ("/", "/vocabulary-fr/"):
                    path = "/vocabulary-fr/index.html"
                allowed = path.startswith("/vocabulary-fr/") or path.startswith(("/assets/vocabulary-fr-v2/", "/assets/vocabulary-fr-audio/", "/assets/vocabulary-fr-sentences/")) or path in {
                    "/data/vocabulary-fr-v2.json", "/data/vocabulary-fr-audio.json", "/data/vocabulary-fr-quiz.json",
                    "/data/vocabulary-fr-sentence-audio.json", "/data/vocabulary-fr-sentence-pictures.json"}
                docs = self.server.rooms.catalog.docs
                target = (docs / path.lstrip("/")).resolve()
                if not allowed or ".." in Path(path).parts or not target.is_relative_to(docs) or not target.is_file():
                    raise GameError("Soubor nebyl nalezen.", 404)
                body = target.read_bytes()
                kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                extra, code = {"Accept-Ranges": "bytes"}, 200
                if requested := self.headers.get("Range"):
                    match = re.fullmatch(r"bytes=([0-9]{0,16})-([0-9]{0,16})", requested)
                    total = len(body)
                    if match and any(match.groups()):
                        first, last = match.groups()
                        start = int(first) if first else max(0, total - int(last))
                        end = min(int(last), total - 1) if first and last else total - 1
                    else:
                        start, end = total, -1
                    if not 0 <= start <= end < total:
                        self._headers(416, kind, 0, {"Content-Range": f"bytes */{total}"})
                        return
                    body = body[start:end + 1]
                    extra["Content-Range"] = f"bytes {start}-{end}/{total}"
                    code = 206
                self._headers(code, kind, len(body), extra)
            if not head:
                self.wfile.write(body)
        except GameError as exc:
            self._json({"error": str(exc)}, exc.status)
        except (OSError, ValueError):
            self._json({"error": "Soubor nelze načíst."}, 404)

    def do_POST(self):
        try:
            self._host()
            if self.headers.get("Origin") != self.server.origin:
                raise GameError("Tento původ není povolený.", 403)
            if self.headers.get_content_type() != "application/json" or self.headers.get("Transfer-Encoding"):
                raise GameError("Požadavek musí obsahovat JSON.", 415)
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise GameError("Neplatná velikost požadavku.") from None
            if not 0 < size <= MAX_BODY:
                raise GameError("Požadavek je příliš velký nebo prázdný.", 413)
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise GameError("Požadavek musí být objekt JSON.")
            path = urlsplit(self.path).path
            if path == API:
                self._rate()
                value = self.server.rooms.create(payload)
            else:
                match = re.fullmatch(re.escape(API) + r"/([a-f0-9]{24})/(join|sync|ready|leave|start|flip|heard|rematch)", path)
                if not match:
                    raise GameError("Herní akce nebyla nalezena.", 404)
                room, action = match.groups()
                if action == "join":
                    self._rate()
                    value = self.server.rooms.join(room, payload)
                else:
                    auth = self.headers.get("Authorization", "")
                    value = self.server.rooms.act(room, auth.removeprefix("Bearer ") if auth.startswith("Bearer ") else "", action, payload)
            self._json(value)
        except GameError as exc:
            self._json({"error": str(exc)}, exc.status)
        except (ValueError, UnicodeError):
            self._json({"error": "Neplatný JSON."}, 400)
        except (sqlite3.Error, OSError):
            self._json({"error": "Partii se nepodařilo uložit. Ověř znovu její stav."}, 503)

    def _rate(self):
        now, address = time.monotonic(), self.client_address[0]
        with self.server.rate_lock:
            values = [t for t in self.server.rate.get(address, []) if now - t < 60]
            if len(values) >= 20:
                raise GameError("Příliš mnoho připojení. Chvíli počkej.", 429)
            self.server.rate[address] = values + [now]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--public-origin")
    parser.add_argument("--database", type=Path, default=Path(__file__).resolve().parents[1] / "data/private/vocabulary-fr-online/rooms.sqlite3")
    args = parser.parse_args()
    if args.bind not in ("127.0.0.1", "localhost", "::1"):
        parser.error("Bind only to loopback; use a separately approved HTTPS reverse proxy.")
    server = GameServer((args.bind, args.port), Rooms(args.database, Catalog()), args.public_origin)
    print(f"Francouzština Jana: {server.origin}/vocabulary-fr/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
