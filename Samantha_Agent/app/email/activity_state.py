from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMAIL_ACTIVITY_STATE_PATH = PROJECT_ROOT / "data" / "email" / "activity_state.json"
EMAIL_ACTIVITY_WARNING_DAYS = 7


@dataclass(frozen=True)
class EmailActivityState:
    last_triage_at: str = ""
    last_archive_at: str = ""


def load_email_activity_state(
    path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
) -> EmailActivityState:
    if not path.exists():
        return EmailActivityState()

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Email activity state musi byt JSON objekt.")

    return EmailActivityState(
        last_triage_at=_string_or_empty(data.get("last_triage_at")),
        last_archive_at=_string_or_empty(data.get("last_archive_at")),
    )


def save_email_activity_state(
    state: EmailActivityState,
    path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_triage_at": state.last_triage_at,
        "last_archive_at": state.last_archive_at,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def record_email_triage_completed(
    completed_at: date | str | None = None,
    path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
) -> EmailActivityState:
    state = load_email_activity_state(path)
    updated = EmailActivityState(
        last_triage_at=_date_to_string(completed_at),
        last_archive_at=state.last_archive_at,
    )
    save_email_activity_state(updated, path)
    return updated


def record_email_archive_completed(
    completed_at: date | str | None = None,
    path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
) -> EmailActivityState:
    state = load_email_activity_state(path)
    updated = EmailActivityState(
        last_triage_at=state.last_triage_at,
        last_archive_at=_date_to_string(completed_at),
    )
    save_email_activity_state(updated, path)
    return updated


def format_email_activity_reminder(
    path: Path = DEFAULT_EMAIL_ACTIVITY_STATE_PATH,
    today: date | str | None = None,
) -> str:
    today_date = _parse_today(today)
    try:
        state = load_email_activity_state(path)
    except (json.JSONDecodeError, ValueError):
        return (
            "EMAIL UDRZBA:\n"
            "- Nelze nacist lokalni data/email/activity_state.json. "
            "Zkontroluj soubor, nez budes spoustet e-mailovou triage nebo archivaci."
        )

    lines = ["EMAIL UDRZBA:"]
    warnings: list[str] = []

    triage_date = _parse_optional_date(state.last_triage_at)
    if triage_date is None:
        warnings.append(
            "Neni zaznam o posledni e-mailove triage. Chces spustit Email Triage?"
        )
    elif today_date - triage_date > timedelta(days=EMAIL_ACTIVITY_WARNING_DAYS):
        warnings.append(
            f"E-maily nebyly projity od {triage_date.isoformat()}. "
            "Chces spustit Email Triage?"
        )

    archive_date = _parse_optional_date(state.last_archive_at)
    if archive_date is None:
        warnings.append(
            "Neni zaznam o posledni zaloze/archivaci dulezitych e-mailu. "
            "Chces vybrat zpravy k zaloze?"
        )
    elif today_date - archive_date > timedelta(days=EMAIL_ACTIVITY_WARNING_DAYS):
        warnings.append(
            f"Dulezite e-maily nebyly archivovany od {archive_date.isoformat()}. "
            "Chces vybrat zpravy k zaloze?"
        )

    if not warnings:
        return "\n".join(
            [
                "EMAIL UDRZBA:",
                (
                    "- E-mailova triage a zaloha dulezitych e-mailu jsou v "
                    "7dennim intervalu."
                ),
            ]
        )

    lines.extend(f"- {warning}" for warning in warnings)
    lines.append(
        "- Tato pripominka sama necte e-maily, nestahuje prilohy, neotevira odkazy "
        "ani nic neuklada."
    )
    return "\n".join(lines)


def _string_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _date_to_string(value: date | str | None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(value).isoformat()


def _parse_today(today: date | str | None) -> date:
    if today is None:
        return date.today()
    if isinstance(today, date):
        return today
    return date.fromisoformat(today)


def _parse_optional_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
