from __future__ import annotations

import imaplib
import re
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from html.parser import HTMLParser

from .archive_models import EmailArchiveSource
from .archive_service import email_message_to_archive_source
from .config import SeznamMailConfig, load_seznam_mail_config
from .header_metadata import extract_attachment_metadata_from_bodystructure
from .models import EmailAttachmentMeta, EmailHeader, EmailMessage, EmailMessageBatch, EmailSkippedMessage


HEADER_WITH_STRUCTURE_FETCH_SPEC = "(RFC822.SIZE BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (DATE FROM SUBJECT)])"
MESSAGE_ID_FETCH_SPEC = "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"
MESSAGE_FETCH_SPEC = "(RFC822.SIZE BODY.PEEK[])"
MESSAGE_SIZE_FETCH_SPEC = "(RFC822.SIZE)"
MAX_MESSAGE_BYTES = 2_000_000
MAX_EXPLICIT_MESSAGE_BYTES = 25_000_000
SEZNAM_DEFAULT_FOLDERS = ("INBOX",)
SEZNAM_SPAM_FOLDER_CANDIDATES = ("spam", "Spam", "Junk", "Bulk Mail")
SEZNAM_TRASH_FOLDER_CANDIDATES = ("trash", "Trash", "Kos", "Deleted Messages", "Deleted Items")


class SeznamEmailProviderError(RuntimeError):
    pass


