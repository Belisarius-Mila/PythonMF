from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agents import function_tool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAYMENT_CASES_DIR = PROJECT_ROOT / "data" / "private" / "payment_cases"
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
SAFE_ID_PATTERN = re.compile(r"[^a-z0-9_.-]+")
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")

SAVE_WORDS = (
    "uloz",
    "ulož",
    "ulozit",
    "uložit",
    "zkopiruj",
    "zkopíruj",
    "archivuj",
)
DOCUMENT_WORDS = (
    "faktura",
    "fakturu",
    "priloha",
    "příloha",
    "prilohu",
    "přílohu",
    "dokument",
    "pdf",
)


@dataclass(frozen=True)
class PaymentDocumentSaveResult:
    case_id: str
    created: bool
    destination: Path
    manifest: Path
    message: str


@function_tool
def save_payment_case_document(
    case_id: str,
    source_path: str,
    document_type: str = "invoice",
    description: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Copy a local invoice/document into the private payment case archive."""
    return save_payment_case_document_text(
        case_id=case_id,
        source_path=source_path,
        document_type=document_type,
        description=description,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def save_payment_case_document_text(
    case_id: str,
    source_path: str,
    document_type: str = "invoice",
    description: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_PAYMENT_CASES_DIR,
    now: datetime | None = None,
) -> str:
    try:
        safe_case_id = _safe_case_id(case_id)
    except ValueError as exc:
        return f"Ulozeni dokumentu k platebnimu pripadu bylo odmitnuto: {exc}"
    source = _resolve_allowed_source(source_path)
    if isinstance(source, str):
        return source

    if not user_confirmed or not has_explicit_payment_document_save_confirmation(
        case_id=safe_case_id,
        filename=source.name,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat case_id {safe_case_id}, nazev souboru "
            f"{source.name} a jasny souhlas s ulozenim faktury/prilohy. "
            "Bez toho na disk nic nekopiruji."
        )

    try:
        result = save_payment_case_document_file(
            case_id=safe_case_id,
            source=source,
            document_type=document_type,
            description=description,
            vault_dir=vault_dir,
            now=now,
        )
    except ValueError as exc:
        return f"Ulozeni dokumentu k platebnimu pripadu bylo odmitnuto: {exc}"

    status = "ulozeno" if result.created else "uz existuje"
    return (
        f"Stav: {status}. Case ID: {result.case_id}. "
        f"Dokument: {_relative_to_project(result.destination)}. "
        f"Manifest: {_relative_to_project(result.manifest)}. "
        f"{result.message}"
    )


def save_payment_case_document_file(
    case_id: str,
    source: Path,
    document_type: str = "invoice",
    description: str = "",
    vault_dir: Path = DEFAULT_PAYMENT_CASES_DIR,
    now: datetime | None = None,
) -> PaymentDocumentSaveResult:
    source = source.resolve(strict=True)
    _validate_source_file(source)

    safe_case_id = _safe_case_id(case_id)
    case_dir = vault_dir / safe_case_id
    docs_dir = case_dir / "documents"
    manifest_path = case_dir / "documents_manifest.json"
    docs_dir.mkdir(parents=True, exist_ok=True)

    digest = _sha256_file(source)
    manifest = _load_manifest(manifest_path, case_id=safe_case_id)
    for document in manifest["documents"]:
        if document.get("sha256") == digest:
            return PaymentDocumentSaveResult(
                case_id=safe_case_id,
                created=False,
                destination=case_dir / str(document.get("stored_path")),
                manifest=manifest_path,
                message="Dokument se stejnym obsahem uz je u platebniho pripadu ulozen.",
            )

    archive_time = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    stored_name = _next_document_name(
        docs_dir=docs_dir,
        source_name=source.name,
        document_type=document_type,
        index=len(manifest["documents"]) + 1,
    )
    destination = docs_dir / stored_name
    shutil.copy2(source, destination)

    manifest["documents"].append(
        {
            "document_type": _safe_document_type(document_type),
            "description": _safe_description(description),
            "original_filename": source.name,
            "stored_path": str(destination.relative_to(case_dir)),
            "source_path": str(_relative_to_project(source)),
            "size_bytes": source.stat().st_size,
            "sha256": digest,
            "saved_at": archive_time.isoformat(),
            "safety_flags": {
                "local_sensitive_archive": True,
                "do_not_commit": True,
                "source_was_local_file": True,
            },
        }
    )
    _write_manifest(manifest_path, manifest)

    return PaymentDocumentSaveResult(
        case_id=safe_case_id,
        created=True,
        destination=destination,
        manifest=manifest_path,
        message="Dokument byl zkopirovan do soukromeho archivu platebniho pripadu.",
    )


def has_explicit_payment_document_save_confirmation(
    case_id: str,
    filename: str,
    confirmation_text: str,
) -> bool:
    normalized = confirmation_text.casefold()
    return (
        case_id.casefold() in normalized
        and filename.casefold() in normalized
        and any(word in normalized for word in SAVE_WORDS)
        and any(word in normalized for word in DOCUMENT_WORDS)
    )


def _resolve_allowed_source(source_path: str) -> Path | str:
    if re.search(r"https?://", source_path, re.IGNORECASE):
        return "Ulozeni dokumentu bylo odmitnuto: source_path musi byt lokalni soubor, ne URL."

    candidate = Path(source_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return f"Ulozeni dokumentu bylo odmitnuto: soubor neexistuje: {source_path}"

    allowed_roots = (
        PROJECT_ROOT / "data",
        Path("/private/tmp"),
    )
    if not any(_is_relative_to(resolved, root.resolve()) for root in allowed_roots):
        return (
            "Ulozeni dokumentu bylo odmitnuto: zdroj musi byt v projektove slozce "
            "`data/` nebo v docasne slozce `/private/tmp`."
        )
    return resolved


def _validate_source_file(source: Path) -> None:
    if not source.is_file():
        raise ValueError("source_path musi ukazovat na soubor.")
    size = source.stat().st_size
    if size <= 0:
        raise ValueError("soubor je prazdny.")
    if size > MAX_DOCUMENT_BYTES:
        raise ValueError("soubor je vetsi nez bezpecny limit 50 MB.")


def _load_manifest(path: Path, case_id: str) -> dict[str, object]:
    if not path.exists():
        return {"case_id": case_id, "documents": []}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("documents"), list):
        raise ValueError("documents_manifest.json ma neocekavany format.")
    return data


def _write_manifest(path: Path, manifest: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _next_document_name(
    docs_dir: Path,
    source_name: str,
    document_type: str,
    index: int,
) -> str:
    extension = Path(source_name).suffix
    stem = Path(source_name).stem
    safe_stem = SAFE_FILENAME_PATTERN.sub("-", stem).strip("-") or "document"
    safe_type = _safe_document_type(document_type)
    candidate = f"{index:03d}_{safe_type}_{safe_stem}{extension}"
    counter = index
    while (docs_dir / candidate).exists():
        counter += 1
        candidate = f"{counter:03d}_{safe_type}_{safe_stem}{extension}"
    return candidate


def _safe_case_id(case_id: str) -> str:
    normalized = SAFE_ID_PATTERN.sub("-", case_id.casefold().strip()).strip("-")
    if not normalized:
        raise ValueError("case_id nesmi byt prazdne.")
    return normalized[:120]


def _safe_document_type(document_type: str) -> str:
    normalized = SAFE_ID_PATTERN.sub("-", document_type.casefold().strip()).strip("-")
    return normalized[:40] or "document"


def _safe_description(description: str) -> str:
    cleaned = re.sub(r"https?://\S+", "[URL redigovano]", description)
    return " ".join(cleaned.split())[:500]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
