"""Local-only runner for safe family-calendar delivery-config migration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
)
from app.family_calendar_delivery_config_migration import (
    DELIVERY_CONFIG_MIGRATION_CONFIRMATION,
    DELIVERY_CONFIG_SCHEMA_VERSION,
    LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION,
    DeliveryConfigMigrationError,
    apply_family_calendar_delivery_config_migration,
    inspect_family_calendar_delivery_config_migration,
    plan_family_calendar_delivery_config_migration,
)


SENDER_ENVIRONMENT_KEYS = {
    "icloud": "ICLOUD_MAIL_ADDRESS",
    "seznam": "SEZNAM_MAIL_ADDRESS",
}


class LocalDeliveryConfigMigrationRunnerError(RuntimeError):
    """Raised when the local migration runner cannot proceed safely."""


@dataclass(frozen=True, repr=False)
class LocalDeliveryConfigMigrationRunResult:
    status: str
    mode: str
    recipient_count: int
    backup_created: bool

    def __repr__(self) -> str:
        return (
            "LocalDeliveryConfigMigrationRunResult("
            f"status={self.status!r}, "
            f"from_schema={LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"to_schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.mode!r}, recipient_count={self.recipient_count}, "
            f"backup_created={self.backup_created!r}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": self.status,
            "from_schema": LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION,
            "to_schema": DELIVERY_CONFIG_SCHEMA_VERSION,
            "mode": self.mode,
            "recipient_count": self.recipient_count,
            "backup_created": self.backup_created,
        }


def run_local_family_calendar_delivery_config_migration(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    apply: bool = False,
    confirmation: str = "",
    environment: Mapping[str, str] | None = None,
) -> LocalDeliveryConfigMigrationRunResult:
    """Preview by default; apply only with the canonical explicit confirmation."""

    source_environment = os.environ if environment is None else environment
    try:
        inspection = inspect_family_calendar_delivery_config_migration(path=path)
        sender_key = SENDER_ENVIRONMENT_KEYS.get(inspection.smtp_provider)
        if sender_key is None:
            raise LocalDeliveryConfigMigrationRunnerError(
                "The local delivery-config migration provider is unsupported."
            )
        sender_address = source_environment.get(sender_key, "")
        if not isinstance(sender_address, str) or not sender_address.strip():
            raise LocalDeliveryConfigMigrationRunnerError(
                "The local sender address required for migration is unavailable."
            )
        plan = plan_family_calendar_delivery_config_migration(
            sender_address=sender_address.strip(),
            path=path,
        )
        if not apply:
            return LocalDeliveryConfigMigrationRunResult(
                status="preview",
                mode=inspection.mode,
                recipient_count=inspection.recipient_count,
                backup_created=False,
            )
        if confirmation != DELIVERY_CONFIG_MIGRATION_CONFIRMATION:
            raise LocalDeliveryConfigMigrationRunnerError(
                "Exact local delivery-config migration confirmation is required."
            )
        result = apply_family_calendar_delivery_config_migration(
            plan,
            confirmation=confirmation,
        )
        return LocalDeliveryConfigMigrationRunResult(
            status="applied",
            mode=result.config.mode.value,
            recipient_count=len(result.config.recipients),
            backup_created=result.backup_created,
        )
    except LocalDeliveryConfigMigrationRunnerError:
        raise
    except DeliveryConfigMigrationError as exc:
        raise LocalDeliveryConfigMigrationRunnerError(
            "Local family-calendar delivery-config migration failed safely."
        ) from exc
