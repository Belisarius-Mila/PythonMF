from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTACTS_PATH = PROJECT_ROOT / "data" / "private" / "contacts" / "family_contacts.json"
DEFAULT_MESSAGES_DB_PATH = Path.home() / "Library" / "Messages" / "chat.db"
MACOS_MESSAGES_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


@dataclass(frozen=True)
class ResolvedMessageRecipient:
    display_name: str
    phone: str
    source: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class MessageDeliveryStatus:
    status: str
    service: str
    is_sent: int
    is_delivered: int
    error: int
    date: str
    handle: str


@dataclass(frozen=True)
class SendMessageResult:
    status: str
    recipient: ResolvedMessageRecipient
    delivery: MessageDeliveryStatus | None
    detail: str


def send_confirmed_sms_rcs_text(
    message_text: str,
    recipient_phone: str = "",
    contact_name: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    preferred_service: str = "SMS",
    contacts_path: Path = DEFAULT_CONTACTS_PATH,
    messages_db_path: Path = DEFAULT_MESSAGES_DB_PATH,
    sender: Callable[[str, str, str], None] = lambda phone, text, service: send_via_messages_app(
        phone, text, service
    ),
    verifier: Callable[[str, int, Path, int, float], MessageDeliveryStatus | None] = lambda phone, sent_after_ns, db_path, attempts, interval: wait_for_message_status(
        phone=phone,
        sent_after_ns=sent_after_ns,
        db_path=db_path,
        attempts=attempts,
        interval_seconds=interval,
    ),
    poll_attempts: int = 8,
    poll_interval_seconds: float = 1.5,
) -> str:
    """Send one SMS/RCS/iMessage only after explicit confirmation and DB status verification."""
    clean_message = " ".join(message_text.split())
    if not clean_message:
        return "SMS/RCS odeslani zastaveno: chybi text zpravy."

    if len(clean_message) > 500:
        return "SMS/RCS odeslani zastaveno: zprava je prilis dlouha pro tento bezpecny tool."

    try:
        recipient = resolve_message_recipient(
            recipient_phone=recipient_phone,
            contact_name=contact_name,
            contacts_path=contacts_path,
        )
    except ValueError as exc:
        return f"SMS/RCS odeslani zastaveno: {exc}"

    if not user_confirmed or not has_explicit_sms_send_confirmation(
        confirmation_text=confirmation_text,
        recipient=recipient,
    ):
        return (
            "SMS/RCS odeslani zastaveno: chybi samostatne potvrzeni. "
            "Napis potvrzeni ve tvaru: Potvrzuji, odeslat SMS/RCS kontaktu "
            f"{recipient.display_name}: {clean_message[:120]}"
        )

    service = _normalize_service(preferred_service)
    sent_after_ns = _messages_timestamp_ns(datetime.now(timezone.utc)) - 5_000_000_000

    try:
        sender(recipient.phone, clean_message, service)
    except Exception as exc:  # noqa: BLE001 - boundary around macOS Messages automation
        return (
            "SMS/RCS odeslani selhalo jeste pred kontrolou stavu: "
            f"{type(exc).__name__}: {_safe_error_text(str(exc))}"
        )

    delivery = verifier(
        recipient.phone,
        sent_after_ns,
        messages_db_path,
        max(1, min(poll_attempts, 20)),
        max(0.2, min(poll_interval_seconds, 5.0)),
    )

    if delivery is None:
        return (
            "SMS/RCS odeslani nelze potvrdit: zpravu jsem po odeslani nenasel "
            "v lokalni Messages databazi. Nepovazuji ji za odeslanou."
        )

    masked_phone = _mask_phone(recipient.phone)
    return (
        f"SMS/RCS stav pro {recipient.display_name} ({masked_phone}): {delivery.status}\n"
        f"- service: {delivery.service or service}\n"
        f"- is_sent: {delivery.is_sent}\n"
        f"- is_delivered: {delivery.is_delivered}\n"
        f"- error: {delivery.error}\n"
        f"- datum v Messages: {delivery.date or 'nezjisteno'}"
    )


def resolve_message_recipient(
    recipient_phone: str = "",
    contact_name: str = "",
    contacts_path: Path = DEFAULT_CONTACTS_PATH,
) -> ResolvedMessageRecipient:
    phone = _normalize_phone(recipient_phone)
    if phone:
        return ResolvedMessageRecipient(display_name=_mask_phone(phone), phone=phone, source="direct")

    query = _normalize_name(contact_name)
    if not query:
        raise ValueError("chybi prijemce; zadej contact_name nebo recipient_phone.")

    contacts = _load_contacts(contacts_path)
    for contact in contacts:
        names = [str(contact.get("name", ""))]
        aliases = contact.get("aliases", [])
        if isinstance(aliases, list):
            names.extend(str(alias) for alias in aliases)

        if query not in {_normalize_name(name) for name in names if name}:
            continue

        contact_phone = _normalize_phone(str(contact.get("phone", "")))
        if not contact_phone:
            raise ValueError(f"kontakt {contact.get('name', contact_name)} nema validni telefon.")
        return ResolvedMessageRecipient(
            display_name=str(contact.get("name", contact_name)).strip() or contact_name,
            phone=contact_phone,
            source="private_contacts",
            aliases=tuple(name for name in names if name),
        )

    raise ValueError("kontakt nebyl nalezen v lokalnim soukromem adresari.")


