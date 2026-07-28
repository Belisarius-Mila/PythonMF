"""Private document boundary owned exclusively by Janička R2-Adam.

The store never derives its authority from the isolated project checkout.
Runtime code must pass the validated canonical private root explicitly.  All
user-controlled names are flat UTF-8 ``.txt`` filenames and every mutation is
confined to one fixed R2-Adam subtree below that root.
"""

from __future__ import annotations

import errno
import os
import stat
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.file_persistence import (
    FilePersistenceError,
    atomic_create_text,
    atomic_replace_text_under_external_lock,
    exclusive_file_lock,
    lock_path_for,
)


R2_DOCUMENTS_RELATIVE_ROOT = Path(
    "communication/workstreams/project-r2-adam-janicka/documents"
)
R2_DOCUMENT_TRASH_DIRNAME = "trash"
MAX_R2_DOCUMENT_NAME_BYTES = 180
MAX_R2_DOCUMENT_TEXT_BYTES = 10 * 1024 * 1024
_ALLOWED_NAME_PUNCTUATION = frozenset(" _-().")


class JanickaR2DocumentError(RuntimeError):
    """Raised when an R2 document operation cannot stay inside its boundary."""


class JanickaR2DocumentNotFoundError(JanickaR2DocumentError):
    """Raised when one expected R2 document does not exist."""


class JanickaR2DocumentExistsError(JanickaR2DocumentError):
    """Raised when create-only persistence would replace an existing document."""


class JanickaR2DocumentConfirmationError(JanickaR2DocumentError):
    """Raised when a trash operation lacks its exact human confirmation."""


@dataclass(frozen=True)
class JanickaR2DocumentInfo:
    """Redacted metadata for one managed document, without a private path."""

    name: str
    size_bytes: int
    modified_at: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "size_bytes": self.size_bytes,
            "modified_at": self.modified_at,
        }


@dataclass(frozen=True)
class JanickaR2TrashResult:
    """Redacted result of one confirmed, recoverable move to the private trash."""

    original_name: str
    trash_id: str
    moved_at: str

    def as_dict(self) -> dict[str, str]:
        return {
            "original_name": self.original_name,
            "trash_id": self.trash_id,
            "moved_at": self.moved_at,
        }


def normalize_r2_document_name(value: object) -> str:
    """Return one safe, flat ``.txt`` filename or fail closed."""

    raw = str(value or "")
    normalized = unicodedata.normalize("NFC", raw.strip())
    if (
        not normalized
        or normalized in {".", ".."}
        or "/" in normalized
        or "\\" in normalized
        or "\x00" in normalized
        or normalized.startswith(".")
        or normalized != Path(normalized).name
        or Path(normalized).suffix != ".txt"
        or len(normalized.encode("utf-8")) > MAX_R2_DOCUMENT_NAME_BYTES
    ):
        raise JanickaR2DocumentError(
            "Dokument musí mít bezpečný jednoduchý název s příponou .txt."
        )
    stem = normalized[:-4].strip()
    if not stem or any(
        not (character.isalnum() or character in _ALLOWED_NAME_PUNCTUATION)
        for character in normalized
    ):
        raise JanickaR2DocumentError(
            "Název dokumentu obsahuje nepovolené znaky."
        )
    return normalized


def r2_document_trash_confirmation(document_name: object) -> str:
    """Return the exact human phrase required for one recoverable removal."""

    name = normalize_r2_document_name(document_name)
    return f"Potvrzuji přesun dokumentu {name} do koše Janičky."


