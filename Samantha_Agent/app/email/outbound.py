from __future__ import annotations

import json
import re
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage as StdEmailMessage
from email import message_from_bytes
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Callable

from .archive_models import EmailArchiveSource
from .config import OutgoingMailConfig, load_smtp_config
from .redaction import redact_email_addresses


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTBOX_DRAFT_DIR = PROJECT_ROOT / "data" / "email" / "outbox_drafts"
SAFE_ID_PATTERN = re.compile(r"[^a-z0-9_.-]+")
FORWARD_WORDS = ("prepos", "přepoš", "přepos", "forward")
SEND_WORDS = ("odesli", "odešli", "odeslat", "pošli", "posli", "send")
CONFIRM_WORDS = ("potvrzuji", "souhlasim", "souhlasím", "ano")


class OutboundEmailError(RuntimeError):
    pass


@dataclass(frozen=True)
class ForwardDraftResult:
    draft_id: str
    draft_dir: Path
    message_path: Path
    metadata_path: Path
    recipient: str
    subject: str
    provider: str
    source_uid: str


@dataclass(frozen=True)
class SendDraftResult:
    draft_id: str
    recipient: str
    subject: str
    provider: str
    sent_at: str


def prepare_forward_draft(
    source: EmailArchiveSource,
    smtp_config: OutgoingMailConfig,
    recipient_email: str,
    note: str = "",
    draft_dir: Path = DEFAULT_OUTBOX_DRAFT_DIR,
    now: datetime | None = None,
) -> ForwardDraftResult:
    recipient = validate_email_address(recipient_email)
    prepared_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    draft_id = build_forward_draft_id(
        provider=source.provider or smtp_config.provider,
        uid=source.uid,
        subject=source.subject,
        prepared_at=prepared_at,
    )
    target_dir = draft_dir / draft_id
    if target_dir.exists():
        raise OutboundEmailError(f"Draft {draft_id} uz existuje.")
    target_dir.mkdir(parents=True, exist_ok=False)

    message = build_forward_message(
        source=source,
        smtp_config=smtp_config,
        recipient_email=recipient,
        note=note,
    )
    message_path = target_dir / "forward.eml"
    metadata_path = target_dir / "metadata.json"
    message_path.write_bytes(message.as_bytes())
    write_json(
        metadata_path,
        {
            "draft_id": draft_id,
            "status": "draft",
            "provider": smtp_config.provider,
            "source_provider": source.provider,
            "source_uid": source.uid,
            "source_date": source.date,
            "source_subject": source.subject,
            "recipient": recipient,
            "subject": str(message["Subject"] or ""),
            "prepared_at": prepared_at.isoformat(),
            "message_path": str(relative_to_project(message_path)),
            "contains_original_eml": source.original_eml is not None,
            "do_not_commit": True,
            "local_sensitive_draft": True,
        },
    )
    return ForwardDraftResult(
        draft_id=draft_id,
        draft_dir=target_dir,
        message_path=message_path,
        metadata_path=metadata_path,
        recipient=recipient,
        subject=str(message["Subject"] or ""),
        provider=smtp_config.provider,
        source_uid=source.uid,
    )


def build_forward_message(
    source: EmailArchiveSource,
    smtp_config: OutgoingMailConfig,
    recipient_email: str,
    note: str = "",
) -> StdEmailMessage:
    recipient = validate_email_address(recipient_email)
    subject = source.subject.strip() or "(bez predmetu)"
    forward_subject = subject if subject.casefold().startswith("fwd:") else f"Fwd: {subject}"

    message = StdEmailMessage()
    message["From"] = smtp_config.address
    message["To"] = recipient
    message["Subject"] = forward_subject

    body_lines = []
    if note.strip():
        body_lines.extend([note.strip(), ""])
    body_lines.extend(
        [
            "Preposilam e-mail.",
            "",
            "Puvodni zprava:",
            f"- Datum: {source.date or 'nezjisteno'}",
            f"- Od: {source.sender or 'nezjisteno'}",
            f"- Predmet: {subject}",
        ]
    )
    if source.original_eml is not None:
        body_lines.append("- Original je prilozen jako soubor original.eml.")
    else:
        body_lines.append("- Originalni .eml neni dostupny; nize je textovy vytah.")
        if source.body_text.strip():
            body_lines.extend(["", source.body_text.strip()])

    message.set_content("\n".join(body_lines))
    if source.original_eml is not None:
        message.add_attachment(
            source.original_eml,
            maintype="message",
            subtype="rfc822",
            filename=f"original-{safe_slug(source.uid, 'email', 40)}.eml",
        )
    return message


