"""Grouped, redacted selection model for the universal workstream menu.

Phase 4.4a is intentionally presentation-neutral. It merges public catalog
identity with redacted legacy/lazy readiness, but does not switch a thread or
expose the model through Cockpit UI until the atomic router is ready.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
    validate_workstream_catalog,
)


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
        legacy_profiles: Mapping[str, str],
        catalog: Iterable[CanonicalWorkstream] = WORKSTREAM_CATALOG,
    ) -> None:
        records = validate_workstream_catalog(catalog)
        by_id = {record.workstream_id: record for record in records}
        unknown_legacy = set(legacy_profiles) - by_id.keys()
        if unknown_legacy:
            raise ValueError("Legacy profil odkazuje na proud mimo katalog.")
        self._records = records
        self._legacy_profiles = {
            str(workstream_id): str(profile_id)
            for workstream_id, profile_id in legacy_profiles.items()
        }

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
        active_legacy_workstream_id: str,
        active_lazy_workstream_id: str,
        thread_status: Mapping[str, Any] | None = None,
        memory_status: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        thread_by_id = self._rows_by_id(thread_status)
        memory_by_id = self._rows_by_id(memory_status)
        lazy_active = str(active_lazy_workstream_id or "").strip()
        legacy_active = str(active_legacy_workstream_id or "").strip()
        active_id = lazy_active or legacy_active
        rows: list[dict[str, Any]] = []
        archived_count = 0
        for record in self._records:
            if record.mode == "archived":
                archived_count += 1
                continue
            thread = thread_by_id.get(record.workstream_id, {})
            memory = memory_by_id.get(record.workstream_id, {})
            profile_id = self._legacy_profiles.get(record.workstream_id, "")
            backend = "legacy_profile" if profile_id else "lazy_private_thread"
            rows.append(
                {
                    "id": record.workstream_id,
                    "type": record.workstream_type,
                    "name": record.name,
                    "mode": record.mode,
                    "priority": record.priority,
                    "backend": backend,
                    "profile_id": profile_id,
                    "active": record.workstream_id == active_id,
                    "available": bool(
                        record.mode != "archived"
                        and (profile_id or thread.get("available") is True)
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
                    "profile_id": active["profile_id"],
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
