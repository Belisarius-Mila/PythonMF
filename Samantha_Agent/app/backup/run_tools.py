from __future__ import annotations

import subprocess
from pathlib import Path

from agents import function_tool


SAMANTHA_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BACKUP_SCRIPT = SAMANTHA_DIR / "scripts" / "backup_samantha.command"
DEFAULT_BACKUP_ROOT = Path("/Volumes/SamanthaSecureBackup/SamanthaBackups")


@function_tool
def run_project_backup(mode: str = "execute", profile: str = "recovery", target: str = "") -> str:
    """Run the configured PythonMF/Samantha backup script."""
    return run_project_backup_text(mode=mode, profile=profile, target=target)


def run_project_backup_text(
    mode: str = "execute",
    profile: str = "recovery",
    target: str = "",
    script_path: Path = DEFAULT_BACKUP_SCRIPT,
) -> str:
    mode = (mode or "execute").strip().casefold()
    profile = (profile or "recovery").strip().casefold()
    backup_root = Path(target).expanduser() if target else DEFAULT_BACKUP_ROOT

    if mode not in {"execute", "dry-run"}:
        return "Zaloha nespustena: mode musi byt `execute` nebo `dry-run`."
    if profile not in {"safe", "recovery"}:
        return "Zaloha nespustena: profile musi byt `safe` nebo `recovery`."
    if not script_path.exists():
        return f"Zaloha nespustena: chybi skript {script_path}."
    if not script_path.is_file():
        return f"Zaloha nespustena: cesta neni soubor {script_path}."
    if not _is_safe_backup_target(backup_root, profile):
        return (
            "Zaloha nespustena: recovery profil smi standardne zapisovat jen do "
            f"{DEFAULT_BACKUP_ROOT}. Pripoj sifrovany kontejner SamanthaSecureBackup."
        )
    if mode == "execute" and not backup_root.parent.exists():
        return (
            "Zaloha nespustena: neni pripojeny cilovy svazek "
            f"{backup_root.parent}. Pripoj externi disk a sifrovany kontejner."
        )

    command = [
        str(script_path),
        f"--{mode}",
        "--profile",
        profile,
        "--target",
        str(backup_root),
    ]
    result = subprocess.run(
        command,
        cwd=str(SAMANTHA_DIR),
        text=True,
        capture_output=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    output = _tail_lines(output, max_lines=80)

    if result.returncode != 0:
        return (
            "Zaloha nedobehla uspesne.\n"
            f"- exit code: {result.returncode}\n"
            f"- prikaz: {' '.join(command)}\n\n"
            f"{output}"
        ).strip()

    heading = "Ostra zaloha dokoncena" if mode == "execute" else "Dry-run zalohy dokoncen"
    return (
        f"{heading}.\n"
        f"- profile: {profile}\n"
        f"- target: {backup_root}\n\n"
        f"{output}"
    ).strip()


def _is_safe_backup_target(backup_root: Path, profile: str) -> bool:
    if profile != "recovery":
        return True
    try:
        return backup_root.resolve().is_relative_to(DEFAULT_BACKUP_ROOT.parent.resolve())
    except FileNotFoundError:
        return str(backup_root).startswith(str(DEFAULT_BACKUP_ROOT.parent) + "/")


def _tail_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    omitted = len(lines) - max_lines
    return "\n".join([f"... zkraceno, vynechano {omitted} radku ...", *lines[-max_lines:]])
