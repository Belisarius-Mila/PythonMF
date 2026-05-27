#!/usr/bin/env python3
from __future__ import annotations

import argparse
import imaplib
import json
import re
import sys
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.email.config import load_seznam_mail_config


DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "private" / "documents" / "inbox" / "incoming"
FETCH_SPEC = "(RFC822.SIZE BODY.PEEK[])"
MAX_MESSAGE_BYTES = 25_000_000
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
GREEN_CARD_HINTS = ("zelen", "karta", "green", "card", "3270612451")


@dataclass(frozen=True)
class SavedCandidate:
    source: str
    filename: str
    path: Path
    content_type: str
    size_bytes: int
    part_index: int | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Seznam IMAP save of green-card candidates from one UID."
    )
    parser.add_argument("--uid", required=True)
    parser.add_argument("--folder", default="INBOX")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--confirmed", action="store_true")
    parser.add_argument("--confirmation-text", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    uid = validate_uid(args.uid)
    require_confirmation(uid=uid, confirmed=args.confirmed, text=args.confirmation_text)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_message = fetch_raw_message(uid=uid, folder=args.folder)
    message = message_from_bytes(raw_message)
    saved = save_green_card_candidates(message=message, uid=uid, out_dir=args.out_dir)

    manifest_path = args.out_dir / f"seznam_uid_{uid}_green_card_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "uid": uid,
                "folder": args.folder,
                "saved_count": len(saved),
                "candidates": [
                    {
                        "source": item.source,
                        "filename": item.filename,
                        "path": str(item.path),
                        "content_type": item.content_type,
                        "size_bytes": item.size_bytes,
                        "part_index": item.part_index,
                    }
                    for item in saved
                ],
                "safety": {
                    "provider_read_only": True,
                    "used_body_peek": True,
                    "links_opened": False,
                    "message_sent": False,
                    "message_deleted": False,
                    "message_moved": False,
                    "marked_read": False,
                    "local_private_data": True,
                    "do_not_commit": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Seznam zelená karta - kandidáti uložení do soukromého document inboxu:")
    print(f"- UID: {uid}")
    print(f"- Počet uložených kandidátů: {len(saved)}")
    print(f"- Manifest: {relative_to_project(manifest_path)}")
    for item in saved:
        print(
            f"- {relative_to_project(item.path)} | "
            f"{item.content_type} | {item.size_bytes} B | {item.source}"
        )
    print(
        "Bezpečnost: IMAP byl read-only přes BODY.PEEK; odkazy nebyly otevřeny, "
        "nic nebylo odesláno, smazáno, přesunuto ani označeno jako přečtené."
    )
    return 0


def fetch_raw_message(uid: str, folder: str) -> bytes:
    cfg = load_seznam_mail_config()
    with imaplib.IMAP4_SSL(cfg.host, cfg.port) as imap:
        imap.login(cfg.address, cfg.password)
        status, _ = imap.select(quote_mailbox(folder), readonly=True)
        if status != "OK":
            raise SystemExit(f"Nepodařilo se otevřít složku {folder}.")
        status, data = imap.uid("FETCH", uid.encode("ascii"), FETCH_SPEC)
        if status != "OK" or not data:
            raise SystemExit("Nepodařilo se načíst zprávu podle UID.")
    raw = first_safe_message_payload(data)
    if raw is None:
        raise SystemExit("Zpráva je prázdná nebo příliš velká.")
    return raw


def save_green_card_candidates(message: Message, uid: str, out_dir: Path) -> list[SavedCandidate]:
    saved: list[SavedCandidate] = []
    parts = message.walk() if message.is_multipart() else [message]
    for index, part in enumerate(parts, start=1):
        if part.get_content_maintype() == "multipart":
            continue
        content_type = part.get_content_type()
        disposition = part.get_content_disposition() or ""
        filename = decode_header_value(part.get_filename()) if part.get_filename() else ""
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes) or not payload:
            continue

        filename_hint = " ".join((filename, content_type, disposition)).casefold()
        is_document_part = bool(filename) or disposition in {"attachment", "inline"}
        is_green_hint = any(hint in filename_hint for hint in GREEN_CARD_HINTS)
        is_candidate_type = content_type == "application/pdf" or content_type.startswith("image/")

        if is_document_part and (is_green_hint or is_candidate_type):
            final_name = f"seznam_uid_{uid}_{index:02d}_{safe_filename(filename or content_type_to_filename(content_type))}"
            path = next_available_path(out_dir / final_name)
            path.write_bytes(payload)
            saved.append(
                SavedCandidate(
                    source="mime-part",
                    filename=filename or "(bez nazvu)",
                    path=path,
                    content_type=content_type,
                    size_bytes=len(payload),
                    part_index=index,
                )
            )

    if saved:
        return saved

    body_html, body_text = extract_body(message)
    if body_html.strip():
        path = next_available_path(out_dir / f"seznam_uid_{uid}_zelena_karta_body.html")
        payload = body_html.encode("utf-8")
        path.write_bytes(payload)
        saved.append(
            SavedCandidate(
                source="html-body",
                filename=path.name,
                path=path,
                content_type="text/html",
                size_bytes=len(payload),
            )
        )
    if body_text.strip():
        path = next_available_path(out_dir / f"seznam_uid_{uid}_zelena_karta_body.txt")
        payload = body_text.encode("utf-8")
        path.write_bytes(payload)
        saved.append(
            SavedCandidate(
                source="text-body",
                filename=path.name,
                path=path,
                content_type="text/plain",
                size_bytes=len(payload),
            )
        )
    return saved


def extract_body(message: Message) -> tuple[str, str]:
    html_parts: list[str] = []
    text_parts: list[str] = []
    for part in message.walk() if message.is_multipart() else [message]:
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in {"text/html", "text/plain"}:
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            continue
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        if content_type == "text/html":
            html_parts.append(text)
        else:
            text_parts.append(text)
    return "\n\n".join(html_parts), "\n\n".join(text_parts)


def validate_uid(uid: str) -> str:
    safe_uid = uid.strip()
    if not safe_uid.isdigit():
        raise SystemExit("UID musí být číslo.")
    return safe_uid


def require_confirmation(uid: str, confirmed: bool, text: str) -> None:
    normalized = normalize_text(text)
    if not confirmed:
        raise SystemExit("Chybí --confirmed.")
    required_words = ("seznam", "precist", "zelenou kartu", "document vault")
    if uid not in text or not all(word in normalized for word in required_words):
        raise SystemExit(
            "Potvrzení musí obsahovat Seznam UID, přečtení, zelenou kartu a document vault."
        )
    forbidden_ok = (
        "neotevirat" in normalized
        and "nic neposilat" in normalized
        and "nemazat" in normalized
        and "nepresouvat" in normalized
        and "neoznacovat" in normalized
    )
    if not forbidden_ok:
        raise SystemExit("Potvrzení musí obsahovat bezpečnostní zákazy.")


def normalize_text(text: str) -> str:
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
    return " ".join(text.casefold().translate(replacements).split())


def first_safe_message_payload(message_data: list[object]) -> bytes | None:
    for item in message_data:
        if not (isinstance(item, tuple) and len(item) >= 2):
            continue
        metadata, payload = item[0], item[1]
        if not isinstance(payload, bytes):
            continue
        if len(payload) > MAX_MESSAGE_BYTES:
            return None
        if isinstance(metadata, bytes):
            size_match = re.search(rb"RFC822\.SIZE\s+(\d+)", metadata)
            if size_match and int(size_match.group(1)) > MAX_MESSAGE_BYTES:
                return None
        return payload
    return None


def quote_mailbox(folder: str) -> str:
    escaped = folder.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


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


def safe_filename(filename: str) -> str:
    path = Path(filename)
    safe_stem = SAFE_FILENAME_PATTERN.sub("-", path.stem).strip("-") or "document"
    safe_suffix = SAFE_FILENAME_PATTERN.sub("", path.suffix)[:12] or ".bin"
    return f"{safe_stem[:90]}{safe_suffix}"


def content_type_to_filename(content_type: str) -> str:
    if content_type == "application/pdf":
        return "zelena-karta.pdf"
    if content_type == "image/png":
        return "zelena-karta.png"
    if content_type in {"image/jpeg", "image/jpg"}:
        return "zelena-karta.jpg"
    return "zelena-karta.bin"


def next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return path


if __name__ == "__main__":
    raise SystemExit(main())
