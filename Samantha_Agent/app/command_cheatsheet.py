"""Read-only loader for Míla's git-safe command cheatsheet."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMMAND_CHEATSHEET_PATH = (
    PROJECT_ROOT / "memory" / "infrastructure" / "klicove_prikazy_pamatovacek.md"
)
MAX_CHEATSHEET_BYTES = 100_000
MAX_CELL_CHARS = 2_000


def _plain_markdown_cell(value: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", value.strip())
    return " ".join(text.split())[:MAX_CELL_CHARS]


def _table_cells(line: str) -> tuple[str, str] | None:
    clean = line.strip()
    if not clean.startswith("|") or not clean.endswith("|"):
        return None
    cells = [cell.strip() for cell in clean[1:-1].split("|")]
    if len(cells) != 2:
        return None
    if all(re.fullmatch(r"[-: ]+", cell or " ") for cell in cells):
        return None
    first = _plain_markdown_cell(cells[0])
    second = _plain_markdown_cell(cells[1])
    if first.casefold() in {"příkaz", "příkaz nebo klávesy"}:
        return None
    if not first or not second:
        return None
    return first, second


def load_command_cheatsheet(
    path: Path = DEFAULT_COMMAND_CHEATSHEET_PATH,
) -> dict[str, Any]:
    """Return only table commands and explanations from the fixed Markdown source."""
    source = Path(path)
    try:
        if source.stat().st_size > MAX_CHEATSHEET_BYTES:
            raise ValueError("Pamatováček je příliš velký pro bezpečné zobrazení.")
        text = source.read_text(encoding="utf-8")
    except OSError:
        return {
            "ok": False,
            "message": "Pamatováček není dostupný.",
            "sections": [],
        }
    except ValueError as exc:
        return {
            "ok": False,
            "message": str(exc) or "Pamatováček není dostupný.",
            "sections": [],
        }

    title = "Pamatováček"
    current_title = ""
    section_rows: list[dict[str, str]] = []
    sections: list[dict[str, Any]] = []

    def flush_section() -> None:
        nonlocal section_rows
        if current_title and section_rows:
            sections.append({"title": current_title, "items": section_rows})
        section_rows = []

    for raw_line in text.splitlines():
        if raw_line.startswith("# "):
            title = _plain_markdown_cell(raw_line[2:]) or title
            continue
        if raw_line.startswith("## "):
            flush_section()
            current_title = _plain_markdown_cell(raw_line[3:])
            continue
        cells = _table_cells(raw_line)
        if cells is not None:
            command, explanation = cells
            section_rows.append({"command": command, "explanation": explanation})
    flush_section()

    if not sections:
        return {
            "ok": False,
            "message": "Pamatováček neobsahuje žádné bezpečně rozpoznané příkazy.",
            "sections": [],
        }
    return {
        "ok": True,
        "message": "Pamatováček je read-only; příkazy nelze z Cockpitu spustit ani upravit.",
        "title": title,
        "sections": sections,
    }
