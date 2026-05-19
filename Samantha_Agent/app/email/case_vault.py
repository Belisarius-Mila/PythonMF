from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .redaction import EMAIL_PATTERN


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMAIL_CASES_DIR = PROJECT_ROOT / "data" / "email" / "cases"
URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)


@dataclass(frozen=True)
class EmailCaseRecord:
    case_id: str
    source: dict[str, Any]
    classification: dict[str, Any]
    summary_redacted: str
    action_items: list[str]
    deadlines: list[str]
    link_domains: list[dict[str, Any]]
    attachments: list[dict[str, Any]]
    reminder_draft: dict[str, Any]
    status: str
    created_at: str


@dataclass(frozen=True)
class EmailCaseSaveResult:
    case_id: str
    created: bool
    message: str
    path: Path


def save_email_case_record(
    record: EmailCaseRecord | Mapping[str, Any],
    directory: Path = DEFAULT_EMAIL_CASES_DIR,
) -> EmailCaseSaveResult:
    record_dict = _safe_record_dict(record)
    case_id = _require_string(record_dict, "case_id")
    case_path = directory / f"{case_id}.json"

    if case_path.exists():
        return EmailCaseSaveResult(
            case_id=case_id,
            created=False,
            message="Case uz ve vaultu existuje; duplicita nebyla pridana.",
            path=case_path,
        )

    directory.mkdir(parents=True, exist_ok=True)
    with case_path.open("w", encoding="utf-8") as handle:
        json.dump(record_dict, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    _update_index(directory=directory, case_id=case_id)
    return EmailCaseSaveResult(
        case_id=case_id,
        created=True,
        message="Case byl ulozen do EmailCaseVault.",
        path=case_path,
    )


def load_email_case_record(case_id: str, directory: Path = DEFAULT_EMAIL_CASES_DIR) -> dict[str, Any]:
    safe_case_id = _safe_case_id(case_id)
    path = directory / f"{safe_case_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Case nenalezen: {safe_case_id}")

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Case JSON musi byt objekt.")
    _validate_safe_value(data)
    return data


def email_case_record_to_dict(record: EmailCaseRecord) -> dict[str, Any]:
    return {
        "case_id": record.case_id,
        "source": record.source,
        "classification": record.classification,
        "summary_redacted": record.summary_redacted,
        "action_items": record.action_items,
        "deadlines": record.deadlines,
        "link_domains": record.link_domains,
        "attachments": record.attachments,
        "reminder_draft": record.reminder_draft,
        "status": record.status,
        "created_at": record.created_at,
    }


def _safe_record_dict(record: EmailCaseRecord | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, EmailCaseRecord):
        record_dict = email_case_record_to_dict(record)
    else:
        record_dict = dict(record)

    _validate_required_fields(record_dict)
    _validate_safe_value(record_dict)
    return record_dict


def _validate_required_fields(record: Mapping[str, Any]) -> None:
    for field in (
        "case_id",
        "source",
        "classification",
        "summary_redacted",
        "action_items",
        "deadlines",
        "link_domains",
        "attachments",
        "reminder_draft",
        "status",
        "created_at",
    ):
        if field not in record:
            raise ValueError(f"Chybi povinne pole: {field}")


def _update_index(directory: Path, case_id: str) -> None:
    index_path = directory / "index.json"
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)
        if not isinstance(index, dict):
            index = {"cases": []}
    else:
        index = {"cases": []}

    cases = index.setdefault("cases", [])
    if not isinstance(cases, list):
        index["cases"] = []
        cases = index["cases"]
    if case_id not in cases:
        cases.append(case_id)

    with index_path.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _validate_safe_value(value: Any) -> None:
    if isinstance(value, str):
        if URL_PATTERN.search(value):
            raise ValueError("Case nesmi obsahovat plne URL.")
        if EMAIL_PATTERN.search(value):
            raise ValueError("Case nesmi obsahovat neredigovanou e-mailovou adresu.")
        return
    if isinstance(value, Mapping):
        for nested in value.values():
            _validate_safe_value(nested)
        return
    if isinstance(value, list | tuple):
        for nested in value:
            _validate_safe_value(nested)
        return
    if value is None or isinstance(value, int | float | bool):
        return
    raise ValueError(f"Nepodporovana hodnota v case JSON: {type(value).__name__}")


def _require_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Pole {key} musi byt neprazdny string.")
    return _safe_case_id(value)


def _safe_case_id(case_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", case_id):
        raise ValueError("case_id obsahuje nepovolene znaky.")
    return case_id
