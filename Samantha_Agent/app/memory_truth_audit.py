"""Deterministic, read-only audit of Samantha workstream memory authority.

P0 deliberately compares only machine-verifiable registry facts:

- canonical workstream identity, lifecycle and priority,
- matching rows in ``memory/ACTIVE_PROJECTS.md``,
- existence of the canonical handoff and TVBCP,
- Git commit timestamps as a review signal, never as proof of truth.

The audit does not read canonical handoff/TVBCP contents, create missing files,
repair memory, or inspect private data.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
    validate_workstream_catalog,
)
from app.communication.human_adam_workstream_memory import (
    WorkstreamMemoryBinding,
    WorkstreamMemoryRegistry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PROJECTS_RELATIVE_PATH = "memory/ACTIVE_PROJECTS.md"

STATUS_PROVEN_CONTRADICTION = "proven_contradiction"
STATUS_UNMATERIALIZED = "unmaterialized"
STATUS_UNVERIFIABLE = "unverifiable"
STATUS_CANDIDATE_DRIFT = "candidate_drift"
STATUS_REGISTRY_CONSISTENT = "registry_consistent"


@dataclass(frozen=True)
class ActiveProjectRow:
    name: str
    priority: str
    mode: str
    line_number: int


@dataclass(frozen=True)
class GitFileEvidence:
    committed_at: str | None = None
    commit: str | None = None


@dataclass(frozen=True)
class MemoryTruthAuditRow:
    workstream_id: str
    workstream_type: str
    name: str
    expected_mode: str
    expected_priority: str
    source_names: tuple[str, ...]
    matched_sources: tuple[str, ...]
    aggregate_rows: tuple[ActiveProjectRow, ...]
    handoff_path: str
    tvbcp_path: str
    handoff_exists: bool
    tvbcp_exists: bool
    aggregate_committed_at: str | None
    canonical_latest_committed_at: str | None
    canonical_newer_than_aggregate: bool
    contradictions: tuple[str, ...]
    evidence_codes: tuple[str, ...]
    status: str

    @property
    def memory_ready(self) -> bool:
        return self.handoff_exists and self.tvbcp_exists

    @property
    def aggregate_covered(self) -> bool:
        return bool(self.aggregate_rows)


@dataclass(frozen=True)
class MemoryTruthAuditResult:
    generated_at: str
    active_projects_path: str
    workstream_count: int
    aggregate_row_count: int
    aggregate_covered_count: int
    memory_ready_count: int
    proven_contradiction_count: int
    candidate_drift_count: int
    status_counts: dict[str, int]
    rows: tuple[MemoryTruthAuditRow, ...]


EvidenceLoader = Callable[[str], GitFileEvidence]
Runner = Callable[..., subprocess.CompletedProcess[str]]


def _normalized_label(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("–", "-").replace("—", "-")
    return " ".join(text.casefold().split())


def _normalized_header(value: object) -> str:
    return _normalized_label(value).replace(" ", "_")


def parse_active_project_registry(text: str) -> tuple[ActiveProjectRow, ...]:
    """Parse only public registry coordinates; ignore status and next-step text."""

    rows: list[ActiveProjectRow] = []
    headers: list[str] | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if headers is None:
            normalized = [_normalized_header(cell) for cell in cells]
            if {"oblast", "priorita", "rezim"}.issubset(normalized):
                headers = normalized
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        values = dict(zip(headers, cells[: len(headers)], strict=False))
        name = " ".join(values.get("oblast", "").split())
        priority = " ".join(values.get("priorita", "").split())
        mode = _normalized_label(values.get("rezim", ""))
        if name:
            rows.append(
                ActiveProjectRow(
                    name=name,
                    priority=priority,
                    mode=mode,
                    line_number=line_number,
                )
            )
    return tuple(rows)


def git_file_evidence(
    project_root: Path,
    relative_path: str,
    *,
    runner: Runner = subprocess.run,
) -> GitFileEvidence:
    """Return the latest committed timestamp without reading file contents."""

    completed = runner(
        [
            "git",
            "-C",
            str(project_root),
            "log",
            "-1",
            "--format=%cI%x09%H",
            "--",
            relative_path,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return GitFileEvidence()
    first_line = str(completed.stdout or "").strip().splitlines()
    if not first_line:
        return GitFileEvidence()
    committed_at, separator, commit = first_line[0].partition("\t")
    if not separator or not _parse_timestamp(committed_at):
        return GitFileEvidence()
    return GitFileEvidence(committed_at=committed_at, commit=commit or None)


def run_memory_truth_audit(
    *,
    project_root: Path = PROJECT_ROOT,
    catalog: Iterable[CanonicalWorkstream] = WORKSTREAM_CATALOG,
    registry: WorkstreamMemoryRegistry | None = None,
    evidence_loader: EvidenceLoader | None = None,
    generated_at: str | None = None,
) -> MemoryTruthAuditResult:
    """Audit all catalog workstreams without mutating the workspace."""

    root = Path(project_root).resolve()
    records = validate_workstream_catalog(catalog)
    memory_registry = registry or WorkstreamMemoryRegistry(catalog=records)
    bindings = {binding.workstream_id: binding for binding in memory_registry.bindings()}
    if set(bindings) != {record.workstream_id for record in records}:
        raise ValueError("Memory registry neodpovídá auditovanému katalogu.")

    active_path = root / ACTIVE_PROJECTS_RELATIVE_PATH
    active_text = active_path.read_text(encoding="utf-8")
    active_rows = parse_active_project_registry(active_text)
    rows_by_name: dict[str, list[ActiveProjectRow]] = {}
    for row in active_rows:
        rows_by_name.setdefault(_normalized_label(row.name), []).append(row)

    load_evidence = evidence_loader or (
        lambda relative_path: git_file_evidence(root, relative_path)
    )
    aggregate_evidence = load_evidence(ACTIVE_PROJECTS_RELATIVE_PATH)

    audit_rows = tuple(
        _audit_workstream(
            root=root,
            record=record,
            binding=bindings[record.workstream_id],
            rows_by_name=rows_by_name,
            aggregate_evidence=aggregate_evidence,
            evidence_loader=load_evidence,
        )
        for record in records
    )
    status_counts = {
        status: sum(1 for row in audit_rows if row.status == status)
        for status in (
            STATUS_PROVEN_CONTRADICTION,
            STATUS_UNMATERIALIZED,
            STATUS_UNVERIFIABLE,
            STATUS_CANDIDATE_DRIFT,
            STATUS_REGISTRY_CONSISTENT,
        )
    }
    return MemoryTruthAuditResult(
        generated_at=generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        active_projects_path=ACTIVE_PROJECTS_RELATIVE_PATH,
        workstream_count=len(audit_rows),
        aggregate_row_count=len(active_rows),
        aggregate_covered_count=sum(row.aggregate_covered for row in audit_rows),
        memory_ready_count=sum(row.memory_ready for row in audit_rows),
        proven_contradiction_count=sum(bool(row.contradictions) for row in audit_rows),
        candidate_drift_count=sum(
            row.canonical_newer_than_aggregate for row in audit_rows
        ),
        status_counts=status_counts,
        rows=audit_rows,
    )


def _audit_workstream(
    *,
    root: Path,
    record: CanonicalWorkstream,
    binding: WorkstreamMemoryBinding,
    rows_by_name: dict[str, list[ActiveProjectRow]],
    aggregate_evidence: GitFileEvidence,
    evidence_loader: EvidenceLoader,
) -> MemoryTruthAuditRow:
    aggregate_rows: list[ActiveProjectRow] = []
    matched_sources: list[str] = []
    evidence_codes: list[str] = []
    contradictions: list[str] = []

    for source_name in record.source_names:
        matches = rows_by_name.get(_normalized_label(source_name), [])
        if not matches:
            evidence_codes.append(f"aggregate_source_missing:{source_name}")
            continue
        matched_sources.append(source_name)
        aggregate_rows.extend(matches)
        for match in matches:
            if match.priority != record.priority:
                contradictions.append(
                    "priority_mismatch:"
                    f"{source_name}:expected={record.priority}:actual={match.priority}"
                )
            if match.mode != record.mode:
                contradictions.append(
                    f"mode_mismatch:{source_name}:expected={record.mode}:actual={match.mode}"
                )

    if not record.source_names:
        evidence_codes.append("aggregate_source_not_declared")
    if aggregate_rows:
        evidence_codes.append("aggregate_source_matched")

    handoff_exists = (root / binding.handoff_relative_path).is_file()
    tvbcp_exists = (root / binding.tvbcp_relative_path).is_file()
    evidence_codes.append(
        "canonical_handoff_exists"
        if handoff_exists
        else "canonical_handoff_missing"
    )
    evidence_codes.append(
        "canonical_tvbcp_exists" if tvbcp_exists else "canonical_tvbcp_missing"
    )

    canonical_evidence = [
        evidence_loader(binding.handoff_relative_path) if handoff_exists else GitFileEvidence(),
        evidence_loader(binding.tvbcp_relative_path) if tvbcp_exists else GitFileEvidence(),
    ]
    canonical_latest = _latest_timestamp(
        evidence.committed_at for evidence in canonical_evidence
    )
    canonical_newer = _is_newer(
        canonical_latest,
        aggregate_evidence.committed_at,
    )
    if canonical_newer:
        evidence_codes.append("canonical_commit_newer_than_aggregate")
    elif canonical_latest and aggregate_evidence.committed_at:
        evidence_codes.append("aggregate_commit_not_older_than_canonical")
    else:
        evidence_codes.append("commit_freshness_unavailable")

    if contradictions:
        status = STATUS_PROVEN_CONTRADICTION
    elif not (handoff_exists and tvbcp_exists):
        status = STATUS_UNMATERIALIZED
    elif not aggregate_rows:
        status = STATUS_UNVERIFIABLE
    elif canonical_newer:
        status = STATUS_CANDIDATE_DRIFT
    else:
        status = STATUS_REGISTRY_CONSISTENT

    return MemoryTruthAuditRow(
        workstream_id=record.workstream_id,
        workstream_type=record.workstream_type,
        name=record.name,
        expected_mode=record.mode,
        expected_priority=record.priority,
        source_names=record.source_names,
        matched_sources=tuple(matched_sources),
        aggregate_rows=tuple(aggregate_rows),
        handoff_path=binding.handoff_relative_path,
        tvbcp_path=binding.tvbcp_relative_path,
        handoff_exists=handoff_exists,
        tvbcp_exists=tvbcp_exists,
        aggregate_committed_at=aggregate_evidence.committed_at,
        canonical_latest_committed_at=canonical_latest,
        canonical_newer_than_aggregate=canonical_newer,
        contradictions=tuple(contradictions),
        evidence_codes=tuple(evidence_codes),
        status=status,
    )


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _latest_timestamp(values: Iterable[str | None]) -> str | None:
    parsed = [
        (timestamp, value)
        for value in values
        if (timestamp := _parse_timestamp(value)) is not None
    ]
    return max(parsed, default=(None, None), key=lambda item: item[0])[1]


def _is_newer(candidate: str | None, reference: str | None) -> bool:
    candidate_time = _parse_timestamp(candidate)
    reference_time = _parse_timestamp(reference)
    return bool(
        candidate_time is not None
        and reference_time is not None
        and candidate_time > reference_time
    )


def format_memory_truth_audit(result: MemoryTruthAuditResult) -> str:
    lines = [
        "P0 - READ-ONLY AUDIT PRAVDIVOSTI PAMETI",
        f"Vygenerovano: {result.generated_at}",
        f"Zdroj agregatu: {result.active_projects_path}",
        "",
        "Bezpecnost:",
        "- Audit cetl pouze katalog, registry metadata a verejny git-safe agregat.",
        "- Necetl obsah handoffu, TVBCP, private dat ani dokumentu.",
        "- Nic nevytvoril, neopravoval ani nematerializoval.",
        "- Datum commitu je pouze signal k rucni kontrole, nikoli dukaz pravdy.",
        "",
        "Souhrn:",
        f"- Workstreamy: {result.workstream_count}",
        f"- Radky agregatu: {result.aggregate_row_count}",
        f"- Workstreamy dohledane v agregatu: {result.aggregate_covered_count}",
        f"- Kompletni kanonicka dvojice handoff + TVBCP: {result.memory_ready_count}",
        f"- Prokazane formalni rozpory: {result.proven_contradiction_count}",
        f"- Kandidati na kontrolu podle casu commitu: {result.candidate_drift_count}",
        "- Stavy: "
        + ", ".join(
            f"{status}={count}" for status, count in result.status_counts.items()
        ),
        "",
        "Mapa 30 workstreamu:",
    ]
    for row in result.rows:
        missing = []
        if not row.handoff_exists:
            missing.append("handoff")
        if not row.tvbcp_exists:
            missing.append("tvbcp")
        memory = "ready" if not missing else "missing:" + "+".join(missing)
        aggregate = (
            f"{len(row.matched_sources)}/{len(row.source_names)} sources"
            if row.source_names
            else "no declared source"
        )
        freshness = (
            "canonical_newer"
            if row.canonical_newer_than_aggregate
            else "not_newer_or_unknown"
        )
        lines.append(
            f"- {row.workstream_id} | {row.status} | "
            f"aggregate={aggregate} | memory={memory} | freshness={freshness}"
        )

    lines.extend(["", "Prokazane formalni rozpory:"])
    contradiction_rows = [row for row in result.rows if row.contradictions]
    if not contradiction_rows:
        lines.append("- Zadny.")
    for row in contradiction_rows:
        for contradiction in row.contradictions:
            lines.append(f"- {row.workstream_id}: {contradiction}")

    lines.extend(
        [
            "",
            "Vyklad:",
            "- proven_contradiction = priorita nebo rezim se prokazatelne lisi.",
            "- unmaterialized = lazy kanonicka dvojice jeste neni kompletni.",
            "- unverifiable = chybi srovnatelny radek agregatu.",
            "- candidate_drift = kanonicky dokument ma novejsi commit; obsah je nutne overit rucne.",
            "- registry_consistent = overena jsou jen formalni pole, nikoli pravdivost celeho textu.",
            "",
        ]
    )
    return "\n".join(lines)


def memory_truth_audit_json(result: MemoryTruthAuditResult) -> str:
    return json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n"
