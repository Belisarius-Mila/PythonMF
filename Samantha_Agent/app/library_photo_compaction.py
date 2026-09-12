"""Reviewed, confirmed compaction of existing library image attachments.

Preparation writes only a separate private review directory. Apply is guarded by
the global safety phrase, checks the exact source snapshot, and retains verified
originals for rollback. PDFs and article text are never changed.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.article_archive import DEFAULT_ARCHIVE_ROOT, update_registry
from app.file_persistence import _atomic_write_bytes_unlocked, atomic_write_json, exclusive_file_lock
from app.library_images import (
    LIBRARY_PHOTO_STORAGE_POLICY,
    MAX_LIBRARY_PHOTO_BYTES, MAX_LIBRARY_THUMB_BYTES,
    prepare_library_photo, prepare_library_thumbnail,
)

COMPACTION_CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
POLICY = LIBRARY_PHOTO_STORAGE_POLICY
DEFAULT_REVIEW_ROOT = DEFAULT_ARCHIVE_ROOT.parent / "library_photo_compaction"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _path(root: Path, relative: str, *, exists: bool = True) -> Path:
    value = Path(relative)
    if value.is_absolute() or ".." in value.parts or not relative:
        raise ValueError("Neplatná cesta v plánu zmenšení.")
    target = (root / value).resolve(strict=exists)
    if root.resolve() not in target.parents:
        raise ValueError("Soubor zmenšení je mimo povolený adresář.")
    return target


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_sources(plan: dict[str, Any], root: Path) -> None:
    for relative, expected in plan["sources"].items():
        if _sha(_path(root, relative).read_bytes()) != expected["sha256"]:
            raise ValueError("Knihovna se od přípravy změnila. Připrav nový plán.")
    metadata_files = sorted(str(p.relative_to(root)) for p in (root / "articles").glob("*/metadata.json"))
    if metadata_files != plan["metadata_files"]:
        raise ValueError("V knihovně přibyly nebo ubyly karty. Připrav nový plán.")


def prepare_library_photo_compaction(
    *, archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    review_root: Path = DEFAULT_REVIEW_ROOT,
) -> dict[str, Any]:
    """Prepare private review JPEGs and a hashed plan; never modify the archive."""
    root = Path(archive_root).resolve(strict=True)
    review = Path(review_root).resolve()
    if review == root or root in review.parents:
        raise ValueError("Příprava a záloha musí být mimo aktivní archiv.")
    plan_dir = review / (datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8])
    plan_dir.mkdir(parents=True, mode=0o700)
    (plan_dir / "prepared").mkdir()
    plan: dict[str, Any] = {"schema": 1, "policy": POLICY, "archive_root": str(root),
                            "sources": {}, "metadata_files": [], "items": [], "before_bytes": 0, "after_bytes": 0}

    def capture(relative: str) -> bytes:
        raw = _path(root, relative).read_bytes()
        plan["sources"][relative] = {"sha256": _sha(raw), "bytes": len(raw)}
        return raw

    registry_rows = [json.loads(line) for line in capture("registry.jsonl").decode("utf-8").splitlines() if line.strip()]
    registry = {entry["id"]: entry for entry in registry_rows}
    if len(registry) != len(registry_rows):
        raise ValueError("Registr obsahuje duplicitní karty; nejdřív je potřeba kontrola archivu.")
    image_owners: dict[str, tuple[str, str]] = {}
    for metadata_path in sorted((root / "articles").glob("*/metadata.json")):
        relative = str(metadata_path.relative_to(root))
        plan["metadata_files"].append(relative)
        metadata = json.loads(capture(relative))
        if registry.get(metadata.get("id")) != metadata:
            raise ValueError("Metadata karty a registr nesouhlasí; nejdřív je potřeba kontrola archivu.")
        for attachment in metadata.get("attachments", []):
            if attachment.get("kind") != "image":
                continue
            sources = sorted(set(str(attachment.get(key, "")) for key in ("original_file", "readable_file", "thumb_file")))
            owner = (relative, str(attachment.get("id", "")))
            attachment_root = (metadata_path.parent / "attachments").resolve()
            for name in sources:
                if attachment_root not in _path(root, name).parents:
                    raise ValueError("Soubor přílohy není v adresáři příloh její karty.")
                if name in image_owners and image_owners[name] != owner:
                    raise ValueError("Více příloh sdílí stejný soubor; vyžadují samostatnou kontrolu.")
                image_owners[name] = owner
            source_bytes = {name: capture(name) for name in sources}
            if (attachment.get("storage_policy") == POLICY
                    and attachment["original_file"] == attachment["readable_file"]
                    and len(source_bytes[attachment["original_file"]]) <= MAX_LIBRARY_PHOTO_BYTES
                    and len(source_bytes[attachment["thumb_file"]]) <= MAX_LIBRARY_THUMB_BYTES):
                continue
            attachment_id = str(attachment["id"])
            if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,128}", attachment_id):
                raise ValueError("Příloha má neplatný identifikátor.")
            main = prepare_library_photo(source_bytes[attachment["original_file"]])
            thumb = prepare_library_thumbnail(main)
            number = len(plan["items"]) + 1
            prepared_main, prepared_thumb = f"prepared/{number:03d}.jpg", f"prepared/{number:03d}-thumb.jpg"
            (plan_dir / prepared_main).write_bytes(main)
            (plan_dir / prepared_thumb).write_bytes(thumb)
            target_base = metadata_path.parent.relative_to(root) / "attachments" / "compact"
            main_file, thumb_file = str(target_base / f"{attachment_id}.jpg"), str(target_base / f"{attachment_id}-thumb.jpg")
            before = sum(len(raw) for raw in source_bytes.values())
            changes = {"original_file": main_file, "readable_file": main_file, "thumb_file": thumb_file,
                       "mime_type": "image/jpeg", "size_bytes": len(main), "readable_size_bytes": len(main),
                       "thumb_size_bytes": len(thumb), "stored_size_bytes": len(main) + len(thumb), "storage_policy": POLICY}
            plan["items"].append({"metadata_file": relative, "attachment_id": attachment_id,
                                  "category": metadata.get("category", "other"), "role": attachment.get("role", ""),
                                  "old_files": sources, "changes": changes, "before_bytes": before,
                                  "prepared": [{"file": prepared_main, "target": main_file, "sha256": _sha(main)},
                                               {"file": prepared_thumb, "target": thumb_file, "sha256": _sha(thumb)}]})
            plan["before_bytes"] += before
            plan["after_bytes"] += len(main) + len(thumb)
    if len(plan["metadata_files"]) != len(registry):
        raise ValueError("Počet karet v registru a archivu nesouhlasí.")
    _verify_sources(plan, root)
    atomic_write_json(plan_dir / "plan.json", plan)
    return {"ok": True, "state": "prepared", "archive_writes": False, "plan_dir": str(plan_dir),
            "image_count": len(plan["items"]), "before_bytes": plan["before_bytes"], "after_bytes": plan["after_bytes"],
            "confirmation_text": COMPACTION_CONFIRMATION}


def _confirmed(user_confirmed: bool, confirmation_text: str) -> None:
    if not user_confirmed or confirmation_text.strip() != COMPACTION_CONFIRMATION:
        raise ValueError(f"Hromadné zmenšení vyžaduje: {COMPACTION_CONFIRMATION}")


def _load_plan(plan_dir: Path, archive_root: Path) -> tuple[Path, Path, dict[str, Any]]:
    directory, root = Path(plan_dir).resolve(strict=True), Path(archive_root).resolve(strict=True)
    plan = _json(directory / "plan.json")
    if plan.get("schema") != 1 or plan.get("policy") != POLICY or plan.get("archive_root") != str(root):
        raise ValueError("Plán nepatří tomuto archivu nebo verzi zmenšení.")
    if root == directory or root in directory.parents:
        raise ValueError("Plán nesmí být uvnitř aktivního archivu.")
    return directory, root, plan


def _restore_backup(directory: Path, root: Path, plan: dict[str, Any]) -> None:
    for relative, expected in plan["sources"].items():
        raw = _path(directory / "backup", relative).read_bytes()
        if _sha(raw) != expected["sha256"]:
            raise ValueError("Záloha nesouhlasí s plánem; obnova byla zastavena.")
    for relative in plan["sources"]:
        _atomic_write_bytes_unlocked(_path(root, relative, exists=False), _path(directory / "backup", relative).read_bytes())
    for item in plan["items"]:
        for prepared in item["prepared"]:
            target = _path(root, prepared["target"], exists=False)
            if target.is_file() and prepared["target"] not in plan["sources"]:
                target.unlink()


def apply_library_photo_compaction(
    *, plan_dir: Path, archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False, confirmation_text: str = "",
) -> dict[str, Any]:
    """Apply an unchanged reviewed plan; keep one verified private rollback copy."""
    _confirmed(user_confirmed, confirmation_text)
    directory, root, plan = _load_plan(plan_dir, archive_root)
    receipt_path = directory / "receipt.json"
    with exclusive_file_lock(root / ".archive-write", timeout=30):
        if receipt_path.exists():
            previous = _json(receipt_path)
            if previous.get("state") == "applied":
                return {**previous, "replayed": True}
            raise ValueError("Plán už byl spuštěn. Zkontroluj jeho účtenku a případnou obnovu.")
        _verify_sources(plan, root)
        for item in plan["items"]:
            for prepared in item["prepared"]:
                if _sha(_path(directory, prepared["file"]).read_bytes()) != prepared["sha256"]:
                    raise ValueError("Připravená fotografie byla změněna.")
                if _path(root, prepared["target"], exists=False).exists():
                    raise ValueError("Cílový soubor už existuje; nic se nepřepisuje.")
        backup = directory / "backup"
        backup.mkdir(mode=0o700)
        for relative in plan["sources"]:
            target = _path(backup, relative, exists=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write_bytes_unlocked(target, _path(root, relative).read_bytes())
            if _sha(target.read_bytes()) != plan["sources"][relative]["sha256"]:
                raise ValueError("Zálohu se nepodařilo ověřit.")
        atomic_write_json(receipt_path, {"state": "applying", "backup_verified": True})
        try:
            updates: dict[str, dict[str, Any]] = {}
            for item in plan["items"]:
                for prepared in item["prepared"]:
                    _atomic_write_bytes_unlocked(_path(root, prepared["target"], exists=False), _path(directory, prepared["file"]).read_bytes())
                metadata = updates.setdefault(item["metadata_file"], _json(_path(root, item["metadata_file"])))
                attachment = next(a for a in metadata["attachments"] if a["id"] == item["attachment_id"])
                attachment.update(item["changes"])
            for relative, metadata in updates.items():
                atomic_write_json(_path(root, relative), metadata)
                update_registry(root / "registry.jsonl", metadata)
            # Verify all new bytes and metadata before removing any obsolete copy.
            for item in plan["items"]:
                for prepared in item["prepared"]:
                    if _sha(_path(root, prepared["target"]).read_bytes()) != prepared["sha256"]:
                        raise ValueError("Kontrola uložené fotografie selhala.")
                metadata = _json(_path(root, item["metadata_file"]))
                saved = next(a for a in metadata["attachments"] if a["id"] == item["attachment_id"])
                if any(saved.get(k) != v for k, v in item["changes"].items()):
                    raise ValueError("Kontrola metadat fotografie selhala.")
            new_files = {entry["target"] for item in plan["items"] for entry in item["prepared"]}
            for relative in sorted({name for item in plan["items"] for name in item["old_files"]} - new_files):
                _path(root, relative).unlink()
            result = {"ok": True, "state": "applied", "image_count": len(plan["items"]),
                      "before_bytes": plan["before_bytes"], "after_bytes": plan["after_bytes"],
                      "backup_retained": True, "backup_bytes": sum(s["bytes"] for s in plan["sources"].values()),
                      "written_metadata": {relative: _sha(_path(root, relative).read_bytes()) for relative in updates},
                      "registry_sha256": _sha((root / "registry.jsonl").read_bytes())}
            atomic_write_json(receipt_path, result)
            return result
        except Exception:
            _restore_backup(directory, root, plan)
            atomic_write_json(receipt_path, {"state": "rolled_back", "backup_retained": True})
            raise


def restore_library_photo_compaction(
    *, plan_dir: Path, archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False, confirmation_text: str = "",
) -> dict[str, Any]:
    """Restore a completed/interrupted compaction without overwriting later edits."""
    _confirmed(user_confirmed, confirmation_text)
    directory, root, plan = _load_plan(plan_dir, archive_root)
    with exclusive_file_lock(root / ".archive-write", timeout=30):
        receipt = _json(directory / "receipt.json")
        if receipt.get("state") not in {"applied", "applying"}:
            raise ValueError("Účtenka neobsahuje zmenšení k obnově.")
        interrupted = receipt["state"] == "applying"
        expected_metadata: dict[str, dict[str, Any]] = {}
        for item in plan["items"]:
            relative = item["metadata_file"]
            metadata = expected_metadata.setdefault(relative, _json(_path(directory / "backup", relative)))
            next(a for a in metadata["attachments"] if a["id"] == item["attachment_id"]).update(item["changes"])
        current_files = sorted(str(p.relative_to(root)) for p in (root / "articles").glob("*/metadata.json"))
        if current_files != plan["metadata_files"]:
            raise ValueError("Po přípravě se změnil seznam karet; obnova byla zastavena.")
        old_images = {name for item in plan["items"] for name in item["old_files"]}
        for relative, original in plan["sources"].items():
            if relative == "registry.jsonl":
                continue
            target = _path(root, relative, exists=False)
            if relative in old_images and not target.exists():
                continue
            allowed = {original["sha256"]}
            if relative in expected_metadata:
                encoded = (json.dumps(expected_metadata[relative], ensure_ascii=False, indent=2) + "\n").encode()
                allowed = {_sha(encoded)} | (allowed if interrupted else set())
            if not target.exists() or _sha(target.read_bytes()) not in allowed:
                raise ValueError("Po zmenšení se změnila knihovna; obnova nesmí přepsat další práci.")
        # A crash can leave the atomic registry at any completed per-card update.
        old_rows = [json.loads(line) for line in _path(directory / "backup", "registry.jsonl").read_text().splitlines() if line.strip()]
        current_rows = [json.loads(line) for line in (root / "registry.jsonl").read_text().splitlines() if line.strip()]
        if len(old_rows) != len(current_rows):
            raise ValueError("Po zmenšení se změnil registr knihovny.")
        new_by_id = {metadata["id"]: metadata for metadata in expected_metadata.values()}
        for old, current in zip(old_rows, current_rows):
            wanted = new_by_id.get(old["id"], old)
            if current != wanted and not (interrupted and current == old):
                raise ValueError("Po zmenšení se změnil registr; obnova nesmí přepsat další práci.")
        for item in plan["items"]:
            for prepared in item["prepared"]:
                target = _path(root, prepared["target"], exists=False)
                if interrupted and not target.exists():
                    continue
                if not target.exists() or _sha(target.read_bytes()) != prepared["sha256"]:
                    raise ValueError("Po zmenšení se změnila fotografie; obnova byla zastavena.")
        _restore_backup(directory, root, plan)
        atomic_write_json(directory / "receipt.json", {"state": "restored", "backup_retained": True})
        return {"ok": True, "state": "restored", "image_count": len(plan["items"])}
