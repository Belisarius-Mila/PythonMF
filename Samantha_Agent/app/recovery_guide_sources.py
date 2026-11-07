"""Frozen, public documentation input for the recovery-guide pilot.

No filesystem crawl into private runtime data, no model call and no writes.
The inventory is a proposal until its exact digest is approved.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

TEXT_SUFFIXES = {".md", ".txt", ".rst"}
SENSITIVE_PARTS = {"private", "session_autosave", "transcripts", "sessions", "node_modules", ".git", ".venv"}
SECRET = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{20,}")
ROOT = Path(__file__).resolve().parents[1]
GUIDE_NAME = "OBNOVA_SAMANTHY_NOVY_MAC.txt"


def digest(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def reject_secrets(text: str) -> None:
    if SECRET.search(text) or "\x00" in text:
        raise ValueError("Podklad obsahuje zakázaný obsah; obsah se nevypisuje.")


@dataclass(frozen=True)
class Source:
    path: str
    sha256: str
    text: str
    authority: str


@dataclass(frozen=True)
class Snapshot:
    head: str
    original: Source
    sources: tuple[Source, ...]
    scopes: tuple[str, ...] = ()
    excluded_text_files: int = 0

    @property
    def sha256(self) -> str:
        return digest(canonical_json(asdict(self)))

    def receipt(self) -> dict:
        return {"head": self.head, "snapshot_sha256": self.sha256,
                "original_sha256": self.original.sha256,
                "source_count": len(self.sources),
                "input_bytes": sum(len(s.text.encode()) for s in (self.original, *self.sources)),
                "sources": [{"path": s.path, "sha256": s.sha256, "authority": s.authority}
                            for s in self.sources],
                "scopes": list(self.scopes), "excluded_text_files": self.excluded_text_files,
                "coverage": "inventory_only", "approval_required": True}


def eligible(name: str, prefix: str = "") -> bool:
    p = PurePosixPath(name)
    relative = str(p.relative_to(prefix)) if prefix else name
    parts = set(p.parts)
    return (not p.is_absolute() and ".." not in parts and not parts & SENSITIVE_PARTS
            and not any(x.startswith(".") for x in p.parts)
            and not re.search(r"(?:transcript|session_log|auth\.json|credentials)", name, re.I)
            and p.suffix.lower() in TEXT_SUFFIXES
            and (relative.startswith(("memory/", "docs/", "camino/"))
                 or "/docs/" in relative or relative.startswith("iOS/")
                 or p.name in {"README.md", "AGENTS.md"}))


def collect(original: Path, root: Path = ROOT, *,
            companion_scopes: tuple[str, ...] = ("docs/", "MatysekANJ/docs/", "iOS/")) -> Snapshot:
    """Read the entire original FIRST, then all selected tracked, clean documents.

    Git HEAD freezes provenance, while byte comparison rejects tracked local
    edits. Untracked/ignored content never silently joins an approved corpus.
    Receipt declares the exact scopes and counts every excluded text path.
    """
    root = root.resolve(strict=True)
    if original.is_symlink() or not original.is_file():
        raise ValueError("Původní návod musí být obyčejný soubor.")
    raw = original.read_bytes()
    original_text = raw.decode("utf-8", errors="strict")
    reject_secrets(original_text)
    if not original_text.strip():
        raise ValueError("Prázdný původní návod.")

    def git(*args: str) -> bytes:
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    top = Path(git("rev-parse", "--show-toplevel").decode().strip())
    prefix = root.relative_to(top).as_posix()
    prefix = "" if prefix == "." else prefix + "/"
    if any(PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts or not p.endswith("/")
           for p in companion_scopes):
        raise ValueError("Neplatný rozsah připojené dokumentace.")
    head = git("rev-parse", "HEAD").decode().strip()
    names = git("ls-tree", "-r", "--name-only", "-z", "--full-tree", head).decode().split("\0")
    rows = []
    excluded = 0
    for name in sorted(n for n in names if n and PurePosixPath(n).suffix.lower() in TEXT_SUFFIXES):
        selected = (name.startswith(prefix) or name.startswith(companion_scopes)
                    or PurePosixPath(name).name in {"AGENTS.md", "README.md"})
        if not selected:
            excluded += 1
            continue
        if not eligible(name, prefix if name.startswith(prefix) else ""):
            excluded += 1
            continue
        path = top / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("Symlink v dokumentačním korpusu.")
        content = path.read_bytes()
        if content != git("show", f"{head}:{name}"):
            raise ValueError("Dokumentace má necommitovanou změnu; nejprve zmrazit podklady.")
        text = content.decode("utf-8", errors="strict")
        reject_secrets(text)
        # A git document is evidence of documentation, never live deployment.
        authority = "historical_or_mixed" if re.search(r"/(reports|handoffs|tvbcp)/", name) else "documented_not_live"
        rows.append(Source(name, digest(content), text, authority))
    if not rows or git("rev-parse", "HEAD").decode().strip() != head:
        raise ValueError("Korpus není stabilní nebo je prázdný.")
    if original.read_bytes() != raw:
        raise ValueError("Původní návod se během inventury změnil.")
    return Snapshot(head, Source("original_guide", digest(raw), original_text, "previous_version"), tuple(rows),
                    (prefix + "{memory,docs,camino}/", "**/{AGENTS,README}.md", *companion_scopes), excluded)


def batches(snapshot: Snapshot, count_tokens: Callable[[str], int], *, input_limit: int,
            output_reserve: int, max_calls: int) -> list[dict]:
    """Exact caller-supplied tokenizer; whole files, no truncation or estimates.

    Synthesis is reserved separately by the controller. A too-large whole file
    requires a new reviewed plan; it never disappears from coverage.
    """
    if input_limit <= 0 or output_reserve <= 0 or max_calls < 2:
        raise ValueError("Neplatné limity.")
    result: list[dict] = []
    current: list[Source] = []

    def payload(rows: list[Source]) -> dict:
        return {"original": asdict(snapshot.original), "sources": [asdict(s) for s in rows]}

    def fits(rows: list[Source]) -> bool:
        return count_tokens(canonical_json(payload(rows))) + output_reserve <= input_limit

    for source in snapshot.sources:
        if not fits([source]):
            raise ValueError("Celý soubor se nevejde do dávky; rozsah se nekrátí.")
        if current and not fits([*current, source]):
            result.append(payload(current))
            current = []
        current.append(source)
    if current:
        result.append(payload(current))
    if len(result) + 1 > max_calls:
        raise ValueError("Počet dávek včetně syntézy překročil limit.")
    return result


def target_preview(home: Path, pythonmf: Path) -> dict:
    cloud = home / "Library/Mobile Documents/com~apple~CloudDocs/Documents"
    return {"local": str(pythonmf / GUIDE_NAME), "icloud": str(cloud / GUIDE_NAME),
            "icloud_resolved_parent": str(cloud.resolve()),
            "documents_alias": cloud.is_symlink(),
            "cloud_upload_verified": False, "writes": False,
            "migration": "Preserve original Desktop/root-iCloud versions; publish only after acceptance."}
