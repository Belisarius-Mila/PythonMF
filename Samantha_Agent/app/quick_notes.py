from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import update_json_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ICLOUD_SHORTCUTS_INBOX = (
    Path.home() / "Library" / "Mobile Documents" / "iCloud~is~workflow~my~workflows" / "Documents" / "Shortcuts"
)
DEFAULT_PRIVATE_DIR = PROJECT_ROOT / "data" / "private" / "quick_notes"
DEFAULT_INDEX_PATH = DEFAULT_PRIVATE_DIR / "index.json"
SUPPORTED_SUFFIXES = {".md", ".txt"}
IGNORED_FILE_PREFIXES = ("samantha_reminder_",)
DIRECT_SOURCE_KIND = "direct_tailscale"
MAX_DIRECT_QUICK_NOTE_CHARS = 8_000
_DELIVERY_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")


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
    source_kind: str = ""
    body_text: str = ""


@dataclass(frozen=True)
class QuickNoteClassification:
    kind: str
    confidence: str
    risk: str
    sensitive: bool
    safe_summary: str
    suggested_next_step: str
    matched_terms: tuple[str, ...] = ()


ACTION_KIND_LABELS = {
    "reminder_candidate": "připomínka",
    "project_candidate": "projekt",
    "tool_candidate": "tool/workflow",
    "action_candidate": "úkol",
    "sensitive_action": "citlivá akce",
    "archive_candidate": "archiv/znalostní databáze",
    "idea": "nápad",
}


def deliver_quick_note(
    text: str,
    *,
    delivery_id: str = "",
    created_at: str = "",
    index_path: Path = DEFAULT_INDEX_PATH,
) -> tuple[QuickNote, bool]:
    """Atomically store one direct Shortcut delivery and deduplicate retries."""

    if not isinstance(text, str):
        raise ValueError("Quick Note musí být text.")
    body_text = text.strip()
    if not body_text:
        raise ValueError("Quick Note nesmí být prázdná.")
    if len(body_text) > MAX_DIRECT_QUICK_NOTE_CHARS:
        raise ValueError(f"Quick Note smí mít nejvýše {MAX_DIRECT_QUICK_NOTE_CHARS} znaků.")
    if not isinstance(created_at, str) or not isinstance(delivery_id, str):
        raise ValueError("Metadata doručení musí být textová.")
    safe_created_at = created_at.strip()[:80]
    safe_delivery_id = delivery_id.strip()
    if safe_delivery_id and not _DELIVERY_ID_PATTERN.fullmatch(safe_delivery_id):
        raise ValueError("delivery_id má neplatný formát.")
    if not safe_delivery_id:
        delivery_day = _delivery_day(safe_created_at)
        digest_input = f"quick-note-v1\0{delivery_day}\0{body_text}".encode("utf-8")
        safe_delivery_id = hashlib.sha256(digest_input).hexdigest()

    now = _now_iso()
    source_path = f"direct://quick-note/{safe_delivery_id}"
    stored: dict[str, Any] | None = None
    created = False

    def store_delivery(current: Any) -> dict[str, list[dict[str, Any]]]:
        nonlocal stored, created
        records = _index_records(current)
        for record in records:
            if (
                str(record.get("source_kind", "")) == DIRECT_SOURCE_KIND
                and str(record.get("delivery_id", "")) == safe_delivery_id
            ):
                stored = dict(record)
                return {"notes": records}
        record = {
            "note_number": _next_note_number(records),
            "source_path": source_path,
            "source_kind": DIRECT_SOURCE_KIND,
            "delivery_id": safe_delivery_id,
            "title": "Samantha Quick Note",
            "snippet": _one_line(body_text),
            "body_text": body_text,
            "created_at": safe_created_at or now,
            "modified_at": now,
            "size_bytes": len(body_text.encode("utf-8")),
            "category": "inbox",
            "status": "inbox",
            "first_seen_at": now,
            "last_seen_at": now,
        }
        records.append(record)
        stored = dict(record)
        created = True
        return {"notes": records}

    update_json_file(
        index_path,
        store_delivery,
        default={"notes": []},
        sort_keys=True,
    )
    if stored is None:  # pragma: no cover - defensive transaction invariant.
        raise RuntimeError("Přímé doručení Quick Note nevytvořilo potvrzení.")
    return _record_to_note(stored), created


