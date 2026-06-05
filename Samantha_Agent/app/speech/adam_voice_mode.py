from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.speech.report import speak_report
from app.speech.voice_inbox import (
    VOICE_COMMAND_INBOX_DIR,
    VoiceCommand,
    format_voice_command_for_adam,
    latest_voice_command_signature,
    voice_command_to_dict,
    wait_for_latest_voice_command,
)


ADAM_VOICE_MODE_STATUS_PATH = VOICE_COMMAND_INBOX_DIR / "adam_voice_mode_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def write_voice_mode_status(
    *,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    state: str,
    message: str,
    last_command: VoiceCommand | None = None,
    pid: int | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ok": True,
        "state": state,
        "message": message,
        "pid": pid if pid is not None else os.getpid(),
        "started_at": started_at or utc_now(),
        "updated_at": utc_now(),
    }
    if last_command is not None:
        payload["last_command"] = voice_command_to_dict(last_command)
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_voice_mode_status(
    *,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    stale_after_seconds: float = 15.0,
) -> dict[str, Any]:
    if not status_path.exists():
        return {
            "ok": True,
            "running": False,
            "state": "stopped",
            "message": "Adam Voice Mode watcher neběží.",
            "status_path": str(status_path),
        }
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "running": False,
            "state": "unknown",
            "message": f"Stav Adam Voice Mode nejde načíst: {exc}",
            "status_path": str(status_path),
        }

    pid = int(payload.get("pid") or 0)
    updated_at = str(payload.get("updated_at") or "")
    age_seconds: float | None = None
    if updated_at:
        try:
            updated = datetime.fromisoformat(updated_at)
            age_seconds = max(0.0, (datetime.now(timezone.utc) - updated).total_seconds())
        except ValueError:
            age_seconds = None
    running = pid_exists(pid) and (age_seconds is None or age_seconds <= stale_after_seconds)
    payload["running"] = running
    payload["stale"] = not running
    payload["age_seconds"] = age_seconds
    payload["status_path"] = str(status_path)
    if not running and payload.get("state") == "listening":
        payload["state"] = "stale"
        payload["message"] = "Adam Voice Mode watcher pravděpodobně neběží nebo se dlouho neozval."
    return payload


def spoken_notice_for_command(command: VoiceCommand) -> str:
    triage = command.triage
    text = command.text.strip()
    if triage.risk in {"blocked", "needs_confirmation"}:
        return (
            "Nový hlasový pokyn vyžaduje potvrzení. "
            f"Riziko: {triage.risk}. "
            f"Text pokynu: {text}"
        )
    if triage.risk == "draft":
        return f"Nový hlasový pokyn je návrh bez přímé akce. Text pokynu: {text}"
    if triage.risk == "read_only":
        return f"Nový hlasový pokyn je bezpečný pro čtení. Text pokynu: {text}"
    return f"Nový hlasový pokyn byl přijat. Text pokynu: {text or 'bez textu'}"


def handle_voice_command(
    command: VoiceCommand,
    *,
    speak: Callable[..., dict[str, Any]] = speak_report,
    should_speak: bool = True,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    started_at: str | None = None,
) -> dict[str, Any]:
    notice = spoken_notice_for_command(command)
    speech_result = {"ok": True, "message": "Hlasové oznámení vypnuté.", "transport": "disabled"}
    if should_speak:
        speech_result = speak(notice, allow_local_fallback=False)
    state = "command_ready" if command.ok else "waiting"
    status = write_voice_mode_status(
        status_path=status_path,
        state=state,
        message=notice,
        last_command=command,
        started_at=started_at,
    )
    return {
        "ok": command.ok,
        "status": status,
        "speech": speech_result,
        "command": voice_command_to_dict(command),
        "notice": notice,
    }


def run_voice_mode(
    *,
    inbox_dir: Path = VOICE_COMMAND_INBOX_DIR,
    status_path: Path = ADAM_VOICE_MODE_STATUS_PATH,
    since_now: bool = True,
    timeout_seconds: float = 0.0,
    poll_seconds: float = 1.0,
    count: int = 0,
    should_speak: bool = True,
    printer: Callable[[str], None] = print,
) -> int:
    started_at = utc_now()
    seen = 0
    since_signature = latest_voice_command_signature(inbox_dir=inbox_dir) if since_now else None
    deadline = time.monotonic() + timeout_seconds if timeout_seconds > 0 else None
    write_voice_mode_status(
        status_path=status_path,
        state="listening",
        message="Adam Voice Mode poslouchá nové hlasové pokyny.",
        started_at=started_at,
    )
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                write_voice_mode_status(
                    status_path=status_path,
                    state="timeout",
                    message="Adam Voice Mode doběhl bez nového hlasového pokynu.",
                    started_at=started_at,
                )
                return 0
            command = wait_for_latest_voice_command(
                inbox_dir=inbox_dir,
                timeout_seconds=poll_seconds,
                poll_seconds=min(max(0.1, poll_seconds), 1.0),
                since_signature=since_signature,
            )
            if not command.ok and command.status == "timeout":
                write_voice_mode_status(
                    status_path=status_path,
                    state="listening",
                    message="Adam Voice Mode poslouchá nové hlasové pokyny.",
                    started_at=started_at,
                )
                continue
            since_signature = latest_voice_command_signature(inbox_dir=inbox_dir)
            result = handle_voice_command(
                command,
                should_speak=should_speak,
                status_path=status_path,
                started_at=started_at,
            )
            printer(format_voice_command_for_adam(command))
            printer("")
            printer("ADAM VOICE MODE NOTICE:")
            printer(result["notice"])
            printer("")
            seen += 1
            if count > 0 and seen >= count:
                write_voice_mode_status(
                    status_path=status_path,
                    state="completed",
                    message=f"Adam Voice Mode zpracoval {seen} hlasových pokynů.",
                    last_command=command,
                    started_at=started_at,
                )
                return 0
    except KeyboardInterrupt:
        write_voice_mode_status(
            status_path=status_path,
            state="stopped",
            message="Adam Voice Mode byl zastaven uživatelem.",
            started_at=started_at,
        )
        return 130


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aktivní Adam Voice Mode watcher pro hlasový inbox.")
    parser.add_argument("--inbox-dir", type=Path, default=VOICE_COMMAND_INBOX_DIR)
    parser.add_argument("--status-path", type=Path, default=ADAM_VOICE_MODE_STATUS_PATH)
    parser.add_argument("--since-now", action="store_true", default=True, help="Ignorovat existující latest pokyn a čekat na nový.")
    parser.add_argument("--include-existing", action="store_true", help="Zpracovat i aktuální latest pokyn.")
    parser.add_argument("--timeout", type=float, default=0.0, help="Celkový timeout v sekundách. 0 znamená bez limitu.")
    parser.add_argument("--poll", type=float, default=1.0, help="Interval kontroly v sekundách.")
    parser.add_argument("--count", type=int, default=0, help="Počet nových pokynů před ukončením. 0 znamená bez limitu.")
    parser.add_argument("--no-speak", action="store_true", help="Nevyslovovat oznámení nahlas.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    return run_voice_mode(
        inbox_dir=args.inbox_dir,
        status_path=args.status_path,
        since_now=not args.include_existing,
        timeout_seconds=args.timeout,
        poll_seconds=args.poll,
        count=args.count,
        should_speak=not args.no_speak,
    )


if __name__ == "__main__":
    raise SystemExit(main())
