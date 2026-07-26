from __future__ import annotations

import errno
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from app.file_persistence import update_json_file
from app.quick_notes import DEFAULT_ICLOUD_SHORTCUTS_INBOX, SUPPORTED_SUFFIXES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE_DIR = PROJECT_ROOT / "data" / "private" / "urgent_reminders"
DEFAULT_INDEX_PATH = DEFAULT_PRIVATE_DIR / "index.json"
URGENT_REMINDER_FILE_PREFIX = "samantha_reminder_"
DEFAULT_HYDRATION_RETRY_DELAYS = (0.5, 1.0, 2.0, 4.0)


@dataclass(frozen=True)
class UrgentReminder:
    reminder_number: int
    source_path: Path
    title: str
    summary: str
    body_text: str
    created_at: str
    modified_at: str
    size_bytes: int
    priority: str
    status: str


class _UrgentReminderNotFound(RuntimeError):
    pass


def sync_urgent_reminders_index(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
    sync_diagnostics: dict[str, int] | None = None,
    hydration_retry_delays: Sequence[float] = DEFAULT_HYDRATION_RETRY_DELAYS,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[UrgentReminder]:
    observed: list[dict[str, Any]] = []
    reminder_files = _iter_reminder_files(inbox_dir)
    readable_texts, pending_downloads = _read_texts_with_hydration_retry(
        reminder_files,
        retry_delays=hydration_retry_delays,
        sleeper=sleeper,
    )
    now = _now_iso()
    for source_path in reminder_files:
        text = readable_texts.get(source_path)
        if text is None:
            continue
        stat = source_path.stat()
        observed.append(
            {
                "source_path": str(source_path),
                "title": _extract_title(text, source_path),
                "summary": _extract_summary(text),
                "body_text": _extract_body_text(text),
                "created_at": _extract_datetime(text) or _format_timestamp(stat.st_mtime),
                "modified_at": _format_timestamp(stat.st_mtime),
                "size_bytes": stat.st_size,
                "priority": _extract_field(text, "priorita"),
                "last_seen_at": now,
            }
        )

    if not observed:
        records = _load_index(index_path)
    else:
        def merge_observed(current: Any) -> dict[str, list[dict[str, Any]]]:
            records = _index_records(current)
            by_path = {str(record.get("source_path", "")): record for record in records}
            next_number = _next_reminder_number(records)
            for snapshot in observed:
                source_key = str(snapshot["source_path"])
                existing = by_path.get(source_key)
                if existing is None:
                    existing = {
                        "reminder_number": next_number,
                        "source_path": source_key,
                        "priority": "urgent",
                        "status": "open",
                        "first_seen_at": now,
                    }
                    next_number += 1
                    records.append(existing)
                    by_path[source_key] = existing
                status = existing.get("status") or "open"
                priority = snapshot.get("priority") or existing.get("priority") or "urgent"
                existing.update(snapshot)
                existing["status"] = status
                existing["priority"] = priority
            return {"reminders": records}

        updated = update_json_file(
            index_path,
            merge_observed,
            default={"reminders": []},
            sort_keys=True,
        )
        records = _index_records(updated)

    if sync_diagnostics is not None:
        sync_diagnostics.clear()
        sync_diagnostics.update(
            {
                "checked_file_count": len(reminder_files),
                "readable_file_count": len(observed),
                "pending_download_count": len(pending_downloads),
            }
        )

    return [
        _record_to_reminder(record)
        for record in sorted(records, key=lambda item: int(item.get("reminder_number", 0)))
        if Path(str(record.get("source_path", ""))).exists()
    ]


def mark_urgent_reminder_done(
    reminder_number: int,
    *,
    index_path: Path = DEFAULT_INDEX_PATH,
) -> UrgentReminder | None:
    now = _now_iso()
    matched: dict[str, Any] | None = None

    def mark_matching(current: Any) -> dict[str, list[dict[str, Any]]]:
        nonlocal matched
        records = _index_records(current)
        for record in records:
            try:
                number = int(record.get("reminder_number", 0) or 0)
            except (TypeError, ValueError):
                number = 0
            if number != reminder_number:
                continue
            record["status"] = "done"
            record["completed_at"] = now
            record["last_seen_at"] = now
            matched = dict(record)
            return {"reminders": records}
        raise _UrgentReminderNotFound

    try:
        update_json_file(
            index_path,
            mark_matching,
            default={"reminders": []},
            sort_keys=True,
        )
    except _UrgentReminderNotFound:
        return None
    if matched is None:  # pragma: no cover - defensive invariant.
        return None
    return _record_to_reminder(matched)


def _load_index(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _index_records(json.loads(path.read_text(encoding="utf-8")))


def _index_records(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise ValueError("Urgent reminders index musi byt JSON objekt.")
    records = data.get("reminders", [])
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("Urgent reminders index musi obsahovat pole reminders se slovniky.")
    return records


def _iter_reminder_files(inbox_dir: Path) -> list[Path]:
    if not inbox_dir.exists() or not inbox_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in inbox_dir.iterdir()
            if path.is_file()
            and path.suffix.casefold() in SUPPORTED_SUFFIXES
            and path.name.casefold().startswith(URGENT_REMINDER_FILE_PREFIX)
        ),
        key=lambda path: (path.stat().st_mtime, path.name.casefold()),
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_texts_with_hydration_retry(
    paths: Sequence[Path],
    *,
    retry_delays: Sequence[float],
    sleeper: Callable[[float], None],
) -> tuple[dict[Path, str], tuple[Path, ...]]:
    delays = tuple(max(0.0, float(delay)) for delay in retry_delays)
    readable: dict[Path, str] = {}
    pending = list(paths)
    for attempt in range(len(delays) + 1):
        next_pending: list[Path] = []
        for path in pending:
            try:
                readable[path] = _read_text(path)
            except OSError as exc:
                if exc.errno != errno.EDEADLK:
                    raise
                next_pending.append(path)
        pending = next_pending
        if not pending or attempt >= len(delays):
            break
        sleeper(delays[attempt])
    return readable, tuple(pending)


def _extract_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    return path.stem


def _extract_summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        if line.casefold().rstrip(":") in {"pripomenuti", "připomenutí", "ukol", "úkol"}:
            for candidate in lines[index + 1:]:
                if candidate:
                    return _one_line(candidate)
    for line in lines:
        lowered = line.casefold()
        if line and not line.startswith("#") and not lowered.startswith(("datum:", "priorita:")):
            return _one_line(line)
    return "(prazdne pripomenuti)"


def _extract_body_text(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().casefold().rstrip(":") in {"pripomenuti", "připomenutí", "ukol", "úkol"}:
            body = "\n".join(lines[index + 1:]).strip()
            return body or "(prazdne pripomenuti)"
    body_lines = []
    for line in lines:
        stripped = line.strip()
        lowered = stripped.casefold()
        if not stripped or stripped.startswith("#") or lowered.startswith(("datum:", "priorita:")):
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip() or "(prazdne pripomenuti)"


def _extract_datetime(text: str) -> str | None:
    return _extract_field(text, "datum")


def _extract_field(text: str, field: str) -> str | None:
    prefix = f"{field.casefold()}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.casefold().startswith(prefix):
            value = stripped.split(":", 1)[1].strip()
            return value or None
    return None


def _one_line(text: str, max_len: int = 140) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 1].rstrip() + "…"


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _next_reminder_number(records: list[dict[str, Any]]) -> int:
    numbers = [
        int(record.get("reminder_number", 0))
        for record in records
        if str(record.get("reminder_number", "")).isdigit()
    ]
    return max(numbers, default=0) + 1


def _record_to_reminder(record: dict[str, Any]) -> UrgentReminder:
    return UrgentReminder(
        reminder_number=int(record["reminder_number"]),
        source_path=Path(str(record["source_path"])),
        title=str(record.get("title") or ""),
        summary=str(record.get("summary") or ""),
        body_text=str(record.get("body_text") or record.get("summary") or ""),
        created_at=str(record.get("created_at") or ""),
        modified_at=str(record.get("modified_at") or ""),
        size_bytes=int(record.get("size_bytes") or 0),
        priority=str(record.get("priority") or "urgent"),
        status=str(record.get("status") or "open"),
    )
