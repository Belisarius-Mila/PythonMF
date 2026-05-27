from __future__ import annotations

import imaplib
import re
import unicodedata
from datetime import date, timedelta
from html.parser import HTMLParser
from email import message_from_bytes
from email.header import decode_header
from email.message import Message

from .archive_models import EmailArchiveSource
from .archive_service import email_message_to_archive_source
from .config import ICloudMailConfig, load_icloud_mail_config
from .models import EmailAttachmentMeta, EmailHeader, EmailMessage, EmailTextSearchHit


HEADER_FETCH_SPEC = "(BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])"
MESSAGE_FETCH_SPEC = "(RFC822.SIZE BODY.PEEK[])"
MAX_MESSAGE_BYTES = 2_000_000


class EmailProviderError(RuntimeError):
    pass


class ICloudReadOnlyEmailProvider:
    def __init__(self, config: ICloudMailConfig | None = None) -> None:
        self._config = config or load_icloud_mail_config()

    def list_recent_headers(self, limit: int = 10) -> list[EmailHeader]:
        safe_limit = max(1, limit)

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.app_password)
                imap.select("INBOX", readonly=True)

                status, data = imap.uid("SEARCH", None, "ALL")
                if status != "OK" or not data:
                    raise EmailProviderError("Nepodarilo se nacist seznam zprav.")

                uids = data[0].split()
                recent_uids = uids[-safe_limit:]
                headers: list[EmailHeader] = []

                for uid in reversed(recent_uids):
                    header = self._fetch_header(imap, uid)
                    if header is not None:
                        headers.append(header)

                return headers
        except EmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise EmailProviderError("IMAP server odmitl pozadavek.") from exc
        except OSError as exc:
            raise EmailProviderError("Nepodarilo se pripojit k iCloud Mailu.") from exc

    def search_headers(
        self,
        query: str = "",
        limit: int = 10,
        scan_limit: int = 200,
    ) -> list[EmailHeader]:
        safe_limit = max(1, limit)
        normalized_query = " ".join(query.casefold().split())
        if not normalized_query:
            return self.list_recent_headers(limit=safe_limit)

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.app_password)
                imap.select("INBOX", readonly=True)

                uids = _search_header_uids(imap, normalized_query)
                headers = _fetch_headers_for_uids(
                    imap=imap,
                    uids=uids,
                    limit=safe_limit,
                )
        except EmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise EmailProviderError("IMAP server odmitl pozadavek.") from exc
        except OSError as exc:
            raise EmailProviderError("Nepodarilo se pripojit k iCloud Mailu.") from exc

        if not headers:
            safe_scan_limit = max(safe_limit, scan_limit)
            headers = self.list_recent_headers(limit=safe_scan_limit)

        query_terms = normalized_query.split()
        matches: list[EmailHeader] = []
        for header in headers:
            searchable_text = " ".join(
                [
                    header.date,
                    header.sender,
                    header.subject,
                ]
            ).casefold()
            if all(term in searchable_text for term in query_terms):
                matches.append(header)
                if len(matches) >= safe_limit:
                    break

        return matches

    def search_text_headers(
        self,
        terms: list[str] | tuple[str, ...],
        since: date,
        before: date,
        limit: int = 50,
    ) -> list[EmailTextSearchHit]:
        safe_terms = _validate_search_terms(terms)
        safe_limit = min(max(1, limit), 200)
        since_imap = _format_imap_date(since)
        before_imap = _format_imap_date(before)
        term_order = {term.casefold(): index for index, term in enumerate(safe_terms)}

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.app_password)
                imap.select("INBOX", readonly=True)

                uid_matches: dict[bytes, set[str]] = {}
                for term in safe_terms:
                    for uid in _search_text_uids(
                        imap=imap,
                        term=term,
                        since_imap=since_imap,
                        before_imap=before_imap,
                    ):
                        uid_matches.setdefault(uid, set()).add(term)

                recent_uids = sorted(uid_matches, key=lambda uid: int(uid))[-safe_limit:]
                hits: list[EmailTextSearchHit] = []
                for uid in reversed(recent_uids):
                    header = self._fetch_header(imap=imap, uid=uid)
                    if header is None:
                        continue
                    matched_terms = tuple(
                        sorted(
                            uid_matches[uid],
                            key=lambda term: term_order.get(term.casefold(), 999),
                        )
                    )
                    hits.append(
                        EmailTextSearchHit(
                            header=header,
                            matched_terms=matched_terms,
                        )
                    )

                return hits
        except EmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise EmailProviderError("IMAP server odmitl pozadavek.") from exc
        except OSError as exc:
            raise EmailProviderError("Nepodarilo se pripojit k iCloud Mailu.") from exc

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

    def read_message_by_uid(
        self,
        uid: str,
        max_chars: int = 4_000,
    ) -> EmailMessage:
        safe_uid = _validate_uid(uid)
        safe_max_chars = min(max(200, max_chars), 20_000)

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.app_password)
                imap.select("INBOX", readonly=True)

                status, message_data = imap.uid(
                    "FETCH",
                    safe_uid.encode("ascii"),
                    MESSAGE_FETCH_SPEC,
                )
                if status != "OK" or not message_data:
                    raise EmailProviderError("Nepodarilo se nacist zpravu podle UID.")

                return _message_data_to_email_message(
                    uid=safe_uid,
                    message_data=message_data,
                    max_chars=safe_max_chars,
                )
        except EmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise EmailProviderError("IMAP server odmitl pozadavek.") from exc
        except OSError as exc:
            raise EmailProviderError("Nepodarilo se pripojit k iCloud Mailu.") from exc

    def read_archive_source_by_uid(
        self,
        uid: str,
        max_chars: int = 50_000,
    ) -> EmailArchiveSource:
        safe_uid = _validate_uid(uid)
        safe_max_chars = min(max(1_000, max_chars), 200_000)

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.app_password)
                imap.select("INBOX", readonly=True)

                status, message_data = imap.uid(
                    "FETCH",
                    safe_uid.encode("ascii"),
                    MESSAGE_FETCH_SPEC,
                )
                if status != "OK" or not message_data:
                    raise EmailProviderError("Nepodarilo se nacist zpravu podle UID.")

                return _message_data_to_archive_source(
                    uid=safe_uid,
                    message_data=message_data,
                    max_chars=safe_max_chars,
                )
        except EmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise EmailProviderError("IMAP server odmitl pozadavek.") from exc
        except OSError as exc:
            raise EmailProviderError("Nepodarilo se pripojit k iCloud Mailu.") from exc

    def list_recent_messages(
        self,
        days: int = 7,
        limit: int = 50,
        max_chars: int = 3_000,
    ) -> list[EmailMessage]:
        safe_days = min(max(1, days), 30)
        safe_limit = min(max(1, limit), 200)
        safe_max_chars = min(max(200, max_chars), 20_000)
        since_date = (date.today() - timedelta(days=safe_days - 1)).strftime("%d-%b-%Y")

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.app_password)
                imap.select("INBOX", readonly=True)

                status, data = imap.uid("SEARCH", None, "SINCE", since_date)
                if status != "OK" or not data:
                    raise EmailProviderError("Nepodarilo se nacist seznam zprav.")

                uids = data[0].split()
                recent_uids = uids[-safe_limit:]
                messages: list[EmailMessage] = []

                for uid in reversed(recent_uids):
                    status, message_data = imap.uid("FETCH", uid, MESSAGE_FETCH_SPEC)
                    if status != "OK" or not message_data:
                        continue
                    messages.append(
                        _message_data_to_email_message(
                            uid=uid.decode("ascii", errors="replace"),
                            message_data=message_data,
                            max_chars=safe_max_chars,
                        )
                    )

                return messages
        except EmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise EmailProviderError("IMAP server odmitl pozadavek.") from exc
        except OSError as exc:
            raise EmailProviderError("Nepodarilo se pripojit k iCloud Mailu.") from exc


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
        raise EmailProviderError("Zprava je prazdna nebo prilis velka.")

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


