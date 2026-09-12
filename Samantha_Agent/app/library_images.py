"""Local, memory-only preparation of library photos which a browser cannot decode."""

from __future__ import annotations

from io import BytesIO

MAX_LIBRARY_PHOTO_INPUT_BYTES = 32 * 1024 * 1024
MAX_LIBRARY_PHOTO_BYTES = 1024 * 1024
MAX_LIBRARY_PHOTO_PIXELS = 64_000_000
MAX_LIBRARY_PHOTO_EDGE = 2400


def prepare_library_photo(raw: bytes) -> bytes:
    """Return an oriented, metadata-free JPEG of at most 1 MiB; never save input."""
    if not raw or len(raw) > MAX_LIBRARY_PHOTO_INPUT_BYTES:
        raise ValueError("Vyber neprázdnou fotografii nejvýše 32 MiB.")
    from PIL import Image, ImageOps, UnidentifiedImageError
    from pillow_heif import register_heif_opener

    register_heif_opener()
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.format not in {"JPEG", "PNG", "WEBP", "HEIF", "HEIC"}:
                raise ValueError("Podporované fotografie jsou JPG, PNG, WEBP a HEIC/HEIF.")
            if source.width * source.height > MAX_LIBRARY_PHOTO_PIXELS:
                raise ValueError("Fotografie má více než 64 milionů bodů. Vyber menší rozlišení.")
            image = ImageOps.exif_transpose(source)
            image.thumbnail((MAX_LIBRARY_PHOTO_EDGE, MAX_LIBRARY_PHOTO_EDGE), Image.Resampling.LANCZOS)
            rgba = image.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, "white")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
            for _ in range(12):
                for quality in (90, 84, 78, 72):
                    output = BytesIO()
                    rgb.save(output, format="JPEG", quality=quality, optimize=True)
                    encoded = output.getvalue()
                    if len(encoded) <= MAX_LIBRARY_PHOTO_BYTES:
                        return encoded
                rgb = rgb.resize((max(1, round(rgb.width * .8)), max(1, round(rgb.height * .8))), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Fotografii se nepodařilo přečíst. Vyber nepoškozený JPG, PNG, WEBP nebo HEIC/HEIF.") from exc
    raise ValueError("Fotografii se nepodařilo zmenšit na 1 MiB.")
