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
from urllib.parse import parse_qs

from camino.film.closed_day import (
    ClosedDayError, ClosedDayStore, _private_directory, _store_lock,
)
from camino.film.project import fingerprint, write_json
from camino.domain.codec import decode_text
from camino.domain.codec import decode_trip
from camino.domain.model import TextHistory
from camino.domain.revision_store import RevisionStore
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

    def available_dates(self):
        """Read candidate days, excluding hidden/private-only inputs.

        Listing is not closure: close_mac_day still checks the full inventory,
        receipts and bytes after the owner confirms the selected day.
        """
        with self._metadata_connection() as metadata:
            metadata.execute("BEGIN")
            state = metadata.execute("SELECT exports_blocked,reconciliation_required FROM meta WHERE singleton=1").fetchone()
            if state is None or state[0] or state[1]:
                raise ClosedDayError("archive_blocked", "Archiv nejprve vyžaduje dokončení obnovy.")
            days = [json.loads(row[0]) for row in metadata.execute("SELECT body FROM days")]
            days = {d["id"]: self._date(d["local_date"]) for d in days if d["trip_id"] == self.trip_id}
            unique = Counter(days.values())
            moments = [json.loads(row[0]) for row in metadata.execute("SELECT body FROM moments")]
            permitted = {m["id"]: days[m["day_id"]] for m in moments
                         if m.get("privacy") == "diary" and m.get("hidden") is False
                         and m.get("day_id") in days and unique[days[m["day_id"]]] == 1}
            assets = [json.loads(row[0]) for row in metadata.execute("SELECT body FROM assets")]
            return sorted({permitted[a["moment_id"]] for a in assets
                           if a.get("moment_id") in permitted and a.get("media_kind") in ("photo", "video")}, reverse=True)

    def travel_projects(self):
        """Owner-only catalog through read-only connections; never migrate an archive."""
        with self._metadata_connection() as metadata:
            metadata.execute("BEGIN")
            state = metadata.execute("SELECT exports_blocked,reconciliation_required FROM meta WHERE singleton=1").fetchone()
            if state is None or state[0] or state[1]:
                raise ClosedDayError("archive_blocked", "Archiv nejprve vyžaduje dokončení obnovy.")
            return [RevisionStore._project_summary(metadata, decode_trip(json.loads(row[0])))
                    for row in metadata.execute("SELECT body FROM trips ORDER BY id")]

    def project_ids(self):
        if not self.root.exists():
            return []
        result = []
        for path in self.root.iterdir():
            if path.is_symlink() or not path.is_dir():
                continue
            try:
                if str(UUID(path.name)) == path.name:
                    result.append(path.name)
            except ValueError:
                continue
        return sorted(result)

    def project_status(self, project_id):
        return self._confirmed_status(project_id)

    def text_choices(self, manifest, references=None):
        """Read permitted accepted text; a saved film pins an exact revision.

        This supplements legacy media manifests without rewriting any project,
        archive or edit. Text provenance must be wholly inside this allowed day.
        """
        with self._metadata_connection() as db:
            db.execute("BEGIN")
            state = db.execute("SELECT server_id,epoch,exports_blocked,reconciliation_required "
                               "FROM meta WHERE singleton=1").fetchone()
            if (not state or tuple(state[:2]) != (manifest["server_id"], manifest["epoch"])
                    or state[2] or state[3]):
                raise ClosedDayError("archive_blocked", "Texty nelze nyní bezpečně ověřit.")
            moments = [json.loads(r[0]) for r in db.execute("SELECT body FROM moments")]
            moments = [m for m in moments if m["day_id"] == manifest["day_id"]]
            ids = {m["id"] for m in moments}
            assets = [json.loads(r[0]) for r in db.execute("SELECT body FROM assets")]
            assets = [a for a in assets if a["moment_id"] in ids]
            inventory = {
                "moments": sorted(({k: m[k] for k in
                    ("id", "revision", "privacy", "hidden", "chapter_date")} for m in moments), key=lambda m: m["id"]),
                "assets": sorted(({k: a[k] for k in
                    ("id", "moment_id", "media_kind", "byte_count", "sha256")} for a in assets), key=lambda a: a["id"]),
            }
            if fingerprint(inventory) != manifest["inventory_sha256"]:
                raise ClosedDayError("source_changed", "Povolené podklady dne se změnily.")
            allowed = {m["id"] for m in moments if m["privacy"] == "diary" and m["hidden"] is False}
            safe_ids = allowed | {a["id"] for a in assets if a["moment_id"] in allowed}
            requested = {r["revision_id"]: r for r in references} if references is not None else None
            if references is not None and any(requested[r["revision_id"]] != r for r in references):
                raise ClosedDayError("text_changed", "Stejná textová revize má rozpornou vazbu.")
            histories, bodies = {}, {}
            for moment in moments:
                if moment["id"] not in allowed:
                    continue
                history = TextHistory()
                for row in db.execute("SELECT body FROM text_revisions WHERE moment_id=? ORDER BY rowid", (moment["id"],)):
                    body = json.loads(row[0])
                    revision = decode_text(body)
                    if revision.moment_id != moment["id"]:
                        raise ClosedDayError("text_changed", "Text nemá platnou vazbu na Moment.")
                    history = history.add(revision)
                    bodies[revision.id] = body
                histories[moment["id"]] = history
            safe = {}
            def safe_revision(revision_id):
                # Iterative traversal also rejects cycles without a recursion limit
                # or leaking text from another/private Moment through ancestry.
                visiting, pending = set(), [(revision_id, False)]
                while pending:
                    current, closing = pending.pop()
                    if current in safe:
                        continue
                    body = bodies.get(current)
                    if body is None:
                        safe[current] = False
                        continue
                    links = [*body["source_ids"]]
                    if body["parent_revision_id"] is not None:
                        links.append(body["parent_revision_id"])
                    if closing:
                        safe[current] = all(sid in safe_ids or safe.get(sid, False) for sid in links)
                        visiting.discard(current)
                    elif current in visiting:
                        safe[current] = False
                    else:
                        visiting.add(current)
                        pending.append((current, True))
                        pending.extend((sid, False) for sid in links if sid not in safe_ids)
                return safe.get(revision_id, False)
            result = []
            for moment in moments:
                if moment["id"] not in allowed:
                    continue
                history = histories[moment["id"]]
                chosen = ([v for v in history.revisions if v.id in requested] if requested is not None
                          else [history.reader_revision] if history.reader_revision else [])
                for revision in chosen:
                    if not revision.content.strip() or not safe_revision(revision.id):
                        continue
                    reference = {"moment_id": moment["id"], "revision_id": revision.id,
                                 "sha256": fingerprint(bodies[revision.id])}
                    if requested is not None and requested[revision.id] != reference:
                        continue
                    result.append({"reference": reference, "text": revision.content,
                        "title": moment.get("title", ""), "role": revision.role,
                        "captured_local": moment["captured"]["local_wall"]})
            if requested is not None and {r["reference"]["revision_id"] for r in result} != set(requested):
                raise ClosedDayError("text_changed", "Použitý text už není v povolených přijatých podkladech.")
            return sorted(result, key=lambda r: (r["captured_local"] or "", r["reference"]["revision_id"]))

    def day_status(self, local_date: str, *, project_id: str | None = None):
        local_date = self._date(local_date)
        result = {"ok": True, "exists": False, "valid": False, "local_date": local_date,
                  "trip_id": self.trip_id}
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


