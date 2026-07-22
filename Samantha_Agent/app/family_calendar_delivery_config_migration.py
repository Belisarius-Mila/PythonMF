"""Explicit, recoverable migration of private delivery config from schema 1 to 2."""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.family_calendar_delivery_config import (
    DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
    DELIVERY_CONFIG_SCHEMA_VERSION,
    MAX_DELIVERY_CONFIG_BYTES,
    FamilyCalendarDeliveryConfig,
    parse_family_calendar_delivery_config_document,
)
from app.file_persistence import (
    FilePersistenceError,
    atomic_replace_text_under_external_lock,
    exclusive_file_lock,
    lock_path_for,
)


LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION = 1
DELIVERY_CONFIG_MIGRATION_CONFIRMATION = (
    "APPLY_FAMILY_CALENDAR_CONFIG_MIGRATION_V1_TO_V2"
)
LEGACY_CONFIG_FIELDS = frozenset(
    {"schema_version", "mode", "smtp_provider", "recipients"}
)


class DeliveryConfigMigrationError(RuntimeError):
    """Raised when private config migration cannot be proven safe."""


@dataclass(frozen=True, repr=False)
class DeliveryConfigMigrationInspection:
    smtp_provider: str
    mode: str
    recipient_count: int

    def __repr__(self) -> str:
        return (
            "DeliveryConfigMigrationInspection("
            f"from_schema={LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"to_schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.mode!r}, recipient_count={self.recipient_count}, "
            "redacted=True)"
        )


@dataclass(frozen=True, repr=False)
class DeliveryConfigMigrationPlan:
    path: Path
    source_digest: str
    config: FamilyCalendarDeliveryConfig

    def __repr__(self) -> str:
        return (
            "DeliveryConfigMigrationPlan("
            f"from_schema={LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"to_schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.config.mode.value!r}, "
            f"recipient_count={len(self.config.recipients)}, redacted=True)"
        )


@dataclass(frozen=True, repr=False)
class DeliveryConfigMigrationResult:
    config: FamilyCalendarDeliveryConfig
    backup_created: bool

    def __repr__(self) -> str:
        return (
            "DeliveryConfigMigrationResult("
            f"schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.config.mode.value!r}, "
            f"recipient_count={len(self.config.recipients)}, "
            f"backup_created={self.backup_created!r}, redacted=True)"
        )


