"""Private ownership proof for one deferred Human–Adam integration.

The marker never stores file contents, chat text, identities, or secrets.  It
binds one validated completion receipt to the exact base commit and a digest of
the path-level workspace status.  Integration remains a separate explicitly
confirmed operation.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from app.codex_appserver import AppServerError
from app.communication.human_adam_turn_completion import (
    COMPLETION_MARKER_END,
    COMPLETION_MARKER_START,
    TurnCompletionMetadata,
    parse_turn_completion,
)
from app.file_persistence import FilePersistenceError, atomic_write_json


DEFERRED_INTEGRATION_SCHEMA = 1
DEFERRED_INTEGRATION_CONFIRMATION = (
    "POTVRZUJI INTEGRACI ODLOZENEHO HUMAN_ADAM WIP"
)
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")


class DeferredIntegrationError(AppServerError):
    """Raised when deferred ownership cannot be proven exactly."""


@dataclass(frozen=True)
class DeferredIntegrationRecord:
    workstream_id: str
    base_head: str
    change_count: int
    change_fingerprint: str
    completion: TurnCompletionMetadata
    created_at: str


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalized_change_rows(
    changes: Sequence[dict[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in changes:
        if not isinstance(raw, dict):
            raise DeferredIntegrationError(
                "Odložená integrace nemá ověřitelný seznam změn."
            )
        status = str(raw.get("status") or "").strip()
        path = str(raw.get("path") or "").strip()
        if not status or not path or "\n" in path or "\r" in path:
            raise DeferredIntegrationError(
                "Odložená integrace nemá ověřitelný seznam změn."
            )
        rows.append({"status": status, "path": path})
    rows.sort(key=lambda row: (row["path"], row["status"]))
    if not rows:
        raise DeferredIntegrationError(
            "Odložená integrace nemá žádnou změnu k převzetí."
        )
    return rows


def change_fingerprint(changes: Sequence[dict[str, Any]]) -> str:
    rows = _normalized_change_rows(changes)
    payload = json.dumps(
        rows,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validated_completion(value: object) -> TurnCompletionMetadata:
    if not isinstance(value, dict):
        raise DeferredIntegrationError(
            "Ownership marker nemá platnou dokončovací účtenku."
        )
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    parsed = parse_turn_completion(
        "Odložený vývoj dokončen.\n\n"
        f"{COMPLETION_MARKER_START}\n{payload}\n{COMPLETION_MARKER_END}"
    )
    if parsed.state != "valid" or parsed.metadata is None:
        raise DeferredIntegrationError(
            "Ownership marker nemá platnou dokončovací účtenku."
        )
    return parsed.metadata


class DeferredIntegrationStore:
    """Persist one exact private marker outside Git."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def save(
        self,
        *,
        workstream_id: str,
        workspace_status: dict[str, Any],
        completion: TurnCompletionMetadata,
        now_factory: Any = _now,
    ) -> DeferredIntegrationRecord:
        clean_workstream = str(workstream_id or "").strip().casefold()
        head = str(workspace_status.get("head") or "").strip().casefold()
        source_head = str(workspace_status.get("source_head") or "").strip().casefold()
        changes = list(workspace_status.get("changes") or [])
        if (
            not _WORKSTREAM_ID_RE.fullmatch(clean_workstream)
            or not _HEAD_RE.fullmatch(head)
            or source_head != head
            or workspace_status.get("workspace_relation") != "aligned"
            or workspace_status.get("dirty") is not True
            or int(workspace_status.get("source_pending_changes") or 0) <= 0
        ):
            raise DeferredIntegrationError(
                "Ownership marker lze vytvořit jen pro ověřený odložený tah "
                "na společném základu při terminálovém WIP."
            )
        fingerprint = change_fingerprint(changes)
        created_at = str(now_factory() or "").strip()
        try:
            parsed_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DeferredIntegrationError(
                "Ownership marker nemá platný čas."
            ) from exc
        if parsed_at.tzinfo is None:
            raise DeferredIntegrationError(
                "Ownership marker nemá platnou časovou zónu."
            )
        payload = {
            "schema_version": DEFERRED_INTEGRATION_SCHEMA,
            "workstream_id": clean_workstream,
            "base_head": head,
            "change_count": len(changes),
            "change_fingerprint": fingerprint,
            "completion": asdict(completion),
            "created_at": parsed_at.isoformat(),
        }
        try:
            atomic_write_json(
                self.path,
                payload,
                ensure_ascii=False,
                indent=2,
            )
            os.chmod(self.path, 0o600)
        except (FilePersistenceError, OSError) as exc:
            raise DeferredIntegrationError(
                "Private ownership marker nelze bezpečně uložit."
            ) from exc
        return self.load()

    def load(self) -> DeferredIntegrationRecord:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise DeferredIntegrationError(
                "Private ownership marker nelze bezpečně načíst."
            ) from exc
        required = {
            "schema_version",
            "workstream_id",
            "base_head",
            "change_count",
            "change_fingerprint",
            "completion",
            "created_at",
        }
        if (
            not isinstance(raw, dict)
            or set(raw) != required
            or raw.get("schema_version") != DEFERRED_INTEGRATION_SCHEMA
        ):
            raise DeferredIntegrationError(
                "Private ownership marker má neznámé schéma."
            )
        workstream_id = str(raw.get("workstream_id") or "").strip().casefold()
        base_head = str(raw.get("base_head") or "").strip().casefold()
        fingerprint = str(raw.get("change_fingerprint") or "").strip().casefold()
        created_at = str(raw.get("created_at") or "").strip()
        try:
            change_count = int(raw.get("change_count") or 0)
            parsed_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise DeferredIntegrationError(
                "Private ownership marker má neplatné údaje."
            ) from exc
        if (
            not _WORKSTREAM_ID_RE.fullmatch(workstream_id)
            or not _HEAD_RE.fullmatch(base_head)
            or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
            or change_count <= 0
            or parsed_at.tzinfo is None
        ):
            raise DeferredIntegrationError(
                "Private ownership marker má neplatné údaje."
            )
        return DeferredIntegrationRecord(
            workstream_id=workstream_id,
            base_head=base_head,
            change_count=change_count,
            change_fingerprint=fingerprint,
            completion=_validated_completion(raw.get("completion")),
            created_at=parsed_at.isoformat(),
        )

    def verify(
        self,
        *,
        workstream_id: str,
        workspace_status: dict[str, Any],
    ) -> DeferredIntegrationRecord:
        record = self.load()
        changes = list(workspace_status.get("changes") or [])
        current_head = str(workspace_status.get("head") or "").strip().casefold()
        source_head = str(workspace_status.get("source_head") or "").strip().casefold()
        if (
            record.workstream_id != str(workstream_id or "").strip().casefold()
            or workspace_status.get("dirty") is not True
            or workspace_status.get("workspace_relation") != "aligned"
            or int(workspace_status.get("source_pending_changes") or 0) != 0
            or current_head != record.base_head
            or source_head != record.base_head
            or len(changes) != record.change_count
            or change_fingerprint(changes) != record.change_fingerprint
        ):
            raise DeferredIntegrationError(
                "Ownership marker neodpovídá aktuálnímu WIP nebo společnému základu; "
                "integrace vyžaduje servisní rozhodnutí."
            )
        return record

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            raise DeferredIntegrationError(
                "Dokončený ownership marker nelze bezpečně uzavřít."
            ) from exc
