"""Audit and send accumulated local ``main`` commits as one GitHub batch.

Local ``main`` is the daytime development authority.  This module touches the
remote only when the user explicitly audits or confirms one batch.  It never
merges, rebases, squashes, force-pushes, or changes the local working tree.
"""

from __future__ import annotations

import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from app.codex_appserver import AppServerError
from app.communication.checkpoint_quality_gate import (
    DEFAULT_GATE_LOG,
    HumanAdamGateError,
    run_checkpoint_quality_gate,
)
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager


GITHUB_BATCH_CONFIRMATION = "POTVRZUJI ODESLANI DENNIHO GITHUB BALICKU"
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_BATCH_LOCK = threading.Lock()
_BLOCKED_PREFIXES = (
    "Samantha_Agent/data/private/",
    "Samantha_Agent/data/session_autosave/",
)
_BLOCKED_NAMES = frozenset({".env", ".env.local", ".env.production"})


class GitHubBatchError(AppServerError):
    """Raised when a daily batch cannot be proven as a plain fast-forward."""


@dataclass(frozen=True)
class GitHubBatchPlan:
    origin_head: str
    local_head: str
    commits: tuple[dict[str, str], ...]
    changes: tuple[dict[str, str], ...]

    def public_dict(self) -> dict[str, Any]:
        commit_preview = self.commits[:40]
        change_preview = self.changes[:80]
        return {
            "ok": True,
            "read_only": True,
            "writes_performed": False,
            "state": "ready",
            "ready": True,
            "pending": True,
            "origin_head": self.origin_head,
            "origin_short": self.origin_head[:12],
            "local_head": self.local_head,
            "local_short": self.local_head[:12],
            "commit_count": len(self.commits),
            "commits": [dict(item) for item in commit_preview],
            "commits_truncated": len(commit_preview) < len(self.commits),
            "change_count": len(self.changes),
            "changes": [dict(item) for item in change_preview],
            "changes_truncated": len(change_preview) < len(self.changes),
            "confirmation_text": GITHUB_BATCH_CONFIRMATION,
            "will_merge": False,
            "will_rebase": False,
            "will_squash": False,
            "will_force_push": False,
        }


def _git(repo: Path, args: Sequence[str], *, timeout: float = 120.0) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise GitHubBatchError(detail or f"Git operace selhala: {' '.join(args)}")
    return completed.stdout.strip()


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(repo),
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.returncode == 0


def _refresh_origin_main(repo: Path) -> str:
    try:
        _git(
            repo,
            [
                "fetch",
                "--no-tags",
                "origin",
                "refs/heads/main:refs/remotes/origin/main",
            ],
        )
        return _git(repo, ["rev-parse", "origin/main"]).casefold()
    except GitHubBatchError as exc:
        raise GitHubBatchError(
            "GitHub nelze ověřit; lokální práce zůstává zachovaná a balíček se neodeslal."
        ) from exc


def _source_head(repo: Path) -> str:
    if _git(repo, ["branch", "--show-current"]) != "main":
        raise GitHubBatchError("Denní GitHub balíček je dostupný pouze na větvi main.")
    if _git(repo, ["status", "--porcelain=v1", "--untracked-files=all"]):
        raise GitHubBatchError("Lokální main není čistý; balíček se neodeslal.")
    head = _git(repo, ["rev-parse", "HEAD"]).casefold()
    if not _HEAD_RE.fullmatch(head):
        raise GitHubBatchError("Lokální main nemá platný commit.")
    return head


def _commit_rows(repo: Path, origin_head: str, local_head: str) -> tuple[dict[str, str], ...]:
    output = _git(
        repo,
        [
            "log",
            "--reverse",
            "--format=%H%x09%s",
            f"{origin_head}..{local_head}",
        ],
    )
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        head, separator, subject = line.partition("\t")
        if not separator or not _HEAD_RE.fullmatch(head.casefold()):
            raise GitHubBatchError("Seznam lokálních commitů má neznámý formát.")
        rows.append({"head": head[:12], "subject": subject[:160]})
    if not rows:
        raise GitHubBatchError("Git hlásí local-ahead stav bez odesílatelného commitu.")
    return tuple(rows)


def _blocked_path(path: str) -> bool:
    clean = str(path or "").strip().replace("\\", "/")
    name = Path(clean).name.casefold()
    return (
        not clean
        or clean.startswith("/")
        or ".." in Path(clean).parts
        or any(clean.startswith(prefix) for prefix in _BLOCKED_PREFIXES)
        or name in _BLOCKED_NAMES
        or name.endswith((".pem", ".key", ".p12", ".pfx"))
    )


def _change_rows(repo: Path, origin_head: str, local_head: str) -> tuple[dict[str, str], ...]:
    output = _git(
        repo,
        [
            "diff",
            "--name-status",
            "--find-renames",
            origin_head,
            local_head,
        ],
    )
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            status, path = parts
            row = {"status": status, "path": path}
            paths = (path,)
        elif len(parts) == 3:
            status, from_path, path = parts
            row = {"status": status, "from_path": from_path, "path": path}
            paths = (from_path, path)
        else:
            raise GitHubBatchError("Změny denního balíčku mají neznámý formát.")
        if any(_blocked_path(path) for path in paths):
            raise GitHubBatchError(
                "Denní balíček obsahuje blokovanou private, env nebo klíčovou cestu."
            )
        rows.append(row)
    if not rows:
        raise GitHubBatchError("Denní balíček neobsahuje žádnou změněnou cestu.")
    return tuple(rows)


