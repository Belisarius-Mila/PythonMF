"""Server-owned, redacted operational capabilities for Human–Adam."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable

from app.family_calendar_delivery_dry_run import (
    FamilyCalendarOperationalDryRunResult,
    run_family_calendar_operational_dry_run,
)
from app.family_calendar_delivery_test_email import (
    FamilyCalendarTestEmailPlan,
    plan_family_calendar_test_email,
)


OPERATION_MARKER_START = "[HUMAN_ADAM_OPERATION_REQUEST]"
OPERATION_MARKER_END = "[/HUMAN_ADAM_OPERATION_REQUEST]"
FAMILY_CALENDAR_WORKSTREAM_ID = "project-family-calendar"
FAMILY_CALENDAR_DRY_RUN_TODAY = "family_calendar_delivery_dry_run_today"
FAMILY_CALENDAR_DRY_RUN_CANDIDATE = "family_calendar_delivery_dry_run_candidate"
FAMILY_CALENDAR_TEST_EMAIL_PREVIEW = "family_calendar_test_email_preview"
FAMILY_CALENDAR_OPERATION_IDS = (
    FAMILY_CALENDAR_DRY_RUN_TODAY,
    FAMILY_CALENDAR_DRY_RUN_CANDIDATE,
    FAMILY_CALENDAR_TEST_EMAIL_PREVIEW,
)
MMTX_WORKSTREAM_ID = "project-mmtx"
MMTX_PAGES_DEPLOY = "mmtx_pages_publish_current_main"
GITHUB_PAGES_TARGET = "github_pages"
_OPERATION_ID_RE = re.compile(r"[a-z][a-z0-9_]{2,95}")
_DRY_RUN_KEYS = frozenset(
    {
        "status",
        "candidate_count",
        "d2_count",
        "d1_count",
        "eligible_count",
        "recipient_count",
        "coordinator_called",
        "transport_called",
    }
)
_TEST_EMAIL_PREVIEW_KEYS = frozenset(
    {
        "status",
        "mode",
        "recipient_count",
        "confirmation_required",
        "transport_called",
    }
)
_PRIVATE_TEXT_MARKERS = ("@", "/users/", "\\users\\", "file:", "path:")


class HumanAdamOperationError(RuntimeError):
    """Raised when an operation request cannot be executed safely."""


@dataclass(frozen=True)
class HumanAdamOperationRequest:
    operation_id: str


@dataclass(frozen=True)
class ParsedHumanAdamOperation:
    state: str
    visible_answer: str
    request: HumanAdamOperationRequest | None = None
    error: str = ""


DryRunRunner = Callable[..., FamilyCalendarOperationalDryRunResult]
TestEmailPlanner = Callable[..., FamilyCalendarTestEmailPlan]
ProductionPublisher = Callable[[], dict[str, object]]


def explicit_publish_and_deploy_command(value: object) -> bool:
    """Recognize only a complete, direct publication command from Míla."""

    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    normalized = " ".join(normalized.split())
    return normalized in {
        "p+n",
        "prosím p+n",
        "prosim p+n",
        "proveď p+n",
        "proved p+n",
        "push a nasaď",
        "push a nasad",
        "push a nasaď na produkci",
        "push a nasad na produkci",
        "push + nasazení",
        "push + nasazeni",
        "nasaď na produkci",
        "nasad na produkci",
    }


def automatic_operation_instruction(
    *,
    workstream_id: str,
    production_deployment_target: str = "",
    publication_authorized: bool = False,
) -> str:
    """Return the private receipt protocol only for an allowed workstream."""

    clean_workstream = str(workstream_id or "").strip()
    clean_target = str(production_deployment_target or "").strip()
    if clean_workstream == MMTX_WORKSTREAM_ID and clean_target == GITHUB_PAGES_TARGET:
        example = json.dumps(
            {"operation_id": MMTX_PAGES_DEPLOY},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return "\n".join(
            (
                "[AUTOMATIC_OPERATION_REQUEST]",
                "enabled=true",
                "scope=server_owned_mmtx_github_push_and_pages_deployment",
                f"allowed_operation_ids={MMTX_PAGES_DEPLOY}",
                f"publication_authorized={'true' if publication_authorized else 'false'}",
                "rule=Use the receipt only when publication_authorized=true.",
                "rule=The server, not the model, performs the exact GitHub push, Pages workflow and verification.",
                "rule=Never improvise shell, gh, Git commands, workflow IDs, paths or credentials.",
                "rule=Use the operation receipt only on a clean read-only turn and never with a step-completion receipt.",
                f"receipt_start={OPERATION_MARKER_START}",
                f"receipt_json_example={example}",
                f"receipt_end={OPERATION_MARKER_END}",
                "rule=The receipt must be the final block and contain exactly one operation_id.",
                "[/AUTOMATIC_OPERATION_REQUEST]",
            )
        )
    if clean_workstream != FAMILY_CALENDAR_WORKSTREAM_ID:
        return ""
    example = json.dumps(
        {"operation_id": FAMILY_CALENDAR_DRY_RUN_TODAY},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return "\n".join(
        (
            "[AUTOMATIC_OPERATION_REQUEST]",
            "enabled=true",
            "scope=server_owned_read_only_family_calendar_operations",
            f"allowed_operation_ids={','.join(FAMILY_CALENDAR_OPERATION_IDS)}",
            "rule=Use a receipt only when Mila asks to execute one matching operation.",
            "rule=Do not ask terminal Adam to run these allowed read-only operations.",
            "rule=Never use this protocol for SMTP send, config mutation, arbitrary shell, paths or arguments.",
            "rule=Use the operation receipt only on a clean read-only turn and never together with a step-completion receipt.",
            f"receipt_start={OPERATION_MARKER_START}",
            f"receipt_json_example={example}",
            f"receipt_end={OPERATION_MARKER_END}",
            "rule=The receipt must be the final block and contain exactly one operation_id.",
            "[/AUTOMATIC_OPERATION_REQUEST]",
        )
    )


def parse_human_adam_operation(answer: object) -> ParsedHumanAdamOperation:
    """Parse one final operational receipt and hide it from the visible answer."""

    text = str(answer or "").strip()
    start_count = text.count(OPERATION_MARKER_START)
    end_count = text.count(OPERATION_MARKER_END)
    if start_count == 0 and end_count == 0:
        return ParsedHumanAdamOperation(state="absent", visible_answer=text)

    start_index = text.find(OPERATION_MARKER_START)
    visible = (
        text[:start_index].rstrip()
        if start_index >= 0
        else text.replace(OPERATION_MARKER_END, "").strip()
    )
    if start_count != 1 or end_count != 1 or start_index < 0:
        return ParsedHumanAdamOperation(
            state="invalid",
            visible_answer=visible,
            error="Provozní účtenka má neplatné nebo opakované značky.",
        )
    end_index = text.find(
        OPERATION_MARKER_END,
        start_index + len(OPERATION_MARKER_START),
    )
    if end_index < 0 or text[end_index + len(OPERATION_MARKER_END) :].strip():
        return ParsedHumanAdamOperation(
            state="invalid",
            visible_answer=visible,
            error="Provozní účtenka musí být posledním blokem odpovědi.",
        )
    payload_text = text[
        start_index + len(OPERATION_MARKER_START) : end_index
    ].strip()
    try:
        payload = json.loads(payload_text)
        if not isinstance(payload, dict) or set(payload) != {"operation_id"}:
            raise ValueError("Provozní účtenka nemá přesně jedno povolené pole.")
        operation_id = str(payload.get("operation_id") or "").strip()
        if not _OPERATION_ID_RE.fullmatch(operation_id):
            raise ValueError("Provozní účtenka nemá platné ID operace.")
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return ParsedHumanAdamOperation(
            state="invalid",
            visible_answer=visible,
            error=str(exc) or "Provozní účtenka není platná.",
        )
    if not visible:
        return ParsedHumanAdamOperation(
            state="invalid",
            visible_answer="",
            error="Odpověď před provozní účtenkou je prázdná.",
        )
    return ParsedHumanAdamOperation(
        state="valid",
        visible_answer=visible,
        request=HumanAdamOperationRequest(operation_id=operation_id),
    )


def execute_human_adam_operation(
    request: HumanAdamOperationRequest,
    *,
    workstream_id: str,
    today_factory: Callable[[], date] = date.today,
    dry_run_runner: DryRunRunner = run_family_calendar_operational_dry_run,
    test_email_planner: TestEmailPlanner = plan_family_calendar_test_email,
    publication_authorized: bool = False,
    production_publisher: ProductionPublisher | None = None,
) -> dict[str, object]:
    """Execute one fixed read-only operation and return a validated safe document."""

    clean_workstream = str(workstream_id or "").strip()
    if not isinstance(request, HumanAdamOperationRequest):
        raise HumanAdamOperationError("Chybí ověřený požadavek provozní operace.")

    operation_id = request.operation_id
    if operation_id == MMTX_PAGES_DEPLOY:
        if clean_workstream != MMTX_WORKSTREAM_ID:
            raise HumanAdamOperationError("Pracovní proud nemá povolené MMTX nasazení.")
        if publication_authorized is not True:
            raise HumanAdamOperationError("Chybí přímý pokyn p+n nebo nasazení na produkci.")
        if production_publisher is None or not callable(production_publisher):
            raise HumanAdamOperationError("Produkční publisher není dostupný.")
        try:
            document = production_publisher()
        except Exception as exc:  # noqa: BLE001 - backend details stay private.
            raise HumanAdamOperationError(
                "MMTX publikace selhala bezpečně a bez zveřejnění detailu."
            ) from exc
        _validate_mmtx_pages_document(document)
        _assert_redacted_document(document)
        return dict(document)
    if clean_workstream != FAMILY_CALENDAR_WORKSTREAM_ID:
        raise HumanAdamOperationError("Pracovní proud nemá povolenou provozní operaci.")
    try:
        if operation_id == FAMILY_CALENDAR_DRY_RUN_TODAY:
            document = dry_run_runner(today=today_factory()).safe_document()
            _validate_dry_run_document(document)
        elif operation_id == FAMILY_CALENDAR_DRY_RUN_CANDIDATE:
            document = _candidate_dry_run_document(
                today=today_factory(),
                dry_run_runner=dry_run_runner,
            )
            if document.get("status") != "no_candidate":
                _validate_dry_run_document(document, require_candidate=True)
        elif operation_id == FAMILY_CALENDAR_TEST_EMAIL_PREVIEW:
            document = test_email_planner().safe_document()
            _validate_test_email_preview(document)
        else:
            raise HumanAdamOperationError("Požadovaná provozní operace není povolená.")
    except HumanAdamOperationError:
        raise
    except Exception as exc:  # noqa: BLE001 - private details never cross this boundary.
        raise HumanAdamOperationError(
            "Provozní operace selhala bezpečně a bez zveřejnění detailu."
        ) from exc

    _assert_redacted_document(document)
    return dict(document)


def _validate_mmtx_pages_document(document: dict[str, object]) -> None:
    expected_keys = {
        "status",
        "main_short",
        "pushed",
        "commit_count",
        "workflow_run_id",
        "deployment_id",
        "production_url",
        "smoke_http_status",
        "redacted",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise HumanAdamOperationError("MMTX publisher vrátil neplatný doklad.")
    if document.get("status") not in {"deployed", "already_deployed"}:
        raise HumanAdamOperationError("MMTX publisher nepotvrdil produkční stav.")
    if not re.fullmatch(r"[0-9a-f]{12}", str(document.get("main_short") or "")):
        raise HumanAdamOperationError("MMTX publisher nepotvrdil commit.")
    if type(document.get("pushed")) is not bool:
        raise HumanAdamOperationError("MMTX publisher vrátil neplatný stav pushnutí.")
    for key in ("commit_count", "workflow_run_id", "deployment_id"):
        if not _non_negative_int(document.get(key)):
            raise HumanAdamOperationError("MMTX publisher vrátil neplatné ID nebo počet.")
    if document.get("smoke_http_status") != 200 or document.get("redacted") is not True:
        raise HumanAdamOperationError("MMTX publisher neprošel produkčním smoke.")
    if str(document.get("production_url") or "") != "https://belisarius-mila.github.io/PythonMF/":
        raise HumanAdamOperationError("MMTX publisher vrátil neznámý produkční cíl.")


def _candidate_dry_run_document(
    *,
    today: date,
    dry_run_runner: DryRunRunner,
) -> dict[str, object]:
    for offset in range(367):
        result = dry_run_runner(today=today + timedelta(days=offset))
        document = result.safe_document()
        if (
            document.get("status") == "dry_run"
            and _positive_int(document.get("candidate_count"))
            and document.get("eligible_count") == document.get("candidate_count")
            and document.get("coordinator_called") is False
            and document.get("transport_called") is False
        ):
            return dict(document)
    return {"status": "no_candidate", "redacted": True}


def _validate_dry_run_document(
    document: dict[str, object],
    *,
    require_candidate: bool = False,
) -> None:
    if not isinstance(document, dict) or set(document) != _DRY_RUN_KEYS:
        raise HumanAdamOperationError("Dry-run vrátil neplatný redigovaný kontrakt.")
    if document.get("coordinator_called") is not False:
        raise HumanAdamOperationError("Dry-run se pokusil použít koordinátor.")
    if document.get("transport_called") is not False:
        raise HumanAdamOperationError("Dry-run se pokusil použít transport.")
    for key in (
        "candidate_count",
        "d2_count",
        "d1_count",
        "eligible_count",
        "recipient_count",
    ):
        if not _non_negative_int(document.get(key)):
            raise HumanAdamOperationError("Dry-run vrátil neplatný souhrnný počet.")
    if require_candidate and (
        not _positive_int(document.get("candidate_count"))
        or document.get("eligible_count") != document.get("candidate_count")
    ):
        raise HumanAdamOperationError("Dry-run nepotvrdil bezpečného kandidáta.")


def _validate_test_email_preview(document: dict[str, object]) -> None:
    if not isinstance(document, dict) or set(document) != _TEST_EMAIL_PREVIEW_KEYS:
        raise HumanAdamOperationError("Preview e-mailu vrátil neplatný kontrakt.")
    if (
        document.get("status") != "preview"
        or document.get("confirmation_required") is not True
        or document.get("transport_called") is not False
        or not _positive_int(document.get("recipient_count"))
    ):
        raise HumanAdamOperationError("Preview e-mailu nepotvrdil bezpečný stav.")


def _assert_redacted_document(document: dict[str, object]) -> None:
    encoded = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).casefold()
    if any(marker in encoded for marker in _PRIVATE_TEXT_MARKERS):
        raise HumanAdamOperationError("Provozní výsledek neprošel redakční kontrolou.")
    for key, value in document.items():
        if not isinstance(key, str) or not isinstance(value, (str, int, bool)):
            raise HumanAdamOperationError("Provozní výsledek má nepovolený datový typ.")


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _positive_int(value: Any) -> bool:
    return _non_negative_int(value) and value > 0
