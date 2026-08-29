from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.communication.mmtx_pages_deploy import (
    GITHUB_REPOSITORY,
    MmtxPagesDeployError,
    _default_smoke_fetcher,
    publish_mmtx_pages_current_main,
)


HEAD = "a" * 40


class FakeRunner:
    def __init__(
        self,
        *,
        already_deployed: bool = False,
        origin_head: str = HEAD,
        deployment_ready_after_queries: int = 2,
    ):
        self.already_deployed = already_deployed
        self.origin_head = origin_head
        self.deployment_ready_after_queries = deployment_ready_after_queries
        self.calls: list[tuple[str, ...]] = []
        self.deployment_queries = 0

    def __call__(self, args, **_kwargs):
        command = tuple(str(item) for item in args)
        self.calls.append(command)
        if command[-2:] == ("branch", "--show-current"):
            output = "main\n"
        elif "status" in command and "--porcelain=v1" in command:
            output = ""
        elif command[-2:] == ("rev-parse", "HEAD"):
            output = HEAD + "\n"
        elif command[-2:] == ("rev-parse", "origin/main"):
            output = self.origin_head + "\n"
        elif command[:3] == ("/usr/local/bin/gh", "api", f"repos/{GITHUB_REPOSITORY}/deployments?environment=github-pages&per_page=20"):
            self.deployment_queries += 1
            deployed = (
                self.already_deployed
                or self.deployment_queries >= self.deployment_ready_after_queries
            )
            output = json.dumps([{"id": 55, "sha": HEAD}] if deployed else [])
        elif command[:3] == (
            "/usr/local/bin/gh",
            "api",
            f"repos/{GITHUB_REPOSITORY}/deployments/55/statuses",
        ):
            output = json.dumps(
                [
                    {
                        "state": "success",
                        "environment_url": "https://belisarius-mila.github.io/PythonMF/",
                    }
                ]
            )
        elif command[:3] == ("/usr/local/bin/gh", "workflow", "run"):
            output = "https://github.com/Belisarius-Mila/PythonMF/actions/runs/12345\n"
        elif command[:3] == ("/usr/local/bin/gh", "run", "watch"):
            output = "completed\n"
        elif command[:3] == ("/usr/local/bin/gh", "run", "view"):
            output = json.dumps(
                {
                    "databaseId": 12345,
                    "headSha": HEAD,
                    "status": "completed",
                    "conclusion": "success",
                    "url": "https://github.com/Belisarius-Mila/PythonMF/actions/runs/12345",
                }
            )
        else:
            raise AssertionError(f"Unexpected command: {command}")
        return subprocess.CompletedProcess(args, 0, output, "")


class MmtxPagesDeployTests(unittest.TestCase):
    def test_publish_triggers_exact_workflow_and_verifies_deployment_and_smoke(self) -> None:
        runner = FakeRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = publish_mmtx_pages_current_main(
                source_repo=Path(temp_dir),
                runner=runner,
                smoke_fetcher=lambda _url: 200,
                sleeper=lambda _seconds: None,
            )

        self.assertEqual(result["status"], "deployed")
        self.assertEqual(result["main_short"], HEAD[:12])
        self.assertEqual(result["workflow_run_id"], 12345)
        self.assertEqual(result["deployment_id"], 55)
        self.assertEqual(result["smoke_http_status"], 200)
        self.assertTrue(
            any(call[:3] == ("/usr/local/bin/gh", "workflow", "run") for call in runner.calls)
        )

    def test_current_successful_deployment_is_not_started_twice(self) -> None:
        runner = FakeRunner(already_deployed=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = publish_mmtx_pages_current_main(
                source_repo=Path(temp_dir),
                runner=runner,
                smoke_fetcher=lambda _url: 200,
                sleeper=lambda _seconds: None,
            )

        self.assertEqual(result["status"], "already_deployed")
        self.assertEqual(result["workflow_run_id"], 0)
        self.assertFalse(any("workflow" in call for call in runner.calls))

    def test_origin_mismatch_fails_before_any_workflow(self) -> None:
        runner = FakeRunner(origin_head="b" * 40)
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(MmtxPagesDeployError):
                publish_mmtx_pages_current_main(
                    source_repo=Path(temp_dir),
                    runner=runner,
                    smoke_fetcher=lambda _url: 200,
                    sleeper=lambda _seconds: None,
                )

        self.assertFalse(any("workflow" in call for call in runner.calls))

    def test_success_status_may_arrive_after_workflow_completion(self) -> None:
        runner = FakeRunner(deployment_ready_after_queries=4)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = publish_mmtx_pages_current_main(
                source_repo=Path(temp_dir),
                runner=runner,
                smoke_fetcher=lambda _url: 200,
                deployment_attempts=5,
                sleeper=lambda _seconds: None,
            )

        self.assertEqual(result["status"], "deployed")
        self.assertEqual(runner.deployment_queries, 4)

    def test_default_smoke_uses_system_curl_tls(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="200",
            stderr="",
        )
        with patch(
            "app.communication.mmtx_pages_deploy.subprocess.run",
            return_value=completed,
        ) as run:
            status = _default_smoke_fetcher("https://example.test/?verify=abc")

        self.assertEqual(status, 200)
        self.assertEqual(run.call_args.args[0][0], "/usr/bin/curl")
        self.assertIn("--location", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
