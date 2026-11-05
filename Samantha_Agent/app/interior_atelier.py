"""Local interior workbench: explicit image intake and versioned human proposals.

No model, network operation, deletion, legacy import or App Server side effect.
Constructors and reads never materialize storage.
"""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import io
import json
import math
import os
import re
import stat
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.work_repository import JsonWorkRepository, RepositoryMutation

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data/private/neuberk_interier_design/atelier"
MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_IMAGE_PIXELS = 32_000_000
SOURCE_KINDS = ("photo", "plan", "inspiration")
ID_RE = re.compile(r"[0-9a-f]{32}")
REQUEST_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")
DRAFT_FIELDS = {"title", "prompt", "source_ids", "image_source_id", "annotations", "fixed_elements"}


class AtelierError(ValueError):
    pass


class AtelierConflict(AtelierError):
    pass


def _identifier(value):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise AtelierError("Neplatná identita projektu, místnosti nebo podkladu.")
    return value


def _text(value, limit, *, required=False):
    if not isinstance(value, str) or len(value) > limit or "\0" in value:
        raise AtelierError("Text má nepovolený formát nebo délku.")
    result = value.strip()
    if required and not result:
        raise AtelierError("Doplň název nebo text.")
    return result


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _fingerprint(value):
    return _hash(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _new_id():
    return uuid.uuid4().hex


def _safe_path(path):
    """Reject links in every existing component, including dangling links."""
    absolute = Path(os.path.abspath(path))
    for component in (*reversed(absolute.parents), absolute):
        if component.is_symlink():
            raise AtelierError("Úložiště obsahuje nepovolený odkaz.")
    return absolute


def _annotations(value):
    if not isinstance(value, list) or len(value) > 100:
        raise AtelierError("Kresba má příliš mnoho tahů.")
    result, total = [], 0
    for stroke in value:
        if not isinstance(stroke, list) or not 2 <= len(stroke) <= 1000:
            raise AtelierError("Kresba obsahuje neplatný tah.")
        total += len(stroke)
        if total > 5000:
            raise AtelierError("Kresba je příliš podrobná; ulož menší počet tahů.")
        points = []
        for point in stroke:
            if not isinstance(point, list) or len(point) != 2 or any(
                type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n <= 1 for n in point
            ):
                raise AtelierError("Body kresby musí zůstat uvnitř obrázku.")
            points.append([round(n, 6) for n in point])
        result.append(points)
    return result


def _image(data):
    if not isinstance(data, str) or not data or len(data) > (MAX_IMAGE_BYTES + 2) // 3 * 4:
        raise AtelierError("Obrázek musí být PNG, JPEG nebo WebP, nejvýše 6 MiB.")
    try:
        raw = base64.b64decode(data, validate=True)
        if not 0 < len(raw) <= MAX_IMAGE_BYTES:
            raise AtelierError("Obrázek překračuje velikost 6 MiB.")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                # iPhone JPEGs may contain an auxiliary MPO image (e.g. a gain map).
                # Decode only their primary photo; retain every original byte.
                image.seek(0)
                if image.format not in {"PNG", "JPEG", "MPO", "WEBP"}:
                    raise AtelierError("Nepodporovaný formát obrázku. Použij PNG, JPEG nebo WebP.")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise AtelierError("Příliš velké rozlišení obrázku; maximum je 32 milionů pixelů.")
                mime = "image/jpeg" if image.format == "MPO" else Image.MIME[image.format]
                if image.format != "MPO" and getattr(image, "n_frames", 1) != 1:
                    raise AtelierError("Použij jeden statický obrázek.")
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.seek(0)
                image = ImageOps.exif_transpose(image)
                image.load()
                width, height = image.size
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
                outputs = {"original": raw}
                for name, size in (("preview", 1400), ("thumbnail", 256)):
                    resized = image.copy()
                    resized.thumbnail((size, size))
                    output = io.BytesIO()
                    # New pixel buffers do not inherit EXIF, location or text metadata.
                    clean = Image.new(resized.mode, resized.size)
                    clean.paste(resized)
                    clean.save(output, format="PNG")
                    outputs[name] = output.getvalue()
        return outputs, mime, width, height
    except (binascii.Error, UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise AtelierError("Obrázek nelze bezpečně načíst. Použij platné PNG, JPEG nebo WebP.") from exc


class InteriorAtelier:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root).absolute()
        self.path = self.root / "atelier.json"
        self.repository = JsonWorkRepository(self.path, default={"schema_version": 1, "projects": {}})

    def _check(self):
        for path in (self.path, self.path.with_name(self.path.name + ".lock"), self.root / "objects"):
            _safe_path(path)

    def _read(self):
        self._check()
        data = self.repository.read()
        if data.get("schema_version") != 1 or not isinstance(data.get("projects"), dict):
            raise AtelierError("Úložiště Ateliéru má neznámý formát.")
        return data

    @staticmethod
    def _room(data, project_id, room_id):
        try:
            project = data["projects"][_identifier(project_id)]
            return project, project["rooms"][_identifier(room_id)]
        except KeyError as exc:
            raise AtelierError("Projekt nebo místnost nebyly nalezené.") from exc

    @staticmethod
    def _draft(room, base_id):
        if base_id != "base":
            _identifier(base_id)
            if base_id not in room["variants"]:
                raise AtelierError("Výchozí varianta nebyla nalezena.")
        if base_id in room["drafts"]:
            return copy.deepcopy(room["drafts"][base_id])
        parent = room["variants"].get(base_id)
        initial = {key: copy.deepcopy(parent[key]) for key in DRAFT_FIELDS} if parent else {
            "title": "", "prompt": "", "source_ids": [], "image_source_id": "",
            "annotations": [], "fixed_elements": "",
        }
        return {**initial, "revision": 0}

    def state(self, project_id="", room_id="", base_id="base"):
        data = self._read()
        projects = [{"id": p["id"], "title": p["title"],
                     "rooms": [{"id": r["id"], "title": r["title"]} for r in p["rooms"].values()]}
                    for p in data["projects"].values()]
        result = {"ok": True, "projects": projects, "room": None, "draft": None,
                  "limits": {"image_bytes": MAX_IMAGE_BYTES, "image_pixels": MAX_IMAGE_PIXELS},
                  "capabilities": {"image_generation": False, "geometry": False}}
        if project_id or room_id:
            _, room = self._room(data, project_id, room_id)
            result["room"] = copy.deepcopy(room)
            result["room"].pop("drafts")
            result["draft"] = self._draft(room, base_id)
        return result

    def _blob_read(self, filename, digest):
        if not re.fullmatch(r"[0-9a-f]{64}\.(original|preview|thumbnail)", filename):
            raise AtelierError("Neplatná identita souboru.")
        path = _safe_path(self.root / "objects" / filename)
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 12 * 1024 * 1024:
                raise AtelierError("Soubor nemá povolený formát.")
            raw = handle.read(info.st_size + 1)
        if len(raw) != info.st_size or _hash(raw) != digest:
            raise AtelierError("Obsah souboru se změnil; nelze ho vydat.")
        return raw

    def asset(self, project_id, room_id, asset_id, view="preview"):
        if view not in {"original", "preview", "thumbnail"}:
            raise AtelierError("Neplatný pohled na podklad.")
        _, room = self._room(self._read(), project_id, room_id)
        source = room["sources"].get(_identifier(asset_id))
        if not source:
            raise AtelierError("Podklad nepatří vybrané místnosti.")
        file = source["files"][view]
        return self._blob_read(file["name"], file["sha256"]), source["mime"] if view == "original" else "image/png"

    def _blob_write(self, filename, raw):
        path = _safe_path(self.root / "objects" / filename)
        if path.exists():
            self._blob_read(filename, _hash(raw))
            return
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def execute(self, payload):
        if not isinstance(payload, dict):
            raise AtelierError("Neplatný požadavek Ateliéru.")
        action = payload.get("action")
        fields = {
            "create_project": {"title", "room_title"},
            "create_room": {"project_id", "title"},
            "add_source": {"project_id", "room_id", "title", "kind", "data"},
            "save_draft": {"project_id", "room_id", "base_id", "expected_revision", "draft"},
            "create_variant": {"project_id", "room_id", "base_id", "expected_revision"},
            "add_note": {"project_id", "room_id", "base_id", "text"},
        }
        if not isinstance(action, str) or action not in fields or set(payload) != fields[action] | {"action", "request_id"}:
            raise AtelierError("Neznámá operace nebo neúplný požadavek.")
        request_id = payload["request_id"]
        if not isinstance(request_id, str) or not REQUEST_RE.fullmatch(request_id):
            raise AtelierError("Požadavek nemá platnou identitu.")
        try:
            fingerprint = _fingerprint(payload)
        except (ValueError, TypeError) as exc:
            raise AtelierError("Požadavek obsahuje neplatnou hodnotu.") from exc
        self._check()
        # Directory creation belongs exclusively to explicit writes.
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root.chmod(0o700)
        objects = self.root / "objects"
        objects.mkdir(exist_ok=True, mode=0o700)

        def mutate(data):
            if data.get("schema_version") != 1:
                raise AtelierError("Nepodporovaný formát úložiště.")
            projects = data["projects"]
            now = _now()
            result = {"fingerprint": fingerprint}
            if action == "create_project":
                if len(projects) >= 50:
                    raise AtelierError("Ateliér už obsahuje maximální počet projektů.")
                project_id, room_id = _new_id(), _new_id()
                room = self._new_room(room_id, _text(payload["room_title"], 120, required=True), now)
                projects[project_id] = {"id": project_id, "title": _text(payload["title"], 120, required=True),
                                        "created_at": now, "rooms": {room_id: room}}
                result.update(project_id=project_id, room_id=room_id)
            elif action == "create_room":
                project = projects.get(_identifier(payload["project_id"]))
                if project is None:
                    raise AtelierError("Projekt nebyl nalezen.")
                if len(project["rooms"]) >= 50:
                    raise AtelierError("Projekt už obsahuje maximální počet místností.")
                room_id = _new_id()
                project["rooms"][room_id] = self._new_room(room_id, _text(payload["title"], 120, required=True), now)
                result.update(project_id=project["id"], room_id=room_id)
            else:
                _, room = self._room(data, payload["project_id"], payload["room_id"])
                if action == "add_source":
                    result.update(self._add_source(room, payload, now))
                else:
                    base_id = payload["base_id"]
                    draft = self._draft(room, base_id)
                    if action == "add_note":
                        if len(room["notes"]) >= 1000:
                            raise AtelierError("Místnost už obsahuje maximální počet poznámek.")
                        note_id = _new_id()
                        room["notes"].append({"id": note_id, "base_id": base_id,
                                              "text": _text(payload["text"], 12000, required=True), "created_at": now})
                        result["note_id"] = note_id
                    else:
                        if type(payload["expected_revision"]) is not int or payload["expected_revision"] != draft["revision"]:
                            raise AtelierConflict("Zadání mezitím změnil jiný klient. Načti aktuální stav; rozepsaný text zůstává v editoru.")
                        if action == "save_draft":
                            saved = self._validate_draft(room, payload["draft"])
                            room["drafts"][base_id] = {**saved, "revision": draft["revision"] + 1}
                            result["revision"] = draft["revision"] + 1
                        else:
                            self._validate_draft(room, {k: draft[k] for k in DRAFT_FIELDS})
                            if not draft["title"]:
                                raise AtelierError("Před uložením variantu pojmenuj.")
                            if len(room["variants"]) >= 200:
                                raise AtelierError("Místnost už obsahuje maximální počet variant.")
                            variant_id = _new_id()
                            room["variants"][variant_id] = {**{k: copy.deepcopy(draft[k]) for k in DRAFT_FIELDS},
                                "id": variant_id, "parent_id": None if base_id == "base" else base_id,
                                "created_at": now, "kind": "human_proposal"}
                            result["variant_id"] = variant_id
                room["updated_at"] = now
            return RepositoryMutation(data, result)

        outcome = self.repository.transact(mutate, operation_id=request_id)
        if outcome.result.get("fingerprint") != fingerprint:
            raise AtelierConflict("Stejná identita požadavku už patří jinému obsahu.")
        return {"ok": True, **{k: v for k, v in outcome.result.items() if k != "fingerprint"},
                "replayed": outcome.idempotent_replay}

    @staticmethod
    def _new_room(room_id, title, now):
        return {"id": room_id, "title": title, "created_at": now, "updated_at": now,
                "sources": {}, "variants": {}, "drafts": {}, "notes": []}

    def _add_source(self, room, payload, now):
        if payload["kind"] not in SOURCE_KINDS:
            raise AtelierError("Vyber skutečný stav, rozměrový podklad nebo inspiraci.")
        title = _text(payload["title"], 200, required=True)
        if len(room["sources"]) >= 500:
            raise AtelierError("Místnost už obsahuje maximální počet podkladů.")
        outputs, mime, width, height = _image(payload["data"])
        digest = _hash(outputs["original"])
        for source in room["sources"].values():
            if source["files"]["original"]["sha256"] == digest and source["kind"] == payload["kind"]:
                return {"asset_id": source["id"], "already_present": True}
        files = {}
        for part, raw in outputs.items():
            filename = digest + "." + part
            self._blob_write(filename, raw)
            files[part] = {"name": filename, "sha256": _hash(raw), "bytes": len(raw)}
        asset_id = _new_id()
        room["sources"][asset_id] = {"id": asset_id, "title": title, "kind": payload["kind"],
                                    "mime": mime, "width": width, "height": height,
                                    "created_at": now, "files": files}
        return {"asset_id": asset_id, "already_present": False}

    @staticmethod
    def _validate_draft(room, draft):
        if not isinstance(draft, dict) or set(draft) != DRAFT_FIELDS:
            raise AtelierError("Zadání nemá úplný formát.")
        source_ids = draft["source_ids"]
        if not isinstance(source_ids, list) or len(source_ids) > 100 or any(
            not isinstance(i, str) or i not in room["sources"] for i in source_ids
        ) or len(set(source_ids)) != len(source_ids):
            raise AtelierError("Vybrané podklady nepatří této místnosti nebo se opakují.")
        image_id = draft["image_source_id"]
        if not isinstance(image_id, str) or (image_id and image_id not in source_ids):
            raise AtelierError("Pracovní obrázek musí být mezi vybranými podklady.")
        annotations = _annotations(draft["annotations"])
        if annotations and not image_id:
            raise AtelierError("Kreslené poznámky potřebují pracovní obrázek.")
        return {"title": _text(draft["title"], 120), "prompt": _text(draft["prompt"], 12000),
                "fixed_elements": _text(draft["fixed_elements"], 2000), "source_ids": list(source_ids),
                "image_source_id": image_id, "annotations": annotations}
