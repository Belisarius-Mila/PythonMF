"""Explicit, bounded permanent removal of one film export and its working bytes."""
from __future__ import annotations

import fcntl
import json
import os
import re
import stat
from contextlib import contextmanager

from app.file_persistence import atomic_write_json
from camino.film.closed_day import _private_directory, _store_lock
from camino.film.project import FilmError, fingerprint

DELETE_CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."


@contextmanager
def _selected(editor, payload, *, deleting=False):
    from app.camino_film_editor import exact, identifier
    exact(payload, "project_id job_id" + (" plan_token confirmation" if deleting else ""))
    if deleting and payload["confirmation"] != DELETE_CONFIRMATION:
        raise FilmError("Trvalé smazání vyžaduje přesnou potvrzovací větu globální brzdy.")
    if deleting and (not isinstance(payload["plan_token"], str) or not re.fullmatch(r"[a-f0-9]{64}", payload["plan_token"])):
        raise FilmError("Neplatné potvrzení vybrané varianty.")
    try:
        project_id, job_id = identifier(payload["project_id"]), identifier(payload["job_id"])
    except ValueError:
        raise FilmError("Neplatný identifikátor vybrané varianty.") from None
    folder, manifest = editor.inputs(project_id)
    with _store_lock(editor.store.root):
        # The same lock is held for the entire render, including status writes.
        worker = os.open(folder / ".render-worker", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(worker, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise FilmError("Projekt právě vytváří video. Po dokončení zkus smazání znovu.") from None
            root = folder / "jobs"
            if not root.is_dir():
                raise FilmError("Vybraná varianta neexistuje.")
            _private_directory(root)
            directory = root / job_id
            if not directory.is_dir() or directory.is_symlink():
                raise FilmError("Vybraná varianta nemá bezpečný adresář.")
            _private_directory(directory)
            spec = editor.store._read(directory / "request.json")
            exact(spec, "project_id request_id revision profile range manifest_sha256 edit_sha256")
            state = editor.store._read(directory / "status.json") if (directory / "status.json").exists() else {"state": "queued"}
            if (spec.get("project_id") != project_id or spec.get("request_id") != job_id
                    or "source_asset_id" in spec or spec.get("profile") not in ("preview", "final")
                    or spec.get("manifest_sha256") != fingerprint(manifest)
                    or spec.get("edit_sha256") != fingerprint(editor.job_edit(folder, manifest, spec))):
                raise FilmError("Smazat lze jen filmový export vybraného projektu.")
            if state.get("state") not in ("ready", "failed", "interrupted", "rendering", "delete_pending", "deleted"):
                raise FilmError("Varianta ještě čeká ve frontě. Počkej na dokončení.")
            yield directory, spec, state
        finally:
            os.close(worker)


def _inventory(directory):
    """Only generated, flat attempt directories; never follow links or mounts."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    entries = []
    root = os.open(directory, flags)
    try:
        device = os.fstat(root).st_dev
        for name in sorted(os.listdir(root)):
            if name in ("request.json", "status.json", "status.json.lock"):
                info = os.stat(name, dir_fd=root, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_dev != device:
                    raise FilmError("Metadata varianty nemají bezpečný soubor.")
                if name == "status.json.lock" and info.st_size != 0:
                    raise FilmError("Zámek varianty obsahuje neočekávaná data.")
                continue
            if not re.fullmatch(r"attempt-[a-f0-9]{32}", name):
                raise FilmError("Varianta obsahuje neznámé pracovní soubory; smazání je zastavené.")
            child = os.open(name, flags, dir_fd=root)
            try:
                info = os.fstat(child)
                if info.st_dev != device:
                    raise FilmError("Pracovní adresář leží na jiném zařízení.")
                entries.append({"path": name, "kind": "directory", "device": device, "inode": info.st_ino})
                for filename in sorted(os.listdir(child)):
                    info = os.stat(filename, dir_fd=child, follow_symlinks=False)
                    if not stat.S_ISREG(info.st_mode) or info.st_dev != device or info.st_nlink != 1:
                        raise FilmError("Varianta obsahuje odkaz nebo neznámý soubor; smazání je zastavené.")
                    entries.append({"path": name + "/" + filename, "kind": "file", "device": device,
                                    "inode": info.st_ino, "bytes": info.st_size, "mtime_ns": info.st_mtime_ns})
            finally:
                os.close(child)
        return entries
    finally:
        os.close(root)


def _plan(directory, spec, state):
    entries = _inventory(directory)
    if state["state"] in ("delete_pending", "deleted"):
        plan = state.get("deletion")
        if not isinstance(plan, dict) or plan.get("request_sha256") != fingerprint(spec):
            raise FilmError("Záznam mazání není platný.")
        if state["state"] == "deleted":
            if entries:
                raise FilmError("U smazané varianty jsou neočekávaná data.")
            return plan, entries
        if plan.get("token") != fingerprint({k: v for k, v in plan.items() if k != "token"}):
            raise FilmError("Potvrzený plán mazání se změnil.")
        expected = {item["path"]: item for item in plan["entries"]}
        if any(expected.get(item["path"]) != item for item in entries):
            raise FilmError("Zbývající soubory neodpovídají potvrzenému mazání.")
        return plan, entries
    plan = {"request_sha256": fingerprint(spec), "project_id": spec["project_id"], "job_id": spec["request_id"],
            "entries": entries, "bytes": sum(e.get("bytes", 0) for e in entries),
            "file_count": sum(e["kind"] == "file" for e in entries)}
    plan["token"] = fingerprint(plan)
    # ClosedDayStore._read rejects JSON above 1 MB. Never persist a recovery
    # record that the normal editor could not read after an interruption.
    pending = {"state": "delete_pending", "progress": 0, "deletion": plan}
    if len((json.dumps(pending, ensure_ascii=False, indent=2) + "\n").encode()) > 950_000:
        raise FilmError("Varianta má příliš mnoho pracovních souborů pro bezpečné mazání v editoru.")
    return plan, entries


def deletion_plan(editor, payload):
    with _selected(editor, payload) as (directory, spec, state):
        plan, entries = _plan(directory, spec, state)
        return {"ok": True, "project_id": spec["project_id"], "job_id": spec["request_id"],
                "plan_token": plan["token"], "profile": spec["profile"], "revision": spec["revision"],
                "range": spec["range"], "bytes": sum(e.get("bytes", 0) for e in entries),
                "file_count": sum(e["kind"] == "file" for e in entries),
                "already_deleted": state["state"] == "deleted", "confirmation_text": DELETE_CONFIRMATION}


def delete_export(editor, payload):
    with _selected(editor, payload, deleting=True) as (directory, spec, state):
        plan, entries = _plan(directory, spec, state)
        if payload["plan_token"] != plan["token"]:
            raise FilmError("Soubory varianty se změnily. Znovu zobraz a potvrď smazání.")
        if state["state"] == "deleted":
            return {"ok": True, "deleted": True, "already_deleted": True, "deleted_bytes": plan["bytes"]}
        # Persist only file identities, never media copies. A crash blocks delivery
        # and rendering; the same exact request can finish the remaining files.
        atomic_write_json(directory / "status.json", {"state": "delete_pending", "progress": 0, "deletion": plan})
        root = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            by_path = {item["path"]: item for item in entries}
            for item in entries:
                if item["kind"] != "directory":
                    continue
                name = item["path"]
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
                try:
                    info = os.fstat(child)
                    if (info.st_dev, info.st_ino) != (item["device"], item["inode"]):
                        raise FilmError("Pracovní adresář se během mazání změnil.")
                    names = os.listdir(child)
                    for filename in names:
                        expected = by_path.get(name + "/" + filename)
                        info = os.stat(filename, dir_fd=child, follow_symlinks=False)
                        if (not expected or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                                or (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) !=
                                (expected["device"], expected["inode"], expected["bytes"], expected["mtime_ns"])):
                            raise FilmError("Soubor se během mazání změnil; pokračování je zastavené.")
                        os.unlink(filename, dir_fd=child)
                    os.fsync(child)
                finally:
                    os.close(child)
                # Do not remove a replacement directory swapped into this name.
                info = os.stat(name, dir_fd=root, follow_symlinks=False)
                if (info.st_dev, info.st_ino) != (item["device"], item["inode"]):
                    raise FilmError("Pracovní adresář se během mazání změnil.")
                os.rmdir(name, dir_fd=root)
            os.fsync(root)
        finally:
            os.close(root)
        # Minimal metadata prevents old retry IDs from resurrecting deleted bytes.
        receipt = {k: plan[k] for k in ("token", "bytes", "file_count", "request_sha256")}
        atomic_write_json(directory / "status.json", {"state": "deleted", "progress": 0, "deletion": receipt})
        return {"ok": True, "deleted": True, "already_deleted": False, "deleted_bytes": plan["bytes"]}
