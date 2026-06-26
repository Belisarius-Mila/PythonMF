from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


CAPABILITY_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class RiskLevel(_StringEnum):
    READ_ONLY = "read_only"
    LOCAL_WRITE = "local_write"
    GIT_COMMIT = "git_commit"
    GIT_PUBLISH = "git_publish"
    EXTERNAL_SEND = "external_send"
    DESTRUCTIVE = "destructive"
    PRIVATE_EXPORT = "private_export"
    SYSTEM_CHANGE = "system_change"


class ConfirmationPolicy(_StringEnum):
    NONE = "none"
    SUMMARY_BEFORE_ACTION = "summary_before_action"
    EXACT_CURRENT_MESSAGE = "exact_current_message"
    APPROVAL_CARD = "approval_card"
    EXACT_PHRASE = "exact_phrase"


class VoicePolicy(_StringEnum):
    ALLOWED = "allowed"
    APPROVAL_ONLY = "approval_only"
    BLOCKED = "blocked"


class MobilePolicy(_StringEnum):
    ALLOWED = "allowed"
    APPROVAL_CARD = "approval_card"
    BLOCKED = "blocked"


class AuditPolicy(_StringEnum):
    SAFE_SUMMARY = "safe_summary"
    REDACTED = "redacted"
    FULL_LOCAL = "full_local"
    NONE = "none"


STRICT_CONFIRMATION_RISKS = frozenset(
    {
        RiskLevel.EXTERNAL_SEND,
        RiskLevel.DESTRUCTIVE,
        RiskLevel.PRIVATE_EXPORT,
        RiskLevel.SYSTEM_CHANGE,
    }
)


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    label: str
    risk: RiskLevel | str
    reads: tuple[str, ...] | list[str] | str
    writes: tuple[str, ...] | list[str] | str
    tool: str
    requires_confirmation: bool = False
    confirmation_policy: ConfirmationPolicy | str = ConfirmationPolicy.NONE
    voice_allowed: VoicePolicy | str = VoicePolicy.ALLOWED
    mobile_allowed: MobilePolicy | str = MobilePolicy.ALLOWED
    audit: AuditPolicy | str = AuditPolicy.SAFE_SUMMARY
    notes: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", self.capability_id.strip())
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "tool", self.tool.strip())
        object.__setattr__(self, "risk", RiskLevel(self.risk))
        object.__setattr__(self, "reads", _normalize_tuple(self.reads))
        object.__setattr__(self, "writes", _normalize_tuple(self.writes))
        object.__setattr__(self, "confirmation_policy", ConfirmationPolicy(self.confirmation_policy))
        object.__setattr__(self, "voice_allowed", VoicePolicy(self.voice_allowed))
        object.__setattr__(self, "mobile_allowed", MobilePolicy(self.mobile_allowed))
        object.__setattr__(self, "audit", AuditPolicy(self.audit))
        object.__setattr__(self, "metadata", dict(self.metadata))
        self.validate()

    def validate(self) -> None:
        if not CAPABILITY_ID_PATTERN.fullmatch(self.capability_id):
            raise ValueError(f"invalid capability_id: {self.capability_id!r}")
        if not self.label:
            raise ValueError("label is required")
        if not self.tool:
            raise ValueError("tool is required")
        if self.requires_confirmation and self.confirmation_policy == ConfirmationPolicy.NONE:
            raise ValueError("requires_confirmation needs a non-none confirmation_policy")
        if not self.requires_confirmation and self.confirmation_policy != ConfirmationPolicy.NONE:
            raise ValueError("confirmation_policy must be none when requires_confirmation is false")
        if self.risk in STRICT_CONFIRMATION_RISKS and not self.requires_confirmation:
            raise ValueError(f"{self.risk.value} capabilities require confirmation")
        if self.voice_allowed == VoicePolicy.APPROVAL_ONLY and not self.requires_confirmation:
            raise ValueError("voice approval_only requires confirmation")
        if self.mobile_allowed == MobilePolicy.APPROVAL_CARD and not self.requires_confirmation:
            raise ValueError("mobile approval_card requires confirmation")
        if self.risk in {RiskLevel.EXTERNAL_SEND, RiskLevel.PRIVATE_EXPORT} and self.audit == AuditPolicy.FULL_LOCAL:
            raise ValueError(f"{self.risk.value} capabilities cannot use full_local audit")

    @property
    def is_read_only(self) -> bool:
        return self.risk == RiskLevel.READ_ONLY and not self.writes

    @property
    def is_high_risk(self) -> bool:
        return self.risk in STRICT_CONFIRMATION_RISKS

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "label": self.label,
            "risk": self.risk.value,
            "reads": list(self.reads),
            "writes": list(self.writes),
            "requires_confirmation": self.requires_confirmation,
            "confirmation_policy": self.confirmation_policy.value,
            "voice_allowed": self.voice_allowed.value,
            "mobile_allowed": self.mobile_allowed.value,
            "audit": self.audit.value,
            "tool": self.tool,
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }


def _normalize_tuple(value: tuple[str, ...] | list[str] | str) -> tuple[str, ...]:
    if isinstance(value, str):
        if not value.strip():
            return ()
        return (value.strip(),)
    return tuple(str(item).strip() for item in value if str(item).strip())
