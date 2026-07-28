"""Create-only TXT compilation from one registered read-only R2 source."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.communication.janicka_r2_documents import (
    JanickaR2DocumentExistsError,
    JanickaR2DocumentInfo,
    JanickaR2DocumentStore,
    normalize_r2_document_name,
)


R2_DOCUMENT_INSPECTION_CAPABILITY = "inspect_document_text"
R2_DOCUMENT_INSPECTION_PREFIX = "Inspekce dokumentu (read-only):"
MAX_R2_SOURCE_TEXT_BYTES = 256 * 1024
_DOCUMENT_ID_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{0,139}")

DocumentInspector = Callable[[str], str]


class JanickaR2CompilationError(RuntimeError):
    """Raised when compilation cannot preserve its read-only source boundary."""


@dataclass(frozen=True)
class JanickaR2CompilationResult:
    """Redacted compilation metadata without source text or private paths."""

    document: JanickaR2DocumentInfo
    source_type: str
    source_count: int
    compiled_at: str

    def as_dict(self) -> dict[str, object]:
        return {
            "document": self.document.as_dict(),
            "source_type": self.source_type,
            "source_count": self.source_count,
            "compiled_at": self.compiled_at,
        }


def inspect_registered_document(
    document_id: str,
    *,
    vault_dir: Path | None = None,
) -> str:
    """Call the existing registered tool implementation lazily at runtime."""

    from app.documents.tools import inspect_document_text_text

    if vault_dir is None:
        return inspect_document_text_text(document_id=document_id)
    return inspect_document_text_text(
        document_id=document_id,
        vault_dir=vault_dir,
    )


class JanickaR2DocumentCompiler:
    """Compile one redacted document inspection into a new owned TXT file."""

    def __init__(
        self,
        *,
        store: JanickaR2DocumentStore,
        document_inspector: DocumentInspector = inspect_registered_document,
    ) -> None:
        if not isinstance(store, JanickaR2DocumentStore):
            raise TypeError("R2 kompilátor nemá platný dokumentový store.")
        if not callable(document_inspector):
            raise TypeError("R2 kompilátor nemá platný read-only zdroj.")
        self._store = store
        self._document_inspector = document_inspector

    def compile_document_inspection(
        self,
        *,
        name: object,
        document_id: object,
        now: datetime | None = None,
    ) -> JanickaR2CompilationResult:
        """Create one TXT from a selected redacted inspection without replacement."""

        safe_name = self.ensure_new_document_name(name)
        safe_document_id = self._validate_document_id(document_id)
        source_text = self._read_source(safe_document_id)
        compiled_at = self._compiled_at(now)
        rendered = self._render(
            name=safe_name,
            document_id=safe_document_id,
            source_text=source_text,
            compiled_at=compiled_at,
        )
        document = self._store.create_text(name=safe_name, text=rendered)
        return JanickaR2CompilationResult(
            document=document,
            source_type=R2_DOCUMENT_INSPECTION_CAPABILITY,
            source_count=1,
            compiled_at=compiled_at,
        )

    def ensure_new_document_name(self, name: object) -> str:
        """Validate a create-only target before any private source is inspected."""

        safe_name = normalize_r2_document_name(name)
        if any(item.name == safe_name for item in self._store.list_documents()):
            raise JanickaR2DocumentExistsError(
                "Dokument s tímto názvem už existuje."
            )
        return safe_name

    def inspect_document_source(self, document_id: object) -> str:
        """Return one validated read-only inspection for a confirmed workflow."""

        return self._read_source(self._validate_document_id(document_id))

    def _compile_confirmed_overview(
        self,
        *,
        name: object,
        overview_text: object,
        source_labels: tuple[str, ...],
        now: datetime | None = None,
    ) -> JanickaR2CompilationResult:
        """Persist an overview already guarded by the multi-source selection flow."""

        safe_name = self.ensure_new_document_name(name)
        safe_overview = self._validate_overview_text(overview_text)
        safe_labels = self._validate_source_labels(source_labels)
        compiled_at = self._compiled_at(now)
        rendered = self._render_overview(
            name=safe_name,
            overview_text=safe_overview,
            source_labels=safe_labels,
            compiled_at=compiled_at,
        )
        document = self._store.create_text(name=safe_name, text=rendered)
        return JanickaR2CompilationResult(
            document=document,
            source_type=R2_DOCUMENT_INSPECTION_CAPABILITY,
            source_count=len(safe_labels),
            compiled_at=compiled_at,
        )

    def _read_source(self, document_id: str) -> str:
        try:
            value = self._document_inspector(document_id)
        except Exception as exc:
            raise JanickaR2CompilationError(
                "Read-only inspekci vybraného dokumentu se nepodařilo získat."
            ) from exc
        if not isinstance(value, str):
            raise JanickaR2CompilationError(
                "Read-only zdroj nevrátil textový výstup."
            )
        text = value.strip()
        if (
            not text.startswith(R2_DOCUMENT_INSPECTION_PREFIX)
            or "\x00" in text
            or len(text.encode("utf-8")) > MAX_R2_SOURCE_TEXT_BYTES
        ):
            raise JanickaR2CompilationError(
                "Read-only zdroj nevrátil bezpečný redigovaný výtah."
            )
        return text

    @staticmethod
    def _validate_document_id(value: object) -> str:
        document_id = str(value or "").strip()
        if not _DOCUMENT_ID_RE.fullmatch(document_id):
            raise JanickaR2CompilationError(
                "Kompilace vyžaduje jeden bezpečný document_id."
            )
        return document_id

    @staticmethod
    def _compiled_at(value: datetime | None) -> str:
        moment = value or datetime.now(timezone.utc)
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise JanickaR2CompilationError(
                "Čas kompilace musí obsahovat časovou zónu."
            )
        return moment.replace(microsecond=0).isoformat()

    @staticmethod
    def _validate_overview_text(value: object) -> str:
        if not isinstance(value, str):
            raise JanickaR2CompilationError("Obsah přehledu musí být text.")
        text = value.strip()
        if not text or "\x00" in text:
            raise JanickaR2CompilationError(
                "Obsah přehledu je prázdný nebo obsahuje nepovolený znak."
            )
        return text

    @staticmethod
    def _validate_source_labels(value: tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(value, tuple) or not 2 <= len(value) <= 5:
            raise JanickaR2CompilationError(
                "Přehled vyžaduje dva až pět potvrzených zdrojů."
            )
        labels: list[str] = []
        for item in value:
            label = " ".join(str(item or "").replace("\x00", " ").split())[:240]
            if not label:
                raise JanickaR2CompilationError(
                    "Přehled obsahuje neplatný popis zdroje."
                )
            labels.append(label)
        return tuple(labels)

    @staticmethod
    def _render(
        *,
        name: str,
        document_id: str,
        source_text: str,
        compiled_at: str,
    ) -> str:
        return "\n".join(
            (
                "R2-Adam – kompilovaný dokument",
                f"Název: {name}",
                f"Vytvořeno: {compiled_at}",
                f"Zdroj: {R2_DOCUMENT_INSPECTION_CAPABILITY}",
                f"Document ID: {document_id}",
                "Rozsah zdroje: redigovaný read-only výtah",
                "",
                source_text,
                "",
            )
        )

    @staticmethod
    def _render_overview(
        *,
        name: str,
        overview_text: str,
        source_labels: tuple[str, ...],
        compiled_at: str,
    ) -> str:
        lines = [
            "R2-Adam – přehled z potvrzených zdrojů",
            f"Název: {name}",
            f"Vytvořeno: {compiled_at}",
            f"Zdroj: {R2_DOCUMENT_INSPECTION_CAPABILITY}",
            f"Počet potvrzených zdrojů: {len(source_labels)}",
            "Použité zdroje:",
            *(f"- {label}" for label in source_labels),
            "",
            "Přehled:",
            overview_text,
            "",
        ]
        return "\n".join(lines)
