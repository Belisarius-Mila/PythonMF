#!/usr/bin/env python3
"""Clean old Samantha/Codex session autosave snapshots.

The tool intentionally looks only at file names and sizes. Autosave files can
contain sensitive conversation content, so cleanup planning must not read them.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUTOSAVE_DIR = PROJECT_ROOT / "data" / "session_autosave"
CONFIRM_TEXT = "SMAZAT STARE AUTOSAVE"
SNAPSHOT_RE = re.compile(r"^session_(?P<stamp>\d{8}_\d{6})\.(?P<ext>jsonl|txt)$")
DEFAULT_RETENTION_DAYS = 0
DEFAULT_KEEP_LATEST_SNAPSHOTS = 12


@dataclass(frozen=True)
class CleanupFile:
    path: str
    size_bytes: int
    timestamp: str


@dataclass(frozen=True)
class CleanupPlan:
    autosave_dir: str
    retention_days: int
    keep_latest_snapshots: int
    scanned_timestamped_files: int
    protected_timestamped_files: int
    delete_count: int
    reclaim_bytes: int
    delete_files: tuple[CleanupFile, ...]


def parse_snapshot_timestamp(path: Path) -> datetime | None:
    match = SNAPSHOT_RE.match(path.name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group("stamp"), "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def build_cleanup_plan(
    *,
    autosave_dir: Path = AUTOSAVE_DIR,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    keep_latest_snapshots: int = DEFAULT_KEEP_LATEST_SNAPSHOTS,
    now: datetime | None = None,
) -> CleanupPlan:
    if retention_days < 0:
        raise ValueError("retention_days must be >= 0")
    if keep_latest_snapshots < 0:
        raise ValueError("keep_latest_snapshots must be >= 0")

    now = now or datetime.now()
    cutoff = now - timedelta(days=retention_days)
    snapshots: list[tuple[Path, datetime, int]] = []

    if autosave_dir.exists():
        for path in autosave_dir.iterdir():
            if not path.is_file() or path.is_symlink():
                continue
            timestamp = parse_snapshot_timestamp(path)
            if timestamp is None:
                continue
            snapshots.append((path, timestamp, path.stat().st_size))

    newest_stamps = {
        stamp
        for stamp in sorted({timestamp for _path, timestamp, _size in snapshots}, reverse=True)[
            :keep_latest_snapshots
        ]
    }

    protected = 0
    delete_files: list[CleanupFile] = []
    for path, timestamp, size in sorted(snapshots, key=lambda item: item[1]):
        if timestamp >= cutoff or timestamp in newest_stamps:
            protected += 1
            continue
        delete_files.append(
            CleanupFile(
                path=display_path(path),
                size_bytes=size,
                timestamp=timestamp.isoformat(sep=" "),
            )
        )

    return CleanupPlan(
        autosave_dir=display_path(autosave_dir),
        retention_days=retention_days,
        keep_latest_snapshots=keep_latest_snapshots,
        scanned_timestamped_files=len(snapshots),
        protected_timestamped_files=protected,
        delete_count=len(delete_files),
        reclaim_bytes=sum(item.size_bytes for item in delete_files),
        delete_files=tuple(delete_files),
    )


def apply_cleanup(plan: CleanupPlan, *, project_root: Path = PROJECT_ROOT) -> int:
    removed = 0
    for item in plan.delete_files:
        path = project_root / item.path
        if not path.exists():
            continue
        if parse_snapshot_timestamp(path) is None:
            raise RuntimeError(f"refusing to remove non-snapshot file: {path}")
        path.unlink()
        removed += 1
    return removed


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def format_bytes(size: int) -> str:
    gib = size / 1024 / 1024 / 1024
    mib = size / 1024 / 1024
    if gib >= 1:
        return f"{gib:.2f} GiB"
    return f"{mib:.1f} MiB"


def format_plan(plan: CleanupPlan, *, applied: bool = False, removed: int = 0) -> str:
    lines = ["Samantha session autosave cleanup:"]
    lines.append(f"- adresar: {plan.autosave_dir}")
    if plan.retention_days:
        lines.append(f"- retence: ponechat vse za poslednich {plan.retention_days} dni")
    else:
        lines.append("- retence podle stari: vypnuta")
    lines.append(f"- pojistka: ponechat nejnovejsich {plan.keep_latest_snapshots} casovych snapshotu")
    lines.append(f"- timestampovane soubory: {plan.scanned_timestamped_files}")
    lines.append(f"- chranene timestampovane soubory: {plan.protected_timestamped_files}")
    lines.append(f"- kandidati ke smazani: {plan.delete_count}")
    lines.append(f"- odhad uvolneni: {format_bytes(plan.reclaim_bytes)}")
    if applied:
        lines.append(f"- provedeno: smazano {removed} souboru")
    else:
        lines.append("- dry-run: nic nebylo smazano")
        lines.append(f"- pro provedeni: --apply --confirm '{CONFIRM_TEXT}'")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply cleanup of old timestamped Samantha/Codex autosave snapshots."
    )
    parser.add_argument("--autosave-dir", type=Path, default=AUTOSAVE_DIR)
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    parser.add_argument("--keep-latest-snapshots", type=int, default=DEFAULT_KEEP_LATEST_SNAPSHOTS)
    parser.add_argument("--apply", action="store_true", help="Actually delete matching old timestamped snapshots.")
    parser.add_argument("--confirm", default="", help=f"Required exact text for --apply: {CONFIRM_TEXT}")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_cleanup_plan(
        autosave_dir=args.autosave_dir,
        retention_days=args.retention_days,
        keep_latest_snapshots=args.keep_latest_snapshots,
    )

    removed = 0
    if args.apply:
        if args.confirm != CONFIRM_TEXT:
            if args.json:
                print(json.dumps({"ok": False, "error": "missing exact confirmation", "plan": asdict(plan)}, indent=2))
            else:
                print(format_plan(plan))
                print(f"\nChybi presne potvrzeni: --confirm '{CONFIRM_TEXT}'")
            return 2
        removed = apply_cleanup(plan)

    if args.json:
        print(json.dumps({"ok": True, "applied": args.apply, "removed": removed, "plan": asdict(plan)}, indent=2))
    else:
        print(format_plan(plan, applied=args.apply, removed=removed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
