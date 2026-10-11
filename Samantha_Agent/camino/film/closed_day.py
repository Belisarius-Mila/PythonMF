"""P2-B: close one phone-proved day into immutable private film inputs."""

from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import re
import sqlite3
import stat
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

from camino.domain.revision_store import RevisionStore
from camino.server.media_store import MediaStore
from .project import fingerprint, write_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_HASH = re.compile(r"[0-9a-f]{64}")
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
_MAX_ITEMS = 10_000


class ClosedDayError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _uuid(value: object) -> str:
    if not isinstance(value, str):
        raise ClosedDayError("invalid_proof", "Neplatná identita v důkazu z telefonu.")
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except ValueError as error:
        raise ClosedDayError("invalid_proof", "Neplatná identita v důkazu z telefonu.") from error
    return value


def _hash(value: object) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ClosedDayError("invalid_proof", "Neplatný otisk zdroje.")
    return value


def _exact(value: object, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ClosedDayError("invalid_proof", "Důkaz z telefonu má neúplná nebo neznámá pole.")
    return value


def validate_phone_proof(proof: object) -> dict[str, Any]:
    """Accept only the native app's fresh, explicit post-discovery inventory."""
    data = _exact(proof, {
        "contract_version", "request_id", "trip_id", "day_id", "device_id",
        "server_id", "epoch", "cursor", "pending_metadata", "pending_media",
        "active_uploads", "moments", "assets",
    })
    if type(data["contract_version"]) is not int or data["contract_version"] != 1:
        raise ClosedDayError("unsupported_version", "Nepodporovaná verze důkazu z telefonu.")
    for key in ("request_id", "trip_id", "day_id", "device_id", "server_id", "epoch"):
        _uuid(data[key])
    if type(data["cursor"]) is not int or data["cursor"] < 1:
        raise ClosedDayError("invalid_proof", "Telefon nemá platný serverový kurzor.")
    if any(type(data[key]) is not int or data[key] != 0 for key in
           ("pending_metadata", "pending_media", "active_uploads")):
        raise ClosedDayError("phone_pending", "Na telefonu ještě čekají změny nebo přenosy.")
    moments, assets = data["moments"], data["assets"]
    if (not isinstance(moments, list) or not 1 <= len(moments) <= _MAX_ITEMS
            or not isinstance(assets, list) or len(assets) > _MAX_ITEMS):
        raise ClosedDayError("invalid_proof", "Inventář dne nemá platný rozsah.")
    moment_ids: set[str] = set()
    for item in moments:
        row = _exact(item, {"id", "revision", "privacy", "hidden", "chapter_date"})
        identifier = _uuid(row["id"])
        if identifier in moment_ids:
            raise ClosedDayError("invalid_proof", "Inventář dne obsahuje duplicitní Moment.")
        moment_ids.add(identifier)
        if (type(row["revision"]) is not int or row["revision"] < 1
                or row["privacy"] not in ("diary", "owner_only")
                or type(row["hidden"]) is not bool
                or not isinstance(row["chapter_date"], str)
                or not _DAY.fullmatch(row["chapter_date"])):
            raise ClosedDayError("invalid_proof", "Neplatná revize nebo povolenost Momentu.")
    asset_ids: set[str] = set()
    for item in assets:
        row = _exact(item, {"id", "moment_id", "media_kind", "byte_count", "sha256"})
        identifier = _uuid(row["id"])
        if identifier in asset_ids or _uuid(row["moment_id"]) not in moment_ids:
            raise ClosedDayError("invalid_proof", "Inventář dne obsahuje neznámé nebo duplicitní médium.")
        asset_ids.add(identifier)
        if (row["media_kind"] not in ("photo", "video", "audio")
                or type(row["byte_count"]) is not int or row["byte_count"] <= 0):
            raise ClosedDayError("invalid_proof", "Neplatné médium v inventáři dne.")
        _hash(row["sha256"])
    return data


def _private_directory(path: Path) -> Path:
    requested = Path(path).expanduser()
    if not requested.is_absolute() or requested.is_symlink():
        raise ClosedDayError("unsafe_store", "Filmové úložiště nemá bezpečnou cestu.")
    resolved = requested.resolve()
    if resolved.is_relative_to(PROJECT_ROOT):
        raise ClosedDayError("unsafe_store", "Filmové úložiště musí být mimo zdrojový kód.")
    if resolved.exists():
        if not resolved.is_dir() or stat.S_IMODE(resolved.stat().st_mode) & 0o077:
            raise ClosedDayError("unsafe_store", "Filmové úložiště není soukromé.")
    else:
        if not resolved.parent.is_dir() or resolved.parent.is_symlink():
            raise ClosedDayError("unsafe_store", "Chybí rodič filmového úložiště.")
        resolved.mkdir(mode=0o700)
    return resolved


@contextmanager
def _store_lock(root: Path):
    descriptor = os.open(root / ".closure-lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _body_rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    # Table names are fixed here; no caller string becomes SQL.
    if table not in {"days", "moments", "assets"}:
        raise AssertionError("unsupported table")
    return [json.loads(row[0]) for row in connection.execute(f"SELECT body FROM {table}")]


class ClosedDayStore:
    """Create-only project revisions; no source media is copied or modified."""

    def __init__(self, root: Path, metadata: RevisionStore, media: MediaStore):
        self.root = _private_directory(root)
        self.metadata = metadata
        self.media = media

    def close(self, raw_proof: object) -> dict[str, Any]:
        proof = validate_phone_proof(raw_proof)
        project_id = proof["request_id"]
        with _store_lock(self.root):
            existing = self.root / project_id
            if existing.exists():
                receipt = self._existing(existing, proof)
                if not self.status(project_id)["valid"]:
                    raise ClosedDayError("closed_day_stale", "Uložený projekt vyžaduje nové uzavření vstupů.")
                return receipt
            with self.metadata._connection() as metadata, closing(self.media._open()) as media:
                metadata.execute("BEGIN IMMEDIATE")
                media.execute("BEGIN")
                try:
                    manifest, project = self._snapshot(metadata, media, proof)
                    result = self._publish(project_id, proof, manifest, project)
                finally:
                    media.rollback()
                    metadata.rollback()
            return result

    def _snapshot(self, metadata: sqlite3.Connection, media: sqlite3.Connection,
                  proof: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        state = metadata.execute(
            "SELECT server_id,epoch,cursor,writer_device_id,exports_blocked,"
            "reconciliation_required FROM meta WHERE singleton=1"
        ).fetchone()
        if (state is None or state[4] or state[5]
                or (state[0], state[1], state[2], state[3]) !=
                (proof["server_id"], proof["epoch"], proof["cursor"], proof["device_id"])):
            raise ClosedDayError("server_mismatch", "Telefon a Mac nemají stejný přijatý stav.")
        days = [day for day in _body_rows(metadata, "days") if day["id"] == proof["day_id"]]
        if len(days) != 1 or days[0]["trip_id"] != proof["trip_id"]:
            raise ClosedDayError("day_missing", "Vybraný den na Macu chybí nebo patří jiné cestě.")
        day = days[0]
        moments = [row for row in _body_rows(metadata, "moments") if row["day_id"] == day["id"]]
        expected_moments = [{key: row[key] for key in
                             ("id", "revision", "privacy", "hidden", "chapter_date")}
                            for row in moments]
        if (len(expected_moments) != len(proof["moments"])
                or sorted(expected_moments, key=lambda row: row["id"]) !=
                sorted(proof["moments"], key=lambda row: row["id"])):
            raise ClosedDayError("metadata_mismatch", "Revize nebo úplnost Momentů dne nesouhlasí.")
        by_moment = {row["id"]: row for row in moments}
        assets = [row for row in _body_rows(metadata, "assets") if row["moment_id"] in by_moment]
        expected_assets = [{key: row[key] for key in
                            ("id", "moment_id", "media_kind", "byte_count", "sha256")}
                           for row in assets]
        if (len(expected_assets) != len(proof["assets"])
                or sorted(expected_assets, key=lambda row: row["id"]) !=
                sorted(proof["assets"], key=lambda row: row["id"])):
            raise ClosedDayError("asset_mismatch", "Inventář médií telefonu a Macu nesouhlasí.")
        operation_order = {row["object_id"]: row["device_sequence"] for row in metadata.execute(
            "SELECT object_id,device_sequence FROM accepted_operations "
            "WHERE kind IN ('create_moment','create_asset')")}
        allowed: list[dict[str, Any]] = []
        for asset in assets:
            receipt_row = media.execute("SELECT receipt FROM verified_assets WHERE asset_id=?",
                                        (asset["id"],)).fetchone()
            session = media.execute("SELECT state,byte_count,sha256 FROM upload_sessions WHERE asset_id=?",
                                    (asset["id"],)).fetchone()
            if (receipt_row is None or session is None or session[0] != "verified"
                    or (session[1], session[2]) != (asset["byte_count"], asset["sha256"])):
                raise ClosedDayError("media_missing", "Některé médium dne není na Macu ověřené.")
            receipt = json.loads(receipt_row[0])
            if (receipt.get("state") != "verified" or
                    (receipt.get("asset_id"), receipt.get("byte_count"), receipt.get("sha256")) !=
                    (asset["id"], asset["byte_count"], asset["sha256"])):
                raise ClosedDayError("media_missing", "Účtenka média nesouhlasí s manifestem.")
            path = self.media.objects / (asset["id"] + ".bin")
            if path.is_symlink() or not path.is_file() or path.stat().st_size != asset["byte_count"]:
                raise ClosedDayError("media_missing", "Originál média chybí nebo má jinou velikost.")
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if not hmac.compare_digest(actual, asset["sha256"]):
                raise ClosedDayError("media_hash_mismatch", "Originál média nesouhlasí s otiskem.")
            moment = by_moment[asset["moment_id"]]
            if moment["privacy"] == "owner_only" or moment["hidden"]:
                continue
            if moment["privacy"] != "diary":
                raise ClosedDayError("privacy_unknown", "Neznámá povolenost blokuje film.")
            if asset["media_kind"] == "video" and (type(asset["duration_ms"]) is not int
                                                     or asset["duration_ms"] <= 0):
                raise ClosedDayError("duration_missing", "Video nemá ověřenou délku.")
            title = next((item["title"] for item in moment.get("attachment_titles", [])
                          if item["kind"] == "asset" and item["target_id"] == asset["id"]),
                         moment.get("title", ""))
            allowed.append({
                "moment_id": moment["id"], "moment_revision": moment["revision"],
                "asset_id": asset["id"], "media_kind": asset["media_kind"],
                "byte_count": asset["byte_count"], "sha256": asset["sha256"],
                "duration_ms": asset["duration_ms"],
                "title": title, "title_origin": "user" if title else "none",
                "capture_utc_ms": moment["captured"]["utc_ms"],
                "capture_local_wall": moment["captured"]["local_wall"],
                "capture_uncertain": moment["captured"]["uncertain"],
                "moment_order": operation_order.get(moment["id"]),
                "asset_order": operation_order.get(asset["id"]),
            })
        if not allowed:
            raise ClosedDayError("no_allowed_sources", "Den nemá žádný povolený zdroj pro film.")
        allowed.sort(key=lambda row: (
            row["capture_utc_ms"] is None,
            row["capture_utc_ms"] if row["capture_utc_ms"] is not None else 0,
            row["moment_order"] if row["moment_order"] is not None else 2**63,
            row["asset_order"] if row["asset_order"] is not None else 2**63,
            row["asset_id"],
        ))
        manifest = {
            "schema": 1, "scope": "camino-closed-day", "trip_id": proof["trip_id"],
            "day_id": day["id"], "local_date": day["local_date"],
            "server_id": proof["server_id"], "epoch": proof["epoch"],
            "cursor": proof["cursor"], "phone_proof_sha256": fingerprint(proof),
            "inventory_sha256": fingerprint({
                "moments": sorted(expected_moments, key=lambda row: row["id"]),
                "assets": sorted(expected_assets, key=lambda row: row["id"]),
            }),
            "sources": allowed,
        }
        shots = []
        cursor = 0
        for source in allowed:
            if source["media_kind"] not in ("photo", "video"):
                continue
            duration = source["duration_ms"] if source["media_kind"] == "video" else 3000
            shots.append({
                "id": source["asset_id"], "asset_id": source["asset_id"],
                "moment_id": source["moment_id"],
                "source_revision": source["moment_revision"],
                "source_sha256": source["sha256"],
                "at_ms": cursor, "in_ms": 0, "out_ms": duration,
                "title": source["title"], "title_origin": source["title_origin"],
                "manual": False,
            })
            cursor += duration
        project = {
            "schema": 1, "scope": "camino-p2b", "id": proof["request_id"], "revision": 1,
            "day_id": day["id"], "local_date": day["local_date"],
            "manifest_sha256": fingerprint(manifest),
            "shots": shots,
            "voice_choices": [row["asset_id"] for row in allowed if row["media_kind"] == "audio"],
        }
        if not project["shots"]:
            raise ClosedDayError("no_visual_sources", "Den nemá povolené foto nebo video.")
        return manifest, project

    def _publish(self, project_id: str, proof: dict[str, Any], manifest: dict[str, Any],
                 project: dict[str, Any]) -> dict[str, Any]:
        staging = self.root / (".pending-" + project_id)
        if staging.exists():
            raise ClosedDayError("incomplete_prior_write", "Předchozí nedokončený zápis vyžaduje kontrolu.")
        staging.mkdir(mode=0o700)
        write_json(staging / "manifest.json", manifest)
        write_json(staging / "project-r1.json", project)
        receipt = self._receipt(project_id, proof, manifest, project)
        write_json(staging / "receipt.json", receipt)
        os.rename(staging, self.root / project_id)
        descriptor = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return receipt

    @staticmethod
    def _receipt(project_id: str, proof: dict[str, Any], manifest: dict[str, Any],
                 project: dict[str, Any]) -> dict[str, Any]:
        return {
            "contract_version": 1, "state": "closed", "project_id": project_id,
            "day_id": proof["day_id"], "local_date": manifest["local_date"],
            "cursor": proof["cursor"], "manifest_sha256": fingerprint(manifest),
            "project_sha256": fingerprint(project),
            "source_count": len(manifest["sources"]), "shot_count": len(project["shots"]),
            "voice_choice_count": len(project["voice_choices"]),
        }

    def _existing(self, directory: Path, proof: dict[str, Any]) -> dict[str, Any]:
        if directory.is_symlink() or not directory.is_dir():
            raise ClosedDayError("unsafe_store", "Projekt má neplatný adresář.")
        try:
            manifest = self._read(directory / "manifest.json")
            project = self._read(directory / "project-r1.json")
            receipt = self._read(directory / "receipt.json")
        except (OSError, ValueError) as error:
            raise ClosedDayError("incomplete_prior_write", "Uložený projekt je neúplný.") from error
        if (manifest.get("phone_proof_sha256") != fingerprint(proof)
                or project.get("manifest_sha256") != fingerprint(manifest)
                or receipt.get("project_sha256") != fingerprint(project)
                or receipt != self._receipt(proof["request_id"], proof, manifest, project)):
            raise ClosedDayError("request_conflict", "Stejné ID uzavření bylo použité pro jiný stav.")
        return receipt

    def status(self, project_id: str) -> dict[str, Any]:
        """Recheck current permission and bytes before any future render or delivery."""
        _uuid(project_id)
        directory = self.root / project_id
        if directory.is_symlink() or not directory.is_dir():
            raise ClosedDayError("project_missing", "Uložený filmový projekt nebyl nalezen.")
        try:
            manifest = self._read(directory / "manifest.json")
            project = self._read(directory / "project-r1.json")
            receipt = self._read(directory / "receipt.json")
        except (OSError, ValueError) as error:
            raise ClosedDayError("project_invalid", "Uložený filmový projekt je neúplný.") from error
        if (manifest.get("schema") != 1 or manifest.get("scope") != "camino-closed-day"
                or project.get("manifest_sha256") != fingerprint(manifest)
                or receipt.get("manifest_sha256") != fingerprint(manifest)
                or receipt.get("project_sha256") != fingerprint(project)
                or project.get("id") != project_id or receipt.get("project_id") != project_id
                or receipt.get("contract_version") != 1 or receipt.get("state") != "closed"
                or receipt.get("day_id") != manifest.get("day_id")
                or receipt.get("local_date") != manifest.get("local_date")
                or receipt.get("cursor") != manifest.get("cursor")
                or not isinstance(manifest.get("sources"), list)
                or not isinstance(project.get("shots"), list)
                or not isinstance(project.get("voice_choices"), list)
                or receipt.get("source_count") != len(manifest["sources"])
                or receipt.get("shot_count") != len(project["shots"])
                or receipt.get("voice_choice_count") != len(project["voice_choices"])):
            raise ClosedDayError("project_invalid", "Uložený filmový projekt má neplatný manifest.")
        with self.metadata._connection() as metadata, closing(self.media._open()) as media:
            state = metadata.execute(
                "SELECT server_id,epoch,exports_blocked,reconciliation_required "
                "FROM meta WHERE singleton=1").fetchone()
            if (state is None or state[0] != manifest["server_id"] or state[1] != manifest["epoch"]
                    or state[2] or state[3]):
                return {**receipt, "valid": False, "reason": "server_state_changed"}
            moments = {row["id"]: row for row in _body_rows(metadata, "moments")}
            assets = {row["id"]: row for row in _body_rows(metadata, "assets")}
            day_moments = [row for row in moments.values() if row["day_id"] == manifest["day_id"]]
            day_moment_ids = {row["id"] for row in day_moments}
            day_assets = [row for row in assets.values() if row["moment_id"] in day_moment_ids]
            inventory_hash = fingerprint({
                "moments": sorted(({key: row[key] for key in
                                    ("id", "revision", "privacy", "hidden", "chapter_date")}
                                   for row in day_moments), key=lambda row: row["id"]),
                "assets": sorted(({key: row[key] for key in
                                   ("id", "moment_id", "media_kind", "byte_count", "sha256")}
                                  for row in day_assets), key=lambda row: row["id"]),
            })
            if inventory_hash != manifest.get("inventory_sha256"):
                return {**receipt, "valid": False, "reason": "day_inventory_changed"}
            for source in manifest["sources"]:
                moment = moments.get(source["moment_id"])
                asset = assets.get(source["asset_id"])
                if (moment is None or moment["revision"] != source["moment_revision"]
                        or moment["privacy"] != "diary" or moment["hidden"]
                        or moment["day_id"] != manifest["day_id"]
                        or asset is None or asset["moment_id"] != moment["id"]
                        or (asset["sha256"], asset["byte_count"]) !=
                        (source["sha256"], source["byte_count"])):
                    return {**receipt, "valid": False, "reason": "source_changed"}
                verified = media.execute("SELECT 1 FROM verified_assets WHERE asset_id=?",
                                         (source["asset_id"],)).fetchone()
                path = self.media.objects / (source["asset_id"] + ".bin")
                if (verified is None or path.is_symlink() or not path.is_file()
                        or path.stat().st_size != source["byte_count"]):
                    return {**receipt, "valid": False, "reason": "media_missing"}
                with path.open("rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if not hmac.compare_digest(actual, source["sha256"]):
                    return {**receipt, "valid": False, "reason": "media_changed"}
        return {**receipt, "valid": True, "reason": None}

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise OSError("invalid private project file")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("invalid private project value")
        return value
