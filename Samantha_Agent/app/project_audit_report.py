from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from app.backup.activity_state import DEFAULT_BACKUP_ACTIVITY_STATE_PATH, backup_activity_status
from app.capability_audit import format_samantha_capability_audit
from app.health_check import run_samantha_health_check
from app.quantitative_status import run_samantha_quantitative_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
MEMORY_DIR = PROJECT_ROOT / "memory"
REPORTS_DIR = MEMORY_DIR / "reports"
ACTIVE_PROJECTS_PATH = MEMORY_DIR / "ACTIVE_PROJECTS.md"
MEMORY_INDEX_PATH = MEMORY_DIR / "MEMORY_INDEX.md"

Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ProjectAuditItem:
    name: str
    priority: str
    lifecycle: str
    memory: str
    handoff: str
    status: str
    next_step: str
    inferred_type: str


@dataclass(frozen=True)
class AuditLayer:
    name: str
    status: str
    next_step: str


@dataclass(frozen=True)
class CapabilityAuditSummary:
    agent_tools: int | None
    mapped_tools: int | None
    unmapped_tools: int | None
    workflow_count: int | None
    gaps: tuple[str, ...]


@dataclass(frozen=True)
class ProjectAuditResult:
    created_at: str
    mode: str
    git_summary: str
    backup_summary: str
    backup_ok: bool
    reminder_count: int
    health_warnings: tuple[str, ...]
    quick_recommendations: tuple[str, ...]
    priority_1: tuple[ProjectAuditItem, ...]
    priority_2: tuple[ProjectAuditItem, ...]
    priority_3: tuple[ProjectAuditItem, ...]
    capability_summary: CapabilityAuditSummary
    local_files: int
    local_lines: int
    git_files: int
    git_lines: int
    layers: tuple[AuditLayer, ...]
    saved_path: Path | None


def format_samantha_project_audit(
    *,
    mode: str = "quick",
    save: bool = False,
    memory_dir: Path = MEMORY_DIR,
    project_root: Path = PROJECT_ROOT,
    repo_root: Path = REPO_ROOT,
    reports_dir: Path = REPORTS_DIR,
    backup_state_path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
    runner: Runner = subprocess.run,
) -> str:
    result = run_samantha_project_audit(
        mode=mode,
        save=save,
        memory_dir=memory_dir,
        project_root=project_root,
        repo_root=repo_root,
        reports_dir=reports_dir,
        backup_state_path=backup_state_path,
        runner=runner,
    )
    return format_project_audit_result(result)


def run_samantha_project_audit(
    *,
    mode: str = "quick",
    save: bool = False,
    memory_dir: Path = MEMORY_DIR,
    project_root: Path = PROJECT_ROOT,
    repo_root: Path = REPO_ROOT,
    reports_dir: Path = REPORTS_DIR,
    backup_state_path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
    runner: Runner = subprocess.run,
) -> ProjectAuditResult:
    normalized_mode = _normalize_mode(mode)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    active_projects_text = _read_text(memory_dir / "ACTIVE_PROJECTS.md")
    memory_index_text = _read_text(memory_dir / "MEMORY_INDEX.md")
    rows = parse_active_project_rows(active_projects_text)
    reminders = _reminder_lines(memory_index_text)

    health = run_samantha_health_check(
        mode="full" if normalized_mode == "full" else "quick",
        repo_root=repo_root,
        memory_dir=memory_dir,
        runner=runner,
    )
    quantitative = run_samantha_quantitative_status(
        save=False,
        project_root=project_root,
        repo_root=repo_root,
        runner=runner,
    )
    backup = backup_activity_status(path=backup_state_path)
    capability_text = format_samantha_capability_audit()
    capability = _parse_capability_summary(capability_text)
    local_totals = _stats_totals(quantitative.local_stats)
    git_totals = _stats_totals(quantitative.git_stats)

    priority_1, priority_2, priority_3 = _prioritize_items(rows, reminders, normalized_mode)
    recommendations = _quick_recommendations(
        git_summary=health.git_summary,
        backup_ok=bool(backup.get("ok")),
        reminder_count=len(reminders),
        capability=capability,
        priority_1=priority_1,
    )
    layers = _build_layers(
        git_summary=health.git_summary,
        backup_ok=bool(backup.get("ok")),
        reminder_count=len(reminders),
        capability=capability,
        priority_1=priority_1,
    )

    result = ProjectAuditResult(
        created_at=created_at,
        mode=normalized_mode,
        git_summary=health.git_summary,
        backup_summary=_one_line(str(backup.get("message", ""))),
        backup_ok=bool(backup.get("ok")),
        reminder_count=len(reminders),
        health_warnings=tuple(_sanitize_text(warning) for warning in health.warnings),
        quick_recommendations=recommendations,
        priority_1=priority_1,
        priority_2=priority_2,
        priority_3=priority_3,
        capability_summary=capability,
        local_files=local_totals[0],
        local_lines=local_totals[1],
        git_files=git_totals[0],
        git_lines=git_totals[1],
        layers=layers,
        saved_path=None,
    )
    if save:
        saved_path = save_project_audit_result(result, reports_dir=reports_dir)
        result = ProjectAuditResult(**{**result.__dict__, "saved_path": saved_path})
    return result


