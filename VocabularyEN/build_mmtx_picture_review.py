#!/usr/bin/env python3
"""Validate MMTX picture candidates and build review reports without publishing."""

from __future__ import annotations

import html
import importlib.util
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
PICTNEW = REPO_ROOT / "PictNew"
PLAN_PATH = PICTNEW / "VocabularyEN_MMTX_picture_plan_20260824.json"
GENERATED_ROOT = PICTNEW / "generated"
MASTER_REVIEW = PICTNEW / "VocabularyEN_MMTX_review_20260824.html"
MAX_BYTES = 300 * 1024


def load_image_generator():
    path = REPO_ROOT / "image_generator.py"
    spec = importlib.util.spec_from_file_location("image_generator", path)
    if not spec or not spec.loader:
        raise SystemExit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def generated_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in sorted(GENERATED_ROOT.glob("20260824_en_mmtx_batch*/*.webp")):
        if path.stem in files:
            raise SystemExit(f"Duplicate generated stem: {path.stem}")
        files[path.stem] = path
    return files


def validate_image(path: Path) -> dict[str, object]:
    if not path.exists():
        raise SystemExit(f"Missing image: {path}")
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise SystemExit(f"Image exceeds 300 kB: {path} ({size} bytes)")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        width, height = image.size
        image_format = image.format
    if width != height:
        raise SystemExit(f"Image is not square: {path} ({width}x{height})")
    return {"bytes": size, "width": width, "height": height, "format": image_format}


def build_batch_reports(plan: dict[str, object], files: dict[str, Path]) -> None:
    generator = load_image_generator()
    requests = {request["image_name"]: request for request in plan["requests"]}
    by_directory: dict[Path, list[Path]] = defaultdict(list)
    for path in files.values():
        by_directory[path.parent].append(path)
    for directory, paths in sorted(by_directory.items()):
        batch_index = int(directory.name.rsplit("batch", 1)[1])
        results = []
        for index, path in enumerate(sorted(paths), start=1):
            request = requests[path.stem]
            results.append(
                {
                    "status": "generated_built_in_imagegen",
                    "request_index": index,
                    "output_path": path.relative_to(REPO_ROOT).as_posix(),
                    "output_file": path.name,
                    "original_bytes": 0,
                    "output_bytes": path.stat().st_size,
                    "request": request,
                }
            )
        (directory / "generation_report.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (directory / "review.html").write_text(
            generator.render_review_html(results=results, batch_index=batch_index),
            encoding="utf-8",
        )


def relative_from_review(path: Path) -> str:
    return Path(os.path.relpath(path.resolve(), PICTNEW.resolve())).as_posix()


def card(path: Path, title: str, subtitle: str, status: str) -> str:
    return f"""<article class="card">
      <img src="{html.escape(relative_from_review(path))}" alt="{html.escape(title)}">
      <h3>{html.escape(title)}</h3>
      <p>{html.escape(subtitle)}</p>
      <code>{html.escape(status)}</code>
    </article>"""


def render_master_review(plan: dict[str, object], files: dict[str, Path]) -> str:
    generated_words: dict[str, list[str]] = defaultdict(list)
    for item in plan["assignments"]:
        if item["action"] == "generate":
            generated_words[item["image_stem"]].append(f"{item['en']} — {item['cz']}")
    generated_cards = "\n".join(
        card(files[stem], " / ".join(words), files[stem].name, "NEW generated")
        for stem, words in sorted(generated_words.items())
    )

    forest_cards = []
    mapped_cards = []
    exact_cards = []
    for item in plan["assignments"]:
        if item["action"] == "generate":
            continue
        source = REPO_ROOT / item["source"]
        rendered = card(
            source,
            f"{item['en']} — {item['cz']}",
            source.name,
            item["action"],
        )
        if item["action"] == "reuse_mmtx_forest_asset":
            forest_cards.append(rendered)
        elif item["action"] == "reuse_pict_mapped":
            mapped_cards.append(rendered)
        else:
            exact_cards.append(rendered)

    mapping_rows = "\n".join(
        f"<tr><td>{html.escape(key)}</td><td><code>{html.escape(value)}</code></td></tr>"
        for key, value in plan["mapping_preview"].items()
    )
    conflict_rows = "\n".join(
        f"<tr><td>{html.escape(item['cz'])}</td><td><code>{html.escape(item['current'])}</code></td>"
        f"<td><code>{html.escape(item['proposed'])}</code></td><td>{html.escape(item['decision'])}</td></tr>"
        for item in plan["preserved_mapping_conflicts"]
    )
    published = (
        (PICTNEW / "VocabularyEN_MMTX_copy_receipt_20260824.json").is_file()
        and (PICTNEW / "VocabularyEN_MMTX_mapping_apply_receipt_20260824.json").is_file()
    )
    status_text = (
        "Obrázky byly schváleny, zkopírovány bez přepisování a centrální mapping byl aplikován."
        if published
        else "Ještě není publikováno ani zkopírováno do hlavního Pict."
    )
    next_text = (
        "Webový sync byl následně ověřen samostatnou kontrolou."
        if published
        else "Po schválení se provede kopie bez přepisování, mapping preview/apply a webový sync."
    )
    return f"""<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><title>VocabularyEN + MMTX review 2026-08-24</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:24px;background:#f4f7f9;color:#17202a}}
h1,h2{{margin-top:32px}} .summary{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 2px 10px #0001}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}}
.card{{background:#fff;border-radius:12px;padding:10px;box-shadow:0 2px 8px #0001}} .card img{{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:8px}}
.card h3{{font-size:16px;margin:8px 0 4px}} .card p{{font-size:13px;margin:0 0 7px;color:#52616b}} code{{font-size:12px}}
table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{border:1px solid #d9e2ec;padding:8px;text-align:left}}th{{background:#eaf0f5}}
</style></head><body>
<h1>VocabularyEN + MMTX — kontrolní galerie</h1>
<div class="summary"><strong>{html.escape(status_text)}</strong><br>
120 nových řádků: 35 nově generovaných motivů, 33 objektů převzatých z Forest School,
21 vhodných existujících obrázků přes mapping a 27 přímých existujících obrázků.
{html.escape(next_text)}</div>
<h2>1. Nově generované obrázky (35)</h2><div class="grid">{generated_cards}</div>
<h2>2. Hotové objekty Forest School k převzetí (33)</h2><div class="grid">{''.join(forest_cards)}</div>
<h2>3. Existující obrázky použité přes mapping (21)</h2><div class="grid">{''.join(mapped_cards)}</div>
<h2>4. Přímé existující obrázky (27)</h2><div class="grid">{''.join(exact_cards)}</div>
<h2>5. Návrh nových mapping položek ({len(plan['mapping_preview'])})</h2>
<table><thead><tr><th>CZ klíč</th><th>image stem</th></tr></thead><tbody>{mapping_rows}</tbody></table>
<h2>6. Existující mapping zachovaný beze změny ({len(plan['preserved_mapping_conflicts'])})</h2>
<table><thead><tr><th>CZ klíč</th><th>současná hodnota</th><th>nový kandidát</th><th>rozhodnutí</th></tr></thead><tbody>{conflict_rows}</tbody></table>
</body></html>"""


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    files = generated_files()
    requested = {request["image_name"] for request in plan["requests"]}
    if set(files) != requested:
        missing = sorted(requested - set(files))
        extra = sorted(set(files) - requested)
        raise SystemExit(f"Generated set mismatch. Missing={missing}; extra={extra}")

    validations = {stem: validate_image(path) for stem, path in sorted(files.items())}
    build_batch_reports(plan, files)
    MASTER_REVIEW.write_text(render_master_review(plan, files), encoding="utf-8")
    print(f"Validated generated images: {len(validations)}")
    print(f"Largest generated image: {max(item['bytes'] for item in validations.values())} bytes")
    print(f"Batch review files: {len({path.parent for path in files.values()})}")
    print(f"Wrote: {MASTER_REVIEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
