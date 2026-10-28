"""Private one-day film edits and durable jobs over a read-only Camino archive."""
from __future__ import annotations

import copy
import fcntl
import hashlib
import io
import json
import math
import os
import re
import sqlite3
import stat
import subprocess
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import UUID, uuid4

from app.camino_film_workshop import DAY, production_store
from app.camino_film_photo import MAX_PHOTO_BYTES, decode_photo
from app.camino_film_layers import validate_layer, validate_display
from app.file_persistence import FilePersistenceError, atomic_write_json
from camino.film.closed_day import ClosedDayError, _private_directory, _store_lock
from camino.film.project import FilmError, digest, fingerprint, write_json
from camino.domain.project_lifecycle import shared


def editor_database(editor):
    return getattr(editor.store, 'metadata_db', None) or editor.store.metadata.path

MAX_MS = 3_600_000
TEXT_CARD_FIT_ERROR = "Text se na kartu čitelně nevejde. Zkrať jej nebo rozděl do více karet."


def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise FilmError("Neplatná struktura střihu nebo požadavku.")


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise FilmError("Čas nebo revize není v povoleném rozsahu.")


def gain(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise FilmError("Hlasitost musí být mezi 0 a 1.")


def identifier(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise FilmError("Neplatný identifikátor.")
    return value


def text_reference(value):
    exact(value, "moment_id revision_id sha256")
    identifier(value["moment_id"]); identifier(value["revision_id"])
    if not isinstance(value["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", value["sha256"]):
        raise FilmError("Text nemá platnou vazbu na přijatou revizi.")


def text_references(draft):
    refs = [r["text_source"] for r in draft["shots"] if "text_source" in r]
    refs += [r["text_source"] for r in draft.get("cards", [])]
    refs += [r["photo_text"]["text_source"] for r in draft["shots"]
             if r.get("photo_text", {}).get("text_source") is not None]
    for ref in refs:
        text_reference(ref)
    return refs


def timeline_shots(draft):
    """Interleave explicit text cards with media without changing legacy drafts."""
    cards = draft.get("cards", [])
    def after(anchor):
        return [{"card_id": c["id"], "in_ms": 0, "out_ms": c["duration_ms"],
                 "title": c["text"], "gain": 0, "included": c["included"]}
                for c in cards if c["after_asset_id"] == anchor]
    rows = after(None)
    for row in draft["shots"]:
        rows.append(row)
        rows.extend(after(row["asset_id"]))
    return rows


def resolved_voices(draft):
    """Photo identity is authoritative; absolute timing remains for legacy edits."""
    starts, cursor = {}, 0
    photos = {r["asset_id"]: r for r in draft["shots"]}
    for row in timeline_shots(draft):
        if row["included"]:
            if "asset_id" in row:
                starts[row["asset_id"]] = cursor
            cursor += row["out_ms"] - row["in_ms"]
    voices = []
    for row in draft["voices"]:
        item = dict(row)
        if row.get("photo_asset_id") is not None and row["included"]:
            sid = row["photo_asset_id"]
            if sid not in starts or row["out_ms"] - row["in_ms"] > photos[sid]["out_ms"]:
                raise FilmError("Komentář přesahuje svou fotografii nebo je fotografie vyřazená. Prodluž ji nebo komentář vyřaď.")
            item["at_ms"] = starts[sid]
        voices.append(item)
    for sid, row in photos.items():
        layer = row.get("photo_text", {})
        n = layer.get("narration")
        if row["included"] and layer.get("mode") == "narration" and n and n["included"]:
            if n["duration_ms"] > row["out_ms"]:
                raise FilmError("Čtení přesahuje fotografii. Prodluž ji podle komentáře nebo vyber kratší text.")
            voices.append({"narration_id": n["id"], "at_ms": starts[sid], "in_ms": 0,
                "out_ms": n["duration_ms"], "gain": 1, "included": True})
    return voices


def validate_draft(draft, manifest, *, for_render=False):
    exact(draft, "shots voices duck_gain" + (" cards" if isinstance(draft, dict) and "cards" in draft else ""))
    gain(draft["duck_gain"])
    sources = {s["asset_id"]: s for s in manifest["sources"]}
    total, spans = 0, []
    for group, kind in (("shots", "visual"), ("voices", "audio")):
        rows = draft[group]
        expected = {sid for sid, s in sources.items()
                    if (s["media_kind"] == "audio") == (kind == "audio")}
        if not isinstance(rows, list) or len(rows) > 256 or len(rows) != len(expected):
            raise FilmError("Střih musí zachovat všechny nabídky; vyřazení označ výslovně.")
        seen = set()
        for row in rows:
            exact(row, "asset_id in_ms out_ms gain included " + ("title" if kind == "visual" else "at_ms")
                  + (" text_source" if kind == "visual" and isinstance(row, dict) and "text_source" in row else "")
                  + (" photo_text" if kind == "visual" and isinstance(row, dict) and "photo_text" in row else "")
                  + (" photo_asset_id" if kind == "audio" and isinstance(row, dict) and "photo_asset_id" in row else ""))
            sid = row["asset_id"]
            if not isinstance(sid, str) or sid not in expected or sid in seen:
                raise FilmError("Střih odkazuje na cizí nebo duplicitní zdroj.")
            seen.add(sid)
            source = sources[sid]
            if "photo_text" in row:
                if source["media_kind"] != "photo":
                    raise FilmError("Textová vrstva patří pouze k fotografii.")
                validate_layer(row["photo_text"], exact=exact, identifier=identifier,
                               integer=integer, text_reference=text_reference)
                if for_render:
                    validate_display(row)
            if "photo_asset_id" in row:
                target = sources.get(row["photo_asset_id"])
                if target is None or target["media_kind"] != "photo":
                    raise FilmError("Komentář vyžaduje fotografii z tohoto filmu.")
            if type(row["included"]) is not bool:
                raise FilmError("Zařazení musí být výslovná volba.")
            integer(row["in_ms"], 0, MAX_MS)
            integer(row["out_ms"], 1, MAX_MS)
            gain(row["gain"])
            if row["out_ms"] <= row["in_ms"]:
                raise FilmError("Konec musí následovat po začátku úseku.")
            if source["media_kind"] == "photo":
                if row["in_ms"] != 0 or not 100 <= row["out_ms"] <= 300_000:
                    raise FilmError("Fotografie má délku od 0,1 do 300 sekund.")
            elif type(source["duration_ms"]) is not int or row["out_ms"] > source["duration_ms"]:
                raise FilmError("Úsek překračuje délku původního média.")
            if kind == "visual":
                title = row["title"]
                if not isinstance(title, str) or len(title) > 140 or any(ord(c) < 32 for c in title):
                    raise FilmError("Titulek může mít nejvýše 140 znaků bez řídicích znaků.")
                if row["included"]:
                    total += row["out_ms"] - row["in_ms"]
            else:
                integer(row["at_ms"], 0, MAX_MS)
    cards = draft.get("cards", [])
    if not isinstance(cards, list) or len(cards) > 32:
        raise FilmError("Jeden film může mít nejvýše 32 textových karet.")
    card_ids = set()
    visual_ids = {r["asset_id"] for r in draft["shots"]}
    for card in cards:
        exact(card, "id after_asset_id text duration_ms included text_source")
        card_id = identifier(card["id"])
        if card_id in card_ids or card["after_asset_id"] is not None and card["after_asset_id"] not in visual_ids:
            raise FilmError("Textová karta nemá jednoznačné místo v tomto filmu.")
        card_ids.add(card_id)
        if (not isinstance(card["text"], str) or not card["text"].strip() or len(card["text"]) > 1000
                or any(ord(c) < 32 and c != "\n" for c in card["text"])):
            raise FilmError("Textová karta vyžaduje 1 až 1000 znaků bez řídicích znaků kromě nového řádku.")
        integer(card["duration_ms"], 100, 300_000)
        if type(card["included"]) is not bool:
            raise FilmError("Zařazení textové karty musí být výslovná volba.")
        if card["included"]:
            total += card["duration_ms"]
    text_references(draft)
    for voice in resolved_voices(draft):
        if voice["included"]:
            spans.append((voice["at_ms"], voice["at_ms"] + voice["out_ms"] - voice["in_ms"]))
    integer(total, 100, MAX_MS)
    spans.sort()
    if any(end > total for _, end in spans):
        raise FilmError("Hlas přesahuje obraz. Prodluž fotografii, přidej záběry nebo hlas vědomě zkrať.")
    if any(b[0] < a[1] for a, b in zip(spans, spans[1:])):
        raise FilmError("Hlasové části se překrývají. Posuň jejich umístění.")
    return total


class FilmEditor:
    def __init__(self, store, *, day=DAY):
        self.store = store
        self.day = day

    def inputs(self, project_id=None, *, cached_files=False):
        status = (self.store.project_status(identifier(project_id), cached_files=cached_files) if project_id is not None
                  else self.store.day_status(self.day, cached_files=cached_files))
        if not status.get("valid"):
            raise FilmError("Projekt nebo jeho zdroje už nejsou platné. Ověř konečnou Mac sadu.")
        folder = self.store.root / status["project_id"]
        manifest = self.store._read(folder / "manifest.json")
        if len(manifest["sources"]) > 256:
            raise FilmError("První editor podporuje nejvýše 256 zdrojů jednoho dne.")
        return folder, manifest

    def verify_texts(self, manifest, draft, *, project_id=None, allow_deleted=True):
        refs = text_references(draft)
        if refs:
            choices = self.store.text_choices(manifest, refs)
            originals = {c["reference"]["revision_id"]: c["text"] for c in choices}
            for row in draft["shots"]:
                layer = row.get("photo_text", {})
                ref = layer.get("text_source")
                if ref and "original_text" in layer and layer["original_text"] != originals[ref["revision_id"]]:
                    raise FilmError("Původní text z iPhonu nelze přepsat. Uprav pouze text pro čtení.")
        from app.camino_film_narration import narration_paths
        return narration_paths(self, manifest, draft, project_id=project_id, allow_deleted=allow_deleted)

    @shared(editor_database)
    def photo_bytes(self, project_id, asset_id, *, image_kind="photo"):
        """Return a metadata-free PNG of a currently permitted original photo."""
        project_id, asset_id = identifier(project_id), identifier(asset_id)
        sizes = {"photo": (4096, 4096), "image-preview": (1600, 1600), "thumbnail": (256, 256)}
        if image_kind not in sizes:
            raise FilmError("Neplatný typ náhledu.")
        _, manifest = self.inputs(project_id, cached_files=True)
        before = fingerprint(manifest)
        source = next((item for item in manifest["sources"]
                       if item.get("asset_id") == asset_id and item.get("media_kind") == "photo"), None)
        if source is None:
            raise FilmError("Fotografie není v aktuálním projektu povolená.")
        size = source.get("byte_count")
        if type(size) is not int or not 0 < size <= MAX_PHOTO_BYTES:
            raise FilmError("Fotografie překračuje povolený limit.")
        objects = Path(self.store.media.objects)
        if objects.is_symlink():
            raise FilmError("Původní fotografie nemá bezpečné umístění.")
        path = objects / f"{asset_id}.bin"
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size != size:
                    raise FilmError("Původní fotografie neodpovídá uzavřeným vstupům.")
                original = handle.read(MAX_PHOTO_BYTES + 1)
            if len(original) != size or hashlib.sha256(original).hexdigest() != source.get("sha256"):
                raise FilmError("Původní fotografie neodpovídá uzavřeným vstupům.")
            with decode_photo(original, size=sizes[image_kind], fast_preview=image_kind != "photo") as photo:
                output = io.BytesIO()
                photo.save(output, "PNG")
                data = output.getvalue()
            _, current = self.inputs(project_id, cached_files=True)
            current_source = next((item for item in current["sources"]
                                   if item.get("asset_id") == asset_id and item.get("media_kind") == "photo"), None)
            if fingerprint(current) != before or current_source != source:
                raise FilmError("Povolení fotografie se během dekódování změnilo.")
            return data
        except FilmError:
            raise
        except Exception as error:
            raise FilmError("Fotografii nelze bezpečně dekódovat.") from error

    def revision(self, folder, manifest, number=None):
        paths = list(folder.glob("edit-r*.json"))
        for p in paths:
            if p.is_symlink() or not re.fullmatch(r"edit-r[0-9]{6}\.json", p.name):
                raise FilmError("Neplatná uložená revize střihu.")
        latest = max([1, *(int(p.stem[6:]) for p in paths)])
        number = latest if number is None else number
        integer(number, 1, latest)
        if number == 1:
            base = self.store._read(folder / "project-r1.json")
            sources = {s["asset_id"]: s for s in manifest["sources"]}
            draft = {"shots": [{"asset_id": s["asset_id"], "in_ms": s["in_ms"],
                "out_ms": s["out_ms"], "title": s["title"], "gain": 1, "included": True}
                for s in base["shots"]],
                "voices": [{"asset_id": sid, "at_ms": 0, "in_ms": 0,
                    "out_ms": sources[sid]["duration_ms"], "gain": 1, "included": False}
                    for sid in base["voice_choices"]], "duck_gain": 0.2}
            record = {"schema": 1, "scope": "camino-film-edit", "project_id": folder.name,
                      "revision": 1, "manifest_sha256": fingerprint(manifest), "draft": draft}
        else:
            record = self.store._read(folder / f"edit-r{number:06d}.json")
        if (record.get("schema") != 1 or record.get("scope") != "camino-film-edit"
                or record.get("project_id") != folder.name or record.get("revision") != number
                or record.get("manifest_sha256") != fingerprint(manifest)):
            raise FilmError("Revize není vázaná na tyto uzavřené vstupy.")
        validate_draft(record["draft"], manifest)
        return record

    def catalog(self):
        dates = self.store.available_dates()
        projects = []
        for project_id in self.store.project_ids():
            try:
                folder, manifest = self.inputs(project_id, cached_files=True)
                edit = self.revision(folder, manifest)
                jobs = self.jobs(folder)
                projects.append({"project_id": project_id, "local_date": manifest["local_date"],
                                 "revision": edit["revision"],
                                 "ready_exports": sum(j["state"] == "ready" and not j.get("source_asset_id") for j in jobs)})
            except (ClosedDayError, FilmError, OSError, ValueError, KeyError, TypeError):
                # Never expose stale titles/counts after privacy or input changes.
                continue
        projects.sort(key=lambda p: (p["local_date"], p["project_id"]), reverse=True)
        return {"ok": True, "days": [{"local_date": day} for day in dates], "projects": projects}

    def view(self, project_id=None):
        folder, manifest = self.inputs(project_id, cached_files=True)
        edit = self.revision(folder, manifest)
        self.verify_texts(manifest, edit["draft"], project_id=folder.name)
        draft = copy.deepcopy(edit["draft"])
        for row in draft["shots"]:
            layer = row.get("photo_text", {})
            if layer.get("text_source") and "original_text" not in layer:
                layer["original_text"] = self.store.text_choices(manifest, [layer["text_source"]])[0]["text"]
        from app.camino_film_narration import list_narrations
        from app.camino_film_orus import voice_profile
        return {"ok": True, "project_id": folder.name, "local_date": manifest["local_date"],
                "revision": edit["revision"], "draft": draft,
                "duration_ms": validate_draft(edit["draft"], manifest),
                "sources": [{"asset_id": s["asset_id"], "kind": s["media_kind"],
                    "duration_ms": s["duration_ms"], "title": s["title"],
                    "moment_id": s["moment_id"], "captured_local": s.get("capture_local_wall")}
                    for s in manifest["sources"]],
                "texts": self.store.text_choices(manifest),
                "jobs": self.jobs(folder), "narrations": list_narrations(self, folder, manifest),
                "narration_voice": voice_profile()}

    @shared(editor_database)
    def save(self, payload):
        exact(payload, "project_id expected_revision request_id draft")
        project_id = identifier(payload["project_id"])
        request_id = identifier(payload["request_id"])
        folder, manifest = self.inputs(project_id)
        validate_draft(payload["draft"], manifest)
        self.verify_texts(manifest, payload["draft"], project_id=folder.name)
        request_hash = fingerprint(payload)
        with _store_lock(self.store.root):
            self.verify_texts(manifest, payload["draft"], project_id=folder.name, allow_deleted=False)
            for path in folder.glob("edit-r*.json"):
                record = self.store._read(path)
                if record.get("request_id") == request_id:
                    if record.get("request_sha256") != request_hash:
                        raise FilmError("Stejný požadavek byl použitý pro jiný střih.")
                    return {"ok": True, "revision": record["revision"], "saved": True}
            latest = self.revision(folder, manifest)
            if type(payload["expected_revision"]) is not int or payload["expected_revision"] != latest["revision"]:
                raise FilmError("Střih už mezitím změnilo jiné okno. Načti poslední uloženou revizi.")
            number = latest["revision"] + 1
            integer(number, 2, 999999)
            record = {"schema": 1, "scope": "camino-film-edit", "project_id": project_id,
                "revision": number, "manifest_sha256": fingerprint(manifest),
                "request_id": request_id, "request_sha256": request_hash, "draft": copy.deepcopy(payload["draft"])}
            write_json(folder / f"edit-r{number:06d}.json", record)
        return {"ok": True, "revision": number, "saved": True}

    @staticmethod
    def worker_busy(folder):
        path = folder / ".render-worker"
        if not path.exists():
            return False
        if path.is_symlink():
            raise FilmError("Neplatný zámek exportu.")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                return False
            except BlockingIOError:
                return True
        finally:
            os.close(fd)

    def jobs(self, folder):
        root = folder / "jobs"
        if not root.exists():
            return []
        _private_directory(root)
        result = []
        directories = [p for p in root.iterdir() if not p.name.startswith(".") and not p.is_symlink() and p.is_dir()]
        for directory in sorted(directories, key=lambda p: (p / "request.json").stat().st_mtime_ns):
            if directory.name.startswith(".") or directory.is_symlink() or not directory.is_dir():
                continue
            identifier(directory.name)
            spec = self.store._read(directory / "request.json")
            state = self.store._read(directory / "status.json") if (directory / "status.json").exists() else {"state": "queued", "progress": 0}
            if state["state"] == "deleted":
                continue
            if state["state"] == "rendering" and not self.worker_busy(folder):
                state = {"state": "interrupted", "progress": 0}
            item = {"job_id": directory.name, "revision": spec["revision"], "profile": spec["profile"],
                "range": spec["range"], "state": state["state"], "progress": state.get("progress", 0)}
            if "source_asset_id" in spec:
                item["source_asset_id"] = spec["source_asset_id"]
            if state.get("error_code") == "text_card_does_not_fit":
                item["message"] = TEXT_CARD_FIT_ERROR
            if state["state"] == "ready":
                item["url"] = f'/api/camino/film/output/{folder.name}/{directory.name}'
                item["bytes"] = state["bytes"]
                # Older exports have no explicit completion clock. Read their
                # status-file time without rewriting any historical metadata.
                item["created_at"] = state.get("completed_at") or datetime.fromtimestamp(
                    (directory / "status.json").stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
                item["created_at_estimated"] = not bool(state.get("completed_at"))
            result.append(item)
        return result

    @shared(editor_database)
    def enqueue(self, payload, *, background=True):
        exact(payload, "project_id revision request_id profile range")
        folder, manifest = self.inputs(identifier(payload["project_id"]))
        identifier(payload["request_id"])
        edit = self.revision(folder, manifest, payload["revision"])
        self.verify_texts(manifest, edit["draft"], project_id=folder.name)
        if payload["profile"] not in ("preview", "final"):
            raise FilmError("Vyber náhled 720p nebo finále 1080p.")
        total = validate_draft(edit["draft"], manifest, for_render=True)
        if payload["range"] is not None:
            exact(payload["range"], "start_ms end_ms")
            start, end = payload["range"]["start_ms"], payload["range"]["end_ms"]
            integer(start, 0, total - 100); integer(end, start + 100, total)
            if payload["profile"] != "preview":
                raise FilmError("Dílčí úsek je určený jen pro pracovní náhled.")
        spec = {**payload, "edit_sha256": fingerprint(edit), "manifest_sha256": fingerprint(manifest)}
        return self._enqueue(folder, spec, background=background)

    def job_edit(self, folder, manifest, spec):
        """Source previews use an isolated full-video draft; saved edits stay immutable."""
        edit = self.revision(folder, manifest, spec["revision"])
        if "source_asset_id" not in spec:
            return edit
        sid = identifier(spec["source_asset_id"])
        source = next((s for s in manifest["sources"] if s["asset_id"] == sid), None)
        if source is None or source["media_kind"] not in ("video", "audio"):
            raise FilmError("Pro přímý náhled vyber video nebo komentář z uzavřené sady.")
        edit = copy.deepcopy(edit)
        if source["media_kind"] == "audio":
            return {**edit, "audio_preview": sid}
        if "cards" in edit["draft"]:
            edit["draft"]["cards"] = []
        for row in edit["draft"]["shots"]:
            row["included"] = row["asset_id"] == sid
            if row["included"]:
                row.update(in_ms=0, out_ms=source["duration_ms"], title="", gain=1)
        for row in edit["draft"]["voices"]:
            row["included"] = False
        validate_draft(edit["draft"], manifest)
        return edit

    @shared(editor_database)
    def source_preview(self, payload, *, background=True):
        exact(payload, "project_id asset_id request_id")
        folder, manifest = self.inputs(identifier(payload["project_id"]))
        identifier(payload["request_id"])
        spec = {"project_id": folder.name, "revision": 1, "request_id": payload["request_id"],
            "profile": "preview", "range": None, "source_asset_id": payload["asset_id"],
            "manifest_sha256": fingerprint(manifest)}
        spec["edit_sha256"] = fingerprint(self.job_edit(folder, manifest, spec))
        return self._enqueue(folder, spec, background=background)

    def _enqueue(self, folder, spec, *, background):
        with _store_lock(self.store.root):
            root = _private_directory(folder / "jobs")
            target = root / spec["request_id"]
            if target.exists():
                _private_directory(target)
                if (target / "status.json").exists() and self.store._read(target / "status.json").get("state") in ("deleted", "delete_pending"):
                    raise FilmError("Varianta byla trvale smazaná. Pro nový export zadej nový požadavek.")
                if self.store._read(target / "request.json") != spec:
                    raise FilmError("Stejné ID exportu bylo použité pro jinou revizi nebo úsek.")
            else:
                # Reopening a source reuses its verified derivative, independent of edit revision.
                if "source_asset_id" in spec:
                    for job in reversed(self.jobs(folder)):
                        if (job.get("source_asset_id") != spec["source_asset_id"]
                                or job["state"] not in ("ready", "queued", "rendering", "interrupted")):
                            continue
                        saved = self.store._read(root / job["job_id"] / "request.json")
                        if any(saved.get(k) != v for k, v in spec.items() if k != "request_id"):
                            continue
                        if job["state"] == "ready":
                            try:
                                self.output(folder.name, job["job_id"])
                            except (FilmError, OSError):
                                continue
                        target = root / job["job_id"]
                        break
                if target.exists():
                    pass
                elif sum(j["state"] in ("queued", "rendering", "interrupted") for j in self.jobs(folder)) >= 16:
                    raise FilmError("Ve frontě je již 16 exportů. Nejdříve dokonči existující úlohy.")
                else:
                    staging = _private_directory(root / (".pending-" + spec["request_id"]))
                    write_json(staging / "request.json", spec)
                    os.rename(staging, target)
        if background:
            self.start_worker(folder.name)
        return {"ok": True, "job_id": target.name, "queued": True}

    @staticmethod
    def start_worker(project_id):
        root = Path(__file__).resolve().parents[1]
        # launchd has a smaller PATH than Terminal. Extend only this film worker,
        # preserving the existing tool choice and leaving all running services alone.
        environment = os.environ.copy()
        environment["PATH"] = os.pathsep.join((environment.get("PATH") or os.defpath,
            "/opt/homebrew/bin", "/usr/local/bin"))
        # An explicitly queued job survives Cockpit reload/restart; this is not a service installation.
        subprocess.Popen([str(root / ".venv/bin/python"), str(root / "scripts/camino_film_editor.py"),
            "work", "--project-id", identifier(project_id)], cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, env=environment)

    @shared(editor_database)
    def run_queue(self, project_id):
        from app.camino_film_render import render_edit, render_audio_preview
        folder, _ = self.inputs(identifier(project_id))
        fd = os.open(folder / ".render-worker", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            while True:
                pending = [j for j in self.jobs(folder) if j["state"] in ("queued", "rendering")]
                if not pending:
                    return
                for job in pending:
                    directory = folder / "jobs" / job["job_id"]
                    attempt = _private_directory(directory / ("attempt-" + uuid4().hex))
                    state_path = directory / "status.json"
                    def progress(value):
                        atomic_write_json(state_path, {"state": "rendering", "progress": value})
                    try:
                        progress(0)
                        _, manifest = self.inputs(project_id)
                        spec = self.store._read(directory / "request.json")
                        edit = self.job_edit(folder, manifest, spec)
                        if fingerprint(edit) != spec["edit_sha256"] or fingerprint(manifest) != spec["manifest_sha256"]:
                            raise FilmError("Uložené podklady exportu se změnily.")
                        def revalidate():
                            _, current = self.inputs(project_id)
                            if (fingerprint(current) != spec["manifest_sha256"]
                                    or fingerprint(self.job_edit(folder, current, spec)) != spec["edit_sha256"]):
                                raise FilmError("Uložené podklady se během renderu změnily.")
                            if "source_asset_id" not in spec:
                                self.verify_texts(current, edit["draft"], project_id=folder.name)
                        revalidate()
                        if "audio_preview" in edit:
                            receipt = render_audio_preview(edit, manifest, self.store.media.objects,
                                attempt, revalidate=revalidate)
                        else:
                            paths = self.verify_texts(manifest, edit["draft"], project_id=folder.name)
                            receipt = render_edit(edit, manifest, self.store.media.objects, attempt,
                                spec["profile"], spec["range"], progress=progress,
                                revalidate=revalidate, **({"narration_paths": paths} if paths else {}))
                        revalidate()
                        atomic_write_json(state_path, {"state": "ready", "progress": 100,
                            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "output": str((attempt / "film.mp4").relative_to(directory)),
                            "bytes": receipt["bytes"], "sha256": receipt["sha256"]})
                    except Exception as error:
                        # FFmpeg paths, title text and raw private exceptions never become HTTP/log content.
                        atomic_write_json(state_path, {"state": "failed", "progress": 0,
                            "error_type": type(error).__name__,
                            **({"error_code": "text_card_does_not_fit"}
                               if type(error) is FilmError and str(error) == TEXT_CARD_FIT_ERROR else {})})
        finally:
            os.close(fd)

    def output(self, project_id, job_id, *, with_content_type=False):
        folder, manifest = self.inputs(identifier(project_id))
        directory = folder / "jobs" / identifier(job_id)
        if not directory.is_dir():
            raise FilmError("Export neexistuje.")
        _private_directory(folder / "jobs")
        _private_directory(directory)
        spec = self.store._read(directory / "request.json")
        edit = self.job_edit(folder, manifest, spec)
        if "source_asset_id" not in spec:
            self.verify_texts(manifest, edit["draft"], project_id=folder.name)
        if fingerprint(edit) != spec["edit_sha256"] or fingerprint(manifest) != spec["manifest_sha256"]:
            raise FilmError("Export už neodpovídá uloženým podkladům.")
        state = self.store._read(directory / "status.json")
        relative = state.get("output", "")
        if state["state"] != "ready" or not re.fullmatch(r"attempt-[a-f0-9]{32}/film\.mp4", relative):
            raise FilmError("Export ještě není hotový a ověřený.")
        target = directory / relative
        if target.parent.is_symlink() or target.is_symlink() or not target.is_file():
            raise FilmError("Export nemá bezpečný soubor.")
        if target.stat().st_size != state["bytes"] or digest(target) != state["sha256"]:
            raise FilmError("Hotový export byl poškozený.")
        if with_content_type:
            source = next((s for s in manifest["sources"] if s["asset_id"] == spec.get("source_asset_id")), None)
            return target, "audio/mp4" if source and source["media_kind"] == "audio" else "video/mp4"
        return target


@lru_cache(maxsize=64)
def production_editor(*, trip_id=None, project_id=None):
    return FilmEditor(production_store(trip_id=trip_id, project_id=project_id)
                      if trip_id is not None or project_id is not None else production_store())


def film_narration_import_action(payload, body):
    try:
        from app.camino_film_narration import import_narration
        editor = production_editor(project_id=identifier(payload["project_id"]))
        return import_narration(editor, payload, body)
    except FilmError as error:
        return {"ok": False, "message": str(error)}
    except (ClosedDayError, FilePersistenceError, sqlite3.DatabaseError, OSError, ValueError, KeyError, TypeError):
        return {"ok": False, "message": "Nahrávku nelze bezpečně importovat."}


def film_editor_action(operation, payload=None):
    try:
        if payload is not None and not isinstance(payload, dict):
            raise FilmError("Neplatná struktura filmového požadavku.")
        if operation == "trips":
            store = production_store()
            return {"ok": True, "trips": store.travel_projects(), "default_trip_id": store.trip_id}
        if operation == "catalog":
            exact(payload or {}, "trip_id" if payload else "")
            editor = production_editor(trip_id=identifier(payload["trip_id"])) if payload else production_editor()
        else:
            pid = (payload or {}).get("project_id")
            editor = production_editor(project_id=identifier(pid)) if pid is not None else production_editor()
        if operation == "catalog":
            result = editor.catalog()
            return {**result, "trip_id": editor.store.trip_id} if payload else result
        if operation == "view":
            exact(payload or {}, "project_id" if payload else "")
            return editor.view((payload or {}).get("project_id"))
        if operation == "save":
            return editor.save(payload)
        if operation == "render":
            return editor.enqueue(payload)
        if operation == "source":
            return editor.source_preview(payload)
        if operation == "narration":
            from app.camino_film_narration import prepare_narration
            return prepare_narration(editor, payload)
        if operation == "narration-trash":
            from app.camino_film_narration import trash_narration
            return trash_narration(editor, payload)
        if operation in ("delete-plan", "delete"):
            from app.camino_film_cleanup import deletion_plan, delete_export
            return (deletion_plan if operation == "delete-plan" else delete_export)(editor, payload)
        raise FilmError("Neznámá filmová operace.")
    except FilmError as error:
        return {"ok": False, "message": str(error)}
    except (ClosedDayError, FilePersistenceError, sqlite3.DatabaseError, OSError, ValueError, KeyError, TypeError):
        return {"ok": False, "message": "Střih nelze bezpečně ověřit nebo uložit. Znovu načti projekt a zkontroluj časy."}
