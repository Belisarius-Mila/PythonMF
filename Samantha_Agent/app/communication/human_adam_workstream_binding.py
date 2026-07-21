"""Validated legacy-profile bindings to canonical workstream identities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG_BY_ID,
    WORKSTREAM_ID_RE,
    WORKSTREAM_TYPES,
)


@dataclass(frozen=True)
class CanonicalWorkstreamBinding:
    """Git-safe workstream identity owned by one compatibility profile."""

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
    """Validate one optional compatibility binding against its service and catalog."""

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
    catalog_record = WORKSTREAM_CATALOG_BY_ID.get(workstream_id)
    if catalog_record is None:
        raise ValueError("Profil odkazuje na pracovní proud mimo kanonický katalog.")
    if (
        workstream_type
        not in {catalog_record.workstream_type, *catalog_record.binding_type_aliases}
        or name not in {catalog_record.name, *catalog_record.binding_aliases}
    ):
        raise ValueError("Profil neodpovídá kanonickému katalogu pracovních proudů.")
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
