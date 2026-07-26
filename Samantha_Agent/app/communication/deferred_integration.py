"""Private ownership proof for one Human–Adam write turn.

The marker never stores file contents, chat text, identities, or secrets.  It
is created before the writable turn, then binds the delivered turn to the exact
base commit and a digest of the path-level workspace status.  Completion
metadata and ownership are deliberately separate: a missing model receipt may
block automatic checkpointing, but it must not make the origin of the WIP
unknowable.  Integration remains a separate explicitly confirmed operation.
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


LEGACY_DEFERRED_INTEGRATION_SCHEMA = 1
DEFERRED_INTEGRATION_SCHEMA = 2
DEFERRED_INTEGRATION_CONFIRMATION = (
    "POTVRZUJI INTEGRACI ODLOZENEHO HUMAN_ADAM WIP"
)
OWNED_WIP_RECOVERY_CONFIRMATION = (
    "POTVRZUJI DOKONCENI VLASTNENEHO HUMAN_ADAM WIP"
)
IN_PROGRESS = "in_progress"
OWNED_WIP_MISSING_METADATA = "owned_wip_missing_metadata"
READY_FOR_CONFIRMED_INTEGRATION = "ready_for_confirmed_integration"
DELIVERY_UNKNOWN = "delivery_unknown"
_MARKER_STATES = frozenset(
    {
        IN_PROGRESS,
        OWNED_WIP_MISSING_METADATA,
        READY_FOR_CONFIRMED_INTEGRATION,
        DELIVERY_UNKNOWN,
    }
)
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
_CLIENT_MESSAGE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")


class DeferredIntegrationError(AppServerError):
    """Raised when deferred ownership cannot be proven exactly."""


@dataclass(frozen=True)
class DeferredIntegrationRecord:
    state: str
    workstream_id: str
    client_message_id: str
    base_head: str
    change_count: int
    change_fingerprint: str
    completion: TurnCompletionMetadata | None
    integration_deferred: bool
    created_at: str
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validated_timestamp(value: object, *, label: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DeferredIntegrationError(
            f"Ownership marker nemá platný čas {label}."
        ) from exc
    if parsed.tzinfo is None:
        raise DeferredIntegrationError(
            f"Ownership marker nemá platnou časovou zónu {label}."
        )
    return parsed.isoformat()


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

    def _write(self, record: DeferredIntegrationRecord) -> DeferredIntegrationRecord:
        payload = {
            "schema_version": DEFERRED_INTEGRATION_SCHEMA,
            "state": record.state,
            "workstream_id": record.workstream_id,
            "client_message_id": record.client_message_id,
            "base_head": record.base_head,
            "change_count": record.change_count,
            "change_fingerprint": record.change_fingerprint,
            "completion": (
                asdict(record.completion)
                if record.completion is not None
                else None
            ),
            "integration_deferred": record.integration_deferred,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
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

    def begin(
        self,
        *,
        workstream_id: str,
        client_message_id: str,
        workspace_status: dict[str, Any],
        integration_deferred: bool,
        now_factory: Any = _now,
    ) -> DeferredIntegrationRecord:
        """Create an ownership transaction before the model may write files."""

        clean_workstream = str(workstream_id or "").strip().casefold()
        clean_message_id = str(client_message_id or "").strip()
        head = str(workspace_status.get("head") or "").strip().casefold()
        source_head = str(workspace_status.get("source_head") or "").strip().casefold()
        changes = list(workspace_status.get("changes") or [])
        if (
            not _WORKSTREAM_ID_RE.fullmatch(clean_workstream)
            or not _CLIENT_MESSAGE_ID_RE.fullmatch(clean_message_id)
            or not _HEAD_RE.fullmatch(head)
            or source_head != head
            or workspace_status.get("workspace_relation") != "aligned"
            or workspace_status.get("dirty") is not False
            or changes
        ):
            raise DeferredIntegrationError(
                "Ownership marker lze zahájit jen před čistým zapisovacím tahem "
                "na ověřeném společném základu."
            )
        if self.path.exists():
            existing = self.load()
            if (
                existing.state == IN_PROGRESS
                and existing.workstream_id == clean_workstream
                and existing.client_message_id == clean_message_id
                and existing.base_head == head
            ):
                return existing
            raise DeferredIntegrationError(
                "Předchozí ownership marker není uzavřený; nový zapisovací tah "
                "zůstává zablokovaný."
            )
        created_at = _validated_timestamp(now_factory(), label="zahájení")
        return self._write(
            DeferredIntegrationRecord(
                state=IN_PROGRESS,
                workstream_id=clean_workstream,
                client_message_id=clean_message_id,
                base_head=head,
                change_count=0,
                change_fingerprint="",
                completion=None,
                integration_deferred=bool(integration_deferred),
                created_at=created_at,
                updated_at=created_at,
            )
        )

    def finalize(
        self,
        *,
        workstream_id: str,
        client_message_id: str,
        workspace_status: dict[str, Any],
        completion: TurnCompletionMetadata | None,
        now_factory: Any = _now,
    ) -> DeferredIntegrationRecord:
        """Bind one delivered turn to its exact resulting path-level WIP."""

        record = self.load()
        clean_workstream = str(workstream_id or "").strip().casefold()
        clean_message_id = str(client_message_id or "").strip()
        current_head = str(workspace_status.get("head") or "").strip().casefold()
        changes = list(workspace_status.get("changes") or [])
        if (
            record.state != IN_PROGRESS
            or record.workstream_id != clean_workstream
            or record.client_message_id != clean_message_id
            or current_head != record.base_head
            or workspace_status.get("dirty") is not True
        ):
            raise DeferredIntegrationError(
                "Ownership marker neodpovídá dokončenému zapisovacímu tahu."
            )
        fingerprint = change_fingerprint(changes)
        updated_at = _validated_timestamp(now_factory(), label="dokončení")
        return self._write(
            DeferredIntegrationRecord(
                state=(
                    READY_FOR_CONFIRMED_INTEGRATION
                    if completion is not None
                    else OWNED_WIP_MISSING_METADATA
                ),
                workstream_id=record.workstream_id,
                client_message_id=record.client_message_id,
                base_head=record.base_head,
                change_count=len(changes),
                change_fingerprint=fingerprint,
                completion=completion,
                integration_deferred=record.integration_deferred,
                created_at=record.created_at,
                updated_at=updated_at,
            )
        )

    def mark_delivery_unknown(
        self,
        *,
        workstream_id: str,
        client_message_id: str,
        workspace_status: dict[str, Any],
        now_factory: Any = _now,
    ) -> DeferredIntegrationRecord:
        """Keep the pre-turn proof while ambiguous delivery remains blocked."""

        record = self.load()
        clean_workstream = str(workstream_id or "").strip().casefold()
        clean_message_id = str(client_message_id or "").strip()
        if (
            record.state != IN_PROGRESS
            or record.workstream_id != clean_workstream
            or record.client_message_id != clean_message_id
        ):
            raise DeferredIntegrationError(
                "Ownership marker neodpovídá nejistému zapisovacímu tahu."
            )
        changes = list(workspace_status.get("changes") or [])
        dirty = workspace_status.get("dirty") is True
        fingerprint = change_fingerprint(changes) if dirty else ""
        updated_at = _validated_timestamp(now_factory(), label="nejistého doručení")
        return self._write(
            DeferredIntegrationRecord(
                state=DELIVERY_UNKNOWN,
                workstream_id=record.workstream_id,
                client_message_id=record.client_message_id,
                base_head=record.base_head,
                change_count=len(changes) if dirty else 0,
                change_fingerprint=fingerprint,
                completion=None,
                integration_deferred=record.integration_deferred,
                created_at=record.created_at,
                updated_at=updated_at,
            )
        )

    def save(
        self,
        *,
        workstream_id: str,
        workspace_status: dict[str, Any],
        completion: TurnCompletionMetadata,
        now_factory: Any = _now,
    ) -> DeferredIntegrationRecord:
        """Create a completed legacy-style marker for compatibility callers."""

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
        created_at = _validated_timestamp(now_factory(), label="vytvoření")
        return self._write(
            DeferredIntegrationRecord(
                state=READY_FOR_CONFIRMED_INTEGRATION,
                workstream_id=clean_workstream,
                client_message_id="legacy-marker",
                base_head=head,
                change_count=len(changes),
                change_fingerprint=fingerprint,
                completion=completion,
                integration_deferred=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )

    def load(self) -> DeferredIntegrationRecord:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise DeferredIntegrationError(
                "Private ownership marker nelze bezpečně načíst."
            ) from exc
        legacy_required = {
            "schema_version",
            "workstream_id",
            "base_head",
            "change_count",
            "change_fingerprint",
            "completion",
            "created_at",
        }
        current_required = {
            "schema_version",
            "state",
            "workstream_id",
            "client_message_id",
            "base_head",
            "change_count",
            "change_fingerprint",
            "completion",
            "integration_deferred",
            "created_at",
            "updated_at",
        }
        if not isinstance(raw, dict):
            raise DeferredIntegrationError(
                "Private ownership marker má neznámé schéma."
            )
        schema = raw.get("schema_version")
        if schema == LEGACY_DEFERRED_INTEGRATION_SCHEMA and set(raw) == legacy_required:
            raw = {
                **raw,
                "schema_version": DEFERRED_INTEGRATION_SCHEMA,
                "state": READY_FOR_CONFIRMED_INTEGRATION,
                "client_message_id": "legacy-marker",
                "integration_deferred": True,
                "updated_at": raw.get("created_at"),
            }
        elif schema != DEFERRED_INTEGRATION_SCHEMA or set(raw) != current_required:
            raise DeferredIntegrationError(
                "Private ownership marker má neznámé schéma."
            )
        state = str(raw.get("state") or "").strip()
        workstream_id = str(raw.get("workstream_id") or "").strip().casefold()
        client_message_id = str(raw.get("client_message_id") or "").strip()
        base_head = str(raw.get("base_head") or "").strip().casefold()
        fingerprint = str(raw.get("change_fingerprint") or "").strip().casefold()
        try:
            change_count = int(raw.get("change_count") or 0)
        except (TypeError, ValueError) as exc:
            raise DeferredIntegrationError(
                "Private ownership marker má neplatné údaje."
            ) from exc
        created_at = _validated_timestamp(raw.get("created_at"), label="vytvoření")
        updated_at = _validated_timestamp(raw.get("updated_at"), label="aktualizace")
        completion = (
            _validated_completion(raw.get("completion"))
            if raw.get("completion") is not None
            else None
        )
        integration_deferred = raw.get("integration_deferred")
        completed_state = state in {
            OWNED_WIP_MISSING_METADATA,
            READY_FOR_CONFIRMED_INTEGRATION,
        }
        if (
            state not in _MARKER_STATES
            or not _WORKSTREAM_ID_RE.fullmatch(workstream_id)
            or not _CLIENT_MESSAGE_ID_RE.fullmatch(client_message_id)
            or not _HEAD_RE.fullmatch(base_head)
            or not isinstance(integration_deferred, bool)
            or (
                completed_state
                and (
                    change_count <= 0
                    or not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
                )
            )
            or (
                not completed_state
                and (
                    change_count < 0
                    or (
                        change_count == 0
                        and fingerprint
                    )
                    or (
                        change_count > 0
                        and not re.fullmatch(r"[0-9a-f]{64}", fingerprint)
                    )
                )
            )
            or (
                state == READY_FOR_CONFIRMED_INTEGRATION
                and completion is None
            )
            or (
                state != READY_FOR_CONFIRMED_INTEGRATION
                and completion is not None
            )
        ):
            raise DeferredIntegrationError(
                "Private ownership marker má neplatné údaje."
            )
        return DeferredIntegrationRecord(
            state=state,
            workstream_id=workstream_id,
            client_message_id=client_message_id,
            base_head=base_head,
            change_count=change_count,
            change_fingerprint=fingerprint,
            completion=completion,
            integration_deferred=integration_deferred,
            created_at=created_at,
            updated_at=updated_at,
        )

    def verify_owned(
        self,
        *,
        workstream_id: str,
        workspace_status: dict[str, Any],
        allowed_states: frozenset[str] = frozenset(
            {
                OWNED_WIP_MISSING_METADATA,
                READY_FOR_CONFIRMED_INTEGRATION,
            }
        ),
    ) -> DeferredIntegrationRecord:
        record = self.load()
        changes = list(workspace_status.get("changes") or [])
        current_head = str(workspace_status.get("head") or "").strip().casefold()
        source_head = str(workspace_status.get("source_head") or "").strip().casefold()
        if (
            record.state not in allowed_states
            or record.workstream_id != str(workstream_id or "").strip().casefold()
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

    def attach_completion(
        self,
        *,
        workstream_id: str,
        workspace_status: dict[str, Any],
        completion: TurnCompletionMetadata,
        now_factory: Any = _now,
    ) -> DeferredIntegrationRecord:
        record = self.verify_owned(
            workstream_id=workstream_id,
            workspace_status=workspace_status,
            allowed_states=frozenset({OWNED_WIP_MISSING_METADATA}),
        )
        updated_at = _validated_timestamp(now_factory(), label="doplnění účtenky")
        return self._write(
            DeferredIntegrationRecord(
                state=READY_FOR_CONFIRMED_INTEGRATION,
                workstream_id=record.workstream_id,
                client_message_id=record.client_message_id,
                base_head=record.base_head,
                change_count=record.change_count,
                change_fingerprint=record.change_fingerprint,
                completion=completion,
                integration_deferred=record.integration_deferred,
                created_at=record.created_at,
                updated_at=updated_at,
            )
        )

    def verify(
        self,
        *,
        workstream_id: str,
        workspace_status: dict[str, Any],
    ) -> DeferredIntegrationRecord:
        record = self.verify_owned(
            workstream_id=workstream_id,
            workspace_status=workspace_status,
            allowed_states=frozenset({READY_FOR_CONFIRMED_INTEGRATION}),
        )
        if record.completion is None:
            raise DeferredIntegrationError(
                "Ownership marker nemá platnou dokončovací účtenku."
            )
        return record

    def clear(self, *, client_message_id: str = "") -> None:
        try:
            if client_message_id and self.path.exists():
                record = self.load()
                if record.client_message_id != str(client_message_id).strip():
                    raise DeferredIntegrationError(
                        "Ownership marker patří jinému zapisovacímu tahu."
                    )
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            raise DeferredIntegrationError(
                "Dokončený ownership marker nelze bezpečně uzavřít."
            ) from exc
