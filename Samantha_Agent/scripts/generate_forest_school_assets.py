from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


SIZE = 1254
ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIRS = [
    ROOT / "docs" / "assets",
    ROOT / "MatysekANJ" / "web_mmtx" / "assets",
]


def rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
        alpha,
    )


def jitter_color(color: tuple[int, int, int, int], spread: int = 18) -> tuple[int, int, int, int]:
    r, g, b, a = color
    return (
        max(0, min(255, r + random.randint(-spread, spread))),
        max(0, min(255, g + random.randint(-spread, spread))),
        max(0, min(255, b + random.randint(-spread, spread))),
        a,
    )


def draw_watercolor_poly(
    layer: Image.Image,
    points: list[tuple[float, float]],
    color: tuple[int, int, int, int],
    passes: int = 60,
    jitter: float = 12,
) -> None:
    draw = ImageDraw.Draw(layer, "RGBA")
    base = (color[0], color[1], color[2], min(185, color[3]))
    draw.polygon(points, fill=base)
    for _ in range(passes):
        shifted = [
            (x + random.uniform(-jitter, jitter), y + random.uniform(-jitter, jitter))
            for x, y in points
        ]
        fill = jitter_color(color, 14)
        fill = (fill[0], fill[1], fill[2], max(10, min(34, color[3] // 7)))
        draw.polygon(shifted, fill=fill)


def draw_watercolor_ellipse(
    layer: Image.Image,
    box: tuple[float, float, float, float],
    color: tuple[int, int, int, int],
    passes: int = 80,
    jitter: float = 14,
) -> None:
    draw = ImageDraw.Draw(layer, "RGBA")
    x0, y0, x1, y1 = box
    base = (color[0], color[1], color[2], min(185, color[3]))
    draw.ellipse(box, fill=base)
    for _ in range(passes):
        dx0 = random.uniform(-jitter, jitter)
        dy0 = random.uniform(-jitter, jitter)
        dx1 = random.uniform(-jitter, jitter)
        dy1 = random.uniform(-jitter, jitter)
        fill = jitter_color(color, 14)
        fill = (fill[0], fill[1], fill[2], max(10, min(30, color[3] // 8)))
        draw.ellipse((x0 + dx0, y0 + dy0, x1 + dx1, y1 + dy1), fill=fill)


def draw_outline(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], close: bool = True) -> None:
    line = points + ([points[0]] if close else [])
    draw.line(line, fill=rgba("#6a5138", 178), width=15, joint="curve")
    draw.line(line, fill=rgba("#fff3d5", 190), width=5, joint="curve")


def soft_shadow(base: Image.Image, box: tuple[int, int, int, int]) -> None:
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow, "RGBA")
    draw.ellipse(box, fill=(55, 40, 25, 42))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    base.alpha_composite(shadow)


def paper_texture(img: Image.Image, strength: int = 28) -> None:
    random.seed(20260526)
    pixels = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pixels, "RGBA")
    for _ in range(7000):
        x = random.randrange(SIZE)
        y = random.randrange(SIZE)
        a = random.randrange(4, strength)
        draw.point((x, y), fill=(255, 255, 255, a))
    img.alpha_composite(pixels.filter(ImageFilter.GaussianBlur(0.6)))


def normalize_asset(img: Image.Image, target: int = 1140) -> Image.Image:
    alpha = img.getchannel("A")
    threshold = alpha.point(lambda value: 255 if value > 44 else 0)
    bbox = threshold.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    width, height = cropped.size
    scale = min(target / width, target / height)
    resized = cropped.resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    result.alpha_composite(resized, ((SIZE - resized.width) // 2, (SIZE - resized.height) // 2))
    return result


def save_asset(name: str, image: Image.Image) -> None:
    image = normalize_asset(image)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=3))
    for output_dir in OUTPUT_DIRS:
        output_dir.mkdir(parents=True, exist_ok=True)
        image.save(output_dir / f"forest_school_{name}.png", "PNG")


def make_book() -> Image.Image:
    random.seed(1001)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    soft_shadow(img, (220, 805, 1030, 1055))
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    left = [(205, 360), (602, 445), (602, 965), (205, 835)]
    right = [(652, 445), (1040, 345), (1040, 825), (652, 965)]
    draw_watercolor_poly(layer, left, rgba("#f4cc58", 230), 95, 11)
    draw_watercolor_poly(layer, right, rgba("#e96d64", 230), 95, 11)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.7)))
    d = ImageDraw.Draw(img, "RGBA")
    draw_outline(d, left)
    draw_outline(d, right)
    d.line([(627, 405), (627, 990)], fill=rgba("#6a5138", 150), width=17)
    d.line([(627, 405), (627, 990)], fill=rgba("#fff3d5", 155), width=5)
    for offset in [0, 85, 170]:
        d.line([(300, 515 + offset), (500, 560 + offset)], fill=rgba("#75583c", 105), width=13)
        d.line([(770, 530 + offset), (955, 480 + offset)], fill=rgba("#75583c", 105), width=13)
    d.arc((310, 360, 620, 610), 204, 260, fill=rgba("#fff8df", 85), width=24)
    paper_texture(img)
    return img


