"""Build and run the isolated FR service on a paid Render web service.

No provider account, payment, network configuration or deployment is created here.
The local pilot keeps its loopback-only CLI and its separate database.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import tarfile
import threading
from datetime import datetime, timezone
from urllib.parse import urlsplit

SERVER = "Samantha_Agent/app/vocabulary_fr_multiplayer.py"
CLOUD = "Samantha_Agent/app/vocabulary_fr_cloud.py"
PUBLIC = ("docs/vocabulary-fr", "docs/data/vocabulary-fr-v2.json", "docs/data/vocabulary-fr-audio.json",
          "docs/data/vocabulary-fr-quiz.json", "docs/data/vocabulary-fr-sentence-audio.json",
          "docs/data/vocabulary-fr-sentence-pictures.json", "docs/assets/vocabulary-fr-v2",
          "docs/assets/vocabulary-fr-audio", "docs/assets/vocabulary-fr-sentences")
RENDER_ORIGIN = re.compile(r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.onrender\.com\Z")


def _sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare_release(*, repo: Path, output: Path, expected_head: str) -> dict:
    """Export committed public FR inputs only; never copy the working directory."""
    repo, output = Path(repo).resolve(), Path(output).resolve()
    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", expected_head) or head != expected_head:
        raise ValueError("Exact approved source commit required")
    if output.is_relative_to(repo / ".git"):
        raise ValueError("Export cannot modify Git metadata")
    manifest = output / "manifest.json"
    if output.exists():
        prior = json.loads(manifest.read_text())
        if prior.get("kind") != "vocabulary-fr-cloud-v1" or prior.get("head") != head or not {SERVER, CLOUD, "docs/vocabulary-fr/online.html"}.issubset(prior.get("files", {})):
            raise ValueError("Existing release belongs to other inputs")
        for name, digest in prior["files"].items():
            path = Path(name)
            allowed = name in (SERVER, CLOUD) or any(name == p or name.startswith(p + "/") for p in PUBLIC)
            if not allowed or path.is_absolute() or ".." in path.parts or (output / path).is_symlink() or _sha(output / path) != digest:
                raise ValueError("Existing release changed")
        actual = set()
        for path in output.rglob("*"):
            if path.is_symlink():
                raise ValueError("Existing release contains a symlink")
            if path.is_file():
                actual.add(path.relative_to(output).as_posix())
        if actual != set(prior["files"]) | {"manifest.json"}:
            raise ValueError("Unexpected file in existing release")
        return prior
    archive = subprocess.check_output(["git", "-C", str(repo), "archive", head, "--", SERVER, CLOUD, *PUBLIC])
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source:
            if member.isdir():
                continue
            path = Path(member.name)
            if (not member.isfile() or path.is_absolute() or ".." in path.parts
                    or not (member.name in (SERVER, CLOUD) or any(member.name == p or member.name.startswith(p + "/") for p in PUBLIC))):
                raise ValueError("Unsafe public release member")
            target = output / path
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("xb") as destination:
                destination.write(source.extractfile(member).read())
            files[member.name] = _sha(target)
    if not {SERVER, CLOUD, "docs/vocabulary-fr/online.html"}.issubset(files):
        raise ValueError("Incomplete cloud release")
    result = {"kind": "vocabulary-fr-cloud-v1", "head": head, "files": files}
    with manifest.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    return result


def configuration(environment: dict | None = None) -> dict:
    """Use Render's assigned HTTPS origin and an existing persistent mount."""
    env = os.environ if environment is None else environment
    origin = env.get("RENDER_EXTERNAL_URL", "")
    port = env.get("PORT", "10000")
    directory = Path(env.get("VOCABULARY_FR_DATA_DIR", "/var/data"))
    if env.get("RENDER") != "true" or not RENDER_ORIGIN.fullmatch(origin):
        raise ValueError("Assigned Render HTTPS origin required")
    if not re.fullmatch(r"[0-9]{1,5}", port) or not 1024 <= int(port) <= 65535:
        raise ValueError("Valid unprivileged Render port required")
    if not directory.is_absolute() or not directory.is_dir() or directory.is_symlink():
        raise ValueError("Existing absolute persistent data directory required")
    return {"origin": origin, "port": int(port), "directory": directory.resolve()}


def _game():
    # -I ignores cwd/PYTHONPATH. Load this one sibling, never the Samantha runtime.
    spec = importlib.util.spec_from_file_location("vocabulary_fr_game", Path(__file__).with_name("vocabulary_fr_multiplayer.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_server(settings: dict, *, bind: str = "0.0.0.0"):
    game = _game()
    server = game.GameServer((bind, settings["port"]), game.Rooms(settings["directory"] / "rooms.sqlite3", game.Catalog()), settings["origin"])
    server.daemon_threads = False  # Drain bounded requests before Render's SIGTERM deadline.
    class CloudHandler(game.Handler):
        def _get(self, head=False):
            if urlsplit(self.path).path == game.API + "/health":
                try:
                    self._host()
                    with sqlite3.connect(self.server.rooms.database.as_uri() + "?mode=ro", uri=True, timeout=1) as conn:
                        conn.execute("SELECT id FROM rooms LIMIT 1").fetchone()
                except game.GameError as error:
                    self._json({"error": str(error)}, error.status)
                    return
                except (sqlite3.Error, OSError):
                    self._json({"error": "Game database unavailable"}, 503)
                    return
            super()._get(head)
    server.RequestHandlerClass = CloudHandler
    return server


def serve(settings: dict) -> None:
    server = create_server(settings)
    stopped = threading.Event()
    def stop(_signal, _frame):
        if not stopped.is_set():
            stopped.set()
            threading.Thread(target=server.shutdown, daemon=True).start()
    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        print("French pairs cloud service ready", flush=True)
        server.serve_forever()
    finally:
        server.server_close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def backup_database(*, directory: Path) -> Path:
    """Consistent local SQLite backup; no deletion, overwrite or external upload."""
    directory = Path(directory).resolve()
    source = directory / "rooms.sqlite3"
    if not source.is_file() or source.is_symlink():
        raise ValueError("Existing regular game database required")
    backups = directory / "backups"
    if backups.is_symlink():
        raise ValueError("Backup directory must not be a symlink")
    backups.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = backups / ("rooms-" + stamp + ".sqlite3")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as reader, sqlite3.connect(target) as writer:
        reader.backup(writer)
        if writer.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise RuntimeError("Game backup integrity not confirmed")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    build.add_argument("--head", default=os.environ.get("RENDER_GIT_COMMIT", ""))
    commands.add_parser("serve")
    commands.add_parser("backup")
    args = parser.parse_args()
    if args.command == "build":
        result = prepare_release(repo=args.repo, output=args.output, expected_head=args.head)
        print(json.dumps({"head": result["head"], "files": len(result["files"])}))
    elif args.command == "serve":
        serve(configuration())
    else:
        backup_database(directory=configuration()["directory"])
        print("Consistent game database backup created on the persistent disk")


if __name__ == "__main__":
    main()
