from __future__ import annotations

import argparse
import imaplib
import os
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICLOUD_IMAP_HOST = "imap.mail.me.com"
ICLOUD_IMAP_PORT = 993
DEFAULT_LIMIT = 10


@dataclass(frozen=True)
class MailHeader:
    date: str
    sender: str
    subject: str


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""

    decoded_parts: list[str] = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)

    return " ".join(" ".join(decoded_parts).split())


def _message_to_header(message: Message) -> MailHeader:
    return MailHeader(
        date=_decode_header_value(message.get("Date")),
        sender=_decode_header_value(message.get("From")),
        subject=_decode_header_value(message.get("Subject")),
    )


def _get_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Chybi {name} v lokalnim .env.")
    return value


def list_recent_headers(limit: int) -> list[MailHeader]:
    load_dotenv(PROJECT_ROOT / ".env")

    address = _get_env("ICLOUD_MAIL_ADDRESS")
    app_password = _get_env("ICLOUD_MAIL_APP_PASSWORD")

    with imaplib.IMAP4_SSL(ICLOUD_IMAP_HOST, ICLOUD_IMAP_PORT) as imap:
        imap.login(address, app_password)
        imap.select("INBOX", readonly=True)

        status, data = imap.search(None, "ALL")
        if status != "OK":
            raise SystemExit("Nepodarilo se vyhledat zpravy v INBOXu.")

        message_ids = data[0].split()
        recent_ids = message_ids[-limit:]
        headers: list[MailHeader] = []

        for message_id in reversed(recent_ids):
            status, message_data = imap.fetch(
                message_id,
                "(BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])",
            )
            if status != "OK" or not message_data:
                continue

            raw_header = message_data[0][1]
            if not isinstance(raw_header, bytes):
                continue

            headers.append(_message_to_header(message_from_bytes(raw_header)))

        return headers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only test vypisu poslednich iCloud e-mailu."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Pocet poslednich zprav k vypsani. Vychozi: {DEFAULT_LIMIT}.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    limit = max(1, args.limit)

    for index, header in enumerate(list_recent_headers(limit), start=1):
        print(f"{index}. {header.date}")
        print(f"   Od: {header.sender}")
        print(f"   Predmet: {header.subject or '(bez predmetu)'}")


if __name__ == "__main__":
    main()