def parse_active_project_rows(active_projects_text: str) -> tuple[ProjectAuditItem, ...]:
    rows: list[ProjectAuditItem] = []
    headers: list[str] = []
    for line in active_projects_text.splitlines():
        if not line.startswith("| ") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not headers:
            headers = [_normalize_header(cell) for cell in cells]
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        row = dict(zip(headers, cells[: len(headers)], strict=False))
        rows.append(
            ProjectAuditItem(
                name=_sanitize_text(row.get("oblast", "")),
                priority=_sanitize_text(row.get("priorita", "")),
                lifecycle=_normalize_lifecycle(row.get("rezim", "")),
                memory=_sanitize_links(row.get("memory", "")),
                handoff=_sanitize_links(row.get("handoff", "")),
                status=_sanitize_text(row.get("stav", "")),
                next_step=_sanitize_text(row.get("dalsi", "")),
                inferred_type=_infer_item_type(row.get("oblast", ""), row.get("memory", "")),
            )
        )
    return tuple(rows)


def save_project_audit_result(result: ProjectAuditResult, *, reports_dir: Path = REPORTS_DIR) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    created = datetime.fromisoformat(result.created_at)
    date_stamp = created.strftime("%Y_%m_%d")
    path = reports_dir / f"systemovy_audit_projekty_tooly_vrstvy_{date_stamp}.txt"
    if path.exists():
        time_stamp = created.strftime("%H%M%S")
        path = reports_dir / f"systemovy_audit_projekty_tooly_vrstvy_{date_stamp}_{time_stamp}.txt"
    path.write_text(format_project_audit_result(result), encoding="utf-8")
    return path


