"""Human-selected R2 document search before create-only TXT compilation."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.communication.janicka_r2_compiler import (
    JanickaR2CompilationResult,
    JanickaR2DocumentCompiler,
)
from app.documents.vault import safe_text


R2_DOCUMENT_SEARCH_CAPABILITY = "search_private_documents"
MAX_R2_DOCUMENT_SEARCH_RESULTS = 5
_MAX_R2_DOCUMENT_QUERY_CHARS = 200
_DOCUMENT_ID_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{0,139}")
_SELECTION_REF_RE = re.compile(r"docref-[a-f0-9]{16}")

DocumentSearchProvider = Callable[[str, int], Mapping[str, object]]


class JanickaR2DocumentSelectionError(RuntimeError):
    """Raised when a search result cannot be safely selected for compilation."""


@dataclass(frozen=True)
class JanickaR2DocumentCandidate:
    """Redacted human-facing candidate without document ID or private path."""

    selection_ref: str
    title: str
    document_type: str
    domain: str
    reading_status: str
    snippet: str

    def as_dict(self) -> dict[str, str]:
        return {
            "selection_ref": self.selection_ref,
            "title": self.title,
            "document_type": self.document_type,
            "domain": self.domain,
            "reading_status": self.reading_status,
            "snippet": self.snippet,
        }


@dataclass(frozen=True)
class JanickaR2DocumentSearchResult:
    """Redacted search result safe for a human selection step."""

    candidates: tuple[JanickaR2DocumentCandidate, ...]

    @property
    def count(self) -> int:
        return len(self.candidates)

    def as_dict(self) -> dict[str, object]:
        return {
            "source_type": R2_DOCUMENT_SEARCH_CAPABILITY,
            "count": self.count,
            "candidates": [item.as_dict() for item in self.candidates],
        }


def search_registered_documents(
    query: str,
    max_results: int,
    *,
    vault_dir: Path | None = None,
) -> Mapping[str, object]:
    """Call the structured service behind the registered read-only capability."""

    from app.documents.search_service import search_document_index

    if vault_dir is None:
        return search_document_index(query=query, limit=max_results)
    return search_document_index(
        query=query,
        vault_dir=vault_dir,
        limit=max_results,
    )


class JanickaR2DocumentSelectionFlow:
    """Require a redacted search and an explicit human choice before compilation."""

    def __init__(
        self,
        *,
        compiler: JanickaR2DocumentCompiler,
        document_search: DocumentSearchProvider = search_registered_documents,
    ) -> None:
        if not isinstance(compiler, JanickaR2DocumentCompiler):
            raise TypeError("R2 výběr nemá platný dokumentový kompilátor.")
        if not callable(document_search):
            raise TypeError("R2 výběr nemá platný read-only vyhledávač.")
        self._compiler = compiler
        self._document_search = document_search

    def search_documents(self, query: object) -> JanickaR2DocumentSearchResult:
        """Return redacted candidates without inspecting or writing a document."""

        result, _document_ids = self._load_candidates(query)
        return result

    def compile_selected_document(
        self,
        *,
        name: object,
        query: object,
        selection_ref: object,
        now: datetime | None = None,
    ) -> JanickaR2CompilationResult:
        """Freshly validate one human-selected reference and compile only that source."""

        safe_selection_ref = self._validate_selection_ref(selection_ref)
        _result, document_ids = self._load_candidates(query)
        document_id = document_ids.get(safe_selection_ref)
        if document_id is None:
            raise JanickaR2DocumentSelectionError(
                "Vybraná položka už není v aktuálních výsledcích hledání."
            )
        return self._compiler.compile_document_inspection(
            name=name,
            document_id=document_id,
            now=now,
        )

    def _load_candidates(
        self,
        query: object,
    ) -> tuple[JanickaR2DocumentSearchResult, dict[str, str]]:
        safe_query = self._validate_query(query)
        try:
            payload = self._document_search(
                safe_query,
                MAX_R2_DOCUMENT_SEARCH_RESULTS,
            )
        except Exception as exc:
            raise JanickaR2DocumentSelectionError(
                "Read-only hledání dokumentů se nepodařilo."
            ) from exc
        if not isinstance(payload, Mapping) or payload.get("ok") is not True:
            raise JanickaR2DocumentSelectionError(
                "Read-only hledání nevrátilo platný výsledek."
            )
        rows = payload.get("results")
        if not isinstance(rows, list):
            raise JanickaR2DocumentSelectionError(
                "Read-only hledání nevrátilo seznam výsledků."
            )

        candidates: list[JanickaR2DocumentCandidate] = []
        document_ids: dict[str, str] = {}
        for row in rows:
            if len(candidates) >= MAX_R2_DOCUMENT_SEARCH_RESULTS:
                break
            if not isinstance(row, Mapping) or row.get("source_type") != "document":
                continue
            document_id = str(row.get("document_id", "")).strip()
            selection_ref = str(row.get("document_ref", "")).strip()
            if (
                not _DOCUMENT_ID_RE.fullmatch(document_id)
                or not _SELECTION_REF_RE.fullmatch(selection_ref)
                or selection_ref != self._document_reference(document_id)
                or selection_ref in document_ids
            ):
                raise JanickaR2DocumentSelectionError(
                    "Read-only hledání vrátilo neplatnou nebo nejednoznačnou volbu."
                )
            candidates.append(
                JanickaR2DocumentCandidate(
                    selection_ref=selection_ref,
                    title=self._display_text(row.get("title"), "Dokument", 180),
                    document_type=self._display_text(
                        row.get("document_type"),
                        "nezjištěno",
                        80,
                    ),
                    domain=self._display_text(row.get("domain"), "nezjištěno", 80),
                    reading_status=self._display_text(
                        row.get("reading_status_label"),
                        "nezjištěno",
                        80,
                    ),
                    snippet=self._display_text(
                        row.get("snippet"),
                        "Náhled není k dispozici.",
                        360,
                    ),
                )
            )
            document_ids[selection_ref] = document_id

        return JanickaR2DocumentSearchResult(tuple(candidates)), document_ids

    @staticmethod
    def _validate_query(value: object) -> str:
        query = " ".join(str(value or "").replace("\x00", " ").split())
        if len(query) < 2 or len(query) > _MAX_R2_DOCUMENT_QUERY_CHARS:
            raise JanickaR2DocumentSelectionError(
                "Hledání vyžaduje konkrétní dotaz do 200 znaků."
            )
        return query

    @staticmethod
    def _validate_selection_ref(value: object) -> str:
        selection_ref = str(value or "").strip()
        if not _SELECTION_REF_RE.fullmatch(selection_ref):
            raise JanickaR2DocumentSelectionError(
                "Kompilace vyžaduje jednu platnou lidskou volbu selection_ref."
            )
        return selection_ref

    @staticmethod
    def _document_reference(document_id: str) -> str:
        digest = hashlib.sha256(document_id.encode("utf-8")).hexdigest()[:16]
        return f"docref-{digest}"

    @staticmethod
    def _display_text(value: object, fallback: str, limit: int) -> str:
        return (safe_text(str(value or "")).strip() or fallback)[:limit]
