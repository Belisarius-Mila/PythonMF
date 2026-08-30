from __future__ import annotations

import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.github_quick_notes import (
    GITHUB_REPOSITORY_ENV,
    GITHUB_TOKEN_ENV,
    GitHubQuickNoteError,
    GitHubQuickNotesClient,
    GitHubQuickNotesConfig,
    github_quick_notes_config_from_environment,
    parse_github_quick_note_issue,
    sync_configured_github_quick_notes,
    sync_github_quick_notes,
)
from app.quick_notes import deliver_quick_note


VALID_BODY = """Samantha quick note v1
delivery_id: samantha-qn-20260830213000123
created_at: 2026-08-30T21:30:00+02:00

Návrh technického řešení.
Druhý řádek zůstane zachovaný.
"""


class GitHubQuickNotesTests(unittest.TestCase):
    def test_environment_config_is_optional_but_not_partial(self) -> None:
        self.assertIsNone(github_quick_notes_config_from_environment({}))

        with self.assertRaisesRegex(GitHubQuickNoteError, "jen částečně"):
            github_quick_notes_config_from_environment(
                {GITHUB_REPOSITORY_ENV: "owner/quick-notes-inbox"}
            )
        with self.assertRaisesRegex(GitHubQuickNoteError, "vlastník/název"):
            github_quick_notes_config_from_environment(
                {
                    GITHUB_REPOSITORY_ENV: "invalid repository",
                    GITHUB_TOKEN_ENV: "secret-token",
                }
            )

        config = github_quick_notes_config_from_environment(
            {
                GITHUB_REPOSITORY_ENV: "owner/quick-notes-inbox",
                GITHUB_TOKEN_ENV: "secret-token",
            }
        )

        self.assertEqual(
            config,
            GitHubQuickNotesConfig(
                repository="owner/quick-notes-inbox",
                token="secret-token",
            ),
        )
        self.assertNotIn("secret-token", repr(config))

    def test_issue_parser_validates_protocol_and_preserves_multiline_text(self) -> None:
        parsed = parse_github_quick_note_issue(number=17, body=VALID_BODY)

        self.assertEqual(parsed.number, 17)
        self.assertEqual(parsed.delivery_id, "samantha-qn-20260830213000123")
        self.assertEqual(
            parsed.text,
            "Návrh technického řešení.\nDruhý řádek zůstane zachovaný.",
        )

        with self.assertRaisesRegex(GitHubQuickNoteError, "platný formát"):
            parse_github_quick_note_issue(number=18, body="Jiný obsah")
        with self.assertRaisesRegex(GitHubQuickNoteError, "delivery_id"):
            parse_github_quick_note_issue(
                number=19,
                body=VALID_BODY.replace("samantha-qn-20260830213000123", "invalid id"),
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
                        "title": "[Samantha QN] pull request",
                        "body": VALID_BODY,
                        "pull_request": {},
                    },
                    {
                        "number": 3,
                        "title": "[Samantha QN] samantha-qn-20260830213000123",
                        "body": VALID_BODY,
                    },
                ]
            return {"number": 3, "state": "closed"}

        client = GitHubQuickNotesClient(
            GitHubQuickNotesConfig(repository="owner/inbox", token="secret-token"),
            request_json=request_json,
        )

        issues = client.list_open_issues()
        client.close_issue(3)

        self.assertEqual([issue.number for issue in issues], [3])
        self.assertEqual(calls[1][0], "PATCH")
        self.assertEqual(calls[1][2], {"state": "closed", "state_reason": "completed"})

        mismatched_client = GitHubQuickNotesClient(
            GitHubQuickNotesConfig(repository="owner/inbox", token="secret-token"),
            request_json=lambda _method, _path, _payload: {"number": 99, "state": "closed"},
        )
        with self.assertRaisesRegex(GitHubQuickNoteError, "nejednoznačnou"):
            mismatched_client.close_issue(3)

    def test_sync_delivers_as_github_fallback_then_closes_issue(self) -> None:
        closed: list[int] = []
        client = _FakeClient(closed=closed)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "quick_notes" / "index.json"
            result = sync_github_quick_notes(client, index_path=index_path)
            stored = json.loads(index_path.read_text(encoding="utf-8"))["notes"]

        self.assertTrue(result["ok"])
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(result["closed_count"], 1)
        self.assertEqual(result["remaining_count"], 0)
        self.assertEqual(closed, [17])
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["delivery_id"], "samantha-qn-20260830213000123")
        self.assertEqual(stored[0]["source_kind"], "github_fallback")
        self.assertNotIn("Návrh", json.dumps(result, ensure_ascii=False))

    def test_failed_close_retries_as_duplicate_without_copying_note(self) -> None:
        closed: list[int] = []
        client = _FakeClient(closed=closed, fail_close=True)

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "quick_notes" / "index.json"
            first = sync_github_quick_notes(client, index_path=index_path)
            client.fail_close = False
            second = sync_github_quick_notes(client, index_path=index_path)
            stored = json.loads(index_path.read_text(encoding="utf-8"))["notes"]

        self.assertFalse(first["ok"])
        self.assertEqual(first["created_count"], 1)
        self.assertEqual(first["remaining_count"], 1)
        self.assertTrue(second["ok"])
        self.assertEqual(second["duplicate_count"], 1)
        self.assertEqual(second["closed_count"], 1)
        self.assertEqual(closed, [17])
        self.assertEqual(len(stored), 1)

    def test_direct_delivery_wins_race_and_conflicting_id_stays_open(self) -> None:
        closed: list[int] = []

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "quick_notes" / "index.json"
            deliver_quick_note(
                "Návrh technického řešení.\nDruhý řádek zůstane zachovaný.",
                delivery_id="samantha-qn-20260830213000123",
                index_path=index_path,
            )
            duplicate = sync_github_quick_notes(_FakeClient(closed=closed), index_path=index_path)
            conflict = sync_github_quick_notes(
                _FakeClient(
                    closed=closed,
                    body=VALID_BODY.replace(
                        "Návrh technického řešení.",
                        "Jiný text se stejným identifikátorem.",
                    ),
                ),
                index_path=index_path,
            )
            stored = json.loads(index_path.read_text(encoding="utf-8"))["notes"]

        self.assertTrue(duplicate["ok"])
        self.assertEqual(duplicate["duplicate_count"], 1)
        self.assertEqual(closed, [17])
        self.assertFalse(conflict["ok"])
        self.assertEqual(conflict["closed_count"], 0)
        self.assertEqual(conflict["remaining_count"], 1)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["source_kind"], "direct_tailscale")

    def test_unconfigured_sync_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            index_path = Path(temp_dir) / "quick_notes" / "index.json"
            result = sync_configured_github_quick_notes(
                index_path=index_path,
                environment={},
                client_factory=lambda _config: self.fail("Klient se nesmí vytvořit."),
            )

        self.assertTrue(result["ok"])
        self.assertFalse(result["configured"])
        self.assertEqual(result["remaining_count"], 0)
        self.assertFalse(index_path.exists())

    def test_http_client_uses_tls_context_and_redacts_http_error(self) -> None:
        config = GitHubQuickNotesConfig(repository="owner/inbox", token="secret-token")
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        response = Mock()
        response.read.return_value = b"[]"
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)

        with patch("app.github_quick_notes.urllib.request.urlopen", return_value=response) as urlopen:
            client = GitHubQuickNotesClient(config, tls_context=tls_context)
            self.assertEqual(client.list_open_issues(), [])

        self.assertIs(urlopen.call_args.kwargs["context"], tls_context)

        from urllib.error import HTTPError

        with patch(
            "app.github_quick_notes.urllib.request.urlopen",
            side_effect=HTTPError("https://api.github.com", 401, "Unauthorized", {}, None),
        ):
            client = GitHubQuickNotesClient(config, tls_context=tls_context)
            with self.assertRaises(GitHubQuickNoteError) as caught:
                client.list_open_issues()

        self.assertIn("HTTP 401", str(caught.exception))
        self.assertNotIn("secret-token", str(caught.exception))


class _FakeClient:
    def __init__(
        self,
        *,
        closed: list[int],
        fail_close: bool = False,
        body: str = VALID_BODY,
    ) -> None:
        self.closed = closed
        self.fail_close = fail_close
        self.body = body

    def list_open_issues(self):  # type: ignore[no-untyped-def]
        return [parse_github_quick_note_issue(number=17, body=self.body)]

    def close_issue(self, issue_number: int) -> None:
        if self.fail_close:
            raise GitHubQuickNoteError("simulované selhání uzavření")
        self.closed.append(issue_number)


if __name__ == "__main__":
    unittest.main()