def format_project_audit_result(result: ProjectAuditResult) -> str:
    lines = [
        "Nazev: Systemovy audit Samanthy - projekty, tooly, vrstvy",
        f"Datum: {result.created_at[:10]}",
        f"Mode: {result.mode}",
        "Zdroj: ACTIVE_PROJECTS.md, MEMORY_INDEX.md, health check, backup status, quantitative status, capability audit",
        "Ucel: Opakovatelny lidsky itinerar pro vyber, na co navazat.",
        "",
        "Bezpecnost:",
        "- Report je git-safe souhrn. Necetl private vault, cela tela e-mailu, soukrome dokumenty ani fulltexty clanku.",
        "- Vystup rediguje soukrome cesty a webove URL.",
        "- Stav priorit je odvozeny z registru projektu a systemovych reportu; neni to pravni, financni ani zdravotni doporuceni.",
        "",
        "======================================================================",
        "RANNI PROVOZNI POZNAMKA",
        "======================================================================",
        "",
        f"- Git: {result.git_summary}",
        f"- Zaloha: {result.backup_summary}",
        f"- Aktivnich `[PRIPOMENOUT]`: {result.reminder_count}",
        f"- Kvantitativne: lokalne {result.local_files} souboru / {result.local_lines} radku; git tracked {result.git_files} souboru / {result.git_lines} radku.",
        _capability_line(result.capability_summary),
        "",
        "Varovani:",
        *_bullet_lines(result.health_warnings or ("Zadna hlavni varovani z health checku.",)),
        "",
        "======================================================================",
        "RYCHLE DOPORUCENI PRO DNES",
        "======================================================================",
        "",
        *_numbered_lines(result.quick_recommendations),
        "",
        "======================================================================",
        "PRIORITA 1 - HLAVNI KANDIDATI",
        "======================================================================",
        "",
        *_format_items(result.priority_1),
        "",
        "======================================================================",
        "PRIORITA 2 - DOBRE NAVAZUJICI SMERY",
        "======================================================================",
        "",
        *_format_items(result.priority_2),
        "",
        "======================================================================",
        "PRIORITA 3 - UDRZBA, ARCHIV, NIZKA NALEHAVOST",
        "======================================================================",
        "",
        *_format_items(result.priority_3),
        "",
        "======================================================================",
        "TOOLY A SCHOPNOSTI - RYCHLA MAPA",
        "======================================================================",
        "",
        _capability_line(result.capability_summary),
        "Registry gaps:",
        *_bullet_lines(result.capability_summary.gaps or ("Bez zjevnych registry gaps.",)),
        "",
        "======================================================================",
        "VRSTVY - SYSTEMOVA ARCHITEKTURA",
        "======================================================================",
        "",
        *_format_layers(result.layers),
        "",
        "======================================================================",
        "ZAVER",
        "======================================================================",
        "",
        "Silne stranky:",
        "- System ma registrovane reporty, health check, capability audit a backup status.",
        "- Cockpit a knowledge/document vrstvy jsou napojene na projektovou pamet.",
        "- Report lze opakovat bez cteni private dat.",
        "",
        "Rizika:",
        f"- Git/provozni stav: {result.git_summary}.",
        f"- Pocet aktivnich `[PRIPOMENOUT]`: {result.reminder_count}.",
        "- Automaticky report sklada fakta; konecny vyber priority porad potvrzuje Mila.",
        "",
        f"Nejmensi dalsi krok: {result.quick_recommendations[0] if result.quick_recommendations else 'Vybrat jeden aktivni projekt a potvrdit dalsi krok.'}",
    ]
    if result.saved_path is not None:
        lines.extend(["", f"Ulozeno: {result.saved_path}"])
    return "\n".join(lines) + "\n"


def _prioritize_items(
    rows: Sequence[ProjectAuditItem],
    reminders: Sequence[str],
    mode: str,
) -> tuple[tuple[ProjectAuditItem, ...], tuple[ProjectAuditItem, ...], tuple[ProjectAuditItem, ...]]:
    active = [item for item in rows if item.lifecycle != "archived"]
    reminder_blob = "\n".join(reminders).casefold()
    priority_1 = [
        item
        for item in active
        if _priority_rank(item.priority) <= 1
        or item.name.casefold() in reminder_blob
        or "[pripomenout]" in item.status.casefold()
    ]
    priority_2 = [item for item in active if item not in priority_1 and _priority_rank(item.priority) == 2]
    priority_3 = [item for item in active if item not in priority_1 and item not in priority_2]
    if mode == "quick":
        return tuple(priority_1[:12]), tuple(priority_2[:8]), tuple(priority_3[:6])
    return tuple(priority_1), tuple(priority_2), tuple(priority_3)


def _quick_recommendations(
    *,
    git_summary: str,
    backup_ok: bool,
    reminder_count: int,
    capability: CapabilityAuditSummary,
    priority_1: Sequence[ProjectAuditItem],
) -> tuple[str, ...]:
    items: list[str] = []
    if _git_dirty_count(git_summary) >= 4 or "ahead" in git_summary:
        items.append("Nejdriv rozhodnout git stav: oddelit hotove commity od rozpracovanych zmen a pred pushem spustit safety check.")
    if not backup_ok:
        items.append("Pred vetsi praci vyresit backup warning a udelat novou recovery zalohu, pokud je dostupny externi disk.")
    if reminder_count >= 40:
        items.append("Zmensit sum v pameti: vybrat malou davku zastaralych `[PRIPOMENOUT]` a presunout je mimo startovni pozornost.")
    if capability.unmapped_tools:
        items.append("Doplnit capability mapu pro nemapovane tooly, aby lidske pokyny sly pres registrovane schopnosti.")
    if priority_1:
        items.append(f"Jako vecny smer vybrat jednu prioritu 1: {priority_1[0].name}. Dalsi krok: {priority_1[0].next_step}")
    items.append("Nemichat dnes vice velkych smeru; generator ma byt podklad pro vyber jedne konkretni navaznosti.")
    return tuple(_sanitize_text(item) for item in _dedupe(items)[:5])


