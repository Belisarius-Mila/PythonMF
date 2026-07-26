"""One confirmed canonical workstream checkpoint completed on ``main``.

The backend runs the established gate and Git transaction, then projects one
redacted live-status snapshot into the same handoff/TVBCP commit.  It never
creates a second post-push documentation commit.
"""

from __future__ import annotations

import re
import subprocess
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
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
from app.communication.workstream_live_status import (
    LIVE_STATUS_SCHEMA_VERSION,
    build_workstream_live_status,
)
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
    operational_context: Mapping[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class CheckpointStatusProjection:
    completed: tuple[str, ...]
    open_items: tuple[str, ...]
    risks: tuple[str, ...]
    next_step: str


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
        operational_context=_safe_operational_context(
            request.operational_context
        ),
        **deployment,
    )


def _safe_operational_context(value: object) -> dict[str, Any]:
    """Copy only evidence fields consumed by the redacted live-status builder."""

    if not isinstance(value, Mapping):
        return {}
    deployment = value.get("deployment")
    deployment_map = deployment if isinstance(deployment, Mapping) else {}
    safe_deployment = {
        key: deployment_map.get(key)
        for key in (
            "state",
            "main_head",
            "main_short",
            "expected_code_stamp",
            "test_count",
            "smoke_count",
            "gate_passed",
            "smoke_passed",
            "deployed_at",
            "prepared_at",
        )
    }
    runtime = value.get("runtime")
    runtime_map = runtime if isinstance(runtime, Mapping) else {}
    session = value.get("session")
    session_map = session if isinstance(session, Mapping) else {}
    messages = session_map.get("messages")
    safe_messages: list[dict[str, Any]] = []
    if isinstance(messages, Sequence) and not isinstance(messages, (str, bytes)):
        for item in messages[-200:]:
            if not isinstance(item, Mapping):
                continue
            safe_messages.append(
                {
                    "status": str(item.get("status") or ""),
                    "recovery_required": item.get("recovery_required") is True,
                }
            )
    server = value.get("server")
    server_map = server if isinstance(server, Mapping) else {}
    return {
        "deployment_expected": value.get("deployment_expected")
        if isinstance(value.get("deployment_expected"), bool)
        else None,
        "deployment": safe_deployment,
        "runtime": {
            "reachable": runtime_map.get("reachable")
            if isinstance(runtime_map.get("reachable"), bool)
            else None,
        },
        "session": {
            "connected": session_map.get("connected")
            if isinstance(session_map.get("connected"), bool)
            else None,
            "turn_busy": bool(session_map.get("turn_busy")),
            "active_turn": bool(session_map.get("active_turn")),
            "messages": safe_messages,
        },
        "server": {
            "code_stamp": str(server_map.get("code_stamp") or ""),
        },
    }


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


