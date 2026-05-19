#!/usr/bin/env python3
from __future__ import annotations

import math

from PIL import ImageDraw

from generate_it_group_a_images import OUT_DIR, draw_cloud, draw_shadow_circle, draw_sun, save_image


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color, width: int = 18, head: int = 42) -> None:
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    left = angle + math.radians(150)
    right = angle - math.radians(150)
    p1 = (x2 + head * math.cos(left), y2 + head * math.sin(left))
    p2 = (x2 + head * math.cos(right), y2 + head * math.sin(right))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def draw_forno(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((270, 260, 754, 780), radius=44, fill=(87, 96, 116))
    draw.rounded_rectangle((340, 360, 684, 620), radius=26, fill=(54, 62, 79))
    draw.rounded_rectangle((380, 405, 644, 585), radius=18, fill=(255, 174, 92))
    draw.arc((395, 430, 460, 525), 200, 340, fill=(255, 231, 170), width=12)
    draw.arc((500, 430, 565, 525), 200, 340, fill=(255, 231, 170), width=12)
    draw.arc((585, 430, 640, 525), 200, 340, fill=(255, 231, 170), width=12)
    for x in (380, 470, 560, 650):
        draw.ellipse((x, 295, x + 28, 323), fill=(220, 220, 228))
    draw.rectangle((470, 650, 554, 705), fill=(220, 220, 228))


def draw_panificio(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((250, 330, 780, 760), radius=36, fill=(247, 231, 209))
    for i, color in enumerate([(227, 83, 53), (255, 245, 235)] * 4):
        draw.rectangle((250 + i * 66, 260, 316 + i * 66, 360), fill=color)
    draw.rectangle((250, 360, 780, 390), fill=(160, 91, 60))
    draw.rounded_rectangle((320, 440, 500, 760), radius=24, fill=(153, 101, 74))
    draw.rounded_rectangle((540, 450, 710, 610), radius=24, fill=(245, 203, 109))
    draw.arc((560, 480, 640, 570), 200, 340, fill=(196, 131, 57), width=10)
    draw.arc((620, 470, 710, 590), 200, 340, fill=(196, 131, 57), width=10)


def draw_esercizio(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((250, 210, 790, 790), radius=34, fill=(252, 250, 244))
    draw.rectangle((420, 210, 440, 790), fill=(214, 218, 228))
    for y in (320, 430, 540, 650):
        draw.rectangle((320, y, 390, y + 52), fill=(129, 176, 226))
        draw.rectangle((470, y + 14, 690, y + 28), fill=(180, 196, 220))
    draw.line((332, 346, 354, 372), fill=(84, 177, 132), width=10)
    draw.line((354, 372, 386, 330), fill=(84, 177, 132), width=10)
    draw.line((332, 566, 354, 592), fill=(84, 177, 132), width=10)
    draw.line((354, 592, 386, 550), fill=(84, 177, 132), width=10)
    draw.line((640, 150, 820, 330), fill=(231, 177, 87), width=24)


def draw_forza(draw: ImageDraw.ImageDraw) -> None:
    draw.line((290, 700, 430, 520), fill=(83, 92, 112), width=28)
    draw.line((590, 520, 730, 700), fill=(83, 92, 112), width=28)
    draw.line((430, 520, 590, 520), fill=(83, 92, 112), width=28)
    for x in (275, 355, 665, 745):
        draw.rectangle((x, 640, x + 24, 760), fill=(231, 98, 82))
    draw.arc((260, 250, 700, 670), 210, 320, fill=(255, 214, 95), width=34)
    draw.line((440, 500, 590, 350), fill=(242, 191, 136), width=34)
    draw.line((590, 350, 710, 420), fill=(242, 191, 136), width=34)


def draw_parola(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((220, 260, 740, 620), radius=42, fill=(252, 250, 244))
    draw.polygon([(380, 620), (450, 720), (500, 620)], fill=(252, 250, 244))
    for y, w in ((350, 350), (445, 300), (540, 250)):
        draw.rounded_rectangle((320, y, 320 + w, y + 24), radius=10, fill=(129, 176, 226))
    draw_shadow_circle(draw, (630, 170, 830, 370), fill=(255, 214, 95))


def draw_viale(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(360, 800), (470, 280), (554, 280), (664, 800)], fill=(83, 92, 112))
    draw.line((512, 720, 512, 360), fill=(255, 214, 95), width=14)
    for x in (250, 330, 690, 770):
        draw.rectangle((x, 430, x + 30, 760), fill=(121, 84, 61))
        draw_shadow_circle(draw, (x - 40, 280, x + 70, 430), fill=(84, 177, 132))


def draw_vocabolo(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((250, 250, 790, 760), radius=34, fill=(252, 250, 244))
    draw.rectangle((500, 250, 520, 760), fill=(214, 218, 228))
    draw.rounded_rectangle((330, 350, 450, 450), radius=22, fill=(255, 214, 95))
    draw.rounded_rectangle((580, 350, 700, 450), radius=22, fill=(91, 146, 223))
    for y in (510, 590, 670):
        draw.rounded_rectangle((330, y, 140 + 330, y + 18), radius=8, fill=(180, 196, 220))
        draw.rounded_rectangle((560, y, 140 + 560, y + 18), radius=8, fill=(180, 196, 220))


def draw_vaniglia(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(450, 720), (580, 720), (540, 860), (490, 860)], fill=(215, 164, 98))
    draw_shadow_circle(draw, (360, 350, 670, 660), fill=(248, 240, 214))
    draw_shadow_circle(draw, (430, 250, 740, 560), fill=(248, 240, 214))
    draw_shadow_circle(draw, (270, 250, 560, 560), fill=(248, 240, 214))
    draw.line((250, 260, 340, 450), fill=(121, 84, 61), width=10)
    draw.line((320, 240, 390, 420), fill=(121, 84, 61), width=10)


def draw_calcio(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((210, 280, 814, 760), fill=(112, 184, 108))
    draw.rectangle((260, 330, 764, 710), outline=(255, 255, 255), width=10)
    draw.line((512, 330, 512, 710), fill=(255, 255, 255), width=8)
    draw.ellipse((430, 448, 594, 612), outline=(255, 255, 255), width=8)
    draw_shadow_circle(draw, (350, 430, 674, 754), fill=(252, 250, 244))
    draw.polygon([(512, 474), (550, 500), (536, 544), (488, 544), (474, 500)], fill=(83, 92, 112))


def draw_gara(draw: ImageDraw.ImageDraw) -> None:
    for i in range(4):
        color = (255, 255, 255) if i % 2 == 0 else (45, 48, 58)
        draw.rectangle((610 + i * 42, 200, 652 + i * 42, 380), fill=color)
        draw.rectangle((610, 200 + i * 42, 778, 242 + i * 42), fill=color)
    draw.arc((180, 330, 720, 880), 200, 330, fill=(83, 92, 112), width=42)
    draw.arc((320, 430, 860, 980), 200, 330, fill=(255, 255, 255), width=34)
    draw.rectangle((260, 580, 390, 760), fill=(255, 214, 95))
    draw.rectangle((430, 500, 560, 760), fill=(129, 176, 226))
    draw.rectangle((600, 620, 730, 760), fill=(228, 102, 101))


def draw_ponte(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((150, 620, 874, 780), fill=(95, 191, 231))
    draw.rectangle((210, 560, 814, 620), fill=(150, 103, 74))
    for x in (290, 430, 570, 710):
        draw.rectangle((x, 620, x + 28, 760), fill=(121, 84, 61))
    draw.arc((240, 360, 784, 800), 200, 340, fill=(226, 214, 194), width=24)


def draw_mercato(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((250, 360, 780, 760), fill=(178, 127, 90))
    for i, color in enumerate([(227, 83, 53), (255, 245, 235)] * 4):
        draw.rectangle((250 + i * 66, 260, 316 + i * 66, 360), fill=color)
    draw.rectangle((250, 360, 780, 390), fill=(160, 91, 60))
    for x, color in ((340, (231, 98, 82)), (490, (255, 214, 95)), (640, (84, 177, 132))):
        draw.ellipse((x, 520, x + 78, 598), fill=color)
        draw.ellipse((x + 36, 460, x + 114, 538), fill=color)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = [
        ("forno", (212, 216, 228), (123, 132, 158), draw_forno),
        ("panificio", (246, 201, 145), (221, 143, 95), draw_panificio),
        ("esercizio", (222, 227, 240), (160, 176, 208), draw_esercizio),
        ("forza", (247, 217, 145), (221, 160, 95), draw_forza),
        ("parola", (221, 232, 247), (154, 181, 226), draw_parola),
        ("viale", (188, 226, 193), (119, 173, 133), draw_viale),
        ("vocabolo", (223, 227, 240), (160, 176, 208), draw_vocabolo),
        ("vaniglia", (248, 235, 194), (226, 198, 133), draw_vaniglia),
        ("calcio", (154, 209, 141), (92, 165, 92), draw_calcio),
        ("gara", (213, 217, 228), (150, 158, 176), draw_gara),
        ("ponte", (168, 215, 243), (107, 174, 223), draw_ponte),
        ("mercato", (246, 201, 145), (221, 143, 95), draw_mercato),
    ]
    for name, top, bottom, renderer in images:
        save_image(name, top, bottom, renderer)
        print(f"OK  {OUT_DIR / f'{name}.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