class SeznamReadOnlyEmailProvider:
    def __init__(self, config: SeznamMailConfig | None = None) -> None:
        self._config = config or load_seznam_mail_config()

    def list_recent_headers(self, limit: int = 10, folder: str = "INBOX") -> list[EmailHeader]:
        safe_limit = min(max(1, limit), 200)
        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                _select_readonly_folder(imap, folder)

                status, data = imap.uid("SEARCH", None, "ALL")
                if status != "OK" or not data:
                    raise SeznamEmailProviderError("Nepodarilo se nacist seznam zprav.")

                headers: list[EmailHeader] = []
                for uid in reversed(data[0].split()[-safe_limit:]):
                    header = self._fetch_header(imap, uid, folder=folder)
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
        return self.read_message_by_uid_from_folder(uid=uid, max_chars=max_chars, folder="INBOX")

    def read_message_by_uid_from_folder(
        self,
        uid: str,
        max_chars: int = 4_000,
        folder: str = "INBOX",
    ) -> EmailMessage:
        safe_uid = _validate_uid(uid)
        safe_max_chars = min(max(200, max_chars), 20_000)
        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                _select_readonly_folder(imap, folder)

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
                    source="Seznam",
                    folder=folder,
                    max_message_bytes=MAX_EXPLICIT_MESSAGE_BYTES,
                )
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl pozadavek.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc

    def read_archive_source_by_uid(
        self,
        uid: str,
        max_chars: int = 50_000,
        folder: str = "INBOX",
    ) -> EmailArchiveSource:
        safe_uid = _validate_uid(uid)
        safe_max_chars = min(max(1_000, max_chars), 200_000)
        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                _select_readonly_folder(imap, folder)

                status, message_data = imap.uid(
                    "FETCH",
                    safe_uid.encode("ascii"),
                    MESSAGE_FETCH_SPEC,
                )
                if status != "OK" or not message_data:
                    raise SeznamEmailProviderError("Nepodarilo se nacist zpravu podle UID.")

                return _message_data_to_archive_source(
                    uid=safe_uid,
                    message_data=message_data,
                    max_chars=safe_max_chars,
                    folder=folder,
                    max_message_bytes=MAX_EXPLICIT_MESSAGE_BYTES,
                )
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl pozadavek.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc

    def move_message_to_trash(self, uid: str, folder: str = "INBOX") -> dict[str, str]:
        safe_uid = _validate_uid(uid)
        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                _select_writable_folder(imap, folder)
                message_id = _fetch_message_id(imap, safe_uid.encode("ascii"))
                result = _move_uid_to_trash(
                    imap=imap,
                    uid=safe_uid.encode("ascii"),
                    trash_candidates=SEZNAM_TRASH_FOLDER_CANDIDATES,
                    provider_label="Seznam",
                )
                return {**result, "message_id": message_id}
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl presun do kose.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc

    def permanently_delete_message_from_trash(
        self,
        *,
        trash_uid: str = "",
        message_id: str = "",
        trash_folder: str = "",
    ) -> None:
        folders = _dedupe_keep_order((trash_folder, *SEZNAM_TRASH_FOLDER_CANDIDATES))
        safe_trash_uid = _validate_uid(trash_uid) if trash_uid else ""
        safe_message_id = " ".join(str(message_id).split())
        if not safe_trash_uid and not safe_message_id:
            raise SeznamEmailProviderError("Chybi UID v kosi nebo Message-ID pro trvale smazani.")

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)
                for folder_name in folders:
                    if not folder_name:
                        continue
                    if not _select_writable_folder_optional(imap, folder_name):
                        continue
                    target_uid = safe_trash_uid or _find_uid_by_message_id(imap, safe_message_id)
                    if not target_uid:
                        continue
                    _delete_uid_and_expunge(imap, target_uid.encode("ascii"))
                    return
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl trvale smazani z kose.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc

        raise SeznamEmailProviderError("Zpravu se nepodarilo najit v kosi pro trvale smazani.")

    def _fetch_header(
        self,
        imap: imaplib.IMAP4_SSL,
        uid: bytes,
        folder: str = "INBOX",
    ) -> EmailHeader | None:
        status, message_data = imap.uid("FETCH", uid, HEADER_WITH_STRUCTURE_FETCH_SPEC)
        if status != "OK" or not message_data:
            return None
        raw_header = _first_bytes_payload(message_data)
        if raw_header is None:
            return None
        return _message_to_header(
            internal_id=uid.decode("ascii", errors="replace"),
            message=message_from_bytes(raw_header),
            source="Seznam",
            folder=folder,
            attachments=extract_attachment_metadata_from_bodystructure(message_data),
        )

    def list_recent_messages(
        self,
        days: int = 7,
        limit: int = 50,
        max_chars: int = 3_000,
        folder: str = "INBOX",
    ) -> list[EmailMessage]:
        return list(
            self.list_recent_messages_with_skipped(
                days=days,
                limit=limit,
                max_chars=max_chars,
                folders=(folder,),
            ).messages
        )

    def list_recent_messages_with_skipped(
        self,
        days: int = 7,
        limit: int = 50,
        max_chars: int = 3_000,
        folders: tuple[str, ...] = SEZNAM_DEFAULT_FOLDERS,
        include_spam: bool = False,
    ) -> EmailMessageBatch:
        from datetime import date, timedelta

        safe_days = min(max(1, days), 30)
        safe_limit = min(max(1, limit), 200)
        safe_max_chars = min(max(200, max_chars), 20_000)
        since_date = (date.today() - timedelta(days=safe_days - 1)).strftime("%d-%b-%Y")
        folder_names = _dedupe_keep_order((*folders, *(SEZNAM_SPAM_FOLDER_CANDIDATES if include_spam else ())))
        messages: list[EmailMessage] = []
        skipped: list[EmailSkippedMessage] = []
        unavailable: list[str] = []
        found_spam_folder = False

        try:
            with imaplib.IMAP4_SSL(self._config.host, self._config.port) as imap:
                imap.login(self._config.address, self._config.password)

                for folder_name in folder_names:
                    if not _select_readonly_folder(imap, folder_name, required=False):
                        continue
                    if folder_name in SEZNAM_SPAM_FOLDER_CANDIDATES:
                        found_spam_folder = True
                    status, data = imap.uid("SEARCH", None, "SINCE", since_date)
                    if status != "OK" or not data:
                        continue

                    for uid in reversed(data[0].split()[-safe_limit:]):
                        header = self._fetch_header(imap, uid, folder=folder_name)
                        if header is None:
                            continue
                        size = _fetch_message_size(imap, uid)
                        if size is not None and size > MAX_MESSAGE_BYTES:
                            skipped.append(EmailSkippedMessage(header=header, reason="too_large"))
                            continue
                        status, message_data = imap.uid("FETCH", uid, MESSAGE_FETCH_SPEC)
                        if status != "OK" or not message_data:
                            skipped.append(EmailSkippedMessage(header=header, reason="fetch_failed"))
                            continue
                        try:
                            messages.append(
                                _message_data_to_email_message(
                                    uid=uid.decode("ascii", errors="replace"),
                                    message_data=message_data,
                                    max_chars=safe_max_chars,
                                    source="Seznam",
                                    folder=folder_name,
                                )
                            )
                        except SeznamEmailProviderError:
                            skipped.append(EmailSkippedMessage(header=header, reason="unreadable"))
                            continue

                if include_spam and not found_spam_folder:
                    unavailable.append("Seznam: spam/nevyzadana posta nebyla nalezena mezi znamymi slozkami")
                return EmailMessageBatch(
                    messages=tuple(messages),
                    skipped=tuple(skipped),
                    unavailable=tuple(unavailable),
                )
        except SeznamEmailProviderError:
            raise
        except imaplib.IMAP4.error as exc:
            raise SeznamEmailProviderError("IMAP server Seznam odmitl pozadavek.") from exc
        except OSError as exc:
            raise SeznamEmailProviderError("Nepodarilo se pripojit k Seznam Mailu.") from exc


