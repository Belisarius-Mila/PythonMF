from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.backup.activity_state import record_backup_completed


SAMANTHA_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = SAMANTHA_DIR.parent
DEFAULT_BACKUP_ROOT = Path("/Volumes/SamanthaSecureBackup/SamanthaBackups")
ALWAYS_FILTER = SAMANTHA_DIR / "scripts" / "backup_rsync_filter_always.rules"
SENSITIVE_FILTER = SAMANTHA_DIR / "scripts" / "backup_rsync_filter_sensitive.rules"
RECOVERY_GUIDE = SAMANTHA_DIR / "RECOVERY_FROM_BACKUP.md"
COPY_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class BackupPlan:
    source_root: Path
    backup_root: Path
    snapshot_dir: Path
    pythonmf_dest: Path
    codex_dest: Path
    previous_snapshot: Path | None
    profile: str
    dry_run: bool


@dataclass
class BackupStats:
    dirs_seen: int = 0
    files_seen: int = 0
    files_copied: int = 0
    files_linked: int = 0
    files_skipped: int = 0
    symlinks_copied: int = 0
    bytes_copied: int = 0


class FilterRules:
    def __init__(self, patterns: Iterable[str]) -> None:
        self.patterns = [pattern for pattern in patterns if pattern]

    @classmethod
    def from_files(cls, paths: Iterable[Path]) -> "FilterRules":
        patterns: list[str] = []
        for path in paths:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    value = line.strip()
                    if not value or value.startswith("#"):
                        continue
                    patterns.append(value)
        return cls(patterns)

    def is_excluded(self, relative_path: Path, is_dir: bool) -> bool:
        posix_path = relative_path.as_posix()
        components = relative_path.parts
        for pattern in self.patterns:
            directory_pattern = pattern.endswith("/")
            clean_pattern = pattern.rstrip("/")
            if directory_pattern and not is_dir:
                continue
            if "/" in clean_pattern:
                if posix_path == clean_pattern or posix_path.startswith(clean_pattern + "/"):
                    return True
                continue
            if any(fnmatch.fnmatchcase(component, clean_pattern) for component in components):
                return True
            if not is_dir and fnmatch.fnmatchcase(relative_path.name, clean_pattern):
                return True
        return False


def run_backup(
    *,
    mode: str,
    profile: str,
    backup_root: Path,
    source_root: Path = PROJECT_ROOT,
    timestamp: str | None = None,
    progress_every: int = 5000,
) -> str:
    if mode not in {"dry-run", "execute"}:
        raise ValueError("mode musi byt dry-run nebo execute")
    if profile not in {"safe", "recovery"}:
        raise ValueError("profile musi byt safe nebo recovery")
    if not source_root.exists():
        raise ValueError(f"Source neexistuje: {source_root}")
    if profile == "recovery" and mode == "execute" and not _is_secure_recovery_target(backup_root):
        raise ValueError("Recovery execute smi bezet jen do /Volumes/SamanthaSecureBackup/SamanthaBackups")

    backup_root = backup_root.expanduser()
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = backup_root / "snapshots" / stamp
    plan = BackupPlan(
        source_root=source_root,
        backup_root=backup_root,
        snapshot_dir=snapshot_dir,
        pythonmf_dest=snapshot_dir / "PythonMF",
        codex_dest=snapshot_dir / "codex_home",
        previous_snapshot=_latest_completed_snapshot(backup_root),
        profile=profile,
        dry_run=mode == "dry-run",
    )

    filter_files = [ALWAYS_FILTER]
    if profile == "safe":
        filter_files.append(SENSITIVE_FILTER)
    rules = FilterRules.from_files(filter_files)

    stats = BackupStats()
    lines = [
        "Samantha Python backup",
        f"Mode: {mode}",
        f"Profile: {profile}",
        f"Source: {source_root}",
        f"Target: {plan.pythonmf_dest}",
        f"Previous snapshot: {plan.previous_snapshot or 'none'}",
        "",
    ]

    if not plan.dry_run:
        plan.pythonmf_dest.mkdir(parents=True, exist_ok=False)
        plan.codex_dest.mkdir(parents=True, exist_ok=True)

    _copy_tree(
        source_root,
        plan.pythonmf_dest,
        previous_root=(plan.previous_snapshot / "PythonMF" if plan.previous_snapshot else None),
        rules=rules,
        stats=stats,
        dry_run=plan.dry_run,
        progress_every=progress_every,
    )
    _copy_codex_home(plan=plan, rules=rules, stats=stats, progress_every=progress_every)

    lines.extend(_format_stats(stats))

    if plan.dry_run:
        lines.append("")
        lines.append("Dry-run hotov. Nic nebylo zkopirovano.")
        return "\n".join(lines)

    _write_manifest(plan, rules)
    record_backup_completed(target=str(plan.pythonmf_dest), mode=profile)
    state_path = SAMANTHA_DIR / "data" / "backup" / "activity_state.json"
    if state_path.exists():
        backup_state_path = plan.pythonmf_dest / "Samantha_Agent" / "data" / "backup" / "activity_state.json"
        backup_state_path.parent.mkdir(parents=True, exist_ok=True)
        _copy_file_chunked(state_path, backup_state_path)
        shutil.copystat(state_path, backup_state_path, follow_symlinks=False)

    lines.append("")
    lines.append("Ostra zaloha hotova.")
    lines.append(f"Manifest: {plan.snapshot_dir / 'backup_manifest.txt'}")
    return "\n".join(lines)


