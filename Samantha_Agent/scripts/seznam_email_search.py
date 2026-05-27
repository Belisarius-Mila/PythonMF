#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import getpass
import imaplib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
OUT_DIR = PROJECT_ROOT / "data" / "private" / "email_seznam"
DEFAULT_TERMS = (
    "pojiš",
    "pojis",
    "pojištění",
    "pojisteni",
    "připojiš",
    "pripojis",
    "připojištění",
    "pripojisteni",
    "smluv",
    "smlouva",
    "smlouvy",
    "pojistka",
    "pojistné",
    "pojistne",
)
HEADER_FETCH_SPEC = "(BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT MESSAGE-ID)])"
MESSAGE_FETCH_SPEC = "(BODY.PEEK[])"
MAX_MESSAGE_BYTES = 25_000_000


@dataclass(frozen=True)
class MailConfig:
    address: str
    password: str
    host: str = "imap.seznam.cz"
    port: int = 993


@dataclass(frozen=True)
class Hit:
    folder: str
    uid: str
    date: str
    sender: str
    subject: str
    message_id: str
    matched_terms: tuple[str, ...]
    attachment_count: int
    attachment_names: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rychle read-only hledani v Seznam.cz e-mailu pres IMAP."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search")
    search.add_argument("--address", default=os.getenv("SEZNAM_MAIL_ADDRESS", ""))
    search.add_argument("--password-env", default="SEZNAM_MAIL_PASSWORD")
    search.add_argument("--since-year", type=int, default=date.today().year - 15)
    search.add_argument("--before-year", type=int, default=date.today().year + 1)
    search.add_argument("--term", action="append", default=[])
    search.add_argument("--limit", type=int, default=500)
    search.add_argument("--folders", default="all", help="'all' nebo carkou oddelene nazvy slozek")
    search.add_argument("--out-dir", type=Path, default=OUT_DIR)

    save = sub.add_parser("save-attachments")
    save.add_argument("--address", default=os.getenv("SEZNAM_MAIL_ADDRESS", ""))
    save.add_argument("--password-env", default="SEZNAM_MAIL_PASSWORD")
    save.add_argument("--folder", required=True)
    save.add_argument("--uid", required=True)
    save.add_argument("--out-dir", type=Path, default=OUT_DIR / "attachments")

    return parser.parse_args()


def load_config(address: str, password_env: str) -> MailConfig:
    if not address:
        raise SystemExit("Chybi Seznam adresa. Pouzij --address nebo SEZNAM_MAIL_ADDRESS v lokalnim .env.")
    password = os.getenv(password_env, "")
    if not password:
        password = getpass.getpass(f"Heslo k {address} (nezobrazuje se): ")
    if not password:
        raise SystemExit("Chybi heslo.")
    return MailConfig(address=address, password=password)


def imap_login(config: MailConfig) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL(config.host, config.port)
    imap.login(config.address, config.password)
    return imap


def decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts: list[str] = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            parts.append(decode_header_bytes(part, encoding))
        else:
            parts.append(part)
    return " ".join(" ".join(parts).split())


def decode_header_bytes(part: bytes, encoding: str | None) -> str:
    for candidate in (encoding, "utf-8", "latin-1"):
        if not candidate:
            continue
        try:
            return part.decode(candidate, errors="replace")
        except LookupError:
            continue
    return part.decode("utf-8", errors="replace")


def quote_imap_utf8(value: str) -> bytes:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'.encode("utf-8")


def quote_mailbox(folder: str) -> str:
    escaped = folder.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_list_response(line: bytes) -> str | None:
    text = line.decode("utf-8", errors="replace")
    match = re.search(r' "/" "?([^"]+)"?$', text)
    if match:
        return match.group(1)
    match = re.search(r' "/" (.+)$', text)
    if match:
        return match.group(1).strip('"')
    return None