def _build_layers(
    *,
    git_summary: str,
    backup_ok: bool,
    reminder_count: int,
    capability: CapabilityAuditSummary,
    priority_1: Sequence[ProjectAuditItem],
) -> tuple[AuditLayer, ...]:
    cockpit_status = "silna, pokud je Cockpit aktualne dostupny; overit manualnim smoke testem po zmenach"
    knowledge_status = "aktivni" if any("knihovna" in item.name.casefold() or "znalost" in item.name.casefold() for item in priority_1) else "stabilni"
    return (
        AuditLayer(
            "Lidska orientacni vrstva",
            f"funkcni, ale hluk `[PRIPOMENOUT]` je {reminder_count}",
            "cistit po malych davkach a drzet aktualni report v indexu",
        ),
        AuditLayer(
            "Provozni a recovery vrstva",
            "backup OK" if backup_ok else "backup vyzaduje pozornost",
            "pred rizikovou praci overit backup a git stav",
        ),
        AuditLayer(
            "Git checkpoint vrstva",
            git_summary,
            "oddělit hotove a rozpracovane veci do tematickych commitu",
        ),
        AuditLayer("Cockpit UI vrstva", cockpit_status, "manualni smoke test po zmenach"),
        AuditLayer("Private data vrstva", "oddelená od reportu", "pokracovat jen pres potvrzene tooly"),
        AuditLayer("Knowledge vrstva", knowledge_status, "sloucit orientaci clanku, receptu, AI nastroju a inboxu"),
        AuditLayer("Mobile/voice vrstva", "pouzitelna, ale resit jen pri realnem provoznim bloku", "pred approval z iPhonu pouzit cockpit notice pravidlo"),
        AuditLayer(
            "Workflow registry vrstva",
            "dobra zakladna" if not capability.unmapped_tools else "ma registry gaps",
            "dopsat mezery pred dalsim routovanim lidskych pokynu na shell",
        ),
    )


def _parse_capability_summary(text: str) -> CapabilityAuditSummary:
    values: dict[str, int] = {}
    gaps: list[str] = []
    in_gaps = False
    for line in text.splitlines():
        stripped = line.strip()
        for label, key in (
            ("- Agent tools:", "agent_tools"),
            ("- Mapped tools:", "mapped_tools"),
            ("- Unmapped tools:", "unmapped_tools"),
            ("- Registered shell workflows:", "workflow_count"),
        ):
            if stripped.startswith(label):
                values[key] = _first_int(stripped)
        if stripped == "Registry gaps:":
            in_gaps = True
            continue
        if in_gaps and stripped.startswith("- "):
            gaps.append(_sanitize_text(stripped.removeprefix("- ")))
        elif in_gaps and stripped and not stripped.startswith("- "):
            in_gaps = False
    return CapabilityAuditSummary(
        agent_tools=values.get("agent_tools"),
        mapped_tools=values.get("mapped_tools"),
        unmapped_tools=values.get("unmapped_tools"),
        workflow_count=values.get("workflow_count"),
        gaps=tuple(gaps),
    )


def _format_items(items: Sequence[ProjectAuditItem]) -> list[str]:
    if not items:
        return ["- Zadna polozka v teto sekci."]
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"{index}. {item.name}",
                f"Typ: {item.inferred_type}",
                f"Priorita: {item.priority or '-'}",
                f"Rezim: {item.lifecycle}",
                f"Stav: {_truncate(item.status, 420)}",
                f"Dalsi krok: {_truncate(item.next_step, 260)}",
                "",
            ]
        )
    return lines[:-1]


