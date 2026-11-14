"""Redirect only legacy browser entry to the existing private HTTPS proxy.

Discovery reads Serve configuration; it never enables TLS or changes Tailscale.
The private hostname is cached in memory only, not stored in project files.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlsplit


LEGACY_PORT = 8770
TAILSCALE_BINARY = Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")


def private_https_origin(status: object) -> str | None:
    """Accept one verified private HTTPS root proxy to this Cockpit."""
    if not isinstance(status, dict):
        return None
    tcp, web, funnel = status.get("TCP"), status.get("Web"), status.get("AllowFunnel", {})
    if not isinstance(tcp, dict) or not isinstance(web, dict) or not isinstance(funnel, dict):
        return None
    if any(value is not False for value in funnel.values()):
        return None
    listener = tcp.get("443")
    if not isinstance(listener, dict) or listener.get("HTTPS") is not True:
        return None
    origins = []
    for authority, config in web.items():
        if not isinstance(authority, str) or not re.fullmatch(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+ts\.net:443", authority
        ):
            continue
        handlers = config.get("Handlers") if isinstance(config, dict) else None
        root = handlers.get("/") if isinstance(handlers, dict) else None
        if root == {"Proxy": "http://127.0.0.1:8770"}:
            origins.append("https://" + authority.removesuffix(":443"))
    return origins[0] if len(origins) == 1 else None


def read_serve_status() -> object:
    binary = Path(os.environ.get("SAMANTHA_TAILSCALE_BIN", "").strip() or TAILSCALE_BINARY).expanduser()
    result = subprocess.run(
        [str(binary), "serve", "status", "--json"],
        capture_output=True, text=True, timeout=2, check=False,
        env={**os.environ, "TAILSCALE_BE_CLI": "1"},
    )
    return json.loads(result.stdout) if result.returncode == 0 else None


class HttpsCockpitEntry:
    def __init__(
        self, *, enabled: bool = True,
        status_loader: Callable[[], object] = read_serve_status,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.enabled = enabled
        self.status_loader = status_loader
        self.clock = clock
        self._origin: str | None = None
        self._expires = 0.0
        self._lock = threading.Lock()

    def origin(self) -> str | None:
        with self._lock:
            now = self.clock()
            if now >= self._expires:
                try:
                    self._origin = private_https_origin(self.status_loader())
                except (OSError, ValueError, subprocess.SubprocessError):
                    self._origin = None
                self._expires = now + (60 if self._origin else 10)
            return self._origin

    def redirect_target(self, path: str, headers: Mapping[str, str]) -> str | None:
        if not self.enabled or not path.startswith("/") or path.startswith("//"):
            return None
        parsed = urlsplit(path)
        if parsed.path != "/" or "\r" in path or "\n" in path:
            return None
        # Ignore fetches, probes, APIs and local development. Older Safari may
        # send only Accept; explicit fetch metadata takes precedence over it.
        dest, mode = headers.get("Sec-Fetch-Dest"), headers.get("Sec-Fetch-Mode")
        if (dest is not None and dest != "document") or (mode is not None and mode != "navigate"):
            return None
        if dest != "document" and mode != "navigate" and "text/html" not in headers.get("Accept", ""):
            return None
        try:
            host = urlsplit("//" + headers.get("Host", ""))
            hostname = (host.hostname or "").rstrip(".")
            if host.port != LEGACY_PORT or not hostname or hostname == "localhost":
                return None
            try:
                if ipaddress.ip_address(hostname).is_loopback:
                    return None
            except ValueError:
                pass
        except ValueError:
            return None
        # HTTPS requests already use the canonical host without :8770. Never
        # derive a destination from Host, forwarded headers or query parameters.
        origin = self.origin()
        return origin + path if origin else None
