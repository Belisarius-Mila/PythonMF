#!/usr/bin/env python3
"""Safe daily 3 AM entry point for Samantha Agent maintenance."""

from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    import fcntl
except ImportError:  # pragma: no cover - this routine is intended for macOS/Linux.
    fcntl = None


EXIT_OK = 0
EXIT_ALREADY_RUNNING = 10
EXIT_SETUP_ERROR = 20
EXIT_TASK_ERROR = 30
EXIT_INVALID_USAGE = 40

PRAGUE_TZ = ZoneInfo("Europe/Prague")
DEFAULT_PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_LOG_FILE = DEFAULT_PROJECT_DIR / "logs" / "daily_3am.log"
DEFAULT_STATE_DIR = DEFAULT_PROJECT_DIR / "data" / "daily_3am"


class AlreadyRunningError(RuntimeError):
    """Raised when the daily routine lock is already held."""


class DailyTaskError(RuntimeError):
    """Raised when a configured daily task fails."""


@dataclass(frozen=True)
class DailyContext:
    project_dir: Path
    log_file: Path
    state_dir: Path
    run_date: str
    started_at: str
    dry_run: bool
    force: bool


class FileLock:
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._handle = None

    def __enter__(self) -> "FileLock":
        if fcntl is None:
            raise DailyTaskError("File locking requires fcntl on macOS/Linux.")

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.lock_path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._handle.close()
            self._handle = None
            raise AlreadyRunningError("Daily 3 AM routine is already running.") from exc

        self._handle.seek(0)
        self._handle.truncate()
        self._handle.write(f"pid={os.getpid()}\nstarted_at={datetime.now(PRAGUE_TZ).isoformat()}\n")
        self._handle.flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._handle is None:
            return
        fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        self._handle.close()
        self._handle = None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Samantha Agent daily 3 AM maintenance.")
    parser.add_argument(
        "--project-dir",
        default=str(DEFAULT_PROJECT_DIR),
        help="Samantha_Agent project directory. Defaults to this script's parent project.",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Log file path. Defaults to <project-dir>/logs/daily_3am.log.",
    )
    parser.add_argument(
        "--state-dir",
        default=None,
        help="Runtime state directory. Defaults to <project-dir>/data/daily_3am.",
    )
    parser.add_argument("--run-date", default=None, help="Override Prague run date as YYYY-MM-DD.")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without marking the day completed.")
    parser.add_argument("--force", action="store_true", help="Run even if today's state is already completed.")
    parser.add_argument(
        "--only-at-hour",
        type=int,
        default=None,
        help="No-op unless current Europe/Prague hour equals this value. Useful for GitHub Actions DST schedules.",
    )
    return parser.parse_args(argv)


def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)


def build_context(args: argparse.Namespace, now: datetime) -> DailyContext:
    project_dir = Path(args.project_dir).expanduser().resolve()
    log_file = Path(args.log_file).expanduser().resolve() if args.log_file else project_dir / "logs" / "daily_3am.log"
    state_dir = (
        Path(args.state_dir).expanduser().resolve()
        if args.state_dir
        else project_dir / "data" / "daily_3am"
    )
    run_date = args.run_date or now.date().isoformat()
    validate_run_date(run_date)
    return DailyContext(
        project_dir=project_dir,
        log_file=log_file,
        state_dir=state_dir,
        run_date=run_date,
        started_at=now.isoformat(),
        dry_run=args.dry_run,
        force=args.force,
    )


def validate_run_date(run_date: str) -> None:
    try:
        datetime.strptime(run_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("--run-date must use YYYY-MM-DD format.") from exc


def state_path(context: DailyContext) -> Path:
    return context.state_dir / f"{context.run_date}.json"


def read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        logging.warning("Ignoring unreadable daily state file: %s", path)
        return {}
    return data if isinstance(data, dict) else {}


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def is_completed(context: DailyContext) -> bool:
    return read_state(state_path(context)).get("status") == "completed"


def mark_running(context: DailyContext) -> None:
    write_state(
        state_path(context),
        {
            "run_date": context.run_date,
            "started_at": context.started_at,
            "status": "running",
            "dry_run": context.dry_run,
        },
    )


def mark_completed(context: DailyContext, result: dict) -> None:
    write_state(
        state_path(context),
        {
            "run_date": context.run_date,
            "started_at": context.started_at,
            "completed_at": datetime.now(PRAGUE_TZ).isoformat(),
            "status": "completed",
            "result": result,
        },
    )


def mark_failed(context: DailyContext, error: str) -> None:
    write_state(
        state_path(context),
        {
            "run_date": context.run_date,
            "started_at": context.started_at,
            "failed_at": datetime.now(PRAGUE_TZ).isoformat(),
            "status": "failed",
            "error": error,
        },
    )


def run_daily_tasks(context: DailyContext) -> dict:
    """Run configured daily work.

    This entry point is intentionally non-destructive for the first version. Concrete
    work such as TTS generation, git commit, or git push should be added here only
    after a dedicated preflight and allowlist are implemented.
    """

    logging.info("Daily 3 AM routine started for %s.", context.run_date)
    logging.info("Project directory: %s", context.project_dir)
    logging.info("Dry run: %s", context.dry_run)
    return {
        "tasks": [
            {
                "name": "daily_3am_skeleton",
                "status": "completed",
                "message": "No destructive daily task is configured yet.",
            }
        ]
    }


def run_once(context: DailyContext) -> int:
    lock_path = context.state_dir / "daily_3am.lock"
    with FileLock(lock_path):
        if is_completed(context) and not context.force:
            logging.info("Daily 3 AM routine already completed for %s; no-op.", context.run_date)
            return EXIT_OK

        if not context.dry_run:
            mark_running(context)

        try:
            result = run_daily_tasks(context)
        except Exception as exc:
            logging.exception("Daily 3 AM routine failed.")
            if not context.dry_run:
                mark_failed(context, str(exc))
            raise DailyTaskError(str(exc)) from exc

        if context.dry_run:
            logging.info("Dry run completed; daily state was not marked completed.")
        else:
            mark_completed(context, result)
            logging.info("Daily 3 AM routine completed for %s.", context.run_date)
        return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else EXIT_INVALID_USAGE

    now = datetime.now(PRAGUE_TZ)
    try:
        context = build_context(args, now)
        setup_logging(context.log_file)
    except Exception as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return EXIT_SETUP_ERROR

    logging.info("Daily 3 AM entry point invoked.")
    if args.only_at_hour is not None and now.hour != args.only_at_hour:
        logging.info(
            "Current Europe/Prague hour is %s, expected %s; no-op.",
            now.hour,
            args.only_at_hour,
        )
        return EXIT_OK

    try:
        return run_once(context)
    except AlreadyRunningError:
        logging.warning("Daily 3 AM routine is already running; exiting.")
        return EXIT_ALREADY_RUNNING
    except DailyTaskError:
        return EXIT_TASK_ERROR
    except Exception:
        logging.exception("Unexpected daily 3 AM setup/runtime error.")
        return EXIT_SETUP_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
