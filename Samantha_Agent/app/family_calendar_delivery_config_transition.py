"""Explicit atomic transition of delivery config from disabled to dry-run."""

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
    DeliveryConfigMode,
    FamilyCalendarDeliveryConfig,
    load_family_calendar_delivery_config,
    parse_family_calendar_delivery_config_document,
)
from app.file_persistence import (
    FilePersistenceError,
    atomic_replace_text_under_external_lock,
    exclusive_file_lock,
    lock_path_for,
)


DELIVERY_CONFIG_DRY_RUN_CONFIRMATION = "ENABLE_FAMILY_CALENDAR_DELIVERY_DRY_RUN"
CONFIG_FIELDS = frozenset(
    {"schema_version", "mode", "smtp_provider", "sender_address", "recipients"}
)


class DeliveryConfigTransitionError(RuntimeError):
    """Raised when the config cannot transition to dry-run safely."""


@dataclass(frozen=True, repr=False)
class DeliveryConfigTransitionPlan:
    path: Path
    source_digest: str
    source_config: FamilyCalendarDeliveryConfig
    target_config: FamilyCalendarDeliveryConfig

    def __repr__(self) -> str:
        return (
            "DeliveryConfigTransitionPlan("
            f"schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"from_mode={self.source_config.mode.value!r}, "
            f"to_mode={self.target_config.mode.value!r}, "
            f"recipient_count={len(self.target_config.recipients)}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "preview",
            "schema": DELIVERY_CONFIG_SCHEMA_VERSION,
            "from_mode": self.source_config.mode.value,
            "to_mode": self.target_config.mode.value,
            "recipient_count": len(self.target_config.recipients),
        }


@dataclass(frozen=True, repr=False)
class DeliveryConfigTransitionResult:
    config: FamilyCalendarDeliveryConfig

    def __repr__(self) -> str:
        return (
            "DeliveryConfigTransitionResult("
            "status='applied', "
            f"schema={DELIVERY_CONFIG_SCHEMA_VERSION}, "
            f"mode={self.config.mode.value!r}, "
            f"recipient_count={len(self.config.recipients)}, redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "applied",
            "schema": DELIVERY_CONFIG_SCHEMA_VERSION,
            "mode": self.config.mode.value,
            "recipient_count": len(self.config.recipients),
        }


def plan_family_calendar_delivery_config_dry_run(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_DELIVERY_CONFIG_PATH,
) -> DeliveryConfigTransitionPlan:
    """Return a redacted no-write plan for the sole allowed mode transition."""

    target = Path(path)
    try:
        source_bytes, raw, source_config = _read_private_config_snapshot(target)
        if source_config.mode is not DeliveryConfigMode.DISABLED:
            raise DeliveryConfigTransitionError(
                "Family-calendar delivery configuration is not disabled."
            )
        target_document = dict(raw)
        target_document["mode"] = DeliveryConfigMode.DRY_RUN.value
        target_config = parse_family_calendar_delivery_config_document(target_document)
    except DeliveryConfigTransitionError:
        raise
    except Exception as exc:  # noqa: BLE001 - keep all private details redacted.
        raise DeliveryConfigTransitionError(
            "Family-calendar delivery dry-run transition cannot be planned safely."
        ) from exc
    return DeliveryConfigTransitionPlan(
        path=target,
        source_digest=hashlib.sha256(source_bytes).hexdigest(),
        source_config=source_config,
        target_config=target_config,
    )


def apply_family_calendar_delivery_config_dry_run(
    plan: DeliveryConfigTransitionPlan,
    *,
    confirmation: str,
    lock_timeout: float = 10.0,
) -> DeliveryConfigTransitionResult:
    """Apply one unchanged disabled-to-dry-run plan atomically."""

    if not isinstance(plan, DeliveryConfigTransitionPlan):
        raise DeliveryConfigTransitionError(
            "A validated delivery configuration transition plan is required."
        )
    if confirmation != DELIVERY_CONFIG_DRY_RUN_CONFIRMATION:
        raise DeliveryConfigTransitionError(
            "Exact delivery configuration dry-run confirmation is required."
        )
    target = plan.path
    try:
        with exclusive_file_lock(target, timeout=lock_timeout):
            lock_path_for(target).chmod(0o600)
            source_bytes, raw, current_config = _read_private_config_snapshot(target)
            if hashlib.sha256(source_bytes).hexdigest() != plan.source_digest:
                raise DeliveryConfigTransitionError(
                    "Private delivery configuration changed after transition planning."
                )
            if current_config != plan.source_config:
                raise DeliveryConfigTransitionError(
                    "Private delivery configuration no longer matches its transition plan."
                )
            if current_config.mode is not DeliveryConfigMode.DISABLED:
                raise DeliveryConfigTransitionError(
                    "Private delivery configuration is no longer disabled."
                )
            target_document = dict(raw)
            target_document["mode"] = DeliveryConfigMode.DRY_RUN.value
            target_config = parse_family_calendar_delivery_config_document(target_document)
            if target_config != plan.target_config:
                raise DeliveryConfigTransitionError(
                    "Private delivery configuration target no longer matches its plan."
                )
            text = json.dumps(
                target_document,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ) + "\n"
            atomic_replace_text_under_external_lock(target, text)
            target.chmod(0o600)
            target.parent.chmod(0o700)
            loaded = load_family_calendar_delivery_config(target)
    except DeliveryConfigTransitionError:
        raise
    except (OSError, UnicodeError, ValueError, FilePersistenceError) as exc:
        raise DeliveryConfigTransitionError(
            "Family-calendar delivery dry-run transition failed safely."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - loader/parser errors remain redacted.
        raise DeliveryConfigTransitionError(
            "Family-calendar delivery dry-run transition verification failed safely."
        ) from exc
    if loaded != plan.target_config:
        raise DeliveryConfigTransitionError(
            "Transitioned private delivery configuration failed verification."
        )
    return DeliveryConfigTransitionResult(config=loaded)


def _read_private_config_snapshot(
    path: Path,
) -> tuple[bytes, dict[str, Any], FamilyCalendarDeliveryConfig]:
    _assert_private_config_file(path)
    try:
        source_bytes = path.read_bytes()
        raw = json.loads(source_bytes.decode("utf-8"))
        config = parse_family_calendar_delivery_config_document(raw)
    except Exception as exc:  # noqa: BLE001 - never expose private parsing details.
        raise DeliveryConfigTransitionError(
            "Private family-calendar delivery configuration cannot be trusted."
        ) from exc
    if not isinstance(raw, dict) or set(raw) != CONFIG_FIELDS:
        raise DeliveryConfigTransitionError(
            "Private family-calendar delivery configuration has an invalid shape."
        )
    return source_bytes, raw, config


def _assert_private_config_file(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise DeliveryConfigTransitionError(
            "Private delivery configuration must not use links."
        )
    if not path.is_file():
        raise DeliveryConfigTransitionError(
            "Private family-calendar delivery configuration is missing."
        )
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise DeliveryConfigTransitionError(
            "Private delivery configuration directory is unsafe."
        )
    file_stat = path.stat()
    if stat.S_IMODE(file_stat.st_mode) != 0o600:
        raise DeliveryConfigTransitionError(
            "Private delivery configuration file is unsafe."
        )
    if file_stat.st_size > MAX_DELIVERY_CONFIG_BYTES:
        raise DeliveryConfigTransitionError(
            "Private delivery configuration is too large."
        )
