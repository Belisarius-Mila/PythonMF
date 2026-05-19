#!/usr/bin/env python3
from __future__ import annotations

import math

from PIL import ImageDraw

from generate_it_group_a_images import OUT_DIR, draw_cloud, draw_shadow_circle, draw_sun, save_image


def draw_snowflake(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    for angle in range(0, 180, 30):
        a = math.radians(angle)
        dx = math.cos(a) * r
        dy = math.sin(a) * r
        draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(255, 255, 255), width=6)


def draw_inverno(draw: ImageDraw.ImageDraw) -> None:
    draw_cloud(draw, 250, 210, 1.3, fill=(244, 248, 255, 245))
    draw.rectangle((200, 710, 840, 790), fill=(233, 241, 252))
    draw_shadow_circle(draw, (360, 430, 660, 730), fill=(248, 251, 255))
    draw_shadow_circle(draw, (410, 310, 610, 510), fill=(248, 251, 255))
    draw_shadow_circle(draw, (445, 220, 575, 350), fill=(248, 251, 255))
    for x, y in ((460, 270), (510, 260), (545, 278)):
        draw.ellipse((x, y, x + 10, y + 10), fill=(68, 78, 94))
    draw.polygon([(510, 286), (565, 302), (510, 318)], fill=(231, 145, 82))
    for x in (450, 490, 530):
        draw.ellipse((x, 390, x + 18, 408), fill=(68, 78, 94))
    draw.line((510, 450, 350, 420), fill=(117, 92, 72), width=12)
    draw.line((510, 450, 680, 455), fill=(117, 92, 72), width=12)
    for cx, cy, r in ((270, 360, 36), (760, 310, 32), (760, 470, 28)):
        draw_snowflake(draw, cx, cy, r)


