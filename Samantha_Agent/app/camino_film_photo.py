"""Bounded, metadata-free photo derivatives shared by film viewing and rendering."""
from __future__ import annotations

import io
import os
import stat
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

from camino.film.project import FilmError

MAX_PHOTO_BYTES = 64 * 1024 * 1024
MAX_PHOTO_PIXELS = 64_000_000
MAX_PHOTO_EDGE = 16_384
PHOTO_VIEW_SIZE = (4096, 4096)


def read_photo(source: Path) -> bytes:
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_PHOTO_BYTES:
            raise FilmError("Fotografie překračuje povolený limit souboru.")
        return handle.read(MAX_PHOTO_BYTES + 1)


def decode_photo(original: bytes, size=PHOTO_VIEW_SIZE) -> Image.Image:
    """Fit the complete main image; never crop, upscale, or modify the source."""
    if not 0 < len(original) <= MAX_PHOTO_BYTES:
        raise FilmError("Fotografie překračuje povolený limit souboru.")
    try:
        with Image.open(io.BytesIO(original)) as image:
            image.seek(0)  # MPO auxiliary images must not enter the film.
            width, height = image.size
            if max(width, height) > MAX_PHOTO_EDGE or width * height > MAX_PHOTO_PIXELS:
                raise FilmError("Fotografie překračuje limit 64 Mpx nebo 16384 pixelů na stranu.")
            photo = ImageOps.exif_transpose(image).convert("RGB")
            if image.info.get("icc_profile"):
                try:
                    photo = ImageCms.profileToProfile(photo,
                        ImageCms.ImageCmsProfile(io.BytesIO(image.info["icc_profile"])),
                        ImageCms.createProfile("sRGB"), outputMode="RGB")
                except (ImageCms.PyCMSError, OSError, ValueError) as error:
                    raise FilmError("Barevný profil fotografie nelze bezpečně převést do SDR.") from error
            photo.thumbnail(size, Image.Resampling.LANCZOS)
            photo.info.clear()
            return photo
    except FilmError:
        raise
    except Exception as error:
        raise FilmError("Fotografii nelze bezpečně dekódovat.") from error
