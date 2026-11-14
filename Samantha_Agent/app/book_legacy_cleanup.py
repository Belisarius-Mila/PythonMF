"""Explicit, preview-bound cleanup of retired book categories, with exact backups.

Never runs on startup, lookup or deployment. Transaction history is immutable.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re

from app import article_archive as archive
from app.file_persistence import atomic_create_bytes, atomic_write_json, atomic_write_text


CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
TECHNICAL_TAGS = {"obalka", "ma-obrazek"}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _encoded(data):
    return base64.b64encode(data).decode("ascii")


def _json_bytes(value, original):
    return (json.dumps(value, ensure_ascii=False, indent=2 if b"\n" in original.rstrip() else None)
            + ("\n" if original.endswith(b"\n") else "")).encode()


def _path(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Neověřená cesta při čištění kategorií.")
    return path


def _digest(plan):
    return _sha(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode())


def _summary(plan, identity):
    return {"plan_id": identity, "book_count": plan["book_count"],
            "changed_books": plan["changed_books"], "removed_labels": plan["removed_labels"],
            "removed_option_count": plan["removed_option_count"], "changed_files": len(plan["changes"]),
            "pending_requests": plan["pending_requests"], "ready": not plan["pending_requests"],
            "confirmation_required": CONFIRMATION}


@archive._serialized_archive_write
def preview_cleanup(*, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    root = Path(archive_root)
    plan = {"version": 1, "book_count": 0, "changed_books": 0, "removed_labels": [],
            "removed_option_count": 0, "pending_requests": 0, "guards": {}, "changes": []}

    def read(relative):
        path = _path(root, relative)
        data = path.read_bytes() if path.exists() else b""
        plan["guards"][relative] = _sha(data)
        return data

    def change(relative, before, after):
        if before != after:
            plan["changes"].append({"path": relative, "before": _encoded(before), "after": _encoded(after)})

    operations = read("inventory_operations.json")
    if operations:
        data = json.loads(operations)
        if data.get("version") != 1 or not isinstance(data.get("operations"), dict):
            raise ValueError("Neověřená evidence rozepsaných knih.")
        plan["pending_requests"] = sum(op.get("state") != "done" for op in data["operations"].values())
    registry = read("registry.jsonl")
    rows = registry.decode().splitlines(keepends=True)
    new_rows = []
    for line in rows:
        if not line.strip():
            new_rows.append(line)
            continue
        row = json.loads(line)
        if row.get("category") != "books":
            new_rows.append(line)
            continue
        item = archive.article_item_from_raw(row)
        metadata_path = archive.article_metadata_path(item, archive_root=root)
        relative = str(metadata_path.relative_to(root))
        original = read(relative)
        raw = json.loads(original)
        if raw.get("category") != "books" or raw.get("id") != row.get("id"):
            raise ValueError("Kniha neodpovídá registru.")
        tags = raw.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise ValueError("Neověřený formát starých kategorií.")
        clean = [tag for tag in tags if tag.casefold() in TECHNICAL_TAGS]
        removed = [tag for tag in tags if tag.casefold() not in TECHNICAL_TAGS]
        plan["book_count"] += 1
        if removed:
            plan["changed_books"] += 1
            plan["removed_labels"].extend(tag for tag in removed if tag not in plan["removed_labels"])
            raw["tags"] = clean
            change(relative, original, _json_bytes(raw, original))
        if row.get("tags", []) != clean:
            row["tags"] = clean
            new_rows.append(json.dumps(row, ensure_ascii=False) + ("\n" if line.endswith("\n") else ""))
        else:
            new_rows.append(line)
    options = read(archive.BOOK_OPTIONS_FILENAME)
    if options:
        data = json.loads(options)
        if not isinstance(data, dict):
            raise ValueError("Neověřený slovník umístění knih.")
        if "categories" in data:
            if not isinstance(data["categories"], list):
                raise ValueError("Neověřený slovník starých kategorií.")
            plan["removed_option_count"] = len(data.pop("categories"))
            change(archive.BOOK_OPTIONS_FILENAME, options, _json_bytes(data, options))
    change("registry.jsonl", registry, "".join(new_rows).encode())
    identity = _digest(plan)
    directory = root / "maintenance"
    directory.mkdir(exist_ok=True, mode=0o700)
    path = _path(root, f"maintenance/categories_{identity}.json")
    atomic_write_json(path, plan)
    path.chmod(0o600)
    return _summary(plan, identity)


def apply_cleanup(*, plan_id, confirmation, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    if confirmation != CONFIRMATION:
        raise ValueError("Hromadné čištění vyžaduje přesnou globální potvrzovací větu.")
    return _apply_cleanup(plan_id=plan_id, confirmation=confirmation, archive_root=archive_root)


@archive._serialized_archive_write
def _apply_cleanup(*, plan_id, confirmation, archive_root=archive.DEFAULT_ARCHIVE_ROOT):
    if confirmation != CONFIRMATION:
        raise ValueError("Hromadné čištění vyžaduje přesnou globální potvrzovací větu.")
    if not isinstance(plan_id, str) or not re.fullmatch(r"[0-9a-f]{64}", plan_id):
        raise ValueError("Chybí přesná identita schváleného náhledu.")
    root = Path(archive_root)
    plan = json.loads(_path(root, f"maintenance/categories_{plan_id}.json").read_bytes())
    if _digest(plan) != plan_id or plan.get("pending_requests"):
        raise ValueError("Náhled není ověřený nebo zbývá nedokončený zápis knihy.")
    state_path = _path(root, f"maintenance/categories_{plan_id}.state.json")
    state = json.loads(state_path.read_bytes()) if state_path.exists() else None
    if state and state.get("state") == "done":
        return {**_summary(plan, plan_id), "state": "done", "already_done": True}
    changes = {change["path"]: change for change in plan["changes"]}
    for relative, old_sha in plan["guards"].items():
        path = _path(root, relative)
        current = path.read_bytes() if path.exists() else b""
        allowed = {old_sha}
        if state and relative in changes:
            allowed.add(_sha(base64.b64decode(changes[relative]["after"], validate=True)))
        if _sha(current) not in allowed:
            raise ValueError("Knihovna se od náhledu změnila. Připrav nový náhled; nic se nepřepsalo.")
    backup = _path(root, f"maintenance/categories_{plan_id}_backup")
    backup.mkdir(exist_ok=True, mode=0o700)
    # Every original byte is backed up before the first live metadata mutation.
    for number, change in enumerate(plan["changes"]):
        path = backup / f"{number:03d}.bin"
        before = base64.b64decode(change["before"], validate=True)
        if path.exists():
            if path.read_bytes() != before:
                raise ValueError("Záloha schváleného čištění nesouhlasí.")
        else:
            atomic_create_bytes(path, before)
            path.chmod(0o600)
    atomic_write_json(state_path, {"plan_id": plan_id, "state": "prepared"})
    for change in plan["changes"]:
        path = _path(root, change["path"])
        after = base64.b64decode(change["after"], validate=True)
        if path.read_bytes() != after:
            atomic_write_text(path, after.decode("utf-8"))
    atomic_write_json(state_path, {"plan_id": plan_id, "state": "done"})
    return {**_summary(plan, plan_id), "state": "done", "backup_directory": str(backup)}