def list_quick_notes_text(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
    limit: int = 30,
) -> str:
    notes = sync_quick_notes_index(inbox_dir=inbox_dir, index_path=index_path)
    active_notes = [note for note in notes if note.status == "inbox"]
    if not inbox_dir.exists() and not active_notes:
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


def quick_notes_action_status_text(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
    limit: int = 30,
) -> str:
    notes = sync_quick_notes_index(inbox_dir=inbox_dir, index_path=index_path)
    active_notes = [note for note in notes if note.status == "inbox"]
    if not inbox_dir.exists() and not active_notes:
        return (
            "Quick Notes akční inbox zatím nejde načíst, protože iCloud složka není synchronizovaná na Mac.\n"
            f"Očekávaná složka: `{inbox_dir}`"
        )
    if not active_notes:
        return (
            "Quick Notes akční inbox je prázdný.\n"
            f"Složka: `{inbox_dir}`"
        )

    shown = sorted(active_notes, key=lambda note: note.note_number, reverse=True)[: max(1, limit)]
    lines = [
        "Quick Notes akční inbox",
        f"- Inbox: `{inbox_dir}`",
        f"- Soukromý index: `{index_path}`",
        "- Režim: automatická předklasifikace bez provádění akcí",
        "",
    ]
    for note in shown:
        classification = classify_quick_note_note(note)
        label = ACTION_KIND_LABELS.get(classification.kind, classification.kind)
        lines.extend(
            [
                f"QN #{note.note_number} - {label}",
                f"  Stav: {note.status}",
                f"  Jistota: {classification.confidence}",
                f"  Riziko: {classification.risk}",
                f"  Shrnutí: {classification.safe_summary}",
                f"  Další krok: {classification.suggested_next_step}",
                f"  Detail: `show_quick_note_detail(note_number={note.note_number})`",
                "",
            ]
        )
    if len(active_notes) > len(shown):
        lines.append(f"... a dalších {len(active_notes) - len(shown)} poznámek.")
    return "\n".join(lines).rstrip()


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

    if note.body_text:
        text = note.body_text
    else:
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


def classify_quick_note_note(note: QuickNote) -> QuickNoteClassification:
    return classify_quick_note_text(note.snippet)


def classify_quick_note_text(text: str) -> QuickNoteClassification:
    folded = _normalize_for_matching(text)
    summary = _safe_summary(text)
    rules: tuple[tuple[str, tuple[str, ...], str, str, str], ...] = (
        (
            "sensitive_action",
            (
                "smaz",
                "vymaz",
                "odstran",
                "posli",
                "odesli",
                "email",
                "e-mail",
                "mail",
                "zaplat",
                "platbu",
                "objedn",
                "kup",
                "nakup",
                "commit",
                "push",
                "force",
                "reset",
                "heslo",
                "token",
                "api klic",
                "api key",
                "tajem",
                "pdf",
                "dokument",
                "smlouv",
                "faktura",
            ),
            "high",
            "high",
            "Jen připravit bezpečný návrh. Nic neposílat, nemazat, neplatit, necommitovat ani nepracovat s citlivými daty bez potvrzení.",
        ),
        (
            "reminder_candidate",
            (
                "pripomen",
                "pripom",
                "pripominka",
                "zitra",
                "dnes",
                "pondeli",
                "utery",
                "streda",
                "ctvrtek",
                "patek",
                "sobota",
                "nedele",
                "termin",
                "deadline",
                "zavolat",
                "zavolej",
            ),
            "high",
            "low",
            "Připravit návrh připomínky a zeptat se na potvrzení data, času a textu.",
        ),
        (
            "tool_candidate",
            (
                "tool",
                "skript",
                "script",
                "tlacitko",
                "tlačítko",
                "workflow",
                "report",
                "automatiz",
                "cli",
                "cockpit",
                "kokpit",
            ),
            "high",
            "medium",
            "Připravit malý implementační návrh toolu/workflow; zatím nic neměnit bez zadání.",
        ),
        (
            "project_candidate",
            (
                "projekt",
                "project",
                "handoff",
                "rozprac",
                "priorita",
                "systemova mapa",
                "systémová mapa",
                "oblast",
            ),
            "high",
            "medium",
            "Připravit návrh projektu nebo handoffu a zařadit ho až po potvrzení.",
        ),
        (
            "archive_candidate",
            (
                "uloz",
                "uložit",
                "archiv",
                "knihovna",
                "knowledge",
                "znalost",
                "recept",
                "poznamka do databaze",
                "poznámka do databáze",
            ),
            "medium",
            "medium",
            "Navrhnout uložení do vhodného soukromého archivu nebo znalostní databáze.",
        ),
        (
            "action_candidate",
            (
                "udelat",
                "udělat",
                "oprav",
                "zkontrol",
                "priprav",
                "připrav",
                "nastav",
                "dodelat",
                "dodělat",
                "vyres",
                "vyřeš",
            ),
            "medium",
            "medium",
            "Připravit konkrétní další krok a před provedením ověřit rozsah.",
        ),
    )
    for kind, needles, confidence, risk, next_step in rules:
        matched = tuple(needle for needle in needles if needle in folded)
        if matched:
            return QuickNoteClassification(
                kind=kind,
                confidence=confidence,
                risk=risk,
                sensitive=kind == "sensitive_action" or risk == "high",
                safe_summary=summary,
                suggested_next_step=next_step,
                matched_terms=matched[:5],
            )

    return QuickNoteClassification(
        kind="idea",
        confidence="low",
        risk="low",
        sensitive=False,
        safe_summary=summary,
        suggested_next_step="Přečíst detail a ručně rozhodnout, jestli z toho bude úkol, projekt, tool, připomínka nebo jen poznámka.",
        matched_terms=(),
    )


