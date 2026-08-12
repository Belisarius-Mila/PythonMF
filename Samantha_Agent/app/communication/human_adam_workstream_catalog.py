"""Git-safe canonical catalog of Human–Adam workstreams.

Phase 4.1 deliberately keeps this catalog independent from UI, profiles,
workspaces and private Codex threads. Runtime bindings may reference catalog
records, but an unbound record does not create or start any private resource.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import PurePosixPath
from typing import Iterable


WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
WORKSTREAM_TYPES = frozenset({"Project", "Tool", "Layer", "Misc"})
WORKSTREAM_MODES = frozenset({"active", "paused", "archived"})
PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES = (
    "delete",
    "bulk_change",
    "external_send",
    "system_change",
)


@dataclass(frozen=True)
class CanonicalWorkstreamCapabilities:
    """Declarative, git-safe capability metadata for one workstream."""

    network_read_only_research: bool = True
    image_generation: bool = False
    private_archive_direct: bool = False
    private_archive_read: bool = False
    private_archive_single_edit: bool = False
    source_data_read_only: bool = False
    private_archive_confirmation_required: tuple[str, ...] = ()
    private_archive_root: str = ""
    owned_private_root: str = ""

    def validate(self) -> None:
        flags = (
            self.network_read_only_research,
            self.image_generation,
            self.private_archive_direct,
            self.private_archive_read,
            self.private_archive_single_edit,
            self.source_data_read_only,
        )
        if any(type(flag) is not bool for flag in flags):
            raise ValueError("Pracovní proud má neplatná capability metadata.")
        archive_flags = (
            self.private_archive_direct,
            self.private_archive_read,
            self.private_archive_single_edit,
        )
        if self.source_data_read_only and any(archive_flags):
            raise ValueError(
                "Read-only zdrojová data nelze kombinovat s přímou editací archivu."
            )
        if not isinstance(self.private_archive_confirmation_required, tuple):
            raise ValueError("Pracovní proud má neplatné private archive capability.")
        enabled = any(archive_flags)
        if not enabled:
            if self.private_archive_confirmation_required or self.private_archive_root:
                raise ValueError("Pracovní proud má neplatné private archive capability.")
        else:
            if not all(archive_flags):
                raise ValueError("Pracovní proud má neúplné private archive capability.")
            if (
                self.private_archive_confirmation_required
                != PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES
            ):
                raise ValueError(
                    "Pracovní proud má neplatné private archive potvrzovací kategorie."
                )
            self._validate_private_root(
                self.private_archive_root,
                kind="private archive",
            )
        if not isinstance(self.owned_private_root, str):
            raise ValueError("Pracovní proud má neplatný owned private root.")
        if self.owned_private_root:
            if not self.source_data_read_only or enabled:
                raise ValueError(
                    "Vlastněný private kořen vyžaduje read-only zdrojová data "
                    "a nesmí se překrývat s přímým archivem."
                )
            self._validate_private_root(
                self.owned_private_root,
                kind="owned private",
            )

    @staticmethod
    def _validate_private_root(value: str, *, kind: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"Pracovní proud má neplatný {kind} root.")
        root = PurePosixPath(value)
        if (
            not value
            or root.is_absolute()
            or ".." in root.parts
            or root.parts[:2] != ("data", "private")
            or len(root.parts) < 3
            or root.as_posix() != value
        ):
            raise ValueError(f"Pracovní proud má neplatný {kind} root.")

    @property
    def private_archive_enabled(self) -> bool:
        self.validate()
        return self.private_archive_direct

    def status_fields(self) -> dict[str, object]:
        return {
            "network_read_only_research": self.network_read_only_research,
            "image_generation": self.image_generation,
            "private_archive_direct": self.private_archive_direct,
            "private_archive_read": self.private_archive_read,
            "private_archive_single_edit": self.private_archive_single_edit,
            "source_data_read_only": self.source_data_read_only,
            "owned_private_write": bool(self.owned_private_root),
            "private_archive_confirmation_required": list(
                self.private_archive_confirmation_required
            ),
        }


@dataclass(frozen=True)
class CanonicalWorkstream:
    """One public, git-safe workstream identity without private runtime state."""

    workstream_id: str
    workstream_type: str
    name: str
    mode: str
    priority: str
    source_names: tuple[str, ...]
    query_aliases: tuple[str, ...] = ()
    binding_aliases: tuple[str, ...] = ()
    binding_type_aliases: tuple[str, ...] = ()
    capabilities: CanonicalWorkstreamCapabilities = CanonicalWorkstreamCapabilities()


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
    seen_query_aliases: set[str] = set()
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
        clean_query_aliases = tuple(
            _clean_label(alias, kind="alias dotazu") for alias in record.query_aliases
        )
        folded_query_aliases = tuple(alias.casefold() for alias in clean_query_aliases)
        if (
            clean_query_aliases != record.query_aliases
            or len(set(folded_query_aliases)) != len(folded_query_aliases)
            or any(alias in seen_query_aliases for alias in folded_query_aliases)
        ):
            raise ValueError("Pracovní proud nemá jednoznačné aliasy dotazu.")
        if folded_name in folded_query_aliases:
            raise ValueError("Kanonický název nesmí být zopakován jako alias dotazu.")
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
        if not isinstance(record.capabilities, CanonicalWorkstreamCapabilities):
            raise ValueError("Pracovní proud nemá platná capability metadata.")
        record.capabilities.validate()
        seen_ids.add(record.workstream_id)
        seen_names.add(folded_name)
        seen_query_aliases.update(folded_query_aliases)
    return catalog


def _record(
    workstream_id: str,
    workstream_type: str,
    name: str,
    mode: str,
    priority: str,
    *source_names: str,
    query_aliases: tuple[str, ...] = (),
    binding_aliases: tuple[str, ...] = (),
    binding_type_aliases: tuple[str, ...] = (),
    capabilities: CanonicalWorkstreamCapabilities = CanonicalWorkstreamCapabilities(),
    image_generation: bool = True,
) -> CanonicalWorkstream:
    return CanonicalWorkstream(
        workstream_id=workstream_id,
        workstream_type=workstream_type,
        name=name,
        mode=mode,
        priority=priority,
        source_names=source_names,
        query_aliases=query_aliases,
        binding_aliases=binding_aliases,
        binding_type_aliases=binding_type_aliases,
        capabilities=replace(capabilities, image_generation=image_generation),
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
            query_aliases=("R2 Adam",),
            capabilities=CanonicalWorkstreamCapabilities(
                source_data_read_only=True,
                owned_private_root=(
                    "data/private/communication/workstreams/"
                    "project-r2-adam-janicka/documents"
                ),
            ),
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
            capabilities=CanonicalWorkstreamCapabilities(
                network_read_only_research=True,
                private_archive_direct=True,
                private_archive_read=True,
                private_archive_single_edit=True,
                private_archive_confirmation_required=(
                    PRIVATE_ARCHIVE_CONFIRMATION_CATEGORIES
                ),
                private_archive_root="data/private/article_archive",
            ),
        ),
        _record(
            "project-family-calendar",
            "Project",
            "Rodinný kalendář",
            "active",
            "1",
            "Rodinný kalendář",
            query_aliases=("Kalendář",),
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
            "TTS / české audio nástroje",
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
            "project-to-be-to-have",
            "Project",
            "ToBeToHave",
            "active",
            "2",
            "ToBeToHave",
            query_aliases=("To Be Training", "ToBeTraining"),
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
            "TTS / české audio nástroje",
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