def send_forward_draft(
    draft_id: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    draft_dir: Path = DEFAULT_OUTBOX_DRAFT_DIR,
    smtp_config_loader: Callable[[str], OutgoingMailConfig] = load_smtp_config,
    smtp_factory: Callable[..., Any] | None = None,
    now: datetime | None = None,
) -> SendDraftResult:
    safe_draft_id = safe_slug(draft_id, default="", limit=140)
    if not safe_draft_id:
        raise OutboundEmailError("Chybi draft_id.")

    target_dir = (draft_dir / safe_draft_id).resolve()
    draft_root = draft_dir.resolve()
    if not is_relative_to(target_dir, draft_root):
        raise OutboundEmailError("Draft musi byt v povolene slozce outbox_drafts.")

    metadata_path = target_dir / "metadata.json"
    message_path = target_dir / "forward.eml"
    if not metadata_path.exists() or not message_path.exists():
        raise OutboundEmailError(f"Draft {safe_draft_id} nebyl nalezen.")

    metadata = read_json(metadata_path)
    if metadata.get("status") == "sent":
        raise OutboundEmailError(f"Draft {safe_draft_id} uz byl odeslan.")

    recipient = validate_email_address(str(metadata.get("recipient", "")))
    if not user_confirmed or not has_explicit_send_confirmation(
        draft_id=safe_draft_id,
        recipient_email=recipient,
        confirmation_text=confirmation_text,
    ):
        raise OutboundEmailError(
            "Pro odeslani potrebuji samostatne potvrzeni v aktualni zprave. "
            f"Pouzij: Potvrzuji, odeslat draft {safe_draft_id} na {recipient}."
        )

    provider = safe_provider(str(metadata.get("provider", "")))
    smtp_config = smtp_config_loader(provider)
    parsed = message_from_bytes(message_path.read_bytes())
    sent_at = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    send_message_via_smtp(parsed, smtp_config=smtp_config, smtp_factory=smtp_factory)

    updated = dict(metadata)
    updated["status"] = "sent"
    updated["sent_at"] = sent_at
    write_json(metadata_path, updated)
    return SendDraftResult(
        draft_id=safe_draft_id,
        recipient=recipient,
        subject=str(metadata.get("subject", "")),
        provider=provider,
        sent_at=sent_at,
    )


def send_message_via_smtp(
    message: Any,
    smtp_config: OutgoingMailConfig,
    smtp_factory: Callable[..., Any] | None = None,
) -> None:
    factory = smtp_factory
    if factory is None:
        factory = smtplib.SMTP_SSL if smtp_config.security == "ssl" else smtplib.SMTP

    with factory(smtp_config.host, smtp_config.port, timeout=30) as smtp:
        if smtp_config.security == "starttls":
            smtp.starttls()
        smtp.login(smtp_config.address, smtp_config.password)
        smtp.send_message(message)


def has_explicit_forward_prepare_confirmation(
    uid: str,
    recipient_email: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    return (
        uid.strip() in normalized
        and validate_email_address(recipient_email).casefold() in normalized
        and any(word in normalized for word in FORWARD_WORDS)
    )


def has_explicit_send_confirmation(
    draft_id: str,
    recipient_email: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    return (
        normalize_confirmation_text(draft_id) in normalized
        and validate_email_address(recipient_email).casefold() in normalized
        and any(word in normalized for word in SEND_WORDS)
        and any(word in normalized for word in CONFIRM_WORDS)
    )


def validate_email_address(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if any(char in cleaned for char in "\r\n"):
        raise OutboundEmailError("E-mailova adresa nesmi obsahovat novy radek.")
    _name, address = parseaddr(cleaned)
    if not address or address != cleaned:
        raise OutboundEmailError("Pouzij jednu cistou e-mailovou adresu bez jmena.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", address):
        raise OutboundEmailError("Neplatna e-mailova adresa prijemce.")
    return address


def build_forward_draft_id(
    provider: str,
    uid: str,
    subject: str,
    prepared_at: datetime,
) -> str:
    timestamp = prepared_at.strftime("%Y%m%d%H%M%S")
    subject_part = safe_slug(subject, default="email", limit=48)
    return safe_slug(
        f"forward-{timestamp}-{provider}-{uid}-{subject_part}",
        default=f"forward-{timestamp}",
        limit=140,
    )


def safe_provider(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized not in {"icloud", "seznam"}:
        raise OutboundEmailError("Neznamy provider draftu.")
    return normalized


def safe_slug(value: str, default: str, limit: int) -> str:
    folded = strip_accents(value.casefold())
    slug = SAFE_ID_PATTERN.sub("-", folded).strip("-._")
    return (slug or default)[:limit].rstrip("-._") or default


def strip_accents(value: str) -> str:
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
    return value.translate(replacements)


def normalize_confirmation_text(value: str) -> str:
    return " ".join(value.casefold().split())


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise OutboundEmailError(f"Neplatny JSON v {path}.")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def relative_to_project(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def redacted_send_summary(result: SendDraftResult) -> str:
    return (
        f"Odeslano: draft {result.draft_id}.\n"
        f"- Provider: {result.provider}\n"
        f"- Komu: {redact_email_addresses(result.recipient)}\n"
        f"- Predmet: {result.subject or '(bez predmetu)'}\n"
        f"- Odeslano v: {result.sent_at}"
    )
