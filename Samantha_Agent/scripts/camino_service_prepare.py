#!/usr/bin/env python3
"""Prepare a fixed release over the stopped C05b archive, without serving it."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import secrets
import subprocess
import sys
import tarfile
import venv
from uuid import uuid4
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from camino.server.auth import RevocableTokenStore
from camino.server.service_safety import private_write, readonly, snapshot
from scripts.camino_c05b_private_control import ControlConfig, _load_state, _validate_state_paths
from scripts import camino_service_control as service

RELEASE_PATHS = (
    "Samantha_Agent/camino/api", "Samantha_Agent/camino/domain", "Samantha_Agent/camino/server",
    "Samantha_Agent/scripts/camino_service_control.py",
    "Samantha_Agent/scripts/camino_c02b_t043_control.py",
)


def archive_evidence(state: dict) -> dict:
    """Read-only counts and hashes. No migration, private content or credentials in output."""
    db = readonly(Path(state["metadata_db"]))
    try:
        if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("metadata integrity failed")
        identity = db.execute("SELECT server_id,epoch,cursor,writer_device_id FROM meta WHERE singleton=1").fetchone()
        trip_rows = db.execute("SELECT DISTINCT trip_id FROM moments").fetchall()
        if len(trip_rows) != 1:
            raise ValueError("exactly one populated trip required; explicit selection needed")
        flags = db.execute("SELECT exports_blocked,reconciliation_required FROM meta WHERE singleton=1").fetchone()
        result = {"operations": db.execute("SELECT COUNT(*) FROM accepted_operations").fetchone()[0],
                  "moments": db.execute("SELECT COUNT(*) FROM moments").fetchone()[0],
                  "identity_sha256": hashlib.sha256(json.dumps(identity).encode()).hexdigest(),
                  "exports_blocked": bool(flags[0]), "reconciliation_required": bool(flags[1])}
    finally:
        db.close()
    db = readonly(Path(state["media_db"]))
    count, total = 0, 0
    try:
        if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("media integrity failed")
        for asset_id, receipt in db.execute("SELECT asset_id,receipt FROM verified_assets"):
            service.RevisionStore._uuid(asset_id)
            receipt = json.loads(receipt)
            path = Path(state["media_root"]) / "objects" / (asset_id + ".bin")
            if path.is_symlink() or not path.is_file() or path.stat().st_size != receipt["byte_count"]:
                raise ValueError("verified medium missing or changed")
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != receipt["sha256"]:
                    raise ValueError("verified medium hash mismatch")
            count += 1
            total += receipt["byte_count"]
        result.update(verified_assets=count, verified_bytes=total)
    finally:
        db.close()
    return result


def release_checkout(destination: Path) -> Path:
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=PROJECT_ROOT).strip():
        raise ValueError("commit and verify the exact release before preparing it")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True).strip()
    release = destination / head
    if release.exists():
        raise ValueError("release already exists; inspect it, never overwrite automatically")
    content = subprocess.check_output(["git", "archive", head, *RELEASE_PATHS], cwd=PROJECT_ROOT.parent)
    release.mkdir(parents=True, mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(content)) as archive:
        if any(not (m.isfile() or m.isdir()) for m in archive.getmembers()):
            raise ValueError("release contains unsupported file types")
        archive.extractall(release, filter="data")
    return release / "Samantha_Agent"


def prepare(*, root: Path = service.ROOT, source: ControlConfig = ControlConfig()) -> dict:
    state = _load_state(source.current_path)
    if state is None or state.get("phase") != "stopped":
        raise ValueError("the existing acceptance service must be stopped first")
    _validate_state_paths(state, source)
    config = {key: service.private_path(Path(state[key]), directory=key == "media_root")
              for key in ("metadata_db", "auth_db", "media_db", "media_root")}
    service.require_private_network()
    if root.exists():
        raise ValueError("preparation already exists; preserve it and inspect before retrying")
    # Check ownership before snapshots, credential preparation or deployment files.
    with service.offline(config):
        evidence = archive_evidence(state)
        root.mkdir(parents=True, mode=0o700)
        backups = root / "preparation-snapshots"
        for key in ("metadata_db", "auth_db", "media_db"):
            snapshot(config[key], backups / key)
        private_write(root / "archive-before.json", json.dumps(evidence, sort_keys=True).encode())
        code = release_checkout(root.parent / "Releases")
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / "bin/python"
        # A private log keeps pip diagnostics out of shared reports; no credentials in argv.
        private_write(root / "environment.log", b"")
        with (root / "environment.log").open("ab") as log:
            subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r",
                            str(code / "camino/server/requirements.txt")], stdout=log, stderr=log, check=True, timeout=300)
            subprocess.run([str(python), "-m", "pip", "check"], stdout=log, stderr=log, check=True, timeout=30)
        copies = root / "viewer-copies"
        copies.mkdir(mode=0o700)
        db = readonly(config["metadata_db"])
        try:
            server_id, epoch = db.execute("SELECT server_id,epoch FROM meta WHERE singleton=1").fetchone()
            trip_id = db.execute("SELECT DISTINCT trip_id FROM moments").fetchone()[0]
        finally:
            db.close()
        owner = RevocableTokenStore(config["auth_db"])
        if owner.active_count():
            # Preserve an existing active connection if the archived credential still matches.
            token = service.private_path(Path(state["token_path"])).read_text().strip()
            if not owner.authenticate("Bearer " + token):
                raise ValueError("active owner credential cannot be matched safely")
        else:
            token = secrets.token_urlsafe(36)
            owner.add(token, label="Camino managed owner")
        private_write(root / "owner-token.txt", token.encode())
        data = {key: str(value) for key, value in config.items()}
        data.update(viewer_media_root=str(copies), python=str(python), code_root=str(code),
                    trip_id=trip_id, server_id=server_id, epoch=epoch)
        private_write(root / "config.json", json.dumps(data, sort_keys=True).encode())
        if archive_evidence(state) != evidence:
            raise ValueError("archive changed during preparation")
        service.load_config(root)
        private_write(root / "preparation-complete.json", json.dumps(evidence, sort_keys=True).encode())
    return {"prepared": True, "installed": False, "viewer_enabled": False,
            "network_changed": False, **evidence}


def upgrade(*, root=service.ROOT, agents=service.LAUNCH_AGENTS, runner=service.run_command):
    """Switch only a stopped owned service to a new immutable, clean Git release."""
    config = service.load_config(root)
    plist = service.verify_plist(root, config, agents)
    service.require_private_network(runner)
    with service.offline(config, runner):
        before = archive_evidence(config)
        old_config = (root / "config.json").read_bytes()
        old_plist = plist.read_bytes()
        code = release_checkout(root.parent / "Releases")
        requirements = Path("camino/server/requirements.txt")
        if (code / requirements).read_bytes() != (config["code_root"] / requirements).read_bytes():
            raise ValueError("dependency changes require a separate isolated environment")
        service.checked([str(config["python"]), "-I", "-c",
            "import sys; sys.path.insert(0, " + repr(str(code)) + "); "
            "from camino.server.application import create_app; "
            "from camino.server.recovery import complete_recovery"], runner)
        receipt = root / "upgrades" / uuid4().hex
        receipt.mkdir(parents=True, mode=0o700)
        os.chmod(receipt.parent, 0o700)
        private_write(receipt / "config-before.json", old_config)
        private_write(receipt / "launchagent-before.plist", old_plist)
        for key in ("metadata_db", "auth_db", "media_db"):
            snapshot(config[key], receipt / key)
        if (root / "readers.sqlite").exists():
            snapshot(service.private_path(root / "readers.sqlite"), receipt / "readers")
        if archive_evidence(config) != before:
            raise ValueError("archive changed during upgrade preparation")
        updated = json.loads(old_config)
        updated["code_root"] = str(code)
        staged_config = receipt / "config-after.json"
        private_write(staged_config, json.dumps(updated, sort_keys=True).encode())
        # Preserve both definitions; separate create-only stage becomes the owned plist.
        definition = service.service_plist(root, {**config, "code_root": code})
        private_write(receipt / "launchagent-after.plist", definition)
        staged_plist = agents / (service.LABEL + ".upgrade-" + receipt.name + ".plist")
        private_write(staged_plist, definition)
        if service.loaded(runner) or plist.read_bytes() != old_plist or (root / "config.json").read_bytes() != old_config:
            raise ValueError("service configuration changed concurrently")
        service.checked(["/bin/launchctl", "disable", service.target()], runner)
        # If interrupted between replaces, the job stays disabled. No blind rollback;
        # both definitions and data snapshots remain in the private receipt directory.
        os.replace(staged_config, root / "config.json")
        os.replace(staged_plist, plist)
        service.load_config(root)
        service.verify_plist(root, {**config, "code_root": code}, agents)
        if archive_evidence(config) != before:
            raise ValueError("archive changed during deployment")
        private_write(receipt / "complete.json", json.dumps(before, sort_keys=True).encode())
    return {"upgraded": True, "started": False, "network_changed": False,
            "release": code.parent.name[:12], "archive_preserved": True,
            "exports_blocked": before["exports_blocked"],
            "reconciliation_required": before["reconciliation_required"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    if not args.confirm:
        parser.error("preparation requires explicit confirmation")
    os.umask(0o077)
    try:
        print(json.dumps(prepare(), sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error": type(error).__name__,
                          "next": "Inspect preserved private preparation; do not overwrite or restart blindly."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
