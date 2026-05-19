#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "Pict"
SIZE = 1024
CENTER = SIZE // 2


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE))
    pix = img.load()
    for y in range(SIZE):
        t = y / max(1, SIZE - 1)
        row = tuple(lerp(top[i], bottom[i], t) for i in range(3)) + (255,)
        for x in range(SIZE):
            pix[x, y] = row
    return img


def make_canvas(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = gradient(top, bottom)
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse((-120, -80, 460, 500), fill=(255, 255, 255, 28))
    draw.ellipse((650, 80, 1120, 550), fill=(255, 255, 255, 20))
    draw.ellipse((120, 650, 540, 1080), fill=(255, 255, 255, 18))
    img = Image.alpha_composite(img, overlay)

    panel = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle((70, 70, 954, 954), radius=64, fill=(255, 255, 255, 222))
    panel = panel.filter(ImageFilter.GaussianBlur(0.3))
    img = Image.alpha_composite(img, panel)
    return img, ImageDraw.Draw(img)


def draw_shadow_circle(draw: ImageDraw.ImageDraw, box, fill, shadow=(0, 0, 0, 40), offset=18):
    x1, y1, x2, y2 = box
    draw.ellipse((x1 + offset, y1 + offset, x2 + offset, y2 + offset), fill=shadow)
    draw.ellipse(box, fill=fill)


def draw_sun(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, color=(255, 205, 72)):
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        x1 = cx + int(math.cos(a) * (r + 16))
        y1 = cy + int(math.sin(a) * (r + 16))
        x2 = cx + int(math.cos(a) * (r + 72))
        y2 = cy + int(math.sin(a) * (r + 72))
        draw.line((x1, y1, x2, y2), fill=color, width=14)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def draw_cloud(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, fill=(255, 255, 255, 240)):
    r1 = int(46 * scale)
    r2 = int(58 * scale)
    r3 = int(40 * scale)
    draw.ellipse((x, y, x + 2 * r1, y + 2 * r1), fill=fill)
    draw.ellipse((x + 45 * scale, y - 25 * scale, x + 45 * scale + 2 * r2, y - 25 * scale + 2 * r2), fill=fill)
    draw.ellipse((x + 120 * scale, y + 10 * scale, x + 120 * scale + 2 * r3, y + 10 * scale + 2 * r3), fill=fill)
    draw.rounded_rectangle((x + 20 * scale, y + 45 * scale, x + 170 * scale, y + 95 * scale), radius=30, fill=fill)


def draw_car(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float, body=(219, 68, 55), roof=(250, 250, 255)):
    w = int(360 * scale)
    h = int(120 * scale)
    draw.rounded_rectangle((x, y + h * 0.3, x + w, y + h), radius=int(28 * scale), fill=body)
    draw.polygon(
        [
            (x + w * 0.18, y + h * 0.3),
            (x + w * 0.38, y),
            (x + w * 0.72, y),
            (x + w * 0.85, y + h * 0.3),
        ],
        fill=body,
    )
    draw.rounded_rectangle((x + w * 0.35, y + 12 * scale, x + w * 0.68, y + h * 0.28), radius=int(18 * scale), fill=roof)
    for wx in (x + w * 0.24, x + w * 0.76):
        draw.ellipse((wx - 38 * scale, y + h * 0.72, wx + 38 * scale, y + h * 1.35), fill=(43, 50, 64))
        draw.ellipse((wx - 18 * scale, y + h * 0.9, wx + 18 * scale, y + h * 1.08), fill=(220, 220, 230))
    draw.rectangle((x + w * 0.05, y + h * 0.5, x + w * 0.13, y + h * 0.62), fill=(255, 232, 158))
    draw.rectangle((x + w * 0.87, y + h * 0.5, x + w * 0.95, y + h * 0.62), fill=(255, 110, 102))


def draw_storefront(draw: ImageDraw.ImageDraw):
    draw.rounded_rectangle((250, 300, 780, 720), radius=36, fill=(247, 231, 209))
    for i, color in enumerate([(227, 83, 53), (255, 245, 235)] * 4):
        draw.rectangle((250 + i * 66, 260, 316 + i * 66, 360), fill=color)
    draw.rectangle((250, 360, 780, 390), fill=(160, 91, 60))
    draw.rounded_rectangle((300, 430, 470, 720), radius=24, fill=(153, 101, 74))
    draw.rounded_rectangle((520, 430, 730, 620), radius=24, fill=(170, 219, 239))
    draw.line((625, 430, 625, 620), fill=(255, 255, 255, 160), width=8)
    draw.line((520, 525, 730, 525), fill=(255, 255, 255, 160), width=8)


def draw_church(draw: ImageDraw.ImageDraw):
    draw.rectangle((340, 330, 710, 760), fill=(236, 219, 189))
    draw.polygon([(525, 210), (295, 370), (755, 370)], fill=(186, 79, 73))
    draw.rectangle((470, 520, 580, 760), fill=(110, 78, 56))
    draw.ellipse((470, 460, 580, 570), fill=(113, 177, 219))
    draw.rectangle((620, 260, 690, 760), fill=(227, 212, 180))
    draw.polygon([(655, 160), (600, 280), (710, 280)], fill=(186, 79, 73))
    draw.rectangle((648, 115, 662, 170), fill=(126, 93, 70))
    draw.rectangle((630, 132, 680, 146), fill=(126, 93, 70))


def draw_exit(draw: ImageDraw.ImageDraw):
    draw.rounded_rectangle((260, 220, 620, 760), radius=24, fill=(85, 157, 96))
    draw.rounded_rectangle((320, 270, 560, 760), radius=18, fill=(242, 245, 249))
    draw.ellipse((520, 490, 548, 518), fill=(85, 157, 96))
    draw.rounded_rectangle((610, 360, 820, 520), radius=32, fill=(68, 180, 92))
    draw.polygon([(670, 440), (760, 440), (760, 400), (840, 470), (760, 540), (760, 500), (670, 500)], fill=(255, 255, 255))


def draw_beach(draw: ImageDraw.ImageDraw):
    draw_sun(draw, 760, 250, 68)
    draw.rectangle((180, 520, 844, 700), fill=(85, 196, 237))
    draw.rectangle((120, 700, 900, 820), fill=(237, 210, 145))
    draw.line((180, 560, 844, 560), fill=(255, 255, 255, 150), width=8)
    draw.line((180, 610, 844, 610), fill=(255, 255, 255, 120), width=6)
    draw.line((380, 470, 340, 740), fill=(124, 83, 52), width=18)
    draw.polygon([(350, 470), (500, 530), (360, 610)], fill=(236, 96, 88))
    draw.polygon([(350, 470), (220, 540), (340, 610)], fill=(255, 245, 240))
    draw.ellipse((600, 720, 680, 760), fill=(255, 255, 255, 120))


def draw_digits(draw: ImageDraw.ImageDraw):
    font = load_font(300)
    colors = [(234, 84, 85), (78, 156, 236), (255, 186, 66)]
    positions = [(220, 270), (420, 230), (620, 290)]
    for digit, pos, color in zip(("1", "2", "3"), positions, colors):
        shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.text((pos[0] + 16, pos[1] + 18), digit, font=font, fill=(0, 0, 0, 45))
        draw.bitmap((0, 0), shadow, fill=None)
        draw.text(pos, digit, font=font, fill=color)


def draw_pin(draw: ImageDraw.ImageDraw):
    draw.rounded_rectangle((260, 620, 770, 720), radius=32, fill=(118, 190, 210))
    draw.ellipse((380, 250, 660, 530), fill=(229, 92, 92))
    draw.ellipse((455, 325, 585, 455), fill=(255, 255, 255))
    draw.polygon([(520, 560), (410, 430), (630, 430)], fill=(229, 92, 92))
    draw.rounded_rectangle((430, 650, 600, 710), radius=18, fill=(255, 255, 255, 210))


def draw_roman(draw: ImageDraw.ImageDraw):
    draw.ellipse((280, 690, 770, 830), fill=(218, 196, 168))
    for x in (340, 470, 600):
        draw.rectangle((x, 320, x + 70, 720), fill=(239, 229, 210))
        for i in range(8):
            draw.arc((x - 20, 330 + i * 45, x + 90, 380 + i * 45), 0, 180, fill=(225, 215, 198), width=7)
        draw.rectangle((x - 25, 280, x + 95, 330), fill=(226, 214, 194))
        draw.rectangle((x - 25, 720, x + 95, 760), fill=(208, 194, 173))
    draw.arc((360, 180, 680, 460), 180, 360, fill=(120, 167, 82), width=24)
    draw.arc((360, 180, 680, 460), 170, 350, fill=(120, 167, 82), width=24)


def draw_russia(draw: ImageDraw.ImageDraw):
    draw.rectangle((260, 220, 760, 520), fill=(255, 255, 255))
    draw.rectangle((260, 320, 760, 520), fill=(60, 116, 214))
    draw.rectangle((260, 420, 760, 520), fill=(216, 66, 66))
    draw.rectangle((430, 420, 600, 760), fill=(239, 187, 104))
    draw.ellipse((360, 300, 670, 520), fill=(182, 90, 77))
    draw.rectangle((500, 220, 530, 300), fill=(239, 187, 104))
    draw.ellipse((480, 170, 550, 240), fill=(239, 187, 104))


def draw_slovakia(draw: ImageDraw.ImageDraw):
    draw.polygon([(220, 690), (400, 420), (560, 650)], fill=(91, 130, 193))
    draw.polygon([(420, 690), (610, 360), (790, 690)], fill=(124, 156, 219))
    draw.rectangle((250, 200, 770, 330), fill=(255, 255, 255))
    draw.rectangle((250, 330, 770, 460), fill=(58, 104, 197))
    draw.rectangle((250, 460, 770, 590), fill=(210, 64, 66))
    draw.rounded_rectangle((340, 300, 470, 480), radius=30, fill=(210, 64, 66))
    draw.rectangle((398, 325, 412, 450), fill=(255, 255, 255))
    draw.rectangle((360, 368, 450, 382), fill=(255, 255, 255))
    draw.polygon([(360, 450), (405, 400), (450, 450)], fill=(91, 130, 193))


def draw_spain(draw: ImageDraw.ImageDraw):
    draw.rectangle((220, 220, 800, 340), fill=(194, 47, 51))
    draw.rectangle((220, 340, 800, 540), fill=(245, 194, 70))
    draw.rectangle((220, 540, 800, 660), fill=(194, 47, 51))
    draw.pieslice((280, 450, 620, 790), start=210, end=340, fill=(217, 94, 88), outline=(139, 55, 50), width=8)
    draw.pieslice((420, 450, 760, 790), start=200, end=330, fill=(245, 178, 80), outline=(173, 103, 39), width=8)
    draw_sun(draw, 770, 220, 40, color=(255, 208, 85))


def draw_technician(draw: ImageDraw.ImageDraw):
    draw.rounded_rectangle((260, 470, 770, 720), radius=28, fill=(72, 94, 135))
    draw.rectangle((320, 520, 710, 680), fill=(165, 218, 237))
    draw.rectangle((450, 720, 580, 760), fill=(95, 103, 116))
    draw.rectangle((400, 760, 630, 790), fill=(95, 103, 116))
    draw.ellipse((260, 250, 470, 460), fill=(242, 191, 136))
    draw.rectangle((320, 440, 410, 520), fill=(242, 191, 136))
    draw.rectangle((340, 470, 560, 640), fill=(72, 132, 211))
    draw.line((620, 330, 770, 220), fill=(72, 72, 82), width=28)
    draw.line((620, 330, 770, 440), fill=(72, 72, 82), width=28)
    draw.ellipse((560, 260, 680, 380), outline=(72, 72, 82), width=22)
    draw.rectangle((670, 205, 820, 260), fill=(72, 72, 82))


def draw_zero(draw: ImageDraw.ImageDraw):
    draw_shadow_circle(draw, (280, 170, 760, 650), fill=(108, 154, 232))
    draw.ellipse((390, 280, 650, 540), fill=(255, 255, 255))
    for px, py, color in ((250, 720, (245, 187, 64)), (420, 770, (84, 190, 141)), (680, 740, (234, 84, 85))):
        draw.ellipse((px, py, px + 80, py + 80), fill=color)


def draw_lemon(draw: ImageDraw.ImageDraw):
    draw.ellipse((260, 300, 770, 690), fill=(250, 224, 87))
    draw.ellipse((610, 250, 820, 460), fill=(241, 208, 74))
    draw.pieslice((500, 360, 850, 710), 20, 340, fill=(255, 245, 170), outline=(240, 214, 92), width=10)
    for angle in range(30, 360, 60):
        a = math.radians(angle)
        x = 675 + math.cos(a) * 120
        y = 535 + math.sin(a) * 120
        draw.line((675, 535, x, y), fill=(240, 214, 92), width=8)
    draw.polygon([(300, 290), (360, 180), (450, 260)], fill=(105, 173, 91))


def draw_banana(draw: ImageDraw.ImageDraw):
    draw.pieslice((220, 250, 840, 820), 210, 330, fill=(246, 211, 74), outline=(215, 174, 52), width=18)
    draw.pieslice((300, 290, 760, 760), 210, 330, fill=(255, 255, 255, 0), outline=(255, 242, 179), width=18)
    draw.rounded_rectangle((250, 540, 340, 590), radius=18, fill=(118, 82, 42))
    draw.rounded_rectangle((730, 350, 790, 400), radius=18, fill=(118, 82, 42))


def draw_czech(draw: ImageDraw.ImageDraw):
    draw.rectangle((250, 230, 780, 520), fill=(255, 255, 255))
    draw.rectangle((250, 375, 780, 520), fill=(213, 70, 72))
    draw.polygon([(250, 230), (250, 520), (480, 375)], fill=(48, 95, 189))
    draw.rectangle((400, 500, 460, 760), fill=(158, 112, 79))
    draw.rectangle((520, 420, 630, 760), fill=(205, 173, 125))
    draw.polygon([(575, 330), (470, 430), (680, 430)], fill=(149, 80, 70))


def draw_autumn(draw: ImageDraw.ImageDraw):
    draw.rectangle((500, 260, 560, 760), fill=(126, 89, 60))
    draw.ellipse((290, 220, 670, 500), fill=(236, 127, 70))
    draw.ellipse((470, 180, 790, 460), fill=(241, 184, 76))
    draw.ellipse((360, 360, 760, 620), fill=(201, 94, 63))
    for x, y, color in ((250, 640, (236, 127, 70)), (380, 720, (201, 94, 63)), (700, 650, (241, 184, 76))):
        draw.polygon([(x, y), (x + 42, y - 70), (x + 84, y), (x + 42, y + 70)], fill=color)


def draw_pig(draw: ImageDraw.ImageDraw):
    draw.ellipse((270, 340, 760, 680), fill=(242, 156, 175))
    draw.ellipse((650, 380, 860, 560), fill=(242, 156, 175))
    draw.polygon([(690, 350), (740, 280), (780, 360)], fill=(226, 128, 152))
    draw.polygon([(780, 380), (840, 300), (860, 390)], fill=(226, 128, 152))
    draw.ellipse((720, 440, 820, 510), fill=(236, 181, 192))
    draw.ellipse((745, 462, 762, 479), fill=(193, 102, 120))
    draw.ellipse((782, 462, 799, 479), fill=(193, 102, 120))
    for leg_x in (360, 470, 590, 700):
        draw.rectangle((leg_x, 620, leg_x + 36, 760), fill=(226, 128, 152))
    draw.arc((260, 470, 330, 540), 20, 320, fill=(226, 128, 152), width=12)


def draw_basketball(draw: ImageDraw.ImageDraw):
    draw.rectangle((650, 220, 820, 520), fill=(240, 247, 255))
    draw.rectangle((725, 520, 745, 760), fill=(150, 150, 160))
    draw.arc((620, 350, 810, 470), 200, 340, fill=(206, 73, 50), width=16)
    draw.line((646, 398, 784, 398), fill=(255, 255, 255), width=8)
    draw_shadow_circle(draw, (240, 360, 560, 680), fill=(231, 132, 50))
    draw.arc((260, 380, 540, 660), 20, 160, fill=(120, 66, 38), width=10)
    draw.arc((260, 380, 540, 660), 200, 340, fill=(120, 66, 38), width=10)
    draw.arc((300, 340, 500, 700), 90, 270, fill=(120, 66, 38), width=10)
    draw.arc((300, 340, 500, 700), -90, 90, fill=(120, 66, 38), width=10)


def draw_volleyball(draw: ImageDraw.ImageDraw):
    draw_shadow_circle(draw, (280, 250, 720, 690), fill=(245, 248, 252))
    draw.arc((280, 250, 720, 690), 30, 150, fill=(102, 144, 209), width=16)
    draw.arc((280, 250, 720, 690), 210, 330, fill=(102, 144, 209), width=16)
    draw.arc((350, 220, 810, 760), 120, 240, fill=(102, 144, 209), width=16)
    draw.arc((210, 220, 670, 760), -60, 60, fill=(102, 144, 209), width=16)
    draw.line((160, 680, 860, 680), fill=(118, 118, 128), width=12)
    for x in range(220, 820, 80):
        draw.line((x, 500, x, 820), fill=(190, 190, 200), width=6)
    for y in range(540, 780, 60):
        draw.line((180, y, 840, y), fill=(190, 190, 200), width=6)


def draw_city(draw: ImageDraw.ImageDraw):
    colors = [(90, 116, 156), (118, 143, 183), (144, 169, 199), (74, 92, 121)]
    x = 160
    widths = [110, 90, 140, 120, 90, 130]
    heights = [390, 470, 340, 520, 420, 360]
    for i, (w, h) in enumerate(zip(widths, heights)):
        draw.rectangle((x, 760 - h, x + w, 760), fill=colors[i % len(colors)])
        for wx in range(x + 18, x + w - 16, 28):
            for wy in range(780 - h, 730, 42):
                draw.rounded_rectangle((wx, wy, wx + 14, wy + 24), radius=4, fill=(255, 221, 139))
        x += w + 24
    draw.rectangle((120, 760, 904, 820), fill=(73, 80, 92))


def draw_formula(draw: ImageDraw.ImageDraw):
    draw.polygon(
        [
            (230, 580), (430, 500), (640, 500), (820, 560), (760, 620), (620, 650),
            (560, 760), (430, 760), (400, 650), (260, 620)
        ],
        fill=(218, 47, 52),
    )
    draw.rectangle((440, 430, 550, 500), fill=(34, 43, 61))
    for wx in (320, 690):
        draw.ellipse((wx - 70, 620, wx + 70, 760), fill=(38, 43, 56))
        draw.ellipse((wx - 34, 656, wx + 34, 724), fill=(205, 205, 215))
    draw.rectangle((240, 540, 820, 575), fill=(240, 240, 245))
    for i in range(6):
        draw.rectangle((190 + i * 110, 780, 250 + i * 110, 840), fill=(255, 255, 255) if i % 2 == 0 else (54, 54, 62))


def draw_auto(draw: ImageDraw.ImageDraw):
    draw_car(draw, 270, 420, 1.2, body=(58, 132, 223), roof=(240, 248, 255))


def draw_automobilismo(draw: ImageDraw.ImageDraw):
    for i in range(4):
        color = (255, 255, 255) if i % 2 == 0 else (45, 48, 58)
        draw.rectangle((620 + i * 40, 200, 660 + i * 40, 380), fill=color)
        draw.rectangle((620, 200 + i * 40, 780, 240 + i * 40), fill=color)
    draw.arc((200, 260, 620, 680), 200, 340, fill=(220, 66, 54), width=32)
    draw.arc((250, 300, 570, 620), 200, 340, fill=(236, 236, 242), width=26)
    draw.rectangle((360, 240, 455, 330), fill=(34, 43, 61))
    draw.rectangle((315, 430, 505, 620), fill=(34, 43, 61))
    draw.rectangle((370, 600, 450, 700), fill=(236, 236, 242))


def save_image(name: str, top: tuple[int, int, int], bottom: tuple[int, int, int], renderer) -> None:
    img, draw = make_canvas(top, bottom)
    renderer(draw)
    img.convert("RGB").save(OUT_DIR / f"{name}.png", quality=95)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = [
        ("uscita", (87, 173, 138), (43, 101, 89), draw_exit),
        ("negozio", (247, 190, 118), (223, 138, 88), draw_storefront),
        ("chiesa", (130, 183, 220), (92, 137, 186), draw_church),
        ("estate", (95, 196, 238), (250, 202, 118), draw_beach),
        ("macchina", (242, 125, 106), (200, 76, 83), lambda d: draw_car(d, 250, 420, 1.2)),
        ("numero", (148, 176, 250), (90, 123, 212), draw_digits),
        ("posto", (139, 195, 219), (73, 136, 179), draw_pin),
        ("romano", (226, 196, 143), (189, 148, 99), draw_roman),
        ("russo", (174, 199, 248), (101, 126, 193), draw_russia),
        ("slovacco", (150, 194, 241), (98, 139, 204), draw_slovakia),
        ("spagna", (246, 196, 109), (210, 80, 73), draw_spain),
        ("tecnico", (154, 182, 217), (105, 131, 176), draw_technician),
        ("zero", (141, 175, 244), (73, 116, 208), draw_zero),
        ("limone", (246, 221, 111), (208, 180, 73), draw_lemon),
        ("banana", (249, 226, 129), (219, 183, 76), draw_banana),
        ("ceco", (154, 181, 226), (94, 118, 187), draw_czech),
        ("autunno", (237, 166, 93), (191, 103, 62), draw_autumn),
        ("porco", (250, 176, 193), (228, 127, 159), draw_pig),
        ("pallacanestro", (247, 183, 105), (223, 123, 76), draw_basketball),
        ("pallavolo", (165, 196, 247), (106, 146, 215), draw_volleyball),
        ("auto", (110, 159, 239), (71, 114, 199), draw_auto),
        ("automobilismo", (161, 161, 176), (86, 90, 108), draw_automobilismo),
        ("citta", (146, 168, 210), (82, 103, 143), draw_city),
        ("formula", (245, 133, 110), (204, 69, 77), draw_formula),
    ]
    for name, top, bottom, renderer in images:
        save_image(name, top, bottom, renderer)
        print(f"OK  {OUT_DIR / f'{name}.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
