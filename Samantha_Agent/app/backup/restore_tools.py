from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from agents import function_tool


SAMANTHA_DIR = Path(__file__).resolve().parents[2]
LOCAL_PYTHONMF_ROOT = SAMANTHA_DIR.parent
DEFAULT_BACKUP_ROOT = Path("/Volumes/SamanthaSecureBackup/SamanthaBackups")
CONFIRMATION_WORDS = ("potvrzuji", "souhlasim", "souhlasím", "ano")
RESTORE_WORDS = ("obnov", "obnovit", "restore", "nahrad", "nahraď")
SENSITIVE_CONFIRMATION_WORDS = ("citlive", "citlivé", "recovery", "sifrovane", "šifrované")
SENSITIVE_PREFIXES = (
    (".env",),
    ("Tax",),
    ("Samantha_Agent", "data", "email"),
    ("Samantha_Agent", "data", "reminders"),
    ("Samantha_Agent", "data", "session_autosave"),
)


@dataclass(frozen=True)
class BackupSnapshot:
    snapshot_id: str
    path: Path
    pythonmf_path: Path
    manifest_path: Path


@function_tool
def list_backup_snapshots(backup_root: str = "") -> str:
    """List available Samantha backup snapshots without restoring anything."""
    return list_backup_snapshots_text(backup_root=backup_root)


@function_tool
def preview_backup_restore(
    relative_path: str,
    snapshot: str = "latest",
    backup_root: str = "",
) -> str:
    """Preview a restore of one relative PythonMF path from backup without writing."""
    return preview_backup_restore_text(
        relative_path=relative_path,
        snapshot=snapshot,
        backup_root=backup_root,
    )


@function_tool
def restore_path_from_backup(
    relative_path: str,
    snapshot: str = "latest",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    backup_root: str = "",
) -> str:
    """Restore one relative PythonMF path from backup after explicit confirmation."""
    return restore_path_from_backup_text(
        relative_path=relative_path,
        snapshot=snapshot,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        backup_root=backup_root,
    )


def list_backup_snapshots_text(backup_root: str = "") -> str:
    root = _backup_root(backup_root)
    snapshots = _list_snapshots(root)
    if not snapshots:
        return f"Nenasla jsem zadne backup snapshoty v {root}."

    lines = ["Backup snapshoty:"]
    for snapshot in snapshots[-10:]:
        profile = _manifest_value(snapshot.manifest_path, "Profile") or "neznamy"
        created = _manifest_value(snapshot.manifest_path, "Created at") or "neznamy"
        lines.append(
            f"- {snapshot.snapshot_id}: profile={profile}; created={created}; path={snapshot.path}"
        )
    lines.append("Poznamka: vypis nic neobnovuje a nic nemeni.")
    return "\n".join(lines)


def preview_backup_restore_text(
    relative_path: str,
    snapshot: str = "latest",
    backup_root: str = "",
    local_root: Path = LOCAL_PYTHONMF_ROOT,
) -> str:
    path_result = _safe_relative_path(relative_path)
    if isinstance(path_result, str):
        return path_result
    rel_path = path_result

    snapshot_result = _resolve_snapshot(snapshot=snapshot, backup_root=_backup_root(backup_root))
    if isinstance(snapshot_result, str):
        return snapshot_result

    source = snapshot_result.pythonmf_path / rel_path
    target = local_root / rel_path
    lines = [
        "Nahled obnovy ze zalohy:",
        f"- snapshot: {snapshot_result.snapshot_id}",
        f"- relativni cesta: {rel_path.as_posix()}",
        f"- zdroj v zaloze: {source}",
        f"- cil v projektu: {target}",
        f"- citliva oblast: {_yes_no(_is_sensitive_path(rel_path))}",
        f"- zdroj existuje: {_yes_no(source.exists())}",
        f"- cil existuje: {_yes_no(target.exists())}",
    ]

    if source.exists():
        lines.append(f"- zdroj typ: {_path_type(source)}")
        lines.append(f"- zdroj velikost: {_path_size_text(source)}")
        lines.append(f"- zdroj zmenen: {_mtime_text(source)}")
    if target.exists():
        lines.append(f"- cil typ: {_path_type(target)}")
        lines.append(f"- cil velikost: {_path_size_text(target)}")
        lines.append(f"- cil zmenen: {_mtime_text(target)}")

    lines.extend(
        [
            "",
            "Bezpecnost:",
            "- Toto je jen nahled, nic nebylo zapsano.",
            "- Obnova vyzaduje samostatne potvrzeni v aktualni zprave.",
            "- Pred prepisem cilove cesty se vzdy vytvori .before_restore kopie.",
        ]
    )
    if _is_sensitive_path(rel_path):
        lines.append(
            "- Protoze jde o citlivou oblast, potvrzeni musi obsahovat i slovo "
            "`citlive` nebo `recovery`."
        )
    return "\n".join(lines)


