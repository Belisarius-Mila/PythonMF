from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .case_vault import DEFAULT_EMAIL_CASES_DIR, load_email_case_record
from .redaction import EMAIL_PATTERN, redact_email_addresses


FULL_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def start_work_mode(case_id: str, directory: Path = DEFAULT_EMAIL_CASES_DIR):
    from .work_mode_models import WorkMode

    record = load_email_case_record(case_id=case_id, directory=directory)
    return WorkMode(case_id=case_id, case_record=record, vault_directory=directory)


def format_work_mode_detail(work_mode) -> str:
    record = work_mode.case_record
    source = _mapping(record.get("source"))
    classification = _mapping(record.get("classification"))

    lines = [
        f"Case: {_safe_text(record.get('case_id'))}",
        f"Status: {_safe_text(record.get('status'))}",
        f"Zdroj: {_safe_text(source.get('type'))}",
        f"UID: {_safe_text(source.get('uid'))}",
        f"Datum: {_safe_text(source.get('date'))}",
        f"Odesilatel: {_safe_text(source.get('sender'))}",
        f"Predmet: {_safe_text(source.get('subject'))}",
        f"Priorita: {_safe_text(classification.get('importance'))}",
        f"Kategorie: {_safe_text(classification.get('category'))}",
        f"Duvod: {_safe_text(classification.get('reason'))}",
        "",
        "Shrnuti:",
        _safe_text(record.get("summary_redacted")) or "(nenalezen text)",
        "",
        "Akcni kroky:",
    ]

    action_items = _list(record.get("action_items"))
    lines.extend(f"- {_safe_text(item)}" for item in action_items) if action_items else lines.append("- Nenalezeny")

    lines.extend(["", "Deadliny:"])
    deadlines = _list(record.get("deadlines"))
    lines.extend(f"- {_safe_text(item)}" for item in deadlines) if deadlines else lines.append("- Nenalezeny")

    lines.extend(["", "Odkazy domeny:"])
    link_domains = _list(record.get("link_domains"))
    if link_domains:
        for link in link_domains:
            link_map = _mapping(link)
            lines.append(f"- {_safe_text(link_map.get('domain'))}: {_safe_text(link_map.get('count'))}")
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Prilohy metadata:"])
    attachments = _list(record.get("attachments"))
    if attachments:
        for attachment in attachments:
            attachment_map = _mapping(attachment)
            size = _safe_text(attachment_map.get("size_bytes")) or "neznamy"
            lines.append(
                "- "
                f"{_safe_text(attachment_map.get('filename'))} | "
                f"{_safe_text(attachment_map.get('content_type'))} | "
                f"{size} B | part_id={_safe_text(attachment_map.get('part_id'))}"
            )
    else:
        lines.append("- Nenalezeny")

    if _safe_text(source.get("type")).casefold() == "email":
        lines.extend(
            [
                "",
                "Poznamka: znovu cist zdrojovy e-mail, zobrazit plne URL, otevrit URL "
                "nebo stahnout prilohu vyzaduje dalsi samostatne potvrzeni.",
            ]
        )

    lines.extend(["", format_work_mode_actions(work_mode)])
    return "\n".join(lines)


def build_work_mode_action_plan(work_mode) -> object:
    from .work_mode_models import WorkModeActionPlan

    return WorkModeActionPlan(
        available_actions=(
            "zobrazit detail case",
            "vytvorit nebo aktualizovat bezpecnou pripominku",
            "doplnit bezpecnou poznamku k pripadu",
            "pripravit navrh odpovedi bez odeslani",
            "oznacit case jako hotovy",
        ),
        requires_confirmation=(
            "znovu cist zdrojovy e-mail podle UID",
            "zobrazit plne URL",
            "otevrit URL v browseru",
            "stahnout prilohu",
            "odeslat e-mail",
            "smazat, presunout nebo oznacit e-mail jako precteny",
        ),
    )


def format_work_mode_actions(work_mode) -> str:
    plan = build_work_mode_action_plan(work_mode)
    lines = ["Mozne dalsi akce:"]
    lines.extend(f"- {item}" for item in plan.available_actions)
    lines.append("Dalsi samostatne potvrzeni vyzaduje:")
    lines.extend(f"- {item}" for item in plan.requires_confirmation)
    return "\n".join(lines)


def _safe_text(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = FULL_URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    return " ".join(text.split())


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []
