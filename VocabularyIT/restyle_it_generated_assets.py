#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


REPO_ROOT = Path(__file__).resolve().parents[1]
PICT_DIR = REPO_ROOT / "Pict"
SCRIPT_SOURCES = [
    REPO_ROOT / "VocabularyIT" / "generate_it_group_a_images.py",
    REPO_ROOT / "VocabularyIT" / "generate_it_group_b_images.py",
    REPO_ROOT / "VocabularyIT" / "generate_it_group_c_images.py",
    REPO_ROOT / "VocabularyIT" / "generate_it_group_a_remaining_images.py",
]


def collect_managed_asset_names() -> list[str]:
    names: list[str] = []
    pattern = re.compile(r'\("([a-z0-9]+)"\s*,\s*\(')
    for script in SCRIPT_SOURCES:
        text = script.read_text(encoding="utf-8")
        names.extend(pattern.findall(text))
    # Preserve stable order while removing duplicates.
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def add_cartoon_finish(src: Path) -> None:
    img = Image.open(src).convert("RGBA").resize((1024, 1024), Image.LANCZOS)
    crop = img.crop((70, 70, 954, 954)).resize((840, 840), Image.LANCZOS)

    crop = ImageEnhance.Color(crop).enhance(1.22)
    crop = ImageEnhance.Contrast(crop).enhance(1.08)
    crop = ImageEnhance.Sharpness(crop).enhance(1.12)

    gray = crop.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.0))
    edge_mask = edges.point(lambda p: 180 if p > 18 else 0).convert("L")
    edge_mask = edge_mask.filter(ImageFilter.MaxFilter(5))
    outline = Image.new("RGBA", crop.size, (88, 120, 160, 120))
    crop = Image.composite(outline, crop, edge_mask)

    # Mild scene tint so the flat white panel feels closer to EN assets.
    tint = Image.new("RGBA", crop.size, (228, 239, 252, 42))
    crop = Image.alpha_composite(crop, tint)

    canvas = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))

    shadow = Image.new("RGBA", (860, 860), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((0, 0, 859, 859), radius=86, fill=(0, 0, 0, 45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(shadow, (96, 108))

    panel = Image.new("RGBA", (860, 860), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle(
        (0, 0, 859, 859),
        radius=86,
        fill=(246, 250, 255, 255),
        outline=(196, 217, 241, 255),
        width=8,
    )
    canvas.alpha_composite(panel, (82, 86))

    mask = Image.new("L", (840, 840), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((0, 0, 839, 839), radius=72, fill=255)
    canvas.paste(crop, (92, 96), mask)

    canvas.convert("RGB").save(src, quality=95)


def main() -> int:
    names = collect_managed_asset_names()
    for name in names:
        path = PICT_DIR / f"{name}.png"
        if not path.exists():
            print(f"SKIP {path}")
            continue
        add_cartoon_finish(path)
        print(f"OK  {path}")
    print(f"Restyled assets: {len(names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