def restore_path_from_backup_text(
    relative_path: str,
    snapshot: str = "latest",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    backup_root: str = "",
    local_root: Path = LOCAL_PYTHONMF_ROOT,
) -> str:
    path_result = _safe_relative_path(relative_path)
    if isinstance(path_result, str):
        return path_result
    rel_path = path_result

    snapshot_result = _resolve_snapshot(snapshot=snapshot, backup_root=_backup_root(backup_root))
    if isinstance(snapshot_result, str):
        return snapshot_result

    if not user_confirmed or not has_explicit_restore_confirmation(
        relative_path=rel_path.as_posix(),
        snapshot_id=snapshot_result.snapshot_id,
        confirmation_text=confirmation_text,
        sensitive=_is_sensitive_path(rel_path),
    ):
        return _restore_confirmation_message(rel_path, snapshot_result.snapshot_id)

    source = snapshot_result.pythonmf_path / rel_path
    target = local_root / rel_path
    if not source.exists():
        return f"Zdroj v zaloze neexistuje: {source}. Nic nebylo zapsano."

    backup_target = _backup_existing_target(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if target.exists():
            if target.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                return (
                    f"Nelze obnovit slozku do existujiciho souboru: {target}. "
                    "Bezpecnostni kopie aktualniho souboru zustala zachovana."
                )
        else:
            shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target, follow_symlinks=False)

    lines = [
        "Obnova ze zalohy dokoncena:",
        f"- snapshot: {snapshot_result.snapshot_id}",
        f"- obnovena cesta: {rel_path.as_posix()}",
        f"- zdroj: {source}",
        f"- cil: {target}",
    ]
    if backup_target is not None:
        lines.append(f"- puvodni cil ulozen jako: {backup_target}")
    else:
        lines.append("- puvodni cil neexistoval, nebylo co zalohovat pred obnovou")
    lines.append("Nic nebylo mazano ze zalohy.")
    return "\n".join(lines)


def has_explicit_restore_confirmation(
    relative_path: str,
    snapshot_id: str,
    confirmation_text: str,
    sensitive: bool = False,
) -> bool:
    normalized = confirmation_text.casefold()
    path_ok = relative_path.casefold() in normalized
    snapshot_ok = snapshot_id.casefold() in normalized or "latest" in normalized
    base_ok = (
        path_ok
        and snapshot_ok
        and any(word in normalized for word in CONFIRMATION_WORDS)
        and any(word in normalized for word in RESTORE_WORDS)
    )
    if not base_ok:
        return False
    if sensitive:
        return any(word in normalized for word in SENSITIVE_CONFIRMATION_WORDS)
    return True


