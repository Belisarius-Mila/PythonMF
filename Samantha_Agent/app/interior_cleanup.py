"""Confirmed removal of one source and its app-owned, unshared image bytes."""
from __future__ import annotations

import copy
import os
import re
import stat
from pathlib import Path

from app.interior_atelier import (
    AtelierConflict, AtelierError, REQUEST_RE, _fingerprint, _hash, _identifier, _now, _safe_path,
)
from app.work_repository import RepositoryMutation
from app.interior_room_basis import room_basis, detach_room_plan

DELETE_CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
BLOCKING = {"queued", "running", "delivery_unknown", "result_ready"}


def _jobs(room, asset_id):
    result = []
    for job_id, job in room.get("ai_requests", {}).items():
        draft = job.get("context", {}).get("draft", {})
        outputs = job.get("variant_ids", []) or [job.get("variant_id", "")]
        if (job.get("context", {}).get("room_basis", {}).get("plan_source_id") == asset_id
                or asset_id in draft.get("source_ids", []) or draft.get("image_source_id") == asset_id
                or any(room["variants"].get(v, {}).get("image_source_id") == asset_id for v in outputs)):
            if job["status"] in BLOCKING:
                raise AtelierConflict("Podklad používá neukončený AI požadavek. Nejprve ověř jeho původní výsledek.")
            result.append(_identifier(job_id))
    return sorted(result)


def _file(store, relative):
    path = _safe_path(store.root / relative)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or not 0 <= info.st_size <= 40 * 1024 * 1024):
            raise AtelierError("Pracovní soubor nemá bezpečný formát pro smazání.")
        raw = handle.read(info.st_size + 1)
    if len(raw) != info.st_size:
        raise AtelierConflict("Soubor se změnil; znovu zobraz náhled smazání.")
    return {"path": relative, "bytes": info.st_size, "sha256": _hash(raw),
            "device": info.st_dev, "inode": info.st_ino, "mtime_ns": info.st_mtime_ns}


def _live_objects(data):
    return {part["name"] for project in data["projects"].values()
            for room in project["rooms"].values() for source in room["sources"].values()
            for part in source["files"].values()}


def _plan(store, data, project_id, room_id, asset_id):
    _, room = store._room(data, project_id, room_id)
    source = room["sources"].get(_identifier(asset_id))
    if source is None:
        raise AtelierError("Podklad už není v této místnosti.")
    if any(d["status"] == "pending" for d in data.get("source_deletions", {}).values()):
        raise AtelierConflict("Nejprve dokonči již potvrzené smazání podkladu.")
    jobs = _jobs(room, asset_id)
    other = copy.deepcopy(data)
    del store._room(other, project_id, room_id)[1]["sources"][asset_id]
    shared = _live_objects(other)
    files = []
    shared_count = 0
    for part in source["files"].values():
        name = part["name"]
        if not re.fullmatch(r"[a-f0-9]{64}\.(original|preview|thumbnail)", name):
            raise AtelierError("Podklad nemá bezpečnou identitu souboru.")
        entry = _file(store, "objects/" + name)
        if entry and entry["sha256"] != part["sha256"]:
            raise AtelierConflict("Obsah podkladu se změnil; smazání je zastavené.")
        if name in shared:
            shared_count += 1
        elif entry:
            files.append(entry)
    for job_id in jobs:
        folder = _safe_path(store.root / "ai_inputs" / job_id)
        if not folder.exists():
            continue
        if not folder.is_dir():
            raise AtelierError("Pracovní kopie požadavku nemají bezpečný adresář.")
        for path in sorted(folder.iterdir()):
            if not re.fullmatch(r"input_[1-6]\.png|result\.json(?:\.lock)?", path.name):
                raise AtelierError("Požadavek obsahuje neznámé pracovní soubory; smazání je zastavené.")
            entry = _file(store, f"ai_inputs/{job_id}/{path.name}")
            if entry:
                files.append(entry)
    if len(files) > 4096:
        raise AtelierError("Podklad má příliš mnoho pracovních kopií pro jediné smazání.")
    # The full manifest pins references, revisions and job states while the user confirms.
    token = _fingerprint({"state": data, "files": files, "asset_id": asset_id,
                          "project_id": project_id, "room_id": room_id})
    affected = lambda item: asset_id in item.get("source_ids", []) or item.get("image_source_id") == asset_id
    return {"plan_token": token, "asset_id": asset_id, "project_id": project_id, "room_id": room_id,
            "room_plan": room_basis(room)["plan_source_id"] == asset_id,
            "title": source["title"], "bytes": sum(f["bytes"] for f in files), "file_count": len(files),
            "shared_file_count": shared_count, "variant_count": sum(affected(v) for v in room["variants"].values()),
            "draft_count": sum(affected(d) for d in room["drafts"].values()), "files": files, "jobs": jobs}


def preview_source_deletion(store, project_id, room_id, asset_id):
    plan = _plan(store, store._read(), project_id, room_id, asset_id)
    return {"ok": True, **{k: v for k, v in plan.items() if k not in {"files", "jobs"}},
            "confirmation_text": DELETE_CONFIRMATION}


