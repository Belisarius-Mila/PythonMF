from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from app.communication.human_adam_workstream_catalog import WORKSTREAM_CATALOG
from app.communication.human_adam_workstream_memory import WorkstreamMemoryRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_DIR = PROJECT_ROOT / "memory"
MAX_MEMORY_RESULTS = 5
MAX_MEMORY_SNIPPET_CHARS = 420
STARTUP_MEMORY_FILES = (
    "samantha_core.md",
    "ACTIVE_PROJECTS.md",
    "MEMORY_INDEX.md",
)
MAX_STATUS_ITEMS = 8
MAX_STATUS_LINE_CHARS = 220
AUTHORITY_CANONICAL = "canonical"
AUTHORITY_AGGREGATE = "aggregate"
AUTHORITY_AGGREGATE_UNVERIFIED = "aggregate_unverified"
AUTHORITY_REFERENCE = "reference"
AUTHORITY_HISTORICAL = "historical"
_TARGET_AUTHORITY_SCORE_BONUS = {
    AUTHORITY_CANONICAL: 40,
    AUTHORITY_AGGREGATE: 15,
    AUTHORITY_AGGREGATE_UNVERIFIED: 10,
    AUTHORITY_REFERENCE: 0,
    AUTHORITY_HISTORICAL: 0,
}


@dataclass(frozen=True)
class MemorySearchResult:
    score: int
    path: str
    snippet: str
    source_type: str
    authority: str
    workstream_id: str


@dataclass(frozen=True)
class MemorySnippetRecord:
    path: str
    snippet: str
    snippet_terms: frozenset[str]
    filename_terms: frozenset[str]
    source_type: str
    is_handoff: bool
    authority: str
    workstream_id: str


@dataclass(frozen=True)
class MemoryIndex:
    memory_dir: Path
    file_count: int
    markdown_chars: int
    fingerprint: tuple[tuple[str, int, int], ...]
    snippets: tuple[MemorySnippetRecord, ...]


_MEMORY_INDEX_CACHE: dict[Path, MemoryIndex] = {}


def query_terms(query: str) -> set[str]:
    terms = {
        term
        for term in re.findall(r"[^\W_]+", query.casefold(), flags=re.UNICODE)
        if len(term) > 2
    }
    if "read" in terms and "only" in terms:
        terms.add("readonly")
    if "readonly" in terms:
        terms.update(("read", "only"))
    return terms


def memory_snippets(markdown_text: str) -> list[str]:
    snippets: list[str] = []
    for part in re.split(r"\n\s*\n", markdown_text):
        block = part.strip()
        if not block:
            continue
        snippets.extend(_markdown_block_snippets(block))
    return snippets


def iter_markdown_files(memory_dir: Path = MEMORY_DIR) -> Iterable[Path]:
    return sorted(memory_dir.rglob("*.md"))


def get_memory_index(memory_dir: Path = MEMORY_DIR) -> MemoryIndex:
    resolved_memory_dir = memory_dir.resolve()
    fingerprint = _memory_fingerprint(resolved_memory_dir)
    cached = _MEMORY_INDEX_CACHE.get(resolved_memory_dir)
    if cached is not None and cached.fingerprint == fingerprint:
        return cached

    index = _build_memory_index(
        memory_dir=resolved_memory_dir,
        fingerprint=fingerprint,
    )
    _MEMORY_INDEX_CACHE[resolved_memory_dir] = index
    return index


def load_markdown_context(
    memory_dir: Path = MEMORY_DIR,
    relative_paths: Iterable[str] | None = None,
) -> str:
    memory_parts: list[str] = []
    paths = _selected_paths(memory_dir, relative_paths)

    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            relative_path = path.relative_to(memory_dir)
            memory_parts.append(f"# {relative_path}\n\n{text}")

    if not memory_parts:
        return "Pamet zatim neobsahuje zadne markdown soubory."

    return "\n\n---\n\n".join(memory_parts)


def load_full_memory_context(
    memory_dir: Path = MEMORY_DIR,
    reminder_formatter: Callable[[], str] | None = None,
    email_activity_formatter: Callable[[], str] | None = None,
    backup_activity_formatter: Callable[[], str] | None = None,
) -> str:
    return _append_dynamic_sections(
        load_markdown_context(memory_dir=memory_dir),
        reminder_formatter=reminder_formatter,
        email_activity_formatter=email_activity_formatter,
        backup_activity_formatter=backup_activity_formatter,
    )


