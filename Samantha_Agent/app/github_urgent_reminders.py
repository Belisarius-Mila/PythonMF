from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

import certifi

from app.urgent_reminders import MAX_DIRECT_REMINDER_CHARS, deliver_urgent_reminder


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_REPOSITORY_ENV = "SAMANTHA_GITHUB_INBOX_REPOSITORY"
GITHUB_TOKEN_ENV = "SAMANTHA_GITHUB_INBOX_TOKEN"
ISSUE_TITLE_PREFIX = "[Samantha Inbox] "
ISSUE_BODY_MARKER = "Samantha urgent reminder v1"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_ISSUES_PER_SYNC = 100

_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_DELIVERY_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")


class GitHubUrgentReminderError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubInboxConfig:
    repository: str
    token: str = field(repr=False)


@dataclass(frozen=True)
class GitHubInboxIssue:
    number: int
    delivery_id: str
    text: str
    created_at: str
    priority: str


RequestJson = Callable[[str, str, dict[str, Any] | None], Any]


class GitHubUrgentReminderClient:
    def __init__(
        self,
        config: GitHubInboxConfig,
        *,
        request_json: RequestJson | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        tls_context: ssl.SSLContext | None = None,
    ) -> None:
        self._config = config
        self._timeout_seconds = timeout_seconds
        self._request_json_override = request_json
        self._tls_context = tls_context or ssl.create_default_context(cafile=certifi.where())

    def list_open_issues(self) -> list[GitHubInboxIssue]:
        query = urllib.parse.urlencode(
            {
                "state": "open",
                "per_page": str(MAX_ISSUES_PER_SYNC),
                "sort": "created",
                "direction": "asc",
            }
        )
        payload = self._request_json(
            "GET",
            f"/repos/{self._config.repository}/issues?{query}",
            None,
        )
        if not isinstance(payload, list):
            raise GitHubUrgentReminderError("GitHub inbox nevrátil seznam Issues.")

        issues: list[GitHubInboxIssue] = []
        for raw_issue in payload:
            if not isinstance(raw_issue, dict) or "pull_request" in raw_issue:
                continue
            title = str(raw_issue.get("title", "") or "")
            if not title.startswith(ISSUE_TITLE_PREFIX):
                continue
            try:
                number = int(raw_issue.get("number", 0) or 0)
            except (TypeError, ValueError):
                number = 0
            if number < 1:
                raise GitHubUrgentReminderError("GitHub inbox obsahuje Issue bez platného čísla.")
            issues.append(parse_github_inbox_issue(number=number, body=str(raw_issue.get("body", "") or "")))
        return issues

    def close_issue(self, issue_number: int) -> None:
        payload = self._request_json(
            "PATCH",
            f"/repos/{self._config.repository}/issues/{issue_number}",
            {"state": "closed", "state_reason": "completed"},
        )
        if not isinstance(payload, dict):
            raise GitHubUrgentReminderError("GitHub nepotvrdil uzavření inboxové položky.")
        try:
            returned_number = int(payload.get("number", 0) or 0)
        except (TypeError, ValueError):
            returned_number = 0
        if returned_number != issue_number or str(payload.get("state", "")) != "closed":
            raise GitHubUrgentReminderError("GitHub vrátil nejednoznačnou účtenku uzavření Issue.")

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None) -> Any:
        if self._request_json_override is not None:
            return self._request_json_override(method, path, payload)

        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{GITHUB_API_BASE_URL}{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._config.token}",
                "Content-Type": "application/json",
                "User-Agent": "Samantha-GitHub-Inbox/1",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout_seconds,
                context=self._tls_context,
            ) as response:
                response_body = response.read()
        except urllib.error.HTTPError as exc:
            raise GitHubUrgentReminderError(f"GitHub inbox API vrátil HTTP {exc.code}.") from None
        except (OSError, urllib.error.URLError) as exc:
            raise GitHubUrgentReminderError(f"GitHub inbox teď není dostupný: {type(exc).__name__}.") from None
        try:
            return json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise GitHubUrgentReminderError("GitHub inbox vrátil neplatnou JSON odpověď.") from None


