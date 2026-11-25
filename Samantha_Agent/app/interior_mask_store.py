"""Transactional SQLite pilot store, isolated from family room data."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from contextlib import closing

from PIL import Image
import io

from app.interior_masks import SIZE, composite, png, sample_image, validate_layers

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data/private/interior_architect_v2/pilot.sqlite3"


class MaskConflict(ValueError):
    pass


class InteriorMaskStore:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path).resolve()

    def state(self):
        empty = {"revision": 0, "layers": [], "variants": [], "base_sha256": hashlib.sha256(self.image()).hexdigest()}
        if not self.path.exists():
            return empty
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0 and not db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                return empty
            if version != 1:
                raise ValueError("Nepodporovaná verze úložiště.")
            revision, body = db.execute("SELECT revision, body FROM draft WHERE id=1").fetchone()
            empty.update(revision=revision, layers=json.loads(body))
            empty["variants"] = [
                {"id": row[0], "title": row[1], "report": json.loads(row[2])}
                for row in db.execute("SELECT id,title,report FROM variants ORDER BY id DESC")
            ]
        return empty

    def image(self, variant=None):
        if variant is None:
            if not self.path.exists():
                return sample_image()
            with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as db:
                version = db.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    return sample_image()
                if version != 1:
                    raise ValueError("Nepodporovaná verze úložiště.")
                return db.execute("SELECT image FROM original WHERE id=1").fetchone()[0]
        if not isinstance(variant, str) or not variant.isdigit() or len(variant) > 18 or not self.path.exists():
            raise ValueError("Obrázek není dostupný.")
        with closing(sqlite3.connect(f"{self.path.as_uri()}?mode=ro", uri=True)) as db:
            row = db.execute("SELECT image FROM variants WHERE id=?", (int(variant),)).fetchone()
        if row is None:
            raise ValueError("Obrázek není dostupný.")
        return row[0]

    def execute(self, payload):
        if not isinstance(payload, dict) or set(payload) != {
            "action", "request_id", "expected_revision", "base_sha256", "layers", "title", "color", "feather"
        }:
            raise ValueError("Neplatný příkaz.")
        action = payload["action"]
        if action not in ("save", "variant", "copy"):
            raise ValueError("Neplatná operace.")
        if not isinstance(payload["request_id"], str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", payload["request_id"]):
            raise ValueError("Neplatná identita operace.")
        if type(payload["expected_revision"]) is not int or payload["expected_revision"] < 0:
            raise ValueError("Neplatná revize.")
        if not isinstance(payload["title"], str) or not 1 <= len(payload["title"].strip()) <= 120:
            raise ValueError("Doplň název varianty.")
        if not isinstance(payload["color"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", payload["color"]):
            raise ValueError("Neplatná barva.")
        if type(payload["feather"]) is not int or not 0 <= payload["feather"] <= 20:
            raise ValueError("Neplatné vyhlazení okraje.")
        validate_layers(payload["layers"], SIZE)
        base = self.image()
        if payload["base_sha256"] != hashlib.sha256(base).hexdigest():
            raise MaskConflict("Pracovní obrázek se změnil. Obnov stav.")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # One transaction contains draft, immutable PNG, report and operation receipt.
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Nepodporovaná verze úložiště.")
            db.execute("CREATE TABLE IF NOT EXISTS original(id INTEGER PRIMARY KEY, image BLOB)")
            db.execute("INSERT OR IGNORE INTO original VALUES(1,?)", (base,))
            db.execute("CREATE TABLE IF NOT EXISTS draft(id INTEGER PRIMARY KEY, revision INTEGER, body TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS variants(id INTEGER PRIMARY KEY, title TEXT, image BLOB, report TEXT, layers TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY, fingerprint TEXT, result TEXT)")
            db.execute("INSERT OR IGNORE INTO draft VALUES(1,0,'[]')")
            db.execute("PRAGMA user_version=1")
            old = db.execute("SELECT fingerprint,result FROM operations WHERE id=?", (payload["request_id"],)).fetchone()
            if old:
                if old[0] != fingerprint:
                    raise MaskConflict("Tato operace již má jiný obsah.")
                return json.loads(old[1])
            revision = db.execute("SELECT revision FROM draft WHERE id=1").fetchone()[0]
            if revision != payload["expected_revision"]:
                raise MaskConflict("Na serveru je novější revize. Místní práci můžeš uložit jako kopii.")
            layers = json.dumps(payload["layers"], ensure_ascii=False)
            result = {"ok": True, "revision": revision+1}
            if action in ("variant", "copy"):
                candidate = png(Image.new("RGB", SIZE, payload["color"]))
                image, report = composite(base, candidate, payload["layers"], payload["feather"])
                cursor = db.execute("INSERT INTO variants(title,image,report,layers) VALUES(?,?,?,?)",
                                    (payload["title"].strip(), image, json.dumps(report), layers))
                result.update(variant_id=cursor.lastrowid, report=report)
            if action == "copy":
                db.execute("UPDATE draft SET revision=? WHERE id=1", (revision+1,))
            else:
                db.execute("UPDATE draft SET revision=?,body=? WHERE id=1", (revision+1, layers))
            db.execute("INSERT INTO operations VALUES(?,?,?)", (payload["request_id"], fingerprint, json.dumps(result)))
            return result


def interior_mask_action(payload, *, store=None):
    try:
        return (store or InteriorMaskStore()).execute(payload)
    except MaskConflict as exc:
        return {"ok": False, "error": "conflict", "message": str(exc)}
    except (ValueError, TypeError) as exc:
        return {"ok": False, "error": "invalid_request", "message": str(exc)}
    except (OSError, sqlite3.Error):
        return {"ok": False, "error": "storage_error", "message": "Ověř stav uložené operace. Rozepsaná práce zůstává v zařízení."}