def _format_layers(layers: Sequence[AuditLayer]) -> list[str]:
    lines: list[str] = []
    for index, layer in enumerate(layers, start=1):
        lines.extend(
            [
                f"{index}. {layer.name}",
                f"Stav: {layer.status}",
                f"Dalsi krok: {layer.next_step}",
                "",
            ]
        )
    return lines[:-1]


def _capability_line(summary: CapabilityAuditSummary) -> str:
    return (
        "- Capability audit: "
        f"{_fmt_int(summary.agent_tools)} agent toolu, "
        f"{_fmt_int(summary.mapped_tools)} namapovanych, "
        f"{_fmt_int(summary.unmapped_tools)} nemapovanych, "
        f"{_fmt_int(summary.workflow_count)} shell workflow."
    )


def _normalize_header(value: str) -> str:
    return {
        "oblast": "oblast",
        "priorita": "priorita",
        "stav": "stav",
        "rezim": "rezim",
        "režim": "rezim",
        "memory soubor": "memory",
        "handoff": "handoff",
        "dalsi krok": "dalsi",
        "další krok": "dalsi",
    }.get(value.strip().casefold(), value.strip().casefold().replace(" ", "_"))


def _normalize_lifecycle(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in {"archiv", "archivni", "archivní", "archive", "archived"}:
        return "archived"
    if normalized in {"paused", "pause", "pozastavene", "pozastavené"}:
        return "paused"
    return "active"


def _priority_rank(priority: str) -> int:
    normalized = priority.strip().casefold()
    if normalized in {"a1+", "a1", "1", "p1", "priorita 1"}:
        return 1
    if normalized in {"2", "p2", "priorita 2"}:
        return 2
    if normalized in {"3", "p3", "priorita 3"}:
        return 3
    return 9


def _infer_item_type(name: str, memory: str) -> str:
    text = f"{name} {memory}".casefold()
    if "infrastructure" in text or "recovery" in text or "backup" in text or "git" in text:
        return "infrastructure layer"
    if "technical/" in text or "workflow" in text or "tool" in text:
        return "toolova / technicka oblast"
    if "cockpit" in text:
        return "projekt + UI vrstva"
    if "knihovna" in text or "knowledge" in text or "znalost" in text:
        return "projekt + knowledge vrstva"
    return "projekt"


def _sanitize_text(value: str) -> str:
    text = _sanitize_links(value)
    text = re.sub(r"`?data/private[^`\s|;,.]*`?", "`[private data]`", text)
    text = re.sub(r"`?~/Downloads[^`\s|;,.]*`?", "`[Downloads]`", text)
    text = re.sub(r"`?/Users/[^`\s|;,.]*`?", "`[local path]`", text)
    text = text.replace("[PRIPOMENOUT]", "[PRIPOMENOUT]")
    return _one_line(text)


def _sanitize_links(value: str) -> str:
    return re.sub(r"https?://[^\s`)|]+", "[URL]", value)


def _one_line(value: str) -> str:
    return " ".join(value.split())


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _reminder_lines(memory_index_text: str) -> tuple[str, ...]:
    return tuple(
        _sanitize_text(line.removeprefix("- "))
        for line in memory_index_text.splitlines()
        if "[PRIPOMENOUT]" in line
    )


def _stats_totals(stats: dict[object, object]) -> tuple[int, int]:
    files = sum(getattr(item, "files", 0) for item in stats.values())
    lines = sum(getattr(item, "lines", 0) for item in stats.values())
    return files, lines


def _git_dirty_count(git_summary: str) -> int:
    match = re.search(r"dirty \((\d+) changed/untracked\)", git_summary)
    return int(match.group(1)) if match else 0


def _first_int(text: str) -> int | None:
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def _fmt_int(value: int | None) -> str:
    return "?" if value is None else str(value)


def _bullet_lines(items: Sequence[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _numbered_lines(items: Sequence[str]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]


def _dedupe(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _normalize_mode(mode: str) -> str:
    normalized = mode.strip().casefold()
    if normalized in {"quick", "full"}:
        return normalized
    return "quick"
