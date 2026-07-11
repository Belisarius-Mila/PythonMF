"""Explicit in-memory command state machine for Samantha VoiceBridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


NON_FINAL_VOICE_RESPONSE_ROUTES = {
    "codex_work",
    "terminal_delivery_pending_reply",
    "terminal_delivery_unverified",
    "voice_command_delivery_unverified",
}


class VoiceCommandState(str, Enum):
    RECEIVED = "received"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    PERSISTED = "persisted"
    WATCHER_QUEUED = "watcher_queued"
    WATCHER_PROCESSING = "watcher_processing"
    AWAITING_ADAM = "awaiting_adam"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    INLINE_DELIVERING = "inline_delivering"
    DELIVERED = "delivered"
    DELIVERY_UNVERIFIED = "delivery_unverified"
    DELIVERY_FAILED = "delivery_failed"
    REJECTED = "rejected"
    TRANSCRIPTION_FAILED = "transcription_failed"
    PERSISTENCE_FAILED = "persistence_failed"
    COMPLETED = "completed"


class VoiceDeliveryOwner(str, Enum):
    NONE = "none"
    WATCHER = "watcher"
    INLINE = "inline"


TERMINAL_STATES = {
    VoiceCommandState.DELIVERED,
    VoiceCommandState.DELIVERY_UNVERIFIED,
    VoiceCommandState.DELIVERY_FAILED,
    VoiceCommandState.REJECTED,
    VoiceCommandState.TRANSCRIPTION_FAILED,
    VoiceCommandState.PERSISTENCE_FAILED,
    VoiceCommandState.COMPLETED,
}

ALLOWED_TRANSITIONS: dict[VoiceCommandState, set[VoiceCommandState]] = {
    VoiceCommandState.RECEIVED: {
        VoiceCommandState.TRANSCRIBING,
        VoiceCommandState.PERSISTED,
        VoiceCommandState.REJECTED,
        VoiceCommandState.PERSISTENCE_FAILED,
    },
    VoiceCommandState.TRANSCRIBING: {
        VoiceCommandState.TRANSCRIBED,
        VoiceCommandState.TRANSCRIPTION_FAILED,
    },
    VoiceCommandState.TRANSCRIBED: {
        VoiceCommandState.PERSISTED,
        VoiceCommandState.PERSISTENCE_FAILED,
    },
    VoiceCommandState.PERSISTED: {
        VoiceCommandState.WATCHER_QUEUED,
        VoiceCommandState.INLINE_DELIVERING,
        VoiceCommandState.DELIVERY_FAILED,
    },
    VoiceCommandState.INLINE_DELIVERING: {
        VoiceCommandState.DELIVERED,
        VoiceCommandState.DELIVERY_UNVERIFIED,
        VoiceCommandState.DELIVERY_FAILED,
    },
    VoiceCommandState.WATCHER_QUEUED: {VoiceCommandState.WATCHER_PROCESSING},
    VoiceCommandState.WATCHER_PROCESSING: {
        VoiceCommandState.AWAITING_ADAM,
        VoiceCommandState.AWAITING_CONFIRMATION,
        VoiceCommandState.COMPLETED,
        VoiceCommandState.DELIVERY_FAILED,
    },
    VoiceCommandState.AWAITING_ADAM: set(),
    VoiceCommandState.AWAITING_CONFIRMATION: set(),
    VoiceCommandState.DELIVERED: set(),
    VoiceCommandState.DELIVERY_UNVERIFIED: set(),
    VoiceCommandState.DELIVERY_FAILED: set(),
    VoiceCommandState.REJECTED: set(),
    VoiceCommandState.TRANSCRIPTION_FAILED: set(),
    VoiceCommandState.PERSISTENCE_FAILED: set(),
    VoiceCommandState.COMPLETED: set(),
}


@dataclass
class VoiceCommandStateMachine:
    """Track one command without storing command text or other private payloads."""

    state: VoiceCommandState = VoiceCommandState.RECEIVED
    owner: VoiceDeliveryOwner = VoiceDeliveryOwner.NONE
    transitions: list[dict[str, str]] = field(default_factory=list)

    def transition(
        self,
        target: VoiceCommandState,
        *,
        event: str,
        owner: VoiceDeliveryOwner | None = None,
    ) -> None:
        if target not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"Nepovolený VoiceBridge přechod: {self.state.value} -> {target.value}.")
        resolved_owner = owner or self.owner
        if self.owner is not VoiceDeliveryOwner.NONE and resolved_owner is not self.owner:
            raise ValueError(
                f"VoiceBridge pokyn už vlastní {self.owner.value}; nelze jej předat {resolved_owner.value}."
            )
        if target is VoiceCommandState.WATCHER_QUEUED and resolved_owner is not VoiceDeliveryOwner.WATCHER:
            raise ValueError("Stav watcher_queued vyžaduje vlastníka watcher.")
        if target in {
            VoiceCommandState.WATCHER_PROCESSING,
            VoiceCommandState.AWAITING_ADAM,
            VoiceCommandState.AWAITING_CONFIRMATION,
            VoiceCommandState.COMPLETED,
        } and resolved_owner is not VoiceDeliveryOwner.WATCHER:
            raise ValueError(f"Stav {target.value} vyžaduje vlastníka watcher.")
        if target in {
            VoiceCommandState.INLINE_DELIVERING,
            VoiceCommandState.DELIVERED,
            VoiceCommandState.DELIVERY_UNVERIFIED,
        } and resolved_owner is not VoiceDeliveryOwner.INLINE:
            raise ValueError(f"Stav {target.value} vyžaduje vlastníka inline.")
        previous = self.state
        self.state = target
        self.owner = resolved_owner
        self.transitions.append({
            "from": previous.value,
            "to": target.value,
            "event": str(event or "transition")[:80],
        })

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "delivery_owner": self.owner.value,
            "terminal": self.state in TERMINAL_STATES,
            "transitions": [dict(item) for item in self.transitions],
        }


def inline_delivery_state(delivery_status: str) -> VoiceCommandState:
    if delivery_status == "voice_command_delivered":
        return VoiceCommandState.DELIVERED
    if delivery_status == "voice_command_delivery_unverified":
        return VoiceCommandState.DELIVERY_UNVERIFIED
    return VoiceCommandState.DELIVERY_FAILED


def is_final_voice_response_route(route: str) -> bool:
    return str(route or "").strip() not in NON_FINAL_VOICE_RESPONSE_ROUTES


def should_speak_voice_result(*, pending: dict[str, Any]) -> bool:
    if not pending.get("pending"):
        return True
    reason = str(pending.get("reason") or pending.get("status") or "").strip()
    return is_final_voice_response_route(reason)


def watcher_command_state(*, pending: dict[str, Any], command_ok: bool) -> dict[str, Any]:
    machine = VoiceCommandStateMachine(
        state=VoiceCommandState.WATCHER_QUEUED,
        owner=VoiceDeliveryOwner.WATCHER,
    )
    machine.transition(VoiceCommandState.WATCHER_PROCESSING, event="watcher_picked_up")
    if pending.get("pending"):
        pending_reason = str(pending.get("reason") or pending.get("status") or "")
        target = (
            VoiceCommandState.AWAITING_CONFIRMATION
            if pending_reason in {"requires_confirmation", "outbound_confirmation"}
            else VoiceCommandState.AWAITING_ADAM
        )
        machine.transition(target, event="pending_saved")
    elif command_ok:
        machine.transition(VoiceCommandState.COMPLETED, event="watcher_result_ready")
    else:
        machine.transition(VoiceCommandState.DELIVERY_FAILED, event="invalid_command")
    return machine.snapshot()
