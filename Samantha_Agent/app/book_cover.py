from __future__ import annotations

import base64
import binascii
import json
import math
from io import BytesIO
from typing import Any

from openai import OpenAI

from app.article_archive import normalize_book_isbn


DEFAULT_BOOK_COVER_MODEL = "gpt-4o-mini"
MAX_BOOK_COVER_BYTES = 7 * 1024 * 1024
MAX_BOOK_COVER_EDGE = 1600
SUPPORTED_BOOK_COVER_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

BOOK_COVER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "author": {"type": "string"},
        "isbn": {"type": "string"},
        "confidence": {"type": "number"},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "author", "isbn", "confidence", "uncertainties"],
}


class BookCoverRecognitionError(RuntimeError):
    """Raised when cover metadata cannot be recognized safely."""


def recognize_book_cover(
    *,
    image_data_url: str,
    model: str = DEFAULT_BOOK_COVER_MODEL,
    client: Any | None = None,
) -> dict[str, Any]:
    prepared_data_url = prepare_book_cover_data_url(image_data_url)
    openai_client = client or OpenAI()
    prompt = (
        "Jsi opatrný katalogizátor domácí knihovny. Z fotografie obálky nebo tiráže přepiš pouze skutečně "
        "viditelný název knihy, autora a ISBN. Nic nedohledávej, neodvozuj a nedoplňuj z obecných znalostí. "
        "Když údaj není čitelný nebo si nejsi jistý, vrať prázdný řetězec a stručně to uveď v uncertainties."
    )
    try:
        completion = openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": prepared_data_url, "detail": "high"}},
                    ],
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "book_cover_metadata",
                    "strict": True,
                    "schema": BOOK_COVER_SCHEMA,
                },
            },
            temperature=0,
            max_tokens=400,
        )
        raw = json.loads(completion.choices[0].message.content or "{}")
    except Exception as exc:
        raise BookCoverRecognitionError(
            "Údaje z obálky se nepodařilo rozpoznat. Zkus ostřejší fotografii nebo údaje vyplň ručně."
        ) from exc
    try:
        if not isinstance(raw, dict):
            raise ValueError("Neplatný formát návrhu.")
        return normalize_book_cover_result(raw)
    except Exception as exc:
        raise BookCoverRecognitionError(
            "Rozpoznané údaje měly neplatný formát. Zkus fotografii znovu nebo údaje vyplň ručně."
        ) from exc


def prepare_book_cover_data_url(image_data_url: str) -> str:
    return prepare_book_image_data_url(
        image_data_url,
        image_description="fotografii obálky",
    )


def prepare_book_image_data_url(
    image_data_url: str,
    *,
    image_description: str,
    max_edge: int = MAX_BOOK_COVER_EDGE,
    jpeg_quality: int = 88,
) -> str:
    value = str(image_data_url or "").strip()
    description = " ".join(str(image_description or "fotografii").split()) or "fotografii"
    display_description = description[:1].upper() + description[1:]
    if "," not in value:
        raise ValueError(f"Vyber {description}.")
    header, encoded = value.split(",", 1)
    if not header.startswith("data:") or ";base64" not in header:
        raise ValueError(f"{display_description} se nepodařilo přečíst.")
    mime_type = header[5:].split(";", 1)[0].casefold()
    if mime_type not in SUPPORTED_BOOK_COVER_MIME_TYPES:
        raise ValueError("Podporované fotografie jsou JPG, PNG, WEBP a HEIC/HEIF.")
    try:
        raw_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"{display_description} se nepodařilo přečíst.") from exc
    if not raw_bytes:
        raise ValueError(f"{display_description} je prázdná.")
    if len(raw_bytes) > MAX_BOOK_COVER_BYTES:
        raise ValueError("Fotografie obálky je větší než 7 MB. Vyber menší kopii.")

    try:
        from PIL import Image, ImageOps

        if mime_type in {"image/heic", "image/heif"}:
            from pillow_heif import register_heif_opener

            register_heif_opener()

        with Image.open(BytesIO(raw_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=jpeg_quality, optimize=True)
            prepared_bytes = output.getvalue()
    except Exception as exc:
        raise ValueError(f"{display_description} se nepodařilo bezpečně převést.") from exc
    return f"data:image/jpeg;base64,{base64.b64encode(prepared_bytes).decode('ascii')}"


def normalize_book_cover_result(raw: dict[str, Any]) -> dict[str, Any]:
    title = " ".join(str(raw.get("title", "") or "").split())[:500]
    author = " ".join(str(raw.get("author", "") or "").split())[:300]
    raw_uncertainties = raw.get("uncertainties", [])
    if not isinstance(raw_uncertainties, list):
        raw_uncertainties = []
    uncertainties = [
        " ".join(str(item).split())[:300]
        for item in raw_uncertainties
        if str(item).strip()
    ][:8]
    raw_isbn = str(raw.get("isbn", "") or "").strip()
    try:
        isbn = normalize_book_isbn(raw_isbn)
    except ValueError:
        isbn = ""
        uncertainties.append("Rozpoznané ISBN neprošlo kontrolou a nebylo předvyplněno.")
    try:
        confidence = float(raw.get("confidence", 0) or 0)
        if not math.isfinite(confidence):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "title": title,
        "author": author,
        "isbn": isbn,
        "confidence": round(confidence, 3),
        "uncertainties": uncertainties,
    }
