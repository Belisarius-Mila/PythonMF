from __future__ import annotations

from collections.abc import Iterable

from app.capabilities.models import CapabilityRecord
from app.capabilities.registry import all_capabilities


def format_runtime_capability_policy(
    records: Iterable[CapabilityRecord] | None = None,
) -> str:
    """Build the compact runtime policy section injected into Samantha's prompt."""
    capability_records = tuple(records if records is not None else all_capabilities())
    confirmed_records = tuple(record for record in capability_records if record.requires_confirmation)

    lines = [
        "Capability registry runtime policy:",
        "- Registry is the source of truth for tool risk, confirmation, voice/mobile policy and audit mode.",
        "- Before calling any capability listed below, require a current-message confirmation matching its policy.",
        "- If the human request is ambiguous, use a read-only preview/status capability first.",
        "",
        "Confirmed capabilities:",
    ]
    if not confirmed_records:
        lines.append("- None.")
        return "\n".join(lines)

    for record in sorted(confirmed_records, key=lambda item: item.capability_id):
        lines.append(
            "- "
            f"{record.capability_id}: "
            f"risk={record.risk.value}; "
            f"confirmation={record.confirmation_policy.value}; "
            f"voice={record.voice_allowed.value}; "
            f"mobile={record.mobile_allowed.value}; "
            f"audit={record.audit.value}; "
            f"tool={record.tool}."
        )
    return "\n".join(lines)
