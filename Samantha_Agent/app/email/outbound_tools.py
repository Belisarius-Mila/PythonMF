from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import function_tool

from .archive_models import EmailArchiveSource
from .config import EmailConfigError, OutgoingMailConfig, load_smtp_config
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .outbound import (
    DEFAULT_OUTBOX_DRAFT_DIR,
    OutboundEmailError,
    SentCopyResult,
    has_explicit_forward_prepare_confirmation,
    prepare_forward_draft,
    redacted_send_summary,
    save_sent_copy_best_effort,
    send_forward_draft,
    validate_email_address,
)
from .redaction import redact_email_addresses
from .seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider


@function_tool
def prepare_forward_email_by_uid(
    provider: str,
    uid: str,
    recipient_email: str,
    note: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Prepare a local forward draft from one confirmed email UID; does not send."""
    return prepare_forward_email_by_uid_text(
        provider=provider,
        uid=uid,
        recipient_email=recipient_email,
        note=note,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def send_prepared_email_draft(
    draft_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Send a previously prepared local email draft after explicit confirmation."""
    return send_prepared_email_draft_text(
        draft_id=draft_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def prepare_forward_email_by_uid_text(
    provider: str,
    uid: str,
    recipient_email: str,
    note: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    draft_dir: Path = DEFAULT_OUTBOX_DRAFT_DIR,
    provider_factory: Callable[[], object] | None = None,
    smtp_config_loader: Callable[[str], OutgoingMailConfig] = load_smtp_config,
) -> str:
    normalized_provider = provider.strip().casefold()
    if normalized_provider not in {"icloud", "seznam"}:
        return "Neznamy provider. Pouzij `icloud` nebo `seznam`."

    try:
        recipient = validate_email_address(recipient_email)
    except OutboundEmailError as exc:
        return f"Priprava preposlani byla odmitnuta: {exc}"

    if not user_confirmed or not has_explicit_forward_prepare_confirmation(
        uid=uid,
        recipient_email=recipient,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat UID {uid}, prijemce {recipient} a jasny "
            "souhlas s pripravenim preposlani. Bez toho e-mail nectu ani "
            "nevytvarim draft."
        )

    try:
        smtp_config = smtp_config_loader(normalized_provider)
        source = read_archive_source_for_forward(
            provider=normalized_provider,
            uid=uid,
            provider_factory=provider_factory,
        )
        result = prepare_forward_draft(
            source=source,
            smtp_config=smtp_config,
            recipient_email=recipient,
            note=note,
            draft_dir=draft_dir,
        )
    except EmailConfigError as exc:
        return f"Chybi lokalni SMTP/e-mail konfigurace: {exc}"
    except (EmailProviderError, SeznamEmailProviderError, OutboundEmailError) as exc:
        return f"Priprava preposlani selhala: {exc}"

    return (
        "Draft preposlani je pripraveny, ale nebyl odeslan.\n"
        f"- Draft ID: {result.draft_id}\n"
        f"- Zdroj: {result.provider} UID {result.source_uid}\n"
        f"- Komu: {redact_email_addresses(result.recipient)}\n"
        f"- Predmet: {result.subject}\n"
        f"- Lokalni draft: `{result.message_path}`\n"
        "Pro odeslani pouzij samostatne potvrzeni: "
        f"`Potvrzuji, odeslat draft {result.draft_id} na {result.recipient}.`"
    )


def send_prepared_email_draft_text(
    draft_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    draft_dir: Path = DEFAULT_OUTBOX_DRAFT_DIR,
    smtp_config_loader: Callable[[str], OutgoingMailConfig] = load_smtp_config,
    smtp_factory: Callable[..., Any] | None = None,
    sent_copy_saver: Callable[[bytes, OutgoingMailConfig, datetime], SentCopyResult] | None = save_sent_copy_best_effort,
) -> str:
    try:
        result = send_forward_draft(
            draft_id=draft_id,
            user_confirmed=user_confirmed,
            confirmation_text=confirmation_text,
            draft_dir=draft_dir,
            smtp_config_loader=smtp_config_loader,
            smtp_factory=smtp_factory,
            sent_copy_saver=sent_copy_saver,
        )
    except EmailConfigError as exc:
        return f"Chybi lokalni SMTP/e-mail konfigurace: {exc}"
    except OutboundEmailError as exc:
        return f"Odeslani bylo odmitnuto: {exc}"
    except OSError as exc:
        return f"Odeslani selhalo na SMTP spojeni: {exc}"

    return redacted_send_summary(result)


def read_archive_source_for_forward(
    provider: str,
    uid: str,
    provider_factory: Callable[[], object] | None = None,
) -> EmailArchiveSource:
    if provider_factory is None:
        if provider == "icloud":
            provider_factory = ICloudReadOnlyEmailProvider
        elif provider == "seznam":
            provider_factory = SeznamReadOnlyEmailProvider
        else:
            raise OutboundEmailError("Neznamy provider.")

    provider_instance = provider_factory()
    reader = getattr(provider_instance, "read_archive_source_by_uid", None)
    if reader is None:
        raise OutboundEmailError("Provider neumi nacist archivni zdroj pro preposlani.")
    source = reader(uid=uid, max_chars=200_000)
    if not isinstance(source, EmailArchiveSource):
        raise OutboundEmailError("Provider vratil neocekavany typ zpravy.")
    return source
