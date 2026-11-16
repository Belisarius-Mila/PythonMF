"""Published-work cleanup with compact, verified preservation of unique files."""
from __future__ import annotations

import hashlib
import gzip
import json
import os
from pathlib import Path
import shutil
import stat

from app.file_persistence import atomic_create_bytes, exclusive_file_lock
from app.worktree_cleanup import CACHES, CONFIRMATION, allocated_bytes, digest

CACHE_ARCHIVES = ("ssd_cleanup_20261115/preserved", "focused_pn_cleanup_20261115/retired_worktree_data")
MAX_UNIQUE_BYTES = 100 * 1024**2
KEEP_SNAPSHOTS = 2
LEGACY_AUTOSAVE_PATTERN = r"(?:latest|previous)_(?:session|info) [1-9]\d*(?:\.(?:jsonl|txt))?"


class PublishedCleanup:
    def __init__(self, service):
        self.h = service

    def _git(self, path, *args, data=None):
        if data is None:
            return self.h._git(path, *args).stdout
        import subprocess
        result = subprocess.run(["git", "--no-optional-locks", "-C", str(path), *args], input=data,
                                capture_output=True, timeout=90)
        if result.returncode:
            raise ValueError("Git cleanup normalization failed")
        return result.stdout

    def _published(self):
        head = self._git(self.h.repo, "rev-parse", "main").decode().strip()
        origin = self._git(self.h.repo, "rev-parse", "origin/main").decode().strip()
        if head != origin or self._git(self.h.repo, "status", "--porcelain=v1", "--untracked-files=all"):
            raise ValueError("Cleanup needs a clean, published main")
        return head

    def _reachable(self):
        return {line.split(b" ", 1)[0].decode() for line in self._git(self.h.repo, "rev-list", "--objects", "main").splitlines()}

    def _sources(self):
        from app.worktree_cleanup import PROJECT
        return {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                (Path(__file__), PROJECT / "app/worktree_cleanup.py", PROJECT / "scripts/cleanup_session_autosave.py")}

    def _scope(self):
        return {"version": 2, "project": str(self.h.project), "base": str(self.h.base),
                "autosave_keep": KEEP_SNAPSHOTS, "legacy_pattern": LEGACY_AUTOSAVE_PATTERN,
                "cache_archives": list(CACHE_ARCHIVES), "cache_names": sorted(CACHES | {".build"}),
                "max_unique_bytes": MAX_UNIQUE_BYTES}

    def _record(self, path, relative, reachable):
        item = path / relative
        if relative.is_absolute() or ".." in relative.parts or ".git" in relative.parts:
            raise ValueError("Unsafe cleanup path")
        if "session_autosave" in relative.parts:
            raise ValueError("Emergency autosave needs separate metadata-only cleanup")
        if any((path / p).is_symlink() for p in relative.parents):
            raise ValueError("Symlink ancestor needs manual preservation")
        s = item.lstat()
        if not stat.S_ISREG(s.st_mode) and not stat.S_ISLNK(s.st_mode):
            raise ValueError("Special file needs manual preservation")
        if stat.S_ISLNK(s.st_mode):
            data = os.fsencode(os.readlink(item))
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            sha = hashlib.sha256(data).hexdigest()
        else:
            blob_hash = hashlib.sha1(b"blob " + str(s.st_size).encode() + b"\0")
            sha_hash = hashlib.sha256()
            with item.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    blob_hash.update(block); sha_hash.update(block)
            blob, sha = blob_hash.hexdigest(), sha_hash.hexdigest()
        after = item.lstat()
        identity = lambda x: [x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_mode]
        if identity(s) != identity(after):
            raise ValueError("File changed during cleanup audit")
        return {"path": str(relative), "kind": "symlink" if stat.S_ISLNK(s.st_mode) else "file",
                "identity": identity(s), "git_blob": blob, "sha256": sha,
                "in_git": blob in reachable, "size": s.st_size}

    def scan(self, name):
        path = self.h._path(name)
        linked = self.h._linked().get(str(path), {})
        if not linked or "locked" in linked or "prunable" in linked:
            raise ValueError("Workspace is locked, missing or prunable")
        head = self._git(path, "rev-parse", "HEAD").decode().strip()
        if self.h._git(self.h.repo, "merge-base", "--is-ancestor", head, "main", check=False).returncode:
            raise ValueError("Commits are not integrated into main")
        if self.h.busy_probe(path):
            raise ValueError("Workspace is in use")
        flags = self._git(path, "ls-files", "-v", "-z").split(b"\0")
        if any(x and (x[:1].islower() or x[:1] == b"S") for x in flags):
            raise ValueError("Hidden index flags need manual review")
        reachable = self._reachable()
        changed = {x for x in self._git(path, "diff", "HEAD", "--name-only", "-z").split(b"\0") if x}
        untracked = {x for x in self._git(path, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if x}
        ignored = {x for x in self._git(path, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").split(b"\0") if x}
        records = []
        for raw in sorted(changed | untracked | ignored):
            rel = Path(os.fsdecode(raw))
            if any(p in CACHES | {".build"} for p in rel.parts[:-1]) or rel.name == ".DS_Store":
                continue
            if not (path / rel).exists() and not (path / rel).is_symlink():
                records.append({"path": str(rel), "kind": "deleted"}); continue
            records.append(self._record(path, rel, reachable))
        staged = {x for x in self._git(path, "diff", "--cached", "--name-only", "-z").split(b"\0") if x}
        for item in self._git(path, "ls-files", "--stage", "-z").split(b"\0"):
            if not item:
                continue
            meta, raw = item.split(b"\t", 1)
            mode, oid, stage = meta.decode().split()
            if stage != "0" or mode == "160000":
                raise ValueError("Conflicts or submodules need manual review")
            if raw in staged:
                if oid not in reachable and int(self._git(path, "cat-file", "-s", oid)) > MAX_UNIQUE_BYTES:
                    raise ValueError("Unique data exceeds compact preservation limit")
                data = None if oid in reachable else self._git(path, "cat-file", "blob", oid)
                records.append({"path": os.fsdecode(raw), "kind": "index", "mode": mode, "git_blob": oid,
                                "in_git": oid in reachable, "sha256": hashlib.sha256(data).hexdigest() if data is not None else None,
                                "size": len(data) if data is not None else 0})
        unique_bytes = sum(r.get("size", 0) for r in records if not r.get("in_git") and r["kind"] != "deleted")
        if unique_bytes > MAX_UNIQUE_BYTES:
            raise ValueError("Unique data exceeds compact preservation limit")
        s = path.stat()
        # Reachability may improve after publication; filesystem identity must not change.
        fingerprint = digest({"head": head, "branch": linked.get("branch"), "identity": [s.st_dev, s.st_ino],
                              "files": [{k: v for k, v in r.items() if k not in {"in_git", "size"}
                                         and not (r["kind"] == "index" and k == "sha256")} for r in records]})
        return {"name": name, "head": head, "fingerprint": fingerprint, "records": records,
                "unique_bytes": unique_bytes, "allocated_bytes": allocated_bytes(path),
                "untracked": [os.fsdecode(x) for x in sorted(untracked)], "dirty": bool(changed)}

    def inspect(self, name):
        try:
            scan = self.scan(name)
            return {"name": name, "eligible": True, "reason": "ready", **{k: scan[k] for k in
                    ("head", "fingerprint", "allocated_bytes", "unique_bytes")}}
        except Exception as error:
            row = {"name": name, "eligible": False, "reason": str(error) if isinstance(error, ValueError) else type(error).__name__}
            try:
                row["allocated_bytes"] = allocated_bytes(self.h._path(name))
            except Exception:
                row["allocated_bytes"] = None
            return row

    def retire_unlocked(self, name, expected_head):
        scan = self.scan(name)
        if scan["head"] != expected_head:
            raise ValueError("Workspace head changed")
        state = self.h._read("state.json", {"entries": {}})
        old = state["entries"].get(name, {})
        if old.get("state") in {"removing", "attention"}:
            raise ValueError("An uncertain removal needs manual review")
        entry = {"state": "retired", "version": 2, "marked_at": self.h.clock(),
                 "fingerprint": scan["fingerprint"], "head": expected_head}
        state["entries"][name] = entry
        self.h._write("state.json", state)
        return entry

    def _preserve(self, scan):
        root = self.h.root / "preserved"
        if root.resolve() != root:
            raise ValueError("Preservation directory cannot be a symlink")
        path = self.h._path(scan["name"])
        for r in scan["records"]:
            if r.get("in_git") or r["kind"] == "deleted":
                continue
            if r["kind"] == "index":
                data = self._git(path, "cat-file", "blob", r["git_blob"])
            elif r["kind"] == "symlink":
                data = os.fsencode(os.readlink(path / r["path"]))
            else:
                data = (path / r["path"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != r["sha256"]:
                raise ValueError("Unique content changed before preservation")
            target = root / "objects" / r["sha256"]
            if target.resolve() != target:
                raise ValueError("Preservation object cannot use a symlink")
            if not target.exists():
                atomic_create_bytes(target, data)
            if hashlib.sha256(target.read_bytes()).hexdigest() != r["sha256"]:
                raise ValueError("Preserved copy was not verified")
        manifest = root / (scan["fingerprint"] + ".json.gz")
        if manifest.resolve() != manifest:
            raise ValueError("Preservation manifest cannot be a symlink")
        payload = gzip.compress(json.dumps(scan, sort_keys=True, separators=(",", ":")).encode(), mtime=0)
        if not manifest.exists():
            atomic_create_bytes(manifest, payload)
        if json.loads(gzip.decompress(manifest.read_bytes()))["fingerprint"] != scan["fingerprint"]:
            raise ValueError("Preservation manifest was not verified")

    def _cache_dirs(self):
        result = []
        for relative in CACHE_ARCHIVES:
            root = self.h.project / "data/private" / relative
            if root.resolve() != root:
                raise ValueError("Archive root cannot be a symlink")
            for directory, dirs, files in os.walk(root, followlinks=False):
                if ".build" in dirs:
                    target = Path(directory) / ".build"
                    if target.resolve() != target:
                        raise ValueError("Build cache cannot be a symlink")
                    result.append(target); dirs.remove(".build")
        return result

    def prepare(self, *, completed_names=()):
        self._published()
        completed_names = set(completed_names)
        rows = []
        for path in sorted(self.h._linked()):
            p = Path(path)
            if p.parent == self.h.base and p.name.startswith("data-"):
                try:
                    scan = self.scan(p.name)
                    rows.append({**{k: scan[k] for k in ("name", "head", "fingerprint", "unique_bytes", "allocated_bytes")},
                                 "close_approved": p.name in completed_names})
                except (ValueError, OSError) as error:
                    rows.append({"name": p.name, "blocked": type(error).__name__, "close_approved": p.name in completed_names})
        if completed_names - {r["name"] for r in rows}:
            raise ValueError("An approved completed workspace is no longer registered")
        caches = [{"path": str(p.relative_to(self.h.project)), "allocated_bytes": allocated_bytes(p)} for p in self._cache_dirs()]
        body = {"version": 2, "project": str(self.h.project), "base": str(self.h.base),
                "autosave_keep": 2, "numbered_autosave": True, "cache_archives": list(CACHE_ARCHIVES),
                "max_unique_bytes": MAX_UNIQUE_BYTES, "worktrees": rows, "caches": caches,
                "sources": self._sources()}
        proposal = {"contract": body, "sha256": digest(body)}
        self.h._write("proposal_v2.json", proposal)
        return proposal

    def activate(self, *, confirmation, proposal_sha256, approval_ref):
        if confirmation != CONFIRMATION or not isinstance(approval_ref, str) or len(approval_ref) < 8:
            raise ValueError("Expanded cleanup needs explicit consent and the global safety acknowledgement")
        with exclusive_file_lock(self.h.root / "operation"):
            p = self.h._read("proposal_v2.json", {})
            if p.get("sha256") != proposal_sha256 or digest(p.get("contract")) != proposal_sha256:
                raise ValueError("Cleanup proposal does not match the approved digest")
            c = p["contract"]
            if (not isinstance(c, dict) or c.get("version") != 2 or c.get("numbered_autosave") is not True
                    or c.get("max_unique_bytes") != MAX_UNIQUE_BYTES
                    or c.get("project") != str(self.h.project) or c.get("base") != str(self.h.base)
                    or c.get("sources") != self._sources() or c.get("autosave_keep") != 2
                    or c.get("cache_archives") != list(CACHE_ARCHIVES)):
                raise ValueError("Cleanup source or scope changed")
            self._published()
            activation = self.h._read("activation.json", {})
            if activation.get("enabled") is not True:
                raise ValueError("The existing owned housekeeping service must already be active")
            if activation.get("policy_version") == 2 and activation.get("expanded_proposal_sha256") == proposal_sha256:
                return {"enabled": True, "policy_version": 2, "already_active": True}
            targets = {}
            for row in c["worktrees"]:
                if row.get("blocked") or not row.get("close_approved"):
                    continue
                scan = self.scan(row["name"])
                if scan["fingerprint"] != row["fingerprint"]:
                    raise ValueError("Workspace changed after cleanup preview")
                targets[row["name"]] = {"state": "retired", "version": 2, "marked_at": self.h.clock(),
                                        "head": row["head"], "fingerprint": row["fingerprint"]}
            activation.update(policy_version=2, expanded_proposal_sha256=proposal_sha256, approval_ref=approval_ref,
                              closed_worktrees=targets, v2_scope=self._scope())
            self.h._write("activation.json", activation)
            return {"enabled": True, "policy_version": 2, "proposal_sha256": proposal_sha256}

    def tick_unlocked(self):
        if self.h._read("activation.json", {}).get("v2_scope") != self._scope():
            result = {"state": "attention", "time": self.h.clock(), "removed": [],
                      "blocked": [{"name": "policy", "reason": "Changed cleanup scope needs approval"}],
                      "autosave": {"state": "blocked"}}
            self.h._write("latest.json", result)
            return result
        try:
            published_head = self._published(); published = True
        except ValueError:
            published = False
        before = shutil.disk_usage(self.h.project).free
        state = self.h._read("state.json", {"entries": {}})
        for name, entry in self.h._read("activation.json", {}).get("closed_worktrees", {}).items():
            if name not in state["entries"]:
                state["entries"][name] = entry
        self.h._write("state.json", state)
        removed, blocked = [], []
        for name, entry in state["entries"].items():
            if entry.get("state") == "removing":
                entry["state"] = "attention"
            if entry.get("state") == "attention":
                blocked.append({"name": name, "reason": "Uncertain removal; no automatic retry"}); continue
            if entry.get("state") != "retired" or entry.get("version") != 2:
                continue
            if not published:
                blocked.append({"name": name, "reason": "Waiting for a clean, published main"}); continue
            stage = "audit"
            try:
                scan = self.scan(name)
                if scan["fingerprint"] != entry["fingerprint"]:
                    raise ValueError("Workspace changed since completion")
                stage = "preservation"
                self._preserve(scan)
                entry["preservation_verified"] = True
                stage = "recheck"
                if self.scan(name)["fingerprint"] != scan["fingerprint"]:
                    raise ValueError("Workspace changed after preservation")
                if self._published() != published_head:
                    raise ValueError("Published main changed during cleanup")
                entry["state"] = "removing"; self.h._write("state.json", state)
                path = self.h._path(name)
                stage = "normalization"
                if scan["dirty"]:
                    self._git(path, "restore", "--source=HEAD", "--staged", "--worktree", "--", ".")
                for relative in scan["untracked"]:
                    item = path / relative
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                stage = "removal"
                self._git(self.h.repo, "worktree", "remove", str(path))
                entry["state"] = "removed"; removed.append(name)
            except Exception as error:
                if entry.get("state") == "removing":
                    entry["state"] = "attention"
                entry.update(failure_stage=stage, failure_type=type(error).__name__)
                blocked.append({"name": name, "reason": "Cleanup needs review at " + stage})
            self.h._write("state.json", state)
        caches_removed = 0
        try:
            for path in self._cache_dirs():
                if not self.h.busy_probe(path):
                    shutil.rmtree(path); caches_removed += 1
        except Exception:
            blocked.append({"name": "build-cache", "reason": "Build cache cleanup needs review"})
        try:
            autosave = self.h._autosave()
        except (OSError, ValueError):
            autosave = {"state": "blocked", "reason": "Autosave changed; review required"}
        after = shutil.disk_usage(self.h.project).free
        result = {"state": "attention" if blocked or autosave["state"] != "completed" else "completed",
                  "time": self.h.clock(), "removed": removed, "blocked": blocked, "autosave": autosave,
                  "cache_dirs_removed": caches_removed, "free_before_bytes": before,
                  "free_after_bytes": after, "free_change_bytes": after - before, "policy_version": 2}
        self.h._write("latest.json", result)
        return result


def after_release_cleanup(job, *, store_root):
    """Only real canonical releases may run previously authorized maintenance."""
    from app.worktree_cleanup import PROJECT, Housekeeping
    canonical = PROJECT / "data/private/communication/luna_release"
    if Path(store_root).resolve() != canonical or not job.get("deployed") or job.get("dry_run"):
        return {"state": "not_applicable"}
    try:
        service = Housekeeping()
        activation = service._read("activation.json", {})
        if not activation.get("enabled") or activation.get("policy_version") != 2:
            return {"state": "not_enabled"}
        result = service.tick()
        return {"state": result["state"], "worktrees_removed": len(result.get("removed", [])),
                "free_change_bytes": result.get("free_change_bytes")}
    except Exception:
        return {"state": "attention"}  # Publication remains successful; no maintenance retry.
