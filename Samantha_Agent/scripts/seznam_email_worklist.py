#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = PROJECT_ROOT / "data" / "private" / "email_seznam"
DEFAULT_INPUT = BASE_DIR / "seznam_pojisteni_only_2011_2026.csv"
ATTACHMENTS_DIR = BASE_DIR / "attachments"


@dataclass(frozen=True)
class WorkItem:
    row: dict[str, str]
    category: str
    score: int
    downloaded: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vytvori prakticky worklist z vyhledanych Seznam e-mailu.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-md", type=Path, default=BASE_DIR / "seznam_email_worklist_500.md")
    parser.add_argument(
        "--out-commands",
        type=Path,
        default=BASE_DIR / "next_attachment_download_commands.txt",
    )
    parser.add_argument("--command-limit", type=int, default=30)
    return parser.parse_args()


def low(value: str | None) -> str:
    return (value or "").casefold()


def attachment_count(row: dict[str, str]) -> int:
    try:
        return int(row.get("attachment_count") or 0)
    except ValueError:
        return 0


def text(row: dict[str, str]) -> str:
    return " ".join(
        (
            row.get("sender", ""),
            row.get("subject", ""),
            row.get("attachment_names", ""),
            row.get("matched_terms", ""),
        )
    ).casefold()


def category(row: dict[str, str]) -> str:
    value = text(row)
    if any(item in value for item in ("rixo", "čpp", "cpp", "koop", "zelená karta", "zelena karta", "autopoji", "vozid", "povinn")):
        return "Auto / vozidlo"
    if any(item in value for item in ("metlife", "život", "zivot", "úraz", "uraz", "nemoci", "danove potvrzeni", "daňové potvrzení")):
        return "Životní / úrazové / daňová potvrzení"
    if any(item in value for item in ("penzijn", "kbps", "generalipenze", "dps")):
        return "Penzijní"
    if any(item in value for item in ("cestovn", "cedok", "top-pojisteni", "axa-assistance", "booking")):
        return "Cestovní"
    if any(item in value for item in ("majet", "domác", "domac", "nemovit", "odpověd", "odpoved")):
        return "Majetek / domácnost / odpovědnost"
    if any(item in value for item in ("kb.cz", "kbinfo", "komercpoj", "platebnich karet", "službě bezpečí", "sluzbe bezpeci")):
        return "Banka / karta / služba Bezpečí"
    if any(item in value for item in ("generali", "pojišťovna", "pojistovna", "pojistn", "pojiště", "pojiste")):
        return "Ostatní pojištění"
    return "Širší smlouvy / prověřit ručně"


def score(row: dict[str, str], cat: str) -> int:
    value = text(row)
    result = attachment_count(row) * 3
    if cat in {"Auto / vozidlo", "Majetek / domácnost / odpovědnost", "Životní / úrazové / daňová potvrzení"}:
        result += 20
    elif cat in {"Penzijní", "Cestovní", "Banka / karta / služba Bezpečí"}:
        result += 12
    else:
        result += 5
    if any(item in value for item in ("smlouva", "pojistná smlouva", "pojistne smlouvy", "zelená karta", "zelena karta", "návrh", "navrh")):
        result += 8
    if any(item in value for item in ("obchodní sdělení", "obchodni sdeleni", "pozvánka", "pozvanka")):
        result -= 10
    if "png" in low(row.get("attachment_names")) and "pdf" not in low(row.get("attachment_names")):
        result -= 12
    return result


def downloaded_uids() -> set[str]:
    if not ATTACHMENTS_DIR.exists():
        return set()
    values: set[str] = set()
    for path in ATTACHMENTS_DIR.glob("*/*"):
        if path.is_dir() and path.name.startswith("uid_"):
            values.add(path.name.removeprefix("uid_"))
    return values


def load_items(input_path: Path) -> list[WorkItem]:
    rows = list(csv.DictReader(input_path.open(encoding="utf-8")))
    done = downloaded_uids()
    items: list[WorkItem] = []
    for row in rows:
        cat = category(row)
        items.append(
            WorkItem(
                row=row,
                category=cat,
                score=score(row, cat),
                downloaded=row.get("uid", "") in done,
            )
        )
    items.sort(key=lambda item: (item.downloaded, item.score, attachment_count(item.row)), reverse=True)
    return items


def item_line(item: WorkItem, index: int) -> list[str]:
    row = item.row
    status = "staženo" if item.downloaded else "stáhnout"
    return [
        f"### {index}. {row.get('subject') or '(bez předmětu)'}",
        "",
        f"- Stav: {status}",
        f"- Kategorie: {item.category}",
        f"- Datum: {row.get('date', '')}",
        f"- Od: {row.get('sender', '')}",
        f"- Složka/UID: `{row.get('folder', '')}` / `{row.get('uid', '')}`",
        f"- Přílohy: {row.get('attachment_count', '')} {row.get('attachment_names', '')}",
        "",
    ]


def main() -> int:
    args = parse_args()
    items = load_items(args.input)
    downloaded = [item for item in items if item.downloaded]
    pending_with_attachments = [
        item for item in items if not item.downloaded and attachment_count(item.row) > 0 and item.score >= 12
    ]
    category_counts: dict[str, int] = {}
    for item in items:
        category_counts[item.category] = category_counts.get(item.category, 0) + 1

    lines = [
        "# Seznam e-mail worklist z prvních 500 výsledků",
        "",
        f"Zdroj: `{args.input.name}`",
        f"Položek ve vstupu: {len(items)}",
        f"Už stažené e-maily s přílohami: {len(downloaded)}",
        f"Doporučené další e-maily ke stažení příloh: {len(pending_with_attachments)}",
        "",
        "## Kategorie",
        "",
    ]
    for cat, count in sorted(category_counts.items(), key=lambda item: item[0]):
        lines.append(f"- {cat}: {count}")
    lines.extend(["", "## Už staženo", ""])
    for index, item in enumerate(downloaded, start=1):
        lines.extend(item_line(item, index))

    lines.extend(["", "## Doporučené další stažení příloh", ""])
    for index, item in enumerate(pending_with_attachments[: args.command_limit], start=1):
        lines.extend(item_line(item, index))

    args.out_md.write_text("\n".join(lines), encoding="utf-8")

    command_lines = [
        "# Spoustet v terminalu, kde je nastavene SEZNAM_MAIL_PASSWORD.",
        "# Prikazy nestahuji nic znovu pro UID, ktere uz jsou oznacene jako stazene ve worklistu.",
        "",
    ]
    for item in pending_with_attachments[: args.command_limit]:
        row = item.row
        command_lines.append(
            ".venv/bin/python scripts/seznam_email_search.py save-attachments "
            f"--folder {row.get('folder', 'INBOX')} --uid {row.get('uid', '')}"
        )
    args.out_commands.write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    print(f"Worklist: {args.out_md}")
    print(f"Prikazy: {args.out_commands}")
    print(f"Už staženo: {len(downloaded)}")
    print(f"Doporučeno ke stažení: {len(pending_with_attachments)}")
    print("Top další:")
    for item in pending_with_attachments[:10]:
        row = item.row
        print(f"- UID {row.get('uid', '')}: {item.category}: {row.get('subject', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
