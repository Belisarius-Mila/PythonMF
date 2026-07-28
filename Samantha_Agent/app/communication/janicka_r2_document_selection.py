"""Human-selected R2 document search before create-only TXT compilation."""

from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.communication.janicka_r2_compiler import (
    JanickaR2CompilationResult,
    JanickaR2DocumentCompiler,
)
from app.documents.vault import safe_text


R2_DOCUMENT_SEARCH_CAPABILITY = "search_private_documents"
MAX_R2_DOCUMENT_SEARCH_RESULTS = 5
MIN_R2_OVERVIEW_SOURCES = 2
MAX_R2_OVERVIEW_SOURCES = 5
_MAX_R2_DOCUMENT_QUERY_CHARS = 200
_DOCUMENT_ID_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{0,139}")
_SELECTION_REF_RE = re.compile(r"docref-[a-f0-9]{16}")
_SOURCE_SET_REF_RE = re.compile(r"r2set-[a-f0-9]{32}")

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


@dataclass(frozen=True)
class JanickaR2ConfirmedSource:
    """One human-selected source with text reserved for internal R2 processing."""

    selection_ref: str
    title: str
    document_type: str
    domain: str
    read_only_text: str = field(repr=False)

    @property
    def label(self) -> str:
        return f"{self.title} ({self.document_type}; {self.domain})"


@dataclass(frozen=True)
class JanickaR2ConfirmedSourceSet:
    """Fresh read-only material bound to one opaque source-set reference."""

    query: str
    source_set_ref: str
    sources: tuple[JanickaR2ConfirmedSource, ...]

    @property
    def source_count(self) -> int:
        return len(self.sources)

    def metadata(self) -> dict[str, object]:
        """Return orchestration metadata without any source fulltext."""

        return {
            "source_set_ref": self.source_set_ref,
            "source_count": self.source_count,
            "sources": [
                {
                    "selection_ref": source.selection_ref,
                    "title": source.title,
                    "document_type": source.document_type,
                    "domain": source.domain,
                }
                for source in self.sources
            ],
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

    def prepare_selected_sources(
        self,
        *,
        query: object,
        selection_refs: object,
    ) -> JanickaR2ConfirmedSourceSet:
        """Freshly inspect two to five explicit human selections without writing."""

        safe_query = self._validate_query(query)
        safe_refs = self._validate_selection_refs(selection_refs)
        result, document_ids = self._load_candidates(safe_query)
        candidates = {
            candidate.selection_ref: candidate
            for candidate in result.candidates
        }
        if any(selection_ref not in candidates for selection_ref in safe_refs):
            raise JanickaR2DocumentSelectionError(
                "Některá vybraná položka už není v aktuálních výsledcích hledání."
            )

        sources: list[JanickaR2ConfirmedSource] = []
        for selection_ref in safe_refs:
            candidate = candidates[selection_ref]
            try:
                source_text = self._compiler.inspect_document_source(
                    document_ids[selection_ref]
                )
            except Exception as exc:
                raise JanickaR2DocumentSelectionError(
                    "Read-only načtení potvrzených zdrojů se nepodařilo."
                ) from exc
            sources.append(
                JanickaR2ConfirmedSource(
                    selection_ref=selection_ref,
                    title=candidate.title,
                    document_type=candidate.document_type,
                    domain=candidate.domain,
                    read_only_text=source_text,
                )
            )
        confirmed = tuple(sources)
        return JanickaR2ConfirmedSourceSet(
            query=safe_query,
            source_set_ref=self._source_set_reference(
                query=safe_query,
                sources=confirmed,
            ),
            sources=confirmed,
        )

    def compile_selected_overview(
        self,
        *,
        name: object,
        query: object,
        selection_refs: object,
        source_set_ref: object,
        overview_text: object,
        now: datetime | None = None,
    ) -> JanickaR2CompilationResult:
        """Create one overview only while the confirmed source set is unchanged."""

        safe_name = self._compiler.ensure_new_document_name(name)
        expected_ref = self._validate_source_set_ref(source_set_ref)
        source_set = self.prepare_selected_sources(
            query=query,
            selection_refs=selection_refs,
        )
        if not hmac.compare_digest(source_set.source_set_ref, expected_ref):
            raise JanickaR2DocumentSelectionError(
                "Potvrzené zdroje se změnily. Zobraz je znovu a vyžádej nové potvrzení."
            )
        return self._compiler._compile_confirmed_overview(
            name=safe_name,
            overview_text=overview_text,
            source_labels=tuple(source.label for source in source_set.sources),
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

    @classmethod
    def _validate_selection_refs(cls, value: object) -> tuple[str, ...]:
        if (
            isinstance(value, (str, bytes))
            or not isinstance(value, (list, tuple))
            or not MIN_R2_OVERVIEW_SOURCES <= len(value) <= MAX_R2_OVERVIEW_SOURCES
        ):
            raise JanickaR2DocumentSelectionError(
                "Přehled vyžaduje dvě až pět výslovně vybraných voleb selection_ref."
            )
        selection_refs = tuple(cls._validate_selection_ref(item) for item in value)
        if len(set(selection_refs)) != len(selection_refs):
            raise JanickaR2DocumentSelectionError(
                "Každý potvrzený zdroj smí být vybrán pouze jednou."
            )
        return selection_refs

    @staticmethod
    def _validate_source_set_ref(value: object) -> str:
        source_set_ref = str(value or "").strip()
        if not _SOURCE_SET_REF_RE.fullmatch(source_set_ref):
            raise JanickaR2DocumentSelectionError(
                "Vytvoření přehledu vyžaduje platný potvrzený source_set_ref."
            )
        return source_set_ref

    @staticmethod
    def _source_set_reference(
        *,
        query: str,
        sources: tuple[JanickaR2ConfirmedSource, ...],
    ) -> str:
        digest = hashlib.blake2s(digest_size=16, person=b"R2SrcSet")
        digest.update(query.encode("utf-8"))
        for source in sources:
            digest.update(b"\x00")
            digest.update(source.selection_ref.encode("ascii"))
            digest.update(b"\x00")
            digest.update(source.label.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(source.read_only_text.encode("utf-8"))
        return f"r2set-{digest.hexdigest()}"

    @staticmethod
    def _document_reference(document_id: str) -> str:
        digest = hashlib.sha256(document_id.encode("utf-8")).hexdigest()[:16]
        return f"docref-{digest}"

    @staticmethod
    def _display_text(value: object, fallback: str, limit: int) -> str:
        return (safe_text(str(value or "")).strip() or fallback)[:limit]