def load_startup_memory_context(
    memory_dir: Path = MEMORY_DIR,
    reminder_formatter: Callable[[], str] | None = None,
    email_activity_formatter: Callable[[], str] | None = None,
    backup_activity_formatter: Callable[[], str] | None = None,
) -> str:
    return _append_dynamic_sections(
        load_markdown_context(
            memory_dir=memory_dir,
            relative_paths=STARTUP_MEMORY_FILES,
        ),
        reminder_formatter=reminder_formatter,
        email_activity_formatter=email_activity_formatter,
        backup_activity_formatter=backup_activity_formatter,
    )


def search_memory(
    query: str,
    memory_dir: Path = MEMORY_DIR,
    source_type: str | None = None,
) -> list[MemorySearchResult]:
    terms = query_terms(query)
    if not terms:
        return []

    normalized_source_type = _normalize_source_type(source_type)
    target_workstreams = _query_workstream_ids(terms)
    best_matches_by_path: dict[str, MemorySearchResult] = {}
    index = get_memory_index(memory_dir)
    for record in index.snippets:
        if normalized_source_type is not None and record.source_type != normalized_source_type:
            continue
        score = _memory_score(terms, record)
        if score <= 0:
            continue

        result = MemorySearchResult(
            score=score,
            path=record.path,
            snippet=record.snippet,
            source_type=record.source_type,
            authority=record.authority,
            workstream_id=record.workstream_id,
        )
        current = best_matches_by_path.get(record.path)
        if current is None or _is_better_memory_result(
            result,
            current,
            target_workstreams=target_workstreams,
        ):
            best_matches_by_path[record.path] = result

    return sorted(
        best_matches_by_path.values(),
        key=lambda item: (
            -_memory_rank_score(item, target_workstreams=target_workstreams),
            -item.score,
            item.path,
            item.snippet,
        ),
    )


def search_memory_text(
    query: str,
    memory_dir: Path = MEMORY_DIR,
    max_results: int = MAX_MEMORY_RESULTS,
    source_type: str | None = None,
) -> str:
    if not query_terms(query):
        return "Dotaz je prilis kratky nebo neobsahuje hledatelna slova."

    normalized_source_type = _normalize_source_type(source_type)
    if source_type is not None and normalized_source_type is None:
        allowed = ", ".join(_SOURCE_TYPE_ALIASES)
        return f"Neznamy typ zdroje `{source_type}`. Pouzij jeden z: {allowed}."

    matches = search_memory(
        query=query,
        memory_dir=memory_dir,
        source_type=normalized_source_type,
    )
    if not matches:
        return "V markdown pameti jsem nenasla relevantni uryvky."

    result_lines = []
    for match in matches[:max_results]:
        prefix = (
            f"- [{match.source_type}] {match.path} "
            f"(autorita {match.authority}, shoda {match.score}): "
        )
        snippet = _compact_memory_snippet(
            match.snippet,
            max_chars=max(
                40,
                MAX_MEMORY_SNIPPET_CHARS + 40 - len(prefix),
            ),
        )
        result_lines.append(
            f"{prefix}{snippet}"
        )

    return "\n".join(result_lines)


