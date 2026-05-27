#!/usr/bin/env python3
from __future__ import annotations

import argparse
import imaplib
import os
import re
import sys
from datetime import datetime
from email.message import Message
from html.parser import HTMLParser
from pathlib import Path

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from scripts.seznam_email_search import (
    attachment_names,
    decode_header_value,
    fetch_message,
    imap_login,
    load_config,
    quote_mailbox,
)

DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "private" / "email_exports" / "seznam"
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    Path("/System/Library/Fonts/Supplemental/Verdana.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exportuje tela Seznam e-mailu podle UID do lokalnich PDF."
    )
    parser.add_argument("--uid", action="append", required=True, help="UID e-mailu v INBOX.")
    parser.add_argument("--address", default=os.getenv("SEZNAM_MAIL_ADDRESS", ""))
    parser.add_argument("--password-env", default="SEZNAM_MAIL_PASSWORD")
    parser.add_argument("--folder", default="INBOX")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-chars", type=int, default=20_000)
    return parser.parse_args()


def register_font() -> tuple[str, str]:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("EmailExportSans", str(candidate)))
            return "EmailExportSans", str(candidate)
    return "Helvetica", "built-in Helvetica"


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned[:90] or "email"


def paragraph_lines(text: str) -> list[str]:
    if not text.strip():
        return ["(E-mail nema textove telo, nebo se nepodarilo extrahovat text.)"]
    lines: list[str] = []
    for line in text.splitlines():
        wrapped = line.strip()
        if wrapped:
            lines.append(wrapped)
    return lines or ["(Prazdne textove telo.)"]


def decode_payload(payload: bytes, charset: str | None) -> str:
    for candidate in (charset, "utf-8", "windows-1250", "iso-8859-2", "latin-1"):
        if not candidate:
            continue
        try:
            return payload.decode(candidate, errors="replace")
        except LookupError:
            continue
    return payload.decode("utf-8", errors="replace")


def extract_body_text(message: Message) -> str:
    plain_parts: list[str] = []
    html_text_parts: list[str] = []
    for part in message.walk() if message.is_multipart() else [message]:
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in {"text/plain", "text/html"}:
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            continue
        text = decode_payload(payload, part.get_content_charset())
        if content_type == "text/plain":
            plain_parts.append(text)
        else:
            html_text_parts.append(html_to_text(text))
    body = "\n\n".join(part.strip() for part in plain_parts if part.strip())
    if not body:
        body = "\n\n".join(part.strip() for part in html_text_parts if part.strip())
    return normalize_body_text(body)


def normalize_body_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


def html_to_text(html: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html)
    return "\n".join(parser.parts)


def build_pdf(path: Path, title: str, meta: list[tuple[str, str]], body: str, font_name: str) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "EmailTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "EmailMeta",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333"),
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "EmailBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=13,
        spaceAfter=5,
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    story = [Paragraph(escape(title), title_style)]
    for key, value in meta:
        story.append(Paragraph(f"<b>{escape(key)}:</b> {escape(value)}", meta_style))
    story.append(Spacer(1, 8))
    for line in paragraph_lines(body):
        story.append(Paragraph(escape(line), body_style))
    doc.build(story)


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = args.out_dir / f"export_{stamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    font_name, font_source = register_font()
    saved: list[Path] = []
    config = load_config(args.address, args.password_env)

    with imap_login(config) as imap:
        status, _data = imap.select(quote_mailbox(args.folder), readonly=True)
        if status != "OK":
            raise SystemExit(f"Nepodarilo se otevrit slozku {args.folder}.")

        for index, uid in enumerate(args.uid, start=1):
            try:
                message = fetch_message(imap, uid)
            except imaplib.IMAP4.error as exc:
                raise SystemExit(f"IMAP server odmitl UID {uid}.") from exc
            subject = decode_header_value(message.get("Subject"))
            sender = decode_header_value(message.get("From"))
            date = decode_header_value(message.get("Date"))
            body_text = extract_body_text(message)
            truncated = len(body_text) > args.max_chars
            if truncated:
                body_text = body_text[: args.max_chars].rstrip()
            attachment_list = ", ".join(attachment_names(message)) or "(zadne)"
            title = subject or f"Seznam UID {uid}"
            filename = f"{index:02d}_seznam_uid_{safe_filename(uid)}_{safe_filename(title)}.pdf"
            path = batch_dir / filename
            meta = [
                ("Zdroj", f"Seznam Mail {args.folder}"),
                ("UID", uid),
                ("Datum", date),
                ("Od", sender),
                ("Predmet", subject),
                ("Prilohy", attachment_list),
                ("Bezpecnost", "Export pres IMAP BODY.PEEK; odkazy nebyly otevirany, zprava nebyla menena."),
            ]
            if truncated:
                meta.append(("Poznamka", f"Telo bylo zkraceno na {args.max_chars} znaku."))
            build_pdf(path=path, title=title, meta=meta, body=body_text, font_name=font_name)
            saved.append(path)

    manifest = batch_dir / "manifest.txt"
    manifest.write_text(
        "\n".join(
            [
                "Seznam email body PDF export",
                f"created_at={stamp}",
                f"font={font_source}",
                "safety=BODY.PEEK read-only; no links opened; no send/delete/move/mark-read",
                "",
                *[str(path) for path in saved],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Ulozeno do: {batch_dir}")
    for path in saved:
        print(path)
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
