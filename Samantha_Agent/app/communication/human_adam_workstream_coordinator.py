"""Private workstream catalog and routing for Human–Adam profile bundles.

The coordinator deliberately has no HTTP or UI surface.  It owns only git-safe
workstream identities and maps them to existing isolated profile bundles.  The
profile manager keeps responsibility for transactional thread switching and
workspace synchronization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from app.codex_appserver import AppServerError


WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
WORKSTREAM_TYPES = frozenset({"Project", "Tool", "Layer", "Misc"})


@dataclass(frozen=True)
class CanonicalWorkstreamBinding:
    """Git-safe workstream identity owned by one Human–Adam profile."""

    workstream_id: str
    workstream_type: str
    name: str
    handoff_relative_path: str
    tvbcp_relative_path: str


def _canonical_memory_path(value: object, *, kind: str) -> str:
    text = str(value or "").strip()
    path = Path(text)
    expected_parent = "handoffs" if kind == "handoff" else "tvbcp"
    suffixes = {".md"} if kind == "handoff" else {".md", ".txt"}
    if (
        not text
        or path.is_absolute()
        or ".." in path.parts
        or len(path.parts) < 3
        or path.parts[:2] != ("memory", expected_parent)
        or path.suffix.casefold() not in suffixes
    ):
        raise ValueError(f"Kanonická vazba profilu nemá platnou cestu k {kind}.")
    return path.as_posix()


def canonical_workstream_binding(
    *,
    profile_id: str,
    profile: Mapping[str, Any],
) -> CanonicalWorkstreamBinding | None:
    """Validate one optional workstream binding against its profile service."""

    raw = profile.get("workstream")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Kanonická vazba pracovního proudu profilu není platná.")
    workstream_id = str(raw.get("id") or "").strip().casefold()
    workstream_type = str(raw.get("type") or "").strip()
    name = " ".join(str(raw.get("name") or "").split())
    if not WORKSTREAM_ID_RE.fullmatch(workstream_id):
        raise ValueError("Kanonická vazba profilu nemá platné ID pracovního proudu.")
    if workstream_type not in WORKSTREAM_TYPES:
        raise ValueError("Kanonická vazba profilu nemá platný typ pracovního proudu.")
    if not name or len(name) > 160:
        raise ValueError("Kanonická vazba profilu nemá platný název pracovního proudu.")
    handoff_path = _canonical_memory_path(raw.get("handoff"), kind="handoff")
    tvbcp_path = _canonical_memory_path(raw.get("tvbcp"), kind="tvbcp")
    service = profile["service"]
    if service.work_profile_id != profile_id:
        raise ValueError("Profil a jeho služba nemají shodný bezpečný identifikátor.")
    if service.tvbcp_relative_path.as_posix() != tvbcp_path:
        raise ValueError("Kanonický TVBCP pracovního proudu neodpovídá TVBCP profilu.")
    return CanonicalWorkstreamBinding(
        workstream_id=workstream_id,
        workstream_type=workstream_type,
        name=name,
        handoff_relative_path=handoff_path,
        tvbcp_relative_path=tvbcp_path,
    )


class HumanAdamWorkstreamCoordinator:
    """Resolve registered workstreams without exposing private thread state."""

    def __init__(self, profiles: Mapping[str, Mapping[str, Any]]) -> None:
        self._profiles = profiles
        self._profile_by_workstream: dict[str, str] = {}
        for profile_id, profile in profiles.items():
            binding = profile.get("workstream_binding")
            if binding is None:
                continue
            if not isinstance(binding, CanonicalWorkstreamBinding):
                raise ValueError("Profil obsahuje neověřenou vazbu pracovního proudu.")
            if binding.workstream_id in self._profile_by_workstream:
                raise ValueError("Dva profily nesmějí vlastnit stejný pracovní proud.")
            self._profile_by_workstream[binding.workstream_id] = profile_id

    def profile_id_for(self, workstream_id: str) -> str:
        clean_id = str(workstream_id or "").strip().casefold()
        if not WORKSTREAM_ID_RE.fullmatch(clean_id):
            raise AppServerError("Požadovaný pracovní proud nemá platný identifikátor.")
        profile_id = self._profile_by_workstream.get(clean_id)
        if not profile_id:
            raise AppServerError("Požadovaný pracovní proud není zaregistrovaný.")
        return profile_id

    def context(self, active_profile_id: str) -> dict[str, Any]:
        profile = self._profiles.get(active_profile_id)
        if profile is None:
            raise AppServerError("Aktivní profil pracovního proudu není známý.")
        binding = profile.get("workstream_binding")
        if not isinstance(binding, CanonicalWorkstreamBinding):
            return {
                "available": False,
                "profile_id": active_profile_id,
                "profile_label": str(profile.get("label") or active_profile_id),
                "message": (
                    "Aktivní profil nemá v terminálu zaregistrovaný kanonický pracovní proud."
                ),
            }
        return {
            "available": True,
            "profile_id": active_profile_id,
            "profile_label": str(profile.get("label") or active_profile_id),
            "workstream_id": binding.workstream_id,
            "workstream_type": binding.workstream_type,
            "workstream_name": binding.name,
            "handoff_relative_path": binding.handoff_relative_path,
            "tvbcp_relative_path": binding.tvbcp_relative_path,
        }

    def status(self, active_profile_id: str) -> dict[str, Any]:
        active = self.context(active_profile_id)
        rows: list[dict[str, Any]] = []
        for profile_id, profile in self._profiles.items():
            binding = profile.get("workstream_binding")
            if not isinstance(binding, CanonicalWorkstreamBinding):
                continue
            rows.append(
                {
                    "id": binding.workstream_id,
                    "type": binding.workstream_type,
                    "name": binding.name,
                    "profile_id": profile_id,
                    "profile_label": str(profile.get("label") or profile_id),
                    "active": profile_id == active_profile_id,
                }
            )
        return {
            "ok": active.get("available") is True,
            "private_backend": True,
            "active": active,
            "workstreams": rows,
            "workstream_count": len(rows),
        }
