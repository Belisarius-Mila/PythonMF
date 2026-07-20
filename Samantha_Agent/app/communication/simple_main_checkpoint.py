"""One confirmed Human–Adam checkpoint completed directly on ``main``.

The module is intentionally not wired to Cockpit routes yet.  Phase 1.1 keeps
the existing UI untouched and provides a tested backend boundary that can later
replace the semaphore/WIP/takeover sequence.
"""

from __future__ import annotations

import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence
from zoneinfo import ZoneInfo

from app.codex_appserver import AppServerError
from app.communication.human_adam_deploy import (
    DEFAULT_GATE_LOG,
    GateEvidence,
    HumanAdamGateError,
    run_checkpoint_quality_gate,
)
from app.communication.human_adam_workspace import HumanAdamWorkspaceManager
from app.file_persistence import atomic_replace_text_under_external_lock
from scripts.human_adam_takeover import (
    CONFIRMATION_TEXT as LEGACY_FAST_FORWARD_CONFIRMATION,
    TakeoverError,
    apply_takeover,
    refresh_origin_main,
)


MAX_MEMORY_FILE_CHARS = 2_000_000
MAX_CHANGED_PATHS_IN_HANDOFF = 40
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
_SENSITIVE_TEXT_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token|token|password|heslo|app-specific password)\b\s*[:=]\s*\S+"
)
_CHECKPOINT_LOCK = threading.Lock()
PROJECT_TIME_ZONE = ZoneInfo("Europe/Prague")


class SimpleMainCheckpointError(AppServerError):
    """Raised when the single-step checkpoint cannot safely reach ``main``."""


@dataclass(frozen=True)
class SimpleMainCheckpointRequest:
    workstream_id: str
    commit_message: str
    summary: str
    next_step: str
    handoff_relative_path: str
    tvbcp_relative_path: str


def _local_now() -> datetime:
    return datetime.now(PROJECT_TIME_ZONE)


def _safe_line(value: object, *, label: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise SimpleMainCheckpointError(f"Chybí {label} checkpointu.")
    if len(text) > limit:
        raise SimpleMainCheckpointError(f"{label.capitalize()} checkpointu je příliš dlouhý.")
    if _SENSITIVE_TEXT_RE.search(text):
        raise SimpleMainCheckpointError(
            "Checkpointový zápis nesmí obsahovat heslo, token ani API klíč."
        )
    return text


def _safe_request(request: SimpleMainCheckpointRequest) -> SimpleMainCheckpointRequest:
    workstream_id = str(request.workstream_id or "").strip().casefold()
    if not _WORKSTREAM_ID_RE.fullmatch(workstream_id):
        raise SimpleMainCheckpointError("Checkpoint nemá platný identifikátor pracovního proudu.")
    return SimpleMainCheckpointRequest(
        workstream_id=workstream_id,
        commit_message=_safe_line(request.commit_message, label="název", limit=120),
        summary=_safe_line(request.summary, label="souhrn", limit=400),
        next_step=_safe_line(request.next_step, label="další krok", limit=500),
        handoff_relative_path=str(request.handoff_relative_path or "").strip(),
        tvbcp_relative_path=str(request.tvbcp_relative_path or "").strip(),
    )


def _memory_path(project_root: Path, relative_text: str, *, kind: str) -> Path:
    relative = Path(relative_text)
    expected_parent = "handoffs" if kind == "handoff" else "tvbcp"
    allowed_suffixes = {".md"} if kind == "handoff" else {".md", ".txt"}
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or len(relative.parts) < 3
        or relative.parts[:2] != ("memory", expected_parent)
        or relative.suffix.casefold() not in allowed_suffixes
    ):
        raise SimpleMainCheckpointError(
            f"{kind.upper()} checkpointu nemá povolenou relativní cestu."
        )
    root = project_root.resolve()
    unresolved = root / relative
    path = unresolved.resolve()
    if root not in path.parents or not path.is_file() or unresolved.is_symlink():
        raise SimpleMainCheckpointError(f"Kanonický {kind} checkpointu nebyl nalezen.")
    return path


