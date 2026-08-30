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

from app.quick_notes import GITHUB_SOURCE_KIND, MAX_DIRECT_QUICK_NOTE_CHARS, deliver_quick_note


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"
GITHUB_REPOSITORY_ENV = "SAMANTHA_GITHUB_QUICK_NOTES_REPOSITORY"
GITHUB_TOKEN_ENV = "SAMANTHA_GITHUB_QUICK_NOTES_TOKEN"
ISSUE_TITLE_PREFIX = "[Samantha QN] "
ISSUE_BODY_MARKER = "Samantha quick note v1"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_ISSUES_PER_SYNC = 100

_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_DELIVERY_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")


class GitHubQuickNoteError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubQuickNotesConfig:
    repository: str
    token: str = field(repr=False)


@dataclass(frozen=True)
class GitHubQuickNoteIssue:
    number: int
    delivery_id: str
    text: str
    created_at: str


RequestJson = Callable[[str, str, dict[str, Any] | None], Any]


class GitHubQuickNotesClient:
    def __init__(
        self,
        config: GitHubQuickNotesConfig,
        *,
        request_json: RequestJson | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        tls_context: ssl.SSLContext | None = None,
    ) -> None:
        self._config = config
        self._timeout_seconds = timeout_seconds
        self._request_json_override = request_json
        self._tls_context = tls_context or ssl.create_default_context(cafile=certifi.where())

    def list_open_issues(self) -> list[GitHubQuickNoteIssue]:
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
            raise GitHubQuickNoteError("GitHub QN inbox nevrátil seznam Issues.")

        issues: list[GitHubQuickNoteIssue] = []
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
                raise GitHubQuickNoteError("GitHub QN inbox obsahuje Issue bez platného čísla.")
            issues.append(
                parse_github_quick_note_issue(
                    number=number,
                    body=str(raw_issue.get("body", "") or ""),
                )
            )
        return issues

    def close_issue(self, issue_number: int) -> None:
        payload = self._request_json(
            "PATCH",
            f"/repos/{self._config.repository}/issues/{issue_number}",
            {"state": "closed", "state_reason": "completed"},
        )
        if not isinstance(payload, dict):
            raise GitHubQuickNoteError("GitHub nepotvrdil uzavření QN inboxové položky.")
        try:
            returned_number = int(payload.get("number", 0) or 0)
        except (TypeError, ValueError):
            returned_number = 0
        if returned_number != issue_number or str(payload.get("state", "")) != "closed":
            raise GitHubQuickNoteError("GitHub vrátil nejednoznačnou účtenku uzavření QN Issue.")

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
                "User-Agent": "Samantha-GitHub-Quick-Notes/1",
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
            raise GitHubQuickNoteError(f"GitHub QN inbox API vrátil HTTP {exc.code}.") from None
        except (OSError, urllib.error.URLError) as exc:
            raise GitHubQuickNoteError(
                f"GitHub QN inbox teď není dostupný: {type(exc).__name__}."
            ) from None
        try:
            return json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise GitHubQuickNoteError("GitHub QN inbox vrátil neplatnou JSON odpověď.") from None


def github_quick_notes_config_from_environment(
    environment: Mapping[str, str] | None = None,
) -> GitHubQuickNotesConfig | None:
    values = os.environ if environment is None else environment
    repository = str(values.get(GITHUB_REPOSITORY_ENV, "") or "").strip()
    token = str(values.get(GITHUB_TOKEN_ENV, "") or "").strip()
    if not repository and not token:
        return None
    if not repository or not token:
        raise GitHubQuickNoteError(
            "GitHub QN inbox je nakonfigurovaný jen částečně; chybí repozitář nebo token."
        )
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise GitHubQuickNoteError("GitHub QN inbox repozitář musí mít tvar vlastník/název.")
    return GitHubQuickNotesConfig(repository=repository, token=token)


def parse_github_quick_note_issue(*, number: int, body: str) -> GitHubQuickNoteIssue:
    header, separator, text = body.partition("\n\n")
    lines = header.splitlines()
    if not separator or not lines or lines[0].strip() != ISSUE_BODY_MARKER:
        raise GitHubQuickNoteError(f"GitHub QN Issue #{number} nemá platný formát.")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        key, colon, value = line.partition(":")
        if not colon:
            raise GitHubQuickNoteError(f"GitHub QN Issue #{number} má neplatnou hlavičku.")
        fields[key.strip()] = value.strip()

    delivery_id = fields.get("delivery_id", "")
    created_at = fields.get("created_at", "")[:80]
    body_text = text.strip()
    if not _DELIVERY_ID_PATTERN.fullmatch(delivery_id):
        raise GitHubQuickNoteError(f"GitHub QN Issue #{number} má neplatné delivery_id.")
    if not body_text or len(body_text) > MAX_DIRECT_QUICK_NOTE_CHARS:
        raise GitHubQuickNoteError(f"GitHub QN Issue #{number} má neplatnou délku textu.")
    return GitHubQuickNoteIssue(
        number=number,
        delivery_id=delivery_id,
        text=body_text,
        created_at=created_at,
    )


def sync_github_quick_notes(
    client: GitHubQuickNotesClient,
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
            _note, created = deliver_quick_note(
                issue.text,
                delivery_id=issue.delivery_id,
                created_at=issue.created_at,
                source_kind=GITHUB_SOURCE_KIND,
                index_path=index_path,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"Issue #{issue.number}: lokální doručení QN selhalo ({type(exc).__name__}).")
            continue
        if created:
            created_count += 1
        else:
            duplicate_count += 1
        try:
            client.close_issue(issue.number)
        except GitHubQuickNoteError as exc:
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


def sync_configured_github_quick_notes(
    *,
    index_path: Path,
    environment: Mapping[str, str] | None = None,
    client_factory: Callable[[GitHubQuickNotesConfig], GitHubQuickNotesClient] = GitHubQuickNotesClient,
) -> dict[str, Any]:
    try:
        config = github_quick_notes_config_from_environment(environment)
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
        return sync_github_quick_notes(client_factory(config), index_path=index_path)
    except GitHubQuickNoteError as exc:
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
