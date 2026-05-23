from __future__ import annotations

import imaplib
import re
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from html.parser import HTMLParser

from .config import SeznamMailConfig, load_seznam_mail_config
from .models import EmailAttachmentMeta, EmailHeader, EmailMessage


HEADER_FETCH_SPEC = "(BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])"
MESSAGE_FETCH_SPEC = "(RFC822.SIZE BODY.PEEK[])"
MAX_MESSAGE_BYTES = 2_000_000


class SeznamEmailProviderError(RuntimeError):
    pass


class SeznamReadOnlyEmailProvider:
    def __init__(self, config: SeznamMailConfig | None = None) -> None:
        self._config = config or load_seznam_mail_config()

    def list_recent_headers(self, limit: int = 10) -> list[EmailHeader]:
        safe_limit = min(max(1, limit), 200)
        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                imap.select("INBOX", readonly=True)

                status, data = imap.uid("SEARCH", None, "ALL")
                if status != "OK" or not data:
                    raise SeznamEmailProviderError("Nepodarilo se nacist seznam zprav.")

                headers: list[EmailHeader] = []
                for uid in reversed(data[0].split()[-safe_limit:]):
                    header = self._fetch_header(imap, uid)
                    if header is not None:
                        headers.append(header)
                return headers
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl pozadavek.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc

    def search_headers(
        self,
        query: str = "",
        limit: int = 10,
        scan_limit: int = 200,
    ) -> list[EmailHeader]:
        safe_limit = min(max(1, limit), 200)
        normalized_query = " ".join(query.casefold().split())
        if not normalized_query:
            return self.list_recent_headers(limit=safe_limit)

        headers = self.list_recent_headers(limit=max(safe_limit, scan_limit))
        terms = normalized_query.split()
        matches: list[EmailHeader] = []
        for header in headers:
            searchable = " ".join((header.date, header.sender, header.subject)).casefold()
            if all(term in searchable for term in terms):
                matches.append(header)
                if len(matches) >= safe_limit:
                    break
        return matches

    def read_message_by_uid(self, uid: str, max_chars: int = 4_000) -> EmailMessage:
        safe_uid = _validate_uid(uid)
        safe_max_chars = min(max(200, max_chars), 20_000)
        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                imap.select("INBOX", readonly=True)

                status, message_data = imap.uid(
                    "FETCH",
                    safe_uid.encode("ascii"),
                    MESSAGE_FETCH_SPEC,
                )
                if status != "OK" or not message_data:
                    raise SeznamEmailProviderError("Nepodarilo se nacist zpravu podle UID.")

                return _message_data_to_email_message(
                    uid=safe_uid,
                    message_data=message_data,
                    max_chars=safe_max_chars,
                )
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl pozadavek.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc

    def _fetch_header(
        self,
        imap: imaplib.IMAP4_SSL,
        uid: bytes,
    ) -> EmailHeader | None:
        status, message_data = imap.uid("FETCH", uid, HEADER_FETCH_SPEC)
        if status != "OK" or not message_data:
            return None
        raw_header = _first_bytes_payload(message_data)
        if raw_header is None:
            return None
        return _message_to_header(
            internal_id=uid.decode("ascii", errors="replace"),
            message=message_from_bytes(raw_header),
        )


def _first_bytes_payload(message_data: list[object]) -> bytes | None:
    for item in message_data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return None


def _first_safe_message_payload(message_data: list[object]) -> bytes | None:
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


def _message_data_to_email_message(
    uid: str,
    message_data: list[object],
    max_chars: int,
) -> EmailMessage:
    raw_message = _first_safe_message_payload(message_data)
    if raw_message is None:
        raise SeznamEmailProviderError("Zprava je prazdna nebo prilis velka.")

    message = message_from_bytes(raw_message)
    body_text = _extract_body_text(message)
    truncated = len(body_text) > max_chars
    if truncated:
        body_text = body_text[:max_chars].rstrip()

    return EmailMessage(
        header=_message_to_header(
            internal_id=uid,
            message=message,
        ),
        body_text=body_text,
        truncated=truncated,
        attachments=tuple(_extract_attachment_metadata(message)),
    )


def _message_to_header(internal_id: str, message: Message) -> EmailHeader:
    return EmailHeader(
        internal_id=internal_id,
        date=_decode_header_value(message.get("Date")),
        sender=_decode_header_value(message.get("From")),
        subject=_decode_header_value(message.get("Subject")),
    )


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


def _validate_uid(uid: str) -> str:
    safe_uid = uid.strip()
    if not safe_uid.isdigit():
        raise SeznamEmailProviderError("UID musi byt cislo.")
    return safe_uid


def _extract_body_text(message: Message) -> str:
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

        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        if content_type == "text/plain":
            plain_parts.append(text)
        else:
            html_text_parts.append(_html_to_text(text))

    body = "\n\n".join(part.strip() for part in plain_parts if part.strip())
    if not body:
        body = "\n\n".join(part.strip() for part in html_text_parts if part.strip())
    return _normalize_body_text(body)


def _extract_attachment_metadata(message: Message) -> list[EmailAttachmentMeta]:
    attachments: list[EmailAttachmentMeta] = []
    for index, part in enumerate(message.walk() if message.is_multipart() else [message]):
        if part.get_content_maintype() == "multipart":
            continue

        disposition = part.get_content_disposition() or ""
        filename = _decode_header_value(part.get_filename()) if part.get_filename() else ""
        if disposition != "attachment" and not filename:
            continue

        size_bytes: int | None = None
        payload = part.get_payload(decode=True)
        if isinstance(payload, bytes):
            size_bytes = len(payload)

        attachments.append(
            EmailAttachmentMeta(
                filename=filename or "(bez nazvu)",
                content_type=part.get_content_type(),
                size_bytes=size_bytes,
                part_id=str(index),
                content_id=_decode_header_value(part.get("Content-ID")),
                disposition=disposition or "inline",
            )
        )
    return attachments


def _normalize_body_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return "\n".join(parser.parts)
