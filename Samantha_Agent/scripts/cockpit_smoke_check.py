#!/usr/bin/env python3
"""Read-only smoke check for the local Samantha Cockpit."""

from __future__ import annotations

import argparse
import http.client
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8770"
DEFAULT_CHECKS = (
    ("home", "/"),
    ("server_health", "/api/server/health"),
    ("status", "/api/status"),
    ("recovery", "/api/recovery/status"),
)


@dataclass(frozen=True)
class SmokeResult:
    name: str
    path: str
    ok: bool
    status_code: int | None
    message: str


def fetch_url(url: str, timeout: float) -> tuple[int, bytes]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, response.read()


def check_endpoint(
    base_url: str,
    name: str,
    path: str,
    *,
    timeout: float,
) -> SmokeResult:
    url = base_url.rstrip("/") + path
    try:
        status_code, body = fetch_url(url, timeout)
    except urllib.error.URLError as exc:
        return SmokeResult(name, path, False, None, str(exc.reason if hasattr(exc, "reason") else exc))
    except (TimeoutError, http.client.RemoteDisconnected) as exc:
        return SmokeResult(name, path, False, None, str(exc))

    if status_code < 200 or status_code >= 300:
        return SmokeResult(name, path, False, status_code, f"HTTP {status_code}")

    if path.startswith("/api/"):
        try:
            payload: Any = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return SmokeResult(name, path, False, status_code, f"invalid JSON: {exc}")
        if not isinstance(payload, dict):
            return SmokeResult(name, path, False, status_code, "JSON response is not an object")
        if path == "/api/server/health":
            server = payload.get("server")
            if not isinstance(server, dict) or not server.get("code_stamp"):
                return SmokeResult(name, path, False, status_code, "invalid server health")
        if path == "/api/status":
            for required_key in ("generated_at", "backup_status", "voice_bridge"):
                if required_key not in payload:
                    return SmokeResult(name, path, False, status_code, f"missing {required_key}")
            backup_status = payload.get("backup_status")
            if not isinstance(backup_status, dict) or "status" not in backup_status:
                return SmokeResult(name, path, False, status_code, "invalid backup_status")
    elif not body:
        return SmokeResult(name, path, False, status_code, "empty response body")

    return SmokeResult(name, path, True, status_code, "OK")


def run_smoke_check(base_url: str, timeout: float) -> list[SmokeResult]:
    return [
        check_endpoint(base_url, name, path, timeout=timeout)
        for name, path in DEFAULT_CHECKS
    ]


def format_results(results: list[SmokeResult]) -> str:
    lines = ["Samantha Cockpit smoke check:"]
    for result in results:
        status = "OK" if result.ok else "FAIL"
        code = f" HTTP {result.status_code}" if result.status_code is not None else ""
        lines.append(f"- {status} {result.name} {result.path}{code}: {result.message}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only smoke check for Samantha Cockpit.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    results = run_smoke_check(args.base_url, args.timeout)
    print(format_results(results))
    return 0 if all(item.ok for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
