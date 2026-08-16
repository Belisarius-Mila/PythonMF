"""Strict local evidence reader for an ambiguously delivered Codex turn."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}")
MAX_RECOVERED_ANSWER_CHARS = 200_000


class CodexDeliveryRecoveryError(RuntimeError):
    """Raised when local completion evidence is absent or ambiguous."""


@dataclass(frozen=True)
class CodexDeliveryEvidence:
    thread_id: str
    client_message_id: str
    turn_id: str
    completed_at: str
    answer: str
    source_path: Path


def default_codex_sessions_root() -> Path:
    configured = str(os.environ.get("SAMANTHA_CODEX_SESSIONS_DIR") or "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".codex" / "sessions"


def _clean_id(value: object, *, label: str) -> str:
    clean = str(value or "").strip()
    if not SAFE_ID_RE.fullmatch(clean):
        raise CodexDeliveryRecoveryError(f"{label} nemá bezpečný formát.")
    return clean


def _candidate_rollout(*, sessions_root: Path, thread_id: str) -> Path:
    root = Path(sessions_root).expanduser().resolve()
    if not root.is_dir():
        raise CodexDeliveryRecoveryError("Lokální adresář Codex relací není dostupný.")
    candidates = [
        path
        for path in root.rglob("rollout-*.jsonl")
        if path.is_file() and path.stem.endswith(thread_id)
    ]
    if len(candidates) != 1:
        raise CodexDeliveryRecoveryError(
            "Dokončení nelze doložit právě jedním lokálním záznamem Codex relace."
        )
    return candidates[0]


def read_completed_delivery_evidence(
    *,
    sessions_root: Path,
    thread_id: str,
    client_message_id: str,
) -> CodexDeliveryEvidence:
    """Return strict completion evidence without retrying or mutating the session."""

    clean_thread_id = _clean_id(thread_id, label="ID vlákna")
    clean_client_id = _clean_id(client_message_id, label="Client message ID")
    source_path = _candidate_rollout(
        sessions_root=sessions_root,
        thread_id=clean_thread_id,
    )

    matched_user_count = 0
    final_answer = ""
    completion: dict[str, Any] | None = None
    conflicting_tail_event = False
    try:
        with source_path.open("r", encoding="utf-8", errors="replace") as source:
            for line in source:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(item, dict) or item.get("type") != "event_msg":
                    continue
                payload = item.get("payload")
                if not isinstance(payload, dict):
                    continue
                event_type = str(payload.get("type") or "")
                if event_type == "user_message" and payload.get("client_id") == clean_client_id:
                    matched_user_count += 1
                    if matched_user_count > 1 or completion is not None:
                        conflicting_tail_event = True
                    continue
                if matched_user_count != 1:
                    continue
                if completion is not None and event_type in {
                    "user_message",
                    "task_complete",
                    "turn_aborted",
                }:
                    conflicting_tail_event = True
                    continue
                if event_type == "user_message":
                    conflicting_tail_event = True
                elif event_type == "turn_aborted":
                    conflicting_tail_event = True
                elif event_type == "agent_message" and payload.get("phase") == "final_answer":
                    candidate = str(payload.get("message") or "").strip()
                    if final_answer and candidate != final_answer:
                        conflicting_tail_event = True
                    final_answer = candidate
                elif event_type == "task_complete":
                    if completion is not None:
                        conflicting_tail_event = True
                    completion = dict(payload)
    except OSError as exc:
        raise CodexDeliveryRecoveryError(
            "Lokální záznam Codex relace nelze bezpečně přečíst."
        ) from exc

    if matched_user_count != 1 or completion is None or conflicting_tail_event:
        raise CodexDeliveryRecoveryError("Lokální důkaz dokončení je neúplný nebo nejednoznačný.")
    recovered_answer = str(completion.get("last_agent_message") or "").strip()
    if not final_answer or recovered_answer != final_answer:
        raise CodexDeliveryRecoveryError("Finální odpověď a doklad dokončení se neshodují.")
    if len(recovered_answer) > MAX_RECOVERED_ANSWER_CHARS:
        raise CodexDeliveryRecoveryError("Obnovená odpověď překračuje bezpečný limit.")
    turn_id = _clean_id(completion.get("turn_id"), label="ID dokončeného tahu")
    completed_at = str(completion.get("completed_at") or "").strip()
    if not completed_at:
        raise CodexDeliveryRecoveryError("Dokladu dokončení chybí čas dokončení.")
    return CodexDeliveryEvidence(
        thread_id=clean_thread_id,
        client_message_id=clean_client_id,
        turn_id=turn_id,
        completed_at=completed_at,
        answer=recovered_answer,
        source_path=source_path,
    )
