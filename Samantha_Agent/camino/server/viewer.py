"""Opt-in, read-only M1 Viewer. No listener, deployment or paid AI."""

from __future__ import annotations

import base64
import binascii
import sqlite3
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

from camino.domain.model import ContractError
from camino.domain.audio_layout import ordered_audio_groups
from camino.domain.revision_store import RevisionStore
from camino.server.auth import RevocableTokenStore
from camino.server.media_store import MediaStore
from camino.server.viewer_media import OUTPUTS, ViewerMedia


HEADERS = {
    "Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'self'; img-src 'self'; media-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
}
CSS = """
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#233b35;background:#f3f2eb}
*{box-sizing:border-box}body{margin:0}header,main,footer{max-width:880px;margin:auto;padding:24px}
header{padding-top:44px}h1{font-size:2.4rem;margin:.2em 0}h2{font-size:1.5rem}h3{font-size:1.1rem}
a{color:#225b48}a:focus-visible{outline:3px solid #bd751a;outline-offset:4px}
.label{letter-spacing:.16em;font-size:.75rem;font-weight:700}.muted,footer{color:#586961;font-size:.9rem}
nav{display:flex;flex-wrap:wrap;gap:12px}nav a{background:#fff;padding:14px 20px;border-radius:12px}
article{background:#fff;border:1px solid #dce2d8;border-radius:16px;padding:22px;margin:18px 0}
.text{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.7}figure{margin:16px 0}
img,video{display:block;max-width:100%;max-height:65vh;border-radius:10px;margin:auto}
audio{width:100%}figcaption{margin:8px 0;color:#586961;font-size:.85rem}
.notice{border-left:3px solid #ac792d;padding:10px 14px;background:#faf5e9}
@media(max-width:520px){header,main,footer{padding:18px}h1{font-size:1.9rem}article{padding:16px}}
"""
KINDS = {"photo": "Fotografie", "video": "Video", "comment": "Komentář", "reflection": "Úvaha", "marker": "Záznam"}


