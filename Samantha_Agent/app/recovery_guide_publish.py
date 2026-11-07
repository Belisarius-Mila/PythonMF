"""Two individually atomic copies, durable journal, never cloud success by path.

Library only: no production targets, installation or publication on import.
The caller must supply reviewed/pinned targets and a validated candidate.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from app.file_persistence import atomic_create_text, atomic_write_json, atomic_replace_text_under_external_lock, exclusive_file_lock
from app.recovery_guide_sources import canonical_json, digest, reject_secrets


@dataclass(frozen=True)
class Target:
    path: str
    parent: str
    device: int
    inode: int
    baseline: str | None
    aliases: tuple[tuple[str, str], ...]

    @classmethod
    def pin(cls, path: Path) -> "Target":
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError("Cíl není běžný soubor.")
        parent = path.parent.resolve(strict=True)
        aliases = tuple((str(p), str(p.resolve(strict=True))) for p in (path.parent, *path.parent.parents)
                        if p.is_symlink())
        stat = parent.stat()
        return cls(str(path.absolute()), str(parent), stat.st_dev, stat.st_ino, file_hash(path), aliases)

    def check(self) -> Path:
        path = Path(self.path)
        parent = path.parent.resolve(strict=True)
        stat = parent.stat()
        aliases = tuple((str(p), str(p.resolve(strict=True))) for p in (path.parent, *path.parent.parents)
                        if p.is_symlink())
        if (str(parent), stat.st_dev, stat.st_ino, aliases) != (self.parent, self.device, self.inode, self.aliases):
            raise ValueError("Identita nebo alias cíle se změnil.")
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError("Cíl se změnil na nepovolený soubor.")
        return path


def file_hash(path: Path) -> str | None:
    return digest(path.read_bytes()) if path.exists() else None


def icloud_metadata(path: Path) -> dict:
    """Supported NSURL resource keys via system Foundation; errors are pending.

    Values are read through argv, never interpolated in executable source.
    A genuine ubiquitous parent/item is required before any first write.
    """
    script = '''ObjC.import('Foundation');
function run(argv) {
 var u = $.NSURL.fileURLWithPath(argv[0]);
 var keys = [$.NSURLIsUbiquitousItemKey, $.NSURLUbiquitousItemIsUploadedKey,
             $.NSURLUbiquitousItemIsUploadingKey, $.NSURLUbiquitousItemUploadingErrorKey];
 var v = ObjC.deepUnwrap(u.resourceValuesForKeysError($(keys), null));
 if (!v) return JSON.stringify({available:false});
 function flag(k) { var x = v[ObjC.unwrap(k)];
   return (x === true || x === 1) ? true : (x === false || x === 0) ? false : null; }
 return JSON.stringify({available:flag(keys[0]) !== null, ubiquitous:flag(keys[0]), uploaded:flag(keys[1]),
                        uploading:flag(keys[2]), upload_error:v[ObjC.unwrap(keys[3])] != null});
}'''
    try:
        # Query the approved alias destination, not the symlink inode: NSURL
        # correctly reports the symlink itself as a non-ubiquitous item.
        resolved = path.resolve(strict=True)
        result = subprocess.run(["/usr/bin/osascript", "-l", "JavaScript", "-e", script, str(resolved)],
                                capture_output=True, text=True, timeout=15, check=True)
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise ValueError("metadata")
        return value
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"available": False}


def uploaded(metadata: dict) -> bool:
    return (metadata.get("available") is True and metadata.get("ubiquitous") is True
            and metadata.get("uploaded") is True and metadata.get("uploading") is False
            and metadata.get("upload_error") is False)


def publish(candidate: str, *, validation_sha256: str, targets: tuple[Target, Target],
            state_dir: Path, request_id: str, cloud_audit: Callable[[Path], dict] = icloud_metadata) -> dict:
    """Idempotently finish the SAME candidate. Never calls a model.

    A crash after either replace is reconciled by hashes. Foreign edits stop
    recovery. If a second write fails, restore an existing first baseline only
    when it still equals our candidate. No deletion of a newly created target.
    """
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request_id):
        raise ValueError("Neplatné ID.")
    reject_secrets(candidate)
    sha = digest(candidate)
    if not candidate.strip() or sha != validation_sha256:
        raise ValueError("Kandidát nemá shodnou validaci.")
    if state_dir.is_symlink():
        raise ValueError("Stav nesmí být alias.")
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    paths = tuple(t.check() for t in targets)
    if paths[0].resolve() == paths[1].resolve():
        raise ValueError("Dva cíle musejí být odlišné soubory.")
    journal = state_dir / f"{request_id}.json"
    identity = digest(canonical_json({"candidate": sha, "targets": [asdict(t) for t in targets]}))
    with exclusive_file_lock(state_dir / "writer", timeout=0):
        if journal.is_symlink():
            raise ValueError("Žurnál nesmí být alias.")
        record = json.loads(journal.read_text()) if journal.exists() else None
        if record and record.get("identity") != identity:
            raise ValueError("ID již patří jinému kandidátu nebo cílům.")
        for target in targets:
            path = target.check()
            if file_hash(path) not in {target.baseline, sha}:
                raise ValueError("Cíl byl ručně změněn; nepřepisovat.")
        meta = cloud_audit(paths[1] if paths[1].exists() else paths[1].parent)
        if meta.get("available") is not True or meta.get("ubiquitous") is not True:
            return {"state": "attention", "reason": "iCloud identita není ověřena", "sha256": sha}
        if record is None:
            # Preserve both originals before replacing either one. Content hashes
            # make the archives immutable and reusable after interrupted prepare.
            for target in targets:
                path = target.check()
                if file_hash(path) != target.baseline:
                    raise ValueError("Cíl se změnil před přípravou.")
                if target.baseline is not None:
                    archive = state_dir / f"previous-{target.baseline}.txt"
                    old = path.read_text(encoding="utf-8")
                    if digest(old) != target.baseline:
                        raise ValueError("Neshoda archivované verze.")
                    if not archive.exists():
                        atomic_create_text(archive, old)
                    elif archive.is_symlink() or file_hash(archive) != target.baseline:
                        raise ValueError("Archiv předchozí verze není platný.")
            saved = state_dir / f"candidate-{sha}.txt"
            if not saved.exists():
                atomic_create_text(saved, candidate)
            elif saved.is_symlink() or file_hash(saved) != sha:
                raise ValueError("Neshoda uloženého kandidáta.")
            record = {"identity": identity, "sha256": sha, "state": "prepared", "request_id": request_id}
            atomic_write_json(journal, record)
        try:
            for index, target in enumerate(targets):
                path = target.check()
                observed = file_hash(path)
                if observed not in {target.baseline, sha}:
                    raise ValueError("Souběžná změna cíle.")
                if observed != sha:
                    atomic_replace_text_under_external_lock(path, candidate)
                if file_hash(path) != sha:
                    raise ValueError("Zápis neodpovídá kandidátu.")
                record["state"] = "local_saved" if index == 0 else "both_local_saved"
                atomic_write_json(journal, record)
        except (OSError, ValueError):
            first = targets[0].check()
            if file_hash(first) == sha and targets[0].baseline is not None:
                archive = state_dir / f"previous-{targets[0].baseline}.txt"
                if not archive.is_symlink() and file_hash(archive) == targets[0].baseline:
                    atomic_replace_text_under_external_lock(first, archive.read_text(encoding="utf-8"))
            record["state"] = "attention"
            atomic_write_json(journal, record)
            return record
        record["state"] = "uploaded" if uploaded(cloud_audit(paths[1])) else "pending_icloud"
        record["physical_iphone_acceptance"] = "not_verified"
        atomic_write_json(journal, record)
        return record
