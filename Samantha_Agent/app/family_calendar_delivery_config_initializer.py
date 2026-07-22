"""Create-only initialization of private family-calendar delivery config."""

from __future__ import annotations

import json
import stat
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    CANONICAL_RECIPIENT_IDS,
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DELIVERY_CONFIG_SCHEMA_VERSION,
    DeliveryConfigError,
    DeliveryConfigMode,
    FamilyCalendarDeliveryConfig,
    load_family_calendar_delivery_config,
    parse_family_calendar_delivery_config_document,
)
from app.file_persistence import FilePersistenceError, atomic_create_text


DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION = (
    "CREATE_FAMILY_CALENDAR_DELIVERY_CONFIG_SCHEMA_2"
)


class DeliveryConfigInitializationError(RuntimeError):
    """Raised when a new private delivery config cannot be created safely."""


@dataclass(frozen=True, repr=False)
class DeliveryConfigInitializationPlan:
    path: Path
    config: FamilyCalendarDeliveryConfig

    def __repr__(self) -> str:
        return (
            "DeliveryConfigInitializationPlan("
            f"schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.config.mode.value!r}, "
            f"recipient_count={len(self.config.recipients)}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "ready",
            "schema": DELIVERY_CONFIG_SCHEMA_VERSION,
            "mode": self.config.mode.value,
            "recipient_count": len(self.config.recipients),
        }


@dataclass(frozen=True, repr=False)
class DeliveryConfigInitializationResult:
    config: FamilyCalendarDeliveryConfig

    def __repr__(self) -> str:
        return (
            "DeliveryConfigInitializationResult("
            "status='created', "
            f"schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.config.mode.value!r}, "
            f"recipient_count={len(self.config.recipients)}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "created",
            "schema": DELIVERY_CONFIG_SCHEMA_VERSION,
            "mode": self.config.mode.value,
            "recipient_count": len(self.config.recipients),
        }


def assert_family_calendar_delivery_config_can_be_initialized(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> None:
    """Read-only preflight proving that no target currently exists."""

    target = Path(path)
    if target.exists() or target.is_symlink():
        raise DeliveryConfigInitializationError(
            "Private family-calendar delivery configuration already exists."
        )
    if target.parent.is_symlink():
        raise DeliveryConfigInitializationError(
            "Private family-calendar delivery configuration must not use links."
        )
    if target.parent.exists():
        if not target.parent.is_dir():
            raise DeliveryConfigInitializationError(
                "Private family-calendar delivery configuration parent is invalid."
            )
        if stat.S_IMODE(target.parent.stat().st_mode) != 0o700:
            raise DeliveryConfigInitializationError(
                "Private family-calendar delivery configuration directory is unsafe."
            )
    elif not target.parent.parent.is_dir() or target.parent.parent.is_symlink():
        raise DeliveryConfigInitializationError(
            "Private family-calendar delivery configuration parent is unavailable."
        )


def plan_family_calendar_delivery_config_initialization(
    *,
    smtp_provider: str,
    sender_address: str,
    recipient_addresses: Sequence[str],
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> DeliveryConfigInitializationPlan:
    """Validate private inputs and return a redacted, read-only creation plan."""

    target = Path(path)
    assert_family_calendar_delivery_config_can_be_initialized(path=target)
    if isinstance(recipient_addresses, (str, bytes)) or len(recipient_addresses) != len(
        CANONICAL_RECIPIENT_IDS
    ):
        raise DeliveryConfigInitializationError(
            "Exactly four local recipient addresses are required."
        )
    raw = {
        "schema_version": DELIVERY_CONFIG_SCHEMA_VERSION,
        "mode": DeliveryConfigMode.DISABLED.value,
        "smtp_provider": smtp_provider,
        "sender_address": sender_address,
        "recipients": [
            {"recipient_id": recipient_id, "address": address}
            for recipient_id, address in zip(
                CANONICAL_RECIPIENT_IDS,
                recipient_addresses,
                strict=True,
            )
        ],
    }
    try:
        config = parse_family_calendar_delivery_config_document(raw)
    except Exception as exc:  # noqa: BLE001 - private validation details stay redacted.
        raise DeliveryConfigInitializationError(
            "Private family-calendar delivery configuration inputs are invalid."
        ) from exc
    return DeliveryConfigInitializationPlan(path=target, config=config)


def apply_family_calendar_delivery_config_initialization(
    plan: DeliveryConfigInitializationPlan,
    *,
    confirmation: str,
) -> DeliveryConfigInitializationResult:
    """Create schema 2 once after exact confirmation; never replace a target."""

    if not isinstance(plan, DeliveryConfigInitializationPlan):
        raise DeliveryConfigInitializationError(
            "A validated delivery configuration initialization plan is required."
        )
    if confirmation != DELIVERY_CONFIG_INITIALIZATION_CONFIRMATION:
        raise DeliveryConfigInitializationError(
            "Exact delivery configuration initialization confirmation is required."
        )
    target = plan.path
    try:
        assert_family_calendar_delivery_config_can_be_initialized(path=target)
        if not target.parent.exists():
            target.parent.mkdir(mode=0o700)
        if target.parent.is_symlink() or not target.parent.is_dir():
            raise DeliveryConfigInitializationError(
                "Private family-calendar delivery configuration directory is unsafe."
            )
        target.parent.chmod(0o700)
        if stat.S_IMODE(target.parent.stat().st_mode) != 0o700:
            raise DeliveryConfigInitializationError(
                "Private family-calendar delivery configuration directory is unsafe."
            )
        document = _config_document(plan.config)
        text = json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        atomic_create_text(target, text, mode=0o600)
        loaded = load_family_calendar_delivery_config(target)
    except DeliveryConfigInitializationError:
        raise
    except (OSError, ValueError, FilePersistenceError, DeliveryConfigError) as exc:
        raise DeliveryConfigInitializationError(
            "Private family-calendar delivery configuration was not created safely."
        ) from exc
    if loaded != plan.config:
        raise DeliveryConfigInitializationError(
            "Created private delivery configuration failed verification."
        )
    return DeliveryConfigInitializationResult(config=loaded)


def _config_document(config: FamilyCalendarDeliveryConfig) -> dict[str, object]:
    return {
        "schema_version": DELIVERY_CONFIG_SCHEMA_VERSION,
        "mode": config.mode.value,
        "smtp_provider": config.smtp_provider,
        "sender_address": config.sender_address,
        "recipients": [
            {
                "recipient_id": recipient.recipient_id,
                "address": recipient.address,
            }
            for recipient in config.recipients
        ],
    }
