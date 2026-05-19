from __future__ import annotations

from agents import function_tool

from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailHeader
from .redaction import redact_email_addresses
from .safety import has_explicit_read_confirmation


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