def inspect_family_calendar_delivery_config_migration(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> DeliveryConfigMigrationInspection:
    """Validate schema 1 without a real sender and return only safe metadata."""

    try:
        _, raw = _read_legacy_document(Path(path))
        config = _schema_two_config(
            raw,
            sender_address="migration-preview@example.invalid",
        )
    except DeliveryConfigMigrationError:
        raise
    except Exception as exc:  # noqa: BLE001 - never expose private parser details.
        raise DeliveryConfigMigrationError(
            "Family-calendar delivery config migration cannot be inspected safely."
        ) from exc
    return DeliveryConfigMigrationInspection(
        smtp_provider=config.smtp_provider,
        mode=config.mode.value,
        recipient_count=len(config.recipients),
    )


def plan_family_calendar_delivery_config_migration(
    *,
    sender_address: str,
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> DeliveryConfigMigrationPlan:
    """Read and validate schema 1, returning a redacted no-write migration plan."""

    target = Path(path)
    try:
        source_bytes, raw = _read_legacy_document(target)
        config = _schema_two_config(raw, sender_address=sender_address)
    except DeliveryConfigMigrationError:
        raise
    except Exception as exc:  # noqa: BLE001 - keep private parser failures redacted.
        raise DeliveryConfigMigrationError(
            "Family-calendar delivery config migration cannot be planned safely."
        ) from exc
    return DeliveryConfigMigrationPlan(
        path=target,
        source_digest=hashlib.sha256(source_bytes).hexdigest(),
        config=config,
    )


def apply_family_calendar_delivery_config_migration(
    plan: DeliveryConfigMigrationPlan,
    *,
    confirmation: str,
    lock_timeout: float = 10.0,
) -> DeliveryConfigMigrationResult:
    """Apply one unchanged plan atomically after exact confirmation and backup."""

    if not isinstance(plan, DeliveryConfigMigrationPlan):
        raise DeliveryConfigMigrationError("A validated delivery config migration plan is required.")
    if confirmation != DELIVERY_CONFIG_MIGRATION_CONFIRMATION:
        raise DeliveryConfigMigrationError("Exact delivery config migration confirmation is required.")

    target = plan.path
    backup_path = _backup_path_for(target)
    try:
        with exclusive_file_lock(target, timeout=lock_timeout):
            lock_path_for(target).chmod(0o600)
            source_bytes, raw = _read_legacy_document(target)
            if hashlib.sha256(source_bytes).hexdigest() != plan.source_digest:
                raise DeliveryConfigMigrationError(
                    "Private delivery configuration changed after migration planning."
                )
            current_config = _schema_two_config(
                raw,
                sender_address=plan.config.sender_address,
            )
            if current_config != plan.config:
                raise DeliveryConfigMigrationError(
                    "Private delivery configuration no longer matches its migration plan."
                )
            if backup_path.exists() or backup_path.is_symlink():
                raise DeliveryConfigMigrationError(
                    "Private schema-1 migration backup already exists."
                )

            source_text = source_bytes.decode("utf-8")
            atomic_replace_text_under_external_lock(backup_path, source_text)
            backup_path.chmod(0o600)
            payload = _config_document(plan.config)
            migrated_text = json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ) + "\n"
            atomic_replace_text_under_external_lock(target, migrated_text)
            target.chmod(0o600)
            target.parent.chmod(0o700)
    except DeliveryConfigMigrationError:
        _harden_private_files_best_effort(target, backup_path)
        raise
    except (OSError, UnicodeError, ValueError, FilePersistenceError) as exc:
        _harden_private_files_best_effort(target, backup_path)
        raise DeliveryConfigMigrationError(
            "Family-calendar delivery config migration failed safely."
        ) from exc

    return DeliveryConfigMigrationResult(config=plan.config, backup_created=True)


def _read_legacy_document(path: Path) -> tuple[bytes, dict[str, Any]]:
    _assert_private_legacy_file(path)
    try:
        source_bytes = path.read_bytes()
        raw = json.loads(source_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryConfigMigrationError(
            "Private schema-1 delivery configuration cannot be trusted."
        ) from exc
    if not isinstance(raw, dict) or set(raw) != LEGACY_CONFIG_FIELDS:
        raise DeliveryConfigMigrationError(
            "Private schema-1 delivery configuration has an invalid shape."
        )
    schema_version = raw.get("schema_version")
    if type(schema_version) is not int or schema_version != LEGACY_DELIVERY_CONFIG_SCHEMA_VERSION:
        raise DeliveryConfigMigrationError(
            "Private delivery configuration is not schema 1."
        )
    return source_bytes, raw


def _schema_two_config(
    legacy: dict[str, Any],
    *,
    sender_address: str,
) -> FamilyCalendarDeliveryConfig:
    candidate = dict(legacy)
    candidate["schema_version"] = DELIVERY_CONFIG_SCHEMA_VERSION
    candidate["sender_address"] = sender_address
    try:
        return parse_family_calendar_delivery_config_document(candidate)
    except Exception as exc:  # noqa: BLE001 - validation details must stay redacted here.
        raise DeliveryConfigMigrationError(
            "Migrated family-calendar delivery configuration is invalid."
        ) from exc


def _config_document(config: FamilyCalendarDeliveryConfig) -> dict[str, Any]:
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


def _assert_private_legacy_file(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise DeliveryConfigMigrationError("Private delivery configuration must not use links.")
    if not path.is_file():
        raise DeliveryConfigMigrationError("Private schema-1 delivery configuration is missing.")
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise DeliveryConfigMigrationError("Private delivery configuration directory is unsafe.")
    file_stat = path.stat()
    if stat.S_IMODE(file_stat.st_mode) != 0o600:
        raise DeliveryConfigMigrationError("Private delivery configuration file is unsafe.")
    if file_stat.st_size > MAX_DELIVERY_CONFIG_BYTES:
        raise DeliveryConfigMigrationError("Private delivery configuration is too large.")


def _backup_path_for(path: Path) -> Path:
    return path.with_name(f"{path.stem}.schema1.backup{path.suffix}")


def _harden_private_files_best_effort(path: Path, backup_path: Path) -> None:
    try:
        path.parent.chmod(0o700)
        for candidate in (path, backup_path, lock_path_for(path)):
            if candidate.exists() and not candidate.is_symlink():
                candidate.chmod(0o600)
    except OSError:
        return
