from __future__ import annotations

from collections.abc import Callable

from agents import function_tool

from .case_service import format_email_full_links
from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailMessage
from .safety import has_explicit_link_confirmation


@function_tool
def show_email_case_links(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 10_000,
    limit: int = 20,
) -> str:
    """Show full URLs from one email by UID, only after explicit URL confirmation."""
    return show_email_case_links_text(
        uid=uid,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        max_chars=max_chars,
        limit=limit,
    )


def show_email_case_links_text(
    uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_chars: int = 10_000,
    limit: int = 20,
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
) -> str:
    """Plain implementation behind the function tool, kept testable without IMAP."""
    if not user_confirmed or not has_explicit_link_confirmation(
        uid=uid,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat UID {uid}, jasny souhlas a zminku, ze chce "
            "zobrazit plne URL/odkazy z tohoto e-mailu. Bez toho URL nezobrazuji."
        )

    safe_max_chars = min(max(500, max_chars), 20_000)
    safe_limit = min(max(1, limit), 50)

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
        return f"Zobrazeni odkazu z e-mailu selhalo: {exc}"

    return format_email_full_links(message=message, limit=safe_limit)