def _read_memory_file(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SimpleMainCheckpointError("Checkpointovou paměť nelze bezpečně přečíst.") from exc
    if len(content) > MAX_MEMORY_FILE_CHARS:
        raise SimpleMainCheckpointError("Checkpointová paměť překročila bezpečný limit.")
    return content


def _append_block(content: str, block: str) -> str:
    return content.rstrip() + "\n\n" + block.strip() + "\n"


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SimpleMainCheckpointError("Checkpoint nemá platnou časovou zónu.")
    local = value.astimezone(PROJECT_TIME_ZONE)
    return local.strftime("%Y-%m-%d %H:%M %Z")


def _memory_blocks(
    *,
    request: SimpleMainCheckpointRequest,
    evidence: GateEvidence,
    timestamp: str,
    changes: Sequence[dict[str, str]],
) -> tuple[str, str]:
    paths = [str(item.get("path") or "").strip() for item in changes]
    paths = [item for item in paths if item][:MAX_CHANGED_PATHS_IN_HANDOFF]
    path_text = ", ".join(f"`{item}`" for item in paths) or "bez pojmenované cesty"
    if len(changes) > len(paths):
        path_text += f", … a dalších {len(changes) - len(paths)}"
    test_text = (
        f"plná Cockpit brána: {evidence.test_count} testů, "
        f"{evidence.duration_seconds:.1f} s, výsledek OK"
    )
    handoff_block = f"""### Automatický checkpoint {timestamp}

- Pracovní proud: `{request.workstream_id}`
- Souhrn: {request.summary}
- Ověření: {test_text}
- Změněné cesty před paměťovým zápisem ({len(changes)}): {path_text}
- Commit: `{request.commit_message}`
- Další krok: {request.next_step}
"""
    tvbcp_block = f"""### {timestamp} – {request.summary}

Pracovní proud: `{request.workstream_id}`.

Milník: {request.summary}

Důkaz: {test_text}. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: {request.next_step}
"""
    return handoff_block, tvbcp_block


def _write_memory_pair(
    *,
    handoff_path: Path,
    tvbcp_path: Path,
    handoff_content: str,
    tvbcp_content: str,
    original_handoff: str,
) -> None:
    atomic_replace_text_under_external_lock(handoff_path, handoff_content)
    try:
        atomic_replace_text_under_external_lock(tvbcp_path, tvbcp_content)
    except OSError as exc:
        atomic_replace_text_under_external_lock(handoff_path, original_handoff)
        raise SimpleMainCheckpointError("TVBCP checkpointu se nepodařilo zapsat.") from exc


def _restore_memory_pair(
    *,
    handoff_path: Path,
    tvbcp_path: Path,
    original_handoff: str,
    original_tvbcp: str,
    written_handoff: str,
    written_tvbcp: str,
) -> None:
    try:
        if handoff_path.read_text(encoding="utf-8") == written_handoff:
            atomic_replace_text_under_external_lock(handoff_path, original_handoff)
        if tvbcp_path.read_text(encoding="utf-8") == written_tvbcp:
            atomic_replace_text_under_external_lock(tvbcp_path, original_tvbcp)
    except OSError:
        # Never overwrite an unexpected concurrent edit while handling another
        # failure.  The remaining dirty files are visible to the user.
        return


def _validate_change_rows(
    workspace: HumanAdamWorkspaceManager,
    changes: Sequence[dict[str, str]],
) -> None:
    if not changes:
        raise SimpleMainCheckpointError("Workspace neobsahuje změnu k checkpointu.")
    for item in changes:
        status = str(item.get("status") or "")
        path = str(item.get("path") or "")
        symbols = set(status.replace(" ", ""))
        if status != "??" and (not symbols or not symbols.issubset({"A", "M"})):
            raise SimpleMainCheckpointError(
                "Jednoduchý checkpoint nepodporuje mazání, přejmenování ani netypickou změnu."
            )
        if not workspace.checkpoint_path_allowed(path):
            raise SimpleMainCheckpointError(
                "Checkpoint obsahuje blokovanou private, env nebo mediální cestu."
            )


def _preflight_workspace(
    workspace: HumanAdamWorkspaceManager,
    *,
    require_changes: bool,
    allow_source_ahead: bool = False,
) -> dict[str, Any]:
    status = workspace.status()
    if not status.get("prepared") or not status.get("ok") or not status.get("project_ready"):
        raise SimpleMainCheckpointError("Profilový workspace není připravený.")
    if status.get("remotes"):
        raise SimpleMainCheckpointError("Profilový workspace má neočekávaný Git remote.")
    if status.get("branch") != "main" or status.get("source_branch") != "main":
        raise SimpleMainCheckpointError("Jednoduchý checkpoint vyžaduje větev main.")
    allowed_relations = {"aligned", "source_ahead"} if allow_source_ahead else {"aligned"}
    if status.get("workspace_relation") not in allowed_relations:
        raise SimpleMainCheckpointError(
            "Profilový workspace není zarovnaný se zdrojovým main; nejdřív použij Připojit."
        )
    if int(status.get("source_pending_changes") or 0) != 0:
        raise SimpleMainCheckpointError("Zdrojový main není čistý; checkpoint je zablokovaný.")
    changes = list(status.get("changes") or [])
    if require_changes:
        _validate_change_rows(workspace, changes)
    elif changes:
        raise SimpleMainCheckpointError("Jiný profil obsahuje nedokončenou práci.")
    return status


def complete_simple_main_checkpoint(
    *,
    workspace: HumanAdamWorkspaceManager,
    request: SimpleMainCheckpointRequest,
    confirmed: bool,
    peer_workspaces: Sequence[HumanAdamWorkspaceManager] = (),
    gate_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    gate_log_path: Path = DEFAULT_GATE_LOG,
    now_factory: Callable[[], datetime] = _local_now,
    progress_callback: Callable[[str, str], None] | None = None,
    takeover: Callable[..., dict[str, Any]] = apply_takeover,
) -> dict[str, Any]:
    """Test, record, commit, push and align one workstream step.

    No persistent semaphore or WIP branch is created.  If the remote update
    loses a race, the single local checkpoint commit remains preserved in the
    profile workspace for explicit recovery.
    """

    if not confirmed:
        raise SimpleMainCheckpointError("Jednoduchý checkpoint vyžaduje výslovné potvrzení.")
    safe_request = _safe_request(request)
    if not _CHECKPOINT_LOCK.acquire(blocking=False):
        raise SimpleMainCheckpointError("Jiný jednoduchý checkpoint právě probíhá.")

    def progress(stage: str, outcome: str) -> None:
        if progress_callback is not None:
            progress_callback(stage, outcome)

    try:
        progress("preflight", "running")
        initial = _preflight_workspace(workspace, require_changes=True)
        for peer_index, peer in enumerate(peer_workspaces, start=1):
            if peer.workspace_root == workspace.workspace_root:
                continue
            _preflight_workspace(peer, require_changes=False, allow_source_ahead=True)
        live_origin_head = refresh_origin_main(workspace.source_repo)
        refreshed = _preflight_workspace(workspace, require_changes=True)
        if str(refreshed.get("source_head") or "") != live_origin_head:
            raise SimpleMainCheckpointError(
                "Lokální main a origin/main se neshodují; nejdřív obnov zdrojový main."
            )
        progress("preflight", "passed")

        handoff_path = _memory_path(
            workspace.project_root,
            safe_request.handoff_relative_path,
            kind="handoff",
        )
        tvbcp_path = _memory_path(
            workspace.project_root,
            safe_request.tvbcp_relative_path,
            kind="tvbcp",
        )
        if handoff_path == tvbcp_path:
            raise SimpleMainCheckpointError("Handoff a TVBCP musí být dva různé soubory.")

        progress("gate", "running")
        try:
            evidence = run_checkpoint_quality_gate(
                workspace=workspace,
                runner=gate_runner,
                log_path=gate_log_path,
            )
        except HumanAdamGateError as exc:
            progress("gate", "failed")
            raise SimpleMainCheckpointError(str(exc)) from exc
        progress("gate", "passed")

        original_handoff = _read_memory_file(handoff_path)
        original_tvbcp = _read_memory_file(tvbcp_path)
        timestamp = _format_timestamp(now_factory())
        handoff_block, tvbcp_block = _memory_blocks(
            request=safe_request,
            evidence=evidence,
            timestamp=timestamp,
            changes=list(initial.get("changes") or []),
        )
        written_handoff = _append_block(original_handoff, handoff_block)
        written_tvbcp = _append_block(original_tvbcp, tvbcp_block)
        progress("memory", "running")
        _write_memory_pair(
            handoff_path=handoff_path,
            tvbcp_path=tvbcp_path,
            handoff_content=written_handoff,
            tvbcp_content=written_tvbcp,
            original_handoff=original_handoff,
        )
        progress("memory", "passed")

        progress("commit", "running")
        try:
            checkpoint = workspace.checkpoint(
                confirmed=True,
                message=safe_request.commit_message,
            )
        except (AppServerError, OSError, ValueError) as exc:
            _restore_memory_pair(
                handoff_path=handoff_path,
                tvbcp_path=tvbcp_path,
                original_handoff=original_handoff,
                original_tvbcp=original_tvbcp,
                written_handoff=written_handoff,
                written_tvbcp=written_tvbcp,
            )
            progress("commit", "failed")
            raise SimpleMainCheckpointError("Checkpoint commit se nepodařilo vytvořit.") from exc
        if checkpoint.get("checkpoint_created") is not True:
            _restore_memory_pair(
                handoff_path=handoff_path,
                tvbcp_path=tvbcp_path,
                original_handoff=original_handoff,
                original_tvbcp=original_tvbcp,
                written_handoff=written_handoff,
                written_tvbcp=written_tvbcp,
            )
            progress("commit", "failed")
            raise SimpleMainCheckpointError("Checkpoint commit nevznikl.")
        progress("commit", "passed")

        try:
            applied = takeover(
                confirmation=LEGACY_FAST_FORWARD_CONFIRMATION,
                push=True,
                workspace=workspace,
                progress_callback=progress,
            )
        except (TakeoverError, AppServerError, OSError, ValueError) as exc:
            raise SimpleMainCheckpointError(
                "Push nebo fast-forward selhal; jeden lokální checkpoint commit zůstal zachovaný."
            ) from exc

        final = workspace.status()
        checkpoint_head = str(checkpoint.get("checkpoint_head") or "")
        if (
            applied.get("applied") is not True
            or applied.get("pushed") is not True
            or applied.get("workspace_aligned") is not True
            or final.get("workspace_relation") != "aligned"
            or final.get("dirty")
            or final.get("remotes")
            or str(final.get("head") or "") != checkpoint_head
            or str(final.get("source_head") or "") != checkpoint_head
        ):
            raise SimpleMainCheckpointError(
                "Checkpoint nedoložil čisté zarovnání zdrojového a profilového main."
            )

        progress("peer_alignment", "running")
        peer_rows: list[dict[str, Any]] = []
        for peer in peer_workspaces:
            if peer.workspace_root == workspace.workspace_root:
                continue
            try:
                peer_status = peer.status()
                if peer_status.get("source_update_available"):
                    peer_status = peer.sync_from_main(confirmed=True)
                aligned = bool(
                    peer_status.get("workspace_relation") == "aligned"
                    and not peer_status.get("dirty")
                    and not peer_status.get("local_checkpoint_ahead")
                    and not peer_status.get("remotes")
                    and str(peer_status.get("head") or "") == checkpoint_head
                    and str(peer_status.get("source_head") or "") == checkpoint_head
                )
                peer_rows.append(
                    {
                        "workspace": f"peer-{peer_index}",
                        "aligned": aligned,
                        "message": "" if aligned else "Čistý profil se nepodařilo doložit jako zarovnaný.",
                    }
                )
            except (AppServerError, OSError, ValueError) as exc:
                peer_rows.append(
                    {
                        "workspace": f"peer-{peer_index}",
                        "aligned": False,
                        "message": str(exc),
                    }
                )
        all_workspaces_aligned = all(row["aligned"] for row in peer_rows)
        progress("peer_alignment", "passed" if all_workspaces_aligned else "partial")
        return {
            "ok": True,
            "operation": "simple_main_checkpoint",
            "checkpoint_head": checkpoint_head,
            "checkpoint_short": checkpoint_head[:12],
            "commit_message": safe_request.commit_message,
            "workstream_id": safe_request.workstream_id,
            "gate": {
                "passed": True,
                "test_count": evidence.test_count,
                "duration_seconds": evidence.duration_seconds,
            },
            "handoff_path": safe_request.handoff_relative_path,
            "tvbcp_path": safe_request.tvbcp_relative_path,
            "pushed": True,
            "source_aligned": True,
            "workspace_aligned": True,
            "peer_workspaces": peer_rows,
            "all_workspaces_aligned": all_workspaces_aligned,
            "branches_created": False,
        }
    finally:
        _CHECKPOINT_LOCK.release()
