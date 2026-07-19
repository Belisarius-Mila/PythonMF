"""Project binding, handoff evidence, and confirmed isolated bootstrap."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from app.codex_appserver import AppServerError
from app.file_persistence import (
    FilePersistenceError,
    atomic_replace_text_under_external_lock,
    atomic_write_text,
    exclusive_file_lock,
)


ACTIVE_PROJECTS_RELATIVE_PATH = Path("memory/ACTIVE_PROJECTS.md")
PROJECT_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{2,79}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
LINK_RE = re.compile(r"`([^`]+)`")
PROPOSAL_BLOCKED_PATH_PARTS = (
    "/.git/",
    "/data/private/",
    "/data/session_autosave/",
    "/.env",
)
PROPOSAL_BLOCKED_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
PROJECT_BOOTSTRAP_CONFIRMATION = "POTVRZUJI REGISTRACI PROJEKTU"
PROJECT_BOOTSTRAP_PRIORITIES = {"1", "2", "3"}


class ProjectContinuityError(AppServerError):
    """Raised when a project binding cannot be proven safe."""


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    label: str
    priority: str
    handoff_paths: tuple[str, ...]
    tvbcp_paths: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "id": self.project_id,
            "label": self.label,
            "priority": self.priority,
            "handoffs": [
                {"path": path, "label": Path(path).name}
                for path in self.handoff_paths
            ],
            "tvbcp_paths": list(self.tvbcp_paths),
        }


def _normalized_header(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.casefold()).strip("_")


def _project_id(label: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.casefold()).strip("-")[:52] or "project"
    suffix = hashlib.sha256(label.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{suffix}"


def _project_slug(label: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.casefold()).strip("_")[:56] or "project"


def _bootstrap_line(
    value: object,
    *,
    label: str,
    minimum: int,
    maximum: int,
) -> str:
    raw = str(value or "").strip()
    if any(character in raw for character in ("\n", "\r", "\x00", "|", "`", "<", ">")):
        raise ProjectContinuityError(f"{label} musí být jeden bezpečný textový řádek.")
    clean = " ".join(raw.split())
    if len(clean) < minimum or len(clean) > maximum:
        raise ProjectContinuityError(f"{label} musí mít {minimum} až {maximum} znaků.")
    return clean


def _append_active_project_row(text: str, row: str) -> str:
    lines = str(text or "").splitlines()
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().startswith("|")
            and "oblast" in {_normalized_header(cell) for cell in line.strip().strip("|").split("|")}
            and "handoff" in {_normalized_header(cell) for cell in line.strip().strip("|").split("|")}
        ),
        -1,
    )
    if header_index < 0 or header_index + 1 >= len(lines):
        raise ProjectContinuityError("Registr aktivních projektů nemá očekávanou tabulku.")
    separator = lines[header_index + 1].strip()
    if not separator.startswith("|") or "---" not in separator:
        raise ProjectContinuityError("Registr aktivních projektů nemá bezpečný oddělovač tabulky.")
    insert_at = header_index + 2
    while insert_at < len(lines) and lines[insert_at].strip().startswith("|"):
        insert_at += 1
    lines.insert(insert_at, row)
    return "\n".join(lines) + "\n"


def _safe_memory_path(raw: str, *, expected_dir: str) -> str:
    text = str(raw or "").strip().replace("\\", "/")
    if text.startswith("memory/"):
        candidate = PurePosixPath(text)
    elif text.startswith(f"{expected_dir}/"):
        candidate = PurePosixPath("memory") / text
    else:
        return ""
    if candidate.is_absolute() or ".." in candidate.parts:
        return ""
    if len(candidate.parts) < 3 or candidate.parts[:2] != ("memory", expected_dir):
        return ""
    if candidate.suffix.casefold() not in {".md", ".txt"}:
        return ""
    return candidate.as_posix()


def _paths_from_cell(value: str, *, expected_dir: str) -> tuple[str, ...]:
    paths: list[str] = []
    for match in LINK_RE.findall(str(value or "")):
        safe = _safe_memory_path(match, expected_dir=expected_dir)
        if safe and safe not in paths:
            paths.append(safe)
    return tuple(paths)


def parse_project_catalog(text: str) -> tuple[ProjectRecord, ...]:
    """Parse active project rows without exposing status text or private data."""
    headers: list[str] = []
    projects: list[ProjectRecord] = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or set("".join(cells)) <= {"-", ":", " "}:
            continue
        if not headers:
            headers = [_normalized_header(cell) for cell in cells]
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = dict(zip(headers, cells[: len(headers)], strict=False))
        label = " ".join(str(row.get("oblast") or "").split())
        lifecycle = str(row.get("rezim") or "active").strip().casefold()
        if not label or lifecycle != "active":
            continue
        handoffs = _paths_from_cell(str(row.get("handoff") or ""), expected_dir="handoffs")
        if not handoffs:
            continue
        memory_cell = str(row.get("memory_soubor") or row.get("memory") or "")
        tvbcps = _paths_from_cell(memory_cell, expected_dir="tvbcp")
        projects.append(
            ProjectRecord(
                project_id=_project_id(label),
                label=label[:180],
                priority=" ".join(str(row.get("priorita") or "").split())[:20],
                handoff_paths=handoffs,
                tvbcp_paths=tvbcps,
            )
        )
    return tuple(projects)


def _parse_timestamp(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _git_output(repo: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _file_evidence_time(project_root: Path, relative_path: str) -> datetime | None:
    path = (project_root / relative_path).resolve()
    if project_root.resolve() not in path.parents or not path.is_file():
        return None
    repo_root = Path(_git_output(project_root, ["rev-parse", "--show-toplevel"]) or project_root)
    try:
        repo_relative = path.relative_to(repo_root).as_posix()
    except ValueError:
        return None
    dirty = bool(_git_output(repo_root, ["status", "--porcelain=v1", "--", repo_relative]))
    if not dirty:
        committed = _parse_timestamp(_git_output(repo_root, ["log", "-1", "--format=%cI", "--", repo_relative]))
        if committed is not None:
            return committed
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def _changed_paths(review: dict[str, Any], *, project_dir_name: str) -> set[str]:
    paths: set[str] = set()
    for key in ("changes", "checkpoint_changes"):
        for row in review.get(key) or []:
            if not isinstance(row, dict):
                continue
            raw = str(row.get("path") or "").split(" → ")[-1].replace("\\", "/").strip()
            prefix = f"{project_dir_name}/"
            if raw.startswith(prefix):
                raw = raw[len(prefix) :]
            if raw:
                paths.add(raw)
    return paths


def _proposal_change_rows(review: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in review.get("checkpoint_changes") or []:
        if not isinstance(item, dict):
            raise ProjectContinuityError("Checkpoint obsahuje neověřitelnou změnu.")
        status = str(item.get("status") or "").strip()
        raw_path = str(item.get("path") or "").strip().strip('"').replace("\\", "/")
        path = PurePosixPath(raw_path)
        normalized = f"/{raw_path.casefold()}"
        if (
            status not in {"A", "M"}
            or not raw_path
            or path.is_absolute()
            or ".." in path.parts
            or "\n" in raw_path
            or "\r" in raw_path
            or " → " in raw_path
            or len(raw_path) > 300
            or any(part in normalized for part in PROPOSAL_BLOCKED_PATH_PARTS)
            or path.suffix.casefold() in PROPOSAL_BLOCKED_SUFFIXES
        ):
            raise ProjectContinuityError("Checkpoint obsahuje cestu nevhodnou pro návrh handoffu.")
        rows.append({"status": status, "path": raw_path})
    if not rows:
        raise ProjectContinuityError("Checkpoint nemá ověřené změny pro návrh handoffu.")
    return rows


class ProjectContinuityService:
    """Build safe bindings, compare evidence, and perform confirmed bootstrap writes."""

    def __init__(self, *, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def catalog(self) -> tuple[ProjectRecord, ...]:
        path = self.project_root / ACTIVE_PROJECTS_RELATIVE_PATH
        try:
            return parse_project_catalog(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ProjectContinuityError("Registr aktivních projektů nelze bezpečně načíst.") from exc

    def public_catalog(self) -> list[dict[str, Any]]:
        return [record.public_dict() for record in self.catalog()]

    def default_project_id(self, label: str) -> str:
        wanted = " ".join(str(label or "").split())
        record = next((item for item in self.catalog() if item.label == wanted), None)
        return record.project_id if record else ""

    def project_bootstrap_preview(
        self,
        *,
        project_label: str,
        priority: str,
        goal: str,
        next_step: str,
    ) -> dict[str, Any]:
        """Validate and preview a git-safe project registration without writing files."""
        clean_label = _bootstrap_line(
            project_label,
            label="Název projektu",
            minimum=3,
            maximum=100,
        )
        clean_priority = str(priority or "").strip()
        if clean_priority not in PROJECT_BOOTSTRAP_PRIORITIES:
            raise ProjectContinuityError("Priorita registrovaného projektu musí být 1, 2 nebo 3.")
        clean_goal = _bootstrap_line(goal, label="Cíl projektu", minimum=5, maximum=240)
        clean_next_step = _bootstrap_line(
            next_step,
            label="První další krok",
            minimum=5,
            maximum=180,
        )
        if any(item.label.casefold() == clean_label.casefold() for item in self.catalog()):
            raise ProjectContinuityError("Projekt s tímto názvem už v aktivním registru existuje.")
        date_text = datetime.now().astimezone().date().isoformat()
        slug = _project_slug(clean_label)
        handoff_path = f"memory/handoffs/{slug}_start_{date_text.replace('-', '_')}.md"
        if (self.project_root / handoff_path).exists():
            raise ProjectContinuityError("Cílový handoff už existuje; zvol jiný název projektu.")
        return {
            "ok": True,
            "ready": True,
            "read_only": True,
            "writes_performed": False,
            "project_id": _project_id(clean_label),
            "project_label": clean_label,
            "priority": clean_priority,
            "goal": clean_goal,
            "next_step": clean_next_step,
            "handoff_path": handoff_path,
            "date": date_text,
            "confirmation_text": PROJECT_BOOTSTRAP_CONFIRMATION,
            "changes": [ACTIVE_PROJECTS_RELATIVE_PATH.as_posix(), handoff_path],
            "message": "Náhled je připravený; zatím nebyl změněn žádný soubor ani semafor.",
        }

    def create_project_bootstrap(
        self,
        *,
        project_label: str,
        priority: str,
        goal: str,
        next_step: str,
        confirmation: str,
    ) -> dict[str, Any]:
        """Register one project row and one starting handoff in an isolated workspace."""
        if str(confirmation or "").strip() != PROJECT_BOOTSTRAP_CONFIRMATION:
            raise ProjectContinuityError(
                f"Chybí přesná potvrzovací věta: {PROJECT_BOOTSTRAP_CONFIRMATION}"
            )
        registry_path = self.project_root / ACTIVE_PROJECTS_RELATIVE_PATH
        handoff_created = False
        registry_written = False
        original_registry = ""
        handoff_path: Path | None = None
        try:
            with exclusive_file_lock(registry_path):
                original_registry = registry_path.read_text(encoding="utf-8")
                preview = self.project_bootstrap_preview(
                    project_label=project_label,
                    priority=priority,
                    goal=goal,
                    next_step=next_step,
                )
                handoff_relative = str(preview["handoff_path"])
                handoff_path = self.project_root / handoff_relative
                if handoff_path.exists():
                    raise ProjectContinuityError(
                        "Cílový handoff mezitím vznikl; nic jsem nepřepsal."
                    )
                handoff_text = "\n".join(
                    (
                        f"Nazev: {preview['project_label']}",
                        f"Priorita: {preview['priority']}",
                        "Stav: rozpracovane",
                        "Pripomenout pri startu: ne",
                        f"Datum: {preview['date']}",
                        "",
                        "Co se resilo:",
                        f"- {preview['goal']}",
                        "",
                        "Co je hotove:",
                        "- Projekt a tento vychozi handoff byly zaregistrovany potvrzenou fazi 0 v Cockpitu.",
                        "- Vyvojovy semafor se po uspesne registraci pripne k tomuto projektu.",
                        "",
                        "Co neni hotove:",
                        "- Dalsi planovana vyvojova etapa zatim nezacala.",
                        "- Samotnou registraci nevznikl novy checkpoint, commit, push ani nasazeni.",
                        "",
                        "Dalsi krok:",
                        f"- {preview['next_step']}",
                        "",
                        "Navrhovane dalsi kroky:",
                        "- Po prvnim vyvoji zkontrolovat navrh handoffu pri checkpointu.",
                        "- Pred prevzetim do main spustit audit nasazeni.",
                        "",
                        "Zmenene nebo relevantni soubory:",
                        "- memory/ACTIVE_PROJECTS.md",
                        f"- {handoff_relative}",
                        "",
                        "Bezpecnost / neukladat:",
                        "- Neukladat hesla, tokeny, API klice, private texty ani osobni udaje.",
                        "",
                    )
                )
                row = (
                    f"| {preview['project_label']} | {preview['priority']} | active | "
                    "Zaregistrováno potvrzenou fází 0 v Cockpitu; další vývojová etapa ještě nezačala. | "
                    f"zatím není | `{handoff_relative}` | {preview['next_step']} |"
                )
                updated_registry = _append_active_project_row(original_registry, row)
                atomic_replace_text_under_external_lock(handoff_path, handoff_text)
                handoff_created = True
                atomic_replace_text_under_external_lock(registry_path, updated_registry)
                registry_written = True
                binding = self.resolve_binding(
                    project_id=str(preview["project_id"]),
                    handoff_path=handoff_relative,
                )
                return {
                    **preview,
                    "read_only": False,
                    "writes_performed": True,
                    "created": True,
                    "binding": binding,
                    "message": (
                        "Projekt a výchozí handoff byly zaregistrovány v izolovaném workspace; "
                        "nic nebylo commitnuto ani pushnuto."
                    ),
                }
        except (FilePersistenceError, OSError) as exc:
            if registry_written:
                try:
                    atomic_write_text(registry_path, original_registry)
                except (FilePersistenceError, OSError):
                    pass
            if handoff_created and handoff_path is not None:
                try:
                    handoff_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise ProjectContinuityError(
                "Projekt se nepodařilo bezpečně zaregistrovat; nic existujícího jsem nepřepsal."
            ) from exc
        except ProjectContinuityError:
            if registry_written:
                try:
                    atomic_write_text(registry_path, original_registry)
                except (FilePersistenceError, OSError):
                    pass
            if handoff_created and handoff_path is not None:
                try:
                    handoff_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    def resolve_binding(
        self,
        *,
        project_id: str,
        handoff_path: str,
        fallback_tvbcp_path: str = "",
    ) -> dict[str, str]:
        clean_project_id = str(project_id or "").strip()
        clean_handoff = _safe_memory_path(handoff_path, expected_dir="handoffs")
        if not PROJECT_ID_RE.fullmatch(clean_project_id):
            raise ProjectContinuityError("Vyber projekt pro tento vývoj.")
        record = next((item for item in self.catalog() if item.project_id == clean_project_id), None)
        if record is None:
            raise ProjectContinuityError("Vybraný projekt už není v aktivním registru.")
        if not clean_handoff or clean_handoff not in record.handoff_paths:
            raise ProjectContinuityError("Vyber registrovaný aktuální handoff projektu.")
        if not (self.project_root / clean_handoff).is_file():
            raise ProjectContinuityError("Vybraný handoff nebyl nalezen.")
        tvbcp_path = next(
            (path for path in record.tvbcp_paths if (self.project_root / path).is_file()),
            "",
        )
        fallback = _safe_memory_path(fallback_tvbcp_path, expected_dir="tvbcp")
        if not tvbcp_path and fallback and (self.project_root / fallback).is_file():
            tvbcp_path = fallback
        return {
            "project_id": record.project_id,
            "project_label": record.label,
            "handoff_path": clean_handoff,
            "tvbcp_path": tvbcp_path,
        }

    def audit(
        self,
        *,
        binding: dict[str, Any],
        workspace_root: Path,
        workspace_review: dict[str, Any],
        context_anchor: dict[str, Any],
        deployment_receipt_path: Path | None = None,
    ) -> dict[str, Any]:
        """Return a conservative read-only status; never mutate project memory."""
        base = {
            "ok": True,
            "read_only": True,
            "blocking": False,
            "state": "unverifiable",
            "label": "Nelze ověřit",
            "message": "Nejdřív vyber projekt a handoff při převzetí semaforu.",
            "reasons": [],
            "evidence": [],
        }
        try:
            resolved = self.resolve_binding(
                project_id=str(binding.get("project_id") or ""),
                handoff_path=str(binding.get("handoff_path") or ""),
                fallback_tvbcp_path=str(binding.get("tvbcp_path") or ""),
            )
        except ProjectContinuityError as exc:
            return {**base, "message": str(exc)}

        root = Path(workspace_root).resolve()
        handoff_path = resolved["handoff_path"]
        handoff_time = _file_evidence_time(root, handoff_path)
        if handoff_time is None:
            return {
                **base,
                "binding": resolved,
                "message": "Vybraný handoff nelze v pracovním prostoru ověřit.",
            }

        reasons: list[str] = []
        evidence: list[dict[str, Any]] = [
            {"source": "handoff", "available": True, "updated_at": handoff_time.isoformat(timespec="seconds")}
        ]
        changed = _changed_paths(workspace_review, project_dir_name=root.name)
        if changed:
            handoff_changed = handoff_path in changed
            evidence.append({"source": "workspace", "available": True, "change_count": len(changed)})
            if not handoff_changed:
                reasons.append("Workspace obsahuje vývojové změny, ale vybraný handoff mezi nimi není.")

        newer_sources: list[str] = []
        anchor_time = _parse_timestamp(context_anchor.get("updated_at"))
        evidence.append(
            {
                "source": "anchor",
                "available": anchor_time is not None,
                "revision": int(context_anchor.get("revision") or 0),
                "updated_at": anchor_time.isoformat(timespec="seconds") if anchor_time else "",
            }
        )
        if anchor_time and anchor_time > handoff_time:
            newer_sources.append("kotva")

        tvbcp_path = resolved.get("tvbcp_path", "")
        tvbcp_time = _file_evidence_time(root, tvbcp_path) if tvbcp_path else None
        evidence.append(
            {
                "source": "tvbcp",
                "available": tvbcp_time is not None,
                "updated_at": tvbcp_time.isoformat(timespec="seconds") if tvbcp_time else "",
            }
        )
        if tvbcp_time and tvbcp_time > handoff_time:
            newer_sources.append("TVBCP")

        receipt_time: datetime | None = None
        if deployment_receipt_path is not None and Path(deployment_receipt_path).is_file():
            try:
                receipt = json.loads(Path(deployment_receipt_path).read_text(encoding="utf-8"))
                if isinstance(receipt, dict) and receipt.get("state") == "deployed":
                    receipt_time = _parse_timestamp(receipt.get("deployed_at"))
            except (OSError, json.JSONDecodeError):
                receipt_time = None
        evidence.append(
            {
                "source": "deployment",
                "available": receipt_time is not None,
                "updated_at": receipt_time.isoformat(timespec="seconds") if receipt_time else "",
            }
        )
        if receipt_time and receipt_time > handoff_time:
            newer_sources.append("poslední nasazení")

        if newer_sources:
            reasons.append(f"Novější než handoff: {', '.join(newer_sources)}.")
        if reasons:
            return {
                **base,
                "binding": resolved,
                "state": "needs_update",
                "label": "Čeká na aktualizaci",
                "message": "Handoff pravděpodobně zaostává; nic nebylo změněno.",
                "reasons": reasons,
                "evidence": evidence,
            }
        return {
            **base,
            "binding": resolved,
            "state": "current",
            "label": "Aktuální",
            "message": "Dostupné důkazy neukazují, že by handoff zaostával.",
            "evidence": evidence,
        }

    def handoff_proposal(
        self,
        *,
        binding: dict[str, Any],
        topic: str,
        workspace_review: dict[str, Any],
        context_anchor: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a metadata-only draft without writing project memory or Git."""
        base = {
            "ok": True,
            "available": False,
            "read_only": True,
            "blocking": False,
            "writes_performed": False,
            "state": "waiting_checkpoint",
            "label": "Čeká na checkpoint",
            "message": "Návrh vznikne až po úspěšném lokálním WIP checkpointu.",
            "draft": "",
            "changed_files": [],
        }
        try:
            resolved = self.resolve_binding(
                project_id=str(binding.get("project_id") or ""),
                handoff_path=str(binding.get("handoff_path") or ""),
                fallback_tvbcp_path=str(binding.get("tvbcp_path") or ""),
            )
        except ProjectContinuityError as exc:
            return {
                **base,
                "state": "unverifiable",
                "label": "Nelze připravit",
                "message": str(exc),
            }
        if not workspace_review.get("local_checkpoint_ahead"):
            return {**base, "binding": resolved}
        if int(workspace_review.get("local_commit_count") or 0) != 1:
            return {
                **base,
                "binding": resolved,
                "state": "unverifiable",
                "label": "Nelze připravit",
                "message": "Návrh handoffu podporuje přesně jeden lokální WIP checkpoint.",
            }
        checkpoint_head = str(workspace_review.get("checkpoint_head") or "").strip().casefold()
        checkpoint_subject = " ".join(
            str(workspace_review.get("checkpoint_subject") or "").split()
        )[:120]
        clean_topic = " ".join(str(topic or "").split())[:120]
        if not COMMIT_RE.fullmatch(checkpoint_head) or not checkpoint_subject or not clean_topic:
            return {
                **base,
                "binding": resolved,
                "state": "unverifiable",
                "label": "Nelze připravit",
                "message": "Checkpoint nebo téma vývoje nemá úplná ověřená metadata.",
            }
        try:
            changes = _proposal_change_rows(workspace_review)
        except ProjectContinuityError as exc:
            return {
                **base,
                "binding": resolved,
                "state": "unverifiable",
                "label": "Nelze připravit",
                "message": str(exc),
            }
        project = next(
            (item for item in self.catalog() if item.project_id == resolved["project_id"]),
            None,
        )
        if project is None:
            return {
                **base,
                "binding": resolved,
                "state": "unverifiable",
                "label": "Nelze připravit",
                "message": "Projekt už nelze dohledat v aktivním registru.",
            }
        anchor_revision = int(context_anchor.get("revision") or 0)
        anchor_state = "připnutá" if context_anchor.get("active") is True else "nepřipnutá"
        file_lines = [f"- {row['status']} · {row['path']}" for row in changes[:40]]
        if len(changes) > 40:
            file_lines.append(f"- … a dalších {len(changes) - 40} souborů")
        tvbcp_line = resolved.get("tvbcp_path") or "projekt nemá přiřazený TVBCP"
        today = datetime.now().astimezone().date().isoformat()
        draft = "\n".join(
            (
                "NÁVRH AKTUALIZACE HANDOFFU — ZATÍM NEULOŽENO",
                "",
                f"Název: {clean_topic}",
                f"Priorita: {project.priority or 'doplnit'}",
                "Stav: rozpracované",
                "Připomenout při startu: ne",
                f"Datum: {today}",
                "",
                "Co se řešilo:",
                f"- {clean_topic}",
                "",
                "Co je hotové:",
                f"- Vytvořen lokální WIP checkpoint {checkpoint_head[:12]}: {checkpoint_subject}.",
                f"- Checkpoint obsahuje {len(changes)} bezpečně auditovaných změn.",
                f"- Kontextová kotva: revize {anchor_revision}, {anchor_state}; její obsah nebyl čten.",
                f"- Projektový TVBCP: {tvbcp_line}; jeho obsah nebyl čten.",
                "",
                "Co není hotové:",
                "- Tento návrh zatím není uložený do handoffu.",
                "- Převzetí do main, nasazení a restart zatím nejsou tímto návrhem potvrzené.",
                "",
                "Další krok:",
                "- Zkontrolovat návrh a teprve samostatně potvrdit jeho uložení.",
                "",
                "Navrhované další kroky:",
                "- Po potvrzeném handoffu provést audit checkpointu, push a bezpečné převzetí do main.",
                "- Po nasazení doplnit skutečný výsledek testů, restartu a smoke testu.",
                "",
                "Změněné nebo relevantní soubory:",
                *file_lines,
                "",
                "Bezpečnost / neukládat:",
                "- Návrh vznikl pouze z Git metadat a projektové vazby; neobsahuje obsah souborů.",
                "- Nevkládat hesla, tokeny, API klíče, private texty ani obsah e-mailů.",
            )
        )
        return {
            **base,
            "available": True,
            "state": "ready",
            "label": "Návrh připraven",
            "message": "Návrh je pouze zobrazený; nic nebylo uloženo ani změněno.",
            "binding": resolved,
            "target_handoff": resolved["handoff_path"],
            "checkpoint_head": checkpoint_head,
            "checkpoint_subject": checkpoint_subject,
            "change_count": len(changes),
            "changed_files": changes,
            "draft": draft,
        }

    def takeover_handoff_check(
        self,
        *,
        binding: dict[str, Any],
        checkpoint_changes: list[dict[str, Any]],
        project_dir_name: str,
    ) -> dict[str, Any]:
        """Check project/handoff checkpoint evidence without blocking or writing."""
        base = {
            "ok": True,
            "read_only": True,
            "blocking": False,
            "writes_performed": False,
            "state": "unverifiable",
            "label": "Nelze ověřit",
            "message": "Handoff checkpointu nelze bezpečně ověřit.",
            "handoff_in_checkpoint": False,
        }
        try:
            resolved = self.resolve_binding(
                project_id=str(binding.get("project_id") or ""),
                handoff_path=str(binding.get("handoff_path") or ""),
                fallback_tvbcp_path=str(binding.get("tvbcp_path") or ""),
            )
        except ProjectContinuityError as exc:
            return {**base, "message": str(exc)}

        changed = _changed_paths(
            {"checkpoint_changes": checkpoint_changes},
            project_dir_name=str(project_dir_name or "").strip(),
        )
        if not changed:
            return {
                **base,
                "binding": resolved,
                "target_handoff": resolved["handoff_path"],
                "message": "Audit checkpointu neposkytl ověřitelné cesty změn.",
            }
        if resolved["handoff_path"] not in changed:
            return {
                **base,
                "binding": resolved,
                "target_handoff": resolved["handoff_path"],
                "state": "warning",
                "label": "Handoff chybí v checkpointu",
                "message": (
                    "Vybraný handoff patří projektu, ale tento checkpoint jej neobsahuje. "
                    "V této fázi jde pouze o varování."
                ),
            }
        return {
            **base,
            "binding": resolved,
            "target_handoff": resolved["handoff_path"],
            "state": "verified",
            "label": "Handoff odpovídá",
            "message": "Vybraný handoff patří projektu a je obsažen v checkpointu.",
            "handoff_in_checkpoint": True,
        }

    def deployment_completion_entry(
        self,
        *,
        binding: dict[str, Any],
        checkpoint_head: str,
        test_count: int,
        deployed_at: str,
        next_step: str,
    ) -> dict[str, Any]:
        """Build one deterministic git-safe completion entry from verified facts."""
        resolved = self.resolve_binding(
            project_id=str(binding.get("project_id") or ""),
            handoff_path=str(binding.get("handoff_path") or ""),
            fallback_tvbcp_path=str(binding.get("tvbcp_path") or ""),
        )
        clean_head = str(checkpoint_head or "").strip().casefold()
        if not COMMIT_RE.fullmatch(clean_head):
            raise ProjectContinuityError("Dokončení nasazení nemá platný commit.")
        clean_test_count = int(test_count)
        if clean_test_count <= 0 or clean_test_count > 100_000:
            raise ProjectContinuityError("Dokončení nasazení nemá ověřený počet testů.")
        raw_next_step = str(next_step or "").strip()
        if any(character in raw_next_step for character in ("\n", "\r", "\x00")):
            raise ProjectContinuityError("Další krok musí být jeden krátký řádek.")
        clean_next_step = " ".join(raw_next_step.split())
        if len(clean_next_step) < 3 or len(clean_next_step) > 180:
            raise ProjectContinuityError("Další krok musí mít 3 až 180 znaků.")
        completed_time = _parse_timestamp(deployed_at)
        if completed_time is None:
            raise ProjectContinuityError("Dokončení nasazení nemá platný čas.")
        local_time = completed_time.astimezone().isoformat(timespec="seconds")
        marker = f"deployment-completion:{clean_head}"
        entry = "\n".join(
            (
                "",
                f"<!-- {marker} -->",
                f"## Potvrzené dokončení po nasazení — {local_time}",
                "",
                "- Stav: nasazeno",
                f"- Commit v `main`: `{clean_head}`",
                f"- Testy: plná Cockpit brána, {clean_test_count} testů, OK",
                "- Restart Cockpitu: potvrzen novým procesem",
                "- Smoke test: 5/5 kontrol, OK",
                f"- Další krok: {clean_next_step}",
                "",
            )
        )
        return {
            "binding": resolved,
            "target_handoff": resolved["handoff_path"],
            "checkpoint_head": clean_head,
            "test_count": clean_test_count,
            "completed_at": local_time,
            "next_step": clean_next_step,
            "marker": marker,
            "entry": entry,
        }
