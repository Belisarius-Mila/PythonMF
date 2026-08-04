from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.book_cover import prepare_book_image_data_url


DEFAULT_BOOK_TEXT_OCR_MODEL = "gpt-4o-mini"
MAX_BOOK_TEXT_OCR_IMAGES = 3
MAX_BOOK_TEXT_OCR_CHARS = 20_000

BOOK_TEXT_OCR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "text": {"type": "string"},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["text", "uncertainties"],
}


class BookTextOcrError(RuntimeError):
    """Raised when text cannot be transcribed safely from temporary photos."""


def extract_book_text_from_images(
    *,
    image_data_urls: list[str],
    model: str = DEFAULT_BOOK_TEXT_OCR_MODEL,
    client: Any | None = None,
) -> dict[str, Any]:
    if not isinstance(image_data_urls, list) or not image_data_urls:
        raise ValueError("Vyber alespoň jednu fotografii textu knihy.")
    if len(image_data_urls) > MAX_BOOK_TEXT_OCR_IMAGES:
        raise ValueError("Pro jedno rozpoznání lze použít nejvýše 3 fotografie.")

    prepared_images = [
        prepare_book_image_data_url(
            str(image_data_url or ""),
            image_description="fotografii textu knihy",
            max_edge=1400,
            jpeg_quality=82,
        )
        for image_data_url in image_data_urls
    ]
    prompt = (
        "Přepiš v původním jazyce pouze text skutečně viditelný na přiložených fotografiích "
        "knihy. Zachovej pořadí fotografií, odstavce, nadpisy a interpunkci. Text neshrnuj, neopravuj fakta, "
        "nic nedohledávej a nic nedoplňuj. Nečitelné místo označ [nečitelné] a stručně je popiš v uncertainties."
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    content.extend(
        {"type": "image_url", "image_url": {"url": image_data_url, "detail": "high"}}
        for image_data_url in prepared_images
    )
    openai_client = client or OpenAI()
    try:
        completion = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "book_text_ocr",
                    "strict": True,
                    "schema": BOOK_TEXT_OCR_SCHEMA,
                },
            },
            temperature=0,
            max_tokens=3000,
        )
        raw = json.loads(completion.choices[0].message.content or "{}")
    except Exception as exc:
        raise BookTextOcrError(
            "Text z fotografií se nepodařilo přečíst. Zkus ostřejší snímek s rovnoměrným světlem."
        ) from exc

    try:
        if not isinstance(raw, dict):
            raise ValueError("Neplatný formát OCR.")
        text = normalize_ocr_text(raw.get("text"))
        raw_uncertainties = raw.get("uncertainties", [])
        if not isinstance(raw_uncertainties, list):
            raw_uncertainties = []
        uncertainties = [
            " ".join(str(item).split())[:300]
            for item in raw_uncertainties
            if str(item).strip()
        ][:8]
    except Exception as exc:
        raise BookTextOcrError("Rozpoznaný text měl neplatný formát. Zkus fotografie znovu.") from exc
    if not text:
        raise BookTextOcrError("Na fotografiích nebyl nalezen čitelný text.")
    return {
        "text": text,
        "uncertainties": uncertainties,
        "image_count": len(prepared_images),
    }


def normalize_ocr_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(text) > MAX_BOOK_TEXT_OCR_CHARS:
        raise ValueError("OCR text je neočekávaně dlouhý.")
    return text
