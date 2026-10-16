#!/usr/bin/env python3
"""Private, atomic autosave of a project session; never prints conversation text."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import sys
from datetime import datetime
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.cleanup_session_autosave import apply_cleanup, build_cleanup_plan


def select_source(sessions: Path, project: Path) -> Path | None:
    project = project.resolve()
    candidates = sorted(sessions.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    custom_source = sessions.resolve() != (Path.home() / ".codex/sessions").resolve()
    for candidate in candidates:
        if candidate.is_symlink():
            continue
        try:
            with candidate.open(encoding="utf-8") as handle:
                header = json.loads(handle.readline())
            cwd = header.get("payload", {}).get("cwd")
            if cwd and (Path(cwd).resolve() == project.parent or Path(cwd).resolve().is_relative_to(project)):
                return candidate
            if not cwd and custom_source:
                return candidate
        except (OSError, ValueError, TypeError):
            continue
    return None


def message(record: dict) -> tuple[str, str] | None:
    payload = record.get("payload") or {}
    kind = record.get("type")
    role = ""
    text = ""
    if kind == "event_msg" and payload.get("type") in {"user_message", "agent_message"}:
        if payload.get("phase") == "analysis":
            return None
        role = "USER" if payload["type"] == "user_message" else "ASSISTANT"
        text = str(payload.get("message") or "")
    elif kind == "response_item" and payload.get("type") == "message":
        if payload.get("role") not in {"user", "assistant"} or payload.get("channel") == "analysis":
            return None
        role = payload["role"].upper()
        text = "\n".join(
            str(part.get("text") or "") for part in payload.get("content", [])
            if isinstance(part, dict) and part.get("type") in {"input_text", "output_text", "text"}
        )
    return (role, text.strip()) if text.strip() else None


def _temporary(directory: Path):
    handle = tempfile.NamedTemporaryFile(dir=directory, prefix=".saving-", delete=False)
    os.chmod(handle.name, 0o600)
    return handle


def _attempt(output: Path, ok: bool, error: str = "") -> None:
    if not output.is_dir():
        return
    staged = _temporary(output)
    with staged:
        staged.write(json.dumps({"ok": ok, "error": error,
                                 "at": datetime.now().astimezone().isoformat()}).encode())
        staged.flush()
        os.fsync(staged.fileno())
    os.replace(staged.name, output / "last_attempt.json")


def _preserve_previous(output: Path) -> None:
    marker = output / "last_attempt.json"
    if marker.exists():
        try:
            if not json.loads(marker.read_text()).get("ok"):
                return
        except (OSError, ValueError, TypeError):
            return
    for name in ("latest_session.jsonl", "latest_session.txt", "latest_info.txt"):
        previous = output / name
        if previous.is_file() and not previous.is_symlink():
            link = output / (".previous-" + uuid4().hex)
            os.link(previous, link)
            os.replace(link, output / name.replace("latest_", "previous_", 1))


def save_snapshot(*, project: Path, sessions: Path, output: Path, history_seconds: int = 3600,
                  keep: int = 12, automatic_cleanup: bool = False) -> bool:
    project = project.resolve()
    source = select_source(sessions, project)
    if source is None:
        # Do not make an old successful autosave look fresh when no source exists.
        _attempt(output, False, "source_unavailable")
        return False
    if output.is_symlink():
        raise ValueError("Autosave output must not be a symlink")
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output, 0o700)
    now = datetime.now().astimezone()
    raw = _temporary(output)
    text = _temporary(output)
    count = 0
    previous = None
    try:
        with raw, text, source.open("rb") as original:
            text.write(("Samantha/Codex autosave TXT\nSaved at: " + now.isoformat() +
                        "\nSoukroma nouzova obnova; necommitovat.\n\n").encode())
            remaining = os.fstat(original.fileno()).st_size
            while remaining > 0:
                line = original.readline(remaining)
                remaining -= len(line)
                if not line or not line.endswith(b"\n"):
                    break
                raw.write(line)
                try:
                    record = json.loads(line)
                    item = message(record)
                except (ValueError, TypeError, AttributeError):
                    continue
                if item and item != previous:
                    timestamp = str(record.get("timestamp") or "")
                    text.write(f"[{timestamp}] {item[0]}:\n{item[1]}\n\n".encode())
                    count += 1
                    previous = item
            raw.flush()
            text.flush()
            os.fsync(raw.fileno())
            os.fsync(text.fileno())
        if Path(raw.name).stat().st_size == 0:
            _attempt(output, False, "no_complete_record")
            return False
        histories = list(output.glob("session_????????_??????.jsonl"))
        due = not histories or time.time() - max(p.stat().st_mtime for p in histories) >= history_seconds
        if due:
            stamp = now.strftime("%Y%m%d_%H%M%S")
            # Exclusive creation: never overwrite an older historical snapshot.
            for staged, suffix in ((raw.name, "jsonl"), (text.name, "txt")):
                with Path(staged).open("rb") as src, (output / f"session_{stamp}.{suffix}").open("xb") as dst:
                    os.chmod(dst.name, 0o600)
                    shutil.copyfileobj(src, dst)
                    dst.flush()
                    os.fsync(dst.fileno())
        _preserve_previous(output)
        os.replace(raw.name, output / "latest_session.jsonl")
        os.replace(text.name, output / "latest_session.txt")
        retention = "vypnuta, stare kopie zachovany"
        if automatic_cleanup:
            plan = build_cleanup_plan(autosave_dir=output, retention_days=0, keep_latest_snapshots=keep)
            # apply_cleanup accepts project-relative or absolute plan paths.
            apply_cleanup(plan)
            retention = "ok"
        info = _temporary(output)
        with info:
            info.write((f"Saved at: {now.isoformat()}\nSource: {source}\n"
                        f"Historicky snapshot: {'nova kopie' if due else 'bez nove kopie (hodinovy interval)'}\n"
                        f"Historicky interval: {history_seconds} sekund\n"
                        f"Automaticka retence: ponechat {keep} nejnovejsich casu ({retention})\n"
                        f"Citelne zpravy: {count}\n").encode())
            info.flush()
            os.fsync(info.fileno())
        os.replace(info.name, output / "latest_info.txt")
        _attempt(output, True)
        return True
    except Exception as exc:
        try:
            _attempt(output, False, type(exc).__name__)
        except OSError:
            pass
        raise
    finally:
        # Remove only our incomplete staging files, never user snapshots.
        for staged in (raw.name, text.name):
            if Path(staged).exists():
                Path(staged).unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--sessions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--history-seconds", type=int, default=3600)
    parser.add_argument("--keep", type=int, default=12)
    parser.add_argument("--automatic-cleanup", action="store_true")
    args = parser.parse_args()
    try:
        saved = save_snapshot(project=args.project, sessions=args.sessions, output=args.output,
                              history_seconds=max(1, args.history_seconds), keep=max(1, args.keep),
                              automatic_cleanup=args.automatic_cleanup)
    except Exception as exc:
        print("Autosave failed: " + type(exc).__name__)
        return 1
    if not saved:
        print("Autosave: no complete project session available")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
