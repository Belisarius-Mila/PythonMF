"""Small, local cover copies from the fixed public Open Library endpoint."""
from __future__ import annotations

from io import BytesIO
import http.client
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlsplit

import certifi
from PIL import Image, UnidentifiedImageError

MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024
MAX_THUMBNAIL_BYTES = 64 * 1024


def _allowed(url):
    parsed = urlsplit(url)
    return (parsed.scheme == "https" and parsed.hostname == "covers.openlibrary.org"
            and not parsed.username and not parsed.password and parsed.port in (None, 443))


class _CoverRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed(newurl):
            raise ValueError("Neověřený cíl obálky.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_thumbnail(isbn, *, opener=None):
    """Return (JPEG bytes, status); unavailable covers never prevent saving a book."""
    # Import lazily: the inventory owns ISBN validation and the fixed URL format.
    from app.book_inventory import cover_url

    url = cover_url(isbn)
    try:
        if opener is None:
            opener = urllib.request.build_opener(
                urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())),
                _CoverRedirect(),
            ).open
        request = urllib.request.Request(url, headers={"User-Agent": "Samantha-Personal-Library/1.0", "Accept": "image/jpeg,image/png,image/webp"})
        with opener(request, timeout=3.0) as response:
            if not _allowed(response.geturl()):
                raise ValueError("Neověřený cíl obálky.")
            if response.headers.get_content_type() not in {"image/jpeg", "image/png", "image/webp"}:
                raise ValueError("Neplatný typ obálky.")
            source = response.read(MAX_DOWNLOAD_BYTES + 1)
        if len(source) > MAX_DOWNLOAD_BYTES:
            raise ValueError("Obálka je příliš velká.")
        with Image.open(BytesIO(source)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"} or not (1 < image.width and 1 < image.height and image.width * image.height <= 8_000_000):
                raise ValueError("Neplatný obrázek obálky.")
            image.thumbnail((240, 320))
            rgb = image.convert("RGB")
            # A fresh image strips EXIF and other source metadata.
            clean = Image.new("RGB", rgb.size, "white")
            clean.paste(rgb)
            output = BytesIO()
            clean.save(output, format="JPEG", quality=78, optimize=True)
        data = output.getvalue()
        if len(data) > MAX_THUMBNAIL_BYTES:
            raise ValueError("Miniatura je příliš velká.")
        return data, "stored"
    except urllib.error.HTTPError as error:
        return None, "not_found" if error.code in (404, 410) else "unavailable"
    except (OSError, ValueError, http.client.HTTPException, UnidentifiedImageError, Image.DecompressionBombError):
        return None, "unavailable"
