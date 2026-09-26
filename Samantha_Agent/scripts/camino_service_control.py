#!/usr/bin/env python3
"""M2c: explicit local service controls. Never changes Serve, Funnel or phone data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import secrets
import socket
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from camino.domain.revision_store import RevisionStore, SCHEMA_VERSION
from camino.server.auth import RevocableTokenStore
from camino.server.service_safety import database_lock, private_write, readonly, snapshot_before_upgrade

ROOT = Path.home() / "Library/Application Support/PythonMF/Camino/Service"
LABEL = "cz.pythonmf.camino.service"
LAUNCH_AGENTS = Path.home() / "Library/LaunchAgents"
PORT = 8767  # 8766 is reserved for ScanDocu on this Mac.
TAILSCALE = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
FIELDS = {"metadata_db", "auth_db", "media_db", "media_root", "viewer_media_root", "python",
          "code_root", "trip_id", "server_id", "epoch"}


def run_command(argv):
    return subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)


def checked(argv, runner=run_command):
    if runner(argv).returncode:
        raise ValueError("system command failed; inspect the private service log")


def private_path(path: Path, *, directory=False):
    if not path.is_absolute() or path.resolve() != path or path.resolve().is_relative_to(PROJECT_ROOT.parent):
        raise ValueError("service data must be absolute, outside Git and not a symlink")
    if path.exists():
        if path.is_dir() != directory or path.stat().st_mode & 0o077:
            raise ValueError("service data must have private permissions")
    elif directory or not path.parent.is_dir():
        raise ValueError("required service directory is missing")
    return path.resolve()


def load_config(root: Path) -> dict:
    private_path(root, directory=True)
    path = private_path(root / "config.json")
    data = json.loads(path.read_text())
    if set(data) != FIELDS:
        raise ValueError("configuration fields do not match M2c")
    for key in ("trip_id", "server_id", "epoch"):
        RevisionStore._uuid(data[key])
    for key in ("metadata_db", "auth_db", "media_db"):
        data[key] = private_path(Path(data[key]))
        if not data[key].is_file():
            raise ValueError("existing database required; empty replacement is forbidden")
    for key in ("media_root", "viewer_media_root"):
        data[key] = private_path(Path(data[key]), directory=True)
    paths = [data[key] for key in ("metadata_db", "auth_db", "media_db", "media_root", "viewer_media_root")]
    if len(set(paths)) != len(paths) or any(
        a.is_relative_to(b) or b.is_relative_to(a)
        for i, a in enumerate(paths) for b in paths[i + 1:]
    ):
        raise ValueError("database, originals and viewer paths must be separate")
    python = Path(data["python"])
    if not python.is_absolute() or not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError("existing isolated Python required")
    # A /tmp venv is an acceptance fixture, not a persistent deployment.
    if python.resolve().is_relative_to(Path("/private/tmp")) or str(python).startswith(("/tmp/", "/private/tmp/")):
        raise ValueError("production Python must not live in temporary storage")
    data["python"] = python
    code_root = Path(data["code_root"])
    if not code_root.is_absolute() or code_root.resolve() != code_root or not (code_root / "scripts/camino_service_control.py").is_file():
        raise ValueError("explicit deployed code checkout required")
    data["code_root"] = code_root
    connection = readonly(data["metadata_db"])
    try:
        row = connection.execute("SELECT server_id,epoch FROM meta WHERE singleton=1").fetchone()
        if row != (data["server_id"], data["epoch"]):
            raise ValueError("server identity differs; do not recreate or rotate the server")
        if not connection.execute("SELECT 1 FROM trips WHERE id=?", (data["trip_id"],)).fetchone():
            raise ValueError("explicitly selected trip is absent")
    finally:
        connection.close()
    for path in (root / "readers.sqlite", root / "service.log"):
        private_path(path)
        if path.resolve() in paths:
            raise ValueError("reader credentials must be separate")
    return data


def target():
    return f"gui/{os.getuid()}/{LABEL}"


def loaded(runner=run_command):
    return runner(["/bin/launchctl", "print", target()]).returncode == 0


def require_private_network(runner=run_command):
    # An existing public proxy could expose even a newly started loopback listener.
    from scripts.camino_c02b_t043_control import _funnel_enabled
    for kind in ("serve", "funnel"):
        result = runner([TAILSCALE, kind, "status", "--json"])
        if result.returncode:
            raise ValueError("cannot verify private proxy state")
        value = json.loads(result.stdout)
        if not isinstance(value, dict) or _funnel_enabled(value):
            raise ValueError("public Funnel is forbidden for Camino")


def viewer_granted(config: dict) -> bool:
    connection = readonly(config["metadata_db"])
    try:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='viewer_permissions'").fetchone():
            return False
        row = connection.execute("SELECT enabled FROM viewer_permissions WHERE trip_id=?", (config["trip_id"],)).fetchone()
        return row is not None and row[0] == 1
    finally:
        connection.close()


def service_plist(root: Path, config: dict) -> bytes:
    return plistlib.dumps({
        "Label": LABEL,
        "ProgramArguments": [str(config["python"]), str(config["code_root"] / "scripts/camino_service_control.py"), "run", "--root", str(root)],
        "WorkingDirectory": str(config["code_root"]),
        "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 30,
        "ExitTimeOut": 330, "Umask": 0o077,
        "StandardOutPath": str(root / "service.log"),
        "StandardErrorPath": str(root / "service.log"),
        # The macOS Tailscale app selects CLI mode only with a terminal marker.
        "EnvironmentVariables": {"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin", "TERM": "dumb"},
    }, sort_keys=True)


def verify_plist(root: Path, config: dict, agents: Path):
    path = agents / (LABEL + ".plist")
    if path.is_symlink() or path.read_bytes() != service_plist(root, config):
        raise ValueError("LaunchAgent is not the exact owned service definition")
    return path


def loaded_definition_matches(output: str, path: Path) -> bool:
    return any(line.strip() == "path = " + str(path) for line in output.splitlines())


@contextmanager
def offline(config: dict, runner=run_command):
    if loaded(runner):
        raise ValueError("stop the managed service before changing configuration")
    # Older C05b binaries do not participate in the new lock. Refuse open DBs too.
    for key in ("metadata_db", "auth_db", "media_db"):
        result = runner(["/usr/sbin/lsof", "-t", "--", str(config[key])])
        if result.returncode != 1 or result.stdout.strip():
            raise ValueError("database is open or writer check failed; stop the old service")
    with database_lock(config["metadata_db"]):
        yield


def prepare_metadata(config: dict):
    snapshot_before_upgrade(config["metadata_db"], config["metadata_db"].parent / "pre-upgrade-snapshots", SCHEMA_VERSION)
    return RevisionStore(config["metadata_db"])


def active_reader(root: Path) -> str | None:
    """Read only owned credential files; revoked copies remain preserved, never reused."""
    path = private_path(root / "readers.sqlite")
    connection = readonly(path)
    try:
        digests = {row[0] for row in connection.execute(
            "SELECT token_sha256 FROM owner_tokens WHERE revoked_at IS NULL")}
    finally:
        connection.close()
    for path in sorted(root.glob("reader-token-*.txt")):
        token = private_path(path).read_text()
        if hashlib.sha256(token.encode()).hexdigest() in digests:
            return token
    return None


def control(action: str, root: Path = ROOT, *, runner=run_command, agents: Path = LAUNCH_AGENTS):
    if action == "status" and not (root / "config.json").exists():
        return {"configured": False, "live_checked": False}
    config = load_config(root)
    if action == "status":
        result = runner(["/bin/launchctl", "print", target()])
        owned = False
        try:
            path = verify_plist(root, config, agents)
            owned = result.returncode != 0 or loaded_definition_matches(result.stdout, path)
        except (OSError, ValueError):
            pass
        return {"configured": True, "owned_definition": owned, "loaded": result.returncode == 0,
                "viewer_granted": viewer_granted(config),
                "running": owned and result.returncode == 0 and "state = running" in result.stdout,
                "https_checked": False, "data_delivery_checked": False}
    if action == "install":
        with offline(config, runner):
            checked([str(config["python"]), "-c", "import fastapi, uvicorn, httpx"], runner)
            agents.mkdir(parents=True, exist_ok=True)
            path = agents / (LABEL + ".plist")
            if path.exists():
                expected = service_plist(root, config)
                legacy = plistlib.loads(expected)
                legacy["EnvironmentVariables"].pop("TERM")
                if not path.is_symlink() and path.read_bytes() == plistlib.dumps(legacy, sort_keys=True):
                    # Only our exact pre-TERM definition is eligible. Preserve it.
                    private_write(root / "launchagent-before-term.plist", path.read_bytes())
                    checked(["/bin/launchctl", "disable", target()], runner)
                    staged = agents / (LABEL + ".term-update.plist")
                    private_write(staged, expected)
                    os.replace(staged, path)
                else:
                    verify_plist(root, config, agents)
            # Disable before creating the auto-login definition: install does not start it.
            checked(["/bin/launchctl", "disable", target()], runner)
            if not path.exists():
                private_write(path, service_plist(root, config))
            if not (root / "service.log").exists():
                private_write(root / "service.log", b"")
            private_path(root / "service.log")
        return {"installed": True, "started": False, "network_changed": False}
    if action == "stop":
        path = verify_plist(root, config, agents)
        current = runner(["/bin/launchctl", "print", target()])
        if current.returncode == 0 and not loaded_definition_matches(current.stdout, path):
            raise ValueError("loaded label is not owned by this service definition")
        checked(["/bin/launchctl", "disable", target()], runner)
        if loaded(runner):
            checked(["/bin/launchctl", "bootout", target()], runner)
        return {"stop_requested": True, "loaded": loaded(runner), "data_preserved": True}
    if action == "start":
        path = verify_plist(root, config, agents)
        if loaded(runner):
            raise ValueError("service already loaded; inspect status instead of starting twice")
        require_private_network(runner)
        with offline(config, runner):
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", PORT))
            connection = readonly(config["auth_db"])
            try:
                if not connection.execute("SELECT 1 FROM owner_tokens WHERE revoked_at IS NULL").fetchone():
                    raise ValueError("owner token must be provisioned explicitly before startup")
            finally:
                connection.close()
            prepare_metadata(config)
        checked(["/bin/launchctl", "enable", target()], runner)
        checked(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(path)], runner)
        return {"start_requested": True, "https_checked": False}
    if action in ("enable-viewer", "disable-viewer"):
        with offline(config, runner):
            store = prepare_metadata(config)
            # Close first, so every partial failure is private. Original create_trip is immutable.
            store.set_viewer_permission(config["trip_id"], enabled=False)
            readers = RevocableTokenStore(root / "readers.sqlite")
            if action == "disable-viewer":
                with readers._open() as connection:
                    connection.execute("UPDATE owner_tokens SET revoked_at=COALESCE(revoked_at,datetime('now'))")
                return {"viewer_enabled": False, "readers_revoked": True}
            token = active_reader(root)
            if token is None:
                token = secrets.token_urlsafe(36)
                # Keep the secret even on partial failure; never emit it in the report.
                private_write(root / f"reader-token-{uuid4().hex}.txt", token.encode())
                readers.add(token, label="Jana read-only")
            store.set_viewer_permission(config["trip_id"], enabled=True)
        return {"viewer_enabled": True, "reader_provisioned": True, "started": False}
    if action == "copy-reader":
        token = active_reader(root)
        if token is None:
            raise ValueError("reader credential is not active")
        subprocess.run(["/usr/bin/pbcopy"], input=token, text=True, check=True, timeout=10)
        return {"copied": True, "username": "jana"}
    raise ValueError("unknown operation")


def serve(root: Path):
    config = load_config(root)
    require_private_network()
    os.umask(0o077)
    # Remove inherited acceptance/fault/viewer settings before using explicit config.
    for key in tuple(os.environ):
        if key.startswith(("CAMINO_C05A_", "CAMINO_VIEWER_")):
            os.environ.pop(key)
    for key in ("metadata_db", "auth_db", "media_db", "media_root"):
        os.environ["CAMINO_C05A_" + key.upper()] = str(config[key])
    reader_path = root / "readers.sqlite"
    if reader_path.exists() and viewer_granted(config):
        connection = readonly(reader_path)
        try:
            active = connection.execute("SELECT COUNT(*) FROM owner_tokens WHERE revoked_at IS NULL").fetchone()[0]
        finally:
            connection.close()
        if active:
            os.environ.update(CAMINO_VIEWER_ENABLED="1", CAMINO_VIEWER_AUTH_DB=str(reader_path),
                              CAMINO_VIEWER_TRIP_ID=config["trip_id"],
                              CAMINO_VIEWER_MEDIA_ROOT=str(config["viewer_media_root"]))
    from camino.server.main import main as server_main
    return server_main(["--host", "127.0.0.1", "--port", str(PORT), "--root-path", "/camino-api"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "install", "start", "stop", "enable-viewer", "disable-viewer", "copy-reader", "run"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    if args.action not in ("status", "run") and not args.confirm:
        parser.error("mutating controls require explicit --confirm")
    try:
        if args.action == "run":
            return serve(args.root)
        print(json.dumps(control(args.action, args.root), sort_keys=True))
        return 0
    except Exception as error:
        # Paths, credentials, SQL and process output never enter a public workflow report.
        print(json.dumps({"ok": False, "error": type(error).__name__,
                          "next": "Check private configuration, stopped writers and M2c runbook."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
