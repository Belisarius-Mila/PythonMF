from __future__ import annotations

import re


EMAIL_REDACTION = "[e-mail redigovan]"
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def redact_email_addresses(text: str) -> str:
    return EMAIL_PATTERN.sub(EMAIL_REDACTION, text)
