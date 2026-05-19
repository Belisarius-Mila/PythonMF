from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agents import function_tool

from .activity_state import (
    DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
    record_email_archive_completed,
)
from .archive_models import EmailArchiveSource
from .archive_service import DEFAULT_EMAIL_ARCHIVE_DIR, save_email_archive
from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .redaction import EMAIL_PATTERN, redact_email_addresses


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
ARCHIVE_WORDS = (
    "archivovat",
    "archivaci",
    "archivací",
    "archivace",
    "archivu",
    "emailarchivevault",
    "archive",
)
COMPLETE_WORDS = (
    "kompletni",
    "kompletní",
    "celeho",
    "celého",
    "celou",
    "uplnou",
    "úplnou",
    "zalohu",
    "zálohu",
)


@function_tool
def archive_email_by_uid(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 50_000,
) -> str:
    """Archive one confirmed iCloud Mail message into EmailArchiveVault."""
    return archive_email_by_uid_text(
        uid=uid,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        max_chars=max_chars,
    )


def archive_email_by_uid_text(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 50_000,
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
    archive_directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
    activity_state_path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
) -> str:
    safe_uid = uid.strip()
    safe_max_chars = min(max(1_000, max_chars), 200_000)

    if not user_confirmed or not has_explicit_archive_confirmation(
        uid=safe_uid,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji jasne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat UID {safe_uid} a jasny souhlas s kompletni "
            "archivaci e-mailu do EmailArchiveVault. Bez toho provider nevolam "
            "a nic neukladam."
        )

    try:
        provider = provider_factory()
        read_archive_source_by_uid = getattr(provider, "read_archive_source_by_uid")
        source = read_archive_source_by_uid(uid=safe_uid, max_chars=safe_max_chars)
        if not isinstance(source, EmailArchiveSource):
            raise EmailProviderError("Provider vratil neocekavany typ archivni zpravy.")
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError as exc:
        return f"Archivace e-mailu selhala: {exc}"

    result = save_email_archive(source, directory=archive_directory)
    if result.created:
        record_email_archive_completed(path=activity_state_path)

    return _format_archive_result(result)


def has_explicit_archive_confirmation(uid: str, confirmation_text: str) -> bool:
    safe_uid = uid.strip()
    if not safe_uid:
        return False

    normalized = _normalize_confirmation_text(confirmation_text)
    return (
        safe_uid.casefold() in confirmation_text.casefold()
        and any(word in normalized for word in ARCHIVE_WORDS)
        and any(word in normalized for word in COMPLETE_WORDS)
    )


def _format_archive_result(result: Any) -> str:
    status = "ulozeno" if result.created else "uz existuje"
    lines = [
        "EmailArchiveVault archivace:",
        f"- Archive ID: {_safe_text(result.archive_id)}",
        f"- Stav: {status}",
        "- Ulozene soubory:",
    ]
    files = tuple(result.files)
    if files:
        lines.extend(f"  - {_safe_text(path)}" for path in files)
    else:
        lines.append("  - Nenalezeny")
    lines.extend(
        [
            "- Archiv je lokalni citlivy archiv a nesmi se commitovat do gitu.",
            "- Vystup zamerne nezobrazuje telo e-mailu, plne URL ani e-mailove adresy.",
            "- Plne URL z archivu maji byt zobrazeny az samostatnym potvrzenym workflow.",
            "Bezpecnost: provider byl pouzit read-only; odkazy nebyly otevreny, "
            "prilohy nebyly spusteny ani samostatne ulozeny, nic nebylo odeslano, "
            "smazano, presunuto ani oznaceno jako prectene. Nic nebylo ulozeno "
            "do memory ani reminders.",
        ]
    )
    return _sanitize_output("\n".join(lines))


def _safe_text(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    return " ".join(text.split())


def _sanitize_output(text: str) -> str:
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    if URL_PATTERN.search(text) or EMAIL_PATTERN.search(text):
        return "Archivacni vystup byl odmitnut, protoze obsahuje citliva data."
    return text


def _normalize_confirmation_text(text: str) -> str:
    normalized = _strip_accents(text.casefold())
    return " ".join(normalized.split())


def _strip_accents(text: str) -> str:
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
    return text.translate(replacements)
