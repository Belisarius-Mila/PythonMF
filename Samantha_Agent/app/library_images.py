"""Local, memory-only preparation of library photos which a browser cannot decode."""

from __future__ import annotations

from io import BytesIO

MAX_LIBRARY_PHOTO_INPUT_BYTES = 32 * 1024 * 1024
LIBRARY_PHOTO_STORAGE_POLICY = "illustration_0_3_mib"
MAX_LIBRARY_PHOTO_BYTES = 285 * 1024
MAX_LIBRARY_THUMB_BYTES = 20 * 1024
MAX_LIBRARY_STORED_PHOTO_BYTES = MAX_LIBRARY_PHOTO_BYTES + MAX_LIBRARY_THUMB_BYTES
MAX_LIBRARY_PHOTO_PIXELS = 64_000_000
MAX_LIBRARY_PHOTO_EDGE = 1600


def prepare_library_photo(raw: bytes) -> bytes:
    """Return a metadata-free JPEG; with its thumbnail it occupies <0.3 MiB."""
    return _prepare_jpeg(raw, max_bytes=MAX_LIBRARY_PHOTO_BYTES,
                         edge=MAX_LIBRARY_PHOTO_EDGE, qualities=(88, 84, 80, 76, 72),
                         keep_compliant=True)


def prepare_library_thumbnail(raw: bytes) -> bytes:
    """Return the only additional stored copy: a thumbnail of at most 20 KiB."""
    return _prepare_jpeg(raw, max_bytes=MAX_LIBRARY_THUMB_BYTES,
                         edge=320, qualities=(78, 72, 66, 60), keep_compliant=False)


def prepare_library_recognition_photo(raw: bytes) -> bytes:
    """Keep the pre-existing temporary OCR/ISBN quality; never archive this copy."""
    return _prepare_jpeg(raw, max_bytes=1024 * 1024,
                         edge=2400, qualities=(90, 84, 78, 72), keep_compliant=True)


def _prepare_jpeg(raw: bytes, *, max_bytes: int, edge: int,
                  qualities: tuple[int, ...], keep_compliant: bool) -> bytes:
    if not raw or len(raw) > MAX_LIBRARY_PHOTO_INPUT_BYTES:
        raise ValueError("Vyber neprázdnou fotografii nejvýše 32 MiB.")
    from PIL import Image, ImageOps, UnidentifiedImageError
    from pillow_heif import register_heif_opener

    register_heif_opener()
    try:
        with Image.open(BytesIO(raw)) as source:
            # Some camera JPEGs include an MPO auxiliary frame; use the main image.
            if source.format not in {"JPEG", "MPO", "PNG", "WEBP", "HEIF", "HEIC"}:
                raise ValueError("Podporované fotografie jsou JPG, PNG, WEBP a HEIC/HEIF.")
            if source.width * source.height > MAX_LIBRARY_PHOTO_PIXELS:
                raise ValueError("Fotografie má více než 64 milionů bodů. Vyber menší rozlišení.")
            source.load()
            # Browser output is already normalized. Preserve its bytes and quality.
            safe_info = {"jfif", "jfif_version", "jfif_unit", "jfif_density"}
            if (keep_compliant and source.format == "JPEG" and source.mode == "RGB"
                    and len(raw) <= max_bytes and max(source.size) <= edge
                    and not source.getexif() and not (set(source.info) - safe_info)):
                return raw
            image = ImageOps.exif_transpose(source)
            image.thumbnail((edge, edge), Image.Resampling.LANCZOS)
            rgba = image.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, "white")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
            for _ in range(12):
                for quality in qualities:
                    output = BytesIO()
                    rgb.save(output, format="JPEG", quality=quality, optimize=True)
                    encoded = output.getvalue()
                    if len(encoded) <= max_bytes:
                        return encoded
                rgb = rgb.resize((max(1, round(rgb.width * .85)), max(1, round(rgb.height * .85))), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Fotografii se nepodařilo přečíst. Vyber nepoškozený JPG, PNG, WEBP nebo HEIC/HEIF.") from exc
    raise ValueError("Fotografii se nepodařilo zmenšit do úsporného limitu.")