def make_apple() -> Image.Image:
    random.seed(1002)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    soft_shadow(img, (300, 825, 960, 1060))
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_watercolor_ellipse(layer, (285, 370, 670, 905), rgba("#e94842", 230), 95, 18)
    draw_watercolor_ellipse(layer, (575, 365, 970, 905), rgba("#f2594c", 230), 95, 18)
    draw_watercolor_ellipse(layer, (410, 330, 830, 940), rgba("#f04f43", 220), 70, 20)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.8)))
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse((285, 370, 670, 905), outline=rgba("#6a5138", 145), width=15)
    d.ellipse((575, 365, 970, 905), outline=rgba("#6a5138", 145), width=15)
    d.line([(625, 350), (690, 170)], fill=rgba("#724a2e", 210), width=44)
    d.line([(625, 350), (690, 170)], fill=rgba("#9a6b3d", 130), width=20)
    leaf = [(690, 220), (805, 115), (1010, 170), (878, 295)]
    draw_watercolor_poly(img, leaf, rgba("#5faa56", 225), 65, 9)
    draw_outline(d, leaf)
    d.arc((390, 415, 650, 675), 190, 265, fill=rgba("#fff7dc", 120), width=28)
    paper_texture(img)
    return img


def make_car() -> Image.Image:
    random.seed(1003)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    soft_shadow(img, (185, 835, 1080, 1050))
    body = [(180, 720), (270, 565), (455, 525), (570, 390), (825, 405), (975, 545), (1085, 590), (1110, 770), (1030, 865), (255, 865)]
    cabin = [(465, 530), (590, 420), (805, 432), (930, 560), (725, 570)]
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_watercolor_poly(layer, body, rgba("#55a5e8", 230), 100, 12)
    draw_watercolor_poly(layer, cabin, rgba("#bfe7ff", 210), 70, 8)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.7)))
    d = ImageDraw.Draw(img, "RGBA")
    draw_outline(d, body)
    draw_outline(d, cabin)
    d.line([(610, 430), (610, 568)], fill=rgba("#6a5138", 125), width=11)
    for cx in [385, 900]:
        draw_watercolor_ellipse(img, (cx - 110, 760, cx + 110, 980), rgba("#3c3c42", 235), 55, 7)
        d.ellipse((cx - 110, 760, cx + 110, 980), outline=rgba("#2a292b", 230), width=18)
        d.ellipse((cx - 55, 815, cx + 55, 925), fill=rgba("#f7e8b4", 230), outline=rgba("#6a5138", 135), width=9)
    d.ellipse((235, 670, 325, 735), fill=rgba("#ffe66d", 205), outline=rgba("#6a5138", 90), width=6)
    d.ellipse((1000, 665, 1080, 725), fill=rgba("#f06d5d", 210), outline=rgba("#6a5138", 90), width=6)
    d.arc((310, 600, 650, 800), 205, 255, fill=rgba("#fff8df", 125), width=24)
    paper_texture(img)
    return img


def make_house() -> Image.Image:
    random.seed(1004)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    soft_shadow(img, (240, 865, 1010, 1070))
    wall = [(320, 520), (945, 520), (945, 920), (320, 920)]
    roof = [(260, 535), (635, 220), (1015, 535)]
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_watercolor_poly(layer, wall, rgba("#f0c46f", 230), 95, 10)
    draw_watercolor_poly(layer, roof, rgba("#d85645", 230), 100, 12)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.8)))
    d = ImageDraw.Draw(img, "RGBA")
    draw_outline(d, wall)
    draw_outline(d, roof)
    door = [(570, 680), (720, 680), (720, 920), (570, 920)]
    draw_watercolor_poly(img, door, rgba("#8b5a38", 225), 60, 7)
    draw_outline(d, door)
    for x0, y0 in [(390, 610), (770, 610)]:
        d.rounded_rectangle((x0, y0, x0 + 120, y0 + 115), radius=16, fill=rgba("#bfe7ff", 210), outline=rgba("#6a5138", 130), width=10)
        d.line([(x0 + 60, y0 + 8), (x0 + 60, y0 + 107)], fill=rgba("#fff7dc", 160), width=6)
        d.line([(x0 + 8, y0 + 58), (x0 + 112, y0 + 58)], fill=rgba("#fff7dc", 160), width=6)
    d.ellipse((685, 790, 710, 815), fill=rgba("#f7df6a", 230), outline=rgba("#6a5138", 110), width=4)
    d.arc((350, 525, 625, 760), 200, 260, fill=rgba("#fff8df", 110), width=24)
    paper_texture(img)
    return img


def main() -> None:
    assets = {
        "book": make_book(),
        "apple": make_apple(),
        "car": make_car(),
        "house": make_house(),
    }
    for name, image in assets.items():
        save_asset(name, image)
    print("Generated:", ", ".join(sorted(assets)))


if __name__ == "__main__":
    main()