def _first_bytes_payload(message_data: list[object]) -> bytes | None:
    fallback: bytes | None = None
    for item in message_data:
        if not (isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes)):
            continue
        payload = item[1]
        if fallback is None:
            fallback = payload
        message = message_from_bytes(payload)
        if message.get("Date") or message.get("From") or message.get("Subject"):
            return payload
    return fallback


def _first_safe_message_payload(message_data: list[object], max_bytes: int = MAX_MESSAGE_BYTES) -> bytes | None:
    for item in message_data:
        if not (isinstance(item, tuple) and len(item) >= 2):
            continue

        metadata, payload = item[0], item[1]
        if not isinstance(payload, bytes):
            continue

        if len(payload) > max_bytes:
            return None

        if isinstance(metadata, bytes):
            size_match = re.search(rb"RFC822\.SIZE\s+(\d+)", metadata)
            if size_match and int(size_match.group(1)) > max_bytes:
                return None

        return payload

    return None


def _message_data_to_email_message(
    uid: str,
    message_data: list[object],
    max_chars: int,
    source: str = "Seznam",
    folder: str = "INBOX",
    max_message_bytes: int = MAX_MESSAGE_BYTES,
) -> EmailMessage:
    raw_message = _first_safe_message_payload(message_data, max_bytes=max_message_bytes)
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
            source=source,
            folder=folder,
        ),
        body_text=body_text,
        truncated=truncated,
        attachments=tuple(_extract_attachment_metadata(message)),
    )


def _message_data_to_archive_source(
    uid: str,
    message_data: list[object],
    max_chars: int,
    folder: str = "INBOX",
    max_message_bytes: int = MAX_MESSAGE_BYTES,
) -> EmailArchiveSource:
    raw_message = _first_safe_message_payload(message_data, max_bytes=max_message_bytes)
    if raw_message is None:
        raise SeznamEmailProviderError("Zprava je prazdna nebo prilis velka.")

    message = message_from_bytes(raw_message)
    body_text = _extract_body_text(message)
    if len(body_text) > max_chars:
        body_text = body_text[:max_chars].rstrip()

    email_message = EmailMessage(
        header=_message_to_header(
            internal_id=uid,
            message=message,
            source="Seznam",
            folder=folder,
        ),
        body_text=body_text,
        truncated=False,
        attachments=tuple(_extract_attachment_metadata(message)),
    )
    return email_message_to_archive_source(
        message=email_message,
        body_html="",
        original_eml=raw_message,
        message_id=_decode_header_value(message.get("Message-ID")),
        mailbox=folder,
        provider="seznam",
    )


def _message_to_header(
    internal_id: str,
    message: Message,
    source: str = "",
    folder: str = "",
    attachments: tuple[EmailAttachmentMeta, ...] = (),
) -> EmailHeader:
    return EmailHeader(
        internal_id=internal_id,
        date=_decode_header_value(message.get("Date")),
        sender=_decode_header_value(message.get("From")),
        subject=_decode_header_value(message.get("Subject")),
        source=source,
        folder=folder,
        attachments=attachments,
    )


def _select_readonly_folder(
    imap: imaplib.IMAP4_SSL,
    folder: str,
    required: bool = True,
) -> bool:
    try:
        status, _data = imap.select(folder, readonly=True)
    except imaplib.IMAP4.error:
        if required:
            raise SeznamEmailProviderError(f"Nepodarilo se otevrit slozku {folder}.")
        return False
    if status == "OK":
        return True
    if required:
        raise SeznamEmailProviderError(f"Nepodarilo se otevrit slozku {folder}.")
    return False


def _select_writable_folder(imap: imaplib.IMAP4_SSL, folder: str) -> None:
    try:
        status, _data = imap.select(folder, readonly=False)
    except imaplib.IMAP4.error as exc:
        raise SeznamEmailProviderError(f"Nepodarilo se otevrit slozku {folder} pro zapis.") from exc
    if status != "OK":
        raise SeznamEmailProviderError(f"Nepodarilo se otevrit slozku {folder} pro zapis.")


def _select_writable_folder_optional(imap: imaplib.IMAP4_SSL, folder: str) -> bool:
    try:
        status, _data = imap.select(folder, readonly=False)
    except imaplib.IMAP4.error:
        return False
    return status == "OK"


