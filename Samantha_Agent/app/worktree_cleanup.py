"""Opt-in housekeeping of explicitly retired, disposable linked worktrees.

No force removal, branch deletion, recursive custom remover or OS cache cleanup.
Unknown local data and uncertain removals are left for a human to resolve.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from app.file_persistence import atomic_write_json, exclusive_file_lock
from scripts.cleanup_session_autosave import build_cleanup_plan

PROJECT = Path(__file__).resolve().parents[1]
CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
LABEL = "com.samantha.workspace-housekeeping"
# These are disposable build artefacts only. Every other ignored file blocks.
CACHES = frozenset({".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"})
GRACE_SECONDS = 3600


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Housekeeping:
    def __init__(self, project=PROJECT, *, worktrees=None, busy_probe=None, clock=time.time):
        self.project = Path(project).resolve()
        self.repo = self.project.parent
        self.base = Path(worktrees or Path.home() / ".codex/worktrees").absolute()
        self.root = self.project / "data/private/workspace_housekeeping"
        if self.root.resolve() != self.root:
            raise ValueError("Housekeeping state cannot use symlink ancestors")
        self.busy_probe = busy_probe or self._busy
        self.clock = clock

    def _read(self, name, default):
        path = self.root / name
        if path.is_symlink():
            raise ValueError("Symlink state is not allowed")
        return json.loads(path.read_text()) if path.exists() else default

    def _write(self, name, value):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic_write_json(self.root / name, value)

    def _git(self, path, *args, check=True):
        result = subprocess.run(["git", "--no-optional-locks", "-C", str(path), *args],
                                capture_output=True, timeout=90)
        if check and result.returncode:
            raise ValueError("Git check failed")
        return result

    def _linked(self):
        raw = self._git(self.repo, "worktree", "list", "--porcelain", "-z").stdout
        entries = {}
        current = None
        for field in raw.split(b"\0"):
            text = os.fsdecode(field)
            if text.startswith("worktree "):
                current = text[9:]
                entries[current] = {}
            elif text and current:
                key, _, value = text.partition(" ")
                entries[current][key] = value
        return entries

    def _path(self, name):
        if not re.fullmatch(r"data-[a-z0-9][a-z0-9-]*", name):
            raise ValueError("Only named disposable data-* worktrees are in scope")
        path = self.base / name
        if self.base.resolve() != self.base or path.resolve() != path or path.is_symlink():
            raise ValueError("Symlink or changed workspace root")
        if not path.is_dir() or not (path / ".git").is_file() or (path / ".git").is_symlink():
            raise ValueError("Not a linked disposable workspace")
        common = self._git(path, "rev-parse", "--git-common-dir").stdout.decode().strip()
        if (path / common).resolve() != self.repo / ".git":
            raise ValueError("Different repository")
        return path

    def _busy(self, path):
        # cwd, directory descriptors and open files are all included. Probe errors block.
        result = subprocess.run(["/usr/sbin/lsof", "-n", "-P", "-Fpn"],
                                capture_output=True, timeout=30)
        if result.returncode:
            raise ValueError("Cannot verify open files")
        prefix = str(path) + "/"
        return any(line[1:] == str(path) or line[1:].startswith(prefix)
                   for line in result.stdout.decode(errors="replace").splitlines() if line.startswith("n"))

    def inspect(self, name):
        row = {"name": name, "eligible": False, "reason": "unverified"}
        try:
            path = self._path(name)
            linked = self._linked().get(str(path))
            if linked is None or "locked" in linked or "prunable" in linked:
                raise ValueError("Workspace is locked, missing or prunable")
            head = self._git(path, "rev-parse", "HEAD").stdout.decode().strip()
            branch = self._git(path, "symbolic-ref", "--quiet", "HEAD", check=False).stdout.decode().strip()
            stat = path.stat()
            row.update(head=head, branch=branch, identity=[stat.st_dev, stat.st_ino])
            if self._git(self.repo, "merge-base", "--is-ancestor", head, "main", check=False).returncode:
                raise ValueError("Commits are not integrated into main")
            if self._git(path, "status", "--porcelain=v1", "--untracked-files=all").stdout:
                raise ValueError("Workspace has staged, modified or untracked files")
            ignored = self._git(path, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").stdout
            inventory = []
            unknown = 0
            duplicates = 0
            for raw in ignored.split(b"\0"):
                if not raw:
                    continue
                relative = Path(os.fsdecode(raw))
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Unsafe ignored path")
                item = path / relative
                s = item.lstat()
                # Never follow ignored symlinks, including ancestors of a cache file.
                safe = not item.is_symlink() and not any((path / p).is_symlink() for p in relative.parents)
                cache = any(p in CACHES for p in relative.parts[:-1]) or relative.name == ".DS_Store"
                canonical = self.repo / relative
                duplicate_hash = None
                if safe and not cache and item.is_file() and canonical.is_file() and canonical.resolve() == canonical:
                    # Hash locally; never persist filenames, contents or individual secret hashes.
                    def file_hash(filename):
                        checksum = hashlib.sha256()
                        with filename.open("rb") as stream:
                            for block in iter(lambda: stream.read(1024 * 1024), b""):
                                checksum.update(block)
                        return checksum.hexdigest()
                    if s.st_size == canonical.stat().st_size:
                        candidate_hash = file_hash(item)
                        if candidate_hash == file_hash(canonical):
                            duplicate_hash = candidate_hash
                            duplicates += 1
                if not safe or (not cache and duplicate_hash is None):
                    unknown += 1
                inventory.append([str(relative), s.st_ino, s.st_size, s.st_mtime_ns, duplicate_hash])
            row["unknown_ignored_files"] = unknown
            row["verified_canonical_duplicates"] = duplicates
            row["inventory_sha256"] = digest(inventory)
            if unknown:
                raise ValueError("Unknown ignored data must be preserved first")
            if self.busy_probe(path):
                raise ValueError("Workspace is in use")
            allocated = 0
            for directory, dirs, files in os.walk(path, followlinks=False):
                for filename in files:
                    s = (Path(directory) / filename).lstat()
                    allocated += s.st_blocks * 512
            row.update(eligible=True, reason="ready", allocated_bytes=allocated)
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            row["reason"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        return row

    def preview(self):
        state = self._read("state.json", {"entries": {}})
        rows = []
        for path in sorted(self._linked()):
            candidate = Path(path)
            if candidate.parent != self.base or not candidate.name.startswith("data-"):
                continue
            row = self.inspect(candidate.name)
            entry = state["entries"].get(candidate.name)
            row["retirement"] = entry.get("state") if entry else "not_retired"
            rows.append(row)
        auto = self.project / "data/session_autosave"
        plan = build_cleanup_plan(autosave_dir=auto, keep_latest_snapshots=12)
        return {"enabled": self._read("activation.json", {}).get("enabled", False), "worktrees": rows,
                "autosave": {"delete_count": plan.delete_count, "allocated_bytes": plan.allocated_bytes,
                             "keep_latest_snapshots": 12}, "grace_seconds": GRACE_SECONDS}

    def retire(self, name, *, expected_head):
        # This is an explicit completion marker, not a delete operation.
        with exclusive_file_lock(self.root / "operation"):
            row = self.inspect(name)
            if not row["eligible"] or row.get("head") != expected_head:
                raise ValueError("Workspace is not ready at the approved head: " + row["reason"])
            state = self._read("state.json", {"entries": {}})
            old = state["entries"].get(name)
            if old and old["state"] in {"removing", "attention"}:
                raise ValueError("An uncertain prior removal needs manual review")
            if old and old["state"] == "retired" and old["snapshot"] == row:
                return old
            entry = {"state": "retired", "marked_at": self.clock(), "snapshot": row}
            state["entries"][name] = entry
            self._write("state.json", state)
            return entry

    def cancel(self, name):
        with exclusive_file_lock(self.root / "operation"):
            state = self._read("state.json", {"entries": {}})
            entry = state["entries"].get(name)
            if entry and entry["state"] in {"removing", "attention"}:
                raise ValueError("Uncertain removal needs manual review")
            if entry:
                entry["state"] = "cancelled"
                self._write("state.json", state)
            return {"name": name, "state": "cancelled"}

    def _autosave(self):
        root = self.project / "data/session_autosave"
        if root.resolve() != root:
            return {"state": "blocked", "reason": "Autosave directory is a symlink"}
        # Never reduce history when the current recovery copy is stale/missing.
        for name in ("latest_session.jsonl", "latest_session.txt", "previous_session.jsonl", "previous_session.txt"):
            p = root / name
            if not p.is_file() or p.is_symlink() or p.stat().st_size == 0:
                return {"state": "blocked", "reason": "Current and previous recovery must exist"}
        if self.clock() - (root / "latest_session.jsonl").stat().st_mtime > 1200:
            return {"state": "blocked", "reason": "Current recovery is stale"}
        plan = build_cleanup_plan(autosave_dir=root, keep_latest_snapshots=12)
        frozen = {}
        for item in plan.delete_files:
            p = Path(item.path)
            if not p.is_absolute():
                p = PROJECT / p
            s = p.lstat()
            frozen[p] = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        removed = 0
        for item in plan.delete_files:
            p = Path(item.path)
            if not p.is_absolute():
                p = PROJECT / p
            if p.parent.resolve() != root.resolve() or p.is_symlink():
                raise ValueError("Autosave path changed")
            if not p.exists():
                continue
            s = p.stat()
            if s.st_size != item.size_bytes or (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns) != frozen[p]:
                raise ValueError("Autosave snapshot changed")
            p.unlink()
            removed += 1
        return {"state": "completed", "removed": removed}

    def tick(self):
        with exclusive_file_lock(self.root / "operation"):
            if not self._read("activation.json", {}).get("enabled", False):
                return {"state": "disabled", "removed": []}
            before = shutil.disk_usage(self.project).free
            state = self._read("state.json", {"entries": {}})
            removed, blocked = [], []
            for name, entry in state["entries"].items():
                if entry["state"] == "removing":
                    entry["state"] = "attention"
                if entry["state"] != "retired":
                    if entry["state"] == "attention":
                        blocked.append({"name": name, "reason": "Uncertain removal; no automatic retry"})
                    continue
                if self.clock() - entry["marked_at"] < GRACE_SECONDS:
                    continue
                row = self.inspect(name)
                if not row["eligible"] or row != entry["snapshot"]:
                    blocked.append({"name": name, "reason": row["reason"] if not row["eligible"] else "Workspace changed since completion"})
                    continue
                entry["state"] = "removing"
                self._write("state.json", state)  # durable intent before removal
                try:
                    # Git owns removal and refuses dirty workspaces. Never --force.
                    self._git(self.repo, "worktree", "remove", str(self.base / name))
                    entry["state"] = "removed"
                    removed.append(name)
                except (ValueError, OSError, subprocess.SubprocessError):
                    entry["state"] = "attention"
                    blocked.append({"name": name, "reason": "Removal not confirmed; no automatic retry"})
                self._write("state.json", state)
            self._write("state.json", state)
            try:
                autosave = self._autosave()
            except (ValueError, OSError):
                autosave = {"state": "blocked", "reason": "Autosave changed; history preserved"}
            after = shutil.disk_usage(self.project).free
            result = {"state": "attention" if blocked or autosave["state"] == "blocked" else "completed",
                      "time": self.clock(), "removed": removed, "blocked": blocked, "autosave": autosave,
                      "free_before_bytes": before, "free_after_bytes": after, "free_change_bytes": after - before}
            self._write("latest.json", result)
            return result
