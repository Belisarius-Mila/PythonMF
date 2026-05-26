from __future__ import annotations

import math
from pathlib import Path

from PIL import Image


SIZE = 1254
ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "PictNew" / "generated" / "20260526_forest_school_batch001"
TARGET_DIRS = [
    ROOT / "docs" / "assets",
    ROOT / "MatysekANJ" / "web_mmtx" / "assets",
]
OBJECTS = ["book", "apple", "car", "house"]
KEY = (255, 0, 255)


def remove_magenta_background(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            distance = math.sqrt((r - KEY[0]) ** 2 + (g - KEY[1]) ** 2 + (b - KEY[2]) ** 2)
            if distance < 34:
                pixels[x, y] = (r, g, b, 0)
            elif distance < 90:
                alpha = int(a * (distance - 34) / 56)
                # Despill the magenta fringe without flattening the object colors.
                r = min(r, int((g + b) * 0.75 + 80))
                b = min(b, int((r + g) * 0.80 + 70))
                pixels[x, y] = (r, g, b, alpha)
    return image


def normalize_canvas(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    threshold = alpha.point(lambda value: 255 if value > 12 else 0)
    bbox = threshold.getbbox()
    if not bbox:
        return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    cropped = image.crop(bbox)
    target = 1120
    scale = min(target / cropped.width, target / cropped.height)
    resized = cropped.resize(
        (round(cropped.width * scale), round(cropped.height * scale)),
        Image.Resampling.LANCZOS,
    )
    output = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    output.alpha_composite(resized, ((SIZE - resized.width) // 2, (SIZE - resized.height) // 2))
    return output


def main() -> int:
    written: list[Path] = []
    for name in OBJECTS:
        source = SOURCE_DIR / f"forest_school_{name}.png"
        if not source.exists():
            raise SystemExit(f"Missing source: {source}")
        final = normalize_canvas(remove_magenta_background(Image.open(source)))
        for target_dir in TARGET_DIRS:
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"forest_school_{name}.png"
            final.save(target, "PNG")
            written.append(target)
    print("Wrote:")
    for path in written:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
