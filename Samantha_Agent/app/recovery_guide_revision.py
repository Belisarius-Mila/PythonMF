"""Read a recovery corpus from a pinned Git object, never another worktree.

No checkout, archive extraction, ref changes, model, network or writes. This
keeps a concurrent main writer separate from Data's isolated pilot checkout.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
import subprocess

from app.recovery_guide_sources import (ROOT, TEXT_SUFFIXES, Snapshot, Source,
                                       digest, eligible, reject_secrets)


def collect_revision(original: Path, commit: str, root: Path = ROOT, *,
                     companion_scopes: tuple[str, ...] = ("docs/", "MatysekANJ/docs/", "iOS/"),
                     project_only: bool = False) -> Snapshot:
    """Read whole original FIRST, then complete eligible blobs at one commit.

    The commit is already a full SHA, not a moving ref. A caller can compare
    its source ref afterwards; a new ref never silently substitutes new input.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("revision_full_commit_required")
    if original.is_symlink() or not original.is_file():
        raise ValueError("revision_original_not_regular")
    raw = original.read_bytes()
    original_text = raw.decode("utf-8", errors="strict")
    reject_secrets(original_text)
    if not original_text.strip():
        raise ValueError("revision_original_empty")
    if any(PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts or not p.endswith("/")
           for p in companion_scopes):
        raise ValueError("revision_invalid_companion_scope")

    def git(*args, data=None):
        return subprocess.run(["git", "-C", str(root), *args], input=data,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

    top = Path(git("rev-parse", "--show-toplevel").decode().strip())
    prefix = root.resolve(strict=True).relative_to(top.resolve(strict=True)).as_posix()
    prefix = "" if prefix == "." else prefix + "/"
    if git("rev-parse", "--verify", commit + "^{commit}").decode().strip() != commit:
        raise ValueError("revision_not_commit")
    tree = git("ls-tree", "-r", "-z", "--full-tree", commit)
    rows, excluded = [], 0
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, name_raw = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        name = name_raw.decode("utf-8", errors="strict")
        if PurePosixPath(name).suffix.lower() not in TEXT_SUFFIXES:
            continue
        selected = name.startswith(prefix) or (not project_only and
            (name.startswith(companion_scopes) or PurePosixPath(name).name in {"AGENTS.md", "README.md"}))
        if not selected or not eligible(name, prefix if name.startswith(prefix) else ""):
            excluded += 1
            continue
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("revision_non_regular_document")
        rows.append((name, oid))
    rows.sort()
    if not rows:
        raise ValueError("revision_empty_corpus")
    # One cat-file process, no commands or files from the selected revision run.
    objects = git("cat-file", "--batch", data="".join(oid + "\n" for _, oid in rows).encode())
    offset, sources = 0, []
    for name, oid in rows:
        end = objects.index(b"\n", offset)
        returned, kind, size = objects[offset:end].decode().split()
        if returned != oid or kind != "blob":
            raise ValueError("revision_object_mismatch")
        start, size = end + 1, int(size)
        content = objects[start:start+size]
        if len(content) != size or objects[start+size:start+size+1] != b"\n":
            raise ValueError("revision_incomplete_blob")
        offset = start + size + 1
        text = content.decode("utf-8", errors="strict")
        reject_secrets(text)
        authority = "historical_or_mixed" if re.search(r"/(reports|handoffs|tvbcp)/", name) else "documented_not_live"
        sources.append(Source(name, digest(content), text, authority))
    if offset != len(objects) or original.read_bytes() != raw:
        raise ValueError("revision_input_changed")
    scopes = ((prefix + "{memory,docs,camino,AGENTS,README}/",) if project_only else
              (prefix + "{memory,docs,camino}/", "**/{AGENTS,README}.md", *companion_scopes))
    return Snapshot(commit, Source("original_guide", digest(raw), original_text, "previous_version"),
        tuple(sources), scopes, excluded)