def has_explicit_sms_send_confirmation(
    confirmation_text: str,
    recipient: ResolvedMessageRecipient,
) -> bool:
    normalized = _normalize_name(confirmation_text)
    phone_digits = re.sub(r"\D+", "", recipient.phone)
    recipient_names = {_normalize_name(recipient.display_name)}
    recipient_names.update(_normalize_name(alias) for alias in recipient.aliases)
    return (
        "potvrzuji" in normalized
        and ("sms" in normalized or "rcs" in normalized or "zpravu" in normalized)
        and ("odeslat" in normalized or "poslat" in normalized)
        and (
            any(name and name in normalized for name in recipient_names)
            or phone_digits in re.sub(r"\D+", "", confirmation_text)
        )
    )


def send_via_messages_app(phone: str, message_text: str, service: str = "SMS") -> None:
    script = """
on run argv
    set recipientPhone to item 1 of argv
    set messageText to item 2 of argv
    set serviceTypeName to item 3 of argv

    tell application "Messages"
        if serviceTypeName is "RCS" then
            set targetService to first service whose service type = RCS
        else if serviceTypeName is "iMessage" then
            set targetService to first service whose service type = iMessage
        else
            set targetService to first service whose service type = SMS
        end if
        set targetBuddy to buddy recipientPhone of targetService
        send messageText to targetBuddy
    end tell
end run
""".strip()
    subprocess.run(
        ["osascript", "-e", script, phone, message_text, _normalize_service(service)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def wait_for_message_status(
    phone: str,
    sent_after_ns: int,
    db_path: Path = DEFAULT_MESSAGES_DB_PATH,
    attempts: int = 8,
    interval_seconds: float = 1.5,
) -> MessageDeliveryStatus | None:
    latest: MessageDeliveryStatus | None = None
    for _ in range(max(1, attempts)):
        latest = read_latest_outbound_message_status(
            phone=phone,
            sent_after_ns=sent_after_ns,
            db_path=db_path,
        )
        if latest is not None and latest.status in {"sent", "delivered", "failed"}:
            return latest
        time.sleep(interval_seconds)
    return latest


def read_latest_outbound_message_status(
    phone: str,
    sent_after_ns: int,
    db_path: Path = DEFAULT_MESSAGES_DB_PATH,
) -> MessageDeliveryStatus | None:
    if not db_path.exists():
        return None

    suffix = re.sub(r"\D+", "", phone)[-9:]
    query = f"%{suffix}"
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        row = conn.execute(
            """
            SELECT message.date, handle.id, message.service, message.is_sent,
                   message.is_delivered, message.error
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            WHERE message.is_from_me = 1
              AND message.date >= ?
              AND replace(replace(replace(handle.id, ' ', ''), '-', ''), '+', '') LIKE ?
            ORDER BY message.date DESC
            LIMIT 1
            """,
            (sent_after_ns, query),
        ).fetchone()

    if row is None:
        return None

    raw_date, handle, service, is_sent, is_delivered, error = row
    status = _delivery_status(is_sent=is_sent, is_delivered=is_delivered, error=error)
    return MessageDeliveryStatus(
        status=status,
        service=str(service or ""),
        is_sent=int(is_sent or 0),
        is_delivered=int(is_delivered or 0),
        error=int(error or 0),
        date=_format_messages_date(raw_date),
        handle=str(handle or ""),
    )


def _load_contacts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        if isinstance(raw.get("contacts"), list):
            return [item for item in raw["contacts"] if isinstance(item, dict)]
        return [item for item in raw.values() if isinstance(item, dict)]
    return []


def _delivery_status(is_sent: int, is_delivered: int, error: int) -> str:
    if int(is_delivered or 0) == 1:
        return "delivered"
    if int(is_sent or 0) == 1:
        return "sent"
    if int(error or 0) != 0:
        return "failed"
    return "queued"


def _normalize_phone(phone: str) -> str:
    compact = phone.strip().replace(" ", "").replace("-", "")
    if not compact:
        return ""
    if not PHONE_PATTERN.match(compact):
        raise ValueError("telefon musi byt ve formatu E.164, napr. +420XXXXXXXXX.")
    return compact


def _normalize_name(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(ascii_text.split())


def _normalize_service(service: str) -> str:
    normalized = service.strip()
    if normalized not in {"SMS", "RCS", "iMessage"}:
        return "SMS"
    return normalized


def _messages_timestamp_ns(value: datetime) -> int:
    return int((value - MACOS_MESSAGES_EPOCH).total_seconds() * 1_000_000_000)


def _format_messages_date(raw_date: object) -> str:
    try:
        ns = int(raw_date or 0)
    except (TypeError, ValueError):
        return ""
    if ns <= 0:
        return ""
    value = MACOS_MESSAGES_EPOCH.timestamp() + ns / 1_000_000_000
    return datetime.fromtimestamp(value).astimezone().isoformat(timespec="seconds")


def _mask_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone)
    if len(digits) <= 4:
        return "***"
    return f"+{digits[:3]}***{digits[-4:]}"


def _safe_error_text(text: str) -> str:
    return re.sub(r"\+\d{7,15}", "[telefon redigovan]", text)
