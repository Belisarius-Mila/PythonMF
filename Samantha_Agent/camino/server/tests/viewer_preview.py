"""Export a self-contained synthetic browser fixture, never live owner data.

No listener, credentials in URLs, Serve or deployment. The HTTP authorization
and Range path is covered separately by test_viewer; this is only visual/media QA.
"""

import base64
import tempfile
from pathlib import Path

from camino.server.auth import RevocableTokenStore
from camino.server.viewer import CaminoViewer
from camino.server.viewer_media import OUTPUTS, ViewerMedia
from tests.camino_viewer_fixture import ViewerFixture, synthetic_media


def main():
    root = Path(tempfile.mkdtemp(prefix="camino-m1-preview-"))
    fixture = ViewerFixture(root)
    assets = [fixture.upload(30 + i, kind, content)
              for i, (kind, content) in enumerate(synthetic_media(root).items())]
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
    output = root / "preview.html"
    output.write_text(page)
    print(output)


if __name__ == "__main__":
    main()