class JanickaR2DocumentStore:
    """Create, read, replace and trash text documents in one fixed private root."""

    def __init__(self, *, canonical_private_root: Path) -> None:
        supplied_root = Path(canonical_private_root)
        if not supplied_root.is_absolute():
            raise JanickaR2DocumentError(
                "Kanonický private kořen musí být předán jako absolutní cesta."
            )
        if (
            supplied_root.is_symlink()
            or not supplied_root.exists()
            or not supplied_root.is_dir()
        ):
            raise JanickaR2DocumentError(
                "Kanonický private kořen není bezpečně dostupný."
            )
        self._canonical_private_root = supplied_root.resolve(strict=True)
        self._document_root = (
            self._canonical_private_root / R2_DOCUMENTS_RELATIVE_ROOT
        )
        self._trash_root = self._document_root / R2_DOCUMENT_TRASH_DIRNAME

    def list_documents(self) -> tuple[JanickaR2DocumentInfo, ...]:
        """List redacted metadata without creating the private directory."""

        try:
            root = self._require_document_root(create=False)
        except JanickaR2DocumentNotFoundError:
            return ()
        rows: list[JanickaR2DocumentInfo] = []
        for candidate in root.iterdir():
            if candidate.name == R2_DOCUMENT_TRASH_DIRNAME or candidate.suffix != ".txt":
                continue
            name = normalize_r2_document_name(candidate.name)
            rows.append(self._document_info(self._require_regular_file(name)))
        return tuple(sorted(rows, key=lambda item: item.name.casefold()))

    def create_text(self, *, name: object, text: object) -> JanickaR2DocumentInfo:
        """Create one complete UTF-8 document without replacing any target."""

        safe_name = normalize_r2_document_name(name)
        safe_text = self._validate_text(text)
        root = self._require_document_root(create=True)
        target = self._candidate(root, safe_name)
        self._reject_existing_symlink_or_directory(target)
        try:
            atomic_create_text(target, safe_text, mode=0o600)
        except FilePersistenceError as exc:
            raise JanickaR2DocumentExistsError(
                "Dokument s tímto názvem už existuje."
            ) from exc
        return self._document_info(target)

    def read_text(self, name: object) -> str:
        """Read one managed UTF-8 document without following a symlink."""

        safe_name = normalize_r2_document_name(name)
        target = self._require_regular_file(safe_name)
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(target, flags)
        except OSError as exc:
            if exc.errno in {errno.ELOOP, errno.ENOENT}:
                raise JanickaR2DocumentNotFoundError(
                    "Dokument nebyl bezpečně nalezen."
                ) from exc
            raise JanickaR2DocumentError(
                "Dokument se nepodařilo bezpečně přečíst."
            ) from exc
        try:
            file_stat = os.fstat(descriptor)
            if (
                not stat.S_ISREG(file_stat.st_mode)
                or file_stat.st_size > MAX_R2_DOCUMENT_TEXT_BYTES
            ):
                raise JanickaR2DocumentError(
                    "Dokument nemá povolený typ nebo velikost."
                )
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                payload = handle.read(MAX_R2_DOCUMENT_TEXT_BYTES + 1)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if len(payload) > MAX_R2_DOCUMENT_TEXT_BYTES:
            raise JanickaR2DocumentError("Dokument překročil bezpečný limit.")
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise JanickaR2DocumentError(
                "Dokument není platný UTF-8 text."
            ) from exc

    def replace_text(
        self,
        *,
        name: object,
        text: object,
    ) -> JanickaR2DocumentInfo:
        """Atomically replace one existing managed document."""

        safe_name = normalize_r2_document_name(name)
        safe_text = self._validate_text(text)
        target = self._require_regular_file(safe_name)
        lock_path = lock_path_for(target)
        if lock_path.is_symlink():
            raise JanickaR2DocumentError(
                "Zámek dokumentu není bezpečný."
            )
        with exclusive_file_lock(target):
            target = self._require_regular_file(safe_name)
            atomic_replace_text_under_external_lock(target, safe_text)
        return self._document_info(target)

    def move_to_trash(
        self,
        *,
        name: object,
        confirmation: object,
    ) -> JanickaR2TrashResult:
        """Move one document to private trash after exact human confirmation."""

        safe_name = normalize_r2_document_name(name)
        required = r2_document_trash_confirmation(safe_name)
        if str(confirmation or "").strip() != required:
            raise JanickaR2DocumentConfirmationError(
                "Přesun do koše vyžaduje přesné potvrzení konkrétního dokumentu."
            )
        target = self._require_regular_file(safe_name)
        lock_path = lock_path_for(target)
        if lock_path.is_symlink():
            raise JanickaR2DocumentError(
                "Zámek dokumentu není bezpečný."
            )
        with exclusive_file_lock(target):
            target = self._require_regular_file(safe_name)
            trash_root = self._require_trash_root()
            now = datetime.now(timezone.utc).replace(microsecond=0)
            trash_id = (
                f"{now.strftime('%Y%m%dT%H%M%SZ')}_"
                f"{uuid.uuid4().hex[:12]}_{safe_name}"
            )
            trash_target = self._candidate(trash_root, trash_id)
            if trash_target.exists() or trash_target.is_symlink():
                raise JanickaR2DocumentError(
                    "Bezpečný cíl v koši už existuje."
                )
            os.replace(target, trash_target)
        return JanickaR2TrashResult(
            original_name=safe_name,
            trash_id=trash_id,
            moved_at=now.isoformat(),
        )

    @staticmethod
    def _validate_text(value: object) -> str:
        if not isinstance(value, str):
            raise JanickaR2DocumentError("Obsah dokumentu musí být text.")
        if "\x00" in value:
            raise JanickaR2DocumentError(
                "Obsah dokumentu obsahuje nepovolený řídicí znak."
            )
        if len(value.encode("utf-8")) > MAX_R2_DOCUMENT_TEXT_BYTES:
            raise JanickaR2DocumentError("Dokument překročil bezpečný limit.")
        return value

    def _require_document_root(self, *, create: bool) -> Path:
        current = self._canonical_private_root
        for part in R2_DOCUMENTS_RELATIVE_ROOT.parts:
            current = current / part
            if current.exists() or current.is_symlink():
                if current.is_symlink() or not current.is_dir():
                    raise JanickaR2DocumentError(
                        "Soukromý adresář Janičky není bezpečný."
                    )
            elif create:
                current.mkdir(mode=0o700)
            else:
                raise JanickaR2DocumentNotFoundError(
                    "Soukromý adresář Janičky zatím neexistuje."
                )
        resolved = current.resolve(strict=True)
        if self._canonical_private_root not in resolved.parents:
            raise JanickaR2DocumentError(
                "Soukromý adresář Janičky míří mimo povolený kořen."
            )
        return resolved

    def _require_trash_root(self) -> Path:
        document_root = self._require_document_root(create=True)
        trash_root = document_root / R2_DOCUMENT_TRASH_DIRNAME
        if trash_root.exists() or trash_root.is_symlink():
            if trash_root.is_symlink() or not trash_root.is_dir():
                raise JanickaR2DocumentError("Koš Janičky není bezpečný.")
        else:
            trash_root.mkdir(mode=0o700)
        resolved = trash_root.resolve(strict=True)
        if document_root not in resolved.parents:
            raise JanickaR2DocumentError("Koš Janičky míří mimo povolený kořen.")
        return resolved

    def _require_regular_file(self, name: str) -> Path:
        try:
            root = self._require_document_root(create=False)
        except JanickaR2DocumentNotFoundError as exc:
            raise JanickaR2DocumentNotFoundError(
                "Dokument nebyl nalezen."
            ) from exc
        target = self._candidate(root, name)
        if target.is_symlink() or not target.exists() or not target.is_file():
            raise JanickaR2DocumentNotFoundError(
                "Dokument nebyl bezpečně nalezen."
            )
        return target

    @staticmethod
    def _candidate(root: Path, name: str) -> Path:
        candidate = root / name
        if candidate.parent != root:
            raise JanickaR2DocumentError(
                "Dokument míří mimo povolený adresář."
            )
        return candidate

    @staticmethod
    def _reject_existing_symlink_or_directory(path: Path) -> None:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise JanickaR2DocumentError(
                "Cílový dokument není bezpečný soubor."
            )

    @staticmethod
    def _document_info(path: Path) -> JanickaR2DocumentInfo:
        file_stat = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(file_stat.st_mode):
            raise JanickaR2DocumentError(
                "Dokument není bezpečný běžný soubor."
            )
        modified = datetime.fromtimestamp(
            file_stat.st_mtime,
            tz=timezone.utc,
        )
        return JanickaR2DocumentInfo(
            name=path.name,
            size_bytes=file_stat.st_size,
            modified_at=modified.isoformat(),
        )
