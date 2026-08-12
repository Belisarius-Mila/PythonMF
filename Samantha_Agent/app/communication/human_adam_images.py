"""Private, confirmed image candidates for the Human–Adam chat."""

from __future__ import annotations

import base64
import binascii
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import atomic_write_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANDIDATE_ROOT = (
    PROJECT_ROOT / "data" / "private" / "communication" / "human_adam_image_candidates"
)
HUMAN_ADAM_WORKSTREAM_ID = "layer-human-adam-development"
IMAGE_CANDIDATE_ID_RE = re.compile(r"img_[0-9a-f]{32}")
CLIENT_MESSAGE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")
IMAGE_REQUEST_RE = re.compile(
    r"\b(?:vytvoř|vytvor|vygeneruj|nakresli|udělej|udelej|navrhni)\b"
    r"[\s\S]{0,120}\b(?:obrázek|obrazek|ilustraci|ilustrace|grafiku|vizuál|vizual)\b"
    r"|\b(?:obrázek|obrazek|ilustraci|ilustrace|grafiku|vizuál|vizual)\b"
    r"[\s\S]{0,120}\b(?:vytvoř|vytvor|vygeneruj|nakresli|udělej|udelej|navrhni)\b",
    re.IGNORECASE,
)
ALLOWED_STATUSES = frozenset({"prepared", "generating", "generated", "approved", "rejected"})
ALLOWED_IMAGE_FILES = frozenset({"image.png", "image.jpg", "image.webp"})
MAX_IMAGE_BYTES = 25 * 1024 * 1024
DEFAULT_PARAMETERS = {
    "model": "gpt-image-2",
    "size": "1024x1024",
    "quality": "low",
    "output_format": "png",
}


