from __future__ import annotations

from dataclasses import dataclass

from .action_case_models import ActionCaseAttachmentMeta, ActionCaseLinkDomain, ReminderDraft


@dataclass(frozen=True)
class TriageEmailItem:
    uid: str
    date: str
    sender: str
    subject: str
    summary_redacted: str
    priority: str
    category: str
    has_deadline: bool
    has_action: bool
    is_newsletter: bool
    deadline_texts: tuple[str, ...]
    action_items: tuple[str, ...]
    link_domains: tuple[ActionCaseLinkDomain, ...]
    attachments: tuple[ActionCaseAttachmentMeta, ...]
    reminder_draft: ReminderDraft
    case_id: str


@dataclass(frozen=True)
class TriageResult:
    important_emails: tuple[TriageEmailItem, ...]
    deadline_emails: tuple[TriageEmailItem, ...]
    action_emails: tuple[TriageEmailItem, ...]
    newsletter_emails: tuple[TriageEmailItem, ...]
    case_candidates: tuple[TriageEmailItem, ...]
    all_items: tuple[TriageEmailItem, ...]