def _move_uid_to_trash(
    imap: imaplib.IMAP4_SSL,
    uid: bytes,
    trash_candidates: tuple[str, ...],
    provider_label: str,
) -> dict[str, str]:
    for trash_folder in trash_candidates:
        mailbox = _mailbox_command_arg(trash_folder)
        try:
            status, data = imap.uid("MOVE", uid, mailbox)
        except imaplib.IMAP4.error:
            status = "NO"
        if status == "OK":
            return {
                "trash_folder": trash_folder,
                "trash_uid": _copyuid_destination_uid(data, uid),
            }

    for trash_folder in trash_candidates:
        mailbox = _mailbox_command_arg(trash_folder)
        try:
            copy_status, copy_data = imap.uid("COPY", uid, mailbox)
        except imaplib.IMAP4.error:
            continue
        if copy_status != "OK":
            continue
        store_status, _store_data = imap.uid("STORE", uid, "+FLAGS.SILENT", r"(\Deleted)")
        if store_status == "OK":
            return {
                "trash_folder": trash_folder,
                "trash_uid": _copyuid_destination_uid(copy_data, uid),
            }
        raise SeznamEmailProviderError(
            f"{provider_label}: zprava byla zkopirovana do kose, ale nepodarilo se oznacit puvodni zpravu."
        )

    raise SeznamEmailProviderError(f"{provider_label}: nepodarilo se najit nebo pouzit slozku Kos.")


def _fetch_message_id(imap: imaplib.IMAP4_SSL, uid: bytes) -> str:
    status, message_data = imap.uid("FETCH", uid, MESSAGE_ID_FETCH_SPEC)
    if status != "OK" or not message_data:
        return ""
    raw_header = _first_bytes_payload(message_data)
    if raw_header is None:
        return ""
    return _decode_header_value(message_from_bytes(raw_header).get("Message-ID"))


def _copyuid_destination_uid(data: list[object], source_uid: bytes) -> str:
    chunks: list[bytes] = []
    for item in data or []:
        if isinstance(item, bytes):
            chunks.append(item)
        elif isinstance(item, tuple):
            chunks.extend(part for part in item if isinstance(part, bytes))
    text = b" ".join(chunks).decode("ascii", errors="ignore")
    match = re.search(r"COPYUID\s+\d+\s+([0-9:,]+)\s+([0-9:,]+)", text, re.IGNORECASE)
    if not match:
        return ""
    source_set, destination_set = match.groups()
    if source_set != source_uid.decode("ascii", errors="ignore"):
        return ""
    if not re.fullmatch(r"\d+", destination_set):
        return ""
    return destination_set


def _find_uid_by_message_id(imap: imaplib.IMAP4_SSL, message_id: str) -> str:
    if not message_id:
        return ""
    status, data = imap.uid("SEARCH", None, "HEADER", "MESSAGE-ID", _quote_imap_search_value(message_id))
    if status != "OK" or not data or data[0] is None:
        return ""
    uids = data[0].split()
    if len(uids) != 1:
        return ""
    return uids[0].decode("ascii", errors="ignore")


def _delete_uid_and_expunge(imap: imaplib.IMAP4_SSL, uid: bytes) -> None:
    store_status, _store_data = imap.uid("STORE", uid, "+FLAGS.SILENT", r"(\Deleted)")
    if store_status != "OK":
        raise SeznamEmailProviderError("Zpravu v kosi se nepodarilo oznacit ke smazani.")
    try:
        expunge_status, _expunge_data = imap.uid("EXPUNGE", uid)
    except imaplib.IMAP4.error:
        expunge_status, _expunge_data = imap.expunge()
    if expunge_status != "OK":
        raise SeznamEmailProviderError("Zpravu v kosi se nepodarilo fyzicky odstranit.")


def _quote_imap_search_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _mailbox_command_arg(folder: str) -> str:
    if re.search(r"[\s(){}%*\"\\\\]", folder):
        return '"' + folder.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return folder


def _fetch_message_size(imap: imaplib.IMAP4_SSL, uid: bytes) -> int | None:
    status, message_data = imap.uid("FETCH", uid, MESSAGE_SIZE_FETCH_SPEC)
    if status != "OK" or not message_data:
        return None
    for item in message_data:
        metadata = item[0] if isinstance(item, tuple) else item
        if isinstance(metadata, bytes):
            size_match = re.search(rb"RFC822\.SIZE\s+(\d+)", metadata)
            if size_match:
                return int(size_match.group(1))
    return None


def _dedupe_keep_order(items: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        folded = normalized.casefold()
        if not normalized or folded in seen:
            continue
        seen.add(folded)
        result.append(normalized)
    return tuple(result)


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
