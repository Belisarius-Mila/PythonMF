from __future__ import annotations

import json
import shlex
import subprocess
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from agents import function_tool


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMANTHA_DIR = PROJECT_ROOT / "Samantha_Agent"
PYTHON_BIN = SAMANTHA_DIR / ".venv" / "bin" / "python"
BACKUP_SCRIPT = SAMANTHA_DIR / "scripts" / "backup_samantha_python.py"
HUMAN_ADAM_TAKEOVER_SCRIPT = SAMANTHA_DIR / "scripts" / "human_adam_takeover.py"
DEVELOPMENT_BRANCH_AUDIT_SCRIPT = SAMANTHA_DIR / "scripts" / "development_branch_audit.py"
HUMAN_ADAM_TAKEOVER_CONFIRMATION = "POTVRZUJI PREVZETI HUMAN-ADAM WIP DO MAIN"
SECURE_BACKUP_ROOT = Path("/Volumes/SamanthaSecureBackup/SamanthaBackups")
DEFAULT_PENDING_COMMAND_PATH = SAMANTHA_DIR / "data" / "workflows" / "pending_command.json"

Preflight = Callable[["WorkflowCommand"], str]


@dataclass(frozen=True)
class WorkflowCommand:
    command_id: str
    title: str
    purpose: str
    aliases: tuple[str, ...]
    argv: tuple[str, ...]
    cwd: Path
    risk: str
    writes: str
    requires_confirmation: bool = False
    intent_keywords: tuple[str, ...] = ()
    required_keyword_groups: tuple[tuple[str, ...], ...] = ()
    preflight: Preflight | None = None

    def exact_shell(self) -> str:
        return " ".join(shlex.quote(part) for part in self.argv)


