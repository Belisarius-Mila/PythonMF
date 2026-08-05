"""Durable, restart-safe job state for Human–Adam step completion."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import threading
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any

from app.codex_appserver import AppServerError
from app.file_persistence import atomic_write_json


COMPLETION_JOB_SCHEMA = 1
QUEUED = "queued"
RUNNING = "running"
RETRY_WAITING = "retry_waiting"
COMPLETED = "completed"
FAILED = "failed"
ACTIVE_STATES = frozenset({QUEUED, RUNNING, RETRY_WAITING})
_ALL_STATES = ACTIVE_STATES | {COMPLETED, FAILED}
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")
_WORKSTREAM_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
MAX_ATTEMPTS = 2


class HumanAdamCompletionJobError(AppServerError):
    """Raised when a durable completion job cannot be trusted."""


@dataclass(frozen=True)
class HumanAdamCompletionJob:
    state: str
    workstream_id: str
    profile_id: str
    client_message_id: str
    base_head: str
    workspace_fingerprint: str
    idempotency_key: str
    commit_message: str
    summary: str
    next_step: str
    decision: str
    proposed_next_steps: tuple[str, ...]
    visible_answer: str
    attempts: int
    failure_code: str
    checkpoint_head: str
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_line(value: object, *, label: str, limit: int, required: bool = True) -> str:
    text = " ".join(str(value or "").split())
    if required and not text:
        raise HumanAdamCompletionJobError(f"Dokončovací úloze chybí {label}.")
    if len(text) > limit:
        raise HumanAdamCompletionJobError(f"Dokončovací úloha má příliš dlouhé {label}.")
    return text


def _validated(raw: object) -> HumanAdamCompletionJob:
    fields = set(HumanAdamCompletionJob.__dataclass_fields__)
    if not isinstance(raw, dict) or set(raw) != fields:
        raise HumanAdamCompletionJobError("Private dokončovací úloha má neznámé schéma.")
    state = str(raw["state"] or "")
    workstream_id = str(raw["workstream_id"] or "").casefold()
    profile_id = str(raw["profile_id"] or "").casefold()
    client_message_id = str(raw["client_message_id"] or "")
    base_head = str(raw["base_head"] or "").casefold()
    fingerprint = str(raw["workspace_fingerprint"] or "").casefold()
    idempotency_key = str(raw["idempotency_key"] or "").casefold()
    attempts = int(raw["attempts"])
    checkpoint_head = str(raw["checkpoint_head"] or "").casefold()
    proposed = raw["proposed_next_steps"]
    visible_answer = str(raw["visible_answer"] or "").strip()
    if (
        state not in _ALL_STATES
        or not _WORKSTREAM_RE.fullmatch(workstream_id)
        or not re.fullmatch(r"[a-z][a-z0-9_-]{1,31}", profile_id)
        or not _ID_RE.fullmatch(client_message_id)
        or not _HEAD_RE.fullmatch(base_head)
        or not _DIGEST_RE.fullmatch(fingerprint)
        or not _DIGEST_RE.fullmatch(idempotency_key)
        or attempts < 0
        or attempts > MAX_ATTEMPTS
        or (checkpoint_head and not _HEAD_RE.fullmatch(checkpoint_head))
        or not isinstance(proposed, list)
        or len(proposed) > 4
        or len(visible_answer) > 200_000
    ):
        raise HumanAdamCompletionJobError("Private dokončovací úloha má neplatné údaje.")
    for field in ("created_at", "updated_at"):
        try:
            parsed = datetime.fromisoformat(str(raw[field]).replace("Z", "+00:00"))
        except ValueError as exc:
            raise HumanAdamCompletionJobError(
                "Private dokončovací úloha má neplatný čas."
            ) from exc
        if parsed.tzinfo is None:
            raise HumanAdamCompletionJobError(
                "Private dokončovací úloha má čas bez časové zóny."
            )
    return HumanAdamCompletionJob(
        state=state,
        workstream_id=workstream_id,
        profile_id=profile_id,
        client_message_id=client_message_id,
        base_head=base_head,
        workspace_fingerprint=fingerprint,
        idempotency_key=idempotency_key,
        commit_message=_safe_line(raw["commit_message"], label="název commitu", limit=120),
        summary=_safe_line(raw["summary"], label="souhrn", limit=400),
        next_step=_safe_line(raw["next_step"], label="další krok", limit=500),
        decision=_safe_line(
            raw["decision"], label="rozhodnutí", limit=400, required=False
        ),
        proposed_next_steps=tuple(
            _safe_line(item, label="navrhovaný krok", limit=300)
            for item in proposed
        ),
        visible_answer=visible_answer,
        attempts=attempts,
        failure_code=_safe_line(
            raw["failure_code"], label="kód chyby", limit=80, required=False
        ),
        checkpoint_head=checkpoint_head,
        created_at=str(raw["created_at"]),
        updated_at=str(raw["updated_at"]),
    )


class HumanAdamCompletionJobStore:
    """One durable job; a second writable turn is rejected while it is active."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".worker.lock")
        self._lock = threading.RLock()

    def load(self) -> HumanAdamCompletionJob | None:
        with self._lock:
            if not self.path.exists():
                return None
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise HumanAdamCompletionJobError(
                    "Private dokončovací úlohu nelze bezpečně načíst."
                ) from exc
            if (
                not isinstance(payload, dict)
                or payload.get("schema_version") != COMPLETION_JOB_SCHEMA
                or set(payload) != {"schema_version", "job"}
            ):
                raise HumanAdamCompletionJobError(
                    "Private dokončovací úloha má neznámé schéma."
                )
            return _validated(payload["job"])

    def _write(self, job: HumanAdamCompletionJob) -> HumanAdamCompletionJob:
        checked = _validated({**asdict(job), "proposed_next_steps": list(job.proposed_next_steps)})
        atomic_write_json(
            self.path,
            {
                "schema_version": COMPLETION_JOB_SCHEMA,
                "job": {**asdict(checked), "proposed_next_steps": list(checked.proposed_next_steps)},
            },
            ensure_ascii=False,
            indent=2,
        )
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        return checked

    def create(
        self,
        *,
        workstream_id: str,
        profile_id: str,
        client_message_id: str,
        base_head: str,
        workspace_fingerprint: str,
        idempotency_key: str,
        commit_message: str,
        summary: str,
        next_step: str,
        decision: str,
        proposed_next_steps: tuple[str, ...],
        visible_answer: str,
    ) -> HumanAdamCompletionJob:
        with self._lock:
            current = self.load()
            if current is not None and current.state in ACTIVE_STATES:
                raise HumanAdamCompletionJobError(
                    "Předchozí dokončovací úloha ještě není uzavřená."
                )
            timestamp = _now()
            return self._write(
                HumanAdamCompletionJob(
                    state=QUEUED,
                    workstream_id=workstream_id,
                    profile_id=profile_id,
                    client_message_id=client_message_id,
                    base_head=base_head,
                    workspace_fingerprint=workspace_fingerprint,
                    idempotency_key=idempotency_key,
                    commit_message=commit_message,
                    summary=summary,
                    next_step=next_step,
                    decision=decision,
                    proposed_next_steps=proposed_next_steps,
                    visible_answer=visible_answer,
                    attempts=0,
                    failure_code="",
                    checkpoint_head="",
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )

    def update(self, job: HumanAdamCompletionJob, **changes: Any) -> HumanAdamCompletionJob:
        with self._lock:
            current = self.load()
            if (
                current is None
                or current.idempotency_key != job.idempotency_key
                or current.state not in ACTIVE_STATES
            ):
                raise HumanAdamCompletionJobError(
                    "Dokončovací úloha se mezitím změnila nebo skončila."
                )
            return self._write(replace(current, updated_at=_now(), **changes))

    def acquire_worker_lease(self) -> IO[str] | None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return None
        return handle


def workspace_fingerprint(workspace_root: Path) -> str:
    """Hash the exact tracked diff and untracked bytes without persisting content."""

    root = Path(workspace_root)
    digest = hashlib.sha256()
    try:
        diff = subprocess.run(
            ["/usr/bin/git", "-C", str(root), "diff", "--binary", "--no-ext-diff", "HEAD", "--", "."],
            capture_output=True,
            timeout=60,
            check=True,
        ).stdout
        untracked = subprocess.run(
            ["/usr/bin/git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
            capture_output=True,
            timeout=30,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise HumanAdamCompletionJobError(
            "Nelze vytvořit bezpečný otisk rozpracované práce."
        ) from exc
    digest.update(diff)
    for raw_path in sorted(item for item in untracked.split(b"\0") if item):
        relative = os.fsdecode(raw_path)
        candidate = (root / relative).resolve()
        if root.resolve() not in candidate.parents:
            raise HumanAdamCompletionJobError("Otisk rozpracované práce míří mimo workspace.")
        digest.update(b"\0U\0" + raw_path + b"\0")
        try:
            digest.update(candidate.read_bytes())
        except OSError as exc:
            raise HumanAdamCompletionJobError(
                "Nelze přečíst soubor pro otisk rozpracované práce."
            ) from exc
    return digest.hexdigest()


def completion_idempotency_key(
    *,
    workstream_id: str,
    client_message_id: str,
    base_head: str,
    workspace_fingerprint: str,
) -> str:
    material = "\0".join(
        (workstream_id, client_message_id, base_head, workspace_fingerprint)
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()
