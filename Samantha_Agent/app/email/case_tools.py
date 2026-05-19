from __future__ import annotations

from collections.abc import Callable

from agents import function_tool

from .case_service import build_email_case_draft, format_email_case_draft
from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailMessage
from .safety import has_explicit_read_confirmation


@function_tool
def build_email_case_from_uid(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 4_000,
) -> str:
    """Build a redacted read-only email case draft from one UID after confirmation."""
    return build_email_case_from_uid_text(
        uid=uid,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        max_chars=max_chars,
    )


def build_email_case_from_uid_text(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 4_000,
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
) -> str:
    """Plain implementation behind the function tool, kept testable without IMAP."""
    if not user_confirmed or not has_explicit_read_confirmation(
        uid=uid,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat UID {uid} a jasny souhlas se ctenim tela "
            "e-mailu pro vytvoreni pracovniho pripadu. Bez toho telo zpravy nectu."
        )

    safe_max_chars = min(max(500, max_chars), 10_000)

    try:
        provider = provider_factory()
        read_message_by_uid = getattr(provider, "read_message_by_uid")
        message = read_message_by_uid(uid=uid, max_chars=safe_max_chars)
        if not isinstance(message, EmailMessage):
            raise EmailProviderError("Provider vratil neocekavany typ zpravy.")
    except EmailConfigError:
        return (
            "Chybi lokalni konfigurace pro iCloud Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except EmailProviderError as exc:
        return f"Vytvoreni e-mailoveho pripadu selhalo: {exc}"

    case = build_email_case_draft(message)
    return format_email_case_draft(case)