def _message_data_to_archive_source(
    uid: str,
    message_data: list[object],
    max_chars: int,
) -> EmailArchiveSource:
    raw_message = _first_safe_message_payload(message_data)
    if raw_message is None:
        raise EmailProviderError("Zprava je prazdna nebo prilis velka.")

    message = message_from_bytes(raw_message)
    body_text, body_html = _extract_body_text_and_html(message)
    if len(body_text) > max_chars:
        body_text = body_text[:max_chars].rstrip()
    if len(body_html) > max_chars:
        body_html = body_html[:max_chars].rstrip()

    email_message = EmailMessage(
        header=_message_to_header(
            internal_id=uid,
            message=message,
        ),
        body_text=body_text,
        truncated=False,
        attachments=tuple(_extract_attachment_metadata(message)),
    )
    return email_message_to_archive_source(
        message=email_message,
        body_html=body_html,
        original_eml=raw_message,
        message_id=_decode_header_value(message.get("Message-ID")),
        mailbox="INBOX",
        provider="icloud",
    )


def _search_header_uids(imap: imaplib.IMAP4_SSL, query: str) -> list[bytes]:
    status, data = imap.uid(
        "SEARCH",
        None,
        "OR",
        "HEADER",
        "FROM",
        query,
        "HEADER",
        "SUBJECT",
        query,
    )
    if status != "OK" or not data:
        raise EmailProviderError("Nepodarilo se vyhledat hlavicky.")
    if data[0] is None:
        return []

    return data[0].split()


