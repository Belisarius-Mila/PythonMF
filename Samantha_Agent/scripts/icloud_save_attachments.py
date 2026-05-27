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

from app.email.config import load_icloud_mail_config

DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "private" / "documents" / "inbox" / "incoming"
FETCH_SPEC = "(RFC822.SIZE BODY.PEEK[])"
MAX_MESSAGE_BYTES = 25_000_000
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class SavedAttachment:
    filename: str
    path: Path
    content_type: str
    size_bytes: int
    part_index: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only iCloud IMAP attachment save by UID into private document inbox."
    )
    parser.add_argument("--uid", required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--confirmed", action="store_true")
    parser.add_argument("--confirmation-text", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    uid = validate_uid(args.uid)
    require_confirmation(uid=uid, confirmed=args.confirmed, text=args.confirmation_text)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_icloud_mail_config()
    with imaplib.IMAP4_SSL(config.host, config.port) as imap:
        imap.login(config.address, config.app_password)
        imap.select("INBOX", readonly=True)
        status, data = imap.uid("FETCH", uid.encode("ascii"), FETCH_SPEC)
        if status != "OK" or not data:
            raise SystemExit("Nepodarilo se nacist zpravu podle UID.")

    raw_message = first_safe_message_payload(data)
    if raw_message is None:
        raise SystemExit("Zprava je prazdna nebo prilis velka.")

    message = message_from_bytes(raw_message)
    saved = save_attachments(message=message, uid=uid, out_dir=out_dir)
    manifest_path = out_dir / f"icloud_uid_{uid}_attachments_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "uid": uid,
                "saved_count": len(saved),
                "attachments": [
                    {
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

    print("iCloud přílohy uložené do soukromého document inboxu:")
    print(f"- UID: {uid}")
    print(f"- Počet uložených příloh: {len(saved)}")
    print(f"- Manifest: {relative_to_project(manifest_path)}")
    for item in saved:
        print(
            f"- {relative_to_project(item.path)} | "
            f"{item.content_type} | {item.size_bytes} B"
        )
    print(
        "Bezpečnost: IMAP byl read-only přes BODY.PEEK; odkazy nebyly otevřeny, "
        "nic nebylo odesláno, smazáno, přesunuto ani označeno jako přečtené."
    )
    return 0


def validate_uid(uid: str) -> str:
    safe_uid = uid.strip()
    if not safe_uid.isdigit():
        raise SystemExit("UID musí být číslo.")
    return safe_uid


def require_confirmation(uid: str, confirmed: bool, text: str) -> None:
    normalized = normalize_text(text)
    if not confirmed:
        raise SystemExit("Chybí --confirmed.")
    required_words = ("stahnout", "priloh", "document vault")
    if uid not in text or not all(word in normalized for word in required_words):
        raise SystemExit(
            "Potvrzení musí obsahovat UID, stažení příloh a document vault."
        )
    forbidden_ok = (
        "neotevirat odkazy" in normalized
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


def save_attachments(message: Message, uid: str, out_dir: Path) -> list[SavedAttachment]:
    saved: list[SavedAttachment] = []
    parts = message.walk() if message.is_multipart() else [message]
    for index, part in enumerate(parts, start=1):
        if part.get_content_maintype() == "multipart":
            continue
        disposition = part.get_content_disposition() or ""
        filename = decode_header_value(part.get_filename()) if part.get_filename() else ""
        if disposition != "attachment" and not filename:
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes) or not payload:
            continue
        final_name = f"icloud_uid_{uid}_{index:02d}_{safe_filename(filename or 'attachment.bin')}"
        path = next_available_path(out_dir / final_name)
        path.write_bytes(payload)
        saved.append(
            SavedAttachment(
                filename=filename or "(bez nazvu)",
                path=path,
                content_type=part.get_content_type(),
                size_bytes=len(payload),
                part_index=index,
            )
        )
    return saved


def decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts: list[str] = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return " ".join(" ".join(parts).split())


def safe_filename(filename: str) -> str:
    path = Path(filename)
    safe_stem = SAFE_FILENAME_PATTERN.sub("-", path.stem).strip("-") or "attachment"
    safe_suffix = SAFE_FILENAME_PATTERN.sub("", path.suffix)[:12] or ".bin"
    return f"{safe_stem[:90]}{safe_suffix}"


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
