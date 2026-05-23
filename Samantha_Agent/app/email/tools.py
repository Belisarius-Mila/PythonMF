from __future__ import annotations

from collections.abc import Callable
from email.utils import parsedate_to_datetime

from agents import function_tool

from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailHeader
from .redaction import redact_email_addresses
from .safety import has_explicit_read_confirmation
from .seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider


@function_tool
def list_recent_email_headers(limit: int = 10) -> str:
    """List recent iCloud Mail headers only: UID, date, sender, and subject."""
    safe_limit = min(max(1, limit), 20)

    try:
        provider = ICloudReadOnlyEmailProvider()
        headers = provider.list_recent_headers(limit=safe_limit)
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError:
        return (
            "Read-only pristup k iCloud Mailu selhal. "
            "Over pripojeni, app-specific password a IMAP pristup."
        )

    if not headers:
        return "V INBOXu nebyly nalezeny zadne e-mailove hlavicky."

    return _format_email_headers(headers)


@function_tool
def search_email_headers(
    query: str = "",
    limit: int = 10,
    scan_limit: int = 200,
) -> str:
    """Search recent iCloud Mail headers only; never reads message bodies."""
    safe_limit = min(max(1, limit), 20)
    safe_scan_limit = min(max(safe_limit, scan_limit), 500)

    try:
        provider = ICloudReadOnlyEmailProvider()
        headers = provider.search_headers(
            query=query,
            limit=safe_limit,
            scan_limit=safe_scan_limit,
        )
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError:
        return (
            "Read-only vyhledani v iCloud Mail hlavickach selhalo. "
            "Over pripojeni, app-specific password a IMAP pristup."
        )

    if not headers:
        return "Nenasel jsem zadne odpovidajici e-mailove hlavicky."

    return _format_email_headers(headers)


def _format_email_headers(headers: list[EmailHeader]) -> str:
    lines: list[str] = []
    for index, header in enumerate(headers, start=1):
        subject = header.subject or "(bez predmetu)"
        lines.extend(
            [
                f"{index}. UID: {header.internal_id}",
                f"   Datum: {header.date}",
                f"   Od: {redact_email_addresses(header.sender)}",
                f"   Predmet: {subject}",
            ]
        )

    return "\n".join(lines)


@function_tool
def list_unified_email_headers(limit_per_source: int = 10) -> str:
    """List recent read-only headers from iCloud and Seznam with explicit source labels."""
    return list_unified_email_headers_text(limit_per_source=limit_per_source)


def list_unified_email_headers_text(
    limit_per_source: int = 10,
    icloud_provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
    seznam_provider_factory: Callable[[], object] = SeznamReadOnlyEmailProvider,
) -> str:
    safe_limit = min(max(1, limit_per_source), 20)
    entries: list[tuple[str, EmailHeader]] = []
    unavailable: list[str] = []

    for source, provider_factory, config_error, provider_error, config_message, error_message in [
        (
            "iCloud",
            icloud_provider_factory,
            EmailConfigError,
            EmailProviderError,
            "chybi lokalni konfigurace pro iCloud Mail",
            "read-only pristup k iCloud Mailu selhal",
        ),
        (
            "Seznam",
            seznam_provider_factory,
            EmailConfigError,
            SeznamEmailProviderError,
            "chybi lokalni konfigurace pro Seznam Mail",
            "read-only pristup k Seznam Mailu selhal",
        ),
    ]:
        try:
            provider = provider_factory()
            headers = provider.list_recent_headers(limit=safe_limit)  # type: ignore[attr-defined]
        except config_error:
            unavailable.append(f"{source}: {config_message}")
            continue
        except provider_error:
            unavailable.append(f"{source}: {error_message}")
            continue

        entries.extend((source, header) for header in headers)

    if entries:
        entries.sort(key=lambda item: _email_header_sort_key(item[1]), reverse=True)
        lines = _format_unified_email_headers(entries)
    else:
        lines = ["Nenasel jsem zadne dostupne e-mailove hlavicky."]

    if unavailable:
        lines.extend(["", "Nedostupne zdroje:"])
        lines.extend(f"- {item}" for item in unavailable)

    lines.extend(
        [
            "",
            "Bezpecnost: jde jen o hlavicky. Pro cteni tela je potreba samostatne "
            "potvrzeni s UID a zdrojem schranky.",
        ]
    )
    return "\n".join(lines)


def _format_unified_email_headers(entries: list[tuple[str, EmailHeader]]) -> list[str]:
    lines: list[str] = []
    for index, (source, header) in enumerate(entries, start=1):
        subject = header.subject or "(bez predmetu)"
        lines.extend(
            [
                f"{index}. Zdroj: {source}",
                f"   UID: {header.internal_id}",
                f"   Datum: {header.date}",
                f"   Od: {redact_email_addresses(header.sender)}",
                f"   Predmet: {subject}",
            ]
        )
    return lines


