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
from app.communication.checkpoint_quality_gate import (
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
CURRENT_STATUS_START = "<!-- SAMANTHA_CURRENT_STATUS_START -->"
CURRENT_STATUS_END = "<!-- SAMANTHA_CURRENT_STATUS_END -->"
_WORKSTREAM_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,63}")
_SHORT_HEAD_RE = re.compile(r"[0-9a-f]{7,12}")
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
    handoff_initial_content: str = ""
    tvbcp_initial_content: str = ""
    decision: str = ""
    proposed_next_steps: tuple[str, ...] = ()
    last_deployed_main_short: str = ""
    last_deployed_at: str = ""
    last_deployed_test_count: int = 0
    last_deployed_smoke_count: int = 0


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


def _safe_optional_line(value: object, *, label: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    return _safe_line(text, label=label, limit=limit)


def _safe_proposed_next_steps(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise SimpleMainCheckpointError(
            "Navrhované další kroky checkpointu musí být seznam."
        )
    if len(value) > 4:
        raise SimpleMainCheckpointError(
            "Checkpoint smí obsahovat nejvýše čtyři navrhované další kroky."
        )
    return tuple(
        _safe_line(item, label="navrhovaný další krok", limit=300)
        for item in value
    )


def _safe_request(request: SimpleMainCheckpointRequest) -> SimpleMainCheckpointRequest:
    workstream_id = str(request.workstream_id or "").strip().casefold()
    if not _WORKSTREAM_ID_RE.fullmatch(workstream_id):
        raise SimpleMainCheckpointError("Checkpoint nemá platný identifikátor pracovního proudu.")
    deployment = _safe_deployment_snapshot(request)
    return SimpleMainCheckpointRequest(
        workstream_id=workstream_id,
        commit_message=_safe_line(request.commit_message, label="název", limit=120),
        summary=_safe_line(request.summary, label="souhrn", limit=400),
        next_step=_safe_line(request.next_step, label="další krok", limit=500),
        handoff_relative_path=str(request.handoff_relative_path or "").strip(),
        tvbcp_relative_path=str(request.tvbcp_relative_path or "").strip(),
        handoff_initial_content=_safe_initial_memory(
            request.handoff_initial_content,
            kind="handoff",
        ),
        tvbcp_initial_content=_safe_initial_memory(
            request.tvbcp_initial_content,
            kind="TVBCP",
        ),
        decision=_safe_optional_line(
            request.decision,
            label="rozhodnutí",
            limit=400,
        ),
        proposed_next_steps=_safe_proposed_next_steps(
            request.proposed_next_steps
        ),
        **deployment,
    )


def _safe_deployment_snapshot(
    request: SimpleMainCheckpointRequest,
) -> dict[str, object]:
    main_short = str(request.last_deployed_main_short or "").strip().casefold()
    deployed_at = str(request.last_deployed_at or "").strip()
    try:
        test_count = int(request.last_deployed_test_count or 0)
        smoke_count = int(request.last_deployed_smoke_count or 0)
    except (TypeError, ValueError) as exc:
        raise SimpleMainCheckpointError(
            "Poslední nasazení checkpointu nemá platné číselné důkazy."
        ) from exc
    values_present = bool(main_short or deployed_at or test_count or smoke_count)
    if not values_present:
        return {
            "last_deployed_main_short": "",
            "last_deployed_at": "",
            "last_deployed_test_count": 0,
            "last_deployed_smoke_count": 0,
        }
    try:
        parsed_at = datetime.fromisoformat(deployed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SimpleMainCheckpointError(
            "Poslední nasazení checkpointu nemá platný čas."
        ) from exc
    if (
        not _SHORT_HEAD_RE.fullmatch(main_short)
        or parsed_at.tzinfo is None
        or test_count <= 0
        or smoke_count != 5
    ):
        raise SimpleMainCheckpointError(
            "Poslední nasazení checkpointu nemá úplný serverový důkaz."
        )
    return {
        "last_deployed_main_short": main_short,
        "last_deployed_at": parsed_at.isoformat(),
        "last_deployed_test_count": test_count,
        "last_deployed_smoke_count": smoke_count,
    }


def _safe_initial_memory(value: object, *, kind: str) -> str:
    content = str(value or "").strip()
    if not content:
        return ""
    if len(content) > 20_000:
        raise SimpleMainCheckpointError(f"Počáteční {kind} překročil bezpečný limit.")
    if _SENSITIVE_TEXT_RE.search(content):
        raise SimpleMainCheckpointError(
            "Počáteční checkpointová paměť nesmí obsahovat heslo, token ani API klíč."
        )
    return content + "\n"


def _memory_path(
    project_root: Path,
    relative_text: str,
    *,
    kind: str,
    allow_missing: bool = False,
) -> Path:
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
    if root not in path.parents or unresolved.is_symlink():
        raise SimpleMainCheckpointError(f"Kanonický {kind} checkpointu nebyl nalezen.")
    relative_parts = path.relative_to(root).parts
    current = root
    for part in relative_parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise SimpleMainCheckpointError(f"Kanonický {kind} checkpointu nebyl nalezen.")
    if path.exists():
        if not path.is_file():
            raise SimpleMainCheckpointError(f"Kanonický {kind} checkpointu nebyl nalezen.")
    elif not allow_missing:
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


def _replace_current_status(content: str, block: str) -> str:
    """Replace only one generated current-status section, preserving history."""

    start_count = content.count(CURRENT_STATUS_START)
    end_count = content.count(CURRENT_STATUS_END)
    clean_block = block.strip()
    if start_count == 0 and end_count == 0:
        if not content:
            return clean_block + "\n"
        return clean_block + "\n\n" + content
    if start_count != 1 or end_count != 1:
        raise SimpleMainCheckpointError(
            "Aktuální souhrn paměti má nejednoznačné značky; checkpoint nic nepřepíše."
        )
    start = content.index(CURRENT_STATUS_START)
    end = content.index(CURRENT_STATUS_END, start)
    end += len(CURRENT_STATUS_END)
    if start >= end:
        raise SimpleMainCheckpointError(
            "Aktuální souhrn paměti má neplatné pořadí značek."
        )
    return content[:start] + clean_block + content[end:]


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
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější push ani nasazení.
- Ověření: {test_text}
- Změněné cesty před paměťovým zápisem ({len(changes)}): {path_text}
- Commit: `{request.commit_message}`
- Další krok: {request.next_step}
"""
    decision_text = (
        f"- {request.decision}"
        if request.decision
        else "- V tomto kroku nebylo přijato nové kanonické rozhodnutí."
    )
    proposed_steps_text = (
        "\n".join(f"- {item}" for item in request.proposed_next_steps)
        if request.proposed_next_steps
        else "- Nebyly zachyceny další návrhy nad rámec bezprostředního kroku."
    )
    tvbcp_block = f"""### {timestamp} – {request.summary}

Hotovo:
- {request.summary}

Rozhodnutí:
{decision_text}

Další krok:
- {request.next_step}

Navrhované další kroky:
{proposed_steps_text}

Technický důkaz:
- {test_text}.
- Pracovní proud: `{request.workstream_id}`.
"""
    return handoff_block, tvbcp_block


def _current_status_block(
    *,
    request: SimpleMainCheckpointRequest,
    evidence: GateEvidence,
    timestamp: str,
    source_head: str,
) -> str:
    source_short = str(source_head or "").strip().casefold()[:12]
    if not _SHORT_HEAD_RE.fullmatch(source_short):
        raise SimpleMainCheckpointError(
            "Aktuální souhrn nemá ověřený commit zdrojového main."
        )
    if request.last_deployed_main_short:
        deployment_relation = (
            "odpovídá ověřenému main před tímto checkpointem"
            if source_short.startswith(request.last_deployed_main_short)
            or request.last_deployed_main_short.startswith(source_short)
            else "je starší než ověřený main před tímto checkpointem"
        )
        deployment_text = (
            f"`{request.last_deployed_main_short}` · {deployment_relation} · "
            f"{request.last_deployed_test_count} testů · "
            f"smoke {request.last_deployed_smoke_count}/5 · "
            f"{request.last_deployed_at}"
        )
    else:
        deployment_text = "serverová deployment receipt pro tento proud není dostupná"
    decision_text = (
        request.decision
        or "V tomto kroku nebylo přijato nové kanonické rozhodnutí."
    )
    proposed_text = (
        "; ".join(request.proposed_next_steps)
        if request.proposed_next_steps
        else "žádné další návrhy nad rámec bezprostředního kroku"
    )
    return f"""{CURRENT_STATUS_START}
## Aktuální stav

- Obnoveno potvrzeným checkpointem: {timestamp}
- Poslední dokončený vývojový výsledek: {request.summary}
- Stav při vytvoření checkpointu: změna je otestovaná ({evidence.test_count} testů); tento snapshot je součástí jediné potvrzené commit/push operace a sám nepotvrzuje pozdější nasazení.
- Git před checkpointem: `main == origin/main` na `{source_short}`.
- Poslední serverově potvrzené nasazení: {deployment_text}.
- Rozhodnutí: {decision_text}
- Bezprostřední další krok: {request.next_step}
- Navrhované další kroky: {proposed_text}
- Aktuálnost: tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
{CURRENT_STATUS_END}"""


def _write_memory_pair(
    *,
    handoff_path: Path,
    tvbcp_path: Path,
    handoff_content: str,
    tvbcp_content: str,
    original_handoff: str,
    handoff_existed: bool,
) -> None:
    atomic_replace_text_under_external_lock(handoff_path, handoff_content)
    try:
        atomic_replace_text_under_external_lock(tvbcp_path, tvbcp_content)
    except OSError as exc:
        if handoff_existed:
            atomic_replace_text_under_external_lock(handoff_path, original_handoff)
        elif handoff_path.read_text(encoding="utf-8") == handoff_content:
            handoff_path.unlink()
        raise SimpleMainCheckpointError("TVBCP checkpointu se nepodařilo zapsat.") from exc


def _restore_memory_pair(
    *,
    handoff_path: Path,
    tvbcp_path: Path,
    original_handoff: str,
    original_tvbcp: str,
    written_handoff: str,
    written_tvbcp: str,
    handoff_existed: bool = True,
    tvbcp_existed: bool = True,
) -> None:
    try:
        if handoff_path.read_text(encoding="utf-8") == written_handoff:
            if handoff_existed:
                atomic_replace_text_under_external_lock(handoff_path, original_handoff)
            else:
                handoff_path.unlink()
        if tvbcp_path.read_text(encoding="utf-8") == written_tvbcp:
            if tvbcp_existed:
                atomic_replace_text_under_external_lock(tvbcp_path, original_tvbcp)
            else:
                tvbcp_path.unlink()
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
            allow_missing=bool(safe_request.handoff_initial_content),
        )
        tvbcp_path = _memory_path(
            workspace.project_root,
            safe_request.tvbcp_relative_path,
            kind="tvbcp",
            allow_missing=bool(safe_request.tvbcp_initial_content),
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

        handoff_existed = handoff_path.is_file()
        tvbcp_existed = tvbcp_path.is_file()
        original_handoff = (
            _read_memory_file(handoff_path)
            if handoff_existed
            else safe_request.handoff_initial_content
        )
        original_tvbcp = (
            _read_memory_file(tvbcp_path)
            if tvbcp_existed
            else safe_request.tvbcp_initial_content
        )
        timestamp = _format_timestamp(now_factory())
        handoff_block, tvbcp_block = _memory_blocks(
            request=safe_request,
            evidence=evidence,
            timestamp=timestamp,
            changes=list(initial.get("changes") or []),
        )
        current_status = _current_status_block(
            request=safe_request,
            evidence=evidence,
            timestamp=timestamp,
            source_head=live_origin_head,
        )
        written_handoff = _append_block(
            _replace_current_status(original_handoff, current_status),
            handoff_block,
        )
        written_tvbcp = _append_block(
            _replace_current_status(original_tvbcp, current_status),
            tvbcp_block,
        )
        progress("memory", "running")
        _write_memory_pair(
            handoff_path=handoff_path,
            tvbcp_path=tvbcp_path,
            handoff_content=written_handoff,
            tvbcp_content=written_tvbcp,
            original_handoff=original_handoff,
            handoff_existed=handoff_existed,
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
                handoff_existed=handoff_existed,
                tvbcp_existed=tvbcp_existed,
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
                handoff_existed=handoff_existed,
                tvbcp_existed=tvbcp_existed,
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