class CaminoViewer:
    def __init__(self, metadata: RevisionStore, media: MediaStore, copies: ViewerMedia,
                 tokens: RevocableTokenStore, trip_id: str):
        metadata._uuid(trip_id)
        self.metadata, self.media, self.copies, self.tokens = metadata, media, copies, tokens
        self.trip_id = trip_id
        self.last_build: str | None = None
        self.build_state = "manual"
        self._conversion_failures: dict[str, int] = {}

    def authorized(self, request: Request) -> bool:
        # A separate, revocable reader credential; never accept an owner Bearer.
        header = request.headers.get("authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            username, password = base64.b64decode(header[6:], validate=True).decode().split(":", 1)
            return username == "jana" and self.tokens.authenticate("Bearer " + password)
        except (ValueError, UnicodeError, binascii.Error):
            return False

    def build_pending(self, *, should_stop: Callable[[], bool] = lambda: False) -> dict[str, int]:
        """A serial batch invoked offline or by the lifespan worker, never GET."""
        report = {"ready": 0, "waiting": 0}
        for moment in self.metadata.viewer_snapshot(self.trip_id)["moments"]:
            for asset in moment["assets"]:
                if should_stop():
                    return report
                # Recheck permission before starting each potentially long conversion.
                if moment["id"] not in self.metadata.viewer_safe_ids(self.trip_id):
                    break
                if self.copies.ready(asset, verify=False):
                    report["ready"] += 1
                    continue
                if self._conversion_failures.get(asset["id"], 0) >= 3:
                    # A broken source must not create private pending files forever.
                    # Three attempts per process; a service restart permits retry.
                    report["waiting"] += 1
                    continue
                source = self.media.verified_source(asset["id"])
                if source and self.copies.build(asset, source, should_stop=should_stop):
                    report["ready"] += 1
                    self._conversion_failures.pop(asset["id"], None)
                else:
                    if source and not should_stop():
                        self._conversion_failures[asset["id"]] = self._conversion_failures.get(asset["id"], 0) + 1
                    report["waiting"] += 1
        self.last_build = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return report

    def asset(self, asset_id: str) -> dict | None:
        for moment in self.metadata.viewer_snapshot(self.trip_id)["moments"]:
            for asset in moment["assets"]:
                if asset["id"] == asset_id:
                    return asset
        return None

    def audio_html(self, moment: dict, root_path: str) -> tuple[str, set[str]]:
        groups, used = ordered_audio_groups(moment["assets"], moment["audio_layouts"])
        body = ""
        for group_index, group in enumerate(groups, 1):
            body += f'<section aria-label="Nahrávka {group_index}"><h3>Nahrávka {group_index}</h3>'
            for clip_index, clip in enumerate(group["clips"], 1):
                if not clip["order_known"]:
                    body += '<p class="notice">Předchozí část není dostupná; návaznost není ověřená.</p>'
                if clip["previous_clip_id"] is not None:
                    gap = clip["gap_before_ms"]
                    label = 'délka neznámá' if gap is None else f'{gap / 1000:.3f}'.rstrip('0').rstrip('.') + ' s'
                    body += f'<p class="notice">Pauza před pokračováním: {label}. Pokračování spusť tlačítkem přehrát.</p>'
                ready = {part["asset_id"]: self.copies.ready(group["assets"][part["asset_id"]], verify=False)
                         for part in clip["parts"]}
                for offset, part in enumerate(clip["parts"]):
                    identifier = part["asset_id"]
                    if part["discontinuity_before"]:
                        body += '<p class="notice">Zde chybí úsek nahrávky; délka mezery není známá.</p>'
                    caption = f'Část {clip_index} · úsek {part["index"] + 1}'
                    if not ready[identifier]:
                        body += f'<p class="notice">{caption}: čeká na doručení nebo převod.</p>'
                        continue
                    following = clip["parts"][offset + 1] if offset + 1 < len(clip["parts"]) else None
                    next_attr = ''
                    if following and ready[following["asset_id"]] and not following["discontinuity_before"]:
                        next_attr = f' data-next="audio-{following["asset_id"]}"'
                    body += (f'<figure><audio id="audio-{identifier}"{next_attr} controls preload="none" '
                             f'src="{root_path}/viewer/media/{identifier}/audio.m4a">Prohlížeč neumí přehrát audio.</audio>'
                             f'<figcaption>{caption}</figcaption></figure>')
                if clip["missing_tail"]:
                    body += '<p class="notice">Konec této části není úplný; délka chybějícího konce není známá.</p>'
            body += '</section>'
        return body, used

    def page(self, day: str | None = None, *, root_path: str = "") -> str | None:
        if root_path not in ("", "/camino-api"):
            raise ContractError("unsupported Viewer proxy prefix")
        snapshot = self.metadata.viewer_snapshot(self.trip_id)
        moments = snapshot["moments"]
        days = sorted({m["day"] for m in moments}, reverse=True)
        if day is not None and day not in days:
            return None
        title = escape(snapshot["name"])
        body = '<nav aria-label="Dny cesty">' + ''.join(
            f'<a href="{root_path}/viewer/days/{d}">{d[8:10]}. {d[5:7]}. {d[:4]}</a>' for d in days
        ) + '</nav>'
        if not days:
            body += '<p class="notice">Zatím tu nejsou žádné dostupné záznamy.</p>'
        elif day is None:
            body += '<p>Vyber den. Najdeš tu doručené fotografie, texty a nahrávky.</p>'
        else:
            body += f'<h2>{day[8:10]}. {day[5:7]}. {day[:4]}</h2>'
            for moment in moments:
                if moment["day"] != day:
                    continue
                body += f'<article><h3>{escape(moment["time"])} · {KINDS.get(moment["kind"], "Záznam")}</h3>'
                if moment["text"]:
                    body += f'<p class="text">{escape(moment["text"])}</p>'
                audio_body, ordered_ids = self.audio_html(moment, root_path)
                body += audio_body
                for index, asset in enumerate(moment["assets"], 1):
                    if asset["id"] in ordered_ids:
                        continue
                    ready = self.copies.ready(asset, verify=False)
                    if not ready:
                        body += '<p class="notice">Médium zatím není připravené k přehrání.</p>'
                        continue
                    base = f'{root_path}/viewer/media/{asset["id"]}/'
                    kind = asset["media_kind"]
                    if kind == "photo":
                        element = f'<img src="{base}preview.jpg" loading="lazy" alt="Fotografie ze záznamu">'
                    elif kind == "video":
                        element = f'<video controls playsinline preload="metadata" poster="{base}poster.jpg" src="{base}clip.mp4">Prohlížeč neumí přehrát video.</video>'
                    else:
                        body += '<p class="notice">Pořadí této nahrávky zatím není přenesené; přehrává se samostatně.</p>'
                        element = f'<audio controls preload="none" src="{base}audio.m4a">Prohlížeč neumí přehrát audio.</audio>'
                    body += f'<figure>{element}<figcaption>{index}. médium</figcaption></figure>'
                body += '</article>'
        built = escape(self.last_build or "zatím neproběhla")
        state = {"manual": "Automatická příprava není zapnutá.",
                 "building": "Připravuji doručená média.",
                 "waiting": "Některá média čekají na doručení nebo úspěšný převod.",
                 "checked": "Poslední kontrola doručených médií dokončena.",
                 "failed": "Příprava se nepodařila; automaticky ji zkusím znovu.",
                 "stopped": "Automatická příprava je zastavená."}.get(self.build_state, "Stav přípravy neznámý.")
        return f'''<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Camino</title>
<script src="{root_path}/viewer/player.js" defer></script>
<style>{CSS}</style></head><body><header><p class="label">CAMINO · PRO JANU</p>
<h1>{title}</h1><p class="muted">Malé zprávy z cesty. Fotografie, slova a původní hlas.</p>
<a href="{root_path}/viewer/">Všechny dny</a></header><main>{body}</main><footer>
Příprava médií: {built}<br>{state}<br>Zobrazuji doručené záznamy. Další mohou ještě čekat v telefonu.
<br>Stránku obnovíš běžným tlačítkem prohlížeče.</footer>
<p id="audioPlaybackStatus" role="status" aria-live="polite"></p></body></html>'''

    def router(self) -> APIRouter:
        router = APIRouter(prefix="/viewer", include_in_schema=False)

        def denied() -> Response:
            return Response("Soukromý přístup pro Janu.", status_code=401, headers={
                **HEADERS, "WWW-Authenticate": 'Basic realm="Camino Viewer", charset="UTF-8"',
            })

        @router.get("/player.js")
        def player(request: Request):
            if not self.authorized(request):
                return denied()
            return FileResponse(Path(__file__).with_name("viewer_player.js"),
                                media_type="text/javascript", headers=HEADERS)

        @router.get("/")
        @router.get("/days/{day}")
        def page(request: Request, day: str | None = None):
            try:
                if not self.authorized(request):
                    return denied()
                content = self.page(day, root_path=request.scope.get("root_path", ""))
                return HTMLResponse(content, headers=HEADERS) if content else Response(status_code=404, headers=HEADERS)
            except (OSError, sqlite3.DatabaseError, ContractError):
                return Response("Přehled teď není dostupný.", status_code=503, headers=HEADERS)

        @router.api_route("/media/{asset_id}/{name}", methods=["GET", "HEAD"])
        def media(request: Request, asset_id: str, name: str):
            try:
                if not self.authorized(request):
                    return denied()
                asset = self.asset(asset_id)
                if asset is None or name not in OUTPUTS[asset["media_kind"]]:
                    return Response(status_code=404, headers=HEADERS)
                paths = self.copies.ready(asset)
                if name not in paths:
                    return Response(status_code=404, headers=HEADERS)
                # FileResponse supports byte Range; every new request goes through
                # the current projection above, including old URLs and HEAD.
                return FileResponse(paths[name], media_type=OUTPUTS[asset["media_kind"]][name], headers=HEADERS)
            except (OSError, sqlite3.DatabaseError, ContractError):
                return Response(status_code=503, headers=HEADERS)

        return router
