"""Canonical git-safe handoff and TVBCP bindings for every workstream.

Phase 4.3 defines paths and initial document contracts without materializing
dozens of empty files at Cockpit startup. Missing documents are created by the
confirmed checkpoint transaction that first needs them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.codex_appserver import AppServerError
from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
    validate_workstream_catalog,
)


LEGACY_MEMORY_PATHS: Mapping[str, tuple[str, str]] = {
    "layer-human-adam-development": (
        "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
        "memory/tvbcp/architektura_komunikace_samantha.txt",
    ),
    "project-knowledge-library": (
        "memory/handoffs/knowledge_library_article_editing_2026_07_16.md",
        "memory/tvbcp/knihovna_cockpit.txt",
    ),
}


@dataclass(frozen=True)
class WorkstreamMemoryBinding:
    workstream_id: str
    workstream_type: str
    name: str
    mode: str
    priority: str
    handoff_relative_path: str
    tvbcp_relative_path: str
    legacy_document: bool = False


def canonical_memory_path(value: object, *, kind: str) -> str:
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
        raise ValueError(f"Kanonická vazba nemá platnou cestu k {kind}.")
    return path.as_posix()


class WorkstreamMemoryRegistry:
    """Resolve exactly one handoff/TVBCP pair for each catalog identity."""

    def __init__(
        self,
        *,
        catalog: Iterable[CanonicalWorkstream] = WORKSTREAM_CATALOG,
        legacy_paths: Mapping[str, tuple[str, str]] = LEGACY_MEMORY_PATHS,
    ) -> None:
        records = validate_workstream_catalog(catalog)
        by_id = {record.workstream_id: record for record in records}
        unknown_legacy = set(legacy_paths) - by_id.keys()
        if unknown_legacy:
            raise ValueError("Legacy paměť odkazuje na proud mimo katalog.")
        bindings: list[WorkstreamMemoryBinding] = []
        seen_paths: set[str] = set()
        for record in records:
            legacy = legacy_paths.get(record.workstream_id)
            if legacy is None:
                handoff = f"memory/handoffs/workstreams/{record.workstream_id}.md"
                tvbcp = f"memory/tvbcp/workstreams/{record.workstream_id}.md"
            else:
                handoff, tvbcp = legacy
            handoff = canonical_memory_path(handoff, kind="handoff")
            tvbcp = canonical_memory_path(tvbcp, kind="tvbcp")
            if handoff == tvbcp or handoff in seen_paths or tvbcp in seen_paths:
                raise ValueError("Dva pracovní proudy nesmějí sdílet kanonickou paměť.")
            seen_paths.update((handoff, tvbcp))
            bindings.append(
                WorkstreamMemoryBinding(
                    workstream_id=record.workstream_id,
                    workstream_type=record.workstream_type,
                    name=record.name,
                    mode=record.mode,
                    priority=record.priority,
                    handoff_relative_path=handoff,
                    tvbcp_relative_path=tvbcp,
                    legacy_document=legacy is not None,
                )
            )
        self._bindings = tuple(bindings)
        self._by_id = {binding.workstream_id: binding for binding in bindings}

    def binding(self, workstream_id: str) -> WorkstreamMemoryBinding:
        clean_id = str(workstream_id or "").strip().casefold()
        binding = self._by_id.get(clean_id)
        if binding is None:
            raise AppServerError("Pracovní proud nemá kanonickou paměťovou vazbu.")
        return binding

    def bindings(self) -> tuple[WorkstreamMemoryBinding, ...]:
        return self._bindings

    @staticmethod
    def initial_handoff(binding: WorkstreamMemoryBinding) -> str:
        return f"""# Handoff pracovního proudu: {binding.name}

Nazev: {binding.name}
Pracovni proud: {binding.workstream_id}
Typ: {binding.workstream_type}
Priorita: {binding.priority}
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
Kanonicky handoff byl zalozen prvnim potvrzenym checkpointem tohoto proudu.

Co je hotove:
- Viz chronologicke checkpointy nize.

Co neni hotove:
- Viz posledni checkpoint a jeho dalsi krok.

Dalsi krok:
Viz posledni chronologicky checkpoint.

Navrhovane dalsi kroky:
- Prubezne aktualizovat pouze potvrzenymi checkpointy tohoto proudu.

Zmenene nebo relevantni soubory:
- Viz jednotlive checkpointy.

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.
"""

    @staticmethod
    def initial_tvbcp(binding: WorkstreamMemoryBinding) -> str:
        return f"""# TVBCP: {binding.name}

Pracovni proud: `{binding.workstream_id}`
Typ: `{binding.workstream_type}`
Rezim: `{binding.mode}`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.
"""

    def status(self, *, project_root: Path | None = None) -> dict[str, Any]:
        root = Path(project_root).resolve() if project_root is not None else None
        rows: list[dict[str, Any]] = []
        for binding in self._bindings:
            handoff_exists = False
            tvbcp_exists = False
            if root is not None:
                handoff_exists = (root / binding.handoff_relative_path).is_file()
                tvbcp_exists = (root / binding.tvbcp_relative_path).is_file()
            rows.append(
                {
                    "id": binding.workstream_id,
                    "type": binding.workstream_type,
                    "name": binding.name,
                    "mode": binding.mode,
                    "legacy_document": binding.legacy_document,
                    "handoff_ready": handoff_exists,
                    "tvbcp_ready": tvbcp_exists,
                    "memory_ready": handoff_exists and tvbcp_exists,
                }
            )
        return {
            "ok": True,
            "workstream_count": len(rows),
            "ready_count": sum(1 for row in rows if row["memory_ready"]),
            "workstreams": rows,
        }
