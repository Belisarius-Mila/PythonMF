"""Runtime path helpers for MultiLO on macOS and local development."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

APP_NAME = "MultiLO"
DATA_FILES = ("vocab_master.csv", "users.csv", "user_item_prefs.csv")
OPTIONAL_DATA_FILES = ("progress.json",)


def _is_macos_app_runtime() -> bool:
    exe = Path(sys.executable or "").resolve()
    file_path = Path(__file__).resolve()
    exe_str = str(exe)
    file_str = str(file_path)
    return (
        ".app/Contents/MacOS/" in exe_str
        or ".app/Contents/Resources/" in file_str
        or ".app/Contents/" in exe_str
    )


def _resource_base_dir() -> Path:
    return Path(__file__).resolve().parent


def _app_support_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / APP_NAME


def _app_container_dir() -> Path:
    exe_dir = Path(sys.executable).resolve().parent
    return exe_dir.parent.parent.parent.resolve()


def _app_parent_dir() -> Path:
    return _app_container_dir().parent.resolve()


def _source_candidates(name: str) -> list[Path]:
    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / name)
    candidates.append(_resource_base_dir() / name)
    if getattr(sys, "frozen", False) or _is_macos_app_runtime():
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend(
            [
                _app_container_dir() / name,
                _app_parent_dir() / name,
                exe_dir / name,
            ]
        )
    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


def _ensure_file_in_support_dir(name: str) -> Path:
    support_dir = _app_support_dir()
    support_dir.mkdir(parents=True, exist_ok=True)
    target = support_dir / name
    if target.exists():
        return target
    for source in _source_candidates(name):
        if source.exists():
            shutil.copy2(source, target)
            return target
    return target


def resolve_data_dir() -> Path:
    if not (getattr(sys, "frozen", False) or _is_macos_app_runtime()):
        return _resource_base_dir()
    for name in DATA_FILES:
        _ensure_file_in_support_dir(name)
    return _app_support_dir()


def resolve_prefs_path() -> Path:
    if not (getattr(sys, "frozen", False) or _is_macos_app_runtime()):
        return _resource_base_dir() / "user_item_prefs.csv"
    return _ensure_file_in_support_dir("user_item_prefs.csv")


def resolve_progress_path() -> Path:
    if not (getattr(sys, "frozen", False) or _is_macos_app_runtime()):
        return _resource_base_dir() / "progress.json"
    return _ensure_file_in_support_dir("progress.json")


def resolve_assets_root() -> Path:
    return _resource_base_dir() / "Foto_normalized"


def resolve_cockpit_icon_dir() -> Path:
    return _resource_base_dir() / "cockpit_icons"
