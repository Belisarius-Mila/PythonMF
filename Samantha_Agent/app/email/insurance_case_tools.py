from __future__ import annotations

from collections.abc import Callable

from agents import function_tool

from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .insurance_case_service import build_insurance_case, format_insurance_case
from .models import EmailMessage
from .safety import has_explicit_multi_uid_read_confirmation


@function_tool
def build_rixo_insurance_case_from_uids(
    uids: list[str],
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars_per_email: int = 4_000,
) -> str:
    """Build one redacted RIXO Insurance Case from multiple confirmed email UIDs."""
    return build_rixo_insurance_case_from_uids_text(
        uids=uids,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        max_chars_per_email=max_chars_per_email,
    )


def build_rixo_insurance_case_from_uids_text(
    uids: list[str],
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars_per_email: int = 4_000,
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
) -> str:
    """Plain implementation behind the function tool, kept testable without IMAP."""
    normalized_uids = [uid.strip() for uid in uids if uid.strip()]
    if len(normalized_uids) < 2:
        return (
            "RIXO Insurance Case z vice e-mailu vyzaduje alespon dve konkretni UID. "
            "Pro jedno UID pouzij build_email_case_from_uid."
        )

    if len(set(normalized_uids)) != len(normalized_uids):
        return "Seznam UID obsahuje duplicity. Posli kazde UID jen jednou."

    if len(normalized_uids) > 10:
        return "Najednou zpracuji maximalne 10 UID, aby zustal vystup kontrolovatelny."

    if not user_confirmed or not has_explicit_multi_uid_read_confirmation(
        uids=normalized_uids,
        confirmation_text=confirmation_text,
    ):
        joined_uids = ", ".join(normalized_uids)
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            "Potvrzeni musi obsahovat vsechna konkretni UID "
            f"({joined_uids}) a jasny souhlas se ctenim tel techto e-mailu pro "
            "vytvoreni jednoho RIXO Insurance Case. Neurcite 'vezmi predchozi' "
            "nestaci."
        )

    safe_max_chars = min(max(500, max_chars_per_email), 10_000)

    try:
        provider = provider_factory()
        read_message_by_uid = getattr(provider, "read_message_by_uid")
        messages: list[EmailMessage] = []
        for uid in normalized_uids:
            message = read_message_by_uid(uid=uid, max_chars=safe_max_chars)
            if not isinstance(message, EmailMessage):
                raise EmailProviderError("Provider vratil neocekavany typ zpravy.")
            messages.append(message)
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError as exc:
        return f"Vytvoreni RIXO Insurance Case selhalo: {exc}"

    case = build_insurance_case(messages)
    return format_insurance_case(case)
