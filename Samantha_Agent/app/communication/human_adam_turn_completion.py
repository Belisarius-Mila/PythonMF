"""Private completion receipt for one successful Human–Adam development turn.

The receipt is carried at the end of the model answer, removed before the
answer is shown to the user and used only as structured input for the existing
direct-main checkpoint backend.  Missing or malformed metadata never triggers
a Git operation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


COMPLETION_MARKER_START = "[HUMAN_ADAM_STEP_COMPLETION]"
COMPLETION_MARKER_END = "[/HUMAN_ADAM_STEP_COMPLETION]"
_SENSITIVE_TEXT_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token|token|password|heslo|app-specific password)\b\s*[:=]\s*\S+"
)


@dataclass(frozen=True)
class TurnCompletionMetadata:
    commit_message: str
    summary: str
    next_step: str
    decision: str = ""
    proposed_next_steps: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedTurnCompletion:
    state: str
    visible_answer: str
    metadata: TurnCompletionMetadata | None = None
    error: str = ""


def automatic_completion_instruction(
    *,
    writable: bool,
    integration_deferred: bool = False,
) -> str:
    """Return a private model protocol only for an authorized writable turn."""

    if not writable:
        return ""
    example = json.dumps(
        {
            "commit_message": "Complete one development step",
            "summary": "Nový TVBCP zápis zvýrazňuje výsledek a další plán",
            "decision": "Technické důkazy budou až v poslední stručné sekci",
            "next_step": "Ověřit výsledek nebo pokračovat dalším krokem",
            "proposed_next_steps": [
                "Po živém ověření použít stejný formát i v dalším projektu"
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    rules = [
            "[AUTOMATIC_STEP_COMPLETION]",
            "enabled=true",
            "rule=Use the receipt only after you changed files successfully and relevant tests passed.",
            "rule=Do not create a Git commit, push, handoff entry or TVBCP entry yourself.",
            "rule=If work is incomplete or tests failed, do not emit the receipt.",
            "rule=Write summary as a short user-visible outcome, not as a commit or test report.",
            "rule=Put only a genuinely agreed canonical decision into decision; otherwise use an empty string.",
            "rule=Preserve useful future plans from the conversation in proposed_next_steps; use an empty list when none exist.",
            f"receipt_start={COMPLETION_MARKER_START}",
            f"receipt_json_example={example}",
            f"receipt_end={COMPLETION_MARKER_END}",
            "rule=The receipt must be the final block, contain one JSON object and no secrets or private content.",
    ]
    if integration_deferred:
        rules.extend(
            (
                "rule=Integration is deferred. Emit metadata only; leave all changes "
                "uncommitted and do not run any Git or deployment action.",
                "rule=The private owner marker may use only this redacted receipt, "
                "the base commit and a digest of path-level changes.",
            )
        )
    rules.append("[/AUTOMATIC_STEP_COMPLETION]")
    return "\n".join(rules)


def _safe_field(value: object, *, label: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise ValueError(f"Chybí {label} automatického dokončení.")
    if len(text) > limit:
        raise ValueError(f"{label.capitalize()} automatického dokončení je příliš dlouhý.")
    if _SENSITIVE_TEXT_RE.search(text) or "-----BEGIN PRIVATE KEY-----" in text.upper():
        raise ValueError("Automatická účtenka nesmí obsahovat heslo, token ani klíč.")
    return text


def _safe_optional_field(value: object, *, label: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    return _safe_field(text, label=label, limit=limit)


def _safe_proposed_next_steps(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("Navrhované další kroky automatického dokončení musí být seznam.")
    if len(value) > 4:
        raise ValueError("Automatická účtenka smí obsahovat nejvýše čtyři navrhované kroky.")
    return tuple(
        _safe_field(item, label="navrhovaný další krok", limit=300)
        for item in value
    )


def parse_turn_completion(answer: object) -> ParsedTurnCompletion:
    """Parse one final receipt and return an answer safe for display."""

    text = str(answer or "").strip()
    start_count = text.count(COMPLETION_MARKER_START)
    end_count = text.count(COMPLETION_MARKER_END)
    if start_count == 0 and end_count == 0:
        return ParsedTurnCompletion(state="absent", visible_answer=text)

    start_index = text.find(COMPLETION_MARKER_START)
    visible = (
        text[:start_index].rstrip()
        if start_index >= 0
        else text.replace(COMPLETION_MARKER_END, "").strip()
    )
    if start_count != 1 or end_count != 1 or start_index < 0:
        return ParsedTurnCompletion(
            state="invalid",
            visible_answer=visible,
            error="Automatická účtenka má neplatné nebo opakované značky.",
        )
    end_index = text.find(COMPLETION_MARKER_END, start_index + len(COMPLETION_MARKER_START))
    if end_index < 0 or text[end_index + len(COMPLETION_MARKER_END) :].strip():
        return ParsedTurnCompletion(
            state="invalid",
            visible_answer=visible,
            error="Automatická účtenka musí být posledním blokem odpovědi.",
        )
    payload_text = text[
        start_index + len(COMPLETION_MARKER_START) : end_index
    ].strip()
    try:
        payload = json.loads(payload_text)
        legacy_fields = {
            "commit_message",
            "summary",
            "next_step",
        }
        current_fields = legacy_fields | {"decision", "proposed_next_steps"}
        payload_fields = frozenset(payload) if isinstance(payload, dict) else frozenset()
        if not isinstance(payload, dict) or payload_fields not in {
            frozenset(legacy_fields),
            frozenset(current_fields),
        }:
            raise ValueError("Automatická účtenka nemá přesně povolená pole.")
        metadata = TurnCompletionMetadata(
            commit_message=_safe_field(
                payload.get("commit_message"),
                label="název commitu",
                limit=120,
            ),
            summary=_safe_field(payload.get("summary"), label="souhrn", limit=400),
            next_step=_safe_field(
                payload.get("next_step"),
                label="další krok",
                limit=500,
            ),
            decision=_safe_optional_field(
                payload.get("decision"),
                label="rozhodnutí",
                limit=400,
            ),
            proposed_next_steps=_safe_proposed_next_steps(
                payload.get("proposed_next_steps")
            ),
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return ParsedTurnCompletion(
            state="invalid",
            visible_answer=visible,
            error=str(exc) or "Automatická účtenka není platná.",
        )
    if not visible:
        return ParsedTurnCompletion(
            state="invalid",
            visible_answer="",
            error="Odpověď před automatickou účtenkou je prázdná.",
        )
    return ParsedTurnCompletion(
        state="valid",
        visible_answer=visible,
        metadata=metadata,
    )
