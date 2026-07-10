from __future__ import annotations

import hashlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def default_cockpit_code_stamp_paths(project_root: Path = PROJECT_ROOT) -> tuple[Path, ...]:
    app_paths = sorted((project_root / "app").rglob("*.py"), key=lambda path: str(path))
    return (*app_paths, project_root / "scripts" / "cockpit_server.py")


COCKPIT_CODE_STAMP_PATHS = default_cockpit_code_stamp_paths()


def cockpit_code_stamp(paths: tuple[Path, ...] = COCKPIT_CODE_STAMP_PATHS) -> str:
    digest = hashlib.sha256()
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            digest.update(f"{path}:missing\n".encode("utf-8"))
            continue
        digest.update(f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}\n".encode("utf-8"))
    return digest.hexdigest()[:16]
