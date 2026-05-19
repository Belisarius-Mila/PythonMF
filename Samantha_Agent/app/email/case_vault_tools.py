from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import function_tool

from .case_vault import (
    DEFAULT_EMAIL_CASES_DIR,
    EmailCaseSaveResult,
    save_email_case_record,
)
from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailMessage
from .redaction import EMAIL_PATTERN, redact_email_addresses
from .triage_service import triage_email_messages, triage_item_to_case_record


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
SAVE_WORDS = (
    "uloz",
    "ulož",
    "ulozit",
    "uložit",
    "ulozenim",
    "uložením",
    "ulozeni",
    "uložení",
    "save",
)
CASE_WORDS = ("case", "pripad", "případ", "vault", "emailcasevault")


@function_tool
def save_selected_email_cases_from_uids(
    uids: list[str],
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars_per_email: int = 3_000,
) -> str:
    """Save selected confirmed email UIDs as safe EmailCaseVault records."""
    return save_selected_email_cases_from_uids_text(
        uids=uids,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        max_chars_per_email=max_chars_per_email,
    )


def save_selected_email_cases_from_uids_text(
    uids: Sequence[str],
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars_per_email: int = 3_000,
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
    vault_directory: Path = DEFAULT_EMAIL_CASES_DIR,
) -> str:
    safe_uids = _normalize_uids(uids)
    safe_max_chars = min(max(500, max_chars_per_email), 10_000)

    if not safe_uids:
        return "Chybi konkretni UID e-mailu k ulozeni jako case."

    if not user_confirmed or not has_explicit_save_cases_confirmation(
        uids=safe_uids,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji jasne potvrzeni od Mily v aktualni zprave. "
            "Potvrzeni musi obsahovat vsechna UID a jasny souhlas s ulozenim "
            "vybranych e-mailu jako case do EmailCaseVault. Bez toho provider "
            "nevolam a nic neukladam."
        )

    try:
        provider = provider_factory()
        read_message_by_uid = getattr(provider, "read_message_by_uid")
        messages = [
            _read_email_message(
                read_message_by_uid=read_message_by_uid,
                uid=uid,
                max_chars=safe_max_chars,
            )
            for uid in safe_uids
        ]
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError as exc:
        return f"Ulozeni email case selhalo: {exc}"

    triage = triage_email_messages(messages)
    items_by_uid = {item.uid: item for item in triage.all_items}
    save_results: list[EmailCaseSaveResult] = []

    try:
        for uid in safe_uids:
            item = items_by_uid.get(uid)
            if item is None:
                raise EmailProviderError(f"Provider nevratil ocekavany UID {uid}.")
            record = triage_item_to_case_record(item)
            record = replace(
                record,
                created_at=datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat(),
            )
            save_results.append(save_email_case_record(record, directory=vault_directory))
    except ValueError as exc:
        return f"Ulozeni email case bylo odmitnuto: {exc}"
    except EmailProviderError as exc:
        return f"Ulozeni email case selhalo: {exc}"

    return _format_save_results(save_results)


def has_explicit_save_cases_confirmation(
    uids: Sequence[str],
    confirmation_text: str,
) -> bool:
    safe_uids = _normalize_uids(uids)
    if not safe_uids:
        return False

    normalized = _normalize_confirmation_text(confirmation_text)
    return (
        all(uid.casefold() in confirmation_text.casefold() for uid in safe_uids)
        and any(word in normalized for word in SAVE_WORDS)
        and any(word in normalized for word in CASE_WORDS)
    )


def _read_email_message(
    read_message_by_uid: Callable[..., Any],
    uid: str,
    max_chars: int,
) -> EmailMessage:
    message = read_message_by_uid(uid=uid, max_chars=max_chars)
    if not isinstance(message, EmailMessage):
        raise EmailProviderError("Provider vratil neocekavany typ zpravy.")
    return message


def _format_save_results(results: Sequence[EmailCaseSaveResult]) -> str:
    lines = ["EmailCaseVault ulozeni vybranych e-mailu:"]
    for result in results:
        status = "ulozeno" if result.created else "uz existuje"
        lines.append(f"- Case ID: {_safe_text(result.case_id)}")
        lines.append(f"  Stav: {status}")
        lines.append(f"  Zprava: {_safe_text(result.message)}")

    created_count = sum(1 for result in results if result.created)
    duplicate_count = len(results) - created_count
    lines.extend(
        [
            "",
            f"Souhrn: ulozeno {created_count}, duplicity {duplicate_count}.",
            "Bezpecnost: e-maily byly nacteny read-only; odkazy nebyly otevreny, "
            "prilohy nebyly stazeny, nic nebylo odeslano, smazano, presunuto ani "
            "oznaceno jako prectene. Do EmailCaseVault se uklada jen bezpecny case "
            "JSON bez celeho tela e-mailu, plnych URL a neredigovanych e-mailovych "
            "adres. Nic nebylo ulozeno do reminders ani memory.",
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
        return "Vystup byl odmitnut, protoze obsahuje citliva data."
    return text


def _normalize_uids(uids: Sequence[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for uid in uids:
        safe_uid = str(uid).strip()
        if not safe_uid or safe_uid in seen:
            continue
        seen.add(safe_uid)
        normalized.append(safe_uid)
    return normalized


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
