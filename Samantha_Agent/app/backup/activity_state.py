from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKUP_ACTIVITY_STATE_PATH = PROJECT_ROOT / "data" / "backup" / "activity_state.json"
BACKUP_WARNING_DAYS = 3


@dataclass(frozen=True)
class BackupActivityState:
    last_backup_at: str = ""
    last_backup_target: str = ""
    last_backup_mode: str = ""


def load_backup_activity_state(
    path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
) -> BackupActivityState:
    if not path.exists():
        return BackupActivityState()

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Backup activity state musi byt JSON objekt.")

    return BackupActivityState(
        last_backup_at=_string_or_empty(data.get("last_backup_at")),
        last_backup_target=_string_or_empty(data.get("last_backup_target")),
        last_backup_mode=_string_or_empty(data.get("last_backup_mode")),
    )


def save_backup_activity_state(
    state: BackupActivityState,
    path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_backup_at": state.last_backup_at,
        "last_backup_target": state.last_backup_target,
        "last_backup_mode": state.last_backup_mode,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def record_backup_completed(
    completed_at: date | str | None = None,
    target: str = "",
    mode: str = "manual",
    path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
) -> BackupActivityState:
    state = BackupActivityState(
        last_backup_at=_date_to_string(completed_at),
        last_backup_target=target,
        last_backup_mode=mode,
    )
    save_backup_activity_state(state, path)
    return state


def format_backup_activity_reminder(
    path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
    today: date | str | None = None,
) -> str:
    return backup_activity_status(path=path, today=today)["message"]


def backup_activity_status(
    path: Path = DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
    today: date | str | None = None,
) -> dict[str, Any]:
    today_date = _parse_today(today)
    try:
        state = load_backup_activity_state(path)
    except (json.JSONDecodeError, ValueError):
        message = (
            "ZALOHA SAMANTHY:\n"
            "- Nelze nacist lokalni data/backup/activity_state.json. "
            "Zkontroluj soubor pred dalsi zalohou."
        )
        return {
            "ok": False,
            "status": "error",
            "message": message,
            "last_backup_at": "",
            "last_backup_target": "",
            "last_backup_mode": "",
            "age_days": None,
            "warning_days": BACKUP_WARNING_DAYS,
        }

    backup_date = _parse_optional_date(state.last_backup_at)
    if backup_date is None:
        message = "\n".join(
            [
                "ZALOHA SAMANTHY:",
                (
                    "- Neni zaznam o posledni zaloze PythonMF/Samantha_Agent. "
                    "Pripoj externi disk a spust zalohu."
                ),
                "- Pripominka sama nic nekopiruje, nemaze ani necte tajemstvi.",
            ]
        )
        return {
            "ok": False,
            "status": "missing",
            "message": message,
            "last_backup_at": "",
            "last_backup_target": state.last_backup_target,
            "last_backup_mode": state.last_backup_mode,
            "age_days": None,
            "warning_days": BACKUP_WARNING_DAYS,
        }

    age_days = (today_date - backup_date).days
    if today_date - backup_date > timedelta(days=BACKUP_WARNING_DAYS):
        target = f" na {state.last_backup_target}" if state.last_backup_target else ""
        message = "\n".join(
            [
                "ZALOHA SAMANTHY:",
                (
                    f"- Posledni uspesna zaloha byla {backup_date.isoformat()}{target}. "
                    "Je starsi nez 3 dny. Pripoj externi disk a spust zalohu."
                ),
                "- Pripominka zustane aktivni pri startu, dokud neprobehnou nova zaloha.",
            ]
        )
        return {
            "ok": False,
            "status": "stale",
            "message": message,
            "last_backup_at": backup_date.isoformat(),
            "last_backup_target": state.last_backup_target,
            "last_backup_mode": state.last_backup_mode,
            "age_days": age_days,
            "warning_days": BACKUP_WARNING_DAYS,
        }

    message = "\n".join(
        [
            "ZALOHA SAMANTHY:",
            f"- Posledni zaloha je v 3dennim intervalu ({backup_date.isoformat()}).",
        ]
    )
    return {
        "ok": True,
        "status": "ok",
        "message": message,
        "last_backup_at": backup_date.isoformat(),
        "last_backup_target": state.last_backup_target,
        "last_backup_mode": state.last_backup_mode,
        "age_days": age_days,
        "warning_days": BACKUP_WARNING_DAYS,
    }


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
