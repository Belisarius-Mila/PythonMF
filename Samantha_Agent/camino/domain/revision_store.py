"""C03b SQLite reference store for versioned, single-writer metadata operations.

It does not store media bytes or expose a network listener. A future C05 server
must supply private authentication, media verification, backup, and recovery.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from .codec import (
    decode_asset, decode_change, decode_day, decode_moment, decode_text,
    decode_trip, encode_change, exact_object, wire,
)
from .model import ContractError, MomentHistory, Privacy, RevisionConflict, TextHistory


class StoreConflict(Exception):
    def __init__(self, code: str, message: str, current_revision: int | None = None):
        super().__init__(message)
        self.code = code
        self.current_revision = current_revision


class StoreNotFound(Exception):
    pass


SCHEMA_VERSION = 1
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RevisionStore:
    def __init__(self, database_path: str | Path):
        requested = Path(database_path).expanduser()
        if requested.is_symlink():
            raise ContractError("private Camino database cannot be a symlink")
        path = requested.resolve()
        if path.is_relative_to(_PROJECT_ROOT):
            raise ContractError("private Camino database must stay outside the source repository")
        if not path.parent.is_dir():
            raise ContractError("private Camino database parent does not exist")
        if path.exists():
            if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
                raise ContractError("private Camino database must be a restricted regular file")
        else:
            descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
        self.path = path
        self._initialize()

    @staticmethod
    def _uuid(value: Any) -> str:
        if not isinstance(value, str):
            raise ContractError("ID must be a canonical UUID")
        try:
            if str(UUID(value)) != value:
                raise ValueError
        except ValueError as error:
            raise ContractError("ID must be a canonical UUID") from error
        return value

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._open()
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ContractError("unsupported Camino database schema version")
            connection.execute("BEGIN IMMEDIATE")
            try:
                for statement in (
                    "CREATE TABLE IF NOT EXISTS meta (singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
                    "server_id TEXT NOT NULL, epoch TEXT NOT NULL, cursor INTEGER NOT NULL, "
                    "exports_blocked INTEGER NOT NULL, reconciliation_required INTEGER NOT NULL, "
                    "writer_device_id TEXT)",
                    "CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, body TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS days (id TEXT PRIMARY KEY, trip_id TEXT NOT NULL, "
                    "body TEXT NOT NULL, FOREIGN KEY(trip_id) REFERENCES trips(id))",
                    "CREATE TABLE IF NOT EXISTS moments (id TEXT PRIMARY KEY, trip_id TEXT NOT NULL, "
                    "revision INTEGER NOT NULL, body TEXT NOT NULL, "
                    "FOREIGN KEY(trip_id) REFERENCES trips(id))",
                    "CREATE TABLE IF NOT EXISTS moment_revisions (moment_id TEXT NOT NULL, "
                    "revision INTEGER NOT NULL, body TEXT NOT NULL, change_body TEXT, "
                    "PRIMARY KEY(moment_id,revision), FOREIGN KEY(moment_id) REFERENCES moments(id))",
                    "CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, moment_id TEXT NOT NULL, "
                    "body TEXT NOT NULL, FOREIGN KEY(moment_id) REFERENCES moments(id))",
                    "CREATE TABLE IF NOT EXISTS text_revisions (id TEXT PRIMARY KEY, moment_id TEXT NOT NULL, "
                    "body TEXT NOT NULL, FOREIGN KEY(moment_id) REFERENCES moments(id))",
                    "CREATE TABLE IF NOT EXISTS accepted_operations (id TEXT PRIMARY KEY, "
                    "device_sequence INTEGER NOT NULL UNIQUE, epoch TEXT NOT NULL, "
                    "request_sha256 TEXT NOT NULL, request_body BLOB NOT NULL, "
                    "kind TEXT NOT NULL, object_id TEXT NOT NULL, receipt TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS conflict_candidates (operation_id TEXT NOT NULL, "
                    "request_sha256 TEXT NOT NULL, request_body BLOB NOT NULL, "
                    "error_code TEXT NOT NULL, error_message TEXT NOT NULL, current_revision INTEGER, "
                    "PRIMARY KEY(operation_id,request_sha256))",
                ):
                    connection.execute(statement)
                connection.execute(
                    "INSERT OR IGNORE INTO meta VALUES (1,?,?,0,0,0,NULL)",
                    (str(uuid4()), str(uuid4())),
                )
                connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _meta(connection: sqlite3.Connection) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM meta WHERE singleton=1").fetchone()
        if row is None:
            raise ContractError("Camino database metadata is missing")
        return row

    def state(self) -> dict[str, Any]:
        with self._connection() as connection:
            meta = self._meta(connection)
            return {
                "contract_version": 1,
                "server_id": meta["server_id"],
                "epoch": meta["epoch"],
                "cursor": meta["cursor"],
                "writer_device_id": meta["writer_device_id"],
                "exports_blocked": bool(meta["exports_blocked"]),
                "reconciliation_required": bool(meta["reconciliation_required"]),
            }

    def rotate_epoch_for_restore(self) -> dict[str, Any]:
        """Called by a controlled restore path; never clears the export block."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "UPDATE meta SET epoch=?, exports_blocked=1, reconciliation_required=1 "
                    "WHERE singleton=1", (str(uuid4()),),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return self.state()

    def _save_conflict(self, connection: sqlite3.Connection, envelope: dict[str, Any],
                       raw: bytes, digest: str, error: StoreConflict) -> None:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT OR IGNORE INTO conflict_candidates VALUES (?,?,?,?,?,?)",
            (envelope["operation_id"], digest, raw, error.code, str(error),
             error.current_revision),
        )
        connection.execute("UPDATE meta SET exports_blocked=1 WHERE singleton=1")
        connection.commit()

    def apply(self, envelope: dict[str, Any], raw: bytes) -> dict[str, Any]:
        """Atomically append one contiguous operation or return an exact retry."""
        digest = hashlib.sha256(raw).hexdigest()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                meta = self._meta(connection)
                if envelope["epoch"] != meta["epoch"]:
                    raise StoreConflict("epoch_mismatch", "server epoch changed; compare inventories")
                prior = connection.execute(
                    "SELECT request_sha256,receipt FROM accepted_operations WHERE id=?",
                    (envelope["operation_id"],),
                ).fetchone()
                if prior is not None:
                    if prior["request_sha256"] == digest:
                        result = json.loads(prior["receipt"])
                        connection.commit()
                        return result
                    raise StoreConflict("operation_id_conflict", "operation ID has different bytes")
                if meta["writer_device_id"] is not None and envelope["device_id"] != meta["writer_device_id"]:
                    raise StoreConflict("writer_mismatch", "another device is the active writer")
                candidate = connection.execute(
                    "SELECT error_code,error_message,current_revision FROM conflict_candidates "
                    "WHERE operation_id=? AND request_sha256=?",
                    (envelope["operation_id"], digest),
                ).fetchone()
                if candidate is not None:
                    raise StoreConflict(candidate["error_code"], candidate["error_message"],
                                        candidate["current_revision"])
                if connection.execute(
                    "SELECT 1 FROM conflict_candidates WHERE operation_id=? LIMIT 1",
                    (envelope["operation_id"],),
                ).fetchone() is not None:
                    raise StoreConflict("operation_id_conflict", "operation ID has different bytes")
                if meta["reconciliation_required"] or meta["exports_blocked"]:
                    raise StoreConflict("reconciliation_required", "server requires inventory review")
                sequence = envelope["device_sequence"]
                if sequence != meta["cursor"] + 1:
                    raise StoreConflict("sequence_gap", "device operations must be contiguous")
                kind, object_id, revision, reused = self._project(connection, envelope)
                receipt = {
                    "contract_version": 1, "server_id": meta["server_id"],
                    "epoch": meta["epoch"], "cursor": sequence,
                    "operation_id": envelope["operation_id"], "kind": kind,
                    "object_id": object_id, "revision": revision, "reused": reused,
                }
                connection.execute(
                    "INSERT INTO accepted_operations VALUES (?,?,?,?,?,?,?,?)",
                    (envelope["operation_id"], sequence, meta["epoch"], digest,
                     raw, kind, object_id, self._json(receipt)),
                )
                connection.execute("UPDATE meta SET cursor=? WHERE singleton=1", (sequence,))
                if meta["writer_device_id"] is None:
                    connection.execute(
                        "UPDATE meta SET writer_device_id=? WHERE singleton=1",
                        (envelope["device_id"],),
                    )
                connection.commit()
                return receipt
            except StoreConflict as error:
                connection.rollback()
                if error.code in {"operation_id_conflict", "identity_conflict", "revision_conflict"}:
                    self._save_conflict(connection, envelope, raw, digest, error)
                raise
            except Exception:
                connection.rollback()
                raise

    def _project(self, connection: sqlite3.Connection, envelope: dict[str, Any]
                 ) -> tuple[str, str, int | None, bool]:
        kind = envelope["kind"]
        payload = envelope["payload"]
        expected = envelope["expected_revision"]
        if kind in {"create_trip", "create_day", "create_moment", "create_asset"}:
            if expected is not None:
                raise ContractError("create operation must not supply expected revision")
            decoders = {
                "create_trip": (decode_trip, "trips"),
                "create_day": (decode_day, "days"),
                "create_moment": (decode_moment, "moments"),
                "create_asset": (decode_asset, "assets"),
            }
            decode, table = decoders[kind]
            model = decode(payload)
            body = self._json(wire(model))
            if kind == "create_moment":
                old = connection.execute(
                    "SELECT body FROM moment_revisions WHERE moment_id=? AND revision=1",
                    (model.id,),
                ).fetchone()
            else:
                old = connection.execute(f"SELECT body FROM {table} WHERE id=?", (model.id,)).fetchone()
            if old is not None:
                if old["body"] != body:
                    raise StoreConflict("identity_conflict", "object ID has different content")
                return kind, model.id, 1 if kind == "create_moment" else None, True
            if kind == "create_day":
                if connection.execute("SELECT 1 FROM trips WHERE id=?", (model.trip_id,)).fetchone() is None:
                    raise StoreNotFound("parent trip is missing")
                connection.execute("INSERT INTO days VALUES (?,?,?)", (model.id, model.trip_id, body))
            elif kind == "create_moment":
                if model.revision != 1:
                    raise ContractError("new Moment must start at revision one")
                if model.privacy not in {Privacy.OWNER_ONLY.value, Privacy.DIARY.value}:
                    raise ContractError("new Moment privacy must be known")
                if connection.execute("SELECT 1 FROM trips WHERE id=?", (model.trip_id,)).fetchone() is None:
                    raise StoreNotFound("parent trip is missing")
                day_row = connection.execute("SELECT body FROM days WHERE id=?", (model.day_id,)).fetchone()
                if day_row is None:
                    raise StoreNotFound("chapter is missing")
                day = decode_day(json.loads(day_row["body"]))
                if day.trip_id != model.trip_id or day.local_date != model.chapter_date:
                    raise ContractError("Moment chapter is inconsistent")
                if model.captured.initial_chapter_date is not None and model.chapter_date != model.captured.initial_chapter_date:
                    raise ContractError("initial chapter disagrees with captured local date")
                if model.location is not None and not model.location.usable_at(model.captured.utc_ms):
                    raise ContractError("stale location cannot be attached as current")
                if model.related_moment_id is not None:
                    parent = connection.execute(
                        "SELECT trip_id FROM moments WHERE id=?", (model.related_moment_id,),
                    ).fetchone()
                    if parent is None or parent["trip_id"] != model.trip_id:
                        raise ContractError("linked Moment is missing or belongs to another trip")
                connection.execute(
                    "INSERT INTO moments VALUES (?,?,?,?)",
                    (model.id, model.trip_id, 1, body),
                )
                connection.execute(
                    "INSERT INTO moment_revisions VALUES (?,?,?,NULL)", (model.id, 1, body),
                )
            elif kind == "create_asset":
                if connection.execute("SELECT 1 FROM moments WHERE id=?", (model.moment_id,)).fetchone() is None:
                    raise StoreNotFound("parent Moment is missing")
                connection.execute("INSERT INTO assets VALUES (?,?,?)", (model.id, model.moment_id, body))
            else:
                connection.execute("INSERT INTO trips VALUES (?,?)", (model.id, body))
            return kind, model.id, 1 if kind == "create_moment" else None, False

        if kind == "update_metadata":
            data = exact_object(payload, {"moment_id", "change"})
            moment_id = self._uuid(data["moment_id"])
            history = self._history(connection, moment_id)
            if expected != history.current.revision:
                raise StoreConflict("revision_conflict", "expected Moment revision differs",
                                    history.current.revision)
            change = data["change"]
            if not isinstance(change, dict) or "type" not in change:
                raise ContractError("metadata change is invalid")
            common = {
                "id": envelope["operation_id"], "moment_id": data["moment_id"],
                "device_sequence": envelope["device_sequence"],
                "expected_revision": expected, "type": change["type"],
            }
            if change["type"] == "chapter":
                exact_object(change, {"type", "day_id"})
                day_id = self._uuid(change["day_id"])
                day_row = connection.execute("SELECT body FROM days WHERE id=?", (day_id,)).fetchone()
                if day_row is None:
                    raise StoreNotFound("new chapter is missing")
                common["day"] = json.loads(day_row["body"])
            elif change["type"] == "privacy":
                exact_object(change, {"type", "new_privacy", "user_action"})
                common.update(new_privacy=change["new_privacy"], user_action=change["user_action"])
            elif change["type"] == "hidden":
                exact_object(change, {"type", "hidden"})
                common["hidden"] = change["hidden"]
            else:
                raise ContractError("unknown metadata change")
            operation = decode_change(common)
            try:
                updated = history.apply(operation)
            except RevisionConflict as error:
                raise StoreConflict("revision_conflict", "expected Moment revision differs",
                                    history.current.revision) from error
            body = self._json(wire(updated.current))
            connection.execute(
                "INSERT INTO moment_revisions VALUES (?,?,?,?)",
                (updated.current.id, updated.current.revision, body,
                 self._json(encode_change(operation))),
            )
            connection.execute(
                "UPDATE moments SET revision=?,body=? WHERE id=?",
                (updated.current.revision, body, updated.current.id),
            )
            return kind, updated.current.id, updated.current.revision, False

        if kind == "append_text":
            text_revision = decode_text(payload)
            current = self._moment(connection, text_revision.moment_id)
            if expected != current.revision:
                raise StoreConflict("revision_conflict", "expected Moment revision differs",
                                    current.revision)
            body = self._json(wire(text_revision))
            old = connection.execute(
                "SELECT body FROM text_revisions WHERE id=?", (text_revision.id,),
            ).fetchone()
            if old is not None:
                if old["body"] != body:
                    raise StoreConflict("identity_conflict", "text revision ID has different content")
                return kind, text_revision.id, current.revision, True
            rows = connection.execute(
                "SELECT body FROM text_revisions WHERE moment_id=? ORDER BY rowid",
                (text_revision.moment_id,),
            ).fetchall()
            history = TextHistory(tuple(decode_text(json.loads(row["body"])) for row in rows))
            history.add(text_revision)  # validates parent and Moment ownership
            connection.execute(
                "INSERT INTO text_revisions VALUES (?,?,?)",
                (text_revision.id, text_revision.moment_id, body),
            )
            return kind, text_revision.id, current.revision, False

        raise ContractError("unknown operation kind")

    def _moment(self, connection: sqlite3.Connection, moment_id: str):
        row = connection.execute("SELECT body FROM moments WHERE id=?", (moment_id,)).fetchone()
        if row is None:
            raise StoreNotFound("Moment is missing")
        return decode_moment(json.loads(row["body"]))

    def _history(self, connection: sqlite3.Connection, moment_id: str) -> MomentHistory:
        rows = connection.execute(
            "SELECT body,change_body FROM moment_revisions WHERE moment_id=? ORDER BY revision",
            (moment_id,),
        ).fetchall()
        if not rows:
            raise StoreNotFound("Moment is missing")
        versions = tuple(decode_moment(json.loads(row["body"])) for row in rows)
        operations = tuple(decode_change(json.loads(row["change_body"])) for row in rows[1:])
        return MomentHistory(versions, operations)

    def moment(self, moment_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            model = self._moment(connection, moment_id)
            return wire(model)

    def asset(self, asset_id: str) -> dict[str, Any]:
        """Return one accepted Asset manifest without implying media verification."""
        asset_id = self._uuid(asset_id)
        with self._connection() as connection:
            row = connection.execute(
                "SELECT body FROM assets WHERE id=?", (asset_id,),
            ).fetchone()
            if row is None:
                raise StoreNotFound("Asset is missing")
            return json.loads(row["body"])

    def moment_history(self, moment_id: str) -> tuple[dict[str, Any], ...]:
        with self._connection() as connection:
            return tuple(wire(value) for value in self._history(connection, moment_id).versions)

    def text_history(self, moment_id: str) -> tuple[dict[str, Any], ...]:
        with self._connection() as connection:
            self._moment(connection, moment_id)
            rows = connection.execute(
                "SELECT body FROM text_revisions WHERE moment_id=? ORDER BY rowid", (moment_id,),
            ).fetchall()
            return tuple(json.loads(row["body"]) for row in rows)

    def viewer_safe_ids(self, trip_id: str) -> tuple[str, ...]:
        """Reference projection: any unresolved conflict or restore closes output."""
        with self._connection() as connection:
            meta = self._meta(connection)
            if meta["exports_blocked"] or meta["reconciliation_required"]:
                return ()
            row = connection.execute("SELECT body FROM trips WHERE id=?", (trip_id,)).fetchone()
            if row is None:
                raise StoreNotFound("trip is missing")
            trip = decode_trip(json.loads(row["body"]))
            if not trip.viewer_enabled:
                return ()
            return tuple(sorted(
                model.id for model in (
                    decode_moment(json.loads(row["body"]))
                    for row in connection.execute("SELECT body FROM moments WHERE trip_id=?", (trip_id,))
                )
                if model.privacy == Privacy.DIARY.value and not model.hidden
            ))

    def changes(self, epoch: str, cursor: int, limit: int = 100) -> dict[str, Any]:
        with self._connection() as connection:
            meta = self._meta(connection)
            if epoch != meta["epoch"]:
                raise StoreConflict("epoch_mismatch", "server epoch changed; compare inventories")
            if cursor > meta["cursor"]:
                raise StoreConflict("cursor_ahead", "client cursor is ahead of server; compare inventories")
            rows = connection.execute(
                "SELECT device_sequence,request_body FROM accepted_operations "
                "WHERE device_sequence>? ORDER BY device_sequence LIMIT ?", (cursor, limit),
            ).fetchall()
            return {
                "contract_version": 1, "epoch": epoch,
                "cursor": rows[-1]["device_sequence"] if rows else cursor,
                "events": [json.loads(row["request_body"]) for row in rows],
                "reconciliation_required": bool(meta["reconciliation_required"]),
                "exports_blocked": bool(meta["exports_blocked"]),
            }

    def compare_inventory(self, client_moments: list[dict[str, Any]]) -> dict[str, Any]:
        """Read-only comparison after restore; never deletes or unblocks exports."""
        with self._connection() as connection:
            if not self._meta(connection)["reconciliation_required"]:
                raise StoreConflict("reconciliation_not_required", "no restored epoch needs comparison")
            server = {
                row["id"]: decode_moment(json.loads(row["body"]))
                for row in connection.execute("SELECT id,body FROM moments")
            }
            seen: set[str] = set()
            differences: list[dict[str, Any]] = []
            for entry in client_moments:
                data = exact_object(entry, {"id", "revision", "privacy"})
                identifier = data["id"]
                if not isinstance(identifier, str) or identifier in seen:
                    raise ContractError("inventory has duplicate or invalid IDs")
                try:
                    if str(UUID(identifier)) != identifier:
                        raise ValueError
                except ValueError as error:
                    raise ContractError("inventory ID must be a canonical UUID") from error
                seen.add(identifier)
                revision = data["revision"]
                if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
                    raise ContractError("inventory revision is invalid")
                if not isinstance(data["privacy"], str):
                    raise ContractError("inventory privacy is invalid")
                present = server.get(identifier)
                if present is None:
                    differences.append({"id": identifier, "reason": "missing_on_server"})
                elif revision > present.revision:
                    differences.append({"id": identifier, "reason": "server_older"})
                elif revision != present.revision or data["privacy"] != present.privacy:
                    differences.append({"id": identifier, "reason": "state_differs"})
            for identifier in sorted(server.keys() - seen):
                differences.append({"id": identifier, "reason": "missing_on_phone"})
            meta = self._meta(connection)
            return {
                "contract_version": 1,
                "epoch": meta["epoch"],
                "differences": differences,
                "exports_blocked": bool(meta["exports_blocked"]),
                "reconciliation_required": bool(meta["reconciliation_required"]),
            }