def _email_header_sort_key(header: EmailHeader) -> float:
    try:
        parsed = parsedate_to_datetime(header.date)
    except (TypeError, ValueError, IndexError):
        return 0.0
    return parsed.timestamp()


@function_tool
def list_recent_seznam_email_headers(limit: int = 10) -> str:
    """List recent Seznam Mail INBOX headers only: UID, date, sender, and subject."""
    safe_limit = min(max(1, limit), 20)

    try:
        provider = SeznamReadOnlyEmailProvider()
        headers = provider.list_recent_headers(limit=safe_limit)
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro Seznam Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except SeznamEmailProviderError:
        return (
            "Read-only pristup k Seznam Mailu selhal. "
            "Over pripojeni, heslo a IMAP pristup."
        )

    if not headers:
        return "V Seznam INBOXu nebyly nalezeny zadne e-mailove hlavicky."

    return _format_email_headers(headers)


@function_tool
def search_seznam_email_headers(
    query: str = "",
    limit: int = 10,
    scan_limit: int = 200,
) -> str:
    """Search recent Seznam Mail INBOX headers only; never reads message bodies."""
    safe_limit = min(max(1, limit), 20)
    safe_scan_limit = min(max(safe_limit, scan_limit), 500)

    try:
        provider = SeznamReadOnlyEmailProvider()
        headers = provider.search_headers(
            query=query,
            limit=safe_limit,
            scan_limit=safe_scan_limit,
        )
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro Seznam Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except SeznamEmailProviderError:
        return (
            "Read-only vyhledani v Seznam Mail hlavickach selhalo. "
            "Over pripojeni, heslo a IMAP pristup."
        )

    if not headers:
        return "Nenasel jsem zadne odpovidajici Seznam e-mailove hlavicky."

    return _format_email_headers(headers)


@function_tool
def read_email_body_by_uid(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 2_000,
) -> str:
    """Read one iCloud Mail message body by UID, only after explicit confirmation."""
    if not user_confirmed or not has_explicit_read_confirmation(
        uid=uid,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat UID {uid} a jasny souhlas se ctenim tela "
            "e-mailu. Bez toho telo zpravy nectu."
        )

    safe_max_chars = min(max(200, max_chars), 5_000)

    try:
        provider = ICloudReadOnlyEmailProvider()
        message = provider.read_message_by_uid(uid=uid, max_chars=safe_max_chars)
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError as exc:
        return f"Read-only nacteni e-mailu podle UID selhalo: {exc}"

    body_text = message.body_text or "(nenalezeno textove telo)"
    body_text = redact_email_addresses(body_text)
    subject = message.header.subject or "(bez predmetu)"

    lines = [
        f"UID: {message.header.internal_id}",
        f"Datum: {message.header.date}",
        f"Od: {redact_email_addresses(message.header.sender)}",
        f"Predmet: {subject}",
        "",
        "Text:",
        body_text,
    ]

    if message.truncated:
        lines.extend(["", "[Zkraceno podle limitu max_chars]"])

    return "\n".join(lines)


@function_tool
def read_seznam_email_body_by_uid(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 2_000,
) -> str:
    """Read one Seznam Mail INBOX message body by UID, only after explicit confirmation."""
    if not user_confirmed or not has_explicit_read_confirmation(
        uid=uid,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat UID {uid} a jasny souhlas se ctenim tela "
            "e-mailu ze Seznamu. Bez toho telo zpravy nectu."
        )

    safe_max_chars = min(max(200, max_chars), 5_000)

    try:
        provider = SeznamReadOnlyEmailProvider()
        message = provider.read_message_by_uid(uid=uid, max_chars=safe_max_chars)
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro Seznam Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except SeznamEmailProviderError as exc:
        return f"Read-only nacteni Seznam e-mailu podle UID selhalo: {exc}"

    body_text = message.body_text or "(nenalezeno textove telo)"
    body_text = redact_email_addresses(body_text)
    subject = message.header.subject or "(bez predmetu)"

    lines = [
        f"UID: {message.header.internal_id}",
        f"Datum: {message.header.date}",
        f"Od: {redact_email_addresses(message.header.sender)}",
        f"Predmet: {subject}",
        "",
        "Text:",
        body_text,
    ]

    if message.attachments:
        lines.extend(["", "Prilohy:"])
        for attachment in message.attachments:
            lines.append(f"- {attachment.filename} ({attachment.content_type})")

    if message.truncated:
        lines.extend(["", "[Zkraceno podle limitu max_chars]"])

    return "\n".join(lines)
