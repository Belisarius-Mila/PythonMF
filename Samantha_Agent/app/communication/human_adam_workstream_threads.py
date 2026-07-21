"""Private lazy Codex-thread ownership for canonical workstreams.

Phase 4.2 keeps this backend deliberately separate from Cockpit API and UI.
Catalog inspection is inert: a private directory and a persistent Codex thread
are created only when one concrete workstream is explicitly opened.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Iterable

from app.codex_appserver import AppServerError
from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
    validate_workstream_catalog,
)
from app.communication.session_hub import CanonicalSessionHub, SessionBusyError


WorkstreamHubFactory = Callable[[CanonicalWorkstream, Path], CanonicalSessionHub]
WorkspaceStatusGetter = Callable[[], dict[str, Any]]


class WorkstreamThreadRegistry:
    """Own at most one connected lazy workstream thread in one clean workspace."""

    def __init__(
        self,
        *,
        state_root: Path,
        hub_factory: WorkstreamHubFactory,
        workspace_status: WorkspaceStatusGetter,
        catalog: Iterable[CanonicalWorkstream] = WORKSTREAM_CATALOG,
        reserved_workstream_ids: Iterable[str] = (),
    ):
        records = validate_workstream_catalog(catalog)
        self.state_root = Path(state_root)
        self.hub_factory = hub_factory
        self.workspace_status = workspace_status
        self._records = records
        self._by_id = {record.workstream_id: record for record in records}
        self._reserved_ids = frozenset(str(item).strip() for item in reserved_workstream_ids)
        unknown_reserved = self._reserved_ids - self._by_id.keys()
        if unknown_reserved:
            raise ValueError("Rezervovaný pracovní proud v katalogu neexistuje.")
        self._hubs: dict[str, CanonicalSessionHub] = {}
        self._active_workstream_id = ""
        self._operation_lock = threading.Lock()
        self._state_lock = threading.RLock()

    def _state_path(self, workstream_id: str) -> Path:
        # IDs were validated by the public catalog and cannot traverse paths.
        return self.state_root / workstream_id / "session.json"

    @property
    def active_workstream_id(self) -> str:
        with self._state_lock:
            return self._active_workstream_id

    def active_hub(self, *, expected_workstream_id: str = "") -> CanonicalSessionHub:
        """Return the already materialized active hub without exposing its thread ID."""

        expected = str(expected_workstream_id or "").strip()
        with self._state_lock:
            workstream_id = self._active_workstream_id
            hub = self._hubs.get(workstream_id) if workstream_id else None
        if hub is None:
            raise AppServerError("Není připojený žádný lazy pracovní proud.")
        if expected and expected != workstream_id:
            raise AppServerError("Aktivní lazy pracovní proud se mezitím změnil.")
        return hub

    def checkpoint_workstream_id(self) -> str:
        """Return the active ID only when its thread is safe to checkpoint."""

        with self._state_lock:
            workstream_id = self._active_workstream_id
            hub = self._hubs.get(workstream_id) if workstream_id else None
        if hub is None:
            raise AppServerError("Není připojený žádný lazy pracovní proud.")
        snapshot = hub.snapshot()
        if not snapshot.get("connected"):
            raise AppServerError("Aktivní lazy pracovní proud není připojený.")
        if snapshot.get("turn_busy") or snapshot.get("active_turn"):
            raise SessionBusyError("Checkpoint nelze spustit během aktivního tahu Adama.")
        if self._has_uncertain_delivery(snapshot):
            raise SessionBusyError(
                "Checkpoint nelze spustit, dokud není vyřešené nejisté doručení."
            )
        return workstream_id

    def _record(self, workstream_id: str) -> CanonicalWorkstream:
        clean_id = str(workstream_id or "").strip()
        record = self._by_id.get(clean_id)
        if record is None:
            raise AppServerError("Požadovaný pracovní proud v katalogu neexistuje.")
        return record

    @staticmethod
    def _has_uncertain_delivery(snapshot: dict[str, Any]) -> bool:
        for item in reversed(snapshot.get("messages") or []):
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "")
            if status == "completed":
                return False
            if status in {"pending", "delivery_unknown"} or item.get("recovery_required") is True:
                return True
        return False

    @staticmethod
    def _assert_clean_shared_workspace(status: dict[str, Any]) -> None:
        if (
            status.get("prepared") is not True
            or status.get("ok") is not True
            or status.get("project_ready") is not True
            or status.get("remotes")
        ):
            raise AppServerError("Sdílený pracovní workspace není bezpečně připravený.")
        if status.get("dirty") or status.get("local_checkpoint_ahead"):
            raise AppServerError("Pracovní proud nelze otevřít: sdílený workspace není čistý.")
        if int(status.get("source_pending_changes") or 0) > 0:
            raise AppServerError("Pracovní proud nelze otevřít: main obsahuje pracovní změny.")
        if status.get("workspace_relation") != "aligned" or status.get("source_update_available"):
            raise AppServerError("Pracovní proud nelze otevřít: workspace není synchronní s main.")

    def _hub(self, record: CanonicalWorkstream) -> CanonicalSessionHub:
        with self._state_lock:
            existing = self._hubs.get(record.workstream_id)
            if existing is not None:
                return existing
            hub = self.hub_factory(record, self._state_path(record.workstream_id))
            if not isinstance(hub, CanonicalSessionHub):
                raise TypeError("Factory pracovního proudu nevrátila kanonický session hub.")
            self._hubs[record.workstream_id] = hub
            return hub

    def status(self) -> dict[str, Any]:
        """Return catalog/thread booleans without private paths or thread IDs."""

        with self._state_lock:
            active_id = self._active_workstream_id
            hubs = dict(self._hubs)
        rows: list[dict[str, Any]] = []
        for record in self._records:
            hub = hubs.get(record.workstream_id)
            snapshot = hub.snapshot() if hub is not None else {}
            reserved = record.workstream_id in self._reserved_ids
            rows.append(
                {
                    "id": record.workstream_id,
                    "type": record.workstream_type,
                    "name": record.name,
                    "mode": record.mode,
                    "available": record.mode != "archived" and not reserved,
                    "initialized": self._state_path(record.workstream_id).is_file(),
                    "connected": bool(snapshot.get("connected")),
                    "turn_busy": bool(snapshot.get("turn_busy") or snapshot.get("active_turn")),
                    "message_count": max(0, int(snapshot.get("thread_message_count") or 0)),
                }
            )
        return {
            "ok": True,
            "active_workstream_id": active_id,
            "initialized_count": sum(1 for row in rows if row["initialized"]),
            "connected_count": sum(1 for row in rows if row["connected"]),
            "workstreams": rows,
        }

    def open(self, *, workstream_id: str, confirmed: bool) -> dict[str, Any]:
        """Create or resume one workstream thread after explicit confirmation."""

        if not confirmed:
            raise AppServerError("Otevření pracovního proudu vyžaduje výslovné potvrzení.")
        record = self._record(workstream_id)
        if record.mode == "archived":
            raise AppServerError("Archivovaný pracovní proud nelze otevřít.")
        if record.workstream_id in self._reserved_ids:
            raise AppServerError("Tento pracovní proud zatím vlastní původní pracovní profil.")
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Pracovní proud právě provádí jinou operaci.")
        try:
            self._assert_clean_shared_workspace(self.workspace_status())
            with self._state_lock:
                current_id = self._active_workstream_id
                current = self._hubs.get(current_id) if current_id else None
            if current is not None and current_id != record.workstream_id:
                current_snapshot = current.snapshot()
                if current_snapshot.get("turn_busy") or current_snapshot.get("active_turn"):
                    raise SessionBusyError("Pracovní proud nelze přepnout během aktivního tahu Adama.")
                if self._has_uncertain_delivery(current_snapshot):
                    raise SessionBusyError(
                        "Pracovní proud nelze přepnout, dokud není vyřešené nejisté doručení."
                    )

            target = self._hub(record)
            target_snapshot = target.snapshot()
            if target_snapshot.get("turn_busy") or target_snapshot.get("active_turn"):
                raise SessionBusyError("Cílový pracovní proud už dokončuje aktivní tah.")
            if self._has_uncertain_delivery(target_snapshot):
                raise SessionBusyError("Cílový pracovní proud čeká na vyřešení nejistého doručení.")
            if current is not None and current_id != record.workstream_id:
                current.close()
                with self._state_lock:
                    self._active_workstream_id = ""
            try:
                target.connect()
            except Exception as target_error:
                try:
                    target.close()
                except Exception:
                    # The target never became authoritative. Restoration of the
                    # previous stream is the transaction's primary obligation.
                    pass
                if current is not None and current_id != record.workstream_id:
                    try:
                        current.connect()
                    except Exception as rollback_error:
                        raise AppServerError(
                            "Cílový proud se nepřipojil a původní proud nelze obnovit."
                        ) from rollback_error
                    with self._state_lock:
                        self._active_workstream_id = current_id
                raise target_error
            with self._state_lock:
                self._active_workstream_id = record.workstream_id
            return {
                "ok": True,
                "opened": True,
                "workstream": {
                    "id": record.workstream_id,
                    "type": record.workstream_type,
                    "name": record.name,
                    "mode": record.mode,
                },
                "thread": {
                    "initialized": self._state_path(record.workstream_id).is_file(),
                    "connected": True,
                },
            }
        finally:
            self._operation_lock.release()

    def close_active(self, *, confirmed: bool) -> dict[str, Any]:
        """Disconnect the active lazy thread only after all leave guards pass."""

        if not confirmed:
            raise AppServerError("Odpojení pracovního proudu vyžaduje výslovné potvrzení.")
        if not self._operation_lock.acquire(blocking=False):
            raise SessionBusyError("Pracovní proud právě provádí jinou operaci.")
        try:
            with self._state_lock:
                workstream_id = self._active_workstream_id
                hub = self._hubs.get(workstream_id) if workstream_id else None
            if hub is None:
                return {"ok": True, "closed": False, "workstream_id": ""}
            snapshot = hub.snapshot()
            if snapshot.get("turn_busy") or snapshot.get("active_turn"):
                raise SessionBusyError(
                    "Pracovní proud nelze odpojit během aktivního tahu Adama."
                )
            if self._has_uncertain_delivery(snapshot):
                raise SessionBusyError(
                    "Pracovní proud nelze odpojit, dokud není vyřešené nejisté doručení."
                )
            self._assert_clean_shared_workspace(self.workspace_status())
            hub.close()
            with self._state_lock:
                self._active_workstream_id = ""
            return {"ok": True, "closed": True, "workstream_id": workstream_id}
        finally:
            self._operation_lock.release()

    def close(self) -> None:
        """Disconnect every materialized in-process hub without creating new ones."""

        with self._state_lock:
            hubs = tuple(self._hubs.values())
            self._active_workstream_id = ""
        for hub in hubs:
            try:
                hub.close()
            except SessionBusyError:
                pass
