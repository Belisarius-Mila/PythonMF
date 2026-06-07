from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


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


@dataclass(frozen=True)
class MemorySearchResult:
    score: int
    path: str
    snippet: str
    source_type: str


@dataclass(frozen=True)
class MemorySnippetRecord:
    path: str
    snippet: str
    snippet_terms: frozenset[str]
    filename_terms: frozenset[str]
    source_type: str
    is_handoff: bool


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
        )
        current = best_matches_by_path.get(record.path)
        if current is None or _is_better_memory_result(result, current):
            best_matches_by_path[record.path] = result

    return sorted(
        best_matches_by_path.values(),
        key=lambda item: (-item.score, item.path, item.snippet),
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
        snippet = _compact_memory_snippet(match.snippet)
        result_lines.append(
            f"- [{match.source_type}] {match.path} (shoda {match.score}): {snippet}"
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

    for relative_path, _mtime_ns, _size in fingerprint:
        path = memory_dir / relative_path
        text = path.read_text(encoding="utf-8")
        markdown_chars += len(text)
        filename_terms = frozenset(query_terms(relative_path))
        source_type = _source_type(relative_path)
        is_handoff = source_type == "handoffs"

        for snippet in memory_snippets(text):
            compact_snippet = " ".join(snippet.split())
            snippets.append(
                MemorySnippetRecord(
                    path=relative_path,
                    snippet=compact_snippet,
                    snippet_terms=frozenset(query_terms(snippet)),
                    filename_terms=filename_terms,
                    source_type=source_type,
                    is_handoff=is_handoff,
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
    if record.is_handoff and not filename_matches and "[PRIPOMENOUT]" not in record.snippet:
        score -= 3
    if record.is_handoff and "handoff" not in terms:
        score -= 35

    return score


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
) -> bool:
    if candidate.score != current.score:
        return candidate.score > current.score
    if len(candidate.snippet) != len(current.snippet):
        return len(candidate.snippet) < len(current.snippet)
    return candidate.snippet < current.snippet


def _compact_memory_snippet(snippet: str) -> str:
    compact = " ".join(snippet.split())
    if len(compact) <= MAX_MEMORY_SNIPPET_CHARS:
        return compact
    return f"{compact[: MAX_MEMORY_SNIPPET_CHARS - 3].rstrip()}..."


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