def production_store(*, trip_id=None, project_id=None):
    # Configuration validation is read-only; never instantiate archive stores
    # that create schemas, migrate databases or recover upload journals.
    from scripts import camino_service_control as service
    config = service.load_config(service.ROOT)
    store = MacFilmProjectStore(service.ROOT.parents[1] / "CaminoFilmProjects", **{
        k: config[k] for k in ("metadata_db", "media_db", "media_root", "trip_id")})
    if project_id is not None:
        project_id = canonical_id(project_id)
        directory = store.root / project_id
        if directory.is_symlink() or not directory.is_dir():
            raise ClosedDayError("project_missing", "Filmový projekt není dostupný.")
        bound_trip = canonical_id(store._read(directory / "manifest.json")["trip_id"])
        if trip_id is not None and canonical_id(trip_id) != bound_trip:
            raise ClosedDayError("project_mismatch", "Film nepatří vybrané cestě.")
        trip_id = bound_trip
    if trip_id is not None:
        trip_id = canonical_id(trip_id)
        if trip_id not in {p["id"] for p in store.travel_projects()}:
            raise ClosedDayError("trip_missing", "Vybraný projekt není v Mac archivu.")
        if trip_id != store.trip_id:
            store = MacFilmProjectStore(store.root, metadata_db=store.metadata_db,
                media_db=store.media_db, media_root=store.media_root, trip_id=trip_id)
    return store


def canonical_id(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError("Neplatný identifikátor projektu.")
    return value


def film_project_query(query, *, allow_date=False, allow_trip=False):
    values = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=3)
    allowed = {"project_id"} | ({"local_date"} if allow_date else set()) | ({"trip_id"} if allow_trip else set())
    if set(values) - allowed:
        raise ValueError("Neznámý parametr filmového projektu.")
    if any(len(v) != 1 or not v[0] for v in values.values()):
        raise ValueError("Nejednoznačný výběr filmového projektu.")
    result = {k: v[0] for k, v in values.items()}
    if "local_date" in result:
        MacFilmProjectStore._date(result["local_date"])
    for key in ("project_id", "trip_id"):
        if key in result:
            canonical_id(result[key])
    return result


def camino_mac_film_project_action(*, confirmed=False, local_date=None, trip_id=None, store=None):
    try:
        if confirmed is not True:
            raise ClosedDayError("confirmation_required", "Potvrď konečnost dat vybraného dne na Macu.")
        selected = store or (production_store(trip_id=trip_id) if trip_id is not None else production_store())
        if trip_id is not None and selected.trip_id != canonical_id(trip_id):
            raise ValueError("Project mismatch")
        return selected.close_mac_day(DAY if local_date is None else local_date, confirmed=True)
    except ClosedDayError as error:
        return {"ok": False, "error": error.code, "message": str(error)}
    except (OSError, ValueError, KeyError, sqlite3.DatabaseError):
        return {"ok": False, "error": "storage_unavailable", "message": "Projekt nelze bezpečně ověřit nebo uložit."}


def camino_mac_film_project_status(*, local_date=None, project_id=None, trip_id=None, store=None):
    try:
        selected = store or (production_store(trip_id=trip_id, project_id=project_id)
                            if trip_id is not None or project_id is not None else production_store())
        if trip_id is not None and selected.trip_id != canonical_id(trip_id):
            raise ValueError("Project mismatch")
        return selected.day_status(DAY if local_date is None else local_date, project_id=project_id)
    except (OSError, ValueError, KeyError, sqlite3.DatabaseError):
        return {"ok": False, "error": "storage_unavailable", "message": "Projekt nelze nyní na Macu ověřit."}