def _restore_confirmation_message(rel_path: Path, snapshot_id: str) -> str:
    message = (
        "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
        "Potvrzeni musi obsahovat relativni cestu, snapshot id nebo slovo latest, "
        "a jasny souhlas s obnovou/nahradou."
    )
    example = (
        f"Priklad: Potvrzuji obnovu {rel_path.as_posix()} "
        f"ze snapshotu {snapshot_id}."
    )
    if _is_sensitive_path(rel_path):
        example += " Potvrzuji, ze jde o citlivou recovery obnovu."
    return f"{message}\n{example}\nBez potvrzeni na disk nic nezapisuji."


def _safe_relative_path(relative_path: str) -> Path | str:
    raw = str(relative_path or "").strip()
    if not raw:
        return "Chybi relativni cesta uvnitr PythonMF."
    raw = raw.replace("\\", "/")
    path = Path(raw)
    if path.is_absolute():
        return "Odmítnuto: cesta musi byt relativni uvnitr PythonMF, ne absolutni."
    if raw.startswith("~"):
        return "Odmítnuto: cesta nesmi zacinat v domovske zkratce ~."

    parts = path.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        return "Odmítnuto: cesta nesmi obsahovat prazdne casti, tecku nebo `..`."
    return Path(*parts)


def _backup_root(backup_root: str) -> Path:
    return Path(backup_root).expanduser() if backup_root else DEFAULT_BACKUP_ROOT


def _list_snapshots(backup_root: Path) -> list[BackupSnapshot]:
    snapshots_dir = backup_root / "snapshots"
    if not snapshots_dir.exists():
        return []

    snapshots: list[BackupSnapshot] = []
    for path in sorted(item for item in snapshots_dir.iterdir() if item.is_dir()):
        pythonmf_path = path / "PythonMF"
        if not pythonmf_path.exists():
            continue
        snapshots.append(
            BackupSnapshot(
                snapshot_id=path.name,
                path=path,
                pythonmf_path=pythonmf_path,
                manifest_path=path / "backup_manifest.txt",
            )
        )
    return snapshots


def _resolve_snapshot(snapshot: str, backup_root: Path) -> BackupSnapshot | str:
    snapshots = _list_snapshots(backup_root)
    if not snapshots:
        return f"Nenasla jsem zadne backup snapshoty v {backup_root / 'snapshots'}."

    snapshot_id = (snapshot or "latest").strip()
    if snapshot_id == "latest":
        return snapshots[-1]

    matches = [item for item in snapshots if item.snapshot_id == snapshot_id]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return f"Snapshot nenalezen: {snapshot_id}."
    return f"Snapshot neni jednoznacny: {snapshot_id}."


def _backup_existing_target(target: Path) -> Path | None:
    if not target.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_target = target.with_name(f"{target.name}.before_restore_{stamp}")
    counter = 1
    while backup_target.exists():
        backup_target = target.with_name(f"{target.name}.before_restore_{stamp}_{counter}")
        counter += 1
    shutil.move(str(target), str(backup_target))
    return backup_target


def _is_sensitive_path(path: Path) -> bool:
    parts = path.parts
    if parts and (parts[-1] == ".env" or parts[-1].startswith(".env.")):
        return True
    return any(parts[: len(prefix)] == prefix for prefix in SENSITIVE_PREFIXES)


def _path_type(path: Path) -> str:
    if path.is_dir():
        return "slozka"
    if path.is_file():
        return "soubor"
    if path.is_symlink():
        return "symlink"
    return "jine"


def _path_size_text(path: Path) -> str:
    try:
        if path.is_dir():
            file_count = sum(1 for item in path.rglob("*") if item.is_file())
            return f"{file_count} souboru"
        return f"{path.stat().st_size} B"
    except OSError:
        return "nelze zjistit"


def _mtime_text(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return "nelze zjistit"


def _manifest_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    prefix = f"{key}:"
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(prefix):
                return line.removeprefix(prefix).strip()
    except OSError:
        return ""
    return ""


def _yes_no(value: Any) -> str:
    return "ano" if bool(value) else "ne"
