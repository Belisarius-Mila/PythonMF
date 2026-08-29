"""Verified GitHub Pages publication for the MMTX production site."""

from __future__ import annotations

import json
import re
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Any, Callable, Sequence

from app.codex_appserver import AppServerError


GITHUB_REPOSITORY = "Belisarius-Mila/PythonMF"
PAGES_WORKFLOW = "Samantha Daily 3 AM"
PRODUCTION_URL = "https://belisarius-mila.github.io/PythonMF/"
_GH_BIN = "/usr/local/bin/gh"
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_RUN_URL_RE = re.compile(r"/actions/runs/(?P<run_id>[1-9][0-9]*)/?$")
_PUBLISH_LOCK = threading.Lock()


class MmtxPagesDeployError(AppServerError):
    """Raised when public MMTX publication cannot be proved end to end."""


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
SmokeFetcher = Callable[[str], int]


def _run(
    runner: CommandRunner,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float,
) -> str:
    try:
        completed = runner(
            list(args),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MmtxPagesDeployError(
            "Publikační operace se nepodařila bezpečně dokončit."
        ) from exc
    if completed.returncode != 0:
        raise MmtxPagesDeployError(
            "Publikační operace selhala; produkce nebyla potvrzena."
        )
    return str(completed.stdout or "").strip()


def _json_command(
    runner: CommandRunner,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float = 60.0,
) -> Any:
    raw = _run(runner, args, cwd=cwd, timeout=timeout)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise MmtxPagesDeployError(
            "GitHub vrátil neplatný publikační doklad."
        ) from exc


def _git_head(runner: CommandRunner, source_repo: Path) -> str:
    branch = _run(
        runner,
        ["/usr/bin/git", "-C", str(source_repo), "branch", "--show-current"],
        cwd=source_repo,
        timeout=30,
    )
    if branch != "main":
        raise MmtxPagesDeployError("Produkční publikace je dostupná pouze z main.")
    dirty = _run(
        runner,
        [
            "/usr/bin/git",
            "-C",
            str(source_repo),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        cwd=source_repo,
        timeout=30,
    )
    if dirty:
        raise MmtxPagesDeployError("Main není čistý; produkce se nenasadila.")
    head = _run(
        runner,
        ["/usr/bin/git", "-C", str(source_repo), "rev-parse", "HEAD"],
        cwd=source_repo,
        timeout=30,
    ).casefold()
    origin = _run(
        runner,
        ["/usr/bin/git", "-C", str(source_repo), "rev-parse", "origin/main"],
        cwd=source_repo,
        timeout=30,
    ).casefold()
    if not _HEAD_RE.fullmatch(head) or origin != head:
        raise MmtxPagesDeployError(
            "Lokální main a GitHub nejsou shodné; produkce se nenasadila."
        )
    return head


def _successful_deployment(
    runner: CommandRunner,
    *,
    source_repo: Path,
    target_head: str,
) -> dict[str, Any] | None:
    deployments = _json_command(
        runner,
        [
            _GH_BIN,
            "api",
            f"repos/{GITHUB_REPOSITORY}/deployments?environment=github-pages&per_page=20",
        ],
        cwd=source_repo,
    )
    if not isinstance(deployments, list):
        raise MmtxPagesDeployError("GitHub nevrátil seznam Pages nasazení.")
    for deployment in deployments:
        if not isinstance(deployment, dict) or deployment.get("sha") != target_head:
            continue
        deployment_id = deployment.get("id")
        if not isinstance(deployment_id, int) or deployment_id <= 0:
            continue
        statuses = _json_command(
            runner,
            [
                _GH_BIN,
                "api",
                f"repos/{GITHUB_REPOSITORY}/deployments/{deployment_id}/statuses",
            ],
            cwd=source_repo,
        )
        if not isinstance(statuses, list):
            continue
        successful = next(
            (
                item
                for item in statuses
                if isinstance(item, dict) and item.get("state") == "success"
            ),
            None,
        )
        if successful is not None:
            return {
                "deployment_id": deployment_id,
                "production_url": str(
                    successful.get("environment_url") or PRODUCTION_URL
                ),
            }
    return None


def _default_smoke_fetcher(url: str) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Samantha-Human-Adam-Pages-Verification/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed public URL
        return int(response.status)


def publish_mmtx_pages_current_main(
    *,
    source_repo: Path,
    runner: CommandRunner = subprocess.run,
    smoke_fetcher: SmokeFetcher = _default_smoke_fetcher,
) -> dict[str, object]:
    """Publish one clean GitHub-aligned main and prove the Pages deployment."""

    repo = Path(source_repo).resolve()
    if not _PUBLISH_LOCK.acquire(blocking=False):
        raise MmtxPagesDeployError("Jiné MMTX nasazení právě probíhá.")
    try:
        target_head = _git_head(runner, repo)
        existing = _successful_deployment(
            runner,
            source_repo=repo,
            target_head=target_head,
        )
        if existing is not None:
            smoke_status = smoke_fetcher(
                f"{existing['production_url']}?verify={target_head[:12]}"
            )
            if smoke_status != 200:
                raise MmtxPagesDeployError("Publikovaná MMTX stránka neprošla HTTP smoke.")
            return {
                "status": "already_deployed",
                "main_short": target_head[:12],
                "workflow_run_id": 0,
                "deployment_id": int(existing["deployment_id"]),
                "production_url": str(existing["production_url"]),
                "smoke_http_status": smoke_status,
                "redacted": True,
            }

        trigger_output = _run(
            runner,
            [
                _GH_BIN,
                "workflow",
                "run",
                PAGES_WORKFLOW,
                "--repo",
                GITHUB_REPOSITORY,
                "--ref",
                "main",
            ],
            cwd=repo,
            timeout=60,
        )
        match = _RUN_URL_RE.search(trigger_output)
        if match is None:
            raise MmtxPagesDeployError("GitHub nepotvrdil ID spuštěné Pages publikace.")
        run_id = int(match.group("run_id"))
        _run(
            runner,
            [
                _GH_BIN,
                "run",
                "watch",
                str(run_id),
                "--repo",
                GITHUB_REPOSITORY,
                "--exit-status",
            ],
            cwd=repo,
            timeout=1_200,
        )
        run = _json_command(
            runner,
            [
                _GH_BIN,
                "run",
                "view",
                str(run_id),
                "--repo",
                GITHUB_REPOSITORY,
                "--json",
                "databaseId,headSha,status,conclusion,url",
            ],
            cwd=repo,
        )
        if (
            not isinstance(run, dict)
            or run.get("databaseId") != run_id
            or run.get("headSha") != target_head
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
        ):
            raise MmtxPagesDeployError(
                "Pages workflow nedoložil úspěšné nasazení auditovaného main."
            )
        deployment = _successful_deployment(
            runner,
            source_repo=repo,
            target_head=target_head,
        )
        if deployment is None:
            raise MmtxPagesDeployError(
                "Workflow skončil, ale produkční Pages deployment není potvrzený."
            )
        smoke_status = smoke_fetcher(
            f"{deployment['production_url']}?verify={target_head[:12]}"
        )
        if smoke_status != 200:
            raise MmtxPagesDeployError("Publikovaná MMTX stránka neprošla HTTP smoke.")
        return {
            "status": "deployed",
            "main_short": target_head[:12],
            "workflow_run_id": run_id,
            "deployment_id": int(deployment["deployment_id"]),
            "production_url": str(deployment["production_url"]),
            "smoke_http_status": smoke_status,
            "redacted": True,
        }
    finally:
        _PUBLISH_LOCK.release()
