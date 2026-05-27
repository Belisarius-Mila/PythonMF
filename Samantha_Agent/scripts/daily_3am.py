#!/usr/bin/env python3
"""Safe daily 3 AM entry point for Samantha Agent maintenance."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
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
DEFAULT_COLORS_NUMBERS_OWL_CONFIG = DEFAULT_PROJECT_DIR / "config" / "colors_numbers_owl_current.json"
DEFAULT_COLORS_NUMBERS_OWL_SPEECH_CSV = DEFAULT_PROJECT_DIR / "config" / "OwlSpeech.csv"
COLORS_NUMBERS_APP_DIR = Path("ColorsAndNumbers") / "web_colors_numbers"
DOCS_COLORS_NUMBERS_APP_DIR = Path("docs") / "colors-numbers"
COLORS_NUMBERS_ALLOWED_DIRS = (COLORS_NUMBERS_APP_DIR, DOCS_COLORS_NUMBERS_APP_DIR)
COLORS_NUMBERS_DEFAULT_OWL_VOICE = "cs-CZ-AntoninNeural"
COLORS_NUMBERS_DEFAULT_OWL_RATE = "-10%"


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
    parser.add_argument(
        "--window-start-hour",
        type=int,
        default=None,
        help="No-op unless current Europe/Prague time is inside a window starting at this hour.",
    )
    parser.add_argument(
        "--window-hours",
        type=int,
        default=None,
        help="Number of hours in the allowed window started by --window-start-hour.",
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


def validate_time_gate_args(args: argparse.Namespace) -> None:
    if args.only_at_hour is not None and not 0 <= args.only_at_hour <= 23:
        raise ValueError("--only-at-hour must be between 0 and 23.")

    has_window_start = args.window_start_hour is not None
    has_window_hours = args.window_hours is not None
    if has_window_start != has_window_hours:
        raise ValueError("--window-start-hour and --window-hours must be used together.")
    if args.only_at_hour is not None and has_window_start:
        raise ValueError("--only-at-hour cannot be combined with --window-start-hour.")
    if has_window_start and not 0 <= args.window_start_hour <= 23:
        raise ValueError("--window-start-hour must be between 0 and 23.")
    if has_window_hours and not 1 <= args.window_hours <= 24:
        raise ValueError("--window-hours must be between 1 and 24.")


def is_within_hour_window(now: datetime, start_hour: int, window_hours: int) -> bool:
    start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if now < start:
        start -= timedelta(days=1)
    end = start + timedelta(hours=window_hours)
    return start <= now <= end


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


def read_json_file(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise DailyTaskError(f"Cannot read task config: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DailyTaskError(f"Task config is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise DailyTaskError(f"Task config must contain a JSON object: {path}")
    return data


def require_text_field(data: dict, field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DailyTaskError(f"Task config is missing required text field: {field}")
    return value.strip()


def resolve_repo_path(project_dir: Path, relative_path: str) -> Path:
    return (project_dir / relative_path).resolve()


def ensure_under(path: Path, allowed_root: Path) -> None:
    try:
        path.relative_to(allowed_root)
    except ValueError as exc:
        raise DailyTaskError(f"Refusing to write outside allowed path: {path}") from exc


def ensure_under_any(path: Path, allowed_roots: tuple[Path, ...]) -> None:
    for allowed_root in allowed_roots:
        try:
            path.relative_to(allowed_root)
            return
        except ValueError:
            continue
    allowed = ", ".join(str(root) for root in allowed_roots)
    raise DailyTaskError(f"Refusing to write outside allowed paths ({allowed}): {path}")


def update_owl_audio_source(script_path: Path, audio_src: str) -> bool:
    try:
        original = script_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DailyTaskError(f"Cannot read ColorsAndNumbers script: {script_path}") from exc

    replacement = f'const owlAudio = new Audio("{audio_src}");'
    pattern = r'const owlAudio = new Audio\("[^"]+"\);'
    updated, count = re.subn(pattern, replacement, original, count=1)
    if count != 1:
        raise DailyTaskError("Could not find exactly one ColorsAndNumbers owl audio declaration.")
    if updated == original:
        return False

    try:
        script_path.write_text(updated, encoding="utf-8")
    except OSError as exc:
        raise DailyTaskError(f"Cannot update ColorsAndNumbers script: {script_path}") from exc
    return True


async def generate_edge_tts_mp3(text: str, output_path: Path, voice: str, rate: str) -> None:
    try:
        import edge_tts
    except ImportError as exc:  # pragma: no cover - GitHub Actions installs this dependency.
        raise DailyTaskError("Missing dependency 'edge-tts' for ColorsAndNumbers owl TTS.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await communicate.save(str(tmp_path))
        if not tmp_path.exists() or tmp_path.stat().st_size <= 0:
            raise DailyTaskError("Generated ColorsAndNumbers MP3 is empty.")
        tmp_path.replace(output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def generate_mp3(text: str, output_path: Path, voice: str, rate: str) -> None:
    asyncio.run(generate_edge_tts_mp3(text=text, output_path=output_path, voice=voice, rate=rate))


def find_owl_speech_row(csv_path: Path, run_date: str) -> dict | None:
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"date", "full_text"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise DailyTaskError(f"Owl speech CSV must contain columns: {', '.join(sorted(required))}")
            for row in reader:
                if row.get("date") == run_date:
                    text = (row.get("full_text") or "").strip()
                    if not text:
                        raise DailyTaskError(f"Owl speech CSV row for {run_date} is missing full_text.")
                    return row
    except OSError as exc:
        raise DailyTaskError(f"Cannot read owl speech CSV: {csv_path}") from exc
    return None


def owl_audio_filename(run_date: str) -> str:
    parsed = datetime.strptime(run_date, "%Y-%m-%d")
    return f"owl_{parsed.strftime('%d%m%y')}.mp3"


def owl_audio_src(run_date: str, filename: str) -> str:
    return f"{filename}?v={run_date.replace('-', '')}a"


def colors_numbers_targets(repo_root: Path, filename: str) -> list[tuple[Path, Path]]:
    return [
        (
            (repo_root / COLORS_NUMBERS_APP_DIR / filename).resolve(),
            (repo_root / COLORS_NUMBERS_APP_DIR / "app.js").resolve(),
        ),
        (
            (repo_root / DOCS_COLORS_NUMBERS_APP_DIR / filename).resolve(),
            (repo_root / DOCS_COLORS_NUMBERS_APP_DIR / "app.js").resolve(),
        ),
    ]


def run_colors_numbers_owl_csv_task(
    context: DailyContext,
    speech_csv_path: Path = DEFAULT_COLORS_NUMBERS_OWL_SPEECH_CSV,
    audio_generator=generate_mp3,
) -> dict:
    if not speech_csv_path.exists():
        return {
            "name": "colors_numbers_owl_tts_csv",
            "status": "skipped",
            "message": f"No owl speech CSV found at {speech_csv_path}.",
        }

    row = find_owl_speech_row(speech_csv_path, context.run_date)
    if row is None:
        return {
            "name": "colors_numbers_owl_tts_csv",
            "status": "skipped",
            "message": "No owl speech row for run date.",
            "run_date": context.run_date,
        }

    text = (row["full_text"] or "").strip()
    filename = owl_audio_filename(context.run_date)
    audio_src = owl_audio_src(context.run_date, filename)
    voice = (row.get("voice") or COLORS_NUMBERS_DEFAULT_OWL_VOICE).strip()
    rate = (row.get("rate") or COLORS_NUMBERS_DEFAULT_OWL_RATE).strip()

    repo_root = context.project_dir.parent.resolve()
    allowed_roots = tuple((repo_root / allowed_dir).resolve() for allowed_dir in COLORS_NUMBERS_ALLOWED_DIRS)
    targets = colors_numbers_targets(repo_root, filename)
    for output_path, script_path in targets:
        ensure_under_any(output_path, allowed_roots)
        ensure_under_any(script_path, allowed_roots)
        if not script_path.exists():
            raise DailyTaskError(f"ColorsAndNumbers script is missing: {script_path}")

    if all(output_path.exists() for output_path, _ in targets) and all(
        audio_src in script_path.read_text(encoding="utf-8") for _, script_path in targets
    ):
        return {
            "name": "colors_numbers_owl_tts_csv",
            "status": "completed",
            "message": "ColorsAndNumbers daily owl audio is already generated and selected.",
            "changed_files": [],
        }

    if context.dry_run:
        return {
            "name": "colors_numbers_owl_tts_csv",
            "status": "planned",
            "scheduled_date": context.run_date,
            "audio_src": audio_src,
            "outputs": [str(output_path.relative_to(repo_root)) for output_path, _ in targets],
        }

    logging.info("Generating daily ColorsAndNumbers owl TTS for %s.", context.run_date)
    primary_output = targets[0][0]
    audio_generator(text, primary_output, voice, rate)
    changed_files = [str(primary_output.relative_to(repo_root))]

    for output_path, _ in targets[1:]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(primary_output, output_path)
        changed_files.append(str(output_path.relative_to(repo_root)))

    for _, script_path in targets:
        if update_owl_audio_source(script_path, audio_src):
            changed_files.append(str(script_path.relative_to(repo_root)))

    return {
        "name": "colors_numbers_owl_tts_csv",
        "status": "completed",
        "scheduled_date": context.run_date,
        "audio_src": audio_src,
        "changed_files": changed_files,
    }


def run_colors_numbers_owl_task(
    context: DailyContext,
    config_path: Path = DEFAULT_COLORS_NUMBERS_OWL_CONFIG,
    speech_csv_path: Path = DEFAULT_COLORS_NUMBERS_OWL_SPEECH_CSV,
    audio_generator=generate_mp3,
) -> dict:
    csv_result = run_colors_numbers_owl_csv_task(
        context,
        speech_csv_path=speech_csv_path,
        audio_generator=audio_generator,
    )
    if csv_result["status"] != "skipped" or speech_csv_path.exists():
        return csv_result

    if not config_path.exists():
        return {
            "name": "colors_numbers_owl_tts",
            "status": "skipped",
            "message": f"No config found at {config_path}.",
        }

    config = read_json_file(config_path)
    scheduled_date = require_text_field(config, "date")
    if context.run_date != scheduled_date:
        return {
            "name": "colors_numbers_owl_tts",
            "status": "skipped",
            "scheduled_date": scheduled_date,
            "run_date": context.run_date,
        }

    text = require_text_field(config, "text_cs")
    audio_src = require_text_field(config, "audio_src")
    output_relative_path = require_text_field(config, "output_relative_path")
    script_relative_path = require_text_field(config, "script_relative_path")
    voice = require_text_field(config, "voice")
    rate = require_text_field(config, "rate")

    repo_root = context.project_dir.parent.resolve()
    allowed_root = (repo_root / COLORS_NUMBERS_APP_DIR).resolve()
    output_path = resolve_repo_path(context.project_dir, output_relative_path)
    script_path = resolve_repo_path(context.project_dir, script_relative_path)
    ensure_under(output_path, allowed_root)
    ensure_under(script_path, allowed_root)

    if output_path.exists() and script_path.exists() and audio_src in script_path.read_text(encoding="utf-8"):
        return {
            "name": "colors_numbers_owl_tts",
            "status": "completed",
            "message": "ColorsAndNumbers owl audio is already generated and selected.",
            "changed_files": [],
        }

    if context.dry_run:
        return {
            "name": "colors_numbers_owl_tts",
            "status": "planned",
            "scheduled_date": scheduled_date,
            "output": str(output_path),
            "script": str(script_path),
        }

    logging.info("Generating ColorsAndNumbers owl TTS for %s.", scheduled_date)
    audio_generator(text, output_path, voice, rate)
    app_js_changed = update_owl_audio_source(script_path, audio_src)

    return {
        "name": "colors_numbers_owl_tts",
        "status": "completed",
        "scheduled_date": scheduled_date,
        "audio_src": audio_src,
        "changed_files": [
            str(output_path.relative_to(repo_root)),
            *( [str(script_path.relative_to(repo_root))] if app_js_changed else [] ),
        ],
    }


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

    Concrete tasks must keep their own date gates and write allowlists. Git commit
    and push are handled by the GitHub Actions workflow, not by this Python entry
    point.
    """

    logging.info("Daily 3 AM routine started for %s.", context.run_date)
    logging.info("Project directory: %s", context.project_dir)
    logging.info("Dry run: %s", context.dry_run)
    return {
        "tasks": [
            {
                "name": "daily_3am_skeleton",
                "status": "completed",
                "message": "Daily scheduler is active.",
            },
            run_colors_numbers_owl_task(context),
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
        validate_time_gate_args(args)
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
    if args.window_start_hour is not None and not is_within_hour_window(
        now, args.window_start_hour, args.window_hours
    ):
        logging.info(
            "Current Europe/Prague time is outside allowed window starting at %s:00 for %s hours; no-op.",
            args.window_start_hour,
            args.window_hours,
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
