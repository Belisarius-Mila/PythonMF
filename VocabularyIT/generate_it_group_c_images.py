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


def draw_clock(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, hour_angle: int = -90, minute_angle: int = 20) -> None:
    draw_shadow_circle(draw, (cx - r, cy - r, cx + r, cy + r), fill=(252, 250, 244))
    draw.ellipse((cx - r + 24, cy - r + 24, cx + r - 24, cy + r - 24), fill=(255, 255, 255))
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        x1 = cx + math.cos(rad) * (r - 36)
        y1 = cy + math.sin(rad) * (r - 36)
        x2 = cx + math.cos(rad) * (r - 16)
        y2 = cy + math.sin(rad) * (r - 16)
        draw.line((x1, y1, x2, y2), fill=(186, 192, 206), width=5)
    for angle, length, width, color in (
        (hour_angle, r * 0.42, 12, (91, 146, 223)),
        (minute_angle, r * 0.58, 9, (84, 177, 132)),
    ):
        rad = math.radians(angle)
        x = cx + math.cos(rad) * length
        y = cy + math.sin(rad) * length
        draw.line((cx, cy, x, y), fill=color, width=width)
    draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(121, 84, 61))


def draw_person(draw: ImageDraw.ImageDraw, cx: int, top: int, scale: float, shirt, pants=(83, 92, 112), skin=(242, 191, 136)) -> None:
    head_r = int(54 * scale)
    body_w = int(160 * scale)
    body_h = int(240 * scale)
    draw.ellipse((cx - head_r, top, cx + head_r, top + 2 * head_r), fill=skin)
    body_top = top + 2 * head_r - int(8 * scale)
    draw.rounded_rectangle((cx - body_w // 2, body_top, cx + body_w // 2, body_top + body_h), radius=int(28 * scale), fill=shirt)
    leg_y = body_top + body_h
    draw.line((cx - int(36 * scale), leg_y, cx - int(60 * scale), leg_y + int(140 * scale)), fill=pants, width=int(18 * scale))
    draw.line((cx + int(36 * scale), leg_y, cx + int(60 * scale), leg_y + int(140 * scale)), fill=pants, width=int(18 * scale))


def draw_sparkle(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color=(255, 224, 128)) -> None:
    draw.polygon(
        [
            (cx, cy - size),
            (cx + size * 0.26, cy - size * 0.26),
            (cx + size, cy),
            (cx + size * 0.26, cy + size * 0.26),
            (cx, cy + size),
            (cx - size * 0.26, cy + size * 0.26),
            (cx - size, cy),
            (cx - size * 0.26, cy - size * 0.26),
        ],
        fill=color,
    )


def draw_fragile(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((440, 300, 584, 360), fill=(173, 219, 237))
    draw.polygon([(470, 360), (554, 360), (530, 620), (494, 620)], fill=(173, 219, 237))
    draw.rectangle((500, 620, 524, 730), fill=(173, 219, 237))
    draw.rounded_rectangle((420, 730, 604, 760), radius=12, fill=(173, 219, 237))
    draw.line((520, 300, 490, 375), fill=(231, 98, 82), width=10)
    draw.line((490, 375, 530, 455), fill=(231, 98, 82), width=10)
    draw.line((530, 455, 500, 540), fill=(231, 98, 82), width=10)
    for cx, cy in ((320, 260), (720, 340), (680, 650)):
        draw_sparkle(draw, cx, cy, 28, color=(255, 214, 95))


def draw_gustoso(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((250, 590, 774, 760), fill=(228, 102, 101))
    draw.ellipse((310, 520, 714, 690), fill=(252, 250, 244))
    draw.ellipse((350, 545, 674, 660), fill=(243, 189, 92))
    draw.arc((390, 420, 470, 560), 180, 330, fill=(255, 255, 255), width=12)
    draw.arc((490, 390, 570, 550), 180, 330, fill=(255, 255, 255), width=12)
    draw.arc((590, 420, 670, 560), 180, 330, fill=(255, 255, 255), width=12)
    draw_sparkle(draw, 710, 320, 36)


def draw_libero(draw: ImageDraw.ImageDraw) -> None:
    draw_sun(draw, 750, 240, 58)
    draw.line((310, 360, 420, 610), fill=(121, 84, 61), width=18)
    draw.line((710, 360, 604, 610), fill=(121, 84, 61), width=18)
    draw.arc((380, 470, 644, 710), 20, 160, fill=(84, 177, 132), width=20)
    draw_shadow_circle(draw, (420, 420, 560, 560), fill=(242, 191, 136))


def draw_stanco(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (280, 220, 744, 684), fill=(255, 214, 95))
    draw.line((390, 410, 470, 400), fill=(68, 78, 94), width=12)
    draw.line((556, 400, 636, 410), fill=(68, 78, 94), width=12)
    draw.arc((390, 420, 470, 470), 0, 180, fill=(68, 78, 94), width=10)
    draw.arc((556, 420, 636, 470), 0, 180, fill=(68, 78, 94), width=10)
    draw.arc((420, 520, 604, 600), 20, 160, fill=(68, 78, 94), width=12)
    draw.text((675, 280), "Z", fill=(129, 176, 226))
    draw.text((735, 220), "Z", fill=(129, 176, 226))


def draw_malato(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (280, 220, 744, 684), fill=(165, 218, 237))
    draw.line((390, 392, 470, 420), fill=(68, 78, 94), width=12)
    draw.line((556, 420, 636, 392), fill=(68, 78, 94), width=12)
    draw.ellipse((420, 450, 455, 485), fill=(68, 78, 94))
    draw.ellipse((571, 450, 606, 485), fill=(68, 78, 94))
    draw.arc((420, 548, 604, 620), 200, 340, fill=(68, 78, 94), width=12)
    draw.rounded_rectangle((418, 610, 604, 650), radius=16, fill=(252, 250, 244))
    draw.rounded_rectangle((470, 625, 584, 635), radius=6, fill=(231, 98, 82))


def draw_chiuso(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((260, 230, 764, 810), radius=36, fill=(226, 214, 194))
    draw.rounded_rectangle((360, 290, 664, 760), radius=26, fill=(150, 103, 74))
    draw.ellipse((594, 500, 628, 534), fill=(235, 204, 104))
    draw.rounded_rectangle((440, 360, 584, 450), radius=20, fill=(231, 98, 82))
    draw.line((452, 372, 572, 438), fill=(255, 255, 255), width=12)
    draw.line((572, 372, 452, 438), fill=(255, 255, 255), width=12)


def draw_freddo(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (300, 250, 724, 674), fill=(129, 176, 226))
    draw.ellipse((440, 390, 580, 530), fill=(242, 191, 136))
    for fx, fy, r in ((290, 280, 34), (730, 340, 28), (250, 540, 26)):
        for angle in range(0, 180, 30):
            a = math.radians(angle)
            dx = math.cos(a) * r
            dy = math.sin(a) * r
            draw.line((fx - dx, fy - dy, fx + dx, fy + dy), fill=(255, 255, 255), width=5)


def draw_pulito(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((280, 320, 744, 700), radius=36, fill=(248, 248, 250))
    draw.line((360, 390, 360, 630), fill=(218, 222, 230), width=8)
    draw.line((440, 390, 440, 630), fill=(218, 222, 230), width=8)
    for cx, cy, size in ((720, 300, 34), (270, 630, 28), (700, 650, 26)):
        draw_sparkle(draw, cx, cy, size)


def draw_sporco(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((260, 280, 764, 760), radius=36, fill=(220, 236, 246))
    draw.rounded_rectangle((340, 360, 684, 520), radius=24, fill=(255, 255, 255))
    draw.ellipse((370, 570, 470, 670), fill=(121, 84, 61))
    for x, y in ((430, 430), (560, 410), (610, 470), (520, 620), (660, 600)):
        draw.ellipse((x, y, x + 50, y + 36), fill=(166, 122, 91))


def draw_turista(draw: ImageDraw.ImageDraw) -> None:
    draw_person(draw, 380, 220, 1.1, shirt=(84, 177, 132), pants=(83, 92, 112))
    draw.rounded_rectangle((305, 470, 460, 620), radius=28, fill=(91, 146, 223))
    draw.rectangle((470, 360, 760, 600), fill=(252, 250, 244))
    draw.line((615, 360, 615, 600), fill=(200, 210, 224), width=8)
    draw.line((470, 480, 760, 480), fill=(200, 210, 224), width=8)
    draw.polygon([(540, 430), (575, 500), (610, 430)], fill=(231, 98, 82))


def draw_aiuto(draw: ImageDraw.ImageDraw) -> None:
    draw_person(draw, 350, 250, 0.95, shirt=(91, 146, 223))
    draw_person(draw, 650, 330, 0.82, shirt=(228, 102, 101))
    draw.line((430, 520, 560, 470), fill=(242, 191, 136), width=18)
    draw.line((560, 470, 610, 550), fill=(242, 191, 136), width=18)
    draw_sparkle(draw, 520, 420, 32, color=(255, 214, 95))


def draw_storia(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((220, 320, 804, 720), radius=28, fill=(91, 146, 223))
    draw.rectangle((512, 320, 532, 720), fill=(255, 255, 255, 160))
    draw.ellipse((340, 410, 412, 482), fill=(255, 214, 95))
    draw_sparkle(draw, 370, 540, 24)
    draw_sparkle(draw, 680, 430, 34)
    draw_cloud(draw, 590, 520, 0.8, fill=(255, 255, 255, 220))


def draw_laggiu(draw: ImageDraw.ImageDraw) -> None:
    draw_sun(draw, 770, 260, 52)
    draw.rectangle((190, 520, 834, 690), fill=(95, 191, 231))
    draw.rectangle((140, 690, 900, 790), fill=(237, 210, 145))
    draw.line((220, 560, 806, 560), fill=(255, 255, 255, 120), width=8)
    draw_arrow(draw, (300, 370), (700, 500), (84, 177, 132), width=20)
    draw.ellipse((690, 470, 730, 510), fill=(231, 98, 82))


def draw_li(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((300, 220, 620, 760), radius=30, fill=(226, 214, 194))
    draw.rounded_rectangle((350, 280, 570, 760), radius=20, fill=(150, 103, 74))
    draw.ellipse((515, 500, 545, 530), fill=(235, 204, 104))
    draw.ellipse((690, 500, 770, 580), fill=(231, 98, 82))
    draw_arrow(draw, (610, 540), (680, 540), (84, 177, 132), width=16, head=34)


def draw_qua(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((220, 530, 300, 610), fill=(231, 98, 82))
    draw_arrow(draw, (760, 350), (320, 570), (84, 177, 132), width=22, head=44)
    draw_shadow_circle(draw, (590, 240, 810, 460), fill=(252, 250, 244))
    draw.ellipse((660, 310, 740, 390), fill=(242, 191, 136))


def draw_sotto(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((220, 360, 804, 420), fill=(150, 103, 74))
    for x in (280, 720):
        draw.rectangle((x, 420, x + 28, 760), fill=(121, 84, 61))
    draw_shadow_circle(draw, (430, 520, 590, 680), fill=(91, 146, 223))


def draw_dritto(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(360, 780), (460, 260), (564, 260), (664, 780)], fill=(83, 92, 112))
    draw.line((512, 720, 512, 360), fill=(255, 214, 95), width=16)
    draw_arrow(draw, (512, 600), (512, 300), (84, 177, 132), width=22, head=50)


def draw_destro(draw: ImageDraw.ImageDraw) -> None:
    draw_arrow(draw, (280, 520), (730, 520), (84, 177, 132), width=24, head=48)
    draw_arrow(draw, (730, 520), (730, 310), (84, 177, 132), width=24, head=48)
    draw.line((250, 720, 774, 720), fill=(83, 92, 112), width=20)


def draw_sinistro(draw: ImageDraw.ImageDraw) -> None:
    draw_arrow(draw, (744, 520), (294, 520), (84, 177, 132), width=24, head=48)
    draw_arrow(draw, (294, 520), (294, 310), (84, 177, 132), width=24, head=48)
    draw.line((250, 720, 774, 720), fill=(83, 92, 112), width=20)


def draw_domani(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((240, 240, 784, 760), radius=40, fill=(252, 250, 244))
    draw.rounded_rectangle((240, 240, 784, 380), radius=40, fill=(228, 102, 101))
    for x in (340, 520, 700):
        draw.rectangle((x, 200, x + 34, 290), fill=(83, 92, 112))
    draw_sun(draw, 682, 560, 72)
    draw_arrow(draw, (320, 540), (520, 540), (84, 177, 132), width=18, head=40)


def draw_domattina(draw: ImageDraw.ImageDraw) -> None:
    draw_sun(draw, 720, 280, 72)
    draw_clock(draw, 420, 560, 170, hour_angle=-70, minute_angle=120)
    draw.line((210, 720, 860, 720), fill=(83, 92, 112), width=18)


def draw_tuttiigiorni(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((240, 260, 784, 720), radius=40, fill=(252, 250, 244))
    for row in range(2):
        for col in range(3):
            x = 310 + col * 128
            y = 360 + row * 120
            draw.rounded_rectangle((x, y, x + 72, y + 52), radius=10, fill=(129, 176, 226))
    draw.arc((250, 220, 520, 490), 210, 350, fill=(84, 177, 132), width=18)
    draw.arc((500, 470, 770, 740), 30, 180, fill=(84, 177, 132), width=18)
    draw.polygon([(500, 242), (550, 304), (470, 318)], fill=(84, 177, 132))
    draw.polygon([(520, 718), (470, 656), (550, 642)], fill=(84, 177, 132))


def draw_pocofa(draw: ImageDraw.ImageDraw) -> None:
    draw_clock(draw, 520, 500, 220, hour_angle=-40, minute_angle=120)
    draw_arc = (220, 200, 820, 800)
    draw.arc(draw_arc, 210, 300, fill=(84, 177, 132), width=22)
    draw.polygon([(246, 434), (305, 495), (220, 518)], fill=(84, 177, 132))


def draw_alzarsi(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((180, 620, 820, 760), fill=(150, 107, 84))
    draw.rectangle((250, 470, 740, 620), fill=(129, 176, 226))
    draw.rounded_rectangle((250, 430, 420, 530), radius=22, fill=(248, 248, 250))
    draw.ellipse((450, 360, 530, 440), fill=(242, 191, 136))
    draw.line((490, 440, 560, 340), fill=(84, 177, 132), width=20)
    draw_arrow(draw, (610, 530), (720, 320), (84, 177, 132), width=18, head=38)


def draw_lavarsi(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((300, 320, 724, 400), fill=(83, 92, 112))
    draw.rectangle((560, 300, 620, 520), fill=(83, 92, 112))
    draw.arc((520, 360, 700, 540), 180, 300, fill=(83, 92, 112), width=20)
    for x in (560, 600, 640):
        draw.line((x, 500, x, 660), fill=(129, 176, 226), width=12)
    draw.ellipse((390, 560, 490, 660), fill=(242, 191, 136))
    draw.ellipse((530, 560, 630, 660), fill=(242, 191, 136))


def draw_buonanotte(draw: ImageDraw.ImageDraw) -> None:
    draw.pieslice((520, 150, 780, 410), 50, 310, fill=(255, 239, 178))
    draw.pieslice((585, 135, 820, 370), 50, 310, fill=(142, 172, 214))
    draw.rectangle((160, 640, 864, 760), fill=(150, 107, 84))
    draw.rectangle((240, 470, 760, 640), fill=(129, 176, 226))
    draw.rounded_rectangle((255, 435, 430, 540), radius=24, fill=(248, 248, 250))
    for cx, cy in ((240, 210), (360, 280), (760, 360)):
        draw_sparkle(draw, cx, cy, 18, color=(255, 214, 95))


def draw_interessante(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((210, 320, 814, 690), radius=34, fill=(83, 104, 145))
    draw.rectangle((280, 380, 744, 610), fill=(165, 218, 237))
    draw.rectangle((470, 690, 554, 750), fill=(95, 103, 116))
    draw.rectangle((390, 750, 634, 780), fill=(95, 103, 116))
    draw_sparkle(draw, 512, 260, 64, color=(255, 224, 128))
    draw.arc((320, 240, 470, 390), 290, 80, fill=(84, 177, 132), width=16)
    draw.arc((554, 240, 704, 390), 100, 250, fill=(84, 177, 132), width=16)


def draw_bello(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(390, 260), (634, 260), (704, 700), (320, 700)], fill=(228, 102, 101))
    draw.polygon([(452, 260), (512, 360), (572, 260)], fill=(255, 214, 95))
    draw.line((452, 260, 410, 340), fill=(228, 102, 101), width=18)
    draw.line((572, 260, 614, 340), fill=(228, 102, 101), width=18)
    for cx, cy in ((290, 240), (730, 300), (690, 640)):
        draw_sparkle(draw, cx, cy, 28, color=(255, 224, 128))


def draw_gentile(draw: ImageDraw.ImageDraw) -> None:
    draw_person(draw, 350, 240, 0.92, shirt=(91, 146, 223))
    draw_person(draw, 650, 320, 0.82, shirt=(228, 102, 101))
    draw.line((430, 520, 560, 500), fill=(242, 191, 136), width=16)
    draw.line((560, 500, 620, 560), fill=(242, 191, 136), width=16)
    draw_sparkle(draw, 520, 430, 28, color=(255, 214, 95))


def draw_giovane(draw: ImageDraw.ImageDraw) -> None:
    draw_person(draw, 512, 220, 1.05, shirt=(84, 177, 132), pants=(83, 92, 112))
    draw.line((430, 660, 360, 760), fill=(84, 177, 132), width=18)
    draw.line((594, 660, 664, 760), fill=(84, 177, 132), width=18)
    draw_sparkle(draw, 740, 250, 26, color=(255, 214, 95))


def draw_ottimista(draw: ImageDraw.ImageDraw) -> None:
    draw_sun(draw, 512, 330, 96, color=(255, 214, 95))
    draw.arc((220, 520, 804, 900), 200, 340, fill=(84, 177, 132), width=24)
    draw_shadow_circle(draw, (350, 470, 674, 794), fill=(252, 250, 244))
    draw.ellipse((438, 580, 474, 616), fill=(68, 78, 94))
    draw.ellipse((550, 580, 586, 616), fill=(68, 78, 94))
    draw.arc((430, 630, 594, 710), 20, 160, fill=(68, 78, 94), width=12)


def draw_dolce(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(390, 700), (634, 700), (592, 830), (432, 830)], fill=(215, 164, 98))
    draw_shadow_circle(draw, (360, 420, 664, 724), fill=(246, 192, 211))
    draw_shadow_circle(draw, (420, 320, 724, 624), fill=(248, 240, 214))
    draw_shadow_circle(draw, (300, 320, 604, 624), fill=(255, 214, 95))
    draw_sparkle(draw, 760, 260, 24, color=(255, 224, 128))


def draw_telefonico(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((300, 250, 724, 774), radius=54, fill=(43, 55, 78))
    draw.rounded_rectangle((334, 315, 690, 674), radius=28, fill=(176, 224, 240))
    draw.ellipse((492, 715, 532, 755), fill=(220, 220, 228))
    draw.arc((250, 390, 420, 560), 270, 90, fill=(84, 177, 132), width=18)
    draw.arc((604, 390, 774, 560), 90, 270, fill=(84, 177, 132), width=18)
    draw.line((430, 530, 470, 470), fill=(255, 255, 255), width=18)
    draw.line((550, 470, 590, 530), fill=(255, 255, 255), width=18)
    draw.line((470, 470, 550, 470), fill=(255, 255, 255), width=18)


def draw_occupato(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((260, 230, 764, 810), radius=36, fill=(226, 214, 194))
    draw.rounded_rectangle((360, 290, 664, 760), radius=26, fill=(150, 103, 74))
    draw.ellipse((594, 500, 628, 534), fill=(235, 204, 104))
    draw.rounded_rectangle((430, 380, 594, 470), radius=22, fill=(228, 102, 101))
    draw.line((455, 425, 569, 425), fill=(255, 255, 255), width=12)


def draw_pronto(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((320, 190, 704, 834), radius=52, fill=(43, 55, 78))
    draw.rounded_rectangle((354, 255, 670, 734), radius=28, fill=(176, 224, 240))
    draw.ellipse((490, 770, 534, 814), fill=(220, 220, 228))
    for box in ((230, 320, 330, 430), (694, 320, 794, 430), (205, 480, 315, 600), (709, 480, 819, 600)):
        draw.arc(box, 270, 90, fill=(84, 177, 132), width=12)
    draw.arc((418, 390, 602, 590), 200, 340, fill=(255, 255, 255), width=26)
    draw.rectangle((470, 520, 550, 610), fill=(255, 255, 255))


def draw_vero(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (250, 220, 774, 744), fill=(252, 250, 244))
    draw_sparkle(draw, 512, 470, 170, color=(255, 214, 95))
    draw.line((400, 500, 490, 590), fill=(84, 177, 132), width=26)
    draw.line((490, 590, 640, 390), fill=(84, 177, 132), width=26)


def draw_solo(draw: ImageDraw.ImageDraw) -> None:
    draw_person(draw, 512, 230, 1.0, shirt=(91, 146, 223), pants=(83, 92, 112))
    draw.rectangle((180, 760, 844, 792), fill=(111, 122, 138))
    draw_shadow_circle(draw, (160, 230, 864, 810), fill=(255, 255, 255, 0))
    draw.arc((190, 310, 834, 890), 210, 330, fill=(83, 92, 112), width=18)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = [
        ("buonanotte", (147, 176, 219), (84, 109, 154), draw_buonanotte),
        ("fragile", (218, 236, 247), (147, 192, 221), draw_fragile),
        ("gustoso", (245, 204, 141), (222, 139, 92), draw_gustoso),
        ("interessante", (194, 211, 242), (121, 156, 206), draw_interessante),
        ("bello", (247, 199, 194), (223, 143, 157), draw_bello),
        ("gentile", (205, 224, 199), (139, 181, 146), draw_gentile),
        ("giovane", (188, 226, 193), (119, 173, 133), draw_giovane),
        ("ottimista", (247, 221, 162), (208, 173, 107), draw_ottimista),
        ("dolce", (248, 219, 181), (232, 172, 145), draw_dolce),
        ("telefonico", (182, 216, 244), (113, 154, 206), draw_telefonico),
        ("occupato", (224, 208, 187), (180, 152, 120), draw_occupato),
        ("pronto", (182, 216, 244), (113, 154, 206), draw_pronto),
        ("vero", (248, 226, 170), (225, 183, 102), draw_vero),
        ("solo", (214, 220, 231), (151, 160, 180), draw_solo),
        ("libero", (183, 223, 190), (120, 184, 145), draw_libero),
        ("stanco", (250, 221, 136), (224, 173, 94), draw_stanco),
        ("malato", (178, 214, 230), (120, 165, 188), draw_malato),
        ("chiuso", (224, 208, 187), (180, 152, 120), draw_chiuso),
        ("freddo", (188, 220, 248), (117, 162, 220), draw_freddo),
        ("pulito", (244, 246, 250), (203, 215, 234), draw_pulito),
        ("sporco", (199, 187, 171), (154, 136, 116), draw_sporco),
        ("turista", (212, 226, 194), (151, 188, 139), draw_turista),
        ("aiuto", (174, 206, 238), (111, 148, 196), draw_aiuto),
        ("storia", (173, 195, 235), (108, 139, 198), draw_storia),
        ("laggiu", (146, 204, 238), (95, 174, 217), draw_laggiu),
        ("li", (227, 212, 191), (189, 160, 127), draw_li),
        ("qua", (203, 224, 190), (143, 185, 132), draw_qua),
        ("sotto", (210, 198, 179), (172, 145, 116), draw_sotto),
        ("dritto", (194, 210, 235), (127, 157, 201), draw_dritto),
        ("destro", (194, 210, 235), (127, 157, 201), draw_destro),
        ("sinistro", (194, 210, 235), (127, 157, 201), draw_sinistro),
        ("domani", (245, 214, 150), (223, 162, 95), draw_domani),
        ("domattina", (247, 221, 162), (208, 173, 107), draw_domattina),
        ("tuttiigiorni", (209, 225, 248), (143, 173, 218), draw_tuttiigiorni),
        ("pocofa", (210, 225, 246), (145, 176, 215), draw_pocofa),
        ("alzarsi", (219, 206, 182), (179, 154, 122), draw_alzarsi),
        ("lavarsi", (182, 216, 244), (113, 154, 206), draw_lavarsi),
    ]
    for name, top, bottom, renderer in images:
        save_image(name, top, bottom, renderer)
        print(f"OK  {OUT_DIR / f'{name}.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
