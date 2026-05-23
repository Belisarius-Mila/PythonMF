from __future__ import annotations

import shutil
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS_DIR = Path.home() / "Downloads"
KNOWLEDGE_INBOX_ROOT = PROJECT_ROOT / "data" / "private" / "knowledge_inbox"
INCOMING_DIR = KNOWLEDGE_INBOX_ROOT / "incoming"
PROCESSED_DIR = KNOWLEDGE_INBOX_ROOT / "processed"
NOTES_DIR = KNOWLEDGE_INBOX_ROOT / "notes"
COPY_CONFIRMATION_PHRASE = "Potvrzuji kopirovani do knowledge inbox"


@dataclass(frozen=True)
class KnowledgeInboxItem:
    area: str
    name: str
    suffix: str
    size_bytes: int
    modified: str


@dataclass(frozen=True)
class DownloadsItem:
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


def format_downloads_inventory(
    *,
    downloads_dir: Path = DOWNLOADS_DIR,
    max_items: int = 50,
) -> str:
    items = downloads_inventory(downloads_dir=downloads_dir)
    totals = _download_totals(items)
    lines = [
        "Downloads Inventory for Knowledge Inbox",
        f"- Source: {downloads_dir}",
        f"- Files: {len(items)}",
        f"- Total size: {_format_size(totals)}",
        "- Reads content: no",
        "- Scope: top-level files only; folders are omitted",
        "- Destination for confirmed copy: `data/private/knowledge_inbox/incoming/`",
        "",
        "Items:",
        "| Name | Type | Size | Modified |",
        "| --- | --- | ---: | --- |",
    ]
    for item in items[:max_items]:
        lines.append(
            f"| `{item.name}` | `{item.suffix}` | {_format_size(item.size_bytes)} | {item.modified} |"
        )
    if len(items) > max_items:
        lines.append(f"| ... | ... | ... | omitted {len(items) - max_items} files |")
    if not items:
        lines.append("| - | - | 0 B | - |")
    lines.extend(
        [
            "",
            "Copy workflow:",
            "- Vyber konkretni soubor nebo malou davku podle nazvu.",
            f"- Kopirovani vyzaduje potvrzeni: `{COPY_CONFIRMATION_PHRASE}`.",
        ]
    )
    return "\n".join(lines)


def downloads_inventory(*, downloads_dir: Path = DOWNLOADS_DIR) -> tuple[DownloadsItem, ...]:
    if not downloads_dir.exists():
        return ()

    items: list[DownloadsItem] = []
    for path in sorted(downloads_dir.iterdir()):
        if not path.is_file():
            continue
        stat = path.stat()
        items.append(
            DownloadsItem(
                name=path.name,
                suffix=_suffix(path),
                size_bytes=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            )
        )
    return tuple(sorted(items, key=lambda item: item.name.casefold()))


def copy_downloads_to_knowledge_inbox(
    relative_paths: str,
    *,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    downloads_dir: Path = DOWNLOADS_DIR,
    inbox_root: Path = KNOWLEDGE_INBOX_ROOT,
) -> str:
    requested_paths = _parse_requested_paths(relative_paths)
    if not requested_paths:
        return (
            "Downloads to Knowledge Inbox\n"
            "- Status: nothing selected\n"
            "- Next step: provide one file name per line or comma-separated file names."
        )

    source_files, errors = _resolve_download_sources(requested_paths, downloads_dir)
    if errors:
        return "\n".join(
            [
                "Downloads to Knowledge Inbox",
                "- Status: blocked",
                "- Reason: invalid selection",
                "",
                "Problems:",
                *[f"- {error}" for error in errors],
            ]
        )

    total_size = sum(path.stat().st_size for path in source_files)
    preview_lines = [
        "Downloads to Knowledge Inbox",
        f"- Source: {downloads_dir}",
        f"- Destination: {inbox_root / 'incoming'}",
        f"- Selected files: {len(source_files)}",
        f"- Total size: {_format_size(total_size)}",
        "",
        "Selected:",
        *[f"- `{path.name}` ({_format_size(path.stat().st_size)})" for path in source_files],
    ]

    if not user_confirmed or not _has_copy_confirmation(confirmation_text):
        preview_lines.extend(
            [
                "",
                "- Status: preview only; no files copied",
                f"- Required confirmation: `{COPY_CONFIRMATION_PHRASE}`",
            ]
        )
        return "\n".join(preview_lines)

    copied: list[str] = []
    ensure_knowledge_inbox_dirs(inbox_root)
    incoming_dir = inbox_root / "incoming"
    for source in source_files:
        destination = _unique_destination(incoming_dir / source.name)
        shutil.copy2(source, destination)
        copied.append(str(destination.relative_to(inbox_root)))

    preview_lines.extend(
        [
            "",
            "- Status: copied",
            "",
            "Copied to private inbox:",
            *[f"- `{path}`" for path in copied],
        ]
    )
    return "\n".join(preview_lines)


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


def _download_totals(items: tuple[DownloadsItem, ...]) -> int:
    return sum(item.size_bytes for item in items)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f} MB"
    return f"{size_bytes / 1024 / 1024 / 1024:.1f} GB"


def _parse_requested_paths(relative_paths: str) -> tuple[str, ...]:
    parts: list[str] = []
    for line in relative_paths.replace(",", "\n").splitlines():
        path = line.strip().strip("'\"")
        if path:
            parts.append(path)
    return tuple(parts)


def _resolve_download_sources(
    requested_paths: tuple[str, ...],
    downloads_dir: Path,
) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    root = downloads_dir.expanduser().resolve()
    files: list[Path] = []
    errors: list[str] = []

    for requested in requested_paths:
        requested_path = Path(requested)
        if requested_path.is_absolute() or ".." in requested_path.parts:
            errors.append(f"`{requested}` is outside the allowed Downloads relative path scope.")
            continue

        source = (root / requested_path).resolve()
        if not _is_relative_to(source, root):
            errors.append(f"`{requested}` resolves outside Downloads.")
            continue
        if not source.exists():
            errors.append(f"`{requested}` was not found in Downloads.")
            continue
        if not source.is_file():
            errors.append(f"`{requested}` is not a file.")
            continue
        files.append(source)

    return tuple(files), tuple(errors)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _has_copy_confirmation(text: str) -> bool:
    normalized = _normalize(text)
    return all(token in normalized for token in ("potvrzuji", "kopirovani", "knowledge", "inbox"))


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