def _copy_tree(
    source_root: Path,
    dest_root: Path,
    *,
    previous_root: Path | None,
    rules: FilterRules,
    stats: BackupStats,
    dry_run: bool,
    progress_every: int,
) -> None:
    for current_root, dir_names, file_names in os.walk(source_root, topdown=True, followlinks=False):
        current = Path(current_root)
        relative_dir = current.relative_to(source_root)
        stats.dirs_seen += 1

        kept_dirs: list[str] = []
        for dir_name in dir_names:
            rel = relative_dir / dir_name
            if rules.is_excluded(rel, is_dir=True):
                continue
            kept_dirs.append(dir_name)
        dir_names[:] = kept_dirs

        target_dir = dest_root / relative_dir
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        for file_name in file_names:
            rel = relative_dir / file_name
            if rules.is_excluded(rel, is_dir=False):
                continue
            source_path = current / file_name
            target_path = dest_root / rel
            previous_path = previous_root / rel if previous_root else None
            _copy_one(source_path, target_path, previous_path=previous_path, stats=stats, dry_run=dry_run)
            if progress_every > 0 and stats.files_seen % progress_every == 0:
                print(
                    f"progress files={stats.files_seen} copied={stats.files_copied} linked={stats.files_linked}",
                    flush=True,
                )


def _copy_one(
    source_path: Path,
    target_path: Path,
    *,
    previous_path: Path | None,
    stats: BackupStats,
    dry_run: bool,
) -> None:
    stats.files_seen += 1
    if source_path.is_symlink():
        stats.symlinks_copied += 1
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.symlink_to(os.readlink(source_path))
        return

    try:
        source_stat = source_path.stat()
    except OSError:
        stats.files_skipped += 1
        return

    if previous_path and previous_path.exists() and _same_file_metadata(source_stat, previous_path):
        stats.files_linked += 1
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(previous_path, target_path)
                return
            except OSError:
                pass

    stats.files_copied += 1
    stats.bytes_copied += source_stat.st_size
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        _copy_file_chunked(source_path, target_path)
        shutil.copystat(source_path, target_path, follow_symlinks=False)


def _same_file_metadata(source_stat: os.stat_result, previous_path: Path) -> bool:
    try:
        previous_stat = previous_path.stat()
    except OSError:
        return False
    return (
        source_stat.st_size == previous_stat.st_size
        and int(source_stat.st_mtime) == int(previous_stat.st_mtime)
        and previous_path.is_file()
    )


def _copy_file_chunked(source_path: Path, target_path: Path) -> None:
    with source_path.open("rb") as source, target_path.open("wb") as target:
        while True:
            chunk = source.read(COPY_CHUNK_SIZE)
            if not chunk:
                break
            target.write(chunk)


