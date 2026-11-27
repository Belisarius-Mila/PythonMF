"""Owned private FR service on Tailscale Serve. Never enables Funnel or grants.

prepare() is local-only. activate() requires the exact global safety phrase
and a frozen, reviewable plan before writing a LaunchAgent or Serve route.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import plistlib
import re
import socket
import sqlite3
import subprocess
import sys
import time
import uuid

from app.vocabulary_fr_cloud import prepare_release, backup_database, SERVER
from app.vocabulary_fr_multiplayer import Catalog

CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
TAILSCALE = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
LABEL = "com.samantha.vocabulary-fr"
PORT = 8792
HTTPS_PORT = "8443"
PROXY = "http://127.0.0.1:8792"
DNS = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+ts\.net\Z")


def _bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    with temporary.open("xb") as stream:
        os.chmod(temporary, 0o600)
        stream.write(value if isinstance(value, bytes) else _bytes(value))
        stream.flush();os.fsync(stream.fileno())
    os.replace(temporary, path)


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=30,
                          env={**os.environ, "TAILSCALE_BE_CLI": "1"})


def _canonical(value):
    result = copy.deepcopy(value)
    for key in ("TCP", "Web", "AllowFunnel"):
        result.setdefault(key, {})
    return result


def _without_game(value, endpoint):
    result = _canonical(value)
    result["TCP"].pop(HTTPS_PORT, None)
    result["Web"].pop(endpoint, None)
    result["AllowFunnel"].pop(endpoint, None)
    return result


def _route(value, endpoint):
    return (value.get("TCP", {}).get(HTTPS_PORT) == {"HTTPS": True}
            and value.get("Web", {}).get(endpoint) == {"Handlers": {"/": {"Proxy": PROXY}}})


def _catalog_transition(previous, current, database):
    """Allow existing rooms only when every old playable meaning is identical."""
    if not Path(database).exists():
        return None
    if Path(database).is_symlink():
        raise ValueError("Foreign game database must be preserved")
    names = ("vocabulary-fr-v2.json", "vocabulary-fr-audio.json", "vocabulary-fr-quiz.json")
    if all((Path(previous) / "docs/data" / name).read_bytes()
           == (Path(current) / "docs/data" / name).read_bytes() for name in names):
        return None
    before, after = Catalog(Path(previous) / "docs"), Catalog(Path(current) / "docs")
    if before.revision == after.revision:
        return None
    for uid, item in before.items.items():
        if item != after.items.get(uid) or before.metadata[uid] != after.metadata.get(uid):
            raise ValueError("Existing vocabulary changed; automatic room migration refused")
    return {"from": before.revision, "to": after.revision, "uids": sorted(before.items)}


def _migrate_rooms(directory, transition):
    """One backed-up transaction; preserve all fields except the catalog version."""
    backup = backup_database(directory=directory)
    database = Path(directory) / "rooms.sqlite3"
    allowed = set(transition["uids"])
    with sqlite3.connect(database) as connection:
        connection.execute("BEGIN IMMEDIATE")
        updates = []
        for uid, body in connection.execute("SELECT id, body FROM rooms"):
            room = json.loads(body)
            if room.get("catalog") != transition["from"]:
                continue
            references = list(room.get("deck", [])) + list(room.get("pool", []))
            for question in room.get("questions", []):
                references += [question["target"], *question["choices"]]
            if room.get("id") != uid or any(word not in allowed for word in references):
                raise ValueError("Room contains an unknown meaning; no room was changed")
            room["catalog"] = transition["to"]
            updates.append((json.dumps(room, ensure_ascii=False), uid))
        connection.executemany("UPDATE rooms SET body=? WHERE id=?", updates)
    return {"rooms": len(updates), "backup": str(backup),
            "from": transition["from"], "to": transition["to"]}


class PrivateGame:
    def __init__(self, repo: Path, *, home: Path | None = None, runner=_run):
        self.repo = Path(repo).resolve()
        self.root = self.repo / "Samantha_Agent/data/private/vocabulary-fr-tailnet"
        self.agent = (Path.home() if home is None else Path(home)) / "Library/LaunchAgents" / (LABEL + ".plist")
        self.target = f"gui/{os.getuid()}/{LABEL}"
        self.runner = runner

    @contextmanager
    def _lock(self):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.root / "operation.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def _checked(self, args):
        result = self.runner(args)
        if result.returncode:
            raise RuntimeError("Owned private service operation not confirmed")
        return result.stdout

    def _network(self):
        device = json.loads(self._checked([TAILSCALE, "status", "--json"]))
        dns = device.get("Self", {}).get("DNSName", "").rstrip(".")
        if device.get("BackendState") != "Running" or not DNS.fullmatch(dns):
            raise ValueError("Running owned Tailscale device required")
        serve = json.loads(self._checked([TAILSCALE, "serve", "status", "--json"]))
        funnel = json.loads(self._checked([TAILSCALE, "funnel", "status", "--json"]))
        for value in (serve, funnel):
            if (not isinstance(value, dict) or not isinstance(value.get("AllowFunnel", {}), dict)
                    or any(v is not False for v in value.get("AllowFunnel", {}).values())):
                raise ValueError("Funnel must remain disabled")
        if serve.get("Web", {}).get(dns + ":443", {}).get("Handlers", {}).get("/") != {"Proxy": "http://127.0.0.1:8770"}:
            raise ValueError("Existing private Cockpit root required")
        return {"dns": dns, "node": device.get("Self", {}).get("ID"), "serve": serve, "funnel": funnel}

    def _head(self):
        head = subprocess.check_output(["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(self.repo), "status", "--porcelain"], text=True).strip()
        branch = subprocess.check_output(["git", "-C", str(self.repo), "branch", "--show-current"], text=True).strip()
        if dirty or branch != "main":
            raise ValueError("Clean main required")
        return head

    def _health(self, origin):
        connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=2)
        try:
            connection.request("GET", "/api/vocabulary-fr/rooms/health", headers={"Host": origin.split("//")[1]})
            response = connection.getresponse();value = json.loads(response.read(4096))
            return value if response.status == 200 and value.get("protocol") == 1 else None
        except (OSError, ValueError, http.client.HTTPException):
            return None
        finally:connection.close()

    def status(self):
        path = self.root / "active.json"
        if not path.exists():
            return {"state": "not_started", "running": False}
        value = json.loads(path.read_text());value["running"] = False
        if value.get("state") != "active":
            return value
        value["running"] = self._running(value)
        return value

    def _running(self, value):
        try:
            owned = self.agent.is_file() and not self.agent.is_symlink() and hashlib.sha256(self.agent.read_bytes()).hexdigest() == value["agentSha256"]
            process = self.runner(["/bin/launchctl", "print", self.target])
            network = self._network()
            correct_path = re.search(r"(?m)^\s*path = " + re.escape(str(self.agent)) + r"\s*$", process.stdout)
            return bool(owned and correct_path and process.returncode == 0 and re.search(r"\bpid = [1-9][0-9]*", process.stdout)
                                    and network["dns"] == value["dns"] and network["node"] == value["node"]
                                    and _route(network["serve"], value["dns"] + ":" + HTTPS_PORT) and self._health(value["origin"]))
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
            return False

    def verify(self, *, request_id: str, plan_digest: str):
        """Resolve only the original activation by live proof, without a new action."""
        if not re.fullmatch(r"[a-zA-Z0-9_-]{12,80}", request_id):raise ValueError("Original request required")
        with self._lock():
            envelope = json.loads((self.root / "plans" / (request_id + ".json")).read_text())
            receipt = self.root / "requests" / (request_id + ".json")
            operation = json.loads(receipt.read_text());plan = envelope["plan"]
            if plan_digest != envelope["digest"] or operation["digest"] != plan_digest or _digest(plan) != plan_digest:
                raise ValueError("Original plan identity differs")
            state = json.loads((self.root / "active.json").read_text())
            definition_sha = hashlib.sha256(plistlib.dumps(plan["definition"], sort_keys=True)).hexdigest()
            if (state.get("head"), state.get("origin"), state.get("agentSha256")) != (plan["head"], plan["origin"], definition_sha):
                raise ValueError("Current service belongs to another activation")
            network = self._network();endpoint = plan["network"]["dns"] + ":" + HTTPS_PORT
            if self._running(state) and _without_game(network["serve"], endpoint) == _without_game(plan["network"]["serve"], endpoint):
                state["state"] = "active";operation["state"] = "completed"
                _write(self.root / "active.json", state);_write(receipt, operation)
            return {**self.status(), "operation": operation}

    def prepare(self, *, expected_head: str, request_id: str):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{12,80}", request_id):
            raise ValueError("Stable request identity required")
        with self._lock():
            plans = self.root / "plans";plans.mkdir(mode=0o700, exist_ok=True)
            path = plans / (request_id + ".json")
            if path.exists():
                prior = json.loads(path.read_text())
                if prior["plan"]["head"] != expected_head:
                    raise ValueError("Request already belongs to another commit")
                return prior
            if self._head() != expected_head:
                raise ValueError("Approved commit differs")
            old = self.status()
            if old["state"] not in ("not_started", "active") or (old["state"] == "active" and not old["running"]):
                raise ValueError("Existing private service requires inspection")
            if self.agent.is_symlink():raise ValueError("Foreign LaunchAgent symlink must be preserved")
            installed = self.agent.read_bytes() if self.agent.exists() else None
            if installed is not None and (not old.get("running") or hashlib.sha256(installed).hexdigest() != old["agentSha256"]):
                raise ValueError("Foreign LaunchAgent must be preserved")
            if installed is None and self.runner(["/bin/launchctl", "print", self.target]).returncode == 0:
                raise ValueError("Foreign service label must be preserved")
            network = self._network();endpoint = network["dns"] + ":" + HTTPS_PORT
            occupied = HTTPS_PORT in network["serve"].get("TCP", {}) or endpoint in network["serve"].get("Web", {})
            if occupied and (not old.get("running") or not _route(network["serve"], endpoint)):
                raise ValueError("Private game port is already owned by another service")
            if not old.get("running"):
                with socket.socket() as probe:probe.bind(("127.0.0.1", PORT))
            release = self.root / "releases" / expected_head
            prepared = prepare_release(repo=self.repo, output=release, expected_head=expected_head)
            origin = "https://" + endpoint
            definition = {"Label": LABEL, "ProgramArguments": [sys.executable, "-I", str(release / SERVER), "--port", str(PORT),
                          "--database", str(self.root / "rooms.sqlite3"), "--public-origin", origin],
                          "WorkingDirectory": str(release), "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 10,
                          "Umask": 63, "EnvironmentVariables": {"PYTHONDONTWRITEBYTECODE": "1"},
                          "StandardOutPath": str(self.root / "server.log"), "StandardErrorPath": str(self.root / "server-error.log")}
            plan = {"requestId": request_id, "head": expected_head, "origin": origin, "network": network,
                    "definition": definition, "priorAgentSha256": hashlib.sha256(installed).hexdigest() if installed is not None else None,
                    "files": len(prepared["files"]),
                    "releaseManifestSha256": hashlib.sha256((release / "manifest.json").read_bytes()).hexdigest()}
            if old.get("running"):
                transition = _catalog_transition(self.root / "releases" / old["head"],
                                                 release, self.root / "rooms.sqlite3")
                if transition:
                    plan["catalogTransition"] = transition
                    plan["previousHead"] = old["head"]
            result = {"plan": plan, "digest": _digest(plan)}
            _write(path, result)
            return result

    def activate(self, *, request_id: str, plan_digest: str, confirmation: str):
        if confirmation != CONFIRMATION or not re.fullmatch(r"[a-zA-Z0-9_-]{12,80}", request_id):
            raise ValueError("Exact global safety phrase and request required")
        with self._lock():
            envelope = json.loads((self.root / "plans" / (request_id + ".json")).read_text())
            plan = envelope["plan"]
            if plan_digest != envelope["digest"] or _digest(plan) != plan_digest:
                raise ValueError("Approved plan differs")
            requests = self.root / "requests";requests.mkdir(mode=0o700, exist_ok=True)
            receipt = requests / (request_id + ".json")
            if receipt.exists():
                original = json.loads(receipt.read_text())
                if original["digest"] != plan_digest:raise ValueError("Foreign activation receipt")
                return {**self.status(), "operation": original}
            if self._head() != plan["head"] or self._network() != plan["network"]:
                raise ValueError("Source or private network changed; prepare a new plan")
            if self.agent.is_symlink():raise ValueError("LaunchAgent symlink must be preserved")
            installed = self.agent.read_bytes() if self.agent.exists() else None
            installed_sha = hashlib.sha256(installed).hexdigest() if installed is not None else None
            if installed_sha != plan["priorAgentSha256"]:
                raise ValueError("LaunchAgent changed; nothing activated")
            if installed is not None and not self.status().get("running"):
                raise ValueError("Original owned running service is not confirmed")
            release = self.root / "releases" / plan["head"]
            prepare_release(repo=self.repo, output=release, expected_head=plan["head"])
            manifest_sha = hashlib.sha256((release / "manifest.json").read_bytes()).hexdigest()
            if plan.get("releaseManifestSha256") and manifest_sha != plan["releaseManifestSha256"]:
                raise ValueError("Frozen release manifest changed; nothing activated")
            if (release / "private/vocabulary-fr-eclair").exists() and not plan.get("releaseManifestSha256"):
                raise ValueError("Private sentence content requires a newly frozen plan")
            if plan.get("catalogTransition"):
                actual = _catalog_transition(self.root / "releases" / plan["previousHead"],
                                             release, self.root / "rooms.sqlite3")
                if actual != plan["catalogTransition"]:
                    raise ValueError("Frozen catalog migration differs; nothing activated")
            definition = plistlib.dumps(plan["definition"], sort_keys=True)
            operation = {"requestId": request_id, "digest": plan_digest, "state": "activating"}
            state = {"state": "activating", "head": plan["head"], "origin": plan["origin"], "dns": plan["network"]["dns"],
                     "node": plan["network"]["node"], "agentSha256": hashlib.sha256(definition).hexdigest()}
            _write(receipt, operation);_write(self.root / "active.json", state)
            try:
                if installed is not None:
                    _write(requests / (request_id + "-previous.plist"), installed)
                    self._checked(["/bin/launchctl", "bootout", self.target])
                elif self.runner(["/bin/launchctl", "print", self.target]).returncode == 0:
                    raise ValueError("Foreign service label appeared")
                deadline = time.monotonic() + 30
                while True:
                    try:
                        with socket.socket() as probe:
                            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1);probe.bind(("127.0.0.1", PORT))
                        break
                    except OSError:
                        if time.monotonic() >= deadline:raise RuntimeError("Game port has not become free")
                        time.sleep(.2)
                if plan.get("catalogTransition"):
                    operation["catalogMigration"] = _migrate_rooms(self.root, plan["catalogTransition"])
                    _write(receipt, operation)
                self.agent.parent.mkdir(parents=True, exist_ok=True)
                if installed is None:
                    with self.agent.open("xb") as stream:
                        os.chmod(self.agent, 0o600);stream.write(definition);stream.flush();os.fsync(stream.fileno())
                else:
                    if self.agent.is_symlink() or self.agent.read_bytes() != installed:
                        raise ValueError("LaunchAgent changed during activation")
                    _write(self.agent, definition)
                self._checked(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(self.agent)])
                expected = hashlib.sha256(b"\0".join((release / "docs/data" / name).read_bytes() for name in
                    ("vocabulary-fr-v2.json", "vocabulary-fr-audio.json", "vocabulary-fr-quiz.json"))).hexdigest()
                deadline = time.monotonic() + 25
                while True:
                    health = self._health(plan["origin"])
                    if health and health.get("catalog") == expected:break
                    if time.monotonic() >= deadline:raise RuntimeError("Owned game health not confirmed")
                    time.sleep(.2)
                self._checked([TAILSCALE, "serve", "--yes", "--bg", "--https=" + HTTPS_PORT, PROXY])
                after = self._network();endpoint = plan["network"]["dns"] + ":" + HTTPS_PORT
                if (after["dns"] != plan["network"]["dns"] or after["node"] != plan["network"]["node"]
                        or not _route(after["serve"], endpoint)
                        or _without_game(after["serve"], endpoint) != _without_game(plan["network"]["serve"], endpoint)):
                    raise RuntimeError("Private route or protected configuration not confirmed")
                state["state"] = "active";_write(self.root / "active.json", state)
                if not self.status().get("running"):raise RuntimeError("Owned running service not confirmed")
                operation["state"] = "completed";_write(receipt, operation)
                return {**self.status(), "operation": operation}
            except Exception:
                state["state"] = operation["state"] = "attention"
                _write(self.root / "active.json", state);_write(receipt, operation)
                raise
