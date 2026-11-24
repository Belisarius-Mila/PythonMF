"""Owned, temporary FR HTTPS pilot. No launchd, VPN or Cockpit changes.

The connector is supplied explicitly after verifying its official release digest.
This controller only exports committed public FR files and starts owned processes.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import re
import signal
import shlex
import socket
import subprocess
import sys
import tarfile
import time
import uuid
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PUBLIC = ("docs/vocabulary-fr", "docs/data/vocabulary-fr-v2.json", "docs/data/vocabulary-fr-audio.json",
          "docs/data/vocabulary-fr-quiz.json", "docs/data/vocabulary-fr-sentence-audio.json",
          "docs/data/vocabulary-fr-sentence-pictures.json", "docs/assets/vocabulary-fr-v2",
          "docs/assets/vocabulary-fr-audio", "docs/assets/vocabulary-fr-sentences")
SERVER = "Samantha_Agent/app/vocabulary_fr_multiplayer.py"
ORIGIN = re.compile(r"https://[a-z0-9]+(?:-[a-z0-9]+)+\.trycloudflare\.com\b")
CLOUD_ORIGIN = re.compile(r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.onrender\.com\Z")


def _sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def _write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    with temporary.open("x") as stream:
        os.chmod(temporary, 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def _git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def cockpit_french_url(original: str, repo: Path) -> str:
    """Attach the owned running game's origin without moving personal browser data.

    The fragment stays out of the Pages HTTP request. Reading the catalog never
    starts a game service, changes a tunnel, or exposes process/player details.
    """
    try:
        try:
            config = json.loads((Path(repo) / "docs/vocabulary-fr/online-hosting.json").read_text())
        except (OSError, ValueError):
            config = {}
        origin = config.get("origin") if isinstance(config, dict) and config.get("schemaVersion") == 1 else None
        if not isinstance(origin, str) or not CLOUD_ORIGIN.fullmatch(origin):
            state = Pilot(repo).status()
            origin = state.get("origin")
            if state.get("running") is not True or not isinstance(origin, str) or not ORIGIN.fullmatch(origin):
                return original
        url = urlsplit(original)
        params = dict(parse_qsl(url.fragment))
        params["onlineOrigin"] = origin
        return urlunsplit((url.scheme, url.netloc, url.path, url.query, urlencode(params)))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError):
        return original


class Pilot:
    def __init__(self, repo: Path):
        self.repo = Path(repo).resolve()
        self.root = self.repo / "Samantha_Agent/data/private/vocabulary-fr-hosting"

    @contextmanager
    def _lock(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        with (self.root / "operation.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def prepare(self, *, expected_head: str, connector: Path, connector_sha256: str) -> dict:
        """Freeze one clean committed FR release and an explicitly verified binary."""
        with self._lock():
            if not re.fullmatch(r"[a-f0-9]{40}", expected_head) or _git(self.repo, "rev-parse", "HEAD") != expected_head:
                raise ValueError("Approved commit differs")
            if _git(self.repo, "status", "--porcelain") or _git(self.repo, "branch", "--show-current") != "main":
                raise ValueError("Clean main required")
            connector = Path(connector).resolve()
            private = self.repo / "Samantha_Agent/data/private"
            if not connector.is_relative_to(private) or not re.fullmatch(r"[a-f0-9]{64}", connector_sha256) or _sha(connector) != connector_sha256:
                raise ValueError("Verified project-local connector required")
            release = self.root / "releases" / expected_head
            manifest = release / "manifest.json"
            if manifest.exists():
                result = json.loads(manifest.read_text())
                self._verify(result)
                if result["connectorSha256"] != connector_sha256 or result["connector"] != str(connector):
                    raise ValueError("Release already has another connector")
                return result
            release.mkdir(mode=0o700, parents=True, exist_ok=False)
            files = {}
            archive = subprocess.check_output(["git", "-C", str(self.repo), "archive", expected_head, "--", SERVER, *PUBLIC])
            with tarfile.open(fileobj=io.BytesIO(archive)) as source:
                for member in source:
                    if member.isdir():
                        continue
                    path = Path(member.name)
                    if not member.isfile() or path.is_absolute() or ".." in path.parts or not (member.name == SERVER or any(member.name == p or member.name.startswith(p + "/") for p in PUBLIC)):
                        raise ValueError("Unsafe release member")
                    target = release / path
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    with target.open("xb") as output:
                        output.write(source.extractfile(member).read())
                    files[member.name] = _sha(target)
            if SERVER not in files or "docs/vocabulary-fr/online.html" not in files:
                raise ValueError("Incomplete FR release")
            if _git(self.repo, "rev-parse", "HEAD") != expected_head or _git(self.repo, "status", "--porcelain"):
                raise ValueError("Source changed during release preparation")
            result = {"head": expected_head, "release": str(release), "files": files,
                      "connector": str(connector), "connectorSha256": connector_sha256}
            _write(manifest, result)
            return result

    def _verify(self, prepared):
        release = Path(prepared["release"])
        if release.resolve() != self.root / "releases" / prepared["head"]:
            raise ValueError("Foreign release")
        if any(_sha(release / name) != sha for name, sha in prepared["files"].items()):
            raise ValueError("Release content changed")
        if _sha(prepared["connector"]) != prepared["connectorSha256"]:
            raise ValueError("Connector content changed")

    @staticmethod
    def _identity(pid):
        environment = {**os.environ, "LC_ALL": "C", "LANG": "C"}
        environment.pop("TZ", None)  # Match the host clock, independent of a caller's UTC test environment.
        result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
                                capture_output=True, text=True, env=environment)
        return result.stdout.strip() if result.returncode == 0 else ""

    @staticmethod
    def _stable_identity(value):
        # macOS Python's launcher execs its framework interpreter in the same PID.
        # Preserve birth time and every server argument; normalize only known executables.
        parts = value.split(None, 5)
        if len(parts) == 6:
            try:
                args = shlex.split(parts[5])
                months = {name: n for n, name in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
                months.update(dict(zip("led úno bře dub kvě čer čvc srp zář říj lis pro".split(), range(1, 13))))
                # Legacy macOS receipts used Czech day-month order; new C output uses month-day.
                if parts[1].lower() in months:
                    month, day = months[parts[1].lower()], int(parts[2])
                else:
                    month, day = months[parts[2].lower()], int(parts[1])
                birth = datetime(int(parts[4]), month, day, *map(int, parts[3].split(":"))).isoformat()
            except (ValueError, KeyError, TypeError):
                return value
            interpreters = {sys.executable, str(Path(sys.executable).resolve()),
                            str(Path(sys.base_prefix) / "Resources/Python.app/Contents/MacOS/Python")}
            if len(args) > 2 and args[0] in interpreters and args[1] == "-I" and args[2].endswith("/Samantha_Agent/app/vocabulary_fr_multiplayer.py"):
                args[0] = "<owned-python>"
            return birth + " " + json.dumps(args)
        return value

    def status(self):
        path = self.root / "active.json"
        if not path.exists():
            return {"state": "not_started"}
        result = json.loads(path.read_text())
        result["alive"] = {name: bool(record["identity"] and self._stable_identity(self._identity(record["pid"])) == self._stable_identity(record["identity"]))
                           for name, record in result.get("processes", {}).items()}
        result["running"] = result.get("state") == "started" and result["alive"] == {"connector": True, "server": True}
        return result

    def start(self, *, expected_head: str, request_id: str, confirmed: bool) -> dict:
        """One explicit pilot; uncertain/previous requests never start twice."""
        if confirmed is not True or not re.fullmatch(r"[a-zA-Z0-9_-]{12,80}", request_id):
            raise ValueError("Explicit deployment confirmation and request identity required")
        with self._lock():
            previous = self.status()
            if previous["state"] != "not_started":
                if previous.get("requestId") == request_id and previous.get("head") == expected_head:
                    return previous
                if previous["state"] != "stopped":
                    raise ValueError("Existing pilot must be checked or stopped; no automatic restart")
            prepared = json.loads((self.root / "releases" / expected_head / "manifest.json").read_text())
            self._verify(prepared)
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 8791))
            state = {"state": "starting", "head": expected_head, "requestId": request_id,
                     "processes": {}, "origin": None, "temporary": True, "created": time.time()}
            active = self.root / "active.json"
            _write(active, state)
            env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")
                   and not k.startswith(("TUNNEL_", "CLOUDFLARED_"))}
            directory = self.root / request_id
            directory.mkdir(mode=0o700)
            # A pilot never consumes an existing home/account tunnel configuration.
            (directory / "connector.yaml").write_text("{}\n")
            def launch(name, args):
                with (directory / (name + ".log")).open("xb") as output:
                    os.chmod(output.name, 0o600)
                    process = subprocess.Popen(args, cwd=prepared["release"], stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                               start_new_session=True, env=env)
                identity = self._identity(process.pid)
                state["processes"][name] = {"pid": process.pid, "identity": identity}
                _write(active, state)
                if not identity:
                    raise RuntimeError(name + " exited during startup")
                return process
            try:
                connector = launch("connector", [prepared["connector"], "--no-autoupdate", "tunnel", "--config", str(directory / "connector.yaml"), "--loglevel", "info", "--protocol", "http2", "--edge-ip-version", "4",
                                                   "--url", "http://127.0.0.1:8791", "--metrics", "127.0.0.1:0"])
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    found = ORIGIN.findall((directory / "connector.log").read_text(errors="replace"))
                    if found:
                        state["origin"] = found[0]
                        break
                    if connector.poll() is not None:
                        raise RuntimeError("HTTPS connector stopped; inspect its original log")
                    time.sleep(.2)
                if not state["origin"]:
                    raise RuntimeError("HTTPS address not confirmed; inspect original connector")
                launch("server", [sys.executable, "-I", str(Path(prepared["release"]) / SERVER), "--port", "8791",
                                  "--database", str(self.root / "rooms.sqlite3"), "--public-origin", state["origin"]])
                state["state"] = "started"
                _write(active, state)
                return self.status()
            except Exception:
                state["state"] = "attention"
                _write(active, state)
                raise

    def stop(self, *, request_id: str, confirmed: bool) -> dict:
        """Stop only exact owned processes; preserve games, logs and release files."""
        if confirmed is not True:
            raise ValueError("Explicit stop required")
        with self._lock():
            state = self.status()
            if state.get("requestId") != request_id:
                raise ValueError("Pilot identity differs")
            for name in ("connector", "server"):
                record = state.get("processes", {}).get(name)
                if record and state["alive"].get(name):
                    os.kill(record["pid"], signal.SIGTERM)
            state["state"] = "stopped"
            _write(self.root / "active.json", state)
            return state

    def _wait_for_server(self, origin, prepared):
        names = ("vocabulary-fr-v2.json", "vocabulary-fr-audio.json", "vocabulary-fr-quiz.json")
        expected = hashlib.sha256(b"\0".join((Path(prepared["release"]) / "docs/data" / name).read_bytes() for name in names)).hexdigest()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            connection = http.client.HTTPConnection("127.0.0.1", 8791, timeout=1)
            try:
                connection.request("GET", "/api/vocabulary-fr/rooms/health", headers={"Host": urlsplit(origin).netloc})
                response = connection.getresponse()
                result = json.loads(response.read(4096))
                if response.status == 200 and isinstance(result, dict) and result.get("protocol") == 1 and result.get("catalog") == expected:
                    return
            except (OSError, ValueError, http.client.HTTPException):
                pass
            finally:
                connection.close()
            time.sleep(.2)
        raise RuntimeError("Updated game server health not confirmed; inspect original upgrade")

    def upgrade(self, *, expected_head: str, expected_running_head: str, request_id: str, confirmed: bool) -> dict:
        """Replace only the owned backend; retain the connector, origin and games.

        Each durable request executes at most once, including partial failures.
        Catalog changes require a separately planned migration, never this path.
        """
        if confirmed is not True or not re.fullmatch(r"[a-zA-Z0-9_-]{12,80}", request_id):
            raise ValueError("Explicit game upgrade confirmation and request identity required")
        if not all(re.fullmatch(r"[a-f0-9]{40}", head) for head in (expected_head, expected_running_head)):
            raise ValueError("Exact approved and running commits required")
        with self._lock():
            directory = self.root / "upgrades"
            receipt = directory / (request_id + ".json")
            if receipt.exists():
                prior = json.loads(receipt.read_text())
                if (prior["head"], prior["fromHead"]) != (expected_head, expected_running_head):
                    raise ValueError("Upgrade request already belongs to different commits")
                return {**self.status(), "upgrade": prior}
            state = self.status()
            if not state.get("running") or state.get("head") != expected_running_head or expected_head == expected_running_head:
                raise ValueError("Exact owned running pilot required; no automatic restart")
            if not ORIGIN.fullmatch(state.get("origin", "")) or not (self.root / "rooms.sqlite3").is_file():
                raise ValueError("Original game origin and database required")
            if (_git(self.repo, "rev-parse", "HEAD") != expected_head or _git(self.repo, "status", "--porcelain")
                    or _git(self.repo, "branch", "--show-current") != "main"):
                raise ValueError("Exact clean approved main required")
            prepared = json.loads((self.root / "releases" / expected_head / "manifest.json").read_text())
            old = json.loads((self.root / "releases" / expected_running_head / "manifest.json").read_text())
            if prepared.get("head") != expected_head or old.get("head") != expected_running_head:
                raise ValueError("Prepared release does not match approved commits")
            self._verify(prepared)
            self._verify(old)
            metadata = ("docs/data/vocabulary-fr-v2.json", "docs/data/vocabulary-fr-audio.json", "docs/data/vocabulary-fr-quiz.json")
            if (any(prepared["files"][name] != old["files"][name] for name in metadata)
                    or prepared["connector"] != old["connector"] or prepared["connectorSha256"] != old["connectorSha256"]):
                raise ValueError("Game catalog and connector must remain unchanged")
            if self.status() != state:
                raise ValueError("Pilot changed during upgrade preparation")
            directory.mkdir(mode=0o700, exist_ok=True)
            operation = {"requestId": request_id, "head": expected_head, "fromHead": expected_running_head, "state": "upgrading"}
            _write(receipt, operation)  # Durable intent precedes the single stop/start.
            state["state"] = "upgrading"
            _write(self.root / "active.json", state)
            try:
                server = state["processes"]["server"]
                if self._stable_identity(self._identity(server["pid"])) != self._stable_identity(server["identity"]):
                    raise RuntimeError("Original game process changed; nothing stopped")
                os.kill(server["pid"], signal.SIGTERM)
                deadline = time.monotonic() + 30
                while self._stable_identity(self._identity(server["pid"])) == self._stable_identity(server["identity"]):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Original game process has not exited; no replacement started")
                    time.sleep(.2)
                with socket.socket() as probe:
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    probe.bind(("127.0.0.1", 8791))
                env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")
                       and not k.startswith(("TUNNEL_", "CLOUDFLARED_"))}
                args = [sys.executable, "-I", str(Path(prepared["release"]) / SERVER), "--port", "8791",
                        "--database", str(self.root / "rooms.sqlite3"), "--public-origin", state["origin"]]
                with (directory / (request_id + "-server.log")).open("xb") as output:
                    os.chmod(output.name, 0o600)
                    process = subprocess.Popen(args, cwd=prepared["release"], stdin=subprocess.DEVNULL, stdout=output,
                                               stderr=output, start_new_session=True, env=env)
                identity = self._identity(process.pid)
                state["processes"]["server"] = {"pid": process.pid, "identity": identity}
                _write(self.root / "active.json", state)
                if not identity:
                    raise RuntimeError("Updated game process exited during startup")
                self._wait_for_server(state["origin"], prepared)
                state.update(state="started", head=expected_head)
                if self.status()["alive"] != {"connector": True, "server": True}:
                    raise RuntimeError("Owned connector or game process stopped during upgrade")
                operation["state"] = "completed"
                _write(self.root / "active.json", state)
                _write(receipt, operation)
                return {**self.status(), "upgrade": operation}
            except Exception:
                state["state"] = operation["state"] = "attention"
                _write(self.root / "active.json", state)
                _write(receipt, operation)
                raise
