"""Durable fail-closed ownership for Samantha development work."""

from __future__ import annotations

import json
import re
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.codex_appserver import AppServerError
from app.file_persistence import (
    FilePersistenceError,
    atomic_replace_text_under_external_lock,
    exclusive_file_lock,
)


DEVELOPMENT_SEMAPHORE_SCHEMA = 1
DEVELOPMENT_OWNER_RE = re.compile(r"[a-z][a-z0-9_-]{1,31}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
VALID_MODES = {"active", "paused"}
TERMINAL_OWNER_ID = "terminal"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DevelopmentSemaphore:
    """Persist one development owner without silently expiring or overriding it."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.RLock()

    @staticmethod
    def _free_state(*, revision: int = 0) -> dict[str, Any]:
        return {
            "schema_version": DEVELOPMENT_SEMAPHORE_SCHEMA,
            "revision": revision,
            "active": False,
            "mode": "free",
            "owner_id": "",
            "owner_label": "",
            "workspace_label": "",
            "base_head": "",
            "topic": "",
            "acquired_at": "",
            "updated_at": "",
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._free_state()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AppServerError("Vývojový semafor nelze bezpečně načíst.") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != DEVELOPMENT_SEMAPHORE_SCHEMA:
            raise AppServerError("Vývojový semafor má neznámé schéma.")
        try:
            revision = int(raw.get("revision"))
        except (TypeError, ValueError) as exc:
            raise AppServerError("Vývojový semafor nemá platnou revizi.") from exc
        if revision < 0:
            raise AppServerError("Vývojový semafor nemá platnou revizi.")
        active = raw.get("active") is True
        if not active:
            return self._free_state(revision=revision)
        owner_id = str(raw.get("owner_id") or "").strip()
        owner_label = " ".join(str(raw.get("owner_label") or "").split())[:80]
        workspace_label = " ".join(str(raw.get("workspace_label") or "").split())[:120]
        mode = str(raw.get("mode") or "").strip()
        base_head = str(raw.get("base_head") or "").strip().lower()
        topic = " ".join(str(raw.get("topic") or "").split())[:120]
        acquired_at = str(raw.get("acquired_at") or "").strip()
        updated_at = str(raw.get("updated_at") or "").strip()
        if (
            not DEVELOPMENT_OWNER_RE.fullmatch(owner_id)
            or not owner_label
            or not workspace_label
            or mode not in VALID_MODES
            or not COMMIT_RE.fullmatch(base_head)
            or not acquired_at
            or not updated_at
        ):
            raise AppServerError("Vývojový semafor obsahuje neplatný aktivní lease.")
        return {
            "schema_version": DEVELOPMENT_SEMAPHORE_SCHEMA,
            "revision": revision,
            "active": True,
            "mode": mode,
            "owner_id": owner_id,
            "owner_label": owner_label,
            "workspace_label": workspace_label,
            "base_head": base_head,
            "topic": topic,
            "acquired_at": acquired_at,
            "updated_at": updated_at,
        }

    @staticmethod
    def _public(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "revision": int(state.get("revision") or 0),
            "active": state.get("active") is True,
            "mode": str(state.get("mode") or "free"),
            "owner_id": str(state.get("owner_id") or ""),
            "owner_label": str(state.get("owner_label") or ""),
            "workspace_label": str(state.get("workspace_label") or ""),
            "base_head_short": str(state.get("base_head") or "")[:12],
            "topic": str(state.get("topic") or ""),
            "acquired_at": str(state.get("acquired_at") or ""),
            "updated_at": str(state.get("updated_at") or ""),
        }

    def status(self) -> dict[str, Any]:
        with self._lock:
            try:
                return self._public(self._load())
            except AppServerError as exc:
                return {
                    "ok": False,
                    "revision": -1,
                    "active": True,
                    "mode": "invalid",
                    "owner_id": "unknown",
                    "owner_label": "Neznámý vlastník",
                    "workspace_label": "Neověřený stav",
                    "base_head_short": "",
                    "topic": "",
                    "acquired_at": "",
                    "updated_at": "",
                    "message": str(exc),
                }

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        try:
            with self._lock, exclusive_file_lock(self.path):
                yield
        except FilePersistenceError as exc:
            raise AppServerError("Vývojový semafor nelze bezpečně zamknout nebo uložit.") from exc

    @staticmethod
    def _assert_revision(state: dict[str, Any], expected_revision: int) -> None:
        if expected_revision != int(state.get("revision") or 0):
            raise AppServerError("Vývojový semafor se mezitím změnil; obnov jeho stav.")

    def _write_locked(self, state: dict[str, Any]) -> dict[str, Any]:
        atomic_replace_text_under_external_lock(
            self.path,
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        )
        return self._public(state)

    def acquire(
        self,
        *,
        owner_id: str,
        owner_label: str,
        workspace_label: str,
        base_head: str,
        topic: str,
        expected_revision: int,
        confirmed: bool,
    ) -> dict[str, Any]:
        if not confirmed:
            raise AppServerError("Převzetí vývojového semaforu vyžaduje výslovné potvrzení.")
        clean_owner = str(owner_id or "").strip()
        clean_owner_label = " ".join(str(owner_label or "").split())[:80]
        clean_workspace = " ".join(str(workspace_label or "").split())[:120]
        clean_head = str(base_head or "").strip().lower()
        clean_topic = " ".join(str(topic or "").split())[:120]
        if not DEVELOPMENT_OWNER_RE.fullmatch(clean_owner):
            raise AppServerError("Vývojový semafor nemá platného vlastníka.")
        if not clean_owner_label or not clean_workspace or not COMMIT_RE.fullmatch(clean_head):
            raise AppServerError("Vývojový semafor nemá úplný ověřený základ.")
        if not clean_topic:
            raise AppServerError("Zadej krátké téma vývoje.")
        with self._transaction():
            current = self._load()
            self._assert_revision(current, expected_revision)
            if current.get("active"):
                if current.get("owner_id") != clean_owner:
                    raise AppServerError(
                        f"Vývoj už vlastní {current.get('owner_label')}; cizí lease nelze přepsat."
                    )
                if current.get("mode") == "active":
                    return {**self._public(current), "changed": False}
            now = _now()
            acquired_at = str(current.get("acquired_at") or now) if current.get("active") else now
            state = {
                "schema_version": DEVELOPMENT_SEMAPHORE_SCHEMA,
                "revision": int(current.get("revision") or 0) + 1,
                "active": True,
                "mode": "active",
                "owner_id": clean_owner,
                "owner_label": clean_owner_label,
                "workspace_label": clean_workspace,
                "base_head": clean_head,
                "topic": clean_topic,
                "acquired_at": acquired_at,
                "updated_at": now,
            }
            return {**self._write_locked(state), "changed": True}

    def set_mode(
        self,
        *,
        owner_id: str,
        mode: str,
        expected_revision: int,
        confirmed: bool,
    ) -> dict[str, Any]:
        if not confirmed:
            raise AppServerError("Změna vývojového semaforu vyžaduje výslovné potvrzení.")
        clean_mode = str(mode or "").strip()
        if clean_mode not in VALID_MODES:
            raise AppServerError("Vývojový semafor nepodporuje požadovaný režim.")
        with self._transaction():
            current = self._load()
            self._assert_revision(current, expected_revision)
            if not current.get("active") or current.get("owner_id") != str(owner_id or "").strip():
                raise AppServerError("Vývojový semafor nevlastní požadovaný vlastník.")
            if current.get("mode") == clean_mode:
                return {**self._public(current), "changed": False}
            current.update(
                {
                    "revision": int(current["revision"]) + 1,
                    "mode": clean_mode,
                    "updated_at": _now(),
                }
            )
            return {**self._write_locked(current), "changed": True}

    def release(
        self,
        *,
        owner_id: str,
        expected_revision: int,
        confirmed: bool,
        safe_to_release: bool,
    ) -> dict[str, Any]:
        if not confirmed:
            raise AppServerError("Uvolnění vývojového semaforu vyžaduje výslovné potvrzení.")
        with self._transaction():
            current = self._load()
            self._assert_revision(current, expected_revision)
            if not current.get("active") or current.get("owner_id") != str(owner_id or "").strip():
                raise AppServerError("Vývojový semafor nevlastní požadovaný vlastník.")
            if not safe_to_release:
                raise AppServerError(
                    "Vývojový semafor nelze uvolnit, dokud existuje neuzavřený WIP nebo nečistý workspace."
                )
            state = self._free_state(revision=int(current["revision"]) + 1)
            state["updated_at"] = _now()
            return {**self._write_locked(state), "changed": True}

    def assert_owner(self, owner_id: str) -> dict[str, Any]:
        with self._lock:
            current = self._load()
            if not current.get("active"):
                raise AppServerError("Nejdřív převezmi globální vývojový semafor.")
            if current.get("owner_id") != str(owner_id or "").strip():
                raise AppServerError(
                    f"Vývoj vlastní {current.get('owner_label')}; tato operace je pro jiný workspace zablokovaná."
                )
            if current.get("mode") != "active":
                raise AppServerError("Vývojový semafor je pozastavený; nejdřív jej obnov.")
            return self._public(current)