def sync_quick_notes_index(
    *,
    inbox_dir: Path = DEFAULT_ICLOUD_SHORTCUTS_INBOX,
    index_path: Path = DEFAULT_INDEX_PATH,
) -> list[QuickNote]:
    observed: list[dict[str, Any]] = []
    now = _now_iso()
    for source_path in _iter_note_files(inbox_dir):
        stat = source_path.stat()
        text = _read_text(source_path)
        observed.append(
            {
                "source_path": str(source_path),
                "title": _extract_title(text, source_path),
                "snippet": _extract_snippet(text),
                "created_at": _extract_note_datetime(text) or _format_timestamp(stat.st_mtime),
                "modified_at": _format_timestamp(stat.st_mtime),
                "size_bytes": stat.st_size,
                "last_seen_at": now,
            }
        )

    if not observed:
        records = _load_index(index_path)
    else:
        def merge_observed(current: Any) -> dict[str, list[dict[str, Any]]]:
            records = _index_records(current)
            by_path = {str(record.get("source_path", "")): record for record in records}
            next_number = _next_note_number(records)
            for snapshot in observed:
                source_key = str(snapshot["source_path"])
                existing = by_path.get(source_key)
                if existing is None:
                    existing = {
                        "note_number": next_number,
                        "source_path": source_key,
                        "category": "inbox",
                        "status": "inbox",
                        "first_seen_at": now,
                    }
                    next_number += 1
                    records.append(existing)
                    by_path[source_key] = existing
                status = existing.get("status") or "inbox"
                category = existing.get("category") or "inbox"
                existing.update(snapshot)
                existing["status"] = status
                existing["category"] = category
            return {"notes": records}

        updated = update_json_file(index_path, merge_observed, default={"notes": []}, sort_keys=True)
        records = _index_records(updated)

    return [
        _record_to_note(record)
        for record in sorted(records, key=lambda item: int(item.get("note_number", 0)))
        if _record_source_available(record)
    ]


def _load_index(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _index_records(json.loads(path.read_text(encoding="utf-8")))


def _index_records(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise ValueError("Quick notes index musi byt JSON objekt.")
    records = data.get("notes", [])
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("Quick notes index musi obsahovat pole notes se slovniky.")
    return records


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


def _safe_summary(text: str, max_len: int = 160) -> str:
    compact = _one_line(text, max_len=max_len)
    return compact if compact else "(prázdná poznámka)"


def _normalize_for_matching(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "č": "c",
            "ď": "d",
            "é": "e",
            "ě": "e",
            "í": "i",
            "ň": "n",
            "ó": "o",
            "ř": "r",
            "š": "s",
            "ť": "t",
            "ú": "u",
            "ů": "u",
            "ý": "y",
            "ž": "z",
        }
    )
    return text.casefold().translate(replacements)


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _delivery_day(created_at: str) -> str:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", created_at)
    if match:
        return match.group(1)
    return datetime.now(timezone.utc).date().isoformat()


def _record_source_available(record: dict[str, Any]) -> bool:
    if str(record.get("source_kind", "")) == DIRECT_SOURCE_KIND:
        return True
    return Path(str(record.get("source_path", ""))).exists()


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
        source_kind=str(record.get("source_kind") or ""),
        body_text=str(record.get("body_text") or ""),
    )