class HumanAdamImageError(RuntimeError):
    """Raised when an image candidate operation cannot be completed safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_image_generation_request(text: str) -> bool:
    return bool(IMAGE_REQUEST_RE.search(str(text or "").strip()))


def prepare_image_prompt(text: str) -> tuple[str, dict[str, str]]:
    request = str(text or "").strip()
    if not request:
        raise HumanAdamImageError("Požadavek na obrázek je prázdný.")
    if not is_image_generation_request(request):
        raise HumanAdamImageError("Text není jednoznačný požadavek na vytvoření obrázku.")
    if len(request) > 8_000:
        raise HumanAdamImageError("Požadavek na obrázek je příliš dlouhý.")

    folded = request.casefold()
    parameters = dict(DEFAULT_PARAMETERS)
    if any(marker in folded for marker in ("na šířku", "na sirku", "landscape")):
        parameters["size"] = "1536x1024"
    elif any(marker in folded for marker in ("na výšku", "na vysku", "portrait")):
        parameters["size"] = "1024x1536"
    if any(
        marker in folded
        for marker in (
            "vysoká kvalita",
            "vysoka kvalita",
            "vysoké kvalitě",
            "vysoke kvalite",
            "high quality",
        )
    ):
        parameters["quality"] = "high"

    prompt = f"Vytvoř jeden obrázek podle tohoto zadání:\n\n{request}"
    return prompt, parameters


def generation_confirmation(candidate_id: str) -> str:
    clean_id = validate_candidate_id(candidate_id)
    return f"POTVRZUJI GENEROVANI OBRAZKU {clean_id}"


def validate_candidate_id(candidate_id: str) -> str:
    clean_id = str(candidate_id or "").strip()
    if not IMAGE_CANDIDATE_ID_RE.fullmatch(clean_id):
        raise HumanAdamImageError("Kandidát obrázku má neplatné ID.")
    return clean_id


def validate_client_message_id(client_message_id: str) -> str:
    clean_id = str(client_message_id or "").strip()
    if not CLIENT_MESSAGE_ID_RE.fullmatch(clean_id):
        raise HumanAdamImageError("Požadavek nemá platné ID chatové zprávy.")
    return clean_id


def _image_kind(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image.png", "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image.jpg", "image/jpeg"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image.webp", "image/webp"
    raise HumanAdamImageError("Generátor nevrátil podporovaný obrazový formát.")


def _atomic_create_bytes(path: Path, payload: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    temp_path = Path(temp_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp_path, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise HumanAdamImageError("Soubor této verze už existuje; nic nebylo přepsáno.") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temp_path.unlink(missing_ok=True)


def generate_image_bytes(
    *,
    prompt: str,
    parameters: dict[str, str],
    client: Any | None = None,
) -> bytes:
    if client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise HumanAdamImageError("Generování obrázku není nakonfigurované.")
        from openai import OpenAI

        client = OpenAI()
    response = client.images.generate(
        model=parameters["model"],
        prompt=prompt,
        n=1,
        size=parameters["size"],
        quality=parameters["quality"],
        output_format=parameters["output_format"],
    )
    data = getattr(response, "data", None)
    encoded = getattr(data[0], "b64_json", None) if data else None
    if not encoded:
        raise HumanAdamImageError("Generátor nevrátil obrazová data.")
    try:
        raw = base64.b64decode(str(encoded), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HumanAdamImageError("Generátor vrátil neplatná obrazová data.") from exc
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise HumanAdamImageError("Vygenerovaný obrázek má nepovolenou velikost.")
    _image_kind(raw)
    return raw


class HumanAdamImageCandidateStore:
    """Persist candidate metadata and bytes under one private allowlisted root."""

    def __init__(self, root: Path = DEFAULT_CANDIDATE_ROOT):
        self.root = Path(root).resolve()
        self._lock = threading.RLock()

    def _candidate_dir(self, candidate_id: str) -> Path:
        clean_id = validate_candidate_id(candidate_id)
        candidate_dir = (self.root / clean_id).resolve()
        if candidate_dir.parent != self.root:
            raise HumanAdamImageError("Kandidát obrázku je mimo povolený adresář.")
        return candidate_dir

    def _metadata_path(self, candidate_id: str) -> Path:
        return self._candidate_dir(candidate_id) / "candidate.json"

    def _save(self, record: dict[str, Any]) -> None:
        candidate_id = validate_candidate_id(str(record.get("candidate_id") or ""))
        record["updated_at"] = utc_now()
        atomic_write_json(self._metadata_path(candidate_id), record, ensure_ascii=False, indent=2)

    def _load(self, candidate_id: str) -> dict[str, Any]:
        import json

        metadata_path = self._metadata_path(candidate_id)
        try:
            loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise HumanAdamImageError("Kandidát obrázku neexistuje.") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise HumanAdamImageError("Kandidáta obrázku nelze bezpečně načíst.") from exc
        if not isinstance(loaded, dict) or loaded.get("schema_version") != 1:
            raise HumanAdamImageError("Kandidát obrázku má neznámé schéma.")
        if str(loaded.get("candidate_id") or "") != validate_candidate_id(candidate_id):
            raise HumanAdamImageError("Kandidát obrázku má nekonzistentní ID.")
        if str(loaded.get("status") or "") not in ALLOWED_STATUSES:
            raise HumanAdamImageError("Kandidát obrázku má neplatný stav.")
        if loaded.get("status") == "generating":
            loaded["status"] = "prepared"
            loaded["generation_note"] = "Předchozí generování bylo přerušeno; vyžaduje nové potvrzení."
            self._save(loaded)
        return loaded

    def prepare(self, *, request_text: str, client_message_id: str) -> dict[str, Any]:
        clean_message_id = validate_client_message_id(client_message_id)
        prompt, parameters = prepare_image_prompt(request_text)
        with self._lock:
            for existing in self.list_records():
                if existing.get("client_message_id") == clean_message_id:
                    return existing
            candidate_id = f"img_{uuid.uuid4().hex}"
            now = utc_now()
            record: dict[str, Any] = {
                "schema_version": 1,
                "candidate_id": candidate_id,
                "version": 1,
                "client_message_id": clean_message_id,
                "request_text": str(request_text).strip(),
                "prompt": prompt,
                "parameters": parameters,
                "status": "prepared",
                "image_file": "",
                "mime_type": "",
                "created_at": now,
                "updated_at": now,
                "decided_at": "",
                "generation_note": "",
            }
            self._candidate_dir(candidate_id).mkdir(parents=True, exist_ok=False)
            self._save(record)
            return record

    def generate(
        self,
        *,
        candidate_id: str,
        confirmation: str,
        client: Any | None = None,
    ) -> dict[str, Any]:
        clean_id = validate_candidate_id(candidate_id)
        if str(confirmation or "").strip() != generation_confirmation(clean_id):
            raise HumanAdamImageError("Placené generování vyžaduje samostatné přesné potvrzení.")
        with self._lock:
            record = self._load(clean_id)
            if record["status"] != "prepared":
                raise HumanAdamImageError("Tento kandidát už nelze znovu generovat.")
            record["status"] = "generating"
            record["generation_note"] = ""
            self._save(record)
            try:
                raw = generate_image_bytes(
                    prompt=str(record["prompt"]),
                    parameters=dict(record["parameters"]),
                    client=client,
                )
                image_file, mime_type = _image_kind(raw)
                target = self._candidate_dir(clean_id) / image_file
                _atomic_create_bytes(target, raw)
                record["image_file"] = image_file
                record["mime_type"] = mime_type
                record["status"] = "generated"
                record["generation_note"] = ""
                self._save(record)
                return record
            except Exception:
                record["status"] = "prepared"
                record["generation_note"] = "Generování selhalo; před dalším pokusem je nutné nové potvrzení."
                self._save(record)
                raise

    def decide(self, *, candidate_id: str, decision: str) -> dict[str, Any]:
        clean_decision = str(decision or "").strip().casefold()
        if clean_decision not in {"approve", "reject"}:
            raise HumanAdamImageError("Rozhodnutí kandidáta není platné.")
        with self._lock:
            record = self._load(candidate_id)
            if record["status"] != "generated":
                raise HumanAdamImageError("Rozhodnout lze pouze právě vygenerovanou verzi.")
            record["status"] = "approved" if clean_decision == "approve" else "rejected"
            record["decided_at"] = utc_now()
            self._save(record)
            return record

    def image_path(self, candidate_id: str) -> tuple[Path, str]:
        with self._lock:
            record = self._load(candidate_id)
            if record["status"] not in {"generated", "approved", "rejected"}:
                raise HumanAdamImageError("Obrázek tohoto kandidáta ještě není dostupný.")
            image_file = str(record.get("image_file") or "")
            if image_file not in ALLOWED_IMAGE_FILES or Path(image_file).name != image_file:
                raise HumanAdamImageError("Kandidát odkazuje na nepovolený obrazový soubor.")
            candidate_dir = self._candidate_dir(candidate_id)
            try:
                target = (candidate_dir / image_file).resolve(strict=True)
            except FileNotFoundError as exc:
                raise HumanAdamImageError("Obrazový soubor kandidáta chybí.") from exc
            if target.parent != candidate_dir or self.root not in target.parents or not target.is_file():
                raise HumanAdamImageError("Obrazový soubor je mimo adresář kandidáta.")
            with target.open("rb") as handle:
                expected_mime = _image_kind(handle.read(16))[1]
            if expected_mime != str(record.get("mime_type") or ""):
                raise HumanAdamImageError("Typ obrazového souboru neodpovídá kandidátovi.")
            return target, expected_mime

    def list_records(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(self.root.iterdir()):
            if path.is_dir() and IMAGE_CANDIDATE_ID_RE.fullmatch(path.name):
                try:
                    records.append(self._load(path.name))
                except HumanAdamImageError:
                    continue
        return sorted(records, key=lambda item: str(item.get("created_at") or ""))[-100:]

    def public(self, record: dict[str, Any]) -> dict[str, Any]:
        candidate_id = validate_candidate_id(str(record.get("candidate_id") or ""))
        status = str(record.get("status") or "")
        generated = status in {"generated", "approved", "rejected"}
        return {
            "candidate_id": candidate_id,
            "version": int(record.get("version") or 1),
            "client_message_id": str(record.get("client_message_id") or ""),
            "prompt": str(record.get("prompt") or ""),
            "parameters": dict(record.get("parameters") or {}),
            "status": status,
            "created_at": str(record.get("created_at") or ""),
            "updated_at": str(record.get("updated_at") or ""),
            "decided_at": str(record.get("decided_at") or ""),
            "generation_note": str(record.get("generation_note") or ""),
            "confirmation_text": generation_confirmation(candidate_id) if status == "prepared" else "",
            "image_url": f"/api/human-adam/images/file?id={candidate_id}" if generated else "",
        }

    def public_list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self.public(record) for record in self.list_records()]


HUMAN_ADAM_IMAGE_STORE = HumanAdamImageCandidateStore()


def _require_human_adam_workstream(service: Any) -> None:
    if str(service.active_workstream_id or "") != HUMAN_ADAM_WORKSTREAM_ID:
        raise HumanAdamImageError("Obrázkové kandidáty jsou dostupné pouze v proudu Human–Adam.")


def human_adam_image_candidates_action(
    *, service: Any, store: HumanAdamImageCandidateStore = HUMAN_ADAM_IMAGE_STORE
) -> dict[str, Any]:
    try:
        _require_human_adam_workstream(service)
        return {"ok": True, "candidates": store.public_list()}
    except (HumanAdamImageError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_images_failed", "message": str(exc), "candidates": []}


def human_adam_image_prepare_action(
    payload: dict[str, Any],
    *,
    service: Any,
    store: HumanAdamImageCandidateStore = HUMAN_ADAM_IMAGE_STORE,
) -> dict[str, Any]:
    try:
        _require_human_adam_workstream(service)
        record = store.prepare(
            request_text=str(payload.get("request_text") or ""),
            client_message_id=str(payload.get("client_message_id") or ""),
        )
        return {"ok": True, "candidate": store.public(record)}
    except (HumanAdamImageError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_image_prepare_failed", "message": str(exc)}


def human_adam_image_generate_action(
    payload: dict[str, Any],
    *,
    service: Any,
    store: HumanAdamImageCandidateStore = HUMAN_ADAM_IMAGE_STORE,
    client: Any | None = None,
) -> dict[str, Any]:
    try:
        _require_human_adam_workstream(service)
        record = store.generate(
            candidate_id=str(payload.get("candidate_id") or ""),
            confirmation=str(payload.get("confirmation") or ""),
            client=client,
        )
        return {"ok": True, "candidate": store.public(record)}
    except (HumanAdamImageError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_image_generate_failed", "message": str(exc)}
    except Exception:
        return {
            "ok": False,
            "status": "human_adam_image_generate_failed",
            "message": "Generování obrázku selhalo bez zveřejnění citlivých podrobností.",
        }


def human_adam_image_decision_action(
    payload: dict[str, Any],
    *,
    service: Any,
    store: HumanAdamImageCandidateStore = HUMAN_ADAM_IMAGE_STORE,
) -> dict[str, Any]:
    try:
        _require_human_adam_workstream(service)
        record = store.decide(
            candidate_id=str(payload.get("candidate_id") or ""),
            decision=str(payload.get("decision") or ""),
        )
        return {"ok": True, "candidate": store.public(record)}
    except (HumanAdamImageError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_image_decision_failed", "message": str(exc)}


def human_adam_image_file_action(
    candidate_id: str,
    *,
    service: Any,
    store: HumanAdamImageCandidateStore = HUMAN_ADAM_IMAGE_STORE,
) -> dict[str, Any]:
    try:
        _require_human_adam_workstream(service)
        path, mime_type = store.image_path(candidate_id)
        return {"ok": True, "path": path, "mime_type": mime_type, "filename": path.name}
    except (HumanAdamImageError, OSError, ValueError) as exc:
        return {"ok": False, "status": "human_adam_image_file_failed", "message": str(exc)}