def github_inbox_config_from_environment(
    environment: Mapping[str, str] | None = None,
) -> GitHubInboxConfig | None:
    values = os.environ if environment is None else environment
    repository = str(values.get(GITHUB_REPOSITORY_ENV, "") or "").strip()
    token = str(values.get(GITHUB_TOKEN_ENV, "") or "").strip()
    if not repository and not token:
        return None
    if not repository or not token:
        raise GitHubUrgentReminderError(
            "GitHub inbox je nakonfigurovaný jen částečně; chybí repozitář nebo token."
        )
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise GitHubUrgentReminderError("GitHub inbox repozitář musí mít tvar vlastník/název.")
    return GitHubInboxConfig(repository=repository, token=token)


def parse_github_inbox_issue(*, number: int, body: str) -> GitHubInboxIssue:
    header, separator, text = body.partition("\n\n")
    lines = header.splitlines()
    if not separator or not lines or lines[0].strip() != ISSUE_BODY_MARKER:
        raise GitHubUrgentReminderError(f"GitHub inbox Issue #{number} nemá platný formát.")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        key, colon, value = line.partition(":")
        if not colon:
            raise GitHubUrgentReminderError(f"GitHub inbox Issue #{number} má neplatnou hlavičku.")
        fields[key.strip()] = value.strip()

    delivery_id = fields.get("delivery_id", "")
    priority = fields.get("priority", "urgent").casefold()
    created_at = fields.get("created_at", "")[:80]
    body_text = text.strip()
    if not _DELIVERY_ID_PATTERN.fullmatch(delivery_id):
        raise GitHubUrgentReminderError(f"GitHub inbox Issue #{number} má neplatné delivery_id.")
    if priority not in {"urgent", "normal"}:
        raise GitHubUrgentReminderError(f"GitHub inbox Issue #{number} má neplatnou prioritu.")
    if not body_text or len(body_text) > MAX_DIRECT_REMINDER_CHARS:
        raise GitHubUrgentReminderError(f"GitHub inbox Issue #{number} má neplatnou délku textu.")
    return GitHubInboxIssue(
        number=number,
        delivery_id=delivery_id,
        text=body_text,
        created_at=created_at,
        priority=priority,
    )


def sync_github_urgent_reminders(
    client: GitHubUrgentReminderClient,
    *,
    index_path: Path,
) -> dict[str, Any]:
    issues = client.list_open_issues()
    created_count = 0
    duplicate_count = 0
    closed_count = 0
    errors: list[str] = []
    for issue in issues:
        try:
            _reminder, created = deliver_urgent_reminder(
                issue.text,
                delivery_id=issue.delivery_id,
                created_at=issue.created_at,
                priority=issue.priority,
                index_path=index_path,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"Issue #{issue.number}: lokální doručení selhalo ({type(exc).__name__}).")
            continue
        if created:
            created_count += 1
        else:
            duplicate_count += 1
        try:
            client.close_issue(issue.number)
        except GitHubUrgentReminderError as exc:
            errors.append(f"Issue #{issue.number}: {exc}")
            continue
        closed_count += 1

    return {
        "ok": not errors,
        "configured": True,
        "pending_count": len(issues),
        "remaining_count": max(0, len(issues) - closed_count),
        "created_count": created_count,
        "duplicate_count": duplicate_count,
        "closed_count": closed_count,
        "error_count": len(errors),
        "errors": errors[:10],
    }


def sync_configured_github_urgent_reminders(
    *,
    index_path: Path,
    environment: Mapping[str, str] | None = None,
    client_factory: Callable[[GitHubInboxConfig], GitHubUrgentReminderClient] = GitHubUrgentReminderClient,
) -> dict[str, Any]:
    try:
        config = github_inbox_config_from_environment(environment)
        if config is None:
            return {
                "ok": True,
                "configured": False,
                "pending_count": 0,
                "remaining_count": 0,
                "created_count": 0,
                "duplicate_count": 0,
                "closed_count": 0,
                "error_count": 0,
                "errors": [],
            }
        return sync_github_urgent_reminders(client_factory(config), index_path=index_path)
    except GitHubUrgentReminderError as exc:
        return {
            "ok": False,
            "configured": True,
            "pending_count": 0,
            "remaining_count": 0,
            "created_count": 0,
            "duplicate_count": 0,
            "closed_count": 0,
            "error_count": 1,
            "errors": [str(exc)],
        }