def audit_github_batch(
    *,
    source_repo: Path,
    refresh_remote: bool = True,
) -> dict[str, Any]:
    """Return one exact read-only batch plan.

    Explicit evening audits refresh ``origin/main``.  Ordinary daytime status
    may use the last known remote ref so opening or completing development does
    not silently contact GitHub.
    """

    repo = Path(source_repo).resolve()
    local_head = _source_head(repo)
    origin_head = (
        _refresh_origin_main(repo)
        if refresh_remote
        else _git(repo, ["rev-parse", "origin/main"]).casefold()
    )
    if not _HEAD_RE.fullmatch(origin_head):
        raise GitHubBatchError("Origin/main nemá platný commit.")
    if local_head == origin_head:
        return {
            "ok": True,
            "read_only": True,
            "writes_performed": False,
            "state": "aligned",
            "ready": False,
            "pending": False,
            "origin_head": origin_head,
            "origin_short": origin_head[:12],
            "local_head": local_head,
            "local_short": local_head[:12],
            "commit_count": 0,
            "commits": [],
            "commits_truncated": False,
            "change_count": 0,
            "changes": [],
            "changes_truncated": False,
            "confirmation_text": GITHUB_BATCH_CONFIRMATION,
        }
    if not _is_ancestor(repo, origin_head, local_head):
        state = "origin_ahead" if _is_ancestor(repo, local_head, origin_head) else "diverged"
        return {
            "ok": True,
            "read_only": True,
            "writes_performed": False,
            "state": state,
            "ready": False,
            "pending": False,
            "origin_head": origin_head,
            "origin_short": origin_head[:12],
            "local_head": local_head,
            "local_short": local_head[:12],
            "commit_count": 0,
            "commits": [],
            "commits_truncated": False,
            "change_count": 0,
            "changes": [],
            "changes_truncated": False,
            "confirmation_text": GITHUB_BATCH_CONFIRMATION,
        }
    return GitHubBatchPlan(
        origin_head=origin_head,
        local_head=local_head,
        commits=_commit_rows(repo, origin_head, local_head),
        changes=_change_rows(repo, origin_head, local_head),
    ).public_dict()


def push_github_batch(
    *,
    workspace: HumanAdamWorkspaceManager,
    expected_origin_head: str,
    expected_local_head: str,
    confirmation: str,
    gate_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    gate_log_path: Path = DEFAULT_GATE_LOG,
) -> dict[str, Any]:
    """Run one full gate and push the exact audited commit range."""

    if str(confirmation or "").strip() != GITHUB_BATCH_CONFIRMATION:
        raise GitHubBatchError(
            f"Chybí přesná potvrzovací věta: {GITHUB_BATCH_CONFIRMATION}"
        )
    expected_origin = str(expected_origin_head or "").strip().casefold()
    expected_local = str(expected_local_head or "").strip().casefold()
    if not _HEAD_RE.fullmatch(expected_origin) or not _HEAD_RE.fullmatch(expected_local):
        raise GitHubBatchError("Denní balíček nemá platné auditované commity.")
    if not _BATCH_LOCK.acquire(blocking=False):
        raise GitHubBatchError("Jiný denní GitHub balíček právě probíhá.")
    try:
        initial = audit_github_batch(source_repo=workspace.source_repo)
        if (
            initial.get("ready") is not True
            or initial.get("origin_head") != expected_origin
            or initial.get("local_head") != expected_local
        ):
            raise GitHubBatchError(
                "GitHub nebo lokální main se od auditu změnil; proveď nový audit."
            )
        try:
            evidence = run_checkpoint_quality_gate(
                workspace=workspace,
                runner=gate_runner,
                log_path=gate_log_path,
            )
        except HumanAdamGateError as exc:
            raise GitHubBatchError(
                "Úplná večerní brána neprošla; nic se nepushnulo a lokální práce zůstává zachovaná."
            ) from exc
        final = audit_github_batch(source_repo=workspace.source_repo)
        if (
            final.get("ready") is not True
            or final.get("origin_head") != expected_origin
            or final.get("local_head") != expected_local
        ):
            raise GitHubBatchError(
                "GitHub nebo lokální main se během brány změnil; nic se nepushnulo."
            )
        _git(
            workspace.source_repo,
            ["push", "origin", f"{expected_local}:refs/heads/main"],
        )
        verified_origin = _refresh_origin_main(workspace.source_repo)
        if verified_origin != expected_local or _source_head(workspace.source_repo) != expected_local:
            raise GitHubBatchError("Push proběhl, ale závěrečná shoda GitHubu není doložená.")
        return {
            **final,
            "ok": True,
            "state": "pushed",
            "ready": False,
            "pending": False,
            "writes_performed": True,
            "pushed": True,
            "gate": evidence.public_dict(),
        }
    finally:
        _BATCH_LOCK.release()
