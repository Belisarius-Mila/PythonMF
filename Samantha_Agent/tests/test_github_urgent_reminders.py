from __future__ import annotations

import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.github_urgent_reminders import (
    GITHUB_REPOSITORY_ENV,
    GITHUB_TOKEN_ENV,
    GitHubInboxConfig,
    GitHubUrgentReminderClient,
    GitHubUrgentReminderError,
    github_inbox_config_from_environment,
    parse_github_inbox_issue,
    sync_configured_github_urgent_reminders,
    sync_github_urgent_reminders,
)


VALID_BODY = """Samantha urgent reminder v1
delivery_id: 12345678-abcd-4321-abcd-123456789abc
created_at: 2026-08-30T10:30:00+02:00
priority: urgent

Zavolat zítra do servisu.
"""


class GitHubUrgentRemindersTests(unittest.TestCase):
    def test_environment_config_is_optional_but_not_partial(self) -> None:
        self.assertIsNone(github_inbox_config_from_environment({}))

        with self.assertRaisesRegex(GitHubUrgentReminderError, "jen částečně"):
            github_inbox_config_from_environment({GITHUB_REPOSITORY_ENV: "owner/inbox"})
        with self.assertRaisesRegex(GitHubUrgentReminderError, "vlastník/název"):
            github_inbox_config_from_environment(
                {
                    GITHUB_REPOSITORY_ENV: "invalid repository",
                    GITHUB_TOKEN_ENV: "secret-token",
                }
            )

        config = github_inbox_config_from_environment(
            {
                GITHUB_REPOSITORY_ENV: "owner/inbox",
                GITHUB_TOKEN_ENV: "secret-token",
            }
        )

        self.assertEqual(config, GitHubInboxConfig(repository="owner/inbox", token="secret-token"))
        self.assertNotIn("secret-token", repr(config))

    def test_issue_parser_validates_protocol_and_preserves_multiline_text(self) -> None:
        parsed = parse_github_inbox_issue(number=17, body=VALID_BODY)

        self.assertEqual(parsed.number, 17)
        self.assertEqual(parsed.delivery_id, "12345678-abcd-4321-abcd-123456789abc")
        self.assertEqual(parsed.priority, "urgent")
        self.assertEqual(parsed.text, "Zavolat zítra do servisu.")

        with self.assertRaisesRegex(GitHubUrgentReminderError, "platný formát"):
            parse_github_inbox_issue(number=18, body="Jiný obsah")
        with self.assertRaisesRegex(GitHubUrgentReminderError, "delivery_id"):
            parse_github_inbox_issue(
                number=19,
                body=VALID_BODY.replace(
                    "12345678-abcd-4321-abcd-123456789abc",
                    "invalid id",
                ),
            )

    def test_client_filters_unrelated_issues_and_requires_exact_close_receipt(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def request_json(method: str, path: str, payload: dict[str, object] | None) -> object:
            calls.append((method, path, payload))
            if method == "GET":
                return [
                    {"number": 1, "title": "Jiná Issue", "body": ""},
                    {
                        "number": 2,
                        "title": "[Samantha Inbox] pull request",
                        "body": VALID_BODY,
                        "pull_request": {},
                    },
                    {
                        "number": 3,
                        "title": "[Samantha Inbox] 12345678-abcd-4321-abcd-123456789abc",
                        "body": VALID_BODY,
                    },
                ]
            return {"number": 3, "state": "closed"}

        client = GitHubUrgentReminderClient(
            GitHubInboxConfig(repository="owner/inbox", token="secret-token"),
            request_json=request_json,
        )

        issues = client.list_open_issues()
        client.close_issue(3)

        self.assertEqual([issue.number for issue in issues], [3])
        self.assertEqual(calls[1][0], "PATCH")
        self.assertEqual(calls[1][2], {"state": "closed", "state_reason": "completed"})

        mismatched_client = GitHubUrgentReminderClient(
            GitHubInboxConfig(repository="owner/inbox", token="secret-token"),
            request_json=lambda _method, _path, _payload: {"number": 99, "state": "closed"},
        )
        with self.assertRaisesRegex(GitHubUrgentReminderError, "nejednoznačnou"):
            mismatched_client.close_issue(3)

    def test_sync_delivers_then_closes_issue(self) -> None:
        closed: list[int] = []
        client = _FakeClient(closed=closed)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "urgent_reminders" / "index.json"
            result = sync_github_urgent_reminders(client, index_path=index_path)
            stored = json.loads(index_path.read_text(encoding="utf-8"))["reminders"]

        self.assertTrue(result["ok"])
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(result["closed_count"], 1)
        self.assertEqual(result["remaining_count"], 0)
        self.assertEqual(closed, [17])
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["delivery_id"], "12345678-abcd-4321-abcd-123456789abc")
        self.assertNotIn("Zavolat", json.dumps(result, ensure_ascii=False))

    def test_failed_close_retries_as_duplicate_without_losing_or_copying_reminder(self) -> None:
        closed: list[int] = []
        client = _FakeClient(closed=closed, fail_close=True)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "urgent_reminders" / "index.json"
            first = sync_github_urgent_reminders(client, index_path=index_path)
            client.fail_close = False
            second = sync_github_urgent_reminders(client, index_path=index_path)
            stored = json.loads(index_path.read_text(encoding="utf-8"))["reminders"]

        self.assertFalse(first["ok"])
        self.assertEqual(first["created_count"], 1)
        self.assertEqual(first["closed_count"], 0)
        self.assertEqual(first["remaining_count"], 1)
        self.assertTrue(second["ok"])
        self.assertEqual(second["created_count"], 0)
        self.assertEqual(second["duplicate_count"], 1)
        self.assertEqual(second["closed_count"], 1)
        self.assertEqual(closed, [17])
        self.assertEqual(len(stored), 1)

    def test_unconfigured_sync_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "urgent_reminders" / "index.json"
            result = sync_configured_github_urgent_reminders(
                index_path=index_path,
                environment={},
                client_factory=lambda _config: self.fail("Klient se nesmí vytvořit."),
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["configured"])
        self.assertEqual(result["remaining_count"], 0)
        self.assertFalse(index_path.exists())

    def test_http_client_uses_injected_tls_context_and_redacts_http_error(self) -> None:
        config = GitHubInboxConfig(repository="owner/inbox", token="secret-token")
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        response = Mock()
        response.read.return_value = b"[]"
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)

        with patch("app.github_urgent_reminders.urllib.request.urlopen", return_value=response) as urlopen:
            client = GitHubUrgentReminderClient(config, tls_context=tls_context)
            self.assertEqual(client.list_open_issues(), [])

        self.assertIs(urlopen.call_args.kwargs["context"], tls_context)

        from urllib.error import HTTPError

        with patch(
            "app.github_urgent_reminders.urllib.request.urlopen",
            side_effect=HTTPError("https://api.github.com", 401, "Unauthorized", {}, None),
        ):
            client = GitHubUrgentReminderClient(config, tls_context=tls_context)
            with self.assertRaises(GitHubUrgentReminderError) as caught:
                client.list_open_issues()

        self.assertIn("HTTP 401", str(caught.exception))
        self.assertNotIn("secret-token", str(caught.exception))


class _FakeClient:
    def __init__(self, *, closed: list[int], fail_close: bool = False) -> None:
        self.closed = closed
        self.fail_close = fail_close

    def list_open_issues(self):  # type: ignore[no-untyped-def]
        return [parse_github_inbox_issue(number=17, body=VALID_BODY)]

    def close_issue(self, issue_number: int) -> None:
        if self.fail_close:
            raise GitHubUrgentReminderError("simulované selhání uzavření")
        self.closed.append(issue_number)


if __name__ == "__main__":
    unittest.main()
