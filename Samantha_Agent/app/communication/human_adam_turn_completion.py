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


@dataclass(frozen=True)
class ParsedTurnCompletion:
    state: str
    visible_answer: str
    metadata: TurnCompletionMetadata | None = None
    error: str = ""


def automatic_completion_instruction(*, writable: bool) -> str:
    """Return a private model protocol only for an authorized writable turn."""

    if not writable:
        return ""
    example = json.dumps(
        {
            "commit_message": "Complete one development step",
            "summary": "Dokončen jeden malý vývojový krok",
            "next_step": "Ověřit výsledek nebo pokračovat dalším krokem",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return "\n".join(
        (
            "[AUTOMATIC_STEP_COMPLETION]",
            "enabled=true",
            "rule=Use the receipt only after you changed files successfully and relevant tests passed.",
            "rule=Do not create a Git commit, push, handoff entry or TVBCP entry yourself.",
            "rule=If work is incomplete or tests failed, do not emit the receipt.",
            f"receipt_start={COMPLETION_MARKER_START}",
            f"receipt_json_example={example}",
            f"receipt_end={COMPLETION_MARKER_END}",
            "rule=The receipt must be the final block, contain one JSON object and no secrets or private content.",
            "[/AUTOMATIC_STEP_COMPLETION]",
        )
    )


def _safe_field(value: object, *, label: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise ValueError(f"Chybí {label} automatického dokončení.")
    if len(text) > limit:
        raise ValueError(f"{label.capitalize()} automatického dokončení je příliš dlouhý.")
    if _SENSITIVE_TEXT_RE.search(text) or "-----BEGIN PRIVATE KEY-----" in text.upper():
        raise ValueError("Automatická účtenka nesmí obsahovat heslo, token ani klíč.")
    return text


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
        if not isinstance(payload, dict) or set(payload) != {
            "commit_message",
            "summary",
            "next_step",
        }:
            raise ValueError("Automatická účtenka nemá přesně tři povolená pole.")
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
