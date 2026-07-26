"""Read-only private configuration for family-calendar delivery."""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH = (
    PROJECT_ROOT / "data" / "private" / "family_calendar" / "notification_config.json"
)
DELIVERY_CONFIG_SCHEMA_VERSION = 2
MAX_DELIVERY_CONFIG_BYTES = 32_000
CANONICAL_RECIPIENT_IDS = (
    "recipient-1",
    "recipient-2",
    "recipient-3",
    "recipient-4",
)
SUPPORTED_SMTP_PROVIDERS = frozenset({"icloud", "seznam"})
EMAIL_ADDRESS_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class DeliveryConfigError(RuntimeError):
    """Raised when the private notification configuration cannot be trusted."""


class DeliveryConfigMode(str, Enum):
    DISABLED = "disabled"
    DRY_RUN = "dry_run"
    ENABLED = "enabled"


@dataclass(frozen=True, repr=False)
class DeliveryRecipientConfig:
    recipient_id: str
    address: str


@dataclass(frozen=True, repr=False)
class FamilyCalendarDeliveryConfig:
    mode: DeliveryConfigMode
    smtp_provider: str
    sender_address: str
    recipients: tuple[DeliveryRecipientConfig, ...]

    @property
    def recipient_ids(self) -> tuple[str, ...]:
        return tuple(recipient.recipient_id for recipient in self.recipients)


def load_family_calendar_delivery_config(
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> FamilyCalendarDeliveryConfig:
    """Load a non-sending, strictly validated private configuration without writing."""

    target = Path(path)
    try:
        _assert_private_config_file(target)
        raw = json.loads(target.read_text(encoding="utf-8"))
        return parse_family_calendar_delivery_config_document(raw)
    except DeliveryConfigError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise DeliveryConfigError("Family-calendar delivery configuration cannot be trusted.") from exc


def parse_family_calendar_delivery_config_document(
    raw: Any,
) -> FamilyCalendarDeliveryConfig:
    """Validate one already-loaded schema-2 document without performing I/O."""

    expected_fields = {
        "schema_version",
        "mode",
        "smtp_provider",
        "sender_address",
        "recipients",
    }
    if not isinstance(raw, dict) or set(raw) != expected_fields:
        raise DeliveryConfigError("Delivery configuration has an invalid shape.")
    schema_version = raw.get("schema_version")
    if type(schema_version) is not int or schema_version != DELIVERY_CONFIG_SCHEMA_VERSION:
        raise DeliveryConfigError("Unsupported family-calendar delivery configuration schema.")

    mode_value = _required_string(raw.get("mode"), field="mode")
    try:
        mode = DeliveryConfigMode(mode_value)
    except ValueError as exc:
        raise DeliveryConfigError("Delivery configuration mode is not enabled for this phase.") from exc

    smtp_provider = _required_string(raw.get("smtp_provider"), field="smtp_provider")
    if smtp_provider not in SUPPORTED_SMTP_PROVIDERS:
        raise DeliveryConfigError("Delivery configuration has an unsupported SMTP provider.")
    if mode is DeliveryConfigMode.ENABLED and smtp_provider != "icloud":
        raise DeliveryConfigError(
            "Enabled family-calendar delivery requires the iCloud SMTP provider."
        )
    sender_address = _email_address(raw.get("sender_address"), field="sender")

    raw_recipients = raw.get("recipients")
    if not isinstance(raw_recipients, list) or len(raw_recipients) != len(
        CANONICAL_RECIPIENT_IDS
    ):
        raise DeliveryConfigError("Delivery configuration requires exactly four recipients.")
    recipients_by_id: dict[str, DeliveryRecipientConfig] = {}
    normalized_addresses = set()
    for raw_recipient in raw_recipients:
        recipient = _recipient_from_document(raw_recipient)
        if recipient.recipient_id in recipients_by_id:
            raise DeliveryConfigError("Delivery configuration has duplicate recipient identities.")
        normalized_address = recipient.address.casefold()
        if normalized_address in normalized_addresses:
            raise DeliveryConfigError("Delivery configuration has duplicate recipient addresses.")
        recipients_by_id[recipient.recipient_id] = recipient
        normalized_addresses.add(normalized_address)
    if set(recipients_by_id) != set(CANONICAL_RECIPIENT_IDS):
        raise DeliveryConfigError("Delivery configuration has non-canonical recipient identities.")

    return FamilyCalendarDeliveryConfig(
        mode=mode,
        smtp_provider=smtp_provider,
        sender_address=sender_address,
        recipients=tuple(recipients_by_id[recipient_id] for recipient_id in CANONICAL_RECIPIENT_IDS),
    )


def _recipient_from_document(raw: Any) -> DeliveryRecipientConfig:
    if not isinstance(raw, dict) or set(raw) != {"recipient_id", "address"}:
        raise DeliveryConfigError("Delivery recipient configuration has an invalid shape.")
    recipient_id = _required_string(raw.get("recipient_id"), field="recipient_id")
    address = _email_address(raw.get("address"), field="recipient")
    return DeliveryRecipientConfig(recipient_id=recipient_id, address=address)


def _email_address(value: Any, *, field: str) -> str:
    address = _required_string(value, field=f"{field}_address")
    if len(address) > 320 or EMAIL_ADDRESS_RE.fullmatch(address) is None:
        raise DeliveryConfigError(f"Delivery {field} address is invalid.")
    return address


def _required_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DeliveryConfigError(f"Delivery configuration field {field} is invalid.")
    if "\r" in value or "\n" in value:
        raise DeliveryConfigError(f"Delivery configuration field {field} is invalid.")
    return value


def _assert_private_config_file(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise DeliveryConfigError("Delivery configuration must not use symbolic links.")
    if not path.is_file():
        raise DeliveryConfigError("Private family-calendar delivery configuration is missing.")
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise DeliveryConfigError("Delivery configuration directory is not private.")
    file_stat = path.stat()
    if stat.S_IMODE(file_stat.st_mode) != 0o600:
        raise DeliveryConfigError("Delivery configuration file is not private.")
    if file_stat.st_size > MAX_DELIVERY_CONFIG_BYTES:
        raise DeliveryConfigError("Delivery configuration file is too large.")
