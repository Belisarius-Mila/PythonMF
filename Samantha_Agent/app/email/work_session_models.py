from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .action_case_models import ActionCaseAttachmentMeta, ReminderDraft


READ_BODY = "read_body"
BUILD_ACTION_CASE = "build_action_case"
SHOW_FULL_URLS = "show_full_urls"
BUILD_REMINDER_DRAFT = "build_reminder_draft"
SHOW_ATTACHMENT_METADATA = "show_attachment_metadata"

OPEN_URLS = "open_urls"
DOWNLOAD_ATTACHMENTS = "download_attachments"
SEND_EMAIL = "send_email"
DELETE_EMAIL = "delete_email"
MOVE_EMAIL = "move_email"
MARK_READ = "mark_read"
SAVE_FULL_BODY_TO_MEMORY = "save_full_body_to_memory"

ALLOWED_ACTIONS = frozenset(
    {
        READ_BODY,
        BUILD_ACTION_CASE,
        SHOW_FULL_URLS,
        BUILD_REMINDER_DRAFT,
        SHOW_ATTACHMENT_METADATA,
    }
)
DENIED_ACTIONS = frozenset(
    {
        OPEN_URLS,
        DOWNLOAD_ATTACHMENTS,
        SEND_EMAIL,
        DELETE_EMAIL,
        MOVE_EMAIL,
        MARK_READ,
        SAVE_FULL_BODY_TO_MEMORY,
    }
)
DEFAULT_DENIED_ACTIONS = DENIED_ACTIONS


@dataclass(frozen=True)
class EmailWorkSession:
    uid: str
    allowed_actions: frozenset[str]
    denied_actions: frozenset[str]
    confirmation_text: str
    created_at: datetime


@dataclass(frozen=True)
class EmailWorkSessionResult:
    uid: str
    summary_redacted: str
    action_case_text: str
    full_urls: tuple[str, ...]
    attachment_metadata: tuple[ActionCaseAttachmentMeta, ...]
    reminder_draft: ReminderDraft
    safety_note: str
