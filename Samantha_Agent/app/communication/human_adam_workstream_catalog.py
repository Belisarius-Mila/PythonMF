"""Git-safe canonical catalog of Human–Adam workstreams.

Phase 4.1 deliberately keeps this catalog independent from UI, profiles,
workspaces and private Codex threads. Runtime bindings may reference catalog
records, but an unbound record does not create or start any private resource.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
WORKSTREAM_TYPES = frozenset({"Project", "Tool", "Layer", "Misc"})
WORKSTREAM_MODES = frozenset({"active", "paused", "archived"})


@dataclass(frozen=True)
class CanonicalWorkstream:
    """One public, git-safe workstream identity without private runtime state."""

    workstream_id: str
    workstream_type: str
    name: str
    mode: str
    priority: str
    source_names: tuple[str, ...]
    binding_aliases: tuple[str, ...] = ()
    binding_type_aliases: tuple[str, ...] = ()


def _clean_label(value: str, *, kind: str) -> str:
    clean = " ".join(str(value or "").split())
    if not clean or len(clean) > 160:
        raise ValueError(f"Katalog obsahuje neplatný {kind} pracovního proudu.")
    return clean


def validate_workstream_catalog(
    records: Iterable[CanonicalWorkstream],
) -> tuple[CanonicalWorkstream, ...]:
    """Validate and return a deterministic workstream catalog."""

    catalog = tuple(records)
    if not catalog:
        raise ValueError("Katalog pracovních proudů nesmí být prázdný.")
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for record in catalog:
        if not isinstance(record, CanonicalWorkstream):
            raise ValueError("Katalog obsahuje neověřený pracovní proud.")
        if not WORKSTREAM_ID_RE.fullmatch(record.workstream_id):
            raise ValueError("Katalog obsahuje neplatné ID pracovního proudu.")
        if record.workstream_id in seen_ids:
            raise ValueError("Katalog obsahuje duplicitní ID pracovního proudu.")
        if record.workstream_type not in WORKSTREAM_TYPES:
            raise ValueError("Katalog obsahuje neplatný typ pracovního proudu.")
        if record.mode not in WORKSTREAM_MODES:
            raise ValueError("Katalog obsahuje neplatný režim pracovního proudu.")
        name = _clean_label(record.name, kind="název")
        if name != record.name:
            raise ValueError("Katalog obsahuje nekanonický název pracovního proudu.")
        folded_name = name.casefold()
        if folded_name in seen_names:
            raise ValueError("Katalog obsahuje duplicitní název pracovního proudu.")
        if record.priority not in {"1", "2", "3"}:
            raise ValueError("Katalog obsahuje neplatnou prioritu pracovního proudu.")
        if record.workstream_type == "Misc":
            if record.source_names:
                raise ValueError("Výchozí Misc proud nesmí předstírat projektový zdroj.")
        elif not record.source_names:
            raise ValueError("Pracovní proud nemá kanonický paměťový zdroj.")
        clean_sources = tuple(
            _clean_label(source_name, kind="zdroj") for source_name in record.source_names
        )
        if clean_sources != record.source_names or len(set(clean_sources)) != len(clean_sources):
            raise ValueError("Pracovní proud nemá jednoznačné kanonické zdroje.")
        clean_aliases = tuple(
            _clean_label(alias, kind="alias") for alias in record.binding_aliases
        )
        if clean_aliases != record.binding_aliases or len(set(clean_aliases)) != len(clean_aliases):
            raise ValueError("Pracovní proud nemá jednoznačné aliasy runtime vazby.")
        if name in clean_aliases:
            raise ValueError("Kanonický název nesmí být zopakován jako alias.")
        if any(alias not in WORKSTREAM_TYPES for alias in record.binding_type_aliases):
            raise ValueError("Pracovní proud obsahuje neplatný alias typu runtime vazby.")
        if record.workstream_type in record.binding_type_aliases:
            raise ValueError("Kanonický typ nesmí být zopakován jako alias.")
        if len(set(record.binding_type_aliases)) != len(record.binding_type_aliases):
            raise ValueError("Pracovní proud nemá jednoznačné aliasy typu runtime vazby.")
        seen_ids.add(record.workstream_id)
        seen_names.add(folded_name)
    return catalog


def _record(
    workstream_id: str,
    workstream_type: str,
    name: str,
    mode: str,
    priority: str,
    *source_names: str,
    binding_aliases: tuple[str, ...] = (),
    binding_type_aliases: tuple[str, ...] = (),
) -> CanonicalWorkstream:
    return CanonicalWorkstream(
        workstream_id=workstream_id,
        workstream_type=workstream_type,
        name=name,
        mode=mode,
        priority=priority,
        source_names=source_names,
        binding_aliases=binding_aliases,
        binding_type_aliases=binding_type_aliases,
    )


WORKSTREAM_CATALOG = validate_workstream_catalog(
    (
        # Projects: long-lived goals and areas of work.
        _record("project-mmtx", "Project", "MMTX", "active", "1", "MMTX"),
        _record(
            "project-janicka-cockpit",
            "Project",
            "Janička Cockpit",
            "active",
            "1",
            "Janička Cockpit / používání a převzetí Samanthy",
        ),
        _record(
            "project-r2-adam-janicka",
            "Project",
            "R2-Adam / Janička",
            "active",
            "2",
            "R2-Adam / Janička",
        ),
        _record(
            "project-family-emergency-plan",
            "Project",
            "Pozůstalost / rodinný nouzový balík",
            "active",
            "1",
            "Pozustalost / rodinny nouzovy balik",
        ),
        _record(
            "project-neuberk-kacenka",
            "Project",
            "Neuberk interiér / Kačenka",
            "active",
            "2",
            "Neuberk interier design / Kacenka",
        ),
        _record(
            "project-samantha-agent-rag",
            "Project",
            "Samantha Agent / RAG",
            "active",
            "1",
            "Samantha Agent/RAG",
        ),
        _record(
            "project-knowledge-library",
            "Project",
            "Knihovna",
            "active",
            "2",
            "Znalostni databaze / Knihovna clanku / Knowledge inbox",
        ),
        _record(
            "project-family-calendar",
            "Project",
            "Rodinný kalendář",
            "active",
            "1",
            "Rodinný kalendář",
        ),
        _record(
            "project-document-vault",
            "Project",
            "Správa dokumentů / private vault",
            "active",
            "1",
            "Sprava dokumentu / private vault",
            "Reminders / platebni SMS",
        ),
        _record(
            "project-shopping-archive",
            "Project",
            "Nákupní průzkum a archiv nákupů",
            "active",
            "2",
            "Nakupni pruzkum a archiv nakupu",
        ),
        _record(
            "project-email-cases",
            "Project",
            "iCloud Mail / Email Cases",
            "active",
            "1",
            "iCloud Mail read-only / Email Cases",
        ),
        _record("project-lekarna", "Project", "Lékárna", "active", "1", "Lekarna"),
        _record(
            "project-tomik-video",
            "Project",
            "Tomík video / FamilyVideoOrganizer",
            "active",
            "1",
            "Tomik video iMovie / FamilyVideoOrganizer",
        ),
        _record(
            "project-family-memory-films",
            "Project",
            "Family Memory Films / USA 2019",
            "active",
            "1",
            "Family Memory Films / USA 2019",
        ),
        _record("project-multilo", "Project", "MultiLO", "active", "2", "MultiLO"),
        _record("project-tax-2025", "Project", "Daňové přiznání 2025", "active", "3", "Tax"),
        _record(
            "project-cockpit",
            "Project",
            "Cockpit / hlavní architektura",
            "active",
            "1",
            "Cockpit hlavni architektura / modernizace",
            "Cockpit Recovery centrum",
            "TTS / Adam Voice Remote Cockpit",
        ),
        _record(
            "layer-human-adam-development",
            "Project",
            "Human–Adam",
            "active",
            "1",
            "App-server rozhrani / novy Adam",
            binding_aliases=("Human–Adam / vývojové prostředí",),
            binding_type_aliases=("Layer",),
        ),
        _record(
            "project-capability-catalog",
            "Project",
            "Katalog projektů a schopností",
            "active",
            "1",
            "Mapovani projektu a schopnosti",
        ),
        _record(
            "project-samantha-infrastructure",
            "Project",
            "Samantha Infrastructure",
            "active",
            "1",
            "Samantha Infrastructure",
            "Codex full access / Guard proti mazani",
        ),
        _record(
            "project-mobile-input",
            "Project",
            "iPhone Shortcuts / Mobile Input",
            "paused",
            "2",
            "iPhone Shortcuts / Mobile Input Layer",
        ),
        _record(
            "project-colors-and-numbers",
            "Project",
            "ColorsAndNumbers / automatické úkoly",
            "active",
            "1",
            "Automaticke opakujici se ukoly / ColorsAndNumbers",
        ),
        _record(
            "project-vocabulary-fr",
            "Project",
            "Vocabulary FR",
            "paused",
            "2",
            "Vocabulary FR",
        ),
        _record(
            "project-vocabulary-it",
            "Project",
            "Vocabulary IT",
            "paused",
            "2",
            "Vocabulary IT",
        ),
        # Tools: concrete reusable executors and workflows.
        _record(
            "tool-backup-restore",
            "Tool",
            "Záloha a obnova",
            "active",
            "1",
            "Samantha external backup",
        ),
        _record(
            "tool-media-image-resize",
            "Tool",
            "Zmenšování obrázků",
            "active",
            "1",
            "Media image resize utility",
        ),
        _record(
            "tool-vocabulary-image-pipeline",
            "Tool",
            "PictNew / obrázky ke slovíčkům",
            "active",
            "2",
            "PictNew / Vocabulary image workflow",
        ),
        _record(
            "tool-tts",
            "Tool",
            "TTS",
            "active",
            "1",
            "TTS / Adam Voice Remote Cockpit",
        ),
        # Default uncategorized streams agreed for the universal catalog.
        _record("misc-brainstorm", "Misc", "Brainstorm / nápady", "active", "2"),
        _record(
            "misc-unclassified-development",
            "Misc",
            "Miscellaneous / nezařazený vývoj",
            "active",
            "2",
        ),
    )
)

WORKSTREAM_CATALOG_BY_ID = {record.workstream_id: record for record in WORKSTREAM_CATALOG}