WORKFLOW_COMMANDS: tuple[WorkflowCommand, ...] = (
    WorkflowCommand(
        command_id="backup_project_recovery",
        title="Ostra recovery zaloha PythonMF/Samantha",
        purpose="Vytvori novy recovery snapshot projektu do sifrovaneho externiho kontejneru.",
        aliases=(
            "uloz aktualni stav na externi disk",
            "zalohuj nas projekt na externi disk",
            "zálohuj náš projekt na externí disk",
            "zalohuj data projektu",
            "zálohuj data projektu",
            "zalohuj projekt",
            "zálohuj projekt",
            "spust zalohu projektu",
            "spusť zálohu projektu",
            "zalohuj samanthu",
            "zálohuj samanthu",
            "udelej recovery zalohu",
            "udělej recovery zálohu",
        ),
        argv=(
            str(PYTHON_BIN),
            str(BACKUP_SCRIPT),
            "--execute",
            "--profile",
            "recovery",
            "--target",
            str(SECURE_BACKUP_ROOT),
        ),
        cwd=SAMANTHA_DIR,
        risk="external_backup_write",
        writes=str(SECURE_BACKUP_ROOT),
        requires_confirmation=True,
        intent_keywords=(
            "zaloha",
            "zalohuj",
            "zazalohuj",
            "zazalohovat",
            "backup",
            "snapshot",
            "uloz",
            "ulozit",
            "ukladat",
            "stav",
            "projekt",
            "data",
            "prace",
            "samantha",
            "pythonmf",
            "externi disk",
            "externi",
            "disk",
            "sifrovany kontejner",
            "recovery",
        ),
        required_keyword_groups=(
            ("zaloha", "zalohuj", "zazalohuj", "zazalohovat", "backup", "snapshot", "uloz", "ulozit", "ukladat"),
            ("projekt", "data", "prace", "samantha", "pythonmf", "stav", "externi disk", "externi", "disk"),
        ),
        preflight=lambda command: _preflight_secure_backup(command),
    ),
    WorkflowCommand(
        command_id="backup_project_dry_run",
        title="Nahled recovery zalohy PythonMF/Samantha",
        purpose="Spusti kontrolni dry-run zalohy bez kopirovani souboru.",
        aliases=(
            "zkontroluj zalohu",
            "zkontroluj zálohu",
            "nahled zalohy",
            "náhled zálohy",
            "dry run zalohy",
            "dry-run zálohy",
        ),
        argv=(
            str(PYTHON_BIN),
            str(BACKUP_SCRIPT),
            "--dry-run",
            "--profile",
            "recovery",
            "--target",
            str(SECURE_BACKUP_ROOT),
        ),
        cwd=SAMANTHA_DIR,
        risk="read_only_preview",
        writes="nic, dry-run",
        requires_confirmation=False,
        intent_keywords=(
            "zkontroluj",
            "kontrola",
            "nahled",
            "over",
            "overit",
            "dry run",
            "dry-run",
            "zaloha",
            "backup",
            "projekt",
            "samantha",
            "pythonmf",
        ),
        required_keyword_groups=(
            ("zkontroluj", "kontrola", "nahled", "over", "overit", "dry run", "dry-run"),
            ("zaloha", "backup", "projekt", "samantha", "pythonmf"),
        ),
        preflight=lambda command: _preflight_secure_backup(command, dry_run=True),
    ),
    WorkflowCommand(
        command_id="development_branch_lifecycle_audit",
        title="Read-only audit životního cyklu vývojových větví",
        purpose="Bez změn klasifikuje dočasné větve a připojené worktrees vůči main.",
        aliases=(
            "audit wip větví",
            "audit wip vetvi",
            "zkontroluj vývojové větve",
            "zkontroluj vyvojove vetve",
            "prověř životní cyklus větví",
            "prover zivotni cyklus vetvi",
        ),
        argv=(str(PYTHON_BIN), str(DEVELOPMENT_BRANCH_AUDIT_SCRIPT)),
        cwd=SAMANTHA_DIR,
        risk="read_only_preview",
        writes="nic, pouze čte Git reference a stav worktrees",
        requires_confirmation=False,
        intent_keywords=(
            "audit",
            "zkontroluj",
            "prover",
            "wip",
            "vyvojove vetve",
            "zivotni cyklus vetvi",
            "worktree",
        ),
        required_keyword_groups=(
            ("audit", "zkontroluj", "prover", "kontrola"),
            ("wip", "vyvojove vetve", "vetve", "zivotni cyklus vetvi", "worktree"),
        ),
    ),
    WorkflowCommand(
        command_id="human_adam_takeover_audit",
        title="Kontrola Human–Adam WIP checkpointu",
        purpose="Read-only ověří, zda lze jeden izolovaný WIP převzít přesným fast-forwardem.",
        aliases=(
            "zkontroluj human adam checkpoint",
            "zkontroluj vzdaleny wip",
            "nahled prevzeti vzdalenych zmen",
            "audit remote checkpointu",
        ),
        argv=(str(PYTHON_BIN), str(HUMAN_ADAM_TAKEOVER_SCRIPT), "audit"),
        cwd=SAMANTHA_DIR,
        risk="read_only_preview",
        writes="nic, pouze Git metadata a cesty změn",
        requires_confirmation=False,
        intent_keywords=("kontrola", "zkontroluj", "audit", "nahled", "prevzeti", "human adam", "wip", "checkpoint"),
        required_keyword_groups=(
            ("kontrola", "zkontroluj", "audit", "nahled"),
            ("human adam", "wip", "checkpoint", "vzdaleny"),
        ),
    ),
    WorkflowCommand(
        command_id="human_adam_takeover_apply",
        title="Převzetí Human–Adam WIP do main a push",
        purpose="Po potvrzení převezme přesně jeden ověřený WIP fast-forwardem a pushne main bez přepisu historie.",
        aliases=(
            "prevezmi human adam checkpoint do main",
            "prevezmi vzdaleny wip do main",
            "aplikuj remote checkpoint",
            "pushni overeny human adam wip",
        ),
        argv=(
            str(PYTHON_BIN),
            str(HUMAN_ADAM_TAKEOVER_SCRIPT),
            "apply",
            "--push",
            "--confirm",
            HUMAN_ADAM_TAKEOVER_CONFIRMATION,
        ),
        cwd=SAMANTHA_DIR,
        risk="git_fast_forward_push",
        writes="lokální main, origin/main a base metadata izolovaného workspace",
        requires_confirmation=True,
        intent_keywords=("prevezmi", "aplikuj", "pushni", "main", "human adam", "wip", "checkpoint", "vzdaleny"),
        required_keyword_groups=(
            ("prevezmi", "aplikuj", "pushni"),
            ("human adam", "wip", "checkpoint", "vzdaleny"),
        ),
        preflight=lambda command: _preflight_human_adam_takeover(command),
    ),
)