def format_memory_status(
    memory_dir: Path = MEMORY_DIR,
    reminder_formatter: Callable[[], str] | None = None,
    email_activity_formatter: Callable[[], str] | None = None,
    backup_activity_formatter: Callable[[], str] | None = None,
) -> str:
    index = get_memory_index(memory_dir)
    startup_context = load_startup_memory_context(
        memory_dir=memory_dir,
        reminder_formatter=reminder_formatter,
        email_activity_formatter=email_activity_formatter,
        backup_activity_formatter=backup_activity_formatter,
    )
    full_context = load_full_memory_context(
        memory_dir=memory_dir,
        reminder_formatter=reminder_formatter,
        email_activity_formatter=email_activity_formatter,
        backup_activity_formatter=backup_activity_formatter,
    )

    lines = [
        "Samantha Memory Status",
        f"- Markdown soubory: {index.file_count}",
        f"- Markdown pamet: {index.markdown_chars} znaku",
        f"- Startup kontext: {len(startup_context)} znaku",
        f"- Plny kontext: {len(full_context)} znaku",
        "",
        "Aktivni projekty s prioritou 1:",
    ]

    priority_projects = _priority_projects(memory_dir)
    if priority_projects:
        lines.extend(
            f"- {_compact_status_line(project)}"
            for project in priority_projects[:MAX_STATUS_ITEMS]
        )
    else:
        lines.append("- Nenalezeny.")

    reminder_lines = _reminder_lines(memory_dir)
    lines.extend(["", "[PRIPOMENOUT] polozky:"])
    if reminder_lines:
        lines.extend(
            f"- {_compact_status_line(line)}"
            for line in reminder_lines[:MAX_STATUS_ITEMS]
        )
        if len(reminder_lines) > MAX_STATUS_ITEMS:
            lines.append(f"- ... dalsich {len(reminder_lines) - MAX_STATUS_ITEMS}")
    else:
        lines.append("- Nenalezeny.")

    return "\n".join(lines)


def _selected_paths(
    memory_dir: Path,
    relative_paths: Iterable[str] | None,
) -> list[Path]:
    if relative_paths is None:
        return list(iter_markdown_files(memory_dir))

    return [memory_dir / relative_path for relative_path in relative_paths]


def _memory_fingerprint(memory_dir: Path) -> tuple[tuple[str, int, int], ...]:
    fingerprint: list[tuple[str, int, int]] = []
    for path in iter_markdown_files(memory_dir):
        stat = path.stat()
        fingerprint.append(
            (
                str(path.relative_to(memory_dir)),
                stat.st_mtime_ns,
                stat.st_size,
            )
        )
    return tuple(fingerprint)


def _build_memory_index(
    memory_dir: Path,
    fingerprint: tuple[tuple[str, int, int], ...],
) -> MemoryIndex:
    snippets: list[MemorySnippetRecord] = []
    markdown_chars = 0
    authority_context = _memory_authority_context(memory_dir)

    for relative_path, _mtime_ns, _size in fingerprint:
        path = memory_dir / relative_path
        text = path.read_text(encoding="utf-8")
        markdown_chars += len(text)
        filename_terms = frozenset(query_terms(relative_path))
        source_type = _source_type(relative_path)
        is_handoff = source_type == "handoffs"

        for snippet in memory_snippets(text):
            compact_snippet = " ".join(snippet.split())
            authority, workstream_id = _memory_authority(
                relative_path=relative_path,
                snippet=compact_snippet,
                context=authority_context,
            )
            snippets.append(
                MemorySnippetRecord(
                    path=relative_path,
                    snippet=compact_snippet,
                    snippet_terms=frozenset(query_terms(snippet)),
                    filename_terms=filename_terms,
                    source_type=source_type,
                    is_handoff=is_handoff,
                    authority=authority,
                    workstream_id=workstream_id,
                )
            )

    return MemoryIndex(
        memory_dir=memory_dir,
        file_count=len(fingerprint),
        markdown_chars=markdown_chars,
        fingerprint=fingerprint,
        snippets=tuple(snippets),
    )


def _markdown_block_snippets(block: str) -> list[str]:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if len(lines) <= 1:
        return [block]

    if _is_structured_line_block(lines):
        return [
            line
            for line in lines
            if not _is_markdown_table_separator(line)
        ]

    return [block]


def _is_structured_line_block(lines: list[str]) -> bool:
    structured_lines = 0
    for line in lines:
        if line.startswith(("- ", "* ", "| ")):
            structured_lines += 1
    return structured_lines >= 2


def _is_markdown_table_separator(line: str) -> bool:
    return line.startswith("|") and set(line.replace("|", "").strip()) <= {"-", " ", ":"}


