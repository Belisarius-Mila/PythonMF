from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.download_intake import match_existing_records, suggest_slug  # noqa: E402
from app.lekarna.openai_vision import (  # noqa: E402
    DEFAULT_OPENAI_VISION_MODEL,
    analyze_lekarna_image_with_openai,
)
from app.lekarna.service import DEFAULT_DOMACI_LEKY_CSV, load_domaci_leky  # noqa: E402


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "lekarna" / "photo_imports"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one confirmed OpenAI Vision pilot for a medicine-box photo.")
    parser.add_argument("--image", required=True, help="One image path to send to OpenAI Vision.")
    parser.add_argument("--model", default=DEFAULT_OPENAI_VISION_MODEL)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--csv", default=str(DEFAULT_DOMACI_LEKY_CSV))
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env", override=True)
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Chybí OPENAI_API_KEY v prostředí nebo lokálním .env.")

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists() or not image_path.is_file():
        raise SystemExit(f"Fotka neexistuje: {image_path}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    result = analyze_image(image_path=image_path, model=args.model)
    matches = match_existing_records(result.get("product_name", ""), load_domaci_leky(Path(args.csv)))
    payload = {
        "schema": "lekarna_openai_vision_pilot_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "image": str(image_path),
        "model": args.model,
        "result": result,
        "duplicate_matches": [
            {
                "nazev": match.nazev,
                "sila": match.sila,
                "forma": match.forma,
                "mnozstvi": match.mnozstvi,
                "umisteni": match.umisteni,
                "zdroj": match.zdroj,
            }
            for match in matches
        ],
    }
    stem = f"lekarna_openai_vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image_path.stem}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(format_markdown(payload), encoding="utf-8")

    print(f"json={json_path}")
    print(f"report={md_path}")
    print(f"product_name={result.get('product_name', '')}")
    print(f"confidence={result.get('confidence', '')}")
    print(f"duplicate_matches={len(matches)}")
    return 0


def analyze_image(*, image_path: Path, model: str) -> dict[str, Any]:
    result = analyze_lekarna_image_with_openai(image_path=image_path, model=model)
    if not result.get("suggested_filename_slug"):
        result["suggested_filename_slug"] = suggest_slug(result.get("product_name", "lekarna_fotka"))
    return result


def format_markdown(payload: dict[str, Any]) -> str:
    result = payload["result"]
    matches = payload["duplicate_matches"]
    lines = [
        "# Lékárna - OpenAI Vision pilot",
        "",
        f"Vygenerováno: {payload['generated_at']}",
        f"Model: `{payload['model']}`",
        f"Fotka: `{payload['image']}`",
        "",
        "## Návrh",
        "",
        f"- Název: {result.get('product_name', '')}",
        f"- Značka/výrobce: {result.get('manufacturer_or_brand', '')}",
        f"- Typ: `{result.get('product_type', '')}`",
        f"- Složení/látky: {', '.join(result.get('active_ingredients_or_composition', []))}",
        f"- Síla: {result.get('strength', '')}",
        f"- Forma: {result.get('form', '')}",
        f"- Množství: {result.get('quantity', '')}",
        f"- Viditelná expirace: {result.get('visible_expiration', '')}",
        f"- Kategorie: {result.get('suggested_category', '')}",
        f"- Inventární použití: {result.get('suggested_use_inventory_only', '')}",
        f"- Slug: `{result.get('suggested_filename_slug', '')}`",
        f"- Confidence: {result.get('confidence', '')}",
        "",
        "## Nejistoty",
        "",
    ]
    uncertainties = result.get("uncertainties", [])
    lines.extend(f"- {item}" for item in uncertainties) if uncertainties else lines.append("- Bez uvedených nejistot")
    lines.extend(["", "## Duplicitní shody", ""])
    if matches:
        for match in matches:
            lines.append(f"- {match['nazev']} | {match['sila']} | {match['mnozstvi']} | `{match['zdroj']}`")
    else:
        lines.append("- Žádné podle názvu.")
    lines.extend(["", "## Viditelný text", ""])
    visible_text = result.get("visible_text", [])
    lines.extend(f"- {line}" for line in visible_text) if visible_text else lines.append("- Neuvedeno.")
    lines.extend(["", "## Bezpečnost", "", f"- {result.get('safety_note', '')}"])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