def _search_text_uids(
    imap: imaplib.IMAP4_SSL,
    term: str,
    since_imap: str,
    before_imap: str,
) -> list[bytes]:
    status, data = imap.uid(
        "SEARCH",
        "CHARSET",
        "UTF-8",
        "SINCE",
        since_imap,
        "BEFORE",
        before_imap,
        "TEXT",
        _quote_imap_utf8(term),
    )
    if status != "OK" or not data:
        raise EmailProviderError("Nepodarilo se fulltextove vyhledat zpravy.")
    if data[0] is None:
        return []

    return data[0].split()


def _quote_imap_utf8(value: str) -> bytes:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'.encode("utf-8")


def _validate_search_terms(terms: list[str] | tuple[str, ...]) -> list[str]:
    safe_terms: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = " ".join(str(term).split())
        folded = normalized.casefold()
        if not normalized or folded in seen:
            continue
        if len(normalized) > 80:
            raise EmailProviderError("Hledany vyraz je prilis dlouhy.")
        safe_terms.append(normalized)
        seen.add(folded)

    if not safe_terms:
        raise EmailProviderError("Chybi hledany vyraz.")
    if len(safe_terms) > 10:
        raise EmailProviderError("Prilis mnoho hledanych vyrazu.")
    return safe_terms


def _format_imap_date(value: date) -> str:
    return value.strftime("%d-%b-%Y")


def _fetch_headers_for_uids(
    imap: imaplib.IMAP4_SSL,
    uids: list[bytes],
    limit: int,
) -> list[EmailHeader]:
    headers: list[EmailHeader] = []
    sorted_uids = sorted(uids, key=lambda uid: int(uid))
    recent_uids = sorted_uids[-limit:]

    for uid in reversed(recent_uids):
        status, message_data = imap.uid("FETCH", uid, HEADER_FETCH_SPEC)
        if status != "OK" or not message_data:
            continue

        raw_header = _first_bytes_payload(message_data)
        if raw_header is None:
            continue

        headers.append(
            _message_to_header(
                internal_id=uid.decode("ascii", errors="replace"),
                message=message_from_bytes(raw_header),
            )
        )

    return headers


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""

    decoded_parts: list[str] = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded_parts.append(_decode_header_bytes(part, encoding))
        else:
            decoded_parts.append(part)

    return " ".join(" ".join(decoded_parts).split())