def _memory_score(terms: set[str], record: MemorySnippetRecord) -> int:
    snippet_matches = len(terms & record.snippet_terms)
    filename_matches = len(terms & record.filename_terms)
    if not snippet_matches and not filename_matches:
        return 0

    score = snippet_matches * 3 + filename_matches * 6
    if filename_matches == len(terms):
        score += 5
    if snippet_matches == len(terms):
        score += 2

    # Old handoffs often repeat broad terms. Keep them searchable, but do not let
    # generic historical snippets crowd out project/core memory.
    if (
        record.authority == AUTHORITY_HISTORICAL
        and not filename_matches
        and "[PRIPOMENOUT]" not in record.snippet
    ):
        score -= 3
    if record.authority == AUTHORITY_HISTORICAL and "handoff" not in terms:
        score -= 35

    return score


@dataclass(frozen=True)
class _MemoryAuthorityContext:
    canonical_paths: dict[str, str]
    memory_ready_workstreams: frozenset[str]
    aggregate_sources: dict[str, str]


def _memory_authority_context(memory_dir: Path) -> _MemoryAuthorityContext:
    registry = WorkstreamMemoryRegistry()
    canonical_paths: dict[str, str] = {}
    memory_ready: set[str] = set()
    for binding in registry.bindings():
        handoff_path = _memory_relative_path(binding.handoff_relative_path)
        tvbcp_path = _memory_relative_path(binding.tvbcp_relative_path)
        canonical_paths[handoff_path] = binding.workstream_id
        canonical_paths[tvbcp_path] = binding.workstream_id
        if (memory_dir / handoff_path).is_file() and (memory_dir / tvbcp_path).is_file():
            memory_ready.add(binding.workstream_id)

    aggregate_sources: dict[str, str] = {}
    duplicate_sources: set[str] = set()
    for record in WORKSTREAM_CATALOG:
        for source_name in record.source_names:
            normalized = _normalized_authority_label(source_name)
            if normalized in aggregate_sources:
                duplicate_sources.add(normalized)
                continue
            aggregate_sources[normalized] = record.workstream_id
    for duplicate in duplicate_sources:
        aggregate_sources.pop(duplicate, None)

    return _MemoryAuthorityContext(
        canonical_paths=canonical_paths,
        memory_ready_workstreams=frozenset(memory_ready),
        aggregate_sources=aggregate_sources,
    )


def _memory_authority(
    *,
    relative_path: str,
    snippet: str,
    context: _MemoryAuthorityContext,
) -> tuple[str, str]:
    canonical_workstream = context.canonical_paths.get(relative_path)
    if canonical_workstream:
        return AUTHORITY_CANONICAL, canonical_workstream

    source_type = _source_type(relative_path)
    if relative_path == "ACTIVE_PROJECTS.md":
        aggregate_workstream = _aggregate_workstream_id(
            snippet,
            aggregate_sources=context.aggregate_sources,
        )
        if (
            aggregate_workstream
            and aggregate_workstream in context.memory_ready_workstreams
        ):
            return AUTHORITY_AGGREGATE, aggregate_workstream
        return AUTHORITY_AGGREGATE_UNVERIFIED, aggregate_workstream
    if source_type == "handoffs":
        return AUTHORITY_HISTORICAL, ""
    return AUTHORITY_REFERENCE, ""


def _memory_relative_path(project_relative_path: str) -> str:
    path = Path(project_relative_path)
    if not path.parts or path.parts[0] != "memory":
        raise ValueError("Kanonická paměťová cesta musí začínat memory/.")
    return Path(*path.parts[1:]).as_posix()


def _aggregate_workstream_id(
    snippet: str,
    *,
    aggregate_sources: dict[str, str],
) -> str:
    stripped = snippet.strip()
    if not stripped.startswith("|"):
        return ""
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if not cells:
        return ""
    return aggregate_sources.get(_normalized_authority_label(cells[0]), "")