def _detach(record, asset_id):
    changed = asset_id in record.get("source_ids", []) or record.get("image_source_id") == asset_id
    record["source_ids"] = [s for s in record.get("source_ids", []) if s != asset_id]
    if record.get("image_source_id") == asset_id:
        record.update(image_source_id="", annotations=[])
    if changed and "revision" in record:
        record["revision"] += 1


def pending_source_deletions(data, project_id, room_id):
    return [{k: d[k] for k in ("request_id", "plan_token", "asset_id", "title", "status", "bytes")} |
            {"confirmation_text": DELETE_CONFIRMATION}
            for d in data.get("source_deletions", {}).values()
            if d["project_id"] == project_id and d["room_id"] == room_id and d["status"] == "pending"]


def validate_delete_payload(payload):
    fields = {"action", "request_id", "project_id", "room_id", "asset_id", "plan_token", "confirmation"}
    if (not isinstance(payload, dict) or set(payload) != fields or payload.get("confirmation") != DELETE_CONFIRMATION
            or not isinstance(payload.get("request_id"), str) or not REQUEST_RE.fullmatch(payload["request_id"])
            or not isinstance(payload.get("plan_token"), str) or not re.fullmatch(r"[a-f0-9]{64}", payload["plan_token"])):
        raise AtelierError("Trvalé smazání vyžaduje přesný náhled a potvrzovací větu globální brzdy.")


def delete_source(store, payload):
    validate_delete_payload(payload)
    with store.media_lock():
        return _delete_source_locked(store, payload)


def _delete_source_locked(store, payload):
    request_id = payload["request_id"]
    fingerprint = _fingerprint(payload)

    def claim(data):
        existing = data.get("source_deletions", {}).get(request_id)
        if existing:
            if existing["fingerprint"] != fingerprint:
                raise AtelierConflict("Stejné potvrzení už patří jinému smazání.")
            return RepositoryMutation(data, changed=False)
        plan = _plan(store, data, payload["project_id"], payload["room_id"], payload["asset_id"])
        if plan["plan_token"] != payload["plan_token"]:
            raise AtelierConflict("Podklady nebo návrhy se změnily. Znovu zobraz a potvrď rozsah smazání.")
        _, room = store._room(data, payload["project_id"], payload["room_id"])
        asset_id = payload["asset_id"]
        del room["sources"][asset_id]
        detach_room_plan(room, asset_id)
        for record in (*room["variants"].values(), *room["drafts"].values()):
            _detach(record, asset_id)
        for job_id in plan["jobs"]:
            job = room["ai_requests"][job_id]
            job["source_cleanup"] = True
            _detach(job.get("context", {}).get("draft", {}), asset_id)
            basis = job.get("context", {}).get("room_basis", {})
            if basis.get("plan_source_id") == asset_id:
                basis.update(plan_source_id="", plan_image_number=None)
        room["updated_at"] = _now()
        # Durable intent precedes unlink. No image copy is kept in this receipt.
        data.setdefault("source_deletions", {})[request_id] = {
            **plan, "request_id": request_id, "fingerprint": fingerprint, "status": "pending",
            "deleted_bytes": 0, "deleted_files": 0, "created_at": _now()}
        return RepositoryMutation(data)

    store.repository.transact(claim)

    def finish(data):
        deletion = data["source_deletions"][request_id]
        if deletion["status"] == "completed":
            return RepositoryMutation(data, {"ok": True, "deleted_bytes": deletion["deleted_bytes"],
                "deleted_files": deletion["deleted_files"], "already_deleted": True}, changed=False)
        live = _live_objects(data)
        # Validate every remaining file before unlinking the first one.
        remaining = []
        for entry in deletion["files"]:
            if entry["path"].startswith("objects/") and Path(entry["path"]).name in live:
                continue
            current = _file(store, entry["path"])
            if current is not None and current != entry:
                raise AtelierConflict("Pracovní soubor se změnil. Smazání nepokračuje; ověř podklady.")
            if current is not None:
                remaining.append(entry)
        for entry in remaining:
            path = _safe_path(store.root / entry["path"])
            parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if (not stat.S_ISREG(current.st_mode) or current.st_nlink != 1
                        or (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
                        != (entry["device"], entry["inode"], entry["bytes"], entry["mtime_ns"])):
                    raise AtelierConflict("Soubor se během mazání změnil; další mazání je zastavené.")
                os.unlink(path.name, dir_fd=parent)
                os.fsync(parent)
            finally:
                os.close(parent)
        # Missing planned files include unlink completed before an interrupted JSON commit.
        deleted = [e for e in deletion["files"] if not (store.root / e["path"]).exists()]
        for job_id in deletion["jobs"]:
            path = _safe_path(store.root / "ai_inputs" / job_id)
            if path.exists() and not any(path.iterdir()):
                path.rmdir()
        deletion.update(status="completed", deleted_bytes=sum(e["bytes"] for e in deleted),
                        deleted_files=len(deleted), completed_at=_now())
        deletion.pop("files")
        deletion.pop("jobs")
        return RepositoryMutation(data, {"ok": True, "deleted_bytes": deletion["deleted_bytes"],
            "deleted_files": deletion["deleted_files"], "already_deleted": False})

    return store.repository.transact(finish).result