def _decode_header_bytes(part: bytes, encoding: str | None) -> str:
    for candidate in (encoding, "utf-8", "latin-1"):
        if not candidate:
            continue
        try:
            return part.decode(candidate, errors="replace")
        except LookupError:
            continue
    return part.decode("utf-8", errors="replace")


def _message_to_header(internal_id: str, message: Message) -> EmailHeader:
    return EmailHeader(
        internal_id=internal_id,
        date=_decode_header_value(message.get("Date")),
        sender=_decode_header_value(message.get("From")),
        subject=_decode_header_value(message.get("Subject")),
    )


def _validate_uid(uid: str) -> str:
    safe_uid = uid.strip()
    if not safe_uid.isdigit():
        raise EmailProviderError("UID musi byt cislo.")
    return safe_uid


def _extract_body_text(message: Message) -> str:
    body_text, _body_html = _extract_body_text_and_html(message)
    return body_text


def _extract_body_text_and_html(message: Message) -> tuple[str, str]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    html_text_parts: list[str] = []

    for part in message.walk() if message.is_multipart() else [message]:
        if part.get_content_maintype() == "multipart":
            continue

        content_disposition = part.get_content_disposition()
        if content_disposition == "attachment":
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
            html_parts.append(text)
            html_text_parts.append(_html_to_text(text))

    body = "\n\n".join(part.strip() for part in plain_parts if part.strip())
    if not body:
        body = "\n\n".join(part.strip() for part in html_text_parts if part.strip())
    html_body = "\n\n".join(part.strip() for part in html_parts if part.strip())

    return _normalize_body_text(body), html_body.strip()




def _extract_attachment_metadata(message: Message) -> list[EmailAttachmentMeta]:
    attachments: list[EmailAttachmentMeta] = []

    for index, part in enumerate(message.walk() if message.is_multipart() else [message]):
        if part.get_content_maintype() == "multipart":
            continue

        disposition = part.get_content_disposition() or ""
        filename = _decode_header_value(part.get_filename()) if part.get_filename() else ""
        content_id = _decode_header_value(part.get("Content-ID"))
        content_type = part.get_content_type()

        if disposition != "attachment" and not filename:
            continue

        size_bytes: int | None = None
        payload = part.get_payload(decode=True)
        if isinstance(payload, bytes):
            size_bytes = len(payload)

        attachments.append(
            EmailAttachmentMeta(
                filename=filename or "(bez nazvu)",
                content_type=content_type,
                size_bytes=size_bytes,
                part_id=str(index),
                content_id=content_id,
                disposition=disposition or "inline",
            )
        )

    return attachments


def _normalize_body_text(text: str) -> str:
    cleaned_text = _remove_invisible_characters(text)
    lines = [" ".join(line.split()) for line in cleaned_text.splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines).strip()


def _remove_invisible_characters(text: str) -> str:
    email_filler_chars = {
        "\u034f",
        "\u061c",
        "\u200b",
        "\u200c",
        "\u200d",
        "\u200e",
        "\u200f",
        "\u2060",
        "\ufeff",
    }
    kept_chars: list[str] = []
    for char in text:
        if char in {"\n", "\t"}:
            kept_chars.append(char)
            continue

        if char in email_filler_chars:
            continue

        category = unicodedata.category(char)
        if category.startswith("C"):
            continue

        kept_chars.append(char)

    return "".join(kept_chars)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in {"head", "style", "script", "noscript"}:
            self._ignored_tag_depth += 1
            return

        if normalized_tag == "a" and self._ignored_tag_depth == 0:
            href = _find_attr(attrs, "href")
            if href and href.casefold().startswith(("http://", "https://")):
                self._parts.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"head", "style", "script", "noscript"}:
            self._ignored_tag_depth = max(0, self._ignored_tag_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._ignored_tag_depth == 0 and data.strip():
            self._parts.append(data)

    def text(self) -> str:
        return " ".join(self._parts)


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.text()


def _find_attr(attrs: list[tuple[str, str | None]], name: str) -> str | None:
    normalized_name = name.casefold()
    for attr_name, attr_value in attrs:
        if attr_name.casefold() == normalized_name:
            return attr_value
    return None