def _normalized_authority_label(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("–", "-").replace("—", "-")
    return " ".join(text.casefold().split())


def _query_workstream_ids(terms: set[str]) -> frozenset[str]:
    matches: set[str] = set()
    for record in WORKSTREAM_CATALOG:
        labels = (
            record.workstream_id,
            record.name,
            *record.source_names,
            *record.query_aliases,
        )
        if any(
            (label_terms := query_terms(label))
            and label_terms.issubset(terms)
            for label in labels
        ):
            matches.add(record.workstream_id)
    return frozenset(matches)


def _memory_rank_score(
    result: MemorySearchResult,
    *,
    target_workstreams: frozenset[str],
) -> int:
    if not result.workstream_id or result.workstream_id not in target_workstreams:
        return result.score
    return result.score + _TARGET_AUTHORITY_SCORE_BONUS[result.authority]


_SOURCE_TYPE_ALIASES = {
    "active": "core",
    "active_projects": "core",
    "core": "core",
    "handoff": "handoffs",
    "handoffs": "handoffs",
    "infrastructure": "infrastructure",
    "infra": "infrastructure",
    "project": "projects",
    "projects": "projects",
    "stories": "stories",
    "story": "stories",
    "technical": "technical",
    "tech": "technical",
}


def _normalize_source_type(source_type: str | None) -> str | None:
    if source_type is None:
        return None
    return _SOURCE_TYPE_ALIASES.get(source_type.strip().casefold())


def _source_type(relative_path: str) -> str:
    if "/" not in relative_path:
        return "core"
    return relative_path.split("/", 1)[0]


def _is_better_memory_result(
    candidate: MemorySearchResult,
    current: MemorySearchResult,
    *,
    target_workstreams: frozenset[str],
) -> bool:
    candidate_rank = _memory_rank_score(
        candidate,
        target_workstreams=target_workstreams,
    )
    current_rank = _memory_rank_score(
        current,
        target_workstreams=target_workstreams,
    )
    if candidate_rank != current_rank:
        return candidate_rank > current_rank
    if candidate.score != current.score:
        return candidate.score > current.score
    if len(candidate.snippet) != len(current.snippet):
        return len(candidate.snippet) < len(current.snippet)
    return candidate.snippet < current.snippet


def _compact_memory_snippet(
    snippet: str,
    *,
    max_chars: int = MAX_MEMORY_SNIPPET_CHARS,
) -> str:
    compact = " ".join(snippet.split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[: max_chars - 3].rstrip()}..."


def _append_dynamic_sections(
    memory_text: str,
    reminder_formatter: Callable[[], str] | None,
    email_activity_formatter: Callable[[], str] | None,
    backup_activity_formatter: Callable[[], str] | None,
) -> str:
    sections = [memory_text]

    if reminder_formatter is not None:
        sections.append(reminder_formatter())
    if email_activity_formatter is not None:
        sections.append(email_activity_formatter())
    if backup_activity_formatter is not None:
        sections.append(backup_activity_formatter())

    return "\n\n---\n\n".join(sections)


def _reminder_lines(memory_dir: Path) -> list[str]:
    index_path = memory_dir / "MEMORY_INDEX.md"
    if not index_path.exists():
        return []

    return [
        " ".join(line.removeprefix("- ").split())
        for line in index_path.read_text(encoding="utf-8").splitlines()
        if "[PRIPOMENOUT]" in line
    ]


def _priority_projects(memory_dir: Path) -> list[str]:
    active_projects_path = memory_dir / "ACTIVE_PROJECTS.md"
    if not active_projects_path.exists():
        return []

    projects: list[str] = []
    headers: list[str] = []
    for line in active_projects_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not headers:
            headers = [_normalize_project_header(cell) for cell in cells]
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = dict(zip(headers, cells[: len(headers)], strict=False))
        if _project_lifecycle(row) == "archived":
            continue
        if row.get("priorita") != "1":
            continue
        projects.append(f"{row.get('oblast', '')}: {row.get('stav', '')}")

    return projects


def _normalize_project_header(value: str) -> str:
    return {
        "oblast": "oblast",
        "priorita": "priorita",
        "stav": "stav",
        "rezim": "rezim",
        "režim": "rezim",
        "dalsi krok": "dalsi_krok",
        "další krok": "dalsi_krok",
    }.get(value.strip().casefold(), value.strip().casefold().replace(" ", "_"))


def _project_lifecycle(row: dict[str, str]) -> str:
    value = (row.get("rezim") or "").strip().casefold()
    if value in {"archiv", "archivni", "archivní", "archive", "archived"}:
        return "archived"
    return "active"


def _compact_status_line(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= MAX_STATUS_LINE_CHARS:
        return compact
    return f"{compact[: MAX_STATUS_LINE_CHARS - 3].rstrip()}..."
