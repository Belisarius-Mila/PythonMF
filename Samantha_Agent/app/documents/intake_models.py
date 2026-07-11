"""Shared domain model for document intake items from every source."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from app.documents.vault import safe_text


class DocumentIntakeSource(str, Enum):
    DOWNLOADS = "downloads"
    EMAIL = "email"
    MOBILE = "mobile"
    LOCAL_INBOX = "local_inbox"


class DocumentIntakeState(str, Enum):
    READY = "ready"
    PROBLEM = "problem"
    MISSING = "missing"
    EMPTY = "empty"


class DocumentIntakeAction(str, Enum):
    OPEN_SCANDOCU = "open_scandocu"
    OPEN_EMAIL_PROCESSING = "open_email_processing"
    MANUAL = "manual"


@dataclass(frozen=True)
class DocumentIntakeSourcePolicy:
    label: str
    priority: int
    action: DocumentIntakeAction
    action_label: str


SOURCE_POLICIES: dict[DocumentIntakeSource, DocumentIntakeSourcePolicy] = {
    DocumentIntakeSource.DOWNLOADS: DocumentIntakeSourcePolicy(
        label="Downloads",
        priority=10,
        action=DocumentIntakeAction.OPEN_SCANDOCU,
        action_label="ScanDocu",
    ),
    DocumentIntakeSource.EMAIL: DocumentIntakeSourcePolicy(
        label="E-mail work queue",
        priority=20,
        action=DocumentIntakeAction.OPEN_EMAIL_PROCESSING,
        action_label="E-maily",
    ),
    DocumentIntakeSource.MOBILE: DocumentIntakeSourcePolicy(
        label="Mobilní sken",
        priority=30,
        action=DocumentIntakeAction.MANUAL,
        action_label="",
    ),
    DocumentIntakeSource.LOCAL_INBOX: DocumentIntakeSourcePolicy(
        label="Lokální inbox",
        priority=40,
        action=DocumentIntakeAction.MANUAL,
        action_label="",
    ),
}

STATE_LABELS: dict[DocumentIntakeState, str] = {
    DocumentIntakeState.READY: "čeká",
    DocumentIntakeState.PROBLEM: "problém",
    DocumentIntakeState.MISSING: "chybí",
    DocumentIntakeState.EMPTY: "prázdné",
}


@dataclass(frozen=True)
class DocumentIntakeItem:
    source: DocumentIntakeSource
    title: str
    meta: str = ""
    source_key: str = ""

    @classmethod
    def build(
        cls,
        *,
        source: DocumentIntakeSource,
        title: str,
        meta: str = "",
        source_key: str = "",
    ) -> "DocumentIntakeItem":
        return cls(
            source=source,
            title=safe_text(str(title or "Dokumentový vstup"))[:180],
            meta=safe_text(str(meta or ""))[:240],
            source_key=safe_text(str(source_key or ""))[:500],
        )

    @property
    def intake_ref(self) -> str:
        identity = self.source_key or f"{self.title}|{self.meta}"
        digest = hashlib.sha256(f"{self.source.value}|{identity}".encode("utf-8")).hexdigest()[:16]
        return f"intakeref-{digest}"

    def to_source_item(self) -> dict[str, str]:
        return {
            "intake_ref": self.intake_ref,
            "title": self.title,
            "meta": self.meta,
        }


@dataclass(frozen=True)
class DocumentIntakeSourceSnapshot:
    source: DocumentIntakeSource
    state: DocumentIntakeState
    total_count: int
    next_action: str
    items: tuple[DocumentIntakeItem, ...] = ()

    def __post_init__(self) -> None:
        if self.total_count < len(self.items):
            raise ValueError("Document intake total_count nesmí být menší než počet položek.")
        if any(item.source is not self.source for item in self.items):
            raise ValueError("Document intake položka nepatří do zdroje snapshotu.")

    @property
    def policy(self) -> DocumentIntakeSourcePolicy:
        return SOURCE_POLICIES[self.source]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.source.value,
            "label": self.policy.label,
            "count": max(0, int(self.total_count)),
            "status": self.state.value,
            "next_action": safe_text(self.next_action)[:240],
            "items": [item.to_source_item() for item in self.items],
        }


def unified_intake_items(
    snapshots: Iterable[DocumentIntakeSourceSnapshot],
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    ranked: list[tuple[float, dict[str, Any]]] = []
    for snapshot in snapshots:
        policy = snapshot.policy
        for index, item in enumerate(snapshot.items):
            ranked.append((
                policy.priority + index / 100,
                {
                    "intake_ref": item.intake_ref,
                    "source_id": snapshot.source.value,
                    "source_label": policy.label,
                    "source_status": snapshot.state.value,
                    "source_status_label": STATE_LABELS[snapshot.state],
                    "title": item.title,
                    "meta": item.meta,
                    "next_action": safe_text(snapshot.next_action)[:240],
                    "action_kind": policy.action.value,
                    "action_label": policy.action_label,
                },
            ))
    ranked.sort(key=lambda entry: entry[0])
    return [item for _, item in ranked[: max(1, limit)]]
