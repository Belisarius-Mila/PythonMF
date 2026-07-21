"""Grouped, redacted selection model for the universal workstream menu.

Catalog identity and backend ownership come from one registry. Thread and
memory registries contribute only redacted readiness; they do not decide which
backend owns a workstream.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.communication.human_adam_workstream_backends import WorkstreamBackendRegistry


WORKSTREAM_GROUPS = (
    ("projects", "Projekty", "Project"),
    ("tools", "Tooly", "Tool"),
    ("layers", "Vrstvy", "Layer"),
    ("other", "Ostatní", "Misc"),
)


class GroupedWorkstreamSelection:
    """Build one deterministic menu model without private paths or thread IDs."""

    def __init__(
        self,
        *,
        backend_registry: WorkstreamBackendRegistry,
    ) -> None:
        if not isinstance(backend_registry, WorkstreamBackendRegistry):
            raise TypeError("Výběr pracovních proudů nemá jednotný backendový registr.")
        self._backend_registry = backend_registry
        self._records = backend_registry.catalog()

    @staticmethod
    def _rows_by_id(payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
        if not isinstance(payload, Mapping):
            return {}
        rows = payload.get("workstreams")
        if not isinstance(rows, list):
            return {}
        return {
            str(row.get("id") or ""): dict(row)
            for row in rows
            if isinstance(row, dict) and row.get("id")
        }

    def status(
        self,
        *,
        active_workstream_id: str,
        thread_status: Mapping[str, Any] | None = None,
        memory_status: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        thread_by_id = self._rows_by_id(thread_status)
        memory_by_id = self._rows_by_id(memory_status)
        active_id = str(active_workstream_id or "").strip()
        rows: list[dict[str, Any]] = []
        archived_count = 0
        for record in self._records:
            if record.mode == "archived":
                archived_count += 1
                continue
            thread = thread_by_id.get(record.workstream_id, {})
            memory = memory_by_id.get(record.workstream_id, {})
            binding = self._backend_registry.binding(record.workstream_id)
            backend = binding.backend
            rows.append(
                {
                    "id": record.workstream_id,
                    "type": record.workstream_type,
                    "name": record.name,
                    "mode": record.mode,
                    "priority": record.priority,
                    "backend": backend,
                    "active": record.workstream_id == active_id,
                    "available": bool(
                        record.mode != "archived"
                        and (
                            binding.compatibility_adapter is not None
                            or thread.get("available") is True
                        )
                    ),
                    "thread_initialized": bool(thread.get("initialized")),
                    "memory_ready": bool(memory.get("memory_ready")),
                }
            )

        active = next((row for row in rows if row["active"]), None)
        groups: list[dict[str, Any]] = []
        for group_id, label, workstream_type in WORKSTREAM_GROUPS:
            group_rows = [
                row
                for row in rows
                if row["type"] == workstream_type and row["mode"] == "active"
            ]
            groups.append(
                {
                    "id": group_id,
                    "label": label,
                    "workstreams": group_rows,
                    "count": len(group_rows),
                }
            )
        paused = [row for row in rows if row["mode"] == "paused"]
        return {
            "ok": active is not None,
            "private_backend": True,
            "active": (
                {
                    "workstream_id": active["id"],
                    "workstream_type": active["type"],
                    "workstream_name": active["name"],
                    "backend": active["backend"],
                }
                if active is not None
                else {}
            ),
            "groups": groups,
            "paused": paused,
            "workstreams": rows,
            "workstream_count": len(rows),
            "active_count": sum(1 for row in rows if row["mode"] == "active"),
            "paused_count": len(paused),
            "archived_count": archived_count,
        }
