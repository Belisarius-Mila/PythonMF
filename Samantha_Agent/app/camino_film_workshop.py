"""Owner-confirmed Mac film inputs; never writes the Camino archive or service."""
from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from uuid import NAMESPACE_URL, UUID, uuid5

from camino.film.closed_day import (
    ClosedDayError, ClosedDayStore, _private_directory, _store_lock,
)
from camino.film.project import fingerprint, write_json
from camino.server.service_safety import readonly

DAY = "2026-10-06"
ORIGIN = "owner_confirmed_mac"


class MacFilmProjectStore(ClosedDayStore):
    """Reuse source validation with strictly read-only SQLite adapters.

    This is a separate store and confirmation origin, not an iPhone proof.
    The existing phone API and running Camino release are untouched.
    """

    def __init__(self, root: Path, *, metadata_db: Path, media_db: Path,
                 media_root: Path, trip_id: str):
        self.root = Path(root)
        if self.root.exists():
            _private_directory(self.root)
        self.trip_id = str(UUID(trip_id))
        self.metadata_db, self.media_db = Path(metadata_db), Path(media_db)
        self.media_root = Path(media_root)
        for path in (self.metadata_db, self.media_db, self.media_root):
            if path.is_symlink() or path.resolve() != path or not path.exists():
                raise ClosedDayError("unsafe_archive", "Archiv nemá bezpečné původní cesty.")
        archive_dirs = (self.metadata_db.parent, self.media_db.parent, self.media_root)
        if any(self.root.resolve().is_relative_to(p) or p.is_relative_to(self.root.resolve())
               for p in archive_dirs):
            raise ClosedDayError("unsafe_store", "Filmový projekt musí být oddělený od archivu.")
        self.metadata = SimpleNamespace(_connection=self._metadata_connection)
        self.media = SimpleNamespace(_open=lambda: self._open(self.media_db),
                                     objects=self.media_root / "objects")

    @staticmethod
    def _open(path: Path):
        connection = readonly(path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _metadata_connection(self):
        connection = self._open(self.metadata_db)
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _date(value: str) -> str:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ClosedDayError("invalid_date", "Vyber platný den.")
        return value

    def _capture(self, local_date: str):
        with self._metadata_connection() as metadata, closing(self.media._open()) as media:
            metadata.execute("BEGIN")
            media.execute("BEGIN")
            state = metadata.execute("SELECT server_id,epoch,cursor,writer_device_id,"
                                     "exports_blocked,reconciliation_required FROM meta "
                                     "WHERE singleton=1").fetchone()
            if not state or state[4] or state[5]:
                raise ClosedDayError("archive_blocked", "Archiv nejprve vyžaduje dokončení obnovy.")
            days = [json.loads(row[0]) for row in metadata.execute("SELECT body FROM days")]
            days = [d for d in days if d["trip_id"] == self.trip_id and d["local_date"] == local_date]
            if len(days) != 1:
                raise ClosedDayError("day_missing", "Den není v aktuálním Mac archivu jednoznačný.")
            moments = [json.loads(row[0]) for row in metadata.execute("SELECT body FROM moments")]
            moments = [m for m in moments if m["day_id"] == days[0]["id"]]
            ids = {m["id"] for m in moments}
            assets = [json.loads(row[0]) for row in metadata.execute("SELECT body FROM assets")]
            assets = [a for a in assets if a["moment_id"] in ids]
            if not 1 <= len(moments) <= 10000 or len(assets) > 10000:
                raise ClosedDayError("invalid_inventory", "Den nemá platný rozsah vstupů.")
            inventory = {
                "moments": sorted(({k: m[k] for k in
                    ("id", "revision", "privacy", "hidden", "chapter_date")} for m in moments),
                    key=lambda m: m["id"]),
                "assets": sorted(({k: a[k] for k in
                    ("id", "moment_id", "media_kind", "byte_count", "sha256")} for a in assets),
                    key=lambda a: a["id"]),
            }
            identity = {"origin": ORIGIN, "server_id": state[0], "epoch": state[1],
                        "trip_id": self.trip_id, "day_id": days[0]["id"],
                        "inventory": fingerprint(inventory)}
            project_id = str(uuid5(NAMESPACE_URL, fingerprint(identity)))
            evidence = {
                "origin": ORIGIN, "owner_confirmed_final": True, "local_date": local_date,
                "request_id": project_id, "trip_id": self.trip_id, "day_id": days[0]["id"],
                "server_id": state[0], "epoch": state[1], "cursor": state[2],
                "device_id": state[3], **inventory,
            }
            # No phone queues or phone completeness are asserted here. The owner
            # explicitly confirms final Mac inputs; shared validation checks every
            # revision, receipt, upload session, permission and original hash.
            manifest, project = super()._snapshot(metadata, media, evidence)
            manifest.pop("phone_proof_sha256")
            manifest.update(closure_origin=ORIGIN, mac_confirmation_sha256=fingerprint(evidence))
            project["manifest_sha256"] = fingerprint(manifest)
            return evidence, manifest, project

    def close_mac_day(self, local_date: str, *, confirmed: bool):
        local_date = self._date(local_date)
        if confirmed is not True:
            raise ClosedDayError("confirmation_required", "Potvrď konečnost dat tohoto dne na Macu.")
        self.root = _private_directory(self.root)
        with _store_lock(self.root):
            evidence, manifest, project = self._capture(local_date)
            project_id = evidence["request_id"]
            target = self.root / project_id
            if target.exists():
                self._confirmed_status(project_id)
            else:
                staging = self.root / (".pending-" + project_id)
                if staging.exists():
                    raise ClosedDayError("incomplete_prior_write", "Předchozí zápis projektu vyžaduje kontrolu.")
                staging.mkdir(mode=0o700)
                write_json(staging / "mac-confirmation.json", evidence)
                write_json(staging / "manifest.json", manifest)
                write_json(staging / "project-r1.json", project)
                write_json(staging / "receipt.json", self._receipt(project_id, evidence, manifest, project))
                os.rename(staging, target)
                descriptor = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            return self.day_status(local_date, project_id=project_id)

    def _confirmed_status(self, project_id: str):
        directory = self.root / str(UUID(project_id))
        if directory.is_symlink() or not directory.is_dir():
            raise ClosedDayError("unsafe_store", "Projekt nemá bezpečný adresář.")
        confirmation = self._read(directory / "mac-confirmation.json")
        manifest = self._read(directory / "manifest.json")
        if (manifest.get("closure_origin") != ORIGIN or "phone_proof_sha256" in manifest
                or confirmation.get("origin") != ORIGIN
                or confirmation.get("owner_confirmed_final") is not True
                or manifest.get("trip_id") != self.trip_id
                or fingerprint(confirmation) != manifest.get("mac_confirmation_sha256")):
            raise ClosedDayError("project_invalid", "Projekt nemá platné potvrzení Mac vstupů.")
        return super().status(project_id)

    def day_status(self, local_date: str, *, project_id: str | None = None):
        local_date = self._date(local_date)
        result = {"ok": True, "exists": False, "valid": False, "local_date": local_date}
        if not self.root.exists():
            return result
        if project_id is None:
            directories = sorted(self.root.iterdir(), key=lambda p: p.stat().st_mtime_ns, reverse=True)
            for path in directories:
                if path.is_symlink() or not path.is_dir():
                    continue
                try:
                    UUID(path.name)
                except ValueError:
                    continue
                manifest = self._read(path / "manifest.json")
                if manifest.get("local_date") == local_date and manifest.get("trip_id") == self.trip_id:
                    project_id = path.name
                    break
        if project_id is None:
            return result
        status = self._confirmed_status(project_id)
        if status["local_date"] != local_date:
            raise ClosedDayError("project_invalid", "Projekt patří jinému dni.")
        result.update(exists=True, valid=status["valid"])
        if not status["valid"]:
            # No old counts, titles or source list survive a privacy change.
            return {**result, "message": "Projekt už neodpovídá aktuálním datům. Potvrď novou sadu."}
        manifest = self._read(self.root / project_id / "manifest.json")
        project = self._read(self.root / project_id / "project-r1.json")
        sources = {s["asset_id"]: s for s in manifest["sources"]}
        counts = Counter(s["media_kind"] for s in sources.values())
        shots = [{"kind": sources[s["asset_id"]]["media_kind"], "title": s["title"],
                  "duration_ms": s["out_ms"] - s["in_ms"]} for s in project["shots"]]
        return {**result, "project_id": project_id, "source_count": status["source_count"],
                "photo_count": counts["photo"], "video_count": counts["video"],
                "audio_count": counts["audio"], "shot_count": len(shots), "shots": shots,
                "duration_ms": sum(s["duration_ms"] for s in shots),
                "message": "Projekt je uložený na Macu a jeho zdroje jsou ověřené."}


def production_store():
    # Configuration validation is read-only; never instantiate archive stores
    # that create schemas, migrate databases or recover upload journals.
    from scripts import camino_service_control as service
    config = service.load_config(service.ROOT)
    return MacFilmProjectStore(service.ROOT.parents[1] / "CaminoFilmProjects", **{
        k: config[k] for k in ("metadata_db", "media_db", "media_root", "trip_id")})


def camino_mac_film_project_action(*, confirmed=False, store=None):
    try:
        if confirmed is not True:
            raise ClosedDayError("confirmation_required", "Potvrď konečnost dat 6. října na Macu.")
        return (store or production_store()).close_mac_day(DAY, confirmed=True)
    except ClosedDayError as error:
        return {"ok": False, "error": error.code, "message": str(error)}
    except (OSError, ValueError, KeyError, sqlite3.DatabaseError):
        return {"ok": False, "error": "storage_unavailable", "message": "Projekt nelze bezpečně ověřit nebo uložit."}


def camino_mac_film_project_status(*, store=None):
    try:
        return (store or production_store()).day_status(DAY)
    except (OSError, ValueError, KeyError, sqlite3.DatabaseError):
        return {"ok": False, "error": "storage_unavailable", "message": "Projekt nelze nyní na Macu ověřit."}
