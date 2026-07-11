"""Shared identity and state model for read-only email work queues."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from app.documents.vault import safe_text


class EmailWorkState(str, Enum):
    NEW = "new"
    QUEUED = "queued"
    TRASH_REVIEW = "trash_review"


class EmailWorkAction(str, Enum):
    NONE = ""
    PROCESS = "process"
    TRASH_REQUESTED = "trash_requested"


def email_processing_stable_key(provider: str, folder: str, uid: str) -> str:
    provider_key = " ".join(provider.casefold().split())
    folder_key = " ".join((folder or "INBOX").casefold().split())
    uid_key = str(uid).strip()
    if not provider_key or not uid_key:
        return ""
    return "|".join([provider_key, folder_key, uid_key])


def email_processing_is_inbound_work_folder(folder: str) -> bool:
    folder_key = " ".join((folder or "INBOX").casefold().split())
    outbound_folders = {
        "sent",
        "sent messages",
        "sent mail",
        "odeslané",
        "odeslane",
        "odeslaná pošta",
        "odeslana posta",
        "outbox",
        "drafts",
        "koncepty",
    }
    return folder_key not in outbound_folders


def email_processing_legacy_item_id(
    category: str,
    provider: str,
    folder: str,
    uid: str,
    date: str,
    subject: str,
) -> str:
    raw = "|".join([category, provider, folder, uid, date, subject])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def email_processing_item_id(
    category: str,
    provider: str,
    folder: str,
    uid: str,
    date: str,
    subject: str,
) -> str:
    stable_key = email_processing_stable_key(provider, folder, uid)
    if stable_key:
        return hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]
    return email_processing_legacy_item_id(category, provider, folder, uid, date, subject)


def email_processing_item_lookup_keys(item: Mapping[str, Any]) -> set[str]:
    keys = {
        str(item.get("id", "")).strip(),
        str(item.get("legacy_id", "")).strip(),
        str(item.get("source_key", "")).strip(),
        str(item.get("work_ref", "")).strip(),
    }
    stable_key = email_processing_stable_key(
        str(item.get("provider", "")),
        str(item.get("folder", "")),
        str(item.get("uid", "")),
    )
    if stable_key:
        keys.add(stable_key)
    computed_id = email_processing_item_id(
        str(item.get("category", "")),
        str(item.get("provider", "")),
        str(item.get("folder", "")),
        str(item.get("uid", "")),
        str(item.get("date", "")),
        str(item.get("subject", "")),
    )
    if computed_id:
        keys.add(computed_id)
    legacy_id = email_processing_legacy_item_id(
        str(item.get("category", "")),
        str(item.get("provider", "")),
        str(item.get("folder", "")),
        str(item.get("uid", "")),
        str(item.get("date", "")),
        str(item.get("subject", "")),
    )
    if legacy_id:
        keys.add(legacy_id)
    return {key for key in keys if key}


def classify_email_processing_category(subject: str, sender: str = "") -> str:
    value = f"{subject} {sender}".casefold()
    invoice_value = any(
        token in value
        for token in (
            "faktura",
            "invoice",
            "daňový doklad",
            "danovy doklad",
            "objedn",
            "platba",
            "zaplac",
            "booking",
            "temu",
            "apple",
            "doruč",
            "doruc",
            "balík",
            "balicek",
            "zásilk",
            "zasilk",
            "eshop",
            "e-shop",
        )
    )
    if any(
        token in value
        for token in (
            "pojišt",
            "pojist",
            "smlouv",
            "zelen",
            "karta",
            "generali",
            "kooperativa",
            "čpp",
            "cpp",
        )
    ):
        return "pojištění/smlouvy"
    if invoice_value:
        return "faktury/e-shopy"
    if any(token in value for token in ("finanční správa", "financni sprava", "daneelektronicky", "fs.mfcr.cz", "fs.gov.cz")):
        return "úřady/daně"
    if any(token in value for token in ("úřad", "urad", "finanční", "financni", "datov", "správa", "sprava")):
        return "úřady/daně"
    return "ostatní"


def email_processing_batch_groups(item: dict[str, Any]) -> list[dict[str, str]]:
    text = " ".join(
        [
            str(item.get("sender", "")),
            str(item.get("subject", "")),
            str(item.get("reason", "")),
            " ".join(str(tag) for tag in (item.get("worklist_tags") or []) if str(tag).strip()),
        ]
    ).casefold()
    category = str(item.get("category", "")).casefold()
    tags = {str(tag).strip() for tag in (item.get("worklist_tags") or []) if str(tag).strip()}
    groups: list[dict[str, str]] = []

    def add(group_id: str, label: str) -> None:
        if not any(group["id"] == group_id for group in groups):
            groups.append({"id": group_id, "label": label})

    if "true_tax_office" in tags or any(
        needle in text for needle in ("daneelektronicky", "fs.mfcr.cz", "fs.gov.cz", "finanční správa")
    ):
        add("tax_office", "Finanční správa")
    if "true_vak" in tags or "vakmb" in text or "vodovod" in text or "kanaliz" in text:
        add("vak", "VAK")
    amount_scan = item.get("amount_scan")
    max_amount = 0.0
    if isinstance(amount_scan, dict):
        try:
            max_amount = float(amount_scan.get("max_amount_czk", 0) or 0)
        except (TypeError, ValueError):
            max_amount = 0.0
    if "invoice_over_2000" in tags or max_amount > 2000:
        add("invoice_over_2000", "Faktury nad 2000 Kč")
    if category == "faktury/e-shopy":
        add("invoice", "Faktury / e-shopy")
    if int(item.get("pdf_attachment_count", 0) or 0) > 0:
        add("pdf", "S PDF přílohou")
    if int(item.get("large_pdf_attachment_count", 0) or 0) > 0:
        add("large_pdf", "Velké PDF")
    if not groups:
        add("other", "Ostatní")
    return groups



@dataclass(frozen=True)
class EmailWorkItem:
    provider: str
    folder: str
    uid: str
    item_id: str
    legacy_id: str
    source_key: str
    state: EmailWorkState
    action: EmailWorkAction

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "EmailWorkItem":
        provider = safe_text(str(item.get("provider", "")))[:80]
        folder = safe_text(str(item.get("folder", "") or "INBOX"))[:120]
        uid = safe_text(str(item.get("uid", "")))[:120]
        category = str(item.get("category", ""))
        date = str(item.get("date", ""))
        subject = str(item.get("subject", ""))
        source_key = str(item.get("source_key", "")).strip() or email_processing_stable_key(provider, folder, uid)
        item_id = str(item.get("id", "")).strip() or email_processing_item_id(
            category, provider, folder, uid, date, subject
        )
        legacy_id = str(item.get("legacy_id", "")).strip() or email_processing_legacy_item_id(
            category, provider, folder, uid, date, subject
        )
        raw_action = str(item.get("action", ""))
        try:
            action = EmailWorkAction(raw_action)
        except ValueError:
            action = EmailWorkAction.NONE
        if bool(item.get("is_new_header")):
            state = EmailWorkState.NEW
        elif action is EmailWorkAction.TRASH_REQUESTED:
            state = EmailWorkState.TRASH_REVIEW
        else:
            state = EmailWorkState.QUEUED
        return cls(
            provider=provider,
            folder=folder,
            uid=uid,
            item_id=item_id,
            legacy_id=legacy_id,
            source_key=source_key,
            state=state,
            action=action,
        )

    @property
    def work_ref(self) -> str:
        identity = self.source_key or self.item_id or self.legacy_id
        digest = hashlib.sha256(f"email-work|{identity}".encode("utf-8")).hexdigest()[:16]
        return f"emailworkref-{digest}"

    def enrich_mapping(self, item: Mapping[str, Any]) -> dict[str, Any]:
        enriched = dict(item)
        enriched.update({
            "id": self.item_id,
            "legacy_id": self.legacy_id,
            "source_key": self.source_key,
            "work_ref": self.work_ref,
            "work_state": self.state.value,
            "work_action": self.action.value,
        })
        return enriched


def normalize_email_work_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return EmailWorkItem.from_mapping(item).enrich_mapping(item)
