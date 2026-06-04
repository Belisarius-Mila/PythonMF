from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ICLOUD_SHORTCUTS_INBOX = (
    Path.home() / "Library" / "Mobile Documents" / "iCloud~is~workflow~my~workflows" / "Documents" / "Shortcuts"
)
DEFAULT_PRIVATE_DIR = PROJECT_ROOT / "data" / "private" / "quick_notes"
DEFAULT_INDEX_PATH = DEFAULT_PRIVATE_DIR / "index.json"
SUPPORTED_SUFFIXES = {".md", ".txt"}
IGNORED_FILE_PREFIXES = ("samantha_reminder_",)


@dataclass(frozen=True)
class QuickNote:
    note_number: int
    source_path: Path
    title: str
    snippet: str
    created_at: str
    modified_at: str
    size_bytes: int
    category: str
    status: str


def list_quick_notes_text(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
    limit: int = 30,
) -> str:
    notes = sync_quick_notes_index(inbox_dir=inbox_dir, index_path=index_path)
    active_notes = [note for note in notes if note.status == "inbox"]
    if not inbox_dir.exists():
        return (
            "Samantha quick notes inbox zatim neexistuje nebo neni synchronizovany na Mac.\n"
            f"Ocekavana slozka: `{inbox_dir}`\n"
            "Na iPhonu spust zkratku a pockej na iCloud sync. Zkratky obvykle ukladaji do sve iCloud slozky Shortcuts."
        )
    if not active_notes:
        return (
            "Samantha quick notes inbox je prazdny.\n"
            f"Slozka: `{inbox_dir}`"
        )

    shown = active_notes[: max(1, limit)]
    lines = [
        "Samantha quick notes - seznam",
        f"- Inbox: `{inbox_dir}`",
        f"- Soukromy index: `{index_path}`",
        "",
    ]
    for note in shown:
        lines.append(
            f"{note.note_number}. [{note.category}] {note.created_at} - {note.snippet}"
        )
        lines.append(f"   Detail: `show_quick_note_detail(note_number={note.note_number})`")
    if len(active_notes) > len(shown):
        lines.append("")
        lines.append(f"... a dalsich {len(active_notes) - len(shown)} poznamek.")
    return "\n".join(lines)


def show_quick_note_detail_text(
    note_number: int,
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
    max_chars: int = 6000,
) -> str:
    notes = sync_quick_notes_index(inbox_dir=inbox_dir, index_path=index_path)
    note = next((item for item in notes if item.note_number == note_number and item.status == "inbox"), None)
    if note is None:
        return f"Poznamka cislo {note_number} nebyla nalezena v quick notes inboxu."

    try:
        text = note.source_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Poznamku cislo {note_number} se nepodarilo precist: {exc}"

    truncated = len(text) > max_chars
    body = text[:max_chars].rstrip()
    lines = [
        f"Samantha quick note #{note.note_number}",
        f"- Kategorie: {note.category}",
        f"- Stav: {note.status}",
        f"- Vytvoreno: {note.created_at}",
        f"- Soubor: `{note.source_path}`",
        "",
        body,
    ]
    if truncated:
        lines.extend(["", f"[Zkraceno na {max_chars} znaku.]"])
    return "\n".join(lines)


def sync_quick_notes_index(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
) -> list[QuickNote]:
    records = _load_index(index_path)
    by_path = {str(record.get("source_path", "")): record for record in records}
    next_number = _next_note_number(records)

    for source_path in _iter_note_files(inbox_dir):
        source_key = str(source_path)
        stat = source_path.stat()
        existing = by_path.get(source_key)
        if existing is None:
            existing = {
                "note_number": next_number,
                "source_path": source_key,
                "category": "inbox",
                "status": "inbox",
                "first_seen_at": _now_iso(),
            }
            next_number += 1
            records.append(existing)
            by_path[source_key] = existing

        text = _read_text(source_path)
        existing.update(
            {
                "source_path": source_key,
                "title": _extract_title(text, source_path),
                "snippet": _extract_snippet(text),
                "created_at": _extract_note_datetime(text) or _format_timestamp(stat.st_mtime),
                "modified_at": _format_timestamp(stat.st_mtime),
                "size_bytes": stat.st_size,
                "status": existing.get("status") or "inbox",
                "category": existing.get("category") or "inbox",
                "last_seen_at": _now_iso(),
            }
        )

    if records:
        _write_index(index_path, records)

    return [
        _record_to_note(record)
        for record in sorted(records, key=lambda item: int(item.get("note_number", 0)))
        if Path(str(record.get("source_path", ""))).exists()
    ]


def _load_index(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("notes", [])
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("Quick notes index musi obsahovat pole notes se slovniky.")
    return records


def _write_index(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"notes": records}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _iter_note_files(inbox_dir: Path) -> list[Path]:
    if not inbox_dir.exists() or not inbox_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in inbox_dir.iterdir()
            if path.is_file()
            and path.suffix.casefold() in SUPPORTED_SUFFIXES
            and not path.name.casefold().startswith(IGNORED_FILE_PREFIXES)
        ),
        key=lambda path: (path.stat().st_mtime, path.name.casefold()),
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    return path.stem


def _extract_snippet(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        if line.casefold().rstrip(":") in {"poznamka", "poznámka"}:
            for candidate in lines[index + 1:]:
                if candidate:
                    return _one_line(candidate)
    for line in lines:
        if line and not line.startswith("#") and not line.lower().startswith("datum:"):
            return _one_line(line)
    return "(prazdna poznamka)"


def _one_line(text: str, max_len: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 1].rstrip() + "…"


def _extract_note_datetime(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("datum:"):
            value = stripped.split(":", 1)[1].strip()
            return value or None
    return None


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _next_note_number(records: list[dict[str, Any]]) -> int:
    numbers = [
        int(record.get("note_number", 0))
        for record in records
        if str(record.get("note_number", "")).isdigit()
    ]
    return max(numbers, default=0) + 1


def _record_to_note(record: dict[str, Any]) -> QuickNote:
    return QuickNote(
        note_number=int(record["note_number"]),
        source_path=Path(str(record["source_path"])),
        title=str(record.get("title") or ""),
        snippet=str(record.get("snippet") or ""),
        created_at=str(record.get("created_at") or ""),
        modified_at=str(record.get("modified_at") or ""),
        size_bytes=int(record.get("size_bytes") or 0),
        category=str(record.get("category") or "inbox"),
        status=str(record.get("status") or "inbox"),
    )