@function_tool
def list_workflow_commands() -> str:
    """List known exact workflow commands that Samantha may run."""
    return list_workflow_commands_text()


@function_tool
def preview_workflow_command(request: str = "", command_id: str = "") -> str:
    """Preview the exact shell command matched to a human workflow request."""
    return preview_workflow_command_text(request=request, command_id=command_id)


@function_tool
def run_workflow_command(
    request: str = "",
    command_id: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Run one known workflow command from the approved local registry."""
    return run_workflow_command_text(
        request=request,
        command_id=command_id,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def list_workflow_commands_text() -> str:
    lines = ["Zname workflow prikazy:"]
    for command in WORKFLOW_COMMANDS:
        lines.extend(
            [
                f"- id: {command.command_id}",
                f"  nazev: {command.title}",
                f"  zamer: {command.purpose}",
                f"  vyznamove pojmy: {', '.join(command.intent_keywords) or 'neuvedeno'}",
                f"  zapisuje: {command.writes}",
                f"  presny prikaz: {command.exact_shell()}",
            ]
        )
    lines.append("Poznamka: Samantha smi spoustet jen prikazy z tohoto registru.")
    return "\n".join(lines)


def preview_workflow_command_text(
    request: str = "",
    command_id: str = "",
    pending_path: Path = DEFAULT_PENDING_COMMAND_PATH,
) -> str:
    resolved = _resolve_command(request=request, command_id=command_id)
    if isinstance(resolved, str):
        return resolved

    preflight_error = resolved.preflight(resolved) if resolved.preflight is not None else ""
    lines = [
        "Nahled workflow prikazu:",
        f"- id: {resolved.command_id}",
        f"- nazev: {resolved.title}",
        f"- ucel: {resolved.purpose}",
        f"- cwd: {resolved.cwd}",
        f"- riziko: {resolved.risk}",
        f"- zapisuje: {resolved.writes}",
        f"- vyzaduje potvrzeni: {_yes_no(resolved.requires_confirmation)}",
        "",
        "Presny shell prikaz:",
        resolved.exact_shell(),
        "",
        "Stav:",
    ]
    if preflight_error:
        lines.append(f"- nelze spustit: {preflight_error}")
    else:
        lines.append("- pripraveno ke spusteni")
        if resolved.requires_confirmation:
            _save_pending_command(resolved, pending_path=pending_path)
            lines.extend(
                [
                    "",
                    "Potvrzeni:",
                    "- Pro spusteni napis `ano` nebo `potvrzuji` v dalsi zprave.",
                    "- Samantha potom spusti prave tento ulozeny prikaz, ne novy shell.",
                ]
            )
    lines.append("Nahled nic nespustil ani nekopiroval.")
    return "\n".join(lines)


def run_workflow_command_text(
    request: str = "",
    command_id: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    pending_path: Path = DEFAULT_PENDING_COMMAND_PATH,
) -> str:
    resolved = _resolve_command(
        request=request,
        command_id=command_id,
        pending_path=pending_path,
        allow_pending_confirmation=True,
    )
    if isinstance(resolved, str):
        return resolved

    preflight_error = resolved.preflight(resolved) if resolved.preflight is not None else ""
    if preflight_error:
        return f"Workflow prikaz nespusten: {preflight_error}"

    if resolved.requires_confirmation and not _has_command_confirmation(
        command=resolved,
        confirmation_text=confirmation_text,
        user_confirmed=user_confirmed,
        pending_path=pending_path,
    ):
        return (
            "Workflow prikaz nespusten: chybi samostatne potvrzeni.\n"
            f"Nejdrive si nech zobrazit nahled prikazu a potom napis `ano`, "
            f"nebo napis: Potvrzuji spusteni workflow prikazu {resolved.command_id}."
        )

    result = runner(
        list(resolved.argv),
        cwd=str(resolved.cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    output = _tail_lines(output, max_lines=80)

    if result.returncode != 0:
        return (
            "Workflow prikaz nedobehl uspesne.\n"
            f"- id: {resolved.command_id}\n"
            f"- exit code: {result.returncode}\n"
            f"- presny prikaz: {resolved.exact_shell()}\n\n"
            f"{output}"
        ).strip()

    _clear_pending_command(resolved.command_id, pending_path=pending_path)
    return (
        "Workflow prikaz dokoncen.\n"
        f"- id: {resolved.command_id}\n"
        f"- nazev: {resolved.title}\n"
        f"- presny prikaz: {resolved.exact_shell()}\n\n"
        f"{output}"
    ).strip()


def _resolve_command(
    request: str = "",
    command_id: str = "",
    pending_path: Path = DEFAULT_PENDING_COMMAND_PATH,
    allow_pending_confirmation: bool = False,
) -> WorkflowCommand | str:
    command_id = (command_id or "").strip()
    if command_id:
        for command in WORKFLOW_COMMANDS:
            if command.command_id == command_id:
                return command
        return f"Neznamy workflow command_id: {command_id}."

    query = _normalize(request)
    if not query:
        return "Chybi lidsky pokyn nebo command_id workflow prikazu."
    if allow_pending_confirmation and _is_simple_confirmation(query):
        pending = _load_pending_command(pending_path)
        if pending is not None:
            for command in WORKFLOW_COMMANDS:
                if (
                    command.command_id == pending.get("command_id")
                    and command.exact_shell() == pending.get("exact_shell")
                ):
                    return command
        return "Neni ulozeny workflow prikaz cekajici na potvrzeni. Nejdrive si nech zobrazit nahled."

    scored: list[tuple[int, WorkflowCommand]] = []
    query_terms = set(query.split())
    for command in WORKFLOW_COMMANDS:
        if not _matches_required_keyword_groups(command, query, query_terms):
            continue
        best = _score_command_intent(command, query, query_terms)
        if best >= 20:
            scored.append((best, command))

    if not scored:
        return (
            "Nenasla jsem odpovidajici workflow prikaz. "
            "Pouzij list_workflow_commands nebo pridej novy prikaz do registru."
        )
    scored.sort(key=lambda item: item[0], reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        top_score = scored[0][0]
        ids = ", ".join(command.command_id for score, command in scored if score == top_score)
        return f"Pokyn je nejednoznacny. Kandidati: {ids}."
    return scored[0][1]


def _score_command_intent(command: WorkflowCommand, query: str, query_terms: set[str]) -> int:
    best = 0
    for alias in command.aliases:
        normalized_alias = _normalize(alias)
        if normalized_alias and normalized_alias in query:
            best = max(best, 120 + len(normalized_alias.split()))
            continue
        alias_terms = set(normalized_alias.split())
        overlap = query_terms & alias_terms
        if alias_terms and overlap:
            best = max(best, len(overlap) * 8 - (len(alias_terms - overlap) * 2))

    keyword_score = 0
    for keyword in command.intent_keywords:
        normalized_keyword = _normalize(keyword)
        if not normalized_keyword:
            continue
        if " " in normalized_keyword and normalized_keyword in query:
            keyword_score += 25 + len(normalized_keyword.split())
        elif normalized_keyword in query_terms:
            keyword_score += 10

    descriptor_terms = set(
        _normalize(f"{command.title} {command.purpose} {command.command_id}").split()
    )
    descriptor_overlap = query_terms & descriptor_terms
    descriptor_score = min(len(descriptor_overlap) * 3, 15)
    return max(best, keyword_score + descriptor_score)


def _matches_required_keyword_groups(
    command: WorkflowCommand,
    query: str,
    query_terms: set[str],
) -> bool:
    for group in command.required_keyword_groups:
        if not any(_keyword_matches(keyword, query, query_terms) for keyword in group):
            return False
    return True


def _keyword_matches(keyword: str, query: str, query_terms: set[str]) -> bool:
    normalized = _normalize(keyword)
    if not normalized:
        return False
    if " " in normalized:
        return normalized in query
    return normalized in query_terms


def _preflight_secure_backup(command: WorkflowCommand, dry_run: bool = False) -> str:
    if not BACKUP_SCRIPT.is_file():
        return f"chybi backup skript {BACKUP_SCRIPT}"
    if not SECURE_BACKUP_ROOT.parent.exists():
        return (
            f"neni pripojeny sifrovany kontejner {SECURE_BACKUP_ROOT.parent}. "
            "Pripoj externi disk a kontejner SamanthaSecureBackup"
        )
    if not str(Path(command.writes if not dry_run else SECURE_BACKUP_ROOT)).startswith(
        str(SECURE_BACKUP_ROOT.parent)
    ):
        return "recovery zaloha nema bezpecny cil SamanthaSecureBackup"
    return ""


def _preflight_human_adam_takeover(_command: WorkflowCommand) -> str:
    if not HUMAN_ADAM_TAKEOVER_SCRIPT.is_file():
        return f"chybi takeover skript {HUMAN_ADAM_TAKEOVER_SCRIPT}"
    completed = subprocess.run(
        [str(PYTHON_BIN), str(HUMAN_ADAM_TAKEOVER_SCRIPT), "audit"],
        cwd=str(SAMANTHA_DIR),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode == 0:
        return ""
    detail = (completed.stderr or completed.stdout).strip().splitlines()
    return detail[-1] if detail else "Human–Adam WIP audit není připravený"


def _has_command_confirmation(
    command: WorkflowCommand,
    confirmation_text: str,
    user_confirmed: bool,
    pending_path: Path = DEFAULT_PENDING_COMMAND_PATH,
) -> bool:
    if not user_confirmed:
        return False
    normalized = _normalize(confirmation_text)
    explicit = (
        _normalize(command.command_id) in normalized
        and "potvrzuji" in normalized
        and any(word in normalized for word in ("spusteni", "spustit", "provedeni", "provest"))
    )
    if explicit:
        return True
    pending = _load_pending_command(pending_path)
    return (
        pending is not None
        and pending.get("command_id") == command.command_id
        and pending.get("exact_shell") == command.exact_shell()
        and _is_simple_confirmation(normalized)
    )


def _save_pending_command(command: WorkflowCommand, pending_path: Path) -> None:
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "command_id": command.command_id,
        "title": command.title,
        "exact_shell": command.exact_shell(),
        "cwd": str(command.cwd),
        "writes": command.writes,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    pending_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_pending_command(pending_path: Path) -> dict[str, str] | None:
    try:
        data = json.loads(pending_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return {str(key): str(value) for key, value in data.items()}


def _clear_pending_command(command_id: str, pending_path: Path) -> None:
    pending = _load_pending_command(pending_path)
    if pending is None or pending.get("command_id") != command_id:
        return
    try:
        pending_path.unlink()
    except FileNotFoundError:
        return


def _is_simple_confirmation(normalized_text: str) -> bool:
    return normalized_text in {
        "ano",
        "jo",
        "potvrzuji",
        "souhlasim",
        "souhlasim spustit",
        "spustit",
        "spust",
        "proved",
        "proved to",
    }


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(ascii_text.replace("-", " ").replace("_", " ").split())


def _tail_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    omitted = len(lines) - max_lines
    return "\n".join([f"... zkraceno, vynechano {omitted} radku ...", *lines[-max_lines:]])


def _yes_no(value: bool) -> str:
    return "ano" if value else "ne"
