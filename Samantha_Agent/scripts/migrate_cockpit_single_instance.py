#!/usr/bin/env python3
"""Safely replace the second Tailscale Cockpit process with a TCP proxy."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


PROJECT_DIR = Path(__file__).resolve().parents[1]
TAILSCALE_APP_BIN = Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")
LEGACY_LABEL = "com.miloslavfalta.samantha.cockpit.tailscale"
LEGACY_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LEGACY_LABEL}.plist"
LOCAL_BASE_URL = "http://127.0.0.1:8770"
COCKPIT_PORT = 8770


class MigrationError(RuntimeError):
    pass


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=PROJECT_DIR, text=True, capture_output=True, check=False)


def tailscale_binary() -> Path:
    configured = os.environ.get("SAMANTHA_TAILSCALE_BIN", "").strip()
    candidate = Path(configured).expanduser() if configured else TAILSCALE_APP_BIN
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise MigrationError(f"Tailscale CLI nebylo nalezeno: {candidate}")
    return candidate


def tailscale_ipv4(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
    binary: Path | None = None,
) -> str:
    result = runner([str(binary or tailscale_binary()), "ip", "-4"])
    if result.returncode != 0:
        raise MigrationError("Nelze zjistit Tailscale IPv4 adresu.")
    address = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
    if not address:
        raise MigrationError("Tailscale nevratilo IPv4 adresu.")
    return address


def fetch_health(base_url: str, *, timeout: float = 3.0) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/api/server/health", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) and payload.get("ok") else None


def same_cockpit_process(local: dict[str, Any] | None, remote: dict[str, Any] | None) -> bool:
    if not local or not remote:
        return False
    local_server = local.get("server") if isinstance(local.get("server"), dict) else {}
    remote_server = remote.get("server") if isinstance(remote.get("server"), dict) else {}
    return bool(
        local_server.get("pid")
        and local_server.get("pid") == remote_server.get("pid")
        and local_server.get("code_stamp")
        and local_server.get("code_stamp") == remote_server.get("code_stamp")
    )


def wait_for_health(
    base_url: str,
    *,
    timeout: float = 30.0,
    interval: float = 0.5,
    health_loader: Callable[[str], dict[str, Any] | None] = fetch_health,
) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        health = health_loader(base_url)
        if health:
            return health
        time.sleep(interval)
    return None


def bootout_legacy_service(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
) -> None:
    domain = f"gui/{os.getuid()}"
    runner(["launchctl", "bootout", domain, str(LEGACY_PLIST)])


def bootstrap_legacy_service(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
) -> None:
    if not LEGACY_PLIST.exists():
        raise MigrationError(f"Rollback plist chybi: {LEGACY_PLIST}")
    domain = f"gui/{os.getuid()}"
    bootstrap = runner(["launchctl", "bootstrap", domain, str(LEGACY_PLIST)])
    if bootstrap.returncode != 0 and "already loaded" not in (bootstrap.stderr or "").casefold():
        raise MigrationError("Legacy Tailscale Cockpit launchd se nepodarilo obnovit.")
    runner(["launchctl", "enable", f"{domain}/{LEGACY_LABEL}"])
    runner(["launchctl", "kickstart", "-k", f"{domain}/{LEGACY_LABEL}"])


def configure_tcp_proxy(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
    binary: Path | None = None,
    port: int = COCKPIT_PORT,
) -> None:
    result = runner(
        [
            str(binary or tailscale_binary()),
            "serve",
            "--bg",
            "--yes",
            "--tcp",
            str(port),
            f"tcp://127.0.0.1:{port}",
        ]
    )
    if result.returncode != 0:
        detail = " ".join((result.stderr or result.stdout or "").split())
        raise MigrationError(f"Tailscale TCP proxy se nepodarilo zapnout: {detail[:300]}")


def disable_tcp_proxy(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
    binary: Path | None = None,
    port: int = COCKPIT_PORT,
) -> None:
    runner([str(binary or tailscale_binary()), "serve", f"--tcp={port}", "off"])


def rollback_to_legacy(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
    binary: Path | None = None,
) -> None:
    disable_tcp_proxy(runner=runner, binary=binary)
    bootstrap_legacy_service(runner=runner)


def migrate_to_single_instance(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
    health_loader: Callable[[str], dict[str, Any] | None] = fetch_health,
    wait_loader: Callable[[str], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    binary = tailscale_binary()
    address = tailscale_ipv4(runner=runner, binary=binary)
    remote_base_url = f"http://{address}:{COCKPIT_PORT}"
    local_health = health_loader(LOCAL_BASE_URL)
    if not local_health:
        raise MigrationError("Lokalni Cockpit neodpovida; migraci nespoustim.")

    remote_before = health_loader(remote_base_url)
    if same_cockpit_process(local_health, remote_before):
        return {"ok": True, "status": "already_single", "remote_base_url": remote_base_url}

    bootout_legacy_service(runner=runner)
    try:
        configure_tcp_proxy(runner=runner, binary=binary)
        remote_after = (wait_loader or (lambda url: wait_for_health(url, health_loader=health_loader)))(remote_base_url)
        if not same_cockpit_process(local_health, remote_after):
            raise MigrationError("Vzdaleny Cockpit neukazuje stejny proces jako lokalni instance.")
    except Exception as exc:
        try:
            rollback_to_legacy(runner=runner, binary=binary)
        except Exception as rollback_exc:
            raise MigrationError(f"Migrace selhala a rollback se nepodaril: {rollback_exc}") from exc
        if isinstance(exc, MigrationError):
            raise
        raise MigrationError(str(exc)) from exc

    return {
        "ok": True,
        "status": "single_instance",
        "remote_base_url": remote_base_url,
        "pid": local_health.get("server", {}).get("pid"),
        "legacy_plist_preserved": LEGACY_PLIST.exists(),
    }


def single_instance_status(
    *,
    runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
    health_loader: Callable[[str], dict[str, Any] | None] = fetch_health,
) -> dict[str, Any]:
    binary = tailscale_binary()
    address = tailscale_ipv4(runner=runner, binary=binary)
    remote_base_url = f"http://{address}:{COCKPIT_PORT}"
    local = health_loader(LOCAL_BASE_URL)
    remote = health_loader(remote_base_url)
    return {
        "ok": bool(local and remote),
        "single_instance": same_cockpit_process(local, remote),
        "local_pid": (local or {}).get("server", {}).get("pid"),
        "remote_pid": (remote or {}).get("server", {}).get("pid"),
        "remote_base_url": remote_base_url,
        "legacy_plist_preserved": LEGACY_PLIST.exists(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate Samantha Cockpit to one Python server process.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Replace legacy Tailscale server with TCP proxy.")
    mode.add_argument("--rollback", action="store_true", help="Restore the preserved legacy Tailscale launchd service.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.apply:
            result = migrate_to_single_instance()
        elif args.rollback:
            binary = tailscale_binary()
            rollback_to_legacy(binary=binary)
            result = {"ok": True, "status": "legacy_restored"}
        else:
            result = single_instance_status()
    except MigrationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
