from __future__ import annotations

import base64
import json
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Any

from openai import OpenAI

from .download_intake import normalize_for_match, suggest_slug


DEFAULT_OPENAI_VISION_MODEL = "gpt-4o-mini"
MAX_IMAGE_EDGE = 1600

VISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "product_name": {"type": "string"},
        "manufacturer_or_brand": {"type": "string"},
        "product_type": {
            "type": "string",
            "enum": ["lek", "doplněk_stravy", "zdravotnický_prostředek", "kosmetika", "nejisté"],
        },
        "active_ingredients_or_composition": {"type": "array", "items": {"type": "string"}},
        "strength": {"type": "string"},
        "form": {"type": "string"},
        "quantity": {"type": "string"},
        "visible_expiration": {"type": "string"},
        "suggested_category": {"type": "string"},
        "suggested_use_inventory_only": {"type": "string"},
        "suggested_filename_slug": {"type": "string"},
        "confidence": {"type": "number"},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
        "visible_text": {"type": "array", "items": {"type": "string"}},
        "safety_note": {"type": "string"},
    },
    "required": [
        "product_name",
        "manufacturer_or_brand",
        "product_type",
        "active_ingredients_or_composition",
        "strength",
        "form",
        "quantity",
        "visible_expiration",
        "suggested_category",
        "suggested_use_inventory_only",
        "suggested_filename_slug",
        "confidence",
        "uncertainties",
        "visible_text",
        "safety_note",
    ],
}


def analyze_lekarna_image_with_openai(
    *,
    image_path: Path,
    model: str = DEFAULT_OPENAI_VISION_MODEL,
    client: Any | None = None,
) -> dict[str, Any]:
    openai_client = client or OpenAI()
    data_url = image_to_data_url(image_path)
    prompt = (
        "Jsi opatrný asistent pro inventář domácí lékárny. "
        "Z fotky krabičky pouze přepiš viditelné informace a navrhni inventární metadata. "
        "Neuváděj dávkování a nedoporučuj léčbu. "
        "Pokud si nejsi jistý, napiš to do uncertainties a sniž confidence. "
        "suggested_filename_slug vrať ASCII lowercase slug bez přípony."
    )
    completion = openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "lekarna_vision_inventory",
                "strict": True,
                "schema": VISION_SCHEMA,
            },
        },
        temperature=0,
    )
    content = completion.choices[0].message.content or "{}"
    result = normalize_openai_vision_result(json.loads(content))
    if not result.get("suggested_filename_slug"):
        result["suggested_filename_slug"] = suggest_slug(result.get("product_name", "lekarna_fotka"))
    return result


def normalize_openai_vision_result(result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    quantity = str(normalized.get("quantity", "") or "").strip()
    form = str(normalized.get("form", "") or "").strip().casefold()
    if quantity.isdigit() and form:
        if "tablet" in form:
            normalized["quantity"] = f"{quantity} tablet"
        elif "tobol" in form or "kaps" in form or "caps" in form:
            normalized["quantity"] = f"{quantity} tobolek"
    if not str(normalized.get("safety_note", "") or "").strip():
        normalized["safety_note"] = (
            "Jde pouze o inventární návrh z fotografie, ne o doporučení léčby ani dávkování; "
            "před použitím ověř příbalovou informaci nebo lékárníka/lékaře."
        )
    return normalized


def openai_vision_label(result: dict[str, Any]) -> str:
    name = openai_vision_display_name(result)
    strength = str(result.get("strength", "") or "").strip()
    quantity = str(result.get("quantity", "") or "").strip()
    parts = [name] if name else []
    for value in (strength, quantity):
        if value:
            parts.append(value)
    return " ".join(parts).strip()


def openai_vision_display_name(result: dict[str, Any]) -> str:
    name = str(result.get("product_name", "") or "").strip()
    brand = canonical_brand(str(result.get("manufacturer_or_brand", "") or "").strip())
    parts: list[str] = []
    if brand and brand.casefold() not in name.casefold():
        parts.append(brand)
    if name:
        parts.append(name)
    return " ".join(parts).strip()


def openai_vision_to_inventory_suggestion(result: dict[str, Any]) -> dict[str, str]:
    label = openai_vision_display_name(result)
    quantity = str(result.get("quantity", "") or "").strip()
    form = str(result.get("form", "") or "").strip()
    strength = str(result.get("strength", "") or "").strip()
    composition = ", ".join(str(item).strip() for item in result.get("active_ingredients_or_composition", []) if str(item).strip())
    expiration = str(result.get("visible_expiration", "") or "").strip() or "nezjisteno"
    category = category_from_openai_result(result)
    slug_source = " ".join(value for value in (label, strength, form, quantity) if value)
    return {
        "nazev": label,
        "ucinna_latka": composition,
        "forma": form,
        "sila": strength,
        "kategorie": category,
        "pouziti": str(result.get("suggested_use_inventory_only", "") or "").strip(),
        "pro_koho": "",
        "nevhodne_pro_koho": "",
        "expirace": expiration,
        "mnozstvi": quantity,
        "umisteni": "leky v krabickach - umisteni nezadano",
        "new_file": f"{suggest_slug(slug_source)}.jpg" if slug_source.strip() else "",
        "Search_Tags": "",
    }


def category_from_openai_result(result: dict[str, Any]) -> str:
    product_type = str(result.get("product_type", "") or "").casefold()
    suggested = normalize_for_match(str(result.get("suggested_category", "") or ""))
    joined = normalize_for_match(
        " ".join(
            [
                str(result.get("product_name", "") or ""),
                str(result.get("manufacturer_or_brand", "") or ""),
                suggested,
                " ".join(str(item) for item in result.get("active_ingredients_or_composition", [])),
            ]
        )
    )
    if product_type == "doplněk_stravy" or any(token in joined for token in ("vitamin", "zinek", "selen", "magnesium", "horcik")):
        return "vitaminy_mineraly_doplnky"
    if product_type == "zdravotnický_prostředek":
        return "zdravotnicky_prostredek"
    if product_type == "kosmetika":
        return "kosmetika"
    return suggested.replace(" ", "_") or "nezarazeno"


def canonical_brand(value: str) -> str:
    normalized = normalize_for_match(value)
    if normalized in {"drmax", "dr max"}:
        return "Dr.Max"
    return value


def image_to_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    image_bytes = maybe_resize_image(image_path)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def maybe_resize_image(image_path: Path) -> bytes:
    try:
        from PIL import Image
    except Exception:
        return image_path.read_bytes()

    try:
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
            output = BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
    except Exception:
        return image_path.read_bytes()