def list_folders(imap: imaplib.IMAP4_SSL) -> list[str]:
    status, data = imap.list()
    if status != "OK" or not data:
        return ["INBOX"]
    folders: list[str] = []
    for item in data:
        if not isinstance(item, bytes):
            continue
        folder = parse_list_response(item)
        if folder:
            folders.append(folder)
    return folders or ["INBOX"]


def selected_folders(imap: imaplib.IMAP4_SSL, value: str) -> list[str]:
    if value.strip().casefold() == "all":
        return list_folders(imap)
    return [part.strip() for part in value.split(",") if part.strip()]


def search_term_uids(
    imap: imaplib.IMAP4_SSL,
    term: str,
    since_year: int,
    before_year: int,
) -> list[bytes]:
    since = f"01-Jan-{since_year}"
    before = f"01-Jan-{before_year}"
    status, data = imap.uid(
        "SEARCH",
        "CHARSET",
        "UTF-8",
        "SINCE",
        since,
        "BEFORE",
        before,
        "TEXT",
        quote_imap_utf8(term),
    )
    if status != "OK" or not data or data[0] is None:
        return []
    return data[0].split()


def first_payload(data: list[object]) -> bytes | None:
    for item in data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return None


def fetch_header(imap: imaplib.IMAP4_SSL, uid: bytes) -> Message | None:
    status, data = imap.uid("FETCH", uid, HEADER_FETCH_SPEC)
    if status != "OK" or not data:
        return None
    payload = first_payload(data)
    return message_from_bytes(payload) if payload else None


def fetch_message(imap: imaplib.IMAP4_SSL, uid: str) -> Message:
    status, data = imap.uid("FETCH", uid.encode("ascii"), MESSAGE_FETCH_SPEC)
    if status != "OK" or not data:
        raise RuntimeError("Nepodarilo se nacist zpravu.")
    payload = first_payload(data)
    if not payload or len(payload) > MAX_MESSAGE_BYTES:
        raise RuntimeError("Zprava je prazdna nebo prilis velka.")
    return message_from_bytes(payload)


def attachment_names(message: Message) -> tuple[str, ...]:
    names: list[str] = []
    for part in message.walk() if message.is_multipart() else [message]:
        if part.get_content_maintype() == "multipart":
            continue
        disposition = part.get_content_disposition() or ""
        filename = decode_header_value(part.get_filename()) if part.get_filename() else ""
        if disposition == "attachment" or filename:
            names.append(filename or "(bez nazvu)")
    return tuple(names)


def message_to_hit(
    folder: str,
    uid: bytes,
    header: Message,
    matched_terms: tuple[str, ...],
    imap: imaplib.IMAP4_SSL,
) -> Hit:
    attachment_tuple: tuple[str, ...] = ()
    try:
        message = fetch_message(imap, uid.decode("ascii", errors="replace"))
        attachment_tuple = attachment_names(message)
    except Exception:
        attachment_tuple = ()
    return Hit(
        folder=folder,
        uid=uid.decode("ascii", errors="replace"),
        date=decode_header_value(header.get("Date")),
        sender=decode_header_value(header.get("From")),
        subject=decode_header_value(header.get("Subject")),
        message_id=decode_header_value(header.get("Message-ID")),
        matched_terms=matched_terms,
        attachment_count=len(attachment_tuple),
        attachment_names=attachment_tuple,
    )


def search(config: MailConfig, args: argparse.Namespace) -> list[Hit]:
    terms = tuple(dict.fromkeys(args.term or DEFAULT_TERMS))
    hits: list[Hit] = []
    with imap_login(config) as imap:
        folders = selected_folders(imap, args.folders)
        print(f"Slozky: {len(folders)}")
        for folder in folders:
            status, _data = imap.select(quote_mailbox(folder), readonly=True)
            if status != "OK":
                print(f"SKIP slozka: {folder}")
                continue
            uid_terms: dict[bytes, set[str]] = {}
            for term in terms:
                try:
                    for uid in search_term_uids(imap, term, args.since_year, args.before_year):
                        uid_terms.setdefault(uid, set()).add(term)
                except imaplib.IMAP4.error:
                    continue
            if not uid_terms:
                continue
            print(f"{folder}: {len(uid_terms)} kandidatu")
            for uid in sorted(uid_terms, key=lambda value: int(value), reverse=True):
                if len(hits) >= args.limit:
                    return hits
                header = fetch_header(imap, uid)
                if header is None:
                    continue
                matched = tuple(term for term in terms if term in uid_terms[uid])
                hits.append(message_to_hit(folder, uid, header, matched, imap))
    return hits


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned or "attachment"