def draw_anno(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((230, 230, 794, 760), radius=40, fill=(248, 249, 252))
    draw.rounded_rectangle((230, 230, 794, 360), radius=40, fill=(216, 92, 88))
    draw.rectangle((230, 320, 794, 360), fill=(216, 92, 88))
    for x in (320, 500, 680):
        draw.rectangle((x, 200, x + 36, 290), fill=(81, 88, 104))
    for row in range(3):
        for col in range(4):
            x1 = 286 + col * 118
            y1 = 410 + row * 98
            draw.rounded_rectangle((x1, y1, x1 + 70, y1 + 50), radius=10, fill=(141, 183, 236))
    draw_sun(draw, 760, 250, 34, color=(255, 207, 93))
    draw.polygon([(256, 260), (280, 300), (305, 260), (345, 244), (305, 228), (280, 188), (256, 228), (216, 244)], fill=(255, 255, 255))


def draw_straniero(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (205, 250, 525, 570), fill=(86, 147, 223))
    draw.arc((235, 280, 495, 540), 0, 360, fill=(220, 240, 255), width=8)
    draw.arc((260, 280, 470, 540), 0, 360, fill=(220, 240, 255), width=8)
    draw.arc((235, 330, 495, 490), 0, 360, fill=(220, 240, 255), width=8)
    draw.line((365, 280, 365, 540), fill=(220, 240, 255), width=8)
    draw.line((235, 410, 495, 410), fill=(220, 240, 255), width=8)
    draw.ellipse((570, 250, 760, 440), fill=(242, 191, 136))
    draw.rectangle((625, 420, 705, 520), fill=(242, 191, 136))
    draw.rounded_rectangle((560, 500, 820, 760), radius=30, fill=(85, 129, 205))
    draw.rounded_rectangle((300, 620, 520, 770), radius=24, fill=(38, 76, 137))
    draw.rectangle((340, 660, 480, 735), fill=(225, 239, 255))
    draw.polygon([(670, 575), (700, 620), (750, 628), (714, 668), (724, 720), (670, 695), (616, 720), (626, 668), (590, 628), (640, 620)], fill=(255, 213, 96))


def draw_aspettare(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((180, 720, 844, 792), fill=(116, 124, 136))
    draw.rectangle((250, 540, 760, 575), fill=(141, 98, 71))
    for x in (310, 700):
        draw.rectangle((x, 575, x + 28, 735), fill=(109, 80, 59))
    draw_shadow_circle(draw, (630, 190, 850, 410), fill=(242, 246, 250))
    draw.ellipse((680, 240, 800, 360), fill=(255, 255, 255))
    draw.line((740, 300, 740, 255), fill=(90, 102, 120), width=8)
    draw.line((740, 300, 780, 320), fill=(90, 102, 120), width=8)
    draw.ellipse((280, 370, 430, 520), fill=(242, 191, 136))
    draw.rectangle((335, 500, 385, 590), fill=(242, 191, 136))
    draw.rounded_rectangle((260, 560, 465, 720), radius=24, fill=(88, 129, 205))
    draw.line((350, 590, 350, 720), fill=(75, 96, 129), width=16)


def draw_cercare(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (230, 240, 690, 700), fill=(253, 252, 248))
    draw.ellipse((320, 330, 600, 610), outline=(84, 139, 214), width=28)
    draw.line((560, 570, 770, 780), fill=(84, 139, 214), width=36)
    for x, y, r in ((330, 260, 16), (660, 310, 14), (730, 200, 12)):
        draw.ellipse((x, y, x + 2 * r, y + 2 * r), fill=(255, 211, 87))


def draw_vendere(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((260, 330, 780, 740), radius=34, fill=(248, 232, 210))
    for i, color in enumerate([(223, 83, 60), (255, 246, 238)] * 4):
        draw.rectangle((260 + i * 65, 250, 325 + i * 65, 350), fill=color)
    draw.rectangle((260, 350, 780, 382), fill=(167, 98, 66))
    draw.rounded_rectangle((340, 430, 520, 740), radius=22, fill=(160, 109, 78))
    draw.rounded_rectangle((560, 430, 730, 610), radius=22, fill=(173, 219, 237))
    draw.rounded_rectangle((625, 470, 770, 560), radius=22, fill=(255, 213, 96))
    draw.text((665, 490), "$", fill=(103, 77, 46))
    draw.ellipse((605, 650, 705, 750), fill=(255, 213, 96))
    draw.ellipse((670, 625, 770, 725), fill=(242, 191, 136))


def draw_vincere(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(512, 160), (550, 250), (650, 260), (575, 325), (600, 425), (512, 370), (424, 425), (449, 325), (374, 260), (474, 250)], fill=(255, 214, 95))
    draw.rounded_rectangle((360, 330, 664, 520), radius=40, fill=(255, 214, 95))
    draw.rectangle((470, 520, 554, 650), fill=(185, 134, 67))
    draw.rounded_rectangle((380, 650, 644, 710), radius=18, fill=(121, 84, 61))
    draw.arc((270, 300, 405, 510), 260, 100, fill=(220, 163, 75), width=18)
    draw.arc((620, 300, 755, 510), 80, 280, fill=(220, 163, 75), width=18)
    for cx, cy, color in ((240, 220, (84, 177, 132)), (770, 270, (91, 146, 223)), (690, 170, (231, 92, 92))):
        draw.ellipse((cx, cy, cx + 26, cy + 26), fill=color)


def draw_chiamare(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((320, 190, 704, 834), radius=52, fill=(43, 55, 78))
    draw.rounded_rectangle((354, 255, 670, 734), radius=28, fill=(176, 224, 240))
    draw.ellipse((490, 770, 534, 814), fill=(220, 220, 228))
    for box in ((230, 320, 330, 430), (694, 320, 794, 430), (205, 480, 315, 600), (709, 480, 819, 600)):
        draw.arc(box, 270, 90, fill=(85, 129, 205), width=12)
    draw.arc((418, 390, 602, 590), 200, 340, fill=(255, 255, 255), width=26)
    draw.rectangle((470, 520, 550, 610), fill=(255, 255, 255))


def draw_aprire(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((240, 220, 760, 800), radius=36, fill=(226, 214, 194))
    draw.rounded_rectangle((340, 280, 690, 760), radius=22, fill=(150, 103, 74))
    draw.polygon([(690, 280), (860, 360), (860, 800), (690, 760)], fill=(184, 144, 107))
    draw.ellipse((610, 490, 640, 520), fill=(235, 204, 104))
    draw.polygon([(760, 510), (900, 510), (900, 460), (980, 530), (900, 600), (900, 550), (760, 550)], fill=(91, 182, 114))


def draw_dormire(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((170, 640, 854, 760), fill=(150, 107, 84))
    draw.rectangle((240, 470, 760, 640), fill=(129, 176, 226))
    draw.rounded_rectangle((255, 435, 430, 540), radius=24, fill=(248, 248, 250))
    draw.ellipse((310, 475, 380, 520), fill=(242, 191, 136))
    draw.rectangle((300, 515, 520, 630), fill=(242, 153, 130))
    draw.polygon([(720, 235), (756, 310), (838, 320), (777, 375), (793, 454), (720, 410), (647, 454), (663, 375), (602, 320), (684, 310)], fill=(255, 226, 126))
    for pos in ((610, 200), (650, 145), (690, 110)):
        draw.text(pos, "Z", fill=(109, 124, 163))


def draw_nuotare(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((140, 520, 884, 760), fill=(95, 191, 231))
    for y in (560, 620, 680):
        draw.arc((140, y - 30, 320, y + 30), 0, 180, fill=(255, 255, 255, 180), width=8)
        draw.arc((300, y - 30, 480, y + 30), 0, 180, fill=(255, 255, 255, 180), width=8)
        draw.arc((460, y - 30, 640, y + 30), 0, 180, fill=(255, 255, 255, 180), width=8)
        draw.arc((620, y - 30, 800, y + 30), 0, 180, fill=(255, 255, 255, 180), width=8)
    draw.ellipse((330, 360, 430, 460), fill=(242, 191, 136))
    draw.arc((360, 430, 630, 610), 190, 330, fill=(231, 98, 82), width=36)
    draw.line((585, 430, 700, 355), fill=(242, 191, 136), width=26)


def draw_pattinare(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((150, 620, 874, 780), fill=(219, 240, 252))
    for x in range(190, 820, 110):
        draw.line((x, 620, x + 80, 780), fill=(255, 255, 255, 120), width=8)
    draw.polygon([(280, 340), (560, 340), (640, 480), (620, 620), (350, 620), (260, 500)], fill=(91, 146, 223))
    draw.polygon([(260, 500), (350, 620), (250, 660), (210, 540)], fill=(91, 146, 223))
    draw.rectangle((350, 620, 620, 650), fill=(59, 67, 84))
    draw.arc((290, 620, 680, 760), 180, 360, fill=(220, 220, 228), width=12)
    for x in (350, 430, 510):
        draw.line((x, 390, x + 50, 570), fill=(255, 255, 255), width=8)


def draw_sciare(draw: ImageDraw.ImageDraw) -> None:
    draw.polygon([(130, 720), (360, 380), (560, 720)], fill=(233, 241, 252))
    draw.polygon([(420, 720), (650, 300), (900, 720)], fill=(219, 231, 247))
    draw.ellipse((420, 270, 500, 350), fill=(242, 191, 136))
    draw.line((460, 350, 560, 500), fill=(231, 92, 92), width=28)
    draw.line((560, 500, 630, 650), fill=(231, 92, 92), width=24)
    draw.line((560, 500, 470, 650), fill=(65, 83, 114), width=24)
    draw.line((510, 380, 650, 310), fill=(117, 92, 72), width=14)
    draw.line((560, 420, 675, 520), fill=(117, 92, 72), width=14)
    draw.line((395, 650, 690, 650), fill=(84, 139, 214), width=12)
    draw.line((370, 690, 665, 690), fill=(255, 191, 60), width=12)


def draw_ballare(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((280, 220, 420, 360), fill=(242, 191, 136))
    draw.ellipse((610, 220, 750, 360), fill=(242, 191, 136))
    draw.arc((240, 340, 520, 680), 210, 330, fill=(226, 82, 107), width=34)
    draw.arc((500, 340, 780, 680), 210, 330, fill=(81, 129, 211), width=34)
    draw.line((400, 400, 540, 380), fill=(242, 191, 136), width=18)
    draw.line((540, 380, 620, 420), fill=(242, 191, 136), width=18)
    draw.line((360, 470, 290, 620), fill=(91, 82, 100), width=18)
    draw.line((420, 470, 500, 650), fill=(91, 82, 100), width=18)
    draw.line((630, 470, 560, 650), fill=(91, 82, 100), width=18)
    draw.line((690, 470, 760, 600), fill=(91, 82, 100), width=18)
    for x in (220, 810):
        draw_sun(draw, x, 240, 18, color=(255, 213, 96))


def draw_tornare(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((180, 730, 860, 790), fill=(111, 122, 138))
    draw.rectangle((560, 430, 780, 760), fill=(241, 224, 198))
    draw.polygon([(670, 290), (500, 430), (840, 430)], fill=(206, 92, 88))
    draw.rectangle((620, 570, 700, 760), fill=(135, 98, 72))
    draw.rounded_rectangle((320, 380, 460, 720), radius=28, fill=(91, 146, 223))
    draw.ellipse((350, 250, 430, 330), fill=(242, 191, 136))
    draw.arc((170, 220, 620, 700), 40, 270, fill=(84, 177, 132), width=26)
    draw.polygon([(214, 352), (168, 430), (262, 430)], fill=(84, 177, 132))


def draw_prendere(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((210, 300, 814, 700), radius=40, fill=(98, 152, 221))
    draw.rounded_rectangle((280, 360, 744, 560), radius=28, fill=(219, 240, 252))
    for x in (360, 510, 660):
        draw.line((x, 360, x, 560), fill=(162, 202, 229), width=10)
    draw.ellipse((310, 590, 420, 700), fill=(44, 53, 69))
    draw.ellipse((604, 590, 714, 700), fill=(44, 53, 69))
    draw.rectangle((470, 190, 560, 360), fill=(242, 191, 136))
    draw.rounded_rectangle((430, 260, 590, 360), radius=20, fill=(255, 216, 112))
    draw.line((480, 170, 640, 100), fill=(242, 191, 136), width=20)
    draw.arc((600, 160, 820, 380), 180, 330, fill=(255, 255, 255), width=16)


def draw_rispondere(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((180, 250, 510, 520), radius=40, fill=(252, 251, 246))
    draw.polygon([(280, 520), (340, 610), (360, 520)], fill=(252, 251, 246))
    draw.rounded_rectangle((520, 390, 840, 650), radius=40, fill=(108, 174, 132))
    draw.polygon([(680, 650), (720, 740), (760, 650)], fill=(108, 174, 132))
    draw.text((305, 320), "?", fill=(86, 96, 112))
    draw.text((635, 455), "!", fill=(255, 255, 255))
    draw.arc((250, 420, 760, 840), 220, 320, fill=(84, 139, 214), width=18)
    draw.polygon([(715, 598), (792, 610), (740, 670)], fill=(84, 139, 214))


def draw_trovare(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (280, 220, 700, 640), fill=(251, 248, 238))
    draw.ellipse((360, 300, 580, 520), outline=(91, 146, 223), width=24)
    draw.line((540, 470, 740, 670), fill=(91, 146, 223), width=28)
    draw.ellipse((380, 600, 470, 690), fill=(255, 213, 96))
    draw.rectangle((450, 632, 640, 660), fill=(255, 213, 96))
    draw.ellipse((618, 620, 676, 678), outline=(255, 213, 96), width=14)
    draw.ellipse((460, 430, 500, 470), fill=(255, 213, 96))


def draw_conoscere(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((220, 250, 380, 410), fill=(242, 191, 136))
    draw.rounded_rectangle((180, 390, 430, 760), radius=32, fill=(89, 144, 221))
    draw.ellipse((644, 250, 804, 410), fill=(242, 191, 136))
    draw.rounded_rectangle((594, 390, 844, 760), radius=32, fill=(228, 102, 101))
    draw.line((410, 520, 590, 520), fill=(242, 191, 136), width=26)
    draw.ellipse((468, 480, 536, 548), fill=(255, 224, 128))
    draw.rectangle((490, 460, 514, 568), fill=(255, 224, 128))


def draw_finire(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((210, 280, 814, 720), radius=38, fill=(252, 250, 244))
    draw.line((512, 300, 512, 700), fill=(212, 198, 176), width=8)
    draw.arc((280, 340, 490, 610), 20, 330, fill=(91, 146, 223), width=16)
    draw.arc((534, 340, 744, 610), 210, 520, fill=(231, 98, 82), width=16)
    draw_shadow_circle(draw, (650, 160, 860, 370), fill=(242, 246, 250))
    draw.line((755, 265, 755, 210), fill=(86, 96, 112), width=8)
    draw.line((755, 265, 808, 265), fill=(86, 96, 112), width=8)
    draw.polygon([(250, 215), (330, 250), (250, 285)], fill=(84, 177, 132))
    draw.rectangle((230, 215, 250, 375), fill=(84, 177, 132))


def draw_restare(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((180, 730, 860, 792), fill=(111, 122, 138))
    draw.rounded_rectangle((390, 320, 540, 720), radius=30, fill=(91, 146, 223))
    draw.ellipse((420, 220, 510, 310), fill=(242, 191, 136))
    draw_shadow_circle(draw, (610, 210, 850, 450), fill=(242, 246, 250))
    draw.ellipse((680, 280, 780, 380), fill=(255, 255, 255))
    draw.line((730, 330, 730, 280), fill=(86, 96, 112), width=8)
    draw.line((730, 330, 770, 360), fill=(86, 96, 112), width=8)
    draw.arc((240, 410, 380, 560), 200, 520, fill=(84, 177, 132), width=18)
    draw.arc((550, 410, 690, 560), 20, 340, fill=(84, 177, 132), width=18)


def draw_ricordare(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse((220, 250, 470, 500), fill=(242, 191, 136))
    draw.rounded_rectangle((190, 480, 500, 770), radius=34, fill=(91, 146, 223))
    draw.ellipse((310, 320, 360, 370), fill=(255, 255, 255, 120))
    draw.polygon([(470, 230), (520, 330), (630, 340), (550, 410), (575, 520), (470, 455), (365, 520), (390, 410), (310, 340), (420, 330)], fill=(255, 224, 128))
    draw.rounded_rectangle((590, 310, 820, 620), radius=26, fill=(252, 250, 244))
    for y in (380, 450, 520):
        draw.rectangle((635, y, 775, y + 18), fill=(160, 190, 224))
    draw.line((580, 330, 660, 300), fill=(84, 177, 132), width=14)


def draw_essere(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (240, 210, 784, 754), fill=(252, 250, 244))
    draw_shadow_circle(draw, (320, 260, 704, 644), fill=(255, 255, 255))
    draw.line((512, 452, 512, 330), fill=(91, 146, 223), width=14)
    draw.line((512, 452, 605, 500), fill=(91, 146, 223), width=14)
    draw.arc((240, 210, 784, 754), 210, 330, fill=(84, 177, 132), width=26)
    draw.line((395, 515, 470, 590), fill=(84, 177, 132), width=18)
    draw.line((470, 590, 640, 430), fill=(84, 177, 132), width=18)
    draw.polygon([(690, 240), (760, 270), (690, 300)], fill=(255, 214, 95))


def draw_odiare(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (250, 220, 774, 744), fill=(252, 250, 244))
    draw_shadow_circle(draw, (560, 250, 810, 500), fill=(242, 246, 250))
    draw.ellipse((635, 325, 735, 425), fill=(255, 255, 255))
    draw.line((685, 375, 685, 320), fill=(86, 96, 112), width=8)
    draw.line((685, 375, 725, 405), fill=(86, 96, 112), width=8)
    draw.ellipse((320, 320, 620, 620), fill=(231, 98, 82))
    draw.line((390, 395, 455, 365), fill=(68, 42, 46), width=12)
    draw.line((485, 365, 550, 395), fill=(68, 42, 46), width=12)
    draw.ellipse((410, 430, 445, 465), fill=(68, 42, 46))
    draw.ellipse((495, 430, 530, 465), fill=(68, 42, 46))
    draw.arc((405, 490, 545, 565), 20, 160, fill=(68, 42, 46), width=12)
    draw.line((610, 300, 760, 220), fill=(68, 42, 46), width=18)


def draw_dovere(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((170, 730, 860, 792), fill=(111, 122, 138))
    draw.rounded_rectangle((230, 320, 470, 700), radius=30, fill=(85, 129, 205))
    draw.rectangle((300, 260, 400, 320), fill=(59, 67, 84))
    draw.ellipse((520, 320, 760, 560), fill=(255, 214, 95))
    draw.text((610, 390), "!", fill=(121, 84, 61))
    draw.polygon([(620, 590), (740, 590), (740, 545), (830, 630), (740, 715), (740, 670), (620, 670)], fill=(84, 177, 132))
    draw.line((350, 430, 640, 430), fill=(242, 191, 136), width=18)
    draw.line((350, 520, 640, 520), fill=(242, 191, 136), width=18)


def draw_interessare(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((210, 320, 814, 690), radius=34, fill=(83, 104, 145))
    draw.rectangle((280, 380, 744, 610), fill=(165, 218, 237))
    draw.rectangle((470, 690, 554, 750), fill=(95, 103, 116))
    draw.rectangle((390, 750, 634, 780), fill=(95, 103, 116))
    draw.polygon([(512, 220), (550, 310), (650, 320), (575, 385), (600, 485), (512, 430), (424, 485), (449, 385), (374, 320), (474, 310)], fill=(255, 224, 128))
    draw.arc((300, 250, 460, 410), 290, 90, fill=(84, 177, 132), width=16)
    draw.arc((560, 250, 720, 410), 90, 250, fill=(84, 177, 132), width=16)


def draw_servire(draw: ImageDraw.ImageDraw) -> None:
    draw_shadow_circle(draw, (220, 230, 804, 744), fill=(252, 250, 244))
    draw.rounded_rectangle((280, 420, 560, 650), radius=28, fill=(91, 146, 223))
    draw.rectangle((390, 300, 450, 420), fill=(59, 67, 84))
    draw.rounded_rectangle((620, 330, 760, 470), radius=26, fill=(255, 214, 95))
    draw.ellipse((650, 360, 690, 400), fill=(121, 84, 61))
    draw.ellipse((705, 360, 745, 400), fill=(121, 84, 61))
    draw.arc((645, 390, 745, 445), 20, 160, fill=(121, 84, 61), width=8)
    draw.line((545, 535, 630, 420), fill=(84, 177, 132), width=18)
    draw.polygon([(600, 365), (690, 250), (780, 365)], fill=(84, 177, 132))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    images = [
        ("ballare", (250, 196, 194), (220, 139, 164), draw_ballare),
        ("inverno", (188, 220, 248), (119, 162, 220), draw_inverno),
        ("anno", (244, 197, 146), (219, 113, 96), draw_anno),
        ("straniero", (164, 205, 247), (94, 131, 199), draw_straniero),
        ("aspettare", (174, 199, 232), (118, 140, 178), draw_aspettare),
        ("tornare", (169, 213, 178), (111, 167, 128), draw_tornare),
        ("prendere", (165, 198, 240), (94, 135, 200), draw_prendere),
        ("rispondere", (182, 213, 240), (110, 162, 194), draw_rispondere),
        ("trovare", (248, 225, 163), (225, 177, 95), draw_trovare),
        ("cercare", (250, 230, 166), (231, 180, 99), draw_cercare),
        ("vendere", (246, 197, 134), (225, 129, 90), draw_vendere),
        ("vincere", (249, 215, 132), (225, 146, 87), draw_vincere),
        ("chiamare", (151, 194, 231), (87, 128, 180), draw_chiamare),
        ("conoscere", (232, 199, 147), (205, 131, 114), draw_conoscere),
        ("aprire", (218, 196, 173), (179, 144, 112), draw_aprire),
        ("dormire", (136, 153, 196), (94, 104, 146), draw_dormire),
        ("finire", (223, 202, 168), (181, 151, 109), draw_finire),
        ("restare", (173, 206, 187), (117, 164, 139), draw_restare),
        ("ricordare", (174, 206, 238), (111, 148, 196), draw_ricordare),
        ("essere", (220, 212, 189), (179, 165, 132), draw_essere),
        ("odiare", (247, 177, 161), (220, 113, 97), draw_odiare),
        ("dovere", (183, 210, 246), (116, 150, 202), draw_dovere),
        ("interessare", (194, 211, 242), (121, 156, 206), draw_interessare),
        ("servire", (222, 211, 187), (181, 162, 130), draw_servire),
        ("nuotare", (132, 203, 238), (76, 151, 208), draw_nuotare),
        ("pattinare", (198, 223, 245), (127, 167, 211), draw_pattinare),
        ("sciare", (210, 228, 248), (128, 169, 220), draw_sciare),
    ]
    for name, top, bottom, renderer in images:
        save_image(name, top, bottom, renderer)
        print(f"OK  {OUT_DIR / f'{name}.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
