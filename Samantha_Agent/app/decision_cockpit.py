"""Read-only prioritization for the Cockpit "Co teď?" overview."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from app.memory_truth_audit import (
    MemoryTruthAuditResult,
    STATUS_CANDIDATE_DRIFT,
    STATUS_PROVEN_CONTRADICTION,
)


MAX_DECISION_ITEMS = 3
ALLOWED_NAVIGATION_ACTIONS = {
    "open_projects",
    "open_recovery",
    "open_reminders",
    "open_document_review",
    "open_scandocu",
    "open_urgent_reminders",
}

CATEGORY_LABELS = {
    "blocks_now": "Blokuje nyní",
    "do_soon": "Udělat brzy",
    "needs_decision": "Čeká na rozhodnutí",
}


@dataclass(frozen=True)
class _Candidate:
    candidate_id: str
    dedupe_key: str
    category: str
    title: str
    reason: str
    source: str
    evidence_at: str | None
    priority: int
    sort_rank: int
    navigation: str = ""
    navigation_label: str = ""


def build_decision_cockpit(
    *,
    action_queue: Mapping[str, Any] | None,
    memory_truth: MemoryTruthAuditResult | None,
    handoff_next_steps: Mapping[str, str] | None = None,
    generated_at: str | None = None,
    memory_truth_error: str = "",
    limit: int = MAX_DECISION_ITEMS,
) -> dict[str, Any]:
    """Choose at most three explained next steps without performing an action."""

    created_at = generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    candidates = _action_candidates(action_queue or {}, created_at)
    if memory_truth is not None:
        candidates.extend(
            _memory_candidates(
                memory_truth,
                handoff_next_steps or {},
            )
        )

    selected: list[_Candidate] = []
    seen: set[str] = set()
    safe_limit = min(MAX_DECISION_ITEMS, max(0, int(limit)))
    for candidate in sorted(candidates, key=_candidate_sort_key):
        if candidate.dedupe_key in seen:
            continue
        seen.add(candidate.dedupe_key)
        selected.append(candidate)
        if len(selected) >= safe_limit:
            break

    items = [_candidate_payload(candidate, created_at) for candidate in selected]
    source_status = "ok" if memory_truth is not None else "partial"
    if not items:
        message = "Nic akutního. Další krok nyní neurčuje čerstvý důkaz."
    elif len(items) == 1:
        message = "Jeden aktuální další krok podle nejsilnějšího dostupného důkazu."
    else:
        message = f"{len(items)} aktuální další kroky podle síly a stáří důkazu."
    return {
        "ok": True,
        "read_only": True,
        "generated_at": created_at,
        "message": message,
        "max_items": MAX_DECISION_ITEMS,
        "items": items,
        "catalog_count": len(candidates),
        "source_status": source_status,
        "source_warning": _one_line(memory_truth_error, 240),
    }


def load_handoff_next_steps(
    memory_truth: MemoryTruthAuditResult,
    *,
    project_root: Path,
) -> dict[str, str]:
    """Read only the first declared next step from canonical handoffs."""

    result: dict[str, str] = {}
    root = Path(project_root).resolve()
    for row in memory_truth.rows:
        if not row.handoff_exists:
            continue
        path = (root / row.handoff_path).resolve()
        if root not in path.parents:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        next_step = extract_handoff_next_step(text)
        if next_step:
            result[row.workstream_id] = next_step
    return result


def extract_handoff_next_step(text: str) -> str:
    """Extract one concise line from a canonical ``Další krok`` section."""

    in_section = False
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if re.match(r"^#{2,6}\s+další\s+krok\s*$", line, flags=re.IGNORECASE):
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("#"):
            break
        cleaned = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line).strip()
        if cleaned:
            return _one_line(cleaned, 260)
    return ""


def _action_candidates(action_queue: Mapping[str, Any], generated_at: str) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for index, raw_item in enumerate(action_queue.get("items") or []):
        if not isinstance(raw_item, Mapping):
            continue
        priority = _priority(raw_item.get("priority"))
        action = _one_line(raw_item.get("action"), 80)
        navigation = action if action in ALLOWED_NAVIGATION_ACTIONS else ""
        category = "blocks_now" if priority == 1 else "do_soon"
        sort_rank = 0 if priority == 1 else 2 if priority == 2 else 5
        kind = _one_line(raw_item.get("kind"), 80) or "item"
        dedupe_action = navigation or kind
        candidates.append(
            _Candidate(
                candidate_id=f"live:{index:04d}:{kind}",
                dedupe_key=f"live:{dedupe_action}",
                category=category,
                title=_one_line(raw_item.get("title"), 180) or "Doporučená kontrola",
                reason=(
                    f"Živý provozní stav; P{priority}. "
                    f"{_one_line(raw_item.get('detail'), 240)}"
                ).strip(),
                source="Živý provozní status",
                evidence_at=generated_at,
                priority=priority,
                sort_rank=sort_rank,
                navigation=navigation,
                navigation_label=(
                    _one_line(raw_item.get("action_label"), 80) if navigation else ""
                ),
            )
        )
    return candidates


def _memory_candidates(
    memory_truth: MemoryTruthAuditResult,
    handoff_next_steps: Mapping[str, str],
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for row in memory_truth.rows:
        project_key = f"project:{row.workstream_id}"
        priority = _priority(row.expected_priority)
        if row.status == STATUS_PROVEN_CONTRADICTION:
            candidates.append(
                _Candidate(
                    candidate_id=f"memory-conflict:{row.workstream_id}",
                    dedupe_key=project_key,
                    category="needs_decision",
                    title=f"Srovnat stav projektu {_one_line(row.name, 120)}",
                    reason=_contradiction_reason(row.contradictions),
                    source="Živý audit pravdivosti paměti",
                    evidence_at=memory_truth.generated_at,
                    priority=1,
                    sort_rank=1,
                    navigation="open_projects",
                    navigation_label="Otevřít projekty",
                )
            )
            continue

        next_step = _one_line(handoff_next_steps.get(row.workstream_id, ""), 260)
        if row.expected_mode != "active" or not next_step:
            continue
        is_drift = row.status == STATUS_CANDIDATE_DRIFT
        candidates.append(
            _Candidate(
                candidate_id=f"handoff:{row.workstream_id}",
                dedupe_key=project_key,
                category="needs_decision" if is_drift else "do_soon",
                title=next_step,
                reason=(
                    f"{_one_line(row.name, 120)}: kanonická paměť je novější než souhrnný registr; "
                    "přednost má tento konkrétní handoff."
                    if is_drift
                    else f"{_one_line(row.name, 120)}: aktivní projekt P{priority}; krok pochází z kanonického handoffu."
                ),
                source="Kanonický handoff workstreamu",
                evidence_at=row.canonical_latest_committed_at,
                priority=priority,
                sort_rank=3 if is_drift else 4 + min(priority, 3),
                navigation="open_projects",
                navigation_label="Otevřít projekty",
            )
        )
    return candidates


def _candidate_sort_key(candidate: _Candidate) -> tuple[int, int, float, str]:
    timestamp = _parse_timestamp(candidate.evidence_at)
    freshness_rank = -timestamp.timestamp() if timestamp is not None else 0.0
    return (candidate.sort_rank, candidate.priority, freshness_rank, candidate.candidate_id)


def _candidate_payload(candidate: _Candidate, generated_at: str) -> dict[str, Any]:
    freshness, freshness_label = _freshness(candidate.evidence_at, generated_at)
    return {
        "id": candidate.candidate_id,
        "category": candidate.category,
        "category_label": CATEGORY_LABELS[candidate.category],
        "title": candidate.title,
        "reason": candidate.reason,
        "source": candidate.source,
        "evidence_at": candidate.evidence_at or "",
        "freshness": freshness,
        "freshness_label": freshness_label,
        "priority": candidate.priority,
        "navigation": candidate.navigation,
        "navigation_label": candidate.navigation_label,
    }


def _freshness(evidence_at: str | None, generated_at: str) -> tuple[str, str]:
    evidence = _parse_timestamp(evidence_at)
    generated = _parse_timestamp(generated_at)
    if evidence is None or generated is None:
        return "unknown", "stáří nezjištěno"
    seconds = max(0.0, (generated - evidence).total_seconds())
    if seconds <= 5 * 60:
        return "live", "živě ověřeno"
    if evidence.date() == generated.date():
        return "today", "dnešní snapshot"
    days = max(1, int(seconds // 86_400))
    return "historical", f"historická paměť ({days} d.)"


def _contradiction_reason(contradictions: tuple[str, ...]) -> str:
    labels: list[str] = []
    for contradiction in contradictions:
        if contradiction.startswith("mode_mismatch:"):
            labels.append("režim projektu se rozchází s kanonickým katalogem")
        elif contradiction.startswith("priority_mismatch:"):
            labels.append("priorita projektu se rozchází s kanonickým katalogem")
    detail = "; ".join(dict.fromkeys(labels)) or "formální údaje projektu si odporují"
    return f"Prokázaný rozpor: {detail}. Má přednost před běžnou historickou prioritou."


def _priority(value: object) -> int:
    try:
        return min(9, max(1, int(value)))
    except (TypeError, ValueError):
        return 9


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _one_line(value: object, limit: int) -> str:
    return " ".join(str(value or "").replace("\x00", "").split())[:limit]
