"""Configuration-only Camino shortcut; never probes, starts or proxies a service."""

from __future__ import annotations

import os
import re


_PRIVATE_URL = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\."
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.ts\.net/(?:camino-api/)?viewer/"
)


def camino_viewer_link_status() -> dict:
    url = os.environ.get("CAMINO_VIEWER_URL", "")
    if not url:
        return {"configured": False, "url": "", "message": "Soukromý odkaz zatím není nastavený."}
    if not _PRIVATE_URL.fullmatch(url):
        return {"configured": False, "url": "", "message": "Soukromý odkaz má neplatné nastavení."}
    return {"configured": True, "url": url,
            "message": "Soukromý odkaz nastavený; dostupnost se ověří otevřením. Vyžaduje přihlášení Jany."}