def _checkpoint_live_status(
    *,
    request: SimpleMainCheckpointRequest,
    observed_at: datetime,
    source_snapshot: Mapping[str, Any],
    origin_head: str,
    workspace_snapshots: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    context = request.operational_context
    source_head = str(source_snapshot.get("source_head") or "")
    return build_workstream_live_status(
        workstream_id=request.workstream_id,
        observed_at=observed_at.isoformat(),
        source_snapshot=source_snapshot,
        remote_snapshot={
            "state": "aligned",
            "local_head": source_head,
            "origin_head": origin_head,
            "read_only": True,
            "writes_performed": False,
        },
        workspace_snapshots=workspace_snapshots,
        deployment_snapshot=context.get("deployment"),
        runtime_snapshot=context.get("runtime"),
        session_snapshot=context.get("session"),
        server_snapshot=context.get("server"),
    )


def _checkpoint_status_projection(
    *,
    request: SimpleMainCheckpointRequest,
    live_status: Mapping[str, Any],
) -> CheckpointStatusProjection:
    completed = [request.summary]
    deployment_expected = request.operational_context.get(
        "deployment_expected"
    )
    open_items: list[str] = []
    if deployment_expected is True:
        open_items.append(
            "Pozdější nasazení nového checkpointu zatím není tímto "
            "snapshotem doložené."
        )
    elif deployment_expected is None:
        open_items.append(
            "Potřeba následného nasazení tohoto checkpointu není v provozním "
            "snapshotu určená."
        )
    risks: list[str] = []
    valid_live_status = bool(
        live_status.get("schema_version") == LIVE_STATUS_SCHEMA_VERSION
        and live_status.get("read_only") is True
        and live_status.get("writes_performed") is False
        and live_status.get("workstream_id") == request.workstream_id
    )
    if not valid_live_status:
        risks.append(
            "Živý provozní stav nebyl pro tento checkpoint bezpečně ověřen."
        )
    else:
        main = live_status.get("main")
        deployment = live_status.get("deployment")
        runtime = live_status.get("runtime")
        main_map = main if isinstance(main, Mapping) else {}
        deployment_map = deployment if isinstance(deployment, Mapping) else {}
        runtime_map = runtime if isinstance(runtime, Mapping) else {}

        main_state = str(main_map.get("state") or "unverified")
        if main_state != "aligned":
            risks.append(
                "Stav lokálního main a origin/main nebyl v živém snapshotu "
                "doložen jako zarovnaný."
            )

        if deployment_expected is True:
            deployment_state = str(
                deployment_map.get("state") or "unverified"
            )
            if deployment_state == "verified_current":
                completed.append(
                    "Předchozí stav main byl před tímto checkpointem serverově "
                    "nasazený a ověřený."
                )
            elif deployment_state == "pending_restart":
                open_items.append(
                    "Předchozí nasazení čeká na dokončení restartu a "
                    "serverového důkazu."
                )
            elif deployment_state == "verified_other_main":
                risks.append(
                    "Poslední ověřené nasazení patří jinému commitu než main "
                    "před tímto checkpointem."
                )
            elif deployment_state == "code_mismatch":
                risks.append(
                    "Deployment receipt a kódový otisk běžícího serveru se "
                    "neshodují."
                )
            elif deployment_state == "current_head_server_unverified":
                risks.append(
                    "Commit nasazení odpovídá main, ale běžící server nemá "
                    "úplný ověřený kódový důkaz."
                )
            elif deployment_state == "unavailable":
                risks.append(
                    "Pro tento pracovní proud není dostupný serverový důkaz "
                    "nasazení."
                )
            else:
                risks.append(
                    "Serverový důkaz posledního nasazení nelze bezpečně ověřit."
                )

        runtime_state = str(runtime_map.get("state") or "unverified")
        if runtime_state == "delivery_uncertain":
            risks.append(
                "Aktivní relace má neuzavřenou nejistotu doručení."
            )
        elif runtime_state == "busy":
            risks.append("Aktivní relace měla při snapshotu rozpracovaný tah.")

    if not risks:
        risks.append("Žádné další doložené provozní riziko.")
    if not open_items:
        open_items.append(
            "Žádný samostatný provozní bod nad rámec dalšího kroku."
        )
    return CheckpointStatusProjection(
        completed=tuple(completed),
        open_items=tuple(open_items),
        risks=tuple(risks),
        next_step=request.next_step,
    )


def _projection_lines(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _live_state_text(live_status: Mapping[str, Any]) -> str:
    return (
        f"main=`{_safe_mapping_state(live_status, 'main')}`, "
        f"deployment=`{_safe_mapping_state(live_status, 'deployment')}`, "
        f"runtime=`{_safe_mapping_state(live_status, 'runtime')}`"
    )


def _memory_blocks(
    *,
    request: SimpleMainCheckpointRequest,
    evidence: GateEvidence,
    timestamp: str,
    changes: Sequence[dict[str, str]],
    projection: CheckpointStatusProjection,
    live_status: Mapping[str, Any],
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
    completed_text = "; ".join(projection.completed)
    open_text = "; ".join(projection.open_items)
    risk_text = "; ".join(projection.risks)
    handoff_block = f"""### Automatický checkpoint {timestamp}

- Pracovní proud: `{request.workstream_id}`
- Hotovo: {completed_text}
- Otevřeno: {open_text}
- Rizika: {risk_text}
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: {test_text}
- Změněné cesty před paměťovým zápisem ({len(changes)}): {path_text}
- Commit: `{request.commit_message}`
- Další krok: {projection.next_step}
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
{_projection_lines(projection.completed)}

Otevřeno:
{_projection_lines(projection.open_items)}

Rizika:
{_projection_lines(projection.risks)}

Rozhodnutí:
{decision_text}

Další krok:
- {projection.next_step}

Navrhované další kroky:
{proposed_steps_text}

Technický důkaz:
- {test_text}.
- Pracovní proud: `{request.workstream_id}`.
- Read-only živý stav při checkpointu: {_live_state_text(live_status)}.
"""
    return handoff_block, tvbcp_block


def _safe_mapping_state(value: Mapping[str, Any], key: str) -> str:
    nested = value.get(key)
    if not isinstance(nested, Mapping):
        return "unverified"
    state = str(nested.get("state") or "unverified").strip()
    return state if re.fullmatch(r"[a-z][a-z0-9_]{1,63}", state) else "unverified"


def _current_status_block(
    *,
    request: SimpleMainCheckpointRequest,
    evidence: GateEvidence,
    timestamp: str,
    source_head: str,
    projection: CheckpointStatusProjection,
    live_status: Mapping[str, Any],
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
        "\n".join(f"- {item}" for item in request.proposed_next_steps)
        if request.proposed_next_steps
        else "- Žádné další návrhy nad rámec bezprostředního kroku."
    )
    return f"""{CURRENT_STATUS_START}
## Aktuální stav

- Obnoveno potvrzeným checkpointem: {timestamp}

### Hotovo
{_projection_lines(projection.completed)}

### Otevřeno
{_projection_lines(projection.open_items)}

### Rizika
{_projection_lines(projection.risks)}

### Další krok
- {projection.next_step}

### Rozhodnutí
- {decision_text}

### Navrhované další kroky
{proposed_text}

### Technický stav checkpointu
- Změna je otestovaná ({evidence.test_count} testů).
- Git před checkpointem: `main == origin/main` na `{source_short}`.
- Poslední serverově potvrzené nasazení: {deployment_text}.
- Read-only živý stav: {_live_state_text(live_status)}.
- Tento snapshot je součástí jediné potvrzené commit/push operace a sám nepotvrzuje pozdější nasazení.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
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
        peer_preflight_statuses: list[dict[str, Any]] = []
        for peer_index, peer in enumerate(peer_workspaces, start=1):
            if peer.workspace_root == workspace.workspace_root:
                continue
            peer_preflight_statuses.append(
                _preflight_workspace(
                    peer,
                    require_changes=False,
                    allow_source_ahead=True,
                )
            )
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
        observed_at = now_factory()
        timestamp = _format_timestamp(observed_at)
        live_status = _checkpoint_live_status(
            request=safe_request,
            observed_at=observed_at,
            source_snapshot=refreshed,
            origin_head=live_origin_head,
            workspace_snapshots=(refreshed, *peer_preflight_statuses),
        )
        projection = _checkpoint_status_projection(
            request=safe_request,
            live_status=live_status,
        )
        handoff_block, tvbcp_block = _memory_blocks(
            request=safe_request,
            evidence=evidence,
            timestamp=timestamp,
            changes=list(initial.get("changes") or []),
            projection=projection,
            live_status=live_status,
        )
        current_status = _current_status_block(
            request=safe_request,
            evidence=evidence,
            timestamp=timestamp,
            source_head=live_origin_head,
            projection=projection,
            live_status=live_status,
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