def _copy_codex_home(*, plan: BackupPlan, rules: FilterRules, stats: BackupStats, progress_every: int) -> None:
    codex_home = Path.home() / ".codex"
    if not codex_home.exists():
        return
    previous_root = plan.previous_snapshot / "codex_home" if plan.previous_snapshot else None
    files = [codex_home / "config.toml"]
    if plan.profile == "recovery":
        files.extend([codex_home / "history.jsonl"])
        sessions = codex_home / "sessions"
        if sessions.exists():
            _copy_tree(
                sessions,
                plan.codex_dest / "sessions",
                previous_root=(previous_root / "sessions" if previous_root else None),
                rules=rules,
                stats=stats,
                dry_run=plan.dry_run,
                progress_every=progress_every,
            )
    for source_path in files:
        if source_path.exists():
            _copy_one(
                source_path,
                plan.codex_dest / source_path.name,
                previous_path=(previous_root / source_path.name if previous_root else None),
                stats=stats,
                dry_run=plan.dry_run,
            )


def _latest_completed_snapshot(backup_root: Path) -> Path | None:
    snapshots_dir = backup_root / "snapshots"
    if not snapshots_dir.exists():
        return None
    candidates = sorted((path for path in snapshots_dir.iterdir() if path.is_dir()), reverse=True)
    for candidate in candidates:
        if (candidate / "backup_manifest.txt").exists():
            return candidate
    return None


def _write_manifest(plan: BackupPlan, rules: FilterRules) -> None:
    recovery_copy = plan.snapshot_dir / "READ_ME_FIRST_RECOVERY.md"
    if RECOVERY_GUIDE.exists():
        _copy_file_chunked(RECOVERY_GUIDE, recovery_copy)
        shutil.copystat(RECOVERY_GUIDE, recovery_copy, follow_symlinks=False)
    manifest = plan.snapshot_dir / "backup_manifest.txt"
    manifest.write_text(
        "\n".join(
            [
                f"Created at: {datetime.now().isoformat(timespec='seconds')}",
                "Tool: python incremental backup",
                f"Profile: {plan.profile}",
                f"Source: {plan.source_root}",
                f"Target: {plan.pythonmf_dest}",
                f"Codex target: {plan.codex_dest}",
                f"Previous snapshot: {plan.previous_snapshot or 'none'}",
                "",
                "Filters:",
                *rules.patterns,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _format_stats(stats: BackupStats) -> list[str]:
    return [
        "Summary:",
        f"- dirs seen: {stats.dirs_seen}",
        f"- files seen: {stats.files_seen}",
        f"- files copied: {stats.files_copied}",
        f"- files hard-linked: {stats.files_linked}",
        f"- files skipped: {stats.files_skipped}",
        f"- symlinks copied: {stats.symlinks_copied}",
        f"- bytes copied: {stats.bytes_copied}",
    ]


def _is_secure_recovery_target(backup_root: Path) -> bool:
    text = str(backup_root.expanduser())
    return text == str(DEFAULT_BACKUP_ROOT) or text.startswith(str(DEFAULT_BACKUP_ROOT) + "/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PythonMF/Samantha incremental backup without rsync mmap.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only, do not write files.")
    mode.add_argument("--execute", action="store_true", help="Write a real snapshot.")
    parser.add_argument("--profile", choices=["safe", "recovery"], default="safe")
    parser.add_argument("--target", default=str(DEFAULT_BACKUP_ROOT))
    parser.add_argument("--source", default=str(PROJECT_ROOT))
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--progress-every", type=int, default=5000)
    args = parser.parse_args(argv)

    selected_mode = "execute" if args.execute else "dry-run"
    try:
        output = run_backup(
            mode=selected_mode,
            profile=args.profile,
            backup_root=Path(args.target),
            source_root=Path(args.source),
            timestamp=args.timestamp or None,
            progress_every=args.progress_every,
        )
    except Exception as exc:
        print(f"Chyba: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
