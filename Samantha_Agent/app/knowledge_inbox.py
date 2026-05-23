from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_INBOX_ROOT = PROJECT_ROOT / "data" / "private" / "knowledge_inbox"
INCOMING_DIR = KNOWLEDGE_INBOX_ROOT / "incoming"
PROCESSED_DIR = KNOWLEDGE_INBOX_ROOT / "processed"
NOTES_DIR = KNOWLEDGE_INBOX_ROOT / "notes"


@dataclass(frozen=True)
class KnowledgeInboxItem:
    area: str
    name: str
    suffix: str
    size_bytes: int
    modified: str


def format_knowledge_inbox_inventory(
    *,
    inbox_root: Path = KNOWLEDGE_INBOX_ROOT,
    max_items: int = 50,
) -> str:
    items = knowledge_inbox_inventory(inbox_root=inbox_root)
    totals = _totals(items)
    lines = [
        "Knowledge Inbox Inventory",
        f"- Root: {inbox_root}",
        f"- Files: {len(items)}",
        f"- Total size: {_format_size(totals)}",
        "- Reads content: no",
        "- Git: private inbox is ignored",
        "",
        "Folders:",
        f"- incoming: {inbox_root / 'incoming'}",
        f"- processed: {inbox_root / 'processed'}",
        f"- notes: {inbox_root / 'notes'}",
        "",
        "Items:",
        "| Area | Name | Type | Size | Modified |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for item in items[:max_items]:
        lines.append(
            f"| {item.area} | `{item.name}` | `{item.suffix}` | {_format_size(item.size_bytes)} | {item.modified} |"
        )
    if len(items) > max_items:
        lines.append(f"| ... | ... | ... | ... | omitted {len(items) - max_items} files |")
    if not items:
        lines.append("| - | - | - | 0 B | - |")
    lines.extend(
        [
            "",
            "Next step:",
            "- Pokud chces neco zpracovat, vyber konkretni soubor nebo malou davku.",
            "- Pred zapracovanim do memory ma nasledovat navrh redigovaneho souhrnu a potvrzeni.",
        ]
    )
    return "\n".join(lines)


def knowledge_inbox_inventory(*, inbox_root: Path = KNOWLEDGE_INBOX_ROOT) -> tuple[KnowledgeInboxItem, ...]:
    items: list[KnowledgeInboxItem] = []
    for area in ("incoming", "processed", "notes"):
        folder = inbox_root / area
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            stat = path.stat()
            items.append(
                KnowledgeInboxItem(
                    area=area,
                    name=str(path.relative_to(folder)),
                    suffix=_suffix(path),
                    size_bytes=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                )
            )
    return tuple(sorted(items, key=lambda item: (item.area, item.name.casefold())))


def ensure_knowledge_inbox_dirs(inbox_root: Path = KNOWLEDGE_INBOX_ROOT) -> None:
    for folder_name in ("incoming", "processed", "notes"):
        (inbox_root / folder_name).mkdir(parents=True, exist_ok=True)


def _suffix(path: Path) -> str:
    suffix = path.suffix.casefold()
    return suffix if suffix else "(no extension)"


def _totals(items: tuple[KnowledgeInboxItem, ...]) -> int:
    return sum(item.size_bytes for item in items)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f} MB"
    return f"{size_bytes / 1024 / 1024 / 1024:.1f} GB"