def save_attachments(config: MailConfig, args: argparse.Namespace) -> Path:
    out_dir = args.out_dir / safe_filename(args.folder) / f"uid_{safe_filename(args.uid)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[dict[str, object]] = []
    with imap_login(config) as imap:
        status, _data = imap.select(quote_mailbox(args.folder), readonly=True)
        if status != "OK":
            raise SystemExit(f"Nepodarilo se otevrit slozku {args.folder}.")
        message = fetch_message(imap, args.uid)
        for index, part in enumerate(message.walk() if message.is_multipart() else [message], start=1):
            if part.get_content_maintype() == "multipart":
                continue
            disposition = part.get_content_disposition() or ""
            filename = decode_header_value(part.get_filename()) if part.get_filename() else ""
            if disposition != "attachment" and not filename:
                continue
            payload = part.get_payload(decode=True)
            if not isinstance(payload, bytes):
                continue
            final_name = f"{index:02d}_{safe_filename(filename or 'attachment.bin')}"
            path = out_dir / final_name
            path.write_bytes(payload)
            saved.append(
                {
                    "filename": filename or "(bez nazvu)",
                    "path": str(path),
                    "content_type": part.get_content_type(),
                    "size_bytes": len(payload),
                }
            )
    (out_dir / "attachments_manifest.json").write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_dir


def write_outputs(hits: list[Hit], out_dir: Path, since_year: int, before_year: int) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"seznam_pojisteni_smlouvy_{since_year}_{before_year - 1}.csv"
    md_path = out_dir / f"seznam_pojisteni_smlouvy_{since_year}_{before_year - 1}.md"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "folder",
                "uid",
                "date",
                "sender",
                "subject",
                "matched_terms",
                "attachment_count",
                "attachment_names",
                "message_id",
            ],
        )
        writer.writeheader()
        for hit in hits:
            writer.writerow(
                {
                    "folder": hit.folder,
                    "uid": hit.uid,
                    "date": hit.date,
                    "sender": hit.sender,
                    "subject": hit.subject,
                    "matched_terms": "; ".join(hit.matched_terms),
                    "attachment_count": hit.attachment_count,
                    "attachment_names": "; ".join(hit.attachment_names),
                    "message_id": hit.message_id,
                }
            )

    lines = [
        "# Seznam.cz search: pojištění / připojištění / smlouvy",
        "",
        f"Rozsah: {since_year}-{before_year - 1}",
        f"Nalezeno: {len(hits)}",
        "",
    ]
    for index, hit in enumerate(hits, start=1):
        lines.extend(
            [
                f"## {index}. {hit.subject or '(bez predmetu)'}",
                "",
                f"- Slozka: `{hit.folder}`",
                f"- UID: `{hit.uid}`",
                f"- Datum: {hit.date}",
                f"- Od: {hit.sender}",
                f"- Nalezene vyrazy: {', '.join(hit.matched_terms)}",
                f"- Prilohy: {hit.attachment_count} {'; '.join(hit.attachment_names)}",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def main() -> int:
    args = parse_args()
    config = load_config(args.address, args.password_env)
    if args.command == "search":
        hits = search(config, args)
        csv_path, md_path = write_outputs(hits, args.out_dir, args.since_year, args.before_year)
        print(f"Nalezeno: {len(hits)}")
        print(f"CSV: {csv_path}")
        print(f"Markdown: {md_path}")
        return 0
    if args.command == "save-attachments":
        out = save_attachments(config, args)
        print(f"Prilohy ulozeny do: {out}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
