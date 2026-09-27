"""Export a self-contained synthetic browser fixture, never live owner data.

No listener, credentials in URLs, Serve or deployment. The HTTP authorization
and Range path is covered separately by test_viewer; this is only visual/media QA.
"""

import base64
import tempfile
from dataclasses import replace
from pathlib import Path

from camino.domain.model import LocationFix
from camino.domain.codec import wire
from camino.server.auth import RevocableTokenStore
from camino.server.viewer import CaminoViewer
from camino.server.viewer_media import OUTPUTS, ViewerMedia
from tests.camino_viewer_fixture import ViewerFixture, synthetic_media, uid
from tests.test_camino_audio_layout import layout


def main():
    root = Path(tempfile.mkdtemp(prefix="camino-m1-preview-"))
    fixture = ViewerFixture(root, location=LocationFix(12.25, 34.5, 1790323200000, 8))
    assets = [fixture.upload(30 + i, kind, content)
              for i, (kind, content) in enumerate(synthetic_media(root).items())]
    fixture.send("create_audio_layout", layout(50, [32]))
    fixture.send("update_metadata", {"moment_id": fixture.public.id,
        "change": {"type": "title", "title": "Ranní zastávka"}}, expected=1)
    for revision, (kind, target, title) in enumerate([
        ("asset", 30, "Fotografie u mostu"), ("asset", 31, "Krátké video"),
        ("audio_session", 50, "Komentář k zastávce")
    ], 2):
        fixture.send("update_metadata", {"moment_id": fixture.public.id, "change": {
            "type": "attachment_title", "attachment": {"kind": kind, "target_id": uid(target), "title": title}
        }}, expected=revision)
    for index in range(1, 13):
        minutes = 10 * 60 + index * 20
        capture = replace(fixture.capture, utc_ms=fixture.capture.utc_ms + index * 1_200_000,
                          local_wall=f"2026-09-25T{minutes // 60:02d}:{minutes % 60:02d}:00")
        fixture.send("create_moment", wire(replace(fixture.public, id=uid(100 + index),
            captured=capture, location=None,
            title=f"Další zážitek {index} — syntetický přehled dlouhého dne")))
    viewer = CaminoViewer(fixture.store, fixture.media, ViewerMedia(root / "copies"),
                          RevocableTokenStore(root / "unused-reader.sqlite"), fixture.trip.id)
    assert viewer.build_pending() == {"ready": 3, "waiting": 0}
    page = viewer.page("2026-09-25")
    for asset in assets:
        for name, path in viewer.copies.ready(asset).items():
            mime = OUTPUTS[asset["media_kind"]][name]
            url = f'/viewer/media/{asset["id"]}/{name}'
            page = page.replace(url, f'data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}')
    page = page.replace('href="/viewer/"', 'href="#"').replace('href="/viewer/days/2026-09-25"', 'href="#"')
    page = page.replace("CAMINO · PRO JANU", "CAMINO · SYNTETICKÝ NÁHLED M1")
    script = Path(__file__).resolve().parents[1] / "viewer_player.js"
    page = page.replace('<script src="/viewer/player.js" defer></script>', '')
    page = page.replace('</body>', '<script>' + script.read_text() + '</script></body>')
    output = root / "preview.html"
    output.write_text(page)
    print(output)


if __name__ == "__main__":
    main()
