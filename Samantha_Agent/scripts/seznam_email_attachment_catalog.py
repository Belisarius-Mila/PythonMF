#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = PROJECT_ROOT / "data" / "private" / "email_seznam"
DEFAULT_CSV = BASE_DIR / "seznam_pojisteni_only_2011_2026.csv"
DEFAULT_ATTACHMENTS_DIR = BASE_DIR / "attachments" / "INBOX"
DEFAULT_OUT_CSV = BASE_DIR / "insurance_attachment_catalog.csv"
DEFAULT_OUT_MD = BASE_DIR / "insurance_attachment_catalog.md"


@dataclass(frozen=True)
class AttachmentItem:
    uid: str
    date: str
    sender: str
    subject: str
    insurer: str
    policy_number: str
    year_hint: str
    document_type: str
    importance: str
    original_filename: str
    local_path: str
    size_bytes: int
    content_type: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vytvori katalog lokalne stazenych pojistnych priloh ze Seznam e-mailu."
    )
    parser.add_argument("--metadata-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--attachments-dir", type=Path, default=DEFAULT_ATTACHMENTS_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def fold(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.casefold()


def load_metadata(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    return {row.get("uid", ""): row for row in rows if row.get("uid")}


def read_manifest(path: Path) -> list[dict[str, object]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def classify_insurer(sender: str, subject: str, filename: str) -> str:
    value = fold(" ".join((sender, subject, filename)))
    checks = (
        ("RIXO", ("rixo",)),
        ("CPP", ("cpp", "c pp", "ceska podnikatelska", "autopojisteni combi plus")),
        ("Kooperativa", ("koop", "kooperativa")),
        ("MetLife", ("metlife", "one life", "onelife")),
        ("AXA / Top-pojisteni", ("axa", "top-pojisteni", "top pojisteni", "travel")),
        ("KB / karta / Bezpeci", ("kb.cz", "kbinfo", "komerc", "platebnich karet", "sluzby bezpeci")),
        ("Generali", ("generali",)),
    )
    for label, terms in checks:
        if any(term in value for term in terms):
            return label
    return "Neurceno"


def classify_document(filename: str, subject: str) -> str:
    file_value = fold(filename)
    file_words = re.sub(r"[_\-.]+", " ", file_value)
    subject_value = fold(subject)
    subject_words = re.sub(r"[_\-.]+", " ", subject_value)
    checks = (
        ("Pojistna smlouva", ("smlouva", "original", "pojistka", "pojisteni vozidla")),
        ("Navrh smlouvy", ("navrh", "nabidka")),
        ("Zelena karta", ("zelena karta", "zelen karta")),
        ("Danove potvrzeni", ("danove potvrzeni", "da ov potvrzen", "danove_potvrzeni")),
        ("Platba / upominka", ("upomenuti", "pripomenuti platby", "neuhrazene pojistne")),
        ("Asistencni karta", ("asistencni karta",)),
        ("Zaznam / jednani / nehoda", ("zaznam", "dopravni nehode", "sjednani", "jednani")),
        ("Predsmluvni informace", ("predsmluvni", "informace pro zajemce", "informace_o_pojisteni", "memorandum", "ipzop")),
        ("IPID / produktovy list", ("ipid", "informacni dokument o pojistnem produktu")),
        ("Pojistne podminky", ("podminky", "vpp", "sucp", "soubor pojistnych")),
        ("Porovnani nabidek", ("porovnani nabidek",)),
        ("Investice / zhodnoceni", ("investice", "akciove fondy", "zhodnoceni")),
        ("Obecne bankovni dokumenty", ("cenik", "vseobecne obchodni", "pravidla provadeni plateb", "sdeleni informaci")),
        ("Obrazek / podpis", (".png", ".jpg", ".jpeg", "signature", "metlife_hdr", "metlife_ftr")),
        ("Archiv ZIP", (".zip",)),
        ("Podpis / certifikat", (".p7s", "smime")),
    )
    for label, terms in checks:
        if any(term in file_value or term in file_words for term in terms):
            return label
    # Subject is only a fallback for attachments without a meaningful filename.
    if filename.strip().casefold() in {"", "(bez nazvu)"}:
        for label, terms in checks:
            if any(term in subject_value or term in subject_words for term in terms):
                return label
    return "Proverit rucne"


def importance(document_type: str, insurer: str) -> str:
    if document_type in {
        "Pojistna smlouva",
        "Navrh smlouvy",
        "Zelena karta",
        "Danove potvrzeni",
        "Platba / upominka",
    }:
        return "dulezite"
    if document_type in {
        "Asistencni karta",
        "Zaznam / jednani / nehoda",
        "Predsmluvni informace",
        "IPID / produktovy list",
        "Porovnani nabidek",
    }:
        return "uzitecne"
    if document_type in {
        "Pojistne podminky",
        "Obecne bankovni dokumenty",
        "Obrazek / podpis",
        "Podpis / certifikat",
    }:
        return "balast"
    if insurer == "Neurceno":
        return "proverit"
    return "uzitecne"


def policy_number(subject: str, filename: str) -> str:
    value = " ".join((subject, filename))
    matches = re.findall(r"\b\d{7,10}\b", value)
    if not matches:
        return ""
    return "; ".join(dict.fromkeys(matches))


def year_hint(date: str, filename: str, subject: str) -> str:
    value = " ".join((date, filename, subject))
    matches = re.findall(r"\b20\d{2}\b", value)
    if not matches:
        return ""
    return "; ".join(dict.fromkeys(matches))


def iter_items(metadata: dict[str, dict[str, str]], attachments_dir: Path) -> list[AttachmentItem]:
    items: list[AttachmentItem] = []
    for manifest_path in sorted(attachments_dir.glob("uid_*/attachments_manifest.json")):
        uid = manifest_path.parent.name.removeprefix("uid_")
        row = metadata.get(uid, {})
        sender = row.get("sender", "")
        subject = row.get("subject", "")
        date = row.get("date", "")
        for attachment in read_manifest(manifest_path):
            original = str(attachment.get("filename") or "")
            path = str(attachment.get("path") or "")
            size = int(attachment.get("size_bytes") or 0)
            content_type = str(attachment.get("content_type") or "")
            insurer = classify_insurer(sender, subject, original)
            doc_type = classify_document(original, subject)
            items.append(
                AttachmentItem(
                    uid=uid,
                    date=date,
                    sender=sender,
                    subject=subject,
                    insurer=insurer,
                    policy_number=policy_number(subject, original),
                    year_hint=year_hint(date, original, subject),
                    document_type=doc_type,
                    importance=importance(doc_type, insurer),
                    original_filename=original,
                    local_path=path,
                    size_bytes=size,
                    content_type=content_type,
                )
            )
    return sorted(
        items,
        key=lambda item: (
            {"dulezite": 0, "uzitecne": 1, "proverit": 2, "balast": 3}.get(item.importance, 9),
            item.insurer,
            item.document_type,
            item.date,
            item.uid,
            item.original_filename,
        ),
    )


def write_csv(items: list[AttachmentItem], path: Path) -> None:
    fieldnames = [
        "uid",
        "date",
        "sender",
        "subject",
        "insurer",
        "policy_number",
        "year_hint",
        "document_type",
        "importance",
        "original_filename",
        "local_path",
        "size_bytes",
        "content_type",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow({name: getattr(item, name) for name in fieldnames})


def write_markdown(items: list[AttachmentItem], path: Path) -> None:
    by_importance = Counter(item.importance for item in items)
    by_insurer = Counter(item.insurer for item in items)
    by_doc = Counter(item.document_type for item in items)
    lines = [
        "# Katalog stazenych pojistnych priloh ze Seznamu",
        "",
        f"Priloh celkem: {len(items)}",
        "",
        "## Souhrn podle dulezitosti",
        "",
    ]
    for label in ("dulezite", "uzitecne", "proverit", "balast"):
        lines.append(f"- {label}: {by_importance.get(label, 0)}")
    lines.extend(["", "## Souhrn podle pojistovny / zdroje", ""])
    for label, count in by_insurer.most_common():
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Souhrn podle typu dokumentu", ""])
    for label, count in by_doc.most_common():
        lines.append(f"- {label}: {count}")

    grouped: dict[str, list[AttachmentItem]] = defaultdict(list)
    for item in items:
        grouped[item.importance].append(item)

    titles = {
        "dulezite": "Dulezite dokumenty",
        "uzitecne": "Uzitecne doplnky",
        "proverit": "Proverit rucne",
        "balast": "Balast / obecne prilohy",
    }
    for importance_label in ("dulezite", "uzitecne", "proverit", "balast"):
        lines.extend(["", f"## {titles[importance_label]}", ""])
        for item in grouped.get(importance_label, []):
            rel_path = Path(item.local_path)
            try:
                rel_path = rel_path.relative_to(PROJECT_ROOT)
            except ValueError:
                pass
            detail = []
            if item.policy_number:
                detail.append(f"smlouva {item.policy_number}")
            if item.year_hint:
                detail.append(f"rok {item.year_hint}")
            suffix = f" ({', '.join(detail)})" if detail else ""
            lines.extend(
                [
                    f"### {item.insurer} - {item.document_type}{suffix}",
                    "",
                    f"- UID: `{item.uid}`",
                    f"- Datum: {item.date}",
                    f"- Predmet: {item.subject}",
                    f"- Soubor: `{item.original_filename}`",
                    f"- Lokalni cesta: `{rel_path}`",
                    f"- Velikost: {round(item.size_bytes / 1024 / 1024, 2)} MB",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    metadata = load_metadata(args.metadata_csv)
    items = iter_items(metadata, args.attachments_dir)
    write_csv(items, args.out_csv)
    write_markdown(items, args.out_md)
    print(f"Katalog CSV: {args.out_csv}")
    print(f"Katalog Markdown: {args.out_md}")
    print(f"Priloh celkem: {len(items)}")
    print("Dulezitost:")
    for label, count in Counter(item.importance for item in items).most_common():
        print(f"- {label}: {count}")
    print("Top dulezite:")
    for item in [item for item in items if item.importance == "dulezite"][:20]:
        print(f"- UID {item.uid}: {item.insurer}: {item.document_type}: {item.original_filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
