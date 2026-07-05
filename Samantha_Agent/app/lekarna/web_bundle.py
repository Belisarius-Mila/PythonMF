from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


AGENT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = AGENT_ROOT.parent
DEFAULT_EXPORT_SCRIPT = AGENT_ROOT / "scripts" / "export_lekarna_web_private_data.py"
DEFAULT_ENCRYPT_SCRIPT = AGENT_ROOT / "scripts" / "encrypt_lekarna_web_bundle.py"
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "docs" / "lekarna" / "private-data" / "lekarna.json"
DEFAULT_ENCRYPTED_PATH = PROJECT_ROOT / "docs" / "lekarna" / "encrypted-data" / "lekarna.enc.json"
KEYCHAIN_SERVICE = "SamanthaLekarnaWebBundle"
PASSWORD_ENV = "LEKARNA_WEB_BUNDLE_PASSWORD"


@dataclass(frozen=True)
class LekarnaWebBundleRefreshResult:
    export_path: Path | None
    encrypted_path: Path | None
    encrypted: bool
    warnings: tuple[str, ...]


def refresh_lekarna_web_bundle(
    *,
    export_script: Path = DEFAULT_EXPORT_SCRIPT,
    encrypt_script: Path = DEFAULT_ENCRYPT_SCRIPT,
    export_path: Path = DEFAULT_EXPORT_PATH,
    encrypted_path: Path = DEFAULT_ENCRYPTED_PATH,
    python_executable: Path | None = None,
    keychain_service: str = KEYCHAIN_SERVICE,
) -> LekarnaWebBundleRefreshResult:
    """Refresh private web export and encrypted bundle when a local keychain password exists."""
    warnings: list[str] = []
    python = python_executable or AGENT_ROOT / ".venv" / "bin" / "python"

    export_completed = subprocess.run(
        [str(python), str(export_script)],
        cwd=str(AGENT_ROOT),
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if export_completed.returncode != 0:
        warning = _short_process_warning("Web export se nepodarilo obnovit", export_completed)
        return LekarnaWebBundleRefreshResult(
            export_path=None,
            encrypted_path=None,
            encrypted=False,
            warnings=(warning,),
        )

    password = _read_keychain_password(keychain_service)
    if not password:
        warnings.append(
            "Web export byl obnoven, ale sifrovany balicek nebyl prepsan: "
            f"v macOS Keychain neni polozka `{keychain_service}`."
        )
        return LekarnaWebBundleRefreshResult(
            export_path=export_path,
            encrypted_path=None,
            encrypted=False,
            warnings=tuple(warnings),
        )

    env = os.environ.copy()
    env[PASSWORD_ENV] = password
    encrypt_completed = subprocess.run(
        [str(python), str(encrypt_script), "--password-env", PASSWORD_ENV],
        cwd=str(AGENT_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=env,
    )
    if encrypt_completed.returncode != 0:
        warnings.append(_short_process_warning("Sifrovany webovy balicek se nepodarilo obnovit", encrypt_completed))
        return LekarnaWebBundleRefreshResult(
            export_path=export_path,
            encrypted_path=None,
            encrypted=False,
            warnings=tuple(warnings),
        )

    return LekarnaWebBundleRefreshResult(
        export_path=export_path,
        encrypted_path=encrypted_path,
        encrypted=True,
        warnings=tuple(warnings),
    )


def _read_keychain_password(service: str) -> str:
    completed = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", service],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.rstrip("\n")


def _short_process_warning(prefix: str, completed: subprocess.CompletedProcess[str], limit: int = 400) -> str:
    details = " ".join(part.strip() for part in (completed.stderr, completed.stdout) if part and part.strip())
    if len(details) > limit:
        details = details[: limit - 3].rstrip() + "..."
    return f"{prefix}: {details or 'bez detailu'}"
