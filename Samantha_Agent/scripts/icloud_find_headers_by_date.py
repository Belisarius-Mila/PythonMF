#!/usr/bin/env python3
from __future__ import annotations

import argparse
import imaplib
import re
import sys
from email import message_from_bytes
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.email.config import load_icloud_mail_config
from app.email.icloud_provider import _decode_header_value


HEADER_FETCH_SPEC = "(BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only iCloud header scan across folders for one IMAP date."
    )
    parser.add_argument("--since", required=True, help="IMAP date, e.g. 26-May-2026")
    parser.add_argument("--folder", default="", help="Optional exact folder name")
    parser.add_argument(
        "--match",
        action="append",
        default=[],
        help="Optional case-insensitive term that must appear in date, sender, or subject. Can be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_icloud_mail_config()
    with imaplib.IMAP4_SSL(cfg.host, cfg.port) as imap:
        imap.login(cfg.address, cfg.app_password)
        folders = [args.folder] if args.folder else list_folders(imap)
        print(f"Složky ke kontrole: {len(folders)}")
        terms = tuple(term.casefold() for term in args.match if term.strip())
        for folder in folders:
            scan_folder(imap=imap, folder=folder, since=args.since, terms=terms)
        imap.logout()
    return 0


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


def parse_list_response(line: bytes) -> str | None:
    text = line.decode("utf-8", errors="replace")
    match = re.search(r' "/" "?([^"]+)"?$', text)
    if match:
        return match.group(1)
    match = re.search(r' "/" (.+)$', text)
    if match:
        return match.group(1).strip('"')
    return None


def quote_mailbox(folder: str) -> str:
    escaped = folder.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def scan_folder(
    imap: imaplib.IMAP4_SSL,
    folder: str,
    since: str,
    terms: tuple[str, ...] = (),
) -> None:
    try:
        status, _ = imap.select(quote_mailbox(folder), readonly=True)
        if status != "OK":
            return
        status, data = imap.uid("SEARCH", None, "SINCE", since)
        if status != "OK" or not data or not data[0]:
            return
        uids = data[0].split()
        lines: list[str] = []
        for uid in uids:
            header = fetch_header(imap=imap, uid=uid)
            if not header:
                continue
            if terms and not any(term in header.casefold() for term in terms):
                continue
            lines.append(header)
        if not lines:
            return
        print(f"\nSložka: {folder} | shody od {since}: {len(lines)}")
        for line in lines:
            print(line)
    except imaplib.IMAP4.error:
        return


def fetch_header(imap: imaplib.IMAP4_SSL, uid: bytes) -> str:
    status, data = imap.uid("FETCH", uid, HEADER_FETCH_SPEC)
    if status != "OK" or not data:
        return ""
    payload = next(
        (
            item[1]
            for item in data
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes)
        ),
        None,
    )
    if not payload:
        return ""
    message = message_from_bytes(payload)
    return (
        f"UID {uid.decode('ascii', errors='replace')} | "
        f"{_decode_header_value(message.get('Date'))} | "
        f"{_decode_header_value(message.get('From'))} | "
        f"{_decode_header_value(message.get('Subject'))}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
