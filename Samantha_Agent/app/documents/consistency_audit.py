from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.documents.vault import DEFAULT_DOCUMENTS_DIR, read_jsonl, safe_text
from app.reminders.store import DEFAULT_REMINDERS_PATH, load_reminders_store


DEFAULT_AUDIT_DECISIONS_PATH = DEFAULT_DOCUMENTS_DIR / "index" / "consistency_audit_decisions.json"
AMOUNT_PATTERN = re.compile(r"(?P<amount>\d{1,3}(?:[ .]\d{3})*)\s*K[čc]")
PAYMENT_AMOUNT_PATTERN = re.compile(
    r"\b\d{1,3}(?:[ .\u00a0]\d{3})*(?:,\d{1,2})?\s*(?:K[čc]|CZK)\b",
    re.IGNORECASE,
)
POLICY_PATTERN = re.compile(
    r"(?:pojistn[áé]\s+smlouva|n[áa]vrh(?:u)?\s+pojistn[ée]\s+smlouvy|variabiln[íi]\s+symbol)\D{0,80}(\d{10})",
    re.IGNORECASE,
)
SPZ_PATTERN = re.compile(
    r"(?:RZ\s*/\s*VIN|Registra[čc]n[íi]\s+zna[čc]ka\s*\(SPZ\)|SPZ|RZ)\D{0,80}([0-9A-Z]{1,3})\s*([0-9A-Z]{3,5})",
    re.IGNORECASE,
)
VIN_PATTERN = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
PERIOD_PATTERN = re.compile(
    r"Obdob[íi]:\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\s*[-–]\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})",
    re.IGNORECASE,
)
START_PATTERN = re.compile(
    r"Po[čc][áa]tek\s+poji[šs]t[ěe]n[íi]:\s*(\d{1,2})\.(\d{1,2})\.(\d{4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AuditFact:
    source_type: str
    source_id: str
    title: str
    document_type: str
    asset_key: str
    asset_label: str
    insurer: str
    policy_numbers: tuple[str, ...]
    coverage_start: str
    coverage_end: str
    amounts: tuple[dict[str, str], ...]
    source_note: str = ""


def run_document_consistency_audit(
    *,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
    reminders_path: Path = DEFAULT_REMINDERS_PATH,
    decisions_path: Path | None = None,
) -> dict[str, Any]:
    facts = collect_insurance_auto_facts(vault_dir=vault_dir, reminders_path=reminders_path)
    findings = build_consistency_findings(facts)
    decisions = load_audit_decisions(decisions_path or DEFAULT_AUDIT_DECISIONS_PATH)
    active_findings, suppressed_findings = apply_audit_decisions(findings, decisions)
    severity_counts: dict[str, int] = defaultdict(int)
    for finding in active_findings:
        severity_counts[str(finding.get("severity", "info"))] += 1
    return {
        "ok": True,
        "scope": "insurance_auto",
        "fact_count": len(facts),
        "finding_count": len(active_findings),
        "raw_finding_count": len(findings),
        "suppressed_finding_count": len(suppressed_findings),
        "severity_counts": dict(sorted(severity_counts.items())),
        "findings": active_findings,
        "suppressed_findings": suppressed_findings,
        "decision_count": len(decisions),
    }


def format_document_consistency_audit(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Document consistency audit selhal: {safe_text(str(result.get('message', 'neznamá chyba')))}"
    lines = [
        "Document consistency audit (insurance/auto):",
        f"- Fakta: {int(result.get('fact_count', 0) or 0)}",
        f"- Nálezy: {int(result.get('finding_count', 0) or 0)}",
    ]
    suppressed_count = int(result.get("suppressed_finding_count", 0) or 0)
    if suppressed_count:
        lines.append(f"- Potlačeno lokálním rozhodnutím: {suppressed_count}")
    counts = result.get("severity_counts")
    if isinstance(counts, dict) and counts:
        lines.append(
            "- Závažnost: "
            + ", ".join(f"{safe_text(str(key))}={int(value)}" for key, value in sorted(counts.items()))
        )
    findings = result.get("findings")
    if not isinstance(findings, list) or not findings:
        lines.append("- Bez nalezených konfliktů.")
        return "\n".join(lines)

    lines.append("")
    for index, finding in enumerate(findings[:12], start=1):
        severity = safe_text(str(finding.get("severity", "info")))
        title = safe_text(str(finding.get("title", "Nález")))
        lines.append(f"{index}. [{severity}] {title}")
        message = safe_text(str(finding.get("message", "")))
        if message:
            lines.append(f"   {message}")
        items = finding.get("items")
        if isinstance(items, list):
            for item in items[:5]:
                if not isinstance(item, dict):
                    continue
                source = safe_text(str(item.get("source_id", "")))
                amount = safe_text(str(item.get("amount", "")))
                label = safe_text(str(item.get("label", "")))
                coverage = safe_text(str(item.get("coverage_start", "")))
                detail = " | ".join(part for part in (label, amount, coverage, source) if part)
                if detail:
                    lines.append(f"   - {detail}")
    return "\n".join(lines)


def collect_insurance_auto_facts(
    *,
    vault_dir: Path,
    reminders_path: Path,
) -> list[AuditFact]:
    text_by_id = {
        str(item.get("document_id", "")): str(item.get("text", ""))
        for item in read_jsonl(vault_dir / "index" / "text_index.jsonl")
    }
    facts: list[AuditFact] = []
    for row in read_jsonl(vault_dir / "index" / "documents_index.jsonl"):
        fact = document_row_to_fact(row=row, text=text_by_id.get(str(row.get("document_id", "")), ""))
        if fact is not None:
            facts.append(fact)

    try:
        reminders = load_reminders_store(reminders_path)["reminders"]
    except (OSError, ValueError):
        reminders = []
    for row in reminders:
        if isinstance(row, dict):
            fact = reminder_row_to_fact(row)
            if fact is not None:
                facts.append(fact)
    return facts


def document_row_to_fact(row: dict[str, Any], text: str) -> AuditFact | None:
    domain = str(row.get("domain", "")).casefold()
    document_type = str(row.get("document_type", "")).casefold()
    tags = " ".join(str(tag) for tag in row.get("tags", []) if isinstance(tag, str)).casefold()
    related_asset = str(row.get("related_asset", ""))
    combined = " ".join([domain, document_type, tags, related_asset, text[:5000]]).casefold()
    if "insurance" not in combined and "pojist" not in combined:
        return None
    asset = extract_vehicle_asset(related_asset=related_asset, text=text)
    if not asset[0]:
        return None
    amounts = extract_payment_amounts(text)
    if not amounts:
        amounts = tuple()
    coverage_start, coverage_end = extract_coverage_period(text)
    return AuditFact(
        source_type="document",
        source_id=safe_text(str(row.get("document_id", "")))[:180],
        title=safe_text(str(row.get("title") or row.get("original_filename") or row.get("document_id", "")))[:220],
        document_type=safe_text(str(row.get("document_type", "")))[:80],
        asset_key=asset[0],
        asset_label=asset[1],
        insurer=extract_insurer(text=text, fallback=str(row.get("counterparty", ""))),
        policy_numbers=extract_policy_numbers(" ".join([str(row.get("document_id", "")), text])),
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        amounts=amounts,
    )


def reminder_row_to_fact(row: dict[str, Any]) -> AuditFact | None:
    if safe_text(str(row.get("status", ""))).casefold() != "open":
        return None
    related_asset = str(row.get("related_asset", ""))
    if not related_asset:
        return None
    asset = extract_vehicle_asset(related_asset=related_asset, text="")
    if not asset[0]:
        return None
    amount_due = safe_text(str(row.get("amount_due", "")))
    amounts = ({"label": "otevřená připomínka", "amount": amount_due, "kind": "reminder"},) if amount_due else tuple()
    source = row.get("source") if isinstance(row.get("source"), dict) else {}
    return AuditFact(
        source_type="reminder",
        source_id=safe_text(str(row.get("id", "")))[:180],
        title=safe_text(str(row.get("title", "")))[:220],
        document_type="reminder",
        asset_key=asset[0],
        asset_label=asset[1],
        insurer=extract_insurer(text=" ".join([str(row.get("notes", "")), str(row.get("title", ""))]), fallback=str(source.get("sender", ""))),
        policy_numbers=extract_policy_numbers(" ".join([str(row.get("id", "")), str(row.get("notes", ""))])),
        coverage_start=safe_text(str(row.get("coverage_start", "")))[:40],
        coverage_end="",
        amounts=amounts,
        source_note=safe_text(str(row.get("amount_note", "")))[:240],
    )


def build_consistency_findings(facts: list[AuditFact]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    by_asset_start: dict[tuple[str, str], list[AuditFact]] = defaultdict(list)
    for fact in facts:
        if fact.asset_key and fact.coverage_start:
            by_asset_start[(fact.asset_key, fact.coverage_start)].append(fact)

    for (_asset_key, coverage_start), items in sorted(by_asset_start.items()):
        asset_label = best_asset_label(items)
        reminders = [item for item in items if item.source_type == "reminder"]
        if len(reminders) >= 2:
            findings.append(
                {
                    "severity": "critical",
                    "code": "duplicate_open_payment_reminders",
                    "title": f"Více otevřených platebních připomínek pro {asset_label}",
                    "message": "Nekonat platbu bez porovnání podkladů a uzavření redundantní připomínky.",
                    "asset": asset_label,
                    "coverage_start": coverage_start,
                    "items": fact_items(reminders),
                }
            )

        policy_numbers = sorted({number for item in items for number in item.policy_numbers})
        priced_items = [item for item in items if item.amounts]
        if len(policy_numbers) >= 2 and len(priced_items) >= 2:
            findings.append(
                {
                    "severity": "warning",
                    "code": "parallel_policy_paths_same_asset",
                    "title": f"Paralelní pojistné cesty pro {asset_label}",
                    "message": (
                        "Pro stejné vozidlo a stejný začátek krytí existuje více čísel smluv/návrhů. "
                        "Porovnat částky a zvolit jednu cestu."
                    ),
                    "asset": asset_label,
                    "coverage_start": coverage_start,
                    "policy_numbers": policy_numbers,
                    "items": fact_items(priced_items),
                }
            )

        for item in items:
            if len(item.amounts) >= 2:
                if document_payment_options_resolved_by_reminder(item, reminders):
                    continue
                findings.append(
                    {
                        "severity": "warning",
                        "code": "multiple_payment_options_in_document",
                        "title": f"Více platebních variant v dokumentu {item.title}",
                        "message": "Rozlišit základní platbu od volitelných připojištění nebo dodatků.",
                        "asset": item.asset_label,
                        "coverage_start": item.coverage_start,
                        "items": fact_amount_items(item),
                    }
                )
    return dedupe_findings(findings)


def best_asset_label(items: list[AuditFact]) -> str:
    labels = [item.asset_label for item in items if item.asset_label]
    for label in labels:
        upper = label.upper()
        if "VOLVO" in upper and "V40" in upper:
            return label
    for label in labels:
        if not label.casefold().startswith("auto "):
            return label
    return labels[0] if labels else "nezjištěná věc"


def fact_items(items: list[AuditFact]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in items:
        amount = primary_amount(item)
        result.append(
            {
                "source_type": item.source_type,
                "source_id": item.source_id,
                "label": item.title,
                "amount": amount,
                "coverage_start": item.coverage_start,
                "insurer": item.insurer,
            }
        )
    return result


def fact_amount_items(item: AuditFact) -> list[dict[str, str]]:
    return [
        {
            "source_type": item.source_type,
            "source_id": item.source_id,
            "label": safe_text(str(amount.get("label", ""))),
            "amount": safe_text(str(amount.get("amount", ""))),
            "coverage_start": item.coverage_start,
            "insurer": item.insurer,
        }
        for amount in item.amounts
    ]


def primary_amount(item: AuditFact) -> str:
    for amount in item.amounts:
        if amount.get("kind") in {"base_renewal", "payment_due", "reminder"}:
            return safe_text(str(amount.get("amount", "")))
    if item.amounts:
        return safe_text(str(item.amounts[0].get("amount", "")))
    return ""


def document_payment_options_resolved_by_reminder(document: AuditFact, reminders: list[AuditFact]) -> bool:
    if document.source_type != "document":
        return False
    has_optional_total = any(amount.get("kind") == "optional_total" for amount in document.amounts)
    base_amounts = {
        normalize_amount(str(amount.get("amount", "")))
        for amount in document.amounts
        if amount.get("kind") in {"base_renewal", "payment_due"}
    }
    if not has_optional_total or not base_amounts:
        return False
    reminder_amounts = {
        normalize_amount(str(amount.get("amount", "")))
        for reminder in reminders
        for amount in reminder.amounts
        if amount.get("kind") == "reminder"
    }
    return bool(base_amounts & reminder_amounts)


def load_audit_decisions(path: Path) -> dict[str, dict[str, Any]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}

    decisions: dict[str, dict[str, Any]] = {}
    if isinstance(raw, dict):
        for container_key in ("resolved_findings", "suppressed_findings"):
            container = raw.get(container_key)
            if isinstance(container, dict):
                for finding_id, decision in container.items():
                    if isinstance(decision, dict):
                        decisions[safe_text(str(finding_id))] = decision
        rows = raw.get("decisions")
    else:
        rows = raw
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            finding_id = safe_text(str(row.get("finding_id", "")))
            if finding_id:
                decisions[finding_id] = row
    return decisions


def apply_audit_decisions(
    findings: list[dict[str, Any]],
    decisions: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not decisions:
        return findings, []
    active: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for finding in findings:
        decision = decisions.get(str(finding.get("finding_id", "")))
        if decision and audit_decision_suppresses(decision):
            item = dict(finding)
            item["suppression"] = {
                "status": safe_text(str(decision.get("status") or decision.get("decision") or "resolved"))[:80],
                "reason": safe_text(str(decision.get("reason", "")))[:300],
                "decided_at": safe_text(str(decision.get("decided_at", "")))[:80],
            }
            suppressed.append(item)
        else:
            active.append(finding)
    return active, suppressed


def save_audit_decision(
    *,
    finding_id: str,
    status: str,
    reason: str,
    decisions_path: Path = DEFAULT_AUDIT_DECISIONS_PATH,
    decided_at: str = "",
) -> dict[str, Any]:
    safe_finding_id = safe_text(str(finding_id))[:120]
    safe_status = safe_text(str(status or "resolved"))[:80]
    if not safe_finding_id:
        return {"ok": False, "message": "Chybí finding_id auditního nálezu."}
    if not audit_decision_suppresses({"status": safe_status}):
        return {"ok": False, "message": "Auditní rozhodnutí musí mít stav resolved/suppressed/ok."}
    safe_reason = safe_text(str(reason))[:500]
    if len(safe_reason) < 8:
        return {"ok": False, "message": "Doplň krátký důvod, proč je nález v pořádku."}
    now = decided_at or datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        raw = json.loads(decisions_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raw = {}
    except (OSError, json.JSONDecodeError, TypeError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    decisions = raw.get("decisions")
    if not isinstance(decisions, list):
        decisions = []
    decisions = [item for item in decisions if isinstance(item, dict) and str(item.get("finding_id", "")) != safe_finding_id]
    decision = {
        "finding_id": safe_finding_id,
        "status": safe_status,
        "reason": safe_reason,
        "decided_at": now,
    }
    decisions.append(decision)
    raw["decisions"] = decisions
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "message": "Auditní nález byl uložen jako lokálně vyřešený.", "decision": decision}


def audit_decision_suppresses(decision: dict[str, Any]) -> bool:
    status = safe_text(str(decision.get("status") or decision.get("decision") or "")).casefold()
    return status in {"resolved", "suppressed", "ok", "ignored", "potlačeno", "potlaceno", "vyřešeno", "vyreseno"}


def dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for finding in findings:
        key = (
            str(finding.get("code", "")),
            str(finding.get("asset", "")),
            str(finding.get("coverage_start", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        finding["finding_id"] = consistency_finding_id(finding)
        result.append(finding)
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    result.sort(key=lambda item: (severity_order.get(str(item.get("severity", "")), 9), str(item.get("title", ""))))
    return result


def consistency_finding_id(finding: dict[str, Any]) -> str:
    items = finding.get("items") if isinstance(finding.get("items"), list) else []
    signature = {
        "code": safe_text(str(finding.get("code", ""))),
        "asset": safe_text(str(finding.get("asset", ""))),
        "coverage_start": safe_text(str(finding.get("coverage_start", ""))),
        "policy_numbers": [safe_text(str(item)) for item in finding.get("policy_numbers", []) if item],
        "items": [
            {
                "source_type": safe_text(str(item.get("source_type", ""))),
                "source_id": safe_text(str(item.get("source_id", ""))),
                "amount": normalize_amount(str(item.get("amount", ""))),
            }
            for item in items
            if isinstance(item, dict)
        ],
    }
    payload = json.dumps(signature, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "audit-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def extract_vehicle_asset(*, related_asset: str, text: str) -> tuple[str, str]:
    source = " ".join([related_asset, text[:8000]])
    spz_match = SPZ_PATTERN.search(source)
    vin_match = VIN_PATTERN.search(source)
    spz = ""
    if spz_match:
        spz = (spz_match.group(1) + spz_match.group(2)).upper()
    vin = vin_match.group(1).upper() if vin_match else ""
    upper = source.upper()
    vehicle = "VOLVO V40" if "VOLVO" in upper and "V40" in upper else "auto"
    if spz:
        return f"auto:spz:{spz}", f"{vehicle} SPZ {spz}"
    if vin:
        return f"auto:vin:{vin}", f"{vehicle} VIN {vin}"
    normalized = " ".join(safe_text(related_asset).upper().split())
    if normalized and "AUTO" in normalized:
        return f"auto:asset:{normalized}", normalized
    return "", ""


def extract_insurer(*, text: str, fallback: str = "") -> str:
    combined = " ".join([fallback, text[:6000]])
    folded = combined.casefold()
    if "česká podnikatelská pojišťovna" in folded or "ceska podnikatelska pojistovna" in folded:
        return "Česká podnikatelská pojišťovna, a. s., Vienna Insurance Group"
    if "čpp" in folded or "cpp" in folded:
        return "ČPP"
    return safe_text(fallback)[:180]


def extract_policy_numbers(text: str) -> tuple[str, ...]:
    numbers = set(POLICY_PATTERN.findall(text))
    for number in re.findall(r"\b(327\d{7})\b", text):
        numbers.add(number)
    return tuple(sorted(numbers))


def extract_coverage_period(text: str) -> tuple[str, str]:
    match = PERIOD_PATTERN.search(text)
    if match:
        start = iso_date(match.group(1), match.group(2), match.group(3))
        end = iso_date(match.group(4), match.group(5), match.group(6))
        return start, end
    match = START_PATTERN.search(text)
    if match:
        return iso_date(match.group(1), match.group(2), match.group(3)), ""
    return "", ""


def iso_date(day: str, month: str, year: str) -> str:
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_payment_amounts(text: str) -> tuple[dict[str, str], ...]:
    amounts: list[dict[str, str]] = []
    base_match = re.search(
        r"nov[ěe]\s+p[řr]edepsan[ée]\s+pojistn[ée]\s+[čc]in[íi]\s+([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE,
    )
    if base_match:
        amounts.append(
            {
                "kind": "base_renewal",
                "label": "stávající pojištění bez volitelného doplňku",
                "amount": normalize_amount(base_match.group(1)),
            }
        )

    extra_match = re.search(
        r"Ro[čc]n[íi]\s+pojistn[ée]\s+za\s+dopl[ňn]kov[ée]\s+poji[šs]t[ěe]n[íi].{0,120}?MAXI:\s*([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    total_match = re.search(
        r"Pojistn[ée]\s+za\s+pojistn[ée]\s+obdob[íi]\s*\(nav[ýy][šs]en[ée].{0,180}?MAXI\):\s*([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if total_match:
        label = "varianta s doplňkovým pojištěním MAXI"
        if extra_match:
            label = f"{label}; doplněk {normalize_amount(extra_match.group(1))}"
        amounts.append({"kind": "optional_total", "label": label, "amount": normalize_amount(total_match.group(1))})

    payment_due_match = re.search(
        r"Pojistn[ée]\s+za\s+pojistn[ée]\s+obdob[íi]\s*-\s*[čc][áa]stka\s+k\s+[úu]hrad[ěe]:\s*([0-9 ]+\s*K[čc])",
        text,
        flags=re.IGNORECASE,
    )
    if payment_due_match:
        amounts.append({"kind": "payment_due", "label": "částka k úhradě", "amount": normalize_amount(payment_due_match.group(1))})
    elif not amounts:
        transfer_match = re.search(r"ČÁSTKA K ÚHRADĚ\s*([0-9 ]+\s*K[čc])", text, flags=re.IGNORECASE)
        if transfer_match:
            amounts.append({"kind": "payment_due", "label": "částka k úhradě", "amount": normalize_amount(transfer_match.group(1))})

    return tuple(dedupe_amounts(amounts))


def extract_primary_payment_amount(text: str) -> dict[str, str] | None:
    """Choose one conservative payable insurance amount from the full text."""

    structured = extract_payment_amounts(text)
    for preferred_kind in ("payment_due", "base_renewal"):
        preferred = [
            item
            for item in structured
            if item.get("kind") == preferred_kind and item.get("amount")
        ]
        preferred_amounts = {
            str(item.get("amount", "")).strip()
            for item in preferred
            if str(item.get("amount", "")).strip()
        }
        if len(preferred_amounts) == 1:
            return dict(preferred[0])
        if len(preferred_amounts) > 1:
            return None

    scored: list[tuple[int, str]] = []
    for match in PAYMENT_AMOUNT_PATTERN.finditer(text):
        context = text[
            max(0, match.start() - 350) : min(len(text), match.end() + 350)
        ].casefold()
        score = 0
        if any(
            marker in context
            for marker in (
                "částka k úhradě",
                "castka k uhrade",
                "celkem k úhradě",
                "celkem k uhrade",
                "k zaplacení",
                "k zaplaceni",
            )
        ):
            score += 100
        if "splatnost" in context:
            score += 60
        if "pojistné" in context or "pojistne" in context:
            score += 40
        if "ročně" in context or "rocne" in context:
            score += 15
        if any(
            marker in context
            for marker in ("maxi", "voliteln", "doplňkov", "doplnkov")
        ):
            score -= 50
        scored.append((score, safe_text(match.group(0))[:80]))

    if not scored:
        return None
    best_score = max(score for score, _amount in scored)
    best_amounts = {
        " ".join(amount.replace("\u00a0", " ").split())
        for score, amount in scored
        if score == best_score and amount
    }
    if best_score < 60 or len(best_amounts) != 1:
        return None
    return {
        "kind": "contextual_payment",
        "label": "částka určená z platebního kontextu",
        "amount": next(iter(best_amounts)),
    }


def normalize_amount(value: str) -> str:
    match = AMOUNT_PATTERN.search(value)
    if not match:
        return safe_text(value)
    amount = " ".join(match.group("amount").replace(".", " ").split())
    return f"{amount} Kč"


def dedupe_amounts(amounts: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for amount in amounts:
        key = (amount.get("kind", ""), amount.get("amount", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(amount)
    return result


def audit_result_to_json(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)
